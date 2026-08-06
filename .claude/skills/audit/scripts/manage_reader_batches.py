#!/usr/bin/env python3
"""Plan and collect Audit's hash-bound bullet/page reader batches.

Reader calls are not evidence rows.  This helper expands every claim/page into
both required roles, groups only units with an identical complete raw manifest,
and writes deterministic call batches before any reader is launched.  Readers
write one sidecar per batch; collection rejects stale, pooled, truncated,
duplicate, or non-independent results and emits only a compact receipt on
stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any


HEX64 = re.compile(r'^[0-9a-f]{64}$')
HARD_MAX_BULLET_UNITS = 25
HARD_MAX_PAGE_UNITS = 4
HARD_MAX_CONCURRENT_CALLS = 4
BULLET_ROLES = ('locator_bullet', 'entailment_bullet')
PAGE_ROLES = ('locator_page', 'entailment_argument_page')
COUNTERPART = {
    'locator_bullet': 'entailment_bullet',
    'entailment_bullet': 'locator_bullet',
    'locator_page': 'entailment_argument_page',
    'entailment_argument_page': 'locator_page',
}
SCOPES = {'ordinary', 'exhaustive_negative'}
INPUT_KEYS = {
    'schema_version', 'run_id', 'relationship_epoch', 'bullet_units',
    'page_units',
}
PLAN_KEYS = {
    'schema_version', 'run_id', 'relationship_epoch', 'input_sha256',
    'max_bullet_units', 'max_page_units', 'max_concurrent_calls',
    'planned_groups', 'planned_bullet_records', 'planned_page_records',
    'planned_calls', 'planned_waves', 'batches', 'plan_sha256',
}
BATCH_KEYS = {
    'batch_id', 'kind', 'role', 'counterpart_role', 'manifest_sha256',
    'batch_number', 'wave_number', 'size', 'units',
}
UNIT_KEYS = {
    'unit_id', 'page_generation', 'raw_manifest', 'verification_scope',
    'quantified_population',
}
ARTIFACT_KEYS = {
    'schema_version', 'run_id', 'relationship_epoch', 'batch_id',
    'plan_sha256', 'input_sha256', 'role', 'agent_id', 'reader_run_id',
    'unit_ids', 'records',
}
EXECUTION_JOURNAL_KEYS = {
    'schema_version', 'run_id', 'warning_baseline_sha256', 'entries',
    'journal_sha256',
}
EXECUTION_JOURNAL_ENTRY_KEYS = {
    'execution_number', 'plan_sha256', 'collected_sha256',
    'previous_entry_sha256', 'anchor_sha256', 'entry_sha256',
}
EXECUTION_ANCHOR_KEYS = {
    'schema_version', 'run_id', 'warning_baseline_sha256',
    'execution_number', 'plan_sha256', 'collected_sha256',
    'previous_anchor_sha256', 'anchor_sha256',
}


class BatchError(ValueError):
    """One deterministic reader-plan or sidecar contract was violated."""

    def __init__(self, *, message: str) -> None:
        super().__init__(message)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value=value)).hexdigest()


def _nonplaceholder(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value == value.strip()
        and value != '...'
    )


def _normalize_manifest(value: Any, *, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise BatchError(message=f'{label} raw_manifest is not a list')
    manifest: list[dict[str, str]] = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {'raw_path', 'sha256'}
            or not isinstance(item.get('raw_path'), str)
            or not item['raw_path'].startswith('0-raw/')
            or not HEX64.fullmatch(str(item.get('sha256')))
        ):
            raise BatchError(message=f'{label} raw_manifest is malformed')
        manifest.append({'raw_path': item['raw_path'], 'sha256': item['sha256']})
    if (
        manifest != sorted(manifest, key=lambda item: item['raw_path'])
        or len({item['raw_path'] for item in manifest}) != len(manifest)
    ):
        raise BatchError(message=f'{label} raw_manifest is not unique and sorted')
    return manifest


def _normalize_unit(value: Any, *, kind: str, index: int) -> dict[str, Any]:
    label = f'{kind}_units[{index}]'
    if not isinstance(value, dict) or set(value) != UNIT_KEYS:
        raise BatchError(message=f'{label} fields are not schema-exact')
    unit_id = value.get('unit_id')
    generation = value.get('page_generation')
    scope = value.get('verification_scope')
    if not _nonplaceholder(value=unit_id):
        raise BatchError(message=f'{label} has invalid unit_id')
    if not HEX64.fullmatch(str(generation)):
        raise BatchError(message=f'{label} has invalid page_generation')
    if scope not in SCOPES or (kind == 'page' and scope != 'ordinary'):
        raise BatchError(message=f'{label} has invalid verification_scope')
    population = value.get('quantified_population')
    if scope == 'ordinary':
        if population is not None:
            raise BatchError(
                message=f'{label} ordinary unit has quantified_population'
            )
    manifest = _normalize_manifest(
        value=value.get('raw_manifest'), label=label
    )
    if scope == 'exhaustive_negative':
        if (
            not isinstance(population, dict)
            or set(population) != {'raw_paths', 'members'}
            or not isinstance(population.get('raw_paths'), list)
            or not isinstance(population.get('members'), list)
            or not population['raw_paths']
            or not population['members']
        ):
            raise BatchError(
                message=(
                    f'{label} exhaustive unit lacks frozen '
                    'quantified_population'
                )
            )
        raw_paths = population['raw_paths']
        if (
            any(not isinstance(item, str) for item in raw_paths)
            or raw_paths != [item['raw_path'] for item in manifest]
        ):
            raise BatchError(
                message=f'{label} quantified raw population differs from manifest'
            )
        member_ids: list[str] = []
        member_order: list[tuple[str, str]] = []
        covered_raws: set[str] = set()
        for member in population['members']:
            if (
                not isinstance(member, dict)
                or set(member) != {'member_id', 'raw_paths'}
                or not _nonplaceholder(value=member.get('member_id'))
                or not isinstance(member.get('raw_paths'), list)
                or not member['raw_paths']
                or any(
                    not isinstance(item, str) for item in member['raw_paths']
                )
                or member['raw_paths'] != sorted(set(member['raw_paths']))
                or not set(member['raw_paths']).issubset(set(raw_paths))
            ):
                raise BatchError(
                    message=f'{label} quantified member mapping is malformed'
                )
            member_ids.append(member['member_id'])
            member_order.append((member['raw_paths'][0], member['member_id']))
            covered_raws.update(member['raw_paths'])
        if (
            len(member_ids) != len(set(member_ids))
            or covered_raws != set(raw_paths)
            or member_order != sorted(member_order)
            or any(len(member['raw_paths']) != 1
                   for member in population['members'])
        ):
            raise BatchError(
                message=(
                    f'{label} quantified members are not unique, ordered, '
                    'and raw-complete'
                )
            )
    return {
        'unit_id': unit_id,
        'page_generation': generation,
        'raw_manifest': manifest,
        'verification_scope': scope,
        'quantified_population': population,
    }


def _normalize_input(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != INPUT_KEYS:
        raise BatchError(message='planner input fields are not schema-exact')
    if value.get('schema_version') != 1:
        raise BatchError(message='planner input schema_version must be 1')
    run_id = value.get('run_id')
    epoch = value.get('relationship_epoch')
    if not _nonplaceholder(value=run_id) or not _nonplaceholder(value=epoch):
        raise BatchError(
            message='planner input lacks run_id or relationship_epoch'
        )
    normalized: dict[str, Any] = {
        'schema_version': 1,
        'run_id': run_id,
        'relationship_epoch': epoch,
    }
    all_ids: set[tuple[str, str]] = set()
    for key, kind in (('bullet_units', 'bullet'), ('page_units', 'page')):
        raw_units = value.get(key)
        if not isinstance(raw_units, list):
            raise BatchError(message=f'{key} is not a list')
        units = [
            _normalize_unit(value=item, kind=kind, index=index)
            for index, item in enumerate(raw_units)
        ]
        units.sort(key=lambda item: item['unit_id'])
        for unit in units:
            identity = (kind, unit['unit_id'])
            if identity in all_ids:
                raise BatchError(
                    message=f'duplicate {kind} unit_id: {unit["unit_id"]}'
                )
            all_ids.add(identity)
        normalized[key] = units
    return normalized


def _batch_id(
    *, run_id: str, epoch: str, input_sha256: str, kind: str, role: str,
    manifest_sha256: str, batch_number: int, units: list[dict[str, Any]],
) -> str:
    digest = _sha256(value={
        'schema_version': 1,
        'run_id': run_id,
        'relationship_epoch': epoch,
        'input_sha256': input_sha256,
        'kind': kind,
        'role': role,
        'manifest_sha256': manifest_sha256,
        'batch_number': batch_number,
        'units': units,
    })
    return f'{kind}-{role}-{digest[:24]}'


def build_plan(
    value: Any, *, max_bullet_units: int = 25, max_page_units: int = 4,
    max_concurrent_calls: int = 4,
) -> dict[str, Any]:
    """Return the deterministic pre-dispatch call plan."""
    if (
        any(
            isinstance(item, bool) or not isinstance(item, int)
            for item in (
                max_bullet_units, max_page_units, max_concurrent_calls
            )
        )
        or max_bullet_units < 1
        or max_page_units < 1
        or max_concurrent_calls < 1
        or max_bullet_units > HARD_MAX_BULLET_UNITS
        or max_page_units > HARD_MAX_PAGE_UNITS
        or max_concurrent_calls > HARD_MAX_CONCURRENT_CALLS
    ):
        raise BatchError(
            message='batch/concurrency limits must be within hard maxima'
        )
    normalized = _normalize_input(value=value)
    input_sha = _sha256(value=normalized)
    batches: list[dict[str, Any]] = []
    planned_groups = 0
    for kind, roles, limit in (
        ('bullet', BULLET_ROLES, max_bullet_units),
        ('page', PAGE_ROLES, max_page_units),
    ):
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for unit in normalized[f'{kind}_units']:
            groups[_sha256(value=unit['raw_manifest'])].append(unit)
        planned_groups += len(groups)
        for manifest_sha in sorted(groups):
            group = groups[manifest_sha]
            for role in roles:
                for offset in range(0, len(group), limit):
                    units = group[offset : offset + limit]
                    number = offset // limit + 1
                    batches.append({
                        'batch_id': _batch_id(
                            run_id=normalized['run_id'],
                            epoch=normalized['relationship_epoch'],
                            input_sha256=input_sha,
                            kind=kind,
                            role=role,
                            manifest_sha256=manifest_sha,
                            batch_number=number,
                            units=units,
                        ),
                        'kind': kind,
                        'role': role,
                        'counterpart_role': COUNTERPART[role],
                        'manifest_sha256': manifest_sha,
                        'batch_number': number,
                        'size': len(units),
                        'units': units,
                    })
    for index, batch in enumerate(batches):
        batch['wave_number'] = index // max_concurrent_calls + 1
    plan: dict[str, Any] = {
        'schema_version': 1,
        'run_id': normalized['run_id'],
        'relationship_epoch': normalized['relationship_epoch'],
        'input_sha256': input_sha,
        'max_bullet_units': max_bullet_units,
        'max_page_units': max_page_units,
        'max_concurrent_calls': max_concurrent_calls,
        'planned_groups': planned_groups,
        'planned_bullet_records': 2 * len(normalized['bullet_units']),
        'planned_page_records': 2 * len(normalized['page_units']),
        'planned_calls': len(batches),
        'planned_waves': (
            (len(batches) + max_concurrent_calls - 1) // max_concurrent_calls
        ),
        'batches': batches,
    }
    plan['plan_sha256'] = _sha256(value=plan)
    validate_plan(plan=plan)
    return plan


def validate_plan(*, plan: Any) -> dict[str, Any]:
    """Reject a self-rehashed or structurally incomplete reader plan."""
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        raise BatchError(message='reader plan fields are not schema-exact')
    expected_plan_sha = plan.get('plan_sha256')
    unhashed = {key: value for key, value in plan.items() if key != 'plan_sha256'}
    if (
        plan.get('schema_version') != 1
        or not HEX64.fullmatch(str(expected_plan_sha))
        or _sha256(value=unhashed) != expected_plan_sha
    ):
        raise BatchError(message='reader plan SHA-256 does not match')
    if (
        not _nonplaceholder(value=plan.get('run_id'))
        or not _nonplaceholder(value=plan.get('relationship_epoch'))
        or not HEX64.fullmatch(str(plan.get('input_sha256')))
    ):
        raise BatchError(message='reader plan identity is malformed')
    limits = {
        'bullet': plan.get('max_bullet_units'),
        'page': plan.get('max_page_units'),
    }
    concurrency = plan.get('max_concurrent_calls')
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 1
        for value in (*limits.values(), concurrency)
    ) or (
        limits['bullet'] > HARD_MAX_BULLET_UNITS
        or limits['page'] > HARD_MAX_PAGE_UNITS
        or concurrency > HARD_MAX_CONCURRENT_CALLS
    ):
        raise BatchError(message='reader plan limits are malformed')
    batches = plan.get('batches')
    if not isinstance(batches, list):
        raise BatchError(message='reader plan lacks batches')
    if not batches:
        raise BatchError(message='reader plan has no executable batches')

    unique_units: dict[str, dict[str, dict[str, Any]]] = {
        'bullet': {}, 'page': {},
    }
    seen_batches: set[str] = set()
    seen_roles: set[tuple[str, str, str]] = set()
    group_numbers: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    groups: set[tuple[str, str]] = set()
    for index, batch in enumerate(batches):
        label = f'reader plan batch {index + 1}'
        if not isinstance(batch, dict) or set(batch) != BATCH_KEYS:
            raise BatchError(message=f'{label} fields are not schema-exact')
        kind = batch.get('kind')
        role = batch.get('role')
        if (
            kind not in {'bullet', 'page'}
            or role not in (BULLET_ROLES if kind == 'bullet' else PAGE_ROLES)
            or batch.get('counterpart_role') != COUNTERPART.get(role)
        ):
            raise BatchError(message=f'{label} role is malformed')
        units = batch.get('units')
        size = batch.get('size')
        number = batch.get('batch_number')
        wave = batch.get('wave_number')
        if (
            not isinstance(units, list)
            or not units
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size != len(units)
            or size > limits[kind]
            or isinstance(number, bool)
            or not isinstance(number, int)
            or number < 1
            or wave != index // concurrency + 1
        ):
            raise BatchError(message=f'{label} size, number, or wave is malformed')
        normalized_units = [
            _normalize_unit(value=unit, kind=kind, index=unit_index)
            for unit_index, unit in enumerate(units)
        ]
        if normalized_units != units:
            raise BatchError(message=f'{label} units are not canonical')
        manifest_sha = batch.get('manifest_sha256')
        if (
            not HEX64.fullmatch(str(manifest_sha))
            or any(_sha256(value=unit['raw_manifest']) != manifest_sha
                   for unit in units)
        ):
            raise BatchError(message=f'{label} mixes raw manifests')
        expected_id = _batch_id(
            run_id=plan['run_id'],
            epoch=plan['relationship_epoch'],
            input_sha256=plan['input_sha256'],
            kind=kind,
            role=role,
            manifest_sha256=manifest_sha,
            batch_number=number,
            units=units,
        )
        if batch.get('batch_id') != expected_id or expected_id in seen_batches:
            raise BatchError(message=f'{label} has invalid or duplicate batch_id')
        seen_batches.add(expected_id)
        group_numbers[(kind, role, manifest_sha)].append(number)
        groups.add((kind, manifest_sha))
        for unit in units:
            identity = (kind, unit['unit_id'], role)
            if identity in seen_roles:
                raise BatchError(message=f'{label} repeats a unit role')
            seen_roles.add(identity)
            existing = unique_units[kind].get(unit['unit_id'])
            if existing is not None and existing != unit:
                raise BatchError(message=f'{label} counterpart unit differs')
            unique_units[kind][unit['unit_id']] = unit
    for key, numbers in group_numbers.items():
        if numbers != list(range(1, len(numbers) + 1)):
            raise BatchError(message=f'reader plan group batches are noncontiguous: {key}')
    for kind, units in unique_units.items():
        required = set(BULLET_ROLES if kind == 'bullet' else PAGE_ROLES)
        for unit_id in units:
            actual = {
                role for row_kind, row_id, role in seen_roles
                if row_kind == kind and row_id == unit_id
            }
            if actual != required:
                raise BatchError(message=f'{kind} unit lacks both roles: {unit_id}')
    reconstructed = {
        'schema_version': 1,
        'run_id': plan['run_id'],
        'relationship_epoch': plan['relationship_epoch'],
        'bullet_units': sorted(
            unique_units['bullet'].values(), key=lambda item: item['unit_id']
        ),
        'page_units': sorted(
            unique_units['page'].values(), key=lambda item: item['unit_id']
        ),
    }
    if _sha256(value=reconstructed) != plan['input_sha256']:
        raise BatchError(message='reader plan units do not reconstruct input SHA-256')
    expected = {
        'planned_groups': len(groups),
        'planned_bullet_records': 2 * len(unique_units['bullet']),
        'planned_page_records': 2 * len(unique_units['page']),
        'planned_calls': len(batches),
        'planned_waves': (len(batches) + concurrency - 1) // concurrency,
    }
    for key, value in expected.items():
        if plan.get(key) != value:
            raise BatchError(message=f'reader plan {key} does not match batches')
    return reconstructed


def _validate_quantified_scope(
    record: dict[str, Any], *, label: str, unit: dict[str, Any],
) -> None:
    scope = record.get('quantified_scope')
    keys = {
        'raw_population', 'population', 'searched_members',
        'counterexamples', 'search_summary',
    }
    if not isinstance(scope, dict) or set(scope) != keys:
        raise BatchError(message=f'{label} lacks schema-exact quantified_scope')
    raw_population = scope.get('raw_population')
    population = scope.get('population')
    searched = scope.get('searched_members')
    counterexamples = scope.get('counterexamples')
    if any(
        not isinstance(items, list)
        or any(not _nonplaceholder(value=item) for item in items)
        or len(items) != len(set(items))
        for items in (raw_population, population, searched, counterexamples)
    ):
        raise BatchError(message=f'{label} quantified_scope lists are malformed')
    frozen = unit['quantified_population']
    if (
        raw_population != frozen['raw_paths']
        or population
        != [member['member_id'] for member in frozen['members']]
        or not set(searched).issubset(population)
        or not set(counterexamples).issubset(set(searched))
    ):
        raise BatchError(
            message=f'{label} quantified_scope population is malformed'
        )
    if not _nonplaceholder(value=scope.get('search_summary')):
        raise BatchError(message=f'{label} quantified_scope lacks search_summary')
    verdict = record.get('verdict')
    if verdict == 'hold' and (searched != population or counterexamples):
        raise BatchError(message=f'{label} HOLD is not exhaustive')
    if verdict == 'refute' and not counterexamples:
        raise BatchError(message=f'{label} REFUTE lacks a counterexample')


def _validate_record(
    *, record: Any, batch: dict[str, Any], unit: dict[str, Any],
    artifact: dict[str, Any],
) -> None:
    label = f'{batch["batch_id"]}:{unit["unit_id"]}'
    if not isinstance(record, dict) or record.get('truncated') is True:
        raise BatchError(message=f'{label} record is missing or truncated')
    if (
        record.get('schema_version') != 1
        or
        record.get('run_id') != artifact['run_id']
        or record.get('relationship_epoch') != artifact['relationship_epoch']
        or record.get('role') != artifact['role']
        or record.get('agent_id') != artifact['agent_id']
        or record.get('blind_to') != [batch['counterpart_role']]
        or not _nonplaceholder(value=record.get('row_id'))
        or record.get('verdict') not in {'hold', 'refute', 'cannot_confirm'}
    ):
        raise BatchError(message=f'{label} record is not bound to its batch')
    if batch['kind'] == 'bullet':
        if (
            record.get('row_type') != 'bullet_verdict'
            or record.get('claim_instance_id') != unit['unit_id']
            or not _nonplaceholder(value=record.get('role_version'))
            or not isinstance(record.get('quote_validated'), bool)
            or not _nonplaceholder(value=record.get('reasoning'))
            or not _nonplaceholder(value=record.get('confidence'))
            or 'correction' not in record
        ):
            raise BatchError(message=f'{label} bullet record is incomplete')
        if (
            record.get('verdict') == 'hold'
            and (
                not _nonplaceholder(value=record.get('quote'))
                or record.get('quote_validated') is not True
            )
        ):
            raise BatchError(message=f'{label} HOLD lacks validated quote')
        if unit['verification_scope'] == 'exhaustive_negative':
            _validate_quantified_scope(record=record, label=label, unit=unit)
    else:
        if (
            record.get('row_type') != 'page_reader'
            or record.get('page_path') != unit['unit_id']
            or record.get('page_generation') != unit['page_generation']
            or record.get('raw_manifest') != unit['raw_manifest']
            or not isinstance(record.get('defects'), list)
            or not _nonplaceholder(value=record.get('evidence'))
        ):
            raise BatchError(message=f'{label} page record is incomplete')
        if (
            (record.get('verdict') == 'hold' and record['defects'])
            or (record.get('verdict') != 'hold' and not record['defects'])
        ):
            raise BatchError(message=f'{label} page verdict contradicts defects')


def _load_artifact(*, path: Path, artifact_root: Path) -> Any:
    try:
        root = artifact_root.resolve(strict=True)
        if path.is_symlink():
            raise BatchError(
                message=f'reader artifact is a symlink: {path.name}'
            )
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file():
            raise BatchError(
                message=f'reader artifact is not a regular file: {path.name}'
            )
        return json.loads(resolved.read_text(encoding='utf-8'))
    except BatchError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BatchError(
            message=f'unreadable reader artifact: {path.name}'
        ) from error
    except ValueError as error:
        raise BatchError(
            message=f'reader artifact escapes its directory: {path.name}'
        ) from error


def collect_artifacts(plan: Any, artifact_dir: Path) -> dict[str, Any]:
    """Validate exact sidecars and return their ordered full ledger records."""
    validate_plan(plan=plan)
    expected_plan_sha = plan['plan_sha256']
    batches = plan['batches']
    expected_files = {f'{batch["batch_id"]}.json' for batch in batches}
    actual_files = {path.name for path in artifact_dir.glob('*.json')}
    if actual_files != expected_files:
        missing = sorted(expected_files - actual_files)
        extra = sorted(actual_files - expected_files)
        raise BatchError(
            message=(
                'reader artifact inventory differs: '
                f'missing={missing}, extra={extra}'
            )
        )

    merged: list[dict[str, Any]] = []
    seen_rows: set[str] = set()
    independence: dict[tuple[str, str], dict[str, tuple[str, str]]] = defaultdict(dict)
    receipts: list[dict[str, Any]] = []
    for batch in batches:
        artifact = _load_artifact(
            path=artifact_dir / f'{batch["batch_id"]}.json',
            artifact_root=artifact_dir,
        )
        if not isinstance(artifact, dict) or set(artifact) != ARTIFACT_KEYS:
            raise BatchError(
                message=(
                    f'{batch["batch_id"]} artifact fields are not schema-exact'
                )
            )
        expected_units = [unit['unit_id'] for unit in batch['units']]
        if (
            artifact.get('schema_version') != 1
            or artifact.get('run_id') != plan.get('run_id')
            or artifact.get('relationship_epoch') != plan.get('relationship_epoch')
            or artifact.get('batch_id') != batch['batch_id']
            or artifact.get('plan_sha256') != expected_plan_sha
            or artifact.get('input_sha256') != plan.get('input_sha256')
            or artifact.get('role') != batch['role']
            or not _nonplaceholder(value=artifact.get('agent_id'))
            or not _nonplaceholder(value=artifact.get('reader_run_id'))
            or artifact.get('unit_ids') != expected_units
            or not isinstance(artifact.get('records'), list)
            or len(artifact['records']) != len(expected_units)
        ):
            raise BatchError(
                message=(
                    f'{batch["batch_id"]} artifact is stale, pooled, or incomplete'
                )
            )
        records_by_id: dict[str, dict[str, Any]] = {}
        identity_key = 'claim_instance_id' if batch['kind'] == 'bullet' else 'page_path'
        for record in artifact['records']:
            identity = record.get(identity_key) if isinstance(record, dict) else None
            if not isinstance(identity, str) or identity in records_by_id:
                raise BatchError(
                    message=(
                        f'{batch["batch_id"]} has duplicate/unknown records'
                    )
                )
            records_by_id[identity] = record
        if set(records_by_id) != set(expected_units):
            raise BatchError(
                message=f'{batch["batch_id"]} pooled or omitted unit records'
            )
        for unit in batch['units']:
            record = records_by_id[unit['unit_id']]
            _validate_record(record=record, batch=batch, unit=unit, artifact=artifact)
            row_id = record['row_id']
            if row_id in seen_rows:
                raise BatchError(message=f'duplicate ledger row_id: {row_id}')
            seen_rows.add(row_id)
            merged.append(record)
            independence[(batch['kind'], unit['unit_id'])][batch['role']] = (
                artifact['agent_id'], artifact['reader_run_id']
            )
        receipts.append({
            'batch_id': batch['batch_id'],
            'role': batch['role'],
            'agent_id': artifact['agent_id'],
            'reader_run_id': artifact['reader_run_id'],
            'records': len(artifact['records']),
            'artifact_sha256': hashlib.sha256(
                (artifact_dir / f'{batch["batch_id"]}.json').read_bytes()
            ).hexdigest(),
        })

    for identity, roles in independence.items():
        kind = identity[0]
        required = set(BULLET_ROLES if kind == 'bullet' else PAGE_ROLES)
        if set(roles) != required:
            raise BatchError(message=f'{identity} lacks both reader roles')
        if len({agent for agent, _ in roles.values()}) != 2:
            raise BatchError(
                message=f'{identity} reuses one agent across blind roles'
            )
        if len({reader_run for _, reader_run in roles.values()}) != 2:
            raise BatchError(
                message=f'{identity} reuses one reader run across blind roles'
            )

    return {
        'schema_version': 1,
        'run_id': plan['run_id'],
        'relationship_epoch': plan['relationship_epoch'],
        'plan_sha256': expected_plan_sha,
        'input_sha256': plan['input_sha256'],
        'terminal_calls': len(receipts),
        'terminal_records': len(merged),
        'records_sha256': _sha256(value=merged),
        'receipts': receipts,
        'records': merged,
    }


def _atomic_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _journal_genesis(*, run_id: str, warning_baseline_sha256: str) -> str:
    return _sha256(value={
        'kind': 'audit-reader-execution-journal-genesis',
        'run_id': run_id,
        'warning_baseline_sha256': warning_baseline_sha256,
    })


def _with_journal_sha(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result['journal_sha256'] = _sha256(value={
        key: item for key, item in result.items()
        if key != 'journal_sha256'
    })
    return result


def _anchor_directory(*, journal_path: Path) -> Path:
    return journal_path.parent / 'execution-anchors'


def _anchor_path(*, journal_path: Path, execution_number: int) -> Path:
    return _anchor_directory(journal_path=journal_path) / (
        f'execution-{execution_number:03d}.json'
    )


def _load_execution_anchors(
    *, journal_path: Path, journal: dict[str, Any],
    trailing_plan_sha256: str | None = None,
    trailing_collected_sha256: str | None = None,
) -> list[dict[str, Any]]:
    """Authenticate the independent write-once execution census."""
    directory = _anchor_directory(journal_path=journal_path)
    if directory.is_symlink() or not directory.is_dir():
        raise BatchError(message='execution anchor directory is invalid')
    has_trailing = (
        trailing_plan_sha256 is not None
        and trailing_collected_sha256 is not None
    )
    expected_count = len(journal['entries']) + (1 if has_trailing else 0)
    expected_names = {
        f'execution-{index:03d}.json'
        for index in range(1, expected_count + 1)
    }
    actual = list(directory.iterdir())
    if (
        {item.name for item in actual} != expected_names
        or any(item.is_symlink() or not item.is_file() for item in actual)
    ):
        raise BatchError(message='execution anchor census differs from journal')
    anchors: list[dict[str, Any]] = []
    previous = _journal_genesis(
        run_id=journal['run_id'],
        warning_baseline_sha256=journal['warning_baseline_sha256'],
    )
    for index in range(1, expected_count + 1):
        entry = (
            journal['entries'][index - 1]
            if index <= len(journal['entries'])
            else None
        )
        path = _anchor_path(
            journal_path=journal_path, execution_number=index
        )
        try:
            anchor = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BatchError(message='execution anchor is unreadable') from error
        unhashed = {
            key: item for key, item in anchor.items()
            if key != 'anchor_sha256'
        } if isinstance(anchor, dict) else {}
        if (
            not isinstance(anchor, dict)
            or set(anchor) != EXECUTION_ANCHOR_KEYS
            or anchor.get('schema_version') != 1
            or anchor.get('run_id') != journal['run_id']
            or anchor.get('warning_baseline_sha256')
            != journal['warning_baseline_sha256']
            or anchor.get('execution_number') != index
            or anchor.get('previous_anchor_sha256') != previous
            or anchor.get('anchor_sha256') != _sha256(value=unhashed)
            or (
                entry is not None
                and (
                    anchor.get('plan_sha256') != entry.get('plan_sha256')
                    or anchor.get('collected_sha256')
                    != entry.get('collected_sha256')
                    or entry.get('anchor_sha256')
                    != anchor.get('anchor_sha256')
                )
            )
            or (
                entry is None
                and (
                    anchor.get('plan_sha256') != trailing_plan_sha256
                    or anchor.get('collected_sha256')
                    != trailing_collected_sha256
                )
            )
        ):
            raise BatchError(
                message=f'execution anchor {index} is not authentic'
            )
        anchors.append(anchor)
        previous = anchor['anchor_sha256']
    return anchors


def _exclusive_json_write(*, path: Path, value: Any) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=f'.{path.name}.', dir=path.parent
    )
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path, follow_symlinks=False)
        except FileExistsError as error:
            raise BatchError(
                message=f'exclusive artifact already exists: {path.name}'
            ) from error
    finally:
        try:
            os.unlink(temporary)
        except OSError:
            pass


def _recover_anchor_temps(
    *, journal_path: Path, journal: dict[str, Any],
) -> None:
    """Remove only unpublished or same-inode anchor temps after interruption."""
    directory = _anchor_directory(journal_path=journal_path)
    next_number = len(journal['entries']) + 1
    for candidate in directory.iterdir():
        matched = re.fullmatch(
            r'\.execution-(\d{3})\.json\..+', candidate.name
        )
        if matched is None:
            continue
        if candidate.is_symlink() or not candidate.is_file():
            raise BatchError(
                message='unpublished execution anchor temp is invalid'
            )
        execution_number = int(matched.group(1))
        final = _anchor_path(
            journal_path=journal_path,
            execution_number=execution_number,
        )
        if final.exists() or final.is_symlink():
            if (
                final.is_symlink()
                or not final.is_file()
                or not os.path.samefile(candidate, final)
            ):
                raise BatchError(
                    message='execution anchor temp does not match final anchor'
                )
        elif execution_number != next_number:
            raise BatchError(
                message='unexpected unpublished execution anchor temp'
            )
        candidate.unlink()


def validate_execution_journal(value: Any) -> dict[str, Any]:
    """Reject a rewritten, truncated, or malformed execution hash chain."""
    if (
        not isinstance(value, dict)
        or set(value) != EXECUTION_JOURNAL_KEYS
        or value.get('schema_version') != 1
        or not _nonplaceholder(value=value.get('run_id'))
        or not HEX64.fullmatch(str(value.get('warning_baseline_sha256')))
        or not isinstance(value.get('entries'), list)
    ):
        raise BatchError(message='execution journal identity is malformed')
    unhashed = {
        key: item for key, item in value.items()
        if key != 'journal_sha256'
    }
    if value.get('journal_sha256') != _sha256(value=unhashed):
        raise BatchError(message='execution journal payload SHA-256 does not match')
    previous = _journal_genesis(
        run_id=value['run_id'],
        warning_baseline_sha256=value['warning_baseline_sha256'],
    )
    seen_plans: set[str] = set()
    for index, entry in enumerate(value['entries'], 1):
        if (
            not isinstance(entry, dict)
            or set(entry) != EXECUTION_JOURNAL_ENTRY_KEYS
        ):
            raise BatchError(
                message=f'execution journal entry {index} is not schema-exact'
            )
        unhashed_entry = {
            key: item for key, item in entry.items()
            if key != 'entry_sha256'
        }
        if (
            entry.get('execution_number') != index
            or not HEX64.fullmatch(str(entry.get('plan_sha256')))
            or not HEX64.fullmatch(str(entry.get('collected_sha256')))
            or entry.get('previous_entry_sha256') != previous
            or entry.get('entry_sha256') != _sha256(value=unhashed_entry)
            or entry['plan_sha256'] in seen_plans
        ):
            raise BatchError(
                message=f'execution journal entry {index} breaks the hash chain'
            )
        seen_plans.add(entry['plan_sha256'])
        previous = entry['entry_sha256']
    return value


def init_execution_journal(
    *, path: Path, run_id: str, warning_baseline_sha256: str,
) -> dict[str, Any]:
    """Create the baseline-bound journal exactly once without replacement."""
    if (
        not _nonplaceholder(value=run_id)
        or not HEX64.fullmatch(warning_baseline_sha256)
    ):
        raise BatchError(message='execution journal identity is malformed')
    path.parent.mkdir(parents=True, exist_ok=True)
    if any(path.parent.iterdir()):
        raise BatchError(
            message='reader artifact run already has state; refusing reinitialization'
        )
    _anchor_directory(journal_path=path).mkdir()
    value = _with_journal_sha(value={
        'schema_version': 1,
        'run_id': run_id,
        'warning_baseline_sha256': warning_baseline_sha256,
        'entries': [],
    })
    try:
        _exclusive_json_write(path=path, value=value)
    except BatchError:
        _anchor_directory(journal_path=path).rmdir()
        raise
    return value


def append_execution_journal(
    *, path: Path, plan_path: Path, collected_path: Path,
) -> dict[str, Any]:
    """Validate the existing chain and append exactly one collected execution."""
    if path.is_symlink() or plan_path.is_symlink() or collected_path.is_symlink():
        raise BatchError(message='execution journal inputs cannot be symlinks')
    try:
        journal = json.loads(path.read_text(encoding='utf-8'))
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        collected_bytes = collected_path.read_bytes()
        collected = json.loads(collected_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BatchError(message='execution journal inputs are unreadable') from error
    validate_execution_journal(value=journal)
    validate_plan(plan=plan)
    if (
        not isinstance(collected, dict)
        or collected.get('schema_version') != 1
        or collected.get('run_id') != journal['run_id']
        or collected.get('run_id') != plan['run_id']
        or collected.get('relationship_epoch') != plan['relationship_epoch']
        or collected.get('plan_sha256') != plan['plan_sha256']
        or collected.get('input_sha256') != plan['input_sha256']
        or collected.get('terminal_calls') != plan['planned_calls']
        or collected.get('terminal_records')
        != plan['planned_bullet_records'] + plan['planned_page_records']
        or not isinstance(collected.get('records'), list)
        or collected.get('records_sha256')
        != _sha256(value=collected.get('records'))
    ):
        raise BatchError(message='collected execution does not match its plan')
    collected_sha256 = hashlib.sha256(collected_bytes).hexdigest()
    trailing_anchor: dict[str, Any] | None = None
    _recover_anchor_temps(
        journal_path=path,
        journal=journal,
    )
    try:
        _load_execution_anchors(journal_path=path, journal=journal)
    except BatchError:
        recovered = _load_execution_anchors(
            journal_path=path,
            journal=journal,
            trailing_plan_sha256=plan['plan_sha256'],
            trailing_collected_sha256=collected_sha256,
        )
        trailing_anchor = recovered[-1]
    if plan['plan_sha256'] in {
        entry['plan_sha256'] for entry in journal['entries']
    }:
        raise BatchError(message='execution plan is already journaled')
    previous = (
        journal['entries'][-1]['entry_sha256']
        if journal['entries']
        else _journal_genesis(
            run_id=journal['run_id'],
            warning_baseline_sha256=journal['warning_baseline_sha256'],
        )
    )
    entry = {
        'execution_number': len(journal['entries']) + 1,
        'plan_sha256': plan['plan_sha256'],
        'collected_sha256': collected_sha256,
        'previous_entry_sha256': previous,
    }
    previous_anchor = (
        journal['entries'][-1]['anchor_sha256']
        if journal['entries']
        else _journal_genesis(
            run_id=journal['run_id'],
            warning_baseline_sha256=journal['warning_baseline_sha256'],
        )
    )
    if trailing_anchor is None:
        anchor = {
            'schema_version': 1,
            'run_id': journal['run_id'],
            'warning_baseline_sha256': journal['warning_baseline_sha256'],
            'execution_number': entry['execution_number'],
            'plan_sha256': entry['plan_sha256'],
            'collected_sha256': entry['collected_sha256'],
            'previous_anchor_sha256': previous_anchor,
        }
        anchor['anchor_sha256'] = _sha256(value=anchor)
        _exclusive_json_write(
            path=_anchor_path(
                journal_path=path,
                execution_number=entry['execution_number'],
            ),
            value=anchor,
        )
        _recover_anchor_temps(journal_path=path, journal=journal)
    else:
        anchor = trailing_anchor
    entry['anchor_sha256'] = anchor['anchor_sha256']
    entry['entry_sha256'] = _sha256(value=entry)
    updated = _with_journal_sha(value={
        **journal,
        'entries': [*journal['entries'], entry],
    })
    validate_execution_journal(value=updated)
    _atomic_write(path=path, value=updated)
    _load_execution_anchors(journal_path=path, journal=updated)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    plan_parser = subparsers.add_parser('plan')
    plan_parser.add_argument('input', type=Path)
    plan_parser.add_argument('output', type=Path)
    plan_parser.add_argument('--max-bullet-units', type=int, default=25)
    plan_parser.add_argument('--max-page-units', type=int, default=4)
    plan_parser.add_argument('--max-concurrent-calls', type=int, default=4)
    collect_parser = subparsers.add_parser('collect')
    collect_parser.add_argument('plan', type=Path)
    collect_parser.add_argument('artifact_dir', type=Path)
    collect_parser.add_argument('output', type=Path)
    journal_init_parser = subparsers.add_parser('journal-init')
    journal_init_parser.add_argument('journal', type=Path)
    journal_init_parser.add_argument('--run-id', required=True)
    journal_init_parser.add_argument(
        '--warning-baseline-sha256', required=True
    )
    journal_append_parser = subparsers.add_parser('journal-append')
    journal_append_parser.add_argument('journal', type=Path)
    journal_append_parser.add_argument('plan', type=Path)
    journal_append_parser.add_argument('collected', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            value = json.loads(args.input.read_text(encoding='utf-8'))
            result = build_plan(
                value=value,
                max_bullet_units=args.max_bullet_units,
                max_page_units=args.max_page_units,
                max_concurrent_calls=args.max_concurrent_calls,
            )
            _atomic_write(path=args.output, value=result)
            print(json.dumps({
                'result': 'planned',
                'plan_sha256': result['plan_sha256'],
                'calls': result['planned_calls'],
                'waves': result['planned_waves'],
                'records': (
                    result['planned_bullet_records']
                    + result['planned_page_records']
                ),
                'output': str(args.output),
            }, sort_keys=True))
        elif args.command == 'collect':
            plan = json.loads(args.plan.read_text(encoding='utf-8'))
            result = collect_artifacts(
                plan=plan, artifact_dir=args.artifact_dir
            )
            _atomic_write(path=args.output, value=result)
            print(json.dumps({
                'result': 'collected',
                'plan_sha256': result['plan_sha256'],
                'calls': result['terminal_calls'],
                'records': result['terminal_records'],
                'records_sha256': result['records_sha256'],
                'output': str(args.output),
            }, sort_keys=True))
        elif args.command == 'journal-init':
            result = init_execution_journal(
                path=args.journal,
                run_id=args.run_id,
                warning_baseline_sha256=args.warning_baseline_sha256,
            )
            print(json.dumps({
                'result': 'journal-initialized',
                'entries': 0,
                'journal_sha256': result['journal_sha256'],
                'output': str(args.journal),
            }, sort_keys=True))
        else:
            result = append_execution_journal(
                path=args.journal,
                plan_path=args.plan,
                collected_path=args.collected,
            )
            print(json.dumps({
                'result': 'journal-appended',
                'entries': len(result['entries']),
                'journal_sha256': result['journal_sha256'],
                'output': str(args.journal),
            }, sort_keys=True))
    except (BatchError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        print(f'manage_reader_batches: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
