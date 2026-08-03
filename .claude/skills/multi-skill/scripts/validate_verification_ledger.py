#!/usr/bin/env python3
"""Validate a report's verification-ledger JSONL without judging semantics."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


START = '<!-- verification-ledger:start -->'
END = '<!-- verification-ledger:end -->'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
GIT_OID = re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
VALID_RESULTS = {'complete', 'unconverged', 'incomplete'}
REQUIRED_ROLES = {'locator_bullet', 'entailment_bullet'}
PAGE_ROLES = {'locator_page', 'entailment_argument_page'}
TERMINAL_VERDICTS = {'hold', 'refute', 'cannot_confirm'}
TERMINAL_CLAIMS = {
    'exempt',
    'reused_hold',
    'backfilled_hold',
    'refute',
    'cannot_confirm',
    'invalidated',
}
EXEMPTION_REASONS = {
    'obvious_definitional',
    'own_voice_judgement',
    'empty_placeholder',
    'verification_neutral_bookkeeping',
}
RECONCILIATION_UNITS = (
    'pages',
    'sources',
    'claims',
    'bullet_roles',
    'page_readers',
    'scanners',
    'status_writes',
)


class LedgerError(ValueError):
    """A deterministic ledger validation failure."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def canonical_claim_text(text: str) -> str:
    return (
        text.replace('\r\n', '\n')
        .replace('\r', '\n')
        .replace('*[unverified]*', '')
    )


def claim_identity_payload(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        'schema_version',
        'page_path',
        'page_type',
        'page_title',
        'semantic_frontmatter',
        'callout_type',
        'callout_id',
        'duplicate_ordinal',
        'locators',
        'raw_dependencies',
        'context_digest',
    )
    payload = {key: row.get(key) for key in keys}
    payload['claim_text_canonical'] = canonical_claim_text(row['claim_text'])
    return payload


def expected_claim_id(row: dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(claim_identity_payload(row))
    ).hexdigest()


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith('---\n'):
        raise LedgerError('report has no opening frontmatter delimiter')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise LedgerError('report frontmatter is unclosed')
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            result[key.strip()] = value.strip().strip('"\'')
    return result


def parse_rows(text: str) -> list[dict[str, Any]]:
    start = text.find(START)
    end = text.find(END, start + len(START))
    if start < 0 or end < 0:
        raise LedgerError('missing verification-ledger boundary')
    block = text[start + len(START) : end]
    fence_start = block.find('```jsonl')
    if fence_start < 0:
        raise LedgerError('ledger boundary contains no jsonl fence')
    content_start = block.find('\n', fence_start)
    fence_end = block.find('```', content_start + 1)
    if content_start < 0 or fence_end < 0:
        raise LedgerError('ledger jsonl fence is unclosed')
    rows: list[dict[str, Any]] = []
    for number, line in enumerate(
        block[content_start + 1 : fence_end].splitlines(), 1
    ):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerError(
                f'ledger line {number} is invalid JSON: {exc}'
            ) from exc
        if not isinstance(row, dict):
            raise LedgerError(f'ledger line {number} is not an object')
        rows.append(row)
    if not rows:
        raise LedgerError('ledger contains no rows')
    return rows


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    candidate = repo_root / value
    resolved = candidate.resolve(strict=True)
    root = repo_root.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise LedgerError(f'path escapes repository: {value}')
    relative = resolved.relative_to(root).as_posix()
    if relative != Path(value).as_posix():
        raise LedgerError(f'path is not canonical repo-relative form: {value}')
    return resolved


def extract_quote(raw: Path, physical_page: Any) -> str:
    if raw.suffix.lower() == '.pdf':
        if not isinstance(physical_page, int) or physical_page < 1:
            raise LedgerError(f'PDF quote lacks a valid physical page: {raw}')
        proc = subprocess.run(
            [
                'pdftotext',
                '-f',
                str(physical_page),
                '-l',
                str(physical_page),
                str(raw),
                '-',
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise LedgerError(
                f'pdftotext failed for {raw}: {proc.stderr.strip()}'
            )
        return proc.stdout
    return raw.read_text(encoding='utf-8')


def normalized_literal(text: str) -> str:
    return ' '.join(text.split())


def run_git(repo_root: Path, arguments: list[str]) -> str:
    """Run one read-only Git query and return stripped stdout."""
    proc = subprocess.run(
        ['git', '-C', str(repo_root), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise LedgerError(
            f'git {" ".join(arguments)} failed: {proc.stderr.strip()}'
        )
    return proc.stdout.strip()


def validate_duplicate_ordinals(claims: dict[str, dict[str, Any]]) -> None:
    """Require contiguous body-order ordinals for identical bullet groups."""
    groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for claim in claims.values():
        group = (
            claim['page_path'],
            claim['callout_id'],
            canonical_claim_text(claim['claim_text']),
        )
        ordinal = claim.get('duplicate_ordinal')
        if not isinstance(ordinal, int) or ordinal < 1:
            raise LedgerError(
                f'invalid duplicate ordinal: {claim["claim_instance_id"]}'
            )
        groups[group].append(ordinal)
    for group, ordinals in groups.items():
        expected = list(range(1, len(ordinals) + 1))
        if sorted(ordinals) != expected:
            raise LedgerError(
                f'duplicate ordinals are not contiguous for {group[:2]}'
            )


def validate_reused_pair(
    repo_root: Path,
    claim_id: str,
    terminal: dict[str, Any],
    *,
    recheck_quotes: bool,
) -> None:
    """Verify a reused pair against its clean committed producer report."""
    report_path = terminal.get('producer_report')
    producer_blob = terminal.get('producer_blob')
    row_ids = terminal.get('reused_role_rows')
    role_versions = terminal.get('role_versions')
    if not isinstance(report_path, str) or not GIT_OID.fullmatch(
        str(producer_blob)
    ):
        raise LedgerError(
            f'reused claim lacks producer provenance: {claim_id}'
        )
    if not isinstance(row_ids, list) or len(row_ids) != 2:
        raise LedgerError(
            f'reused claim lacks two role references: {claim_id}'
        )
    if (
        not isinstance(role_versions, dict)
        or set(role_versions) != REQUIRED_ROLES
    ):
        raise LedgerError(f'reused claim lacks role versions: {claim_id}')
    report = resolve_repo_path(repo_root, report_path)
    if run_git(repo_root, ['status', '--porcelain', '--', report_path]):
        raise LedgerError(f'producer report is dirty: {report_path}')
    head_blob = run_git(repo_root, ['rev-parse', f'HEAD:{report_path}'])
    if head_blob != producer_blob:
        raise LedgerError(f'producer blob mismatch: {report_path}')
    text = report.read_text(encoding='utf-8')
    frontmatter = parse_frontmatter(text)
    producer_rows = parse_rows(text)
    reconciliations = [
        row for row in producer_rows if row.get('row_type') == 'reconciliation'
    ]
    if (
        frontmatter.get('result') not in {'complete', 'unconverged'}
        or frontmatter.get('ledger_schema') != '1'
        or len(reconciliations) != 1
        or reconciliations[0].get('pending') != 0
    ):
        raise LedgerError(f'producer report is not terminal: {report_path}')
    role_rows = {
        row['row_id']: row
        for row in producer_rows
        if row.get('row_id') in row_ids
    }
    if set(role_rows) != set(row_ids):
        raise LedgerError(f'producer role rows are missing: {claim_id}')
    roles = {
        row.get('role')
        for row in role_rows.values()
        if row.get('claim_instance_id') == claim_id
        and row.get('verdict') == 'hold'
    }
    if roles != REQUIRED_ROLES:
        raise LedgerError(f'producer rows are not a HOLD pair: {claim_id}')
    for row in role_rows.values():
        if row.get('role_version') != role_versions[row['role']]:
            raise LedgerError(f'producer role version mismatch: {claim_id}')
        if recheck_quotes:
            validate_quote(repo_root, row)


def validate_quote(repo_root: Path, row: dict[str, Any]) -> None:
    if row.get('verdict') != 'hold':
        return
    quote = row.get('quote')
    raw_path = row.get('quote_raw_path')
    if (
        not isinstance(quote, str)
        or not quote.strip()
        or not isinstance(raw_path, str)
    ):
        raise LedgerError(f'HOLD row {row.get("row_id")} lacks quote/raw path')
    raw = resolve_repo_path(repo_root, raw_path)
    extracted = extract_quote(raw, row.get('physical_page'))
    if normalized_literal(quote) not in normalized_literal(extracted):
        raise LedgerError(
            'HOLD quote does not occur at attributed raw page: '
            f'{row.get("row_id")}'
        )


def validate(
    report: Path, repo_root: Path, *, recheck_quotes: bool
) -> dict[str, int | str]:
    text = report.read_text(encoding='utf-8')
    frontmatter = parse_frontmatter(text)
    result = frontmatter.get('result')
    if result not in VALID_RESULTS:
        raise LedgerError(f'invalid or missing report result: {result!r}')
    if frontmatter.get('ledger_schema') != '1':
        raise LedgerError('report does not declare ledger_schema 1')
    rows = parse_rows(text)

    row_ids: set[str] = set()
    rows_by_id: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    verdicts: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    terminals: dict[str, dict[str, Any]] = {}
    page_roles: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(
        dict
    )
    manifests: list[dict[str, Any]] = []
    scanners: list[dict[str, Any]] = []
    status_writes: list[dict[str, Any]] = []
    reconciliations: list[dict[str, Any]] = []

    for row in rows:
        if row.get('schema_version') != 1:
            raise LedgerError('every row must use schema_version 1')
        row_id = row.get('row_id')
        if not isinstance(row_id, str) or not row_id or row_id in row_ids:
            raise LedgerError(f'missing or duplicate row_id: {row_id!r}')
        row_ids.add(row_id)
        rows_by_id[row_id] = row
        row_type = row.get('row_type')
        if row_type == 'manifest':
            manifests.append(row)
        elif row_type == 'claim':
            claim_id = row.get('claim_instance_id')
            if claim_id in claims or not isinstance(claim_id, str):
                raise LedgerError(
                    f'missing or duplicate claim_instance_id: {claim_id!r}'
                )
            text_value = row.get('claim_text')
            if not isinstance(text_value, str):
                raise LedgerError(f'claim {claim_id} lacks full claim_text')
            if row.get('claim_bytes') != len(text_value.encode('utf-8')):
                raise LedgerError(f'claim byte length mismatch: {claim_id}')
            expected = expected_claim_id(row)
            if claim_id != expected or not HEX64.fullmatch(claim_id):
                raise LedgerError(f'claim identity mismatch: {claim_id}')
            if row.get('classification') not in {'required', 'exempt'}:
                raise LedgerError(f'invalid claim classification: {claim_id}')
            if not HEX64.fullmatch(str(row.get('context_digest'))):
                raise LedgerError(f'invalid context digest: {claim_id}')
            resolve_repo_path(repo_root, row['page_path'])
            dependencies = row.get('raw_dependencies')
            if not isinstance(dependencies, list):
                raise LedgerError(f'invalid raw dependencies: {claim_id}')
            dependency_paths = [
                dependency.get('raw_path')
                for dependency in dependencies
                if isinstance(dependency, dict)
            ]
            if dependency_paths != sorted(set(dependency_paths)):
                raise LedgerError(
                    f'raw dependencies are not unique and sorted: {claim_id}'
                )
            for dependency in dependencies:
                if not isinstance(dependency, dict):
                    raise LedgerError(f'invalid raw dependency: {claim_id}')
                raw_path = dependency.get('raw_path')
                raw_sha = dependency.get('sha256')
                if not isinstance(raw_path, str) or not HEX64.fullmatch(
                    str(raw_sha)
                ):
                    raise LedgerError(f'invalid raw dependency: {claim_id}')
                raw = resolve_repo_path(repo_root, raw_path)
                if hashlib.sha256(raw.read_bytes()).hexdigest() != raw_sha:
                    raise LedgerError(f'raw dependency changed: {claim_id}')
            claims[claim_id] = row
        elif row_type == 'bullet_verdict':
            claim_id = row.get('claim_instance_id')
            role = row.get('role')
            if role not in REQUIRED_ROLES or role in verdicts[claim_id]:
                raise LedgerError(
                    f'invalid/duplicate bullet role for {claim_id}: {role}'
                )
            if row.get('verdict') not in TERMINAL_VERDICTS:
                raise LedgerError(f'nonterminal bullet verdict: {row_id}')
            if recheck_quotes:
                validate_quote(repo_root, row)
            verdicts[claim_id][role] = row
        elif row_type == 'claim_terminal':
            claim_id = row.get('claim_instance_id')
            if (
                claim_id in terminals
                or row.get('disposition') not in TERMINAL_CLAIMS
            ):
                raise LedgerError(
                    f'invalid/duplicate terminal claim row: {claim_id}'
                )
            terminals[claim_id] = row
        elif row_type == 'page_reader':
            key = (row.get('page_path'), row.get('page_generation'))
            role = row.get('role')
            if role not in PAGE_ROLES or role in page_roles[key]:
                raise LedgerError(
                    f'invalid/duplicate page role for {key}: {role}'
                )
            if row.get('verdict') not in TERMINAL_VERDICTS:
                raise LedgerError(f'nonterminal page verdict: {row_id}')
            page_roles[key][role] = row
        elif row_type == 'reconciliation':
            reconciliations.append(row)
        elif row_type == 'scanner':
            scanners.append(row)
        elif row_type == 'status_write':
            status_writes.append(row)
        else:
            raise LedgerError(f'unknown row_type: {row_type!r}')

    if len(manifests) != 1:
        raise LedgerError('report must contain exactly one manifest row')
    validate_duplicate_ordinals(claims)
    if set(claims) != set(terminals):
        raise LedgerError(
            'claim manifest does not equal terminal claim dispositions'
        )
    if set(verdicts) - set(claims):
        raise LedgerError('bullet verdict references an unknown claim')
    for claim_id, claim in claims.items():
        terminal = terminals[claim_id]
        if claim['classification'] == 'exempt':
            if (
                terminal['disposition'] != 'exempt'
                or claim.get('exemption_reason') not in EXEMPTION_REASONS
                or verdicts[claim_id]
            ):
                raise LedgerError(
                    f'exempt claim lacks exempt terminal: {claim_id}'
                )
            continue
        disposition = terminal['disposition']
        if disposition in {'backfilled_hold', 'refute', 'cannot_confirm'}:
            if set(verdicts[claim_id]) != REQUIRED_ROLES:
                raise LedgerError(
                    f'current evidence does not contain both roles: {claim_id}'
                )
            agents = {
                verdicts[claim_id][role].get('agent_id')
                for role in REQUIRED_ROLES
            }
            if len(agents) != 2 or None in agents:
                raise LedgerError(f'bullet roles are not distinct: {claim_id}')
            outcomes = {
                verdicts[claim_id][role]['verdict'] for role in REQUIRED_ROLES
            }
            if disposition == 'backfilled_hold' and outcomes != {'hold'}:
                raise LedgerError(
                    f'backfilled HOLD has a non-HOLD role: {claim_id}'
                )
            if disposition == 'refute' and 'refute' not in outcomes:
                raise LedgerError(
                    f'refute disposition lacks a refutation: {claim_id}'
                )
            if disposition == 'cannot_confirm' and (
                'refute' in outcomes or 'cannot_confirm' not in outcomes
            ):
                raise LedgerError(
                    'cannot-confirm disposition mismatches its roles: '
                    f'{claim_id}'
                )
        elif disposition == 'reused_hold':
            if verdicts[claim_id]:
                raise LedgerError(
                    f'reused claim also carries current rows: {claim_id}'
                )
            validate_reused_pair(
                repo_root,
                claim_id,
                terminal,
                recheck_quotes=recheck_quotes,
            )

    for key, roles in page_roles.items():
        if set(roles) != PAGE_ROLES:
            raise LedgerError(f'page generation lacks both page roles: {key}')
        agents = {roles[role].get('agent_id') for role in PAGE_ROLES}
        if len(agents) != 2 or None in agents:
            raise LedgerError(f'page roles are not distinct: {key}')

    if len(reconciliations) != 1:
        raise LedgerError('report must contain exactly one reconciliation row')
    rec = reconciliations[0]
    if rec.get('result') != result:
        raise LedgerError('frontmatter and reconciliation results differ')
    pending = rec.get('pending')
    if not isinstance(pending, int) or pending < 0:
        raise LedgerError(
            'reconciliation pending must be a nonnegative integer'
        )
    if result in {'complete', 'unconverged'} and pending != 0:
        raise LedgerError('terminal report has pending work')
    frontmatter_pending = frontmatter.get('pending')
    try:
        parsed_frontmatter_pending = int(str(frontmatter_pending))
    except ValueError as exc:
        raise LedgerError('frontmatter pending is not an integer') from exc
    if parsed_frontmatter_pending != pending:
        raise LedgerError('frontmatter and reconciliation pending differ')
    manifest = manifests[0]
    pending_units = 0
    for prefix in RECONCILIATION_UNITS:
        planned = rec.get(f'planned_{prefix}')
        terminal = rec.get(f'terminal_{prefix}')
        if not isinstance(planned, int) or not isinstance(terminal, int):
            raise LedgerError(f'reconciliation lacks integer {prefix} counts')
        pending_unit = rec.get(f'pending_{prefix}')
        if not isinstance(pending_unit, int) or pending_unit < 0:
            raise LedgerError(
                f'reconciliation lacks integer pending {prefix} count'
            )
        if planned != terminal + pending_unit:
            raise LedgerError(
                f'planned/terminal/pending mismatch for {prefix}'
            )
        pending_units += pending_unit
        if manifest.get(f'planned_{prefix}') != planned:
            raise LedgerError(f'manifest/reconciliation mismatch for {prefix}')
    if pending != pending_units:
        raise LedgerError('overall pending does not equal pending unit counts')
    required_claims = sum(
        claim['classification'] == 'required' for claim in claims.values()
    )
    reused_claims = sum(
        terminal['disposition'] == 'reused_hold'
        for terminal in terminals.values()
    )
    actual_terminal = {
        'claims': len(terminals),
        'bullet_roles': len(
            [row for roles in verdicts.values() for row in roles.values()]
        )
        + (2 * reused_claims),
        'page_readers': sum(len(roles) for roles in page_roles.values()),
        'scanners': len(scanners),
        'status_writes': len(status_writes),
    }
    if rec['planned_claims'] != len(claims):
        raise LedgerError('planned claim count does not match claim rows')
    claim_pages = {claim['page_path'] for claim in claims.values()}
    if rec['planned_pages'] != len(claim_pages):
        raise LedgerError('planned page count does not match claim rows')
    raw_paths = {
        dependency['raw_path']
        for claim in claims.values()
        for dependency in claim['raw_dependencies']
    }
    if rec['planned_sources'] != len(raw_paths):
        raise LedgerError(
            'planned source count does not match raw dependencies'
        )
    if rec['planned_bullet_roles'] != 2 * required_claims:
        raise LedgerError(
            'planned bullet roles do not equal required claim pairs'
        )
    if frontmatter.get('type') == 'audit':
        if rec['planned_page_readers'] != 2 * rec['planned_pages']:
            raise LedgerError('audit does not plan two readers per page')
        if rec['planned_status_writes'] != rec['planned_pages']:
            raise LedgerError('audit lacks one status disposition per page')
    for unit, actual in actual_terminal.items():
        if rec[f'terminal_{unit}'] != actual:
            raise LedgerError(f'terminal {unit} count does not match rows')

    return {
        'result': result,
        'rows': len(rows),
        'claims': len(claims),
        'page_generations': len(page_roles),
        'pending': pending,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--skip-quote-recheck', action='store_true')
    args = parser.parse_args()
    try:
        summary = validate(
            args.report,
            args.repo_root,
            recheck_quotes=not args.skip_quote_recheck,
        )
    except (OSError, LedgerError) as exc:
        print(
            json.dumps(
                [
                    {
                        'check_id': 'verification_ledger_invalid',
                        'error': str(exc),
                    }
                ]
            )
        )
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
