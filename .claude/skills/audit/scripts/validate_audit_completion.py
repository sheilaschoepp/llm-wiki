#!/usr/bin/env python3
"""Reject Audit completion when final Warning or pending proof is non-zero."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from build_suppression_batches import (  # noqa: E402
    CANDIDATE_FIELDS,
    REVIEW_KINDS,
    build_batches,
    validate_candidate,
)
from capture_warning_baseline import (  # noqa: E402
    BASELINE_DIRECTORY,
    CANONICAL_RULE_PATHS,
    CANONICAL_CHECKER_PATH,
    IGNORE_PATH,
    RELATIONSHIP_RULE_PATHS,
)


START = '<!-- verification-ledger:start -->'
END = '<!-- verification-ledger:end -->'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
ORIGINS = {'initial', 'introduced'}
NONMENTION_DISPOSITIONS = {
    'fixed',
    'standing_ignore',
    'verified_not_applicable',
    'needs_update',
}
SEMANTIC_OCCURRENCE_DISPOSITIONS = {
    'genuine_wrap',
    'accepted_suppression',
    'graph_repair',
    'graph_ignore',
}
TRANSITION_DISPOSITIONS = {'superseded', 'rekeyed'}
UNREVIEWED_OCCURRENCE_DISPOSITIONS = {
    'genuine_wrap',
    'graph_repair',
}
READER_ROLES = {'reader_a', 'reader_b'}
READER_COUNTERPART = {'reader_a': 'reader_b', 'reader_b': 'reader_a'}
QUESTION_VERSIONS = {
    'generic_suppression': 'generic-suppression-v1',
    'graph_ignore': 'graph-ignore-v1',
}
WARNING_ID_FIELDS = (
    'origin',
    'check_id',
    'page_path',
    'target',
    'message_sha256',
)
WARNING_ROW_FIELDS = frozenset(
    {
        'schema_version',
        'row_id',
        'run_id',
        'warning_id',
        *WARNING_ID_FIELDS,
        'disposition',
        'resolution',
    }
)
OCCURRENCE_COMMON_FIELDS = CANDIDATE_FIELDS | frozenset(
    {
        'schema_version',
        'row_id',
        'run_id',
        'origin',
        'disposition',
        'review_kind',
        'resolution',
        'ignore_entry',
    }
)
OCCURRENCE_ROW_FIELDS = OCCURRENCE_COMMON_FIELDS
SUPERSEDED_ROW_FIELDS = OCCURRENCE_COMMON_FIELDS | {'rekeyed_to'}
REKEYED_ROW_FIELDS = OCCURRENCE_COMMON_FIELDS | {
    'rekeyed_from',
    'final_disposition',
}
BATCH_ROW_FIELDS = frozenset(
    {
        'schema_version',
        'row_id',
        'run_id',
        'review_kind',
        'evidence_context_sha256',
        'input_sha256',
        'batch_number',
        'batch_digest',
        'size',
        'occurrence_ids',
    }
)
READER_ROW_FIELDS = frozenset(
    {
        'schema_version',
        'row_id',
        'run_id',
        'occurrence_id',
        'review_kind',
        'evidence_context_sha256',
        'input_sha256',
        'batch_number',
        'batch_digest',
        'reader_role',
        'agent_id',
        'reader_run_id',
        'blind_to',
        'verdict',
        'question_version',
        'reasoning',
    }
)
NEUTRAL_TRANSACTION_FIELDS = frozenset(
    {
        'schema_version',
        'row_id',
        'run_id',
        'page_path',
        'preimage_sha256',
        'postimage_sha256',
        'postimage_bytes_base64',
        'before_status',
        'after_status',
        'verified_hash',
        'baseline_occurrence_ids',
    }
)


def _frontmatter(report: Path) -> dict[str, Any]:
    text = report.read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not match:
        raise ValueError('report frontmatter missing or malformed')
    fields: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if ':' not in line:
            continue
        key, raw_value = line.split(':', 1)
        value = raw_value.strip().strip('"').strip("'")
        fields[key.strip()] = (
            int(value) if re.fullmatch(r'-?\d+', value) else value
        )
    return fields


def _ledger_rows(report: Path) -> list[dict[str, Any]]:
    text = report.read_text(encoding='utf-8')
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError('report must contain exactly one ledger marker pair')
    pattern = re.compile(
        r'^' + re.escape(START) + r'\n'
        r'```jsonl\n(?P<payload>.*?)\n```\n'
        + re.escape(END) + r'$',
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(
            'ledger markers and jsonl fence must be line-anchored and unique'
        )
    payload = matches[0].group('payload')
    if re.search(r'^```', payload, re.MULTILINE):
        raise ValueError('ledger payload contains an additional fence')
    rows: list[dict[str, Any]] = []
    for line in payload.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        row = json.loads(stripped)
        if not isinstance(row, dict):
            raise ValueError('ledger row is not an object')
        rows.append(row)
    if not rows:
        raise ValueError('verification ledger is empty')
    return rows


def _integer(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(
            f'{row.get("row_type", "row")} field {key} is not an integer'
        )
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def expected_warning_id(row: dict[str, Any]) -> str:
    """Return the exact identity of one frozen non-mention Warning."""
    payload = {key: row.get(key) for key in WARNING_ID_FIELDS}
    return hashlib.sha256(_canonical_json(value=payload)).hexdigest()


def _canonical_report_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and '..' not in path.parts
        and path.as_posix() == value
    )


def _exact_rows(
    *,
    reconciliation: dict[str, Any],
    key: str,
    fields: frozenset[str],
    failures: list[str],
) -> list[dict[str, Any]]:
    value = reconciliation.get(key)
    if not isinstance(value, list):
        failures.append(f'reconciliation {key} is not an array')
        return []
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value, 1):
        if not isinstance(row, dict):
            failures.append(f'{key} row {index} is not an object')
            continue
        missing = sorted(fields - set(row))
        extra = sorted(set(row) - fields)
        if missing or extra:
            failures.append(
                f'{key} row {index} has schema mismatch: '
                f'missing={missing}; extra={extra}'
            )
            continue
        rows.append(row)
    return rows


def _exact_occurrence_rows(
    *, reconciliation: Dict[str, Any], failures: List[str]
) -> List[Dict[str, Any]]:
    value = reconciliation.get('mention_occurrences')
    if not isinstance(value, list):
        failures.append('reconciliation mention_occurrences is not an array')
        return []
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(value, 1):
        label = 'mention_occurrences row {}'.format(index)
        if not isinstance(row, dict):
            failures.append('{} is not an object'.format(label))
            continue
        disposition = row.get('disposition')
        if disposition == 'superseded':
            fields = SUPERSEDED_ROW_FIELDS
        elif disposition == 'rekeyed':
            fields = REKEYED_ROW_FIELDS
        else:
            fields = OCCURRENCE_ROW_FIELDS
        missing = sorted(fields - set(row))
        extra = sorted(set(row) - fields)
        if missing or extra:
            failures.append(
                '{} has schema mismatch: missing={}; extra={}'.format(
                    label, missing, extra
                )
            )
            continue
        rows.append(row)
    return rows


def _validate_nested_identity(
    *,
    row: dict[str, Any],
    label: str,
    run_id: Any,
    used_row_ids: set[str],
    failures: list[str],
) -> None:
    if row.get('schema_version') != 1 or isinstance(
        row.get('schema_version'), bool
    ):
        failures.append(f'{label} does not use schema_version 1')
    row_id = row.get('row_id')
    if (
        not isinstance(row_id, str)
        or not row_id.strip()
        or row_id != row_id.strip()
        or row_id.strip() == '...'
        or row_id in used_row_ids
    ):
        failures.append(
            f'{label} has missing, placeholder, or duplicate row_id'
        )
    else:
        used_row_ids.add(row_id)
    if row.get('run_id') != run_id:
        failures.append(f'{label} run_id differs from terminal run')


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_status_paths(*, status_bytes: bytes) -> set:
    paths = set()
    fields = status_bytes.split(b'\0')
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        status = field[:2]
        path = field[3:] if len(field) > 3 else b''
        if path:
            paths.add(path.decode('utf-8', errors='surrogateescape'))
        if b'R' in status or b'C' in status:
            if index < len(fields) and fields[index]:
                paths.add(
                    fields[index].decode('utf-8', errors='surrogateescape')
                )
                index += 1
    return paths


def _trusted_checker_sha256(*, root: Path, head: str) -> Optional[str]:
    if head == 'unavailable':
        current = subprocess.run(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'],
            capture_output=True,
            check=False,
        )
        if current.returncode == 0:
            raise ValueError(
                'warning baseline omits the repository pre-edit HEAD'
            )
        return None
    committed = subprocess.run(
        [
            'git',
            '-C',
            str(root),
            'show',
            '{}:{}'.format(head, CANONICAL_CHECKER_PATH),
        ],
        capture_output=True,
        check=False,
    )
    if committed.returncode != 0:
        raise ValueError(
            'warning baseline checker is absent from its pre-edit HEAD'
        )
    return _sha256_bytes(data=committed.stdout)


def _resolve_baseline_path(
    *, report: Path, repo_root: Optional[Path], value: Any
) -> Tuple[Path, Path]:
    if not _canonical_report_path(value=value):
        raise ValueError('warning baseline path is not canonical')
    baseline_path = PurePosixPath(str(value))
    if (
        baseline_path.parent.as_posix() != BASELINE_DIRECTORY
        or baseline_path.suffix != '.json'
    ):
        raise ValueError(
            'warning baseline path is outside the canonical baseline directory'
        )
    root = report.parent.resolve() if repo_root is None else repo_root.resolve()
    path = (root / str(value)).resolve(strict=True)
    if root != path and root not in path.parents:
        raise ValueError('warning baseline path escapes repository root')
    return root, path


def _validate_hash_map(
    *,
    root: Path,
    value: Any,
    expected_paths: Optional[set] = None,
    verify_current: bool = True,
) -> Dict[str, str]:
    if not isinstance(value, dict) or any(
        not _canonical_report_path(value=path)
        or not isinstance(digest, str)
        or not HEX64.fullmatch(digest)
        for path, digest in value.items()
    ):
        raise ValueError('warning baseline contains a malformed hash map')
    if expected_paths is not None and set(value) != expected_paths:
        raise ValueError('warning baseline rule-path inventory is incomplete')
    for relative, digest in value.items():
        if not verify_current:
            continue
        path = (root / relative).resolve(strict=True)
        if root != path and root not in path.parents:
            raise ValueError('warning baseline hash path escapes repository')
        if _sha256_bytes(data=path.read_bytes()) != digest:
            raise ValueError(
                'warning baseline evidence context changed: {}'.format(
                    relative
                )
            )
    return dict(value)


def _load_warning_baseline(
    *,
    report: Path,
    repo_root: Optional[Path],
    reconciliation: Dict[str, Any],
) -> Tuple[Path, Dict[str, Any]]:
    baseline_value = reconciliation.get('warning_baseline_path')
    root, path = _resolve_baseline_path(
        report=report, repo_root=repo_root, value=baseline_value
    )
    expected_sha = reconciliation.get('warning_baseline_sha256')
    data = path.read_bytes()
    if not isinstance(expected_sha, str) or not HEX64.fullmatch(expected_sha):
        raise ValueError('warning baseline SHA-256 is missing or malformed')
    if _sha256_bytes(data=data) != expected_sha:
        raise ValueError('warning baseline SHA-256 does not match artifact')
    try:
        baseline = json.loads(data)
    except json.JSONDecodeError as error:
        raise ValueError('warning baseline is not parseable JSON') from error
    if (
        not isinstance(baseline, dict)
        or baseline.get('schema_version') != 1
        or baseline.get('kind') != 'audit-warning-baseline'
    ):
        raise ValueError('warning baseline schema is invalid')
    git_pre_edit = baseline.get('git_pre_edit')
    if not isinstance(git_pre_edit, dict):
        raise ValueError('warning baseline lacks pre-edit Git evidence')
    try:
        status_bytes = base64.b64decode(
            git_pre_edit.get('status_bytes_base64', ''), validate=True
        )
    except (TypeError, ValueError) as error:
        raise ValueError('warning baseline Git status bytes are invalid') from error
    head = git_pre_edit.get('head')
    if (
        not isinstance(head, str)
        or (
            head != 'unavailable'
            and not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', head)
        )
        or git_pre_edit.get('status_sha256') != _sha256_bytes(data=status_bytes)
    ):
        raise ValueError('warning baseline Git evidence is malformed')
    protected_dirty = _git_status_paths(status_bytes=status_bytes) & {
        CANONICAL_CHECKER_PATH,
    }
    if protected_dirty:
        raise ValueError(
            'warning baseline captured dirty protected inputs: {}'.format(
                sorted(protected_dirty)
            )
        )
    trusted_checker_sha = _trusted_checker_sha256(root=root, head=head)

    canonical = _validate_hash_map(
        root=root,
        value=baseline.get('canonical_rule_hashes'),
        expected_paths=set(CANONICAL_RULE_PATHS),
    )
    relationship = _validate_hash_map(
        root=root,
        value=baseline.get('relationship_rule_hashes'),
        expected_paths=set(RELATIONSHIP_RULE_PATHS),
    )
    targets = _validate_hash_map(
        root=root,
        value=baseline.get('target_page_hashes'),
        verify_current=False,
    )
    ignore = baseline.get('ignore_file')
    if not isinstance(ignore, dict) or ignore.get('path') != IGNORE_PATH:
        raise ValueError('warning baseline ignore-file record is invalid')
    try:
        ignore_bytes = base64.b64decode(
            ignore.get('bytes_base64', ''), validate=True
        )
    except (TypeError, ValueError) as error:
        raise ValueError('warning baseline ignore bytes are invalid') from error
    ignore_sha = ignore.get('sha256')
    if (
        not isinstance(ignore_sha, str)
        or not HEX64.fullmatch(ignore_sha)
        or _sha256_bytes(data=ignore_bytes) != ignore_sha
    ):
        raise ValueError('warning baseline ignore hash is invalid')
    evidence_payload = {
        'canonical_rule_hashes': canonical,
        'relationship_rule_hashes': relationship,
        'target_page_hashes': targets,
        'initial_ignore_sha256': ignore_sha,
    }
    expected_context = _sha256_bytes(
        data=_canonical_json(value=evidence_payload)
    )
    if baseline.get('evidence_context_sha256') != expected_context:
        raise ValueError('warning baseline evidence-context hash is invalid')
    if reconciliation.get('evidence_context_sha256') != expected_context:
        raise ValueError('report is not bound to baseline evidence context')
    baseline_id = baseline.get('baseline_id')
    if (
        not isinstance(baseline_id, str)
        or not baseline_id.strip()
        or baseline_id != baseline_id.strip()
        or baseline_id == '...'
        or reconciliation.get('warning_baseline_id') != baseline_id
    ):
        raise ValueError('report lacks the exact non-placeholder baseline ID')
    if (
        baseline.get('run_id') != reconciliation.get('run_id')
        or baseline.get('run_id') in {None, '', '...'}
    ):
        raise ValueError('warning baseline run ID differs from report run')

    checker = baseline.get('checker')
    enumerator = baseline.get('enumerator')
    preimages = baseline.get('affected_page_preimages')
    if (
        not isinstance(checker, dict)
        or not isinstance(checker.get('findings'), list)
        or not isinstance(checker.get('warning_findings'), list)
        or not isinstance(enumerator, dict)
        or not isinstance(enumerator.get('groups'), list)
        or not isinstance(enumerator.get('occurrences'), list)
        or not isinstance(preimages, dict)
    ):
        raise ValueError('warning baseline inventories are malformed')
    checker_path = (root / CANONICAL_CHECKER_PATH).resolve(strict=True)
    if (
        checker.get('path') != CANONICAL_CHECKER_PATH
        or (
            trusted_checker_sha is not None
            and checker.get('sha256') != trusted_checker_sha
        )
        or checker.get('sha256')
        != _sha256_bytes(data=checker_path.read_bytes())
        or checker.get('status') != 0
    ):
        raise ValueError('warning baseline is not bound to canonical checker')
    exact_warnings = [
        row
        for row in checker['findings']
        if isinstance(row, dict) and row.get('severity') == 'warning'
    ]
    if checker['warning_findings'] != exact_warnings:
        raise ValueError('warning baseline Warning array differs from checker')
    nonmention = [
        row
        for row in exact_warnings
        if row.get('check_id') != 'unlinked_page_mention'
    ]
    derived_fingerprints = [
        {
            'origin': 'initial',
            'check_id': row.get('check_id'),
            'page_path': row.get('file'),
            'target': row.get('target', ''),
            'message_sha256': _sha256_bytes(
                data=str(row.get('message', '')).encode('utf-8')
            ),
        }
        for row in nonmention
    ]
    if baseline.get('warning_fingerprints') != derived_fingerprints:
        raise ValueError(
            'warning baseline fingerprints are not derived from checker output'
        )
    groups = enumerator['groups']
    occurrences = enumerator['occurrences']
    if enumerator.get('status') != 'ok':
        raise ValueError('warning baseline enumerator is not terminal')
    if enumerator.get('mention_groups') != len(groups):
        raise ValueError('warning baseline mention group count is invalid')
    if enumerator.get('exact_occurrences') != len(occurrences):
        raise ValueError('warning baseline occurrence count is invalid')
    if enumerator.get('zero_match_scanner_defects') != 0:
        raise ValueError('warning baseline contains zero-match scanner defects')

    native_groups: Dict[Tuple[str, str], int] = {}
    for finding in exact_warnings:
        if finding.get('check_id') != 'unlinked_page_mention':
            continue
        parsed = re.search(
            r'Existing page `([^`]+)` is mentioned unlinked (\d+)×',
            str(finding.get('message', '')),
        )
        if parsed is None:
            raise ValueError(
                'warning baseline contains an unparseable mention finding'
            )
        key = (str(finding.get('file', '')), parsed.group(1))
        if key in native_groups:
            raise ValueError('warning baseline has duplicate mention groups')
        native_groups[key] = int(parsed.group(2))
    enumerated_groups = {
        (row.get('page_path'), row.get('target_stem')): row.get(
            'exact_occurrences'
        )
        for row in groups
        if isinstance(row, dict)
    }
    if native_groups != enumerated_groups:
        raise ValueError('warning baseline lacks native mention-group parity')

    for relative, record in preimages.items():
        if not _canonical_report_path(value=relative) or not isinstance(
            record, dict
        ):
            raise ValueError('warning baseline page preimage is malformed')
        try:
            preimage = base64.b64decode(
                record.get('bytes_base64', ''), validate=True
            )
        except (TypeError, ValueError) as error:
            raise ValueError('warning baseline page bytes are invalid') from error
        if _sha256_bytes(data=preimage) != record.get('sha256'):
            raise ValueError('warning baseline page preimage hash is invalid')
        if record.get('status') == 'verified':
            try:
                lines, body = _frontmatter_and_body(data=preimage)
            except (UnicodeDecodeError, ValueError) as error:
                raise ValueError(
                    'verified baseline preimage is malformed'
                ) from error
            stamped = _frontmatter_field(lines=lines, key='verified_hash')
            if (
                not HEX64.fullmatch(stamped)
                or stamped != record.get('verified_hash')
                or stamped != _sha256_bytes(data=body)
            ):
                raise ValueError(
                    'verified baseline preimage has a stale verified_hash'
                )
    needed_preimages = {
        row.get('file')
        for row in exact_warnings
        if isinstance(row.get('file'), str)
        and row.get('file').startswith('1-wiki/')
    } | {
        row.get('page_path')
        for row in occurrences
        if isinstance(row, dict)
    }
    if not needed_preimages <= set(preimages):
        raise ValueError('warning baseline omits affected page preimages')
    target_paths = {
        row.get('target_path') for row in occurrences if isinstance(row, dict)
    }
    if not target_paths <= set(targets):
        raise ValueError('warning baseline target-page inventory is incomplete')
    seen_occurrences: set[str] = set()
    seen_physical_spans: set[Tuple[str, str, int, int]] = set()
    ordinals_by_group: Dict[Tuple[str, str, str], List[Tuple[int, int]]] = {}
    rebuilt_groups: Dict[Tuple[str, str], int] = {}
    order: List[Tuple[Any, Any, Any]] = []
    for occurrence in occurrences:
        if not isinstance(occurrence, dict):
            raise ValueError('warning baseline occurrence is malformed')
        validate_candidate(row=occurrence)
        occurrence_id = occurrence['occurrence_id']
        if occurrence_id in seen_occurrences:
            raise ValueError('warning baseline occurrence is duplicated')
        seen_occurrences.add(occurrence_id)
        page_record = preimages.get(occurrence['page_path'])
        if page_record is None:
            raise ValueError('warning baseline occurrence lacks page preimage')
        page_bytes = base64.b64decode(
            page_record['bytes_base64'], validate=True
        )
        if occurrence['page_preimage_sha256'] != page_record['sha256']:
            raise ValueError('warning baseline occurrence has wrong preimage')
        start = occurrence['start_byte']
        end = occurrence['end_byte']
        physical_span = (
            occurrence['page_path'],
            occurrence['page_preimage_sha256'],
            start,
            end,
        )
        if physical_span in seen_physical_spans:
            raise ValueError('warning baseline occurrence span is duplicated')
        seen_physical_spans.add(physical_span)
        if page_bytes[start:end] != occurrence['matched_text'].encode('utf-8'):
            raise ValueError('warning baseline occurrence span is stale')
        line_start = page_bytes.rfind(b'\n', 0, start) + 1
        line_end = page_bytes.find(b'\n', end)
        if line_end < 0:
            line_end = len(page_bytes)
        if _sha256_bytes(data=page_bytes[line_start:line_end]) != occurrence[
            'line_sha256'
        ]:
            raise ValueError('warning baseline occurrence line hash is stale')
        key = (occurrence['page_path'], occurrence['target_stem'])
        rebuilt_groups[key] = rebuilt_groups.get(key, 0) + 1
        ordinal_key = (
            occurrence['page_path'],
            occurrence['page_preimage_sha256'],
            occurrence['target_stem'],
        )
        ordinals_by_group.setdefault(ordinal_key, []).append(
            (start, occurrence['occurrence_ordinal'])
        )
        order.append(
            (
                occurrence['page_path'],
                occurrence['target_stem'],
                occurrence['start_byte'],
            )
        )
    for values in ordinals_by_group.values():
        ordered_ordinals = [
            ordinal for _, ordinal in sorted(values, key=lambda item: item[0])
        ]
        if ordered_ordinals != list(range(1, len(values) + 1)):
            raise ValueError(
                'warning baseline occurrence ordinals are noncontiguous'
            )
    if order != sorted(order) or rebuilt_groups != enumerated_groups:
        raise ValueError('warning baseline occurrence inventory is noncanonical')
    return root, baseline


def _frontmatter_and_body(data: bytes) -> Tuple[List[str], bytes]:
    text = data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    if not text.startswith('---\n'):
        raise ValueError('neutral page lacks opening frontmatter')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise ValueError('neutral page has malformed frontmatter')
    return text[4:end].splitlines(), text[end + 5 :].encode('utf-8')


def _frontmatter_field(lines: List[str], key: str) -> str:
    prefix = key + ':'
    values = [
        line.split(':', 1)[1].strip().strip('"\'')
        for line in lines
        if line.startswith(prefix)
    ]
    return values[0] if len(values) == 1 else ''


def _semantic_page_bytes(data: bytes) -> bytes:
    lines, body = _frontmatter_and_body(data=data)
    semantic = [
        line
        for line in lines
        if not line.startswith(('updated:', 'verified_hash:'))
    ]
    return ('---\n' + '\n'.join(semantic) + '\n---\n').encode('utf-8') + body


def _validate_ignore_additions(
    *,
    root: Path,
    baseline: Dict[str, Any],
    occurrence_rows: List[Dict[str, Any]],
    transaction_rows: List[Dict[str, Any]],
) -> List[str]:
    failures: List[str] = []
    initial = base64.b64decode(
        baseline['ignore_file']['bytes_base64'], validate=True
    ).decode('utf-8')
    current = (root / IGNORE_PATH).read_text(encoding='utf-8')
    removed = Counter(initial.splitlines()) - Counter(current.splitlines())
    if removed:
        failures.append('ignore file removed a frozen standing-ignore entry')
    added = Counter(current.splitlines()) - Counter(initial.splitlines())
    actual = Counter(
        line for line, count in added.items() for _ in range(count) if line
    )
    preimages_by_sha: Dict[str, bytes] = {}
    for record in baseline['affected_page_preimages'].values():
        try:
            data = base64.b64decode(
                record.get('bytes_base64', ''), validate=True
            )
        except (AttributeError, TypeError, ValueError):
            continue
        preimages_by_sha[_sha256_bytes(data=data)] = data
    for transaction in transaction_rows:
        try:
            data = base64.b64decode(
                transaction.get('postimage_bytes_base64', ''), validate=True
            )
        except (AttributeError, TypeError, ValueError):
            continue
        preimages_by_sha[_sha256_bytes(data=data)] = data
    expected_entries: List[str] = []
    for row in occurrence_rows:
        entry = row.get('ignore_entry')
        if row.get('disposition') in {'accepted_suppression', 'graph_ignore'}:
            prefix = '- {} :: {} :: '.format(
                row.get('page_path'), row.get('target_stem')
            )
            if (
                not isinstance(entry, str)
                or not entry.startswith(prefix)
                or len(entry) <= len(prefix)
                or '\n' in entry
            ):
                failures.append(
                    'accepted ignore occurrence lacks its exact ignore entry'
                )
            else:
                expected_entries.append(entry)
                phrase = entry[len(prefix) :]
                page_bytes = preimages_by_sha.get(
                    str(row.get('page_preimage_sha256'))
                )
                if page_bytes is None:
                    try:
                        current = (root / str(row.get('page_path'))).read_bytes()
                    except OSError:
                        current = b''
                    if _sha256_bytes(data=current) == row.get(
                        'page_preimage_sha256'
                    ):
                        page_bytes = current
                try:
                    text = page_bytes.decode('utf-8') if page_bytes else ''
                    pattern = re.compile(
                        r'\s+'.join(
                            re.escape(word) for word in phrase.split()
                        ),
                        re.IGNORECASE,
                    )
                    phrase_spans = [
                        (match.start(), match.end())
                        for match in pattern.finditer(text)
                    ]
                    start = int(row.get('start_byte'))
                    end = int(row.get('end_byte'))
                    row_start = len(page_bytes[:start].decode('utf-8'))
                    row_end = len(page_bytes[:end].decode('utf-8'))
                except (TypeError, ValueError, UnicodeDecodeError, re.error):
                    failures.append(
                        'accepted ignore occurrence has unprovable phrase coverage'
                    )
                    continue
                if sum(
                    phrase_start <= row_start and row_end <= phrase_end
                    for phrase_start, phrase_end in phrase_spans
                ) != 1:
                    failures.append(
                        'accepted ignore entry does not cover exactly its occurrence'
                    )
                    continue
                covered_ids = {
                    candidate.get('occurrence_id')
                    for candidate in occurrence_rows
                    if candidate.get('page_path') == row.get('page_path')
                    and candidate.get('target_stem') == row.get('target_stem')
                    and candidate.get('page_preimage_sha256')
                    == row.get('page_preimage_sha256')
                    and any(
                        phrase_start
                        <= len(
                            page_bytes[
                                : int(candidate.get('start_byte'))
                            ].decode('utf-8')
                        )
                        and len(
                            page_bytes[
                                : int(candidate.get('end_byte'))
                            ].decode('utf-8')
                        )
                        <= phrase_end
                        for phrase_start, phrase_end in phrase_spans
                    )
                }
                if covered_ids != {row.get('occurrence_id')}:
                    failures.append(
                        'accepted ignore entry covers another occurrence'
                    )
        elif entry is not None:
            failures.append('non-ignore occurrence carries an ignore entry')
    if actual != Counter(expected_entries):
        failures.append('ignore file contains unaccounted additions')
    return failures


def _validate_neutral_transactions(
    *,
    root: Path,
    baseline: Dict[str, Any],
    occurrence_rows: List[Dict[str, Any]],
    transaction_rows: List[Dict[str, Any]],
    ledger_rows: List[Dict[str, Any]],
    run_id: Any,
    used_row_ids: set,
) -> List[str]:
    failures: List[str] = []
    baseline_occurrences = {
        row['occurrence_id']: row
        for row in baseline['enumerator']['occurrences']
    }
    wraps_by_page: Dict[str, List[Dict[str, Any]]] = {}
    for row in occurrence_rows:
        baseline_id = row.get('rekeyed_from', row.get('occurrence_id'))
        frozen = baseline_occurrences.get(baseline_id)
        if row.get('disposition') != 'genuine_wrap' or frozen is None:
            continue
        wraps_by_page.setdefault(frozen['page_path'], []).append(frozen)

    transactions_by_page: Dict[str, Dict[str, Any]] = {}
    for index, row in enumerate(transaction_rows, 1):
        label = 'neutral_page_transactions row {}'.format(index)
        _validate_nested_identity(
            row=row,
            label=label,
            run_id=run_id,
            used_row_ids=used_row_ids,
            failures=failures,
        )
        page_path = row.get('page_path')
        if page_path in transactions_by_page or page_path not in wraps_by_page:
            failures.append('{} is duplicate or unplanned'.format(label))
            continue
        transactions_by_page[page_path] = row

    if set(transactions_by_page) != set(wraps_by_page):
        failures.append('genuine-wrap neutral transaction inventory is incomplete')
    for page_path, wraps in wraps_by_page.items():
        row = transactions_by_page.get(page_path)
        if row is None:
            continue
        preimage_record = baseline['affected_page_preimages'][page_path]
        preimage = base64.b64decode(
            preimage_record['bytes_base64'], validate=True
        )
        initial_status = preimage_record.get('status')
        if (
            row.get('preimage_sha256') != preimage_record['sha256']
            or initial_status not in {'verified', 'draft', 'needs-update'}
            or row.get('before_status') != initial_status
            or row.get('after_status') != initial_status
        ):
            failures.append(
                'neutral transaction does not preserve preimage status'
            )
        expected_ids = [
            item['occurrence_id']
            for item in sorted(
                wraps,
                key=lambda item: (
                    item['target_stem'], item['start_byte'], item['occurrence_id']
                ),
            )
        ]
        if row.get('baseline_occurrence_ids') != expected_ids:
            failures.append('neutral transaction occurrence inventory differs')
        replay = preimage
        previous_start = len(replay) + 1
        for frozen in sorted(
            wraps, key=lambda item: item['start_byte'], reverse=True
        ):
            start = frozen['start_byte']
            end = frozen['end_byte']
            matched = frozen['matched_text'].encode('utf-8')
            if end > previous_start or replay[start:end] != matched:
                failures.append('neutral transaction has stale/overlapping span')
                break
            replacement = (
                '[[{}|{}]]'.format(
                    frozen['target_path'], frozen['matched_text']
                )
            ).encode('utf-8')
            replay = replay[:start] + replacement + replay[end:]
            previous_start = start
        try:
            postimage = base64.b64decode(
                row.get('postimage_bytes_base64', ''), validate=True
            )
        except (TypeError, ValueError):
            failures.append('neutral transaction postimage bytes are invalid')
            continue
        retained = (root / page_path).read_bytes()
        try:
            post_lines, post_body = _frontmatter_and_body(data=postimage)
            replay_lines, replay_body = _frontmatter_and_body(data=replay)
        except (UnicodeDecodeError, ValueError) as error:
            failures.append('neutral transaction page is malformed: {}'.format(error))
            continue
        if _semantic_page_bytes(data=postimage) != _semantic_page_bytes(
            data=replay
        ):
            failures.append('neutral transaction postimage differs from replay')
        post_status = _frontmatter_field(lines=post_lines, key='status')
        post_hash = _frontmatter_field(
            lines=post_lines, key='verified_hash'
        )
        replay_status = _frontmatter_field(lines=replay_lines, key='status')
        if (
            row.get('postimage_sha256') != _sha256_bytes(data=postimage)
            or post_status != initial_status
            or replay_status != initial_status
        ):
            failures.append('neutral transaction postimage/status does not match')
        if initial_status == 'verified':
            if (
                row.get('verified_hash') != post_hash
                or post_hash != _sha256_bytes(data=post_body)
            ):
                failures.append('neutral transaction verified hash does not match')
        elif row.get('verified_hash') is not None or post_hash:
            failures.append('non-verified neutral transaction carries a hash')
        later_scope_rows = [
            item
            for item in ledger_rows
            if item.get('page_path') == page_path
            and item.get('row_type') in {'claim', 'page_reader', 'status_write'}
        ]
        if not later_scope_rows and retained != postimage:
            failures.append('neutral-only final page differs from transaction')
    return failures


def _validate_review_target_context(
    *,
    root: Path,
    baseline: Dict[str, Any],
    occurrence_rows: List[Dict[str, Any]],
    transaction_rows: List[Dict[str, Any]],
) -> List[str]:
    """Reject a reader slate whose target bytes changed without exact replay."""
    failures: List[str] = []
    transactions = {
        row.get('page_path'): row for row in transaction_rows
    }
    for row in occurrence_rows:
        if row.get('review_kind') not in REVIEW_KINDS:
            continue
        target_path = row.get('target_path')
        baseline_sha = baseline['target_page_hashes'].get(target_path)
        try:
            current_sha = _sha256_bytes(
                data=(root / target_path).read_bytes()
            )
        except (OSError, TypeError):
            failures.append('suppression target page is missing at completion')
            continue
        if current_sha == baseline_sha:
            continue
        transaction = transactions.get(target_path)
        if (
            transaction is None
            or transaction.get('preimage_sha256') != baseline_sha
            or transaction.get('postimage_sha256') != current_sha
        ):
            failures.append(
                'suppression reader target bytes differ from frozen context'
            )
    return failures


def _validate_exact_worklist(
    *,
    reconciliation: dict[str, Any],
    run_id: Any,
    ledger_rows: list[dict[str, Any]],
    root: Path,
    baseline: Dict[str, Any],
) -> tuple[list[str], dict[str, int]]:
    """Validate exact Warning closure and every suppression reader quorum."""
    failures: list[str] = []
    warning_rows = _exact_rows(
        reconciliation=reconciliation,
        key='warning_fingerprints',
        fields=WARNING_ROW_FIELDS,
        failures=failures,
    )
    occurrence_rows = _exact_occurrence_rows(
        reconciliation=reconciliation, failures=failures
    )
    batch_rows = _exact_rows(
        reconciliation=reconciliation,
        key='suppression_batches',
        fields=BATCH_ROW_FIELDS,
        failures=failures,
    )
    reader_rows = _exact_rows(
        reconciliation=reconciliation,
        key='suppression_reader_verdicts',
        fields=READER_ROW_FIELDS,
        failures=failures,
    )
    transaction_rows = _exact_rows(
        reconciliation=reconciliation,
        key='neutral_page_transactions',
        fields=NEUTRAL_TRANSACTION_FIELDS,
        failures=failures,
    )

    used_row_ids = {
        row.get('row_id')
        for row in ledger_rows
        if isinstance(row.get('row_id'), str)
    }
    warning_ids: set[str] = set()
    for index, row in enumerate(warning_rows, 1):
        label = f'warning_fingerprints row {index}'
        _validate_nested_identity(
            row=row,
            label=label,
            run_id=run_id,
            used_row_ids=used_row_ids,
            failures=failures,
        )
        if row.get('origin') not in ORIGINS:
            failures.append(f'{label} has invalid origin')
        if (
            not isinstance(row.get('check_id'), str)
            or not row['check_id'].strip()
            or not _canonical_report_path(value=row.get('page_path'))
            or not isinstance(row.get('target'), str)
            or not HEX64.fullmatch(str(row.get('message_sha256')))
        ):
            failures.append(f'{label} has malformed Warning identity fields')
        warning_id = row.get('warning_id')
        if (
            not isinstance(warning_id, str)
            or not HEX64.fullmatch(warning_id)
            or warning_id != expected_warning_id(row=row)
            or warning_id in warning_ids
        ):
            failures.append(f'{label} has invalid or duplicate warning_id')
        else:
            warning_ids.add(warning_id)
        if row.get('disposition') not in NONMENTION_DISPOSITIONS:
            failures.append(f'{label} has nonterminal disposition')
        if (
            not isinstance(row.get('resolution'), str)
            or not row['resolution'].strip()
        ):
            failures.append(f'{label} lacks resolution evidence')

    expected_initial_warnings = baseline['warning_fingerprints']
    actual_initial_warnings = [
        {key: row.get(key) for key in WARNING_ID_FIELDS}
        for row in warning_rows
        if row.get('origin') == 'initial'
    ]
    if actual_initial_warnings != expected_initial_warnings:
        failures.append(
            'initial Warning rows do not equal the frozen checker baseline'
        )

    occurrence_ids: set[str] = set()
    baseline_occurrences = {
        row.get('occurrence_id'): row
        for row in baseline['enumerator']['occurrences']
        if isinstance(row, dict)
    }
    ordinary_by_id: Dict[str, Dict[str, Any]] = {}
    superseded_by_id: Dict[str, Dict[str, Any]] = {}
    rekeyed_by_id: Dict[str, Dict[str, Any]] = {}
    for index, row in enumerate(occurrence_rows, 1):
        label = f'mention_occurrences row {index}'
        _validate_nested_identity(
            row=row,
            label=label,
            run_id=run_id,
            used_row_ids=used_row_ids,
            failures=failures,
        )
        candidate = {key: row.get(key) for key in CANDIDATE_FIELDS}
        try:
            validate_candidate(row=candidate)
        except ValueError as error:
            failures.append(f'{label} is not an exact occurrence: {error}')
        occurrence_id = row.get('occurrence_id')
        if not isinstance(occurrence_id, str):
            failures.append(f'{label} has invalid occurrence_id')
        elif occurrence_id in occurrence_ids:
            failures.append(f'{label} has duplicate occurrence_id')
        else:
            occurrence_ids.add(occurrence_id)
        if row.get('origin') not in ORIGINS:
            failures.append(f'{label} has invalid origin')
        if row.get('target_path') not in baseline['target_page_hashes']:
            failures.append(f'{label} target is absent from evidence context')
        disposition = row.get('disposition')
        if disposition not in (
            SEMANTIC_OCCURRENCE_DISPOSITIONS | TRANSITION_DISPOSITIONS
        ):
            failures.append(f'{label} has nonterminal disposition')
            semantic_disposition = None
        elif disposition == 'rekeyed':
            semantic_disposition = row.get('final_disposition')
            if semantic_disposition not in SEMANTIC_OCCURRENCE_DISPOSITIONS:
                failures.append(f'{label} has invalid final_disposition')
            rekeyed_by_id[str(occurrence_id)] = row
        elif disposition == 'superseded':
            semantic_disposition = None
            superseded_by_id[str(occurrence_id)] = row
        else:
            semantic_disposition = disposition
            ordinary_by_id[str(occurrence_id)] = row
        review_kind = row.get('review_kind')
        if review_kind not in REVIEW_KINDS | {'none'}:
            failures.append(f'{label} has invalid review_kind')
        if (
            review_kind == 'none'
            and semantic_disposition is not None
            and semantic_disposition
            not in UNREVIEWED_OCCURRENCE_DISPOSITIONS
        ):
            failures.append(
                f'{label} disposition requires a two-reader review'
            )
        if (
            not isinstance(row.get('resolution'), str)
            or not row['resolution'].strip()
        ):
            failures.append(f'{label} lacks resolution evidence')
        if disposition == 'superseded' and (
            review_kind != 'none' or row.get('ignore_entry') is not None
        ):
            failures.append(f'{label} superseded row carries semantic output')

    effective_rows: List[Dict[str, Any]] = []
    expected_row_ids: List[str] = []
    consumed_rekeyed: set[str] = set()
    stable_fields = (
        'check_id',
        'page_path',
        'target_path',
        'target_stem',
        'matched_text',
        'callout_id',
        'occurrence_ordinal',
    )
    for baseline_id, frozen in baseline_occurrences.items():
        ordinary = ordinary_by_id.get(baseline_id)
        old = superseded_by_id.get(baseline_id)
        if ordinary is not None and old is None:
            if ordinary.get('origin') != 'initial' or any(
                ordinary.get(key) != frozen.get(key)
                for key in CANDIDATE_FIELDS
            ):
                failures.append(
                    'initial ordinary occurrence differs from frozen baseline'
                )
            effective_rows.append(ordinary)
            expected_row_ids.append(ordinary['occurrence_id'])
            continue
        if old is None or ordinary is not None:
            failures.append(
                'initial occurrence rows do not cover the frozen enumerator baseline'
            )
            continue
        if old.get('origin') != 'initial' or any(
            old.get(key) != frozen.get(key) for key in CANDIDATE_FIELDS
        ):
            failures.append('superseded row differs from frozen baseline identity')
        new_id = old.get('rekeyed_to')
        new = rekeyed_by_id.get(new_id)
        if (
            not isinstance(new_id, str)
            or new is None
            or new.get('rekeyed_from') != baseline_id
            or new.get('origin') != 'initial'
            or new_id in consumed_rekeyed
        ):
            failures.append('superseded/rekeyed transition is not reciprocal')
            continue
        consumed_rekeyed.add(new_id)
        if any(new.get(key) != frozen.get(key) for key in stable_fields):
            failures.append('rekeyed row changed frozen semantic identity')
        effective = dict(new)
        effective['disposition'] = new.get('final_disposition')
        effective_rows.append(effective)
        expected_row_ids.extend([baseline_id, new_id])

    introduced_rows = [
        row
        for row in ordinary_by_id.values()
        if row.get('origin') == 'introduced'
    ]
    if any(
        row.get('origin') != 'initial'
        for row in list(superseded_by_id.values())
        + list(rekeyed_by_id.values())
    ):
        failures.append('only frozen initial occurrences may be rekeyed')
    if set(rekeyed_by_id) != consumed_rekeyed:
        failures.append('rekeyed row lacks one reciprocal predecessor')
    for new_id in consumed_rekeyed:
        new = rekeyed_by_id[new_id]
        matching_transactions = [
            transaction
            for transaction in transaction_rows
            if transaction.get('page_path') == new.get('page_path')
            and transaction.get('postimage_sha256')
            == new.get('page_preimage_sha256')
        ]
        if len(matching_transactions) != 1:
            failures.append(
                'rekeyed occurrence preimage lacks one proven transaction postimage'
            )
            continue
        try:
            proven_preimage = base64.b64decode(
                matching_transactions[0].get('postimage_bytes_base64', ''),
                validate=True,
            )
        except (TypeError, ValueError):
            failures.append('rekeyed occurrence transaction bytes are invalid')
            continue
        start = new.get('start_byte')
        end = new.get('end_byte')
        matched = str(new.get('matched_text', '')).encode('utf-8')
        if (
            _sha256_bytes(data=proven_preimage)
            != new.get('page_preimage_sha256')
            or not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or proven_preimage[start:end] != matched
        ):
            failures.append('rekeyed occurrence span is absent from proven preimage')
            continue
        line_start = proven_preimage.rfind(b'\n', 0, start) + 1
        line_end = proven_preimage.find(b'\n', end)
        if line_end < 0:
            line_end = len(proven_preimage)
        if _sha256_bytes(
            data=proven_preimage[line_start:line_end]
        ) != new.get(
            'line_sha256'
        ):
            failures.append('rekeyed occurrence line hash is unproven')
    unmatched_initial = [
        row
        for occurrence_id, row in ordinary_by_id.items()
        if row.get('origin') == 'initial'
        and occurrence_id not in baseline_occurrences
    ]
    if unmatched_initial:
        failures.append('initial ordinary occurrence is absent from baseline')
    introduced_rows.sort(
        key=lambda row: (
            row.get('page_path'), row.get('target_stem'), row.get('start_byte')
        )
    )
    effective_rows.extend(introduced_rows)
    expected_row_ids.extend(row['occurrence_id'] for row in introduced_rows)
    effective_spans: set[Tuple[Any, Any, Any, Any]] = set()
    effective_ordinals: Dict[
        Tuple[Any, Any, Any], List[Tuple[Any, Any]]
    ] = {}
    for row in effective_rows:
        span = (
            row.get('page_path'),
            row.get('page_preimage_sha256'),
            row.get('start_byte'),
            row.get('end_byte'),
        )
        if span in effective_spans:
            failures.append('terminal occurrence physical span is duplicated')
        effective_spans.add(span)
        ordinal_key = (
            row.get('page_path'),
            row.get('page_preimage_sha256'),
            row.get('target_stem'),
        )
        effective_ordinals.setdefault(ordinal_key, []).append(
            (row.get('start_byte'), row.get('occurrence_ordinal'))
        )
    for values in effective_ordinals.values():
        ordered_ordinals = [
            ordinal for _, ordinal in sorted(values, key=lambda item: item[0])
        ]
        if ordered_ordinals != list(range(1, len(values) + 1)):
            failures.append('terminal occurrence ordinals are noncontiguous')
    if [row.get('occurrence_id') for row in occurrence_rows] != expected_row_ids:
        failures.append(
            'mention_occurrences are not in canonical ledger/transition order'
        )
    occurrences_by_id = {
        row['occurrence_id']: row for row in effective_rows
    }

    expected_batches: dict[tuple[str, int], dict[str, Any]] = {}
    occurrence_batch: dict[str, dict[str, Any]] = {}
    for review_kind in sorted(REVIEW_KINDS):
        candidates = [
            {key: row.get(key) for key in CANDIDATE_FIELDS}
            for row in effective_rows
            if row.get('review_kind') == review_kind
        ]
        try:
            built = build_batches(
                rows=candidates,
                review_kind=review_kind,
                evidence_context_sha256=baseline[
                    'evidence_context_sha256'
                ],
            )
        except ValueError as error:
            failures.append(
                f'{review_kind} candidates cannot form canonical batches: '
                f'{error}'
            )
            built = []
        for batch in built:
            expected_batches[(review_kind, batch['batch_number'])] = batch
            for occurrence_id in batch['occurrence_ids']:
                occurrence_batch[occurrence_id] = batch

    seen_batches: set[tuple[str, int]] = set()
    for index, row in enumerate(batch_rows, 1):
        label = f'suppression_batches row {index}'
        _validate_nested_identity(
            row=row,
            label=label,
            run_id=run_id,
            used_row_ids=used_row_ids,
            failures=failures,
        )
        number = row.get('batch_number')
        review_kind = row.get('review_kind')
        if (
            review_kind not in REVIEW_KINDS
            or isinstance(number, bool)
            or not isinstance(number, int)
            or number < 1
        ):
            failures.append(f'{label} has invalid batch identity')
            continue
        key = (review_kind, number)
        expected = expected_batches.get(key)
        if key in seen_batches or expected is None:
            failures.append(f'{label} is duplicate or unplanned')
            continue
        seen_batches.add(key)
        for field in (
            'input_sha256',
            'batch_digest',
            'size',
            'occurrence_ids',
        ):
            if row.get(field) != expected[field]:
                failures.append(
                    f'{label} {field} differs from maximal canonical batch'
                )
        if (
            row.get('evidence_context_sha256')
            != baseline['evidence_context_sha256']
        ):
            failures.append(f'{label} has stale evidence context')
    if seen_batches != set(expected_batches):
        failures.append('suppression batch inventory is incomplete')

    readers_by_occurrence: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(reader_rows, 1):
        label = f'suppression_reader_verdicts row {index}'
        _validate_nested_identity(
            row=row,
            label=label,
            run_id=run_id,
            used_row_ids=used_row_ids,
            failures=failures,
        )
        occurrence_id = row.get('occurrence_id')
        if not isinstance(occurrence_id, str):
            failures.append(f'{label} has invalid occurrence_id')
            continue
        occurrence = occurrences_by_id.get(occurrence_id)
        batch = occurrence_batch.get(occurrence_id)
        if occurrence is None or batch is None:
            failures.append(f'{label} references an unreviewed occurrence')
            continue
        if (
            row.get('review_kind') != occurrence.get('review_kind')
            or row.get('evidence_context_sha256')
            != baseline['evidence_context_sha256']
            or row.get('input_sha256') != batch['input_sha256']
            or row.get('batch_number') != batch['batch_number']
            or row.get('batch_digest') != batch['batch_digest']
        ):
            failures.append(f'{label} is not bound to its exact batch')
        role = row.get('reader_role')
        if role not in READER_ROLES or row.get('blind_to') != [
            READER_COUNTERPART.get(role)
        ]:
            failures.append(f'{label} lacks blind reader-role provenance')
        if (
            not isinstance(row.get('agent_id'), str)
            or not row['agent_id'].strip()
            or row['agent_id'] != row['agent_id'].strip()
            or row['agent_id'] == '...'
        ):
            failures.append(f'{label} has invalid agent identity')
        if (
            not isinstance(row.get('reader_run_id'), str)
            or not row['reader_run_id'].strip()
            or row['reader_run_id'] != row['reader_run_id'].strip()
            or row['reader_run_id'] == '...'
        ):
            failures.append(f'{label} has invalid reader_run_id')
        if row.get('verdict') not in {'hold', 'refute', 'cannot_confirm'}:
            failures.append(f'{label} has invalid verdict')
        if (
            row.get('question_version')
            != QUESTION_VERSIONS[occurrence['review_kind']]
        ):
            failures.append(f'{label} uses the wrong reader question')
        if (
            not isinstance(row.get('reasoning'), str)
            or not row['reasoning'].strip()
        ):
            failures.append(f'{label} lacks reasoning')
        readers_by_occurrence.setdefault(occurrence_id, []).append(row)

    reviewed_ids = set(occurrence_batch)
    if set(readers_by_occurrence) - reviewed_ids:
        failures.append('reader verdicts include an unplanned occurrence')
    for occurrence_id in sorted(reviewed_ids):
        occurrence = occurrences_by_id.get(occurrence_id)
        rows = readers_by_occurrence.get(occurrence_id, [])
        label = f'suppression review for {occurrence_id}'
        by_role = {row.get('reader_role'): row for row in rows}
        agents = {
            row.get('agent_id', '').strip()
            for row in rows
            if isinstance(row.get('agent_id'), str)
        }
        if len(rows) != 2 or set(by_role) != READER_ROLES:
            failures.append(f'{label} lacks exactly two reader roles')
            continue
        if len(agents) != 2:
            failures.append(f'{label} reader agents are not independent')
        reader_runs = {
            row.get('reader_run_id', '').strip()
            for row in rows
            if isinstance(row.get('reader_run_id'), str)
        }
        if len(reader_runs) != 2:
            failures.append(f'{label} reader runs are not independent')
        outcomes = {row.get('verdict') for row in rows}
        if outcomes == {'hold'}:
            expected_disposition = (
                'accepted_suppression'
                if occurrence.get('review_kind') == 'generic_suppression'
                else 'graph_ignore'
            )
        elif outcomes == {'refute'}:
            expected_disposition = (
                'genuine_wrap'
                if occurrence.get('review_kind') == 'generic_suppression'
                else 'graph_repair'
            )
        else:
            failures.append(f'{label} is split or contains CANNOT_CONFIRM')
            continue
        if occurrence.get('disposition') != expected_disposition:
            failures.append(
                f'{label} outcome contradicts terminal disposition'
            )

    failures.extend(
        _validate_ignore_additions(
            root=root,
            baseline=baseline,
            occurrence_rows=effective_rows,
            transaction_rows=transaction_rows,
        )
    )
    failures.extend(
        _validate_neutral_transactions(
            root=root,
            baseline=baseline,
            occurrence_rows=effective_rows,
            transaction_rows=transaction_rows,
            ledger_rows=ledger_rows,
            run_id=run_id,
            used_row_ids=used_row_ids,
        )
    )
    failures.extend(
        _validate_review_target_context(
            root=root,
            baseline=baseline,
            occurrence_rows=effective_rows,
            transaction_rows=transaction_rows,
        )
    )

    initial_nonmention = len(baseline['warning_fingerprints'])
    introduced_nonmention = sum(
        row.get('origin') == 'introduced' for row in warning_rows
    )
    initial_occurrences = baseline['enumerator']['occurrences']
    introduced_occurrences = [
        row for row in effective_rows if row.get('origin') == 'introduced'
    ]
    initial_groups = len(
        {
            (row.get('page_path'), row.get('target_stem'))
            for row in initial_occurrences
        }
    )
    introduced_groups = len(
        {
            (row.get('page_path'), row.get('target_stem'))
            for row in introduced_occurrences
        }
    )
    exact_counts = {
        'initial_nonmention_warning_fingerprints': initial_nonmention,
        'introduced_nonmention_warning_fingerprints': introduced_nonmention,
        'terminal_nonmention_warning_fingerprints': len(warning_rows),
        'initial_mention_groups': initial_groups,
        'expanded_mention_occurrences': len(initial_occurrences),
        'introduced_mention_groups': introduced_groups,
        'introduced_mention_occurrences': len(introduced_occurrences),
        'terminal_mention_occurrences': len(effective_rows),
    }
    for key, expected in exact_counts.items():
        if reconciliation.get(key) != expected:
            failures.append(f'{key} does not match exact worklist rows')

    return failures, {
        'warning_fingerprints': len(warning_rows),
        'mention_occurrences': len(effective_rows),
        'mention_occurrence_rows': len(occurrence_rows),
        'suppression_batches': len(batch_rows),
        'suppression_reader_verdicts': len(reader_rows),
        'neutral_page_transactions': len(transaction_rows),
    }


def validate(
    report: Path, *, repo_root: Optional[Path] = None
) -> tuple[bool, dict[str, Any]]:
    frontmatter = _frontmatter(report=report)
    rows = _ledger_rows(report=report)
    scanners = [
        row
        for row in rows
        if row.get('row_type') == 'scanner'
        and row.get('scanner') == 'final_lint_post_bookkeeping'
    ]
    reconciliations = [
        row for row in rows if row.get('row_type') == 'reconciliation'
    ]
    if not scanners:
        raise ValueError('final_lint_post_bookkeeping scanner row missing')
    if not reconciliations:
        raise ValueError('reconciliation row missing')

    scanner = scanners[-1]
    reconciliation = reconciliations[-1]
    root, baseline = _load_warning_baseline(
        report=report,
        repo_root=repo_root,
        reconciliation=reconciliation,
    )
    failures: list[str] = []
    if len(scanners) != 1:
        failures.append(
            'report does not contain exactly one final scanner row'
        )
    if len(reconciliations) != 1:
        failures.append(
            'report does not contain exactly one reconciliation row'
        )
    if frontmatter.get('type') != 'audit':
        failures.append('frontmatter type is not audit')
    if frontmatter.get('result') not in {'complete', 'unconverged'}:
        failures.append('frontmatter result is not terminal')
    for key in ('pending', 'markers_pending'):
        value = frontmatter.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            failures.append(f'frontmatter {key} is not numeric')
    inherited_value = frontmatter.get('inherited_cleared')
    inherited_match = (
        re.fullmatch(r'(\d+)\s+of\s+(\d+)', inherited_value)
        if isinstance(inherited_value, str)
        else None
    )
    inherited_cleared = inherited_total = None
    if inherited_match is None:
        failures.append(
            'frontmatter inherited_cleared is not canonical "C of I"'
        )
    else:
        inherited_cleared = int(inherited_match.group(1))
        inherited_total = int(inherited_match.group(2))
        if inherited_cleared > inherited_total:
            failures.append('frontmatter inherited_cleared exceeds inherited')
        if inherited_cleared != inherited_total:
            failures.append(
                'frontmatter inherited markers are not all cleared'
            )
    if frontmatter.get('pending') != 0:
        failures.append('frontmatter pending is non-zero')
    if frontmatter.get('markers_pending') != 0:
        failures.append('frontmatter markers_pending is non-zero')
    if reconciliation.get('result') != frontmatter.get('result'):
        failures.append('frontmatter and reconciliation results do not match')

    scanner_run = scanner.get('run_id')
    reconciliation_run = reconciliation.get('run_id')
    if (
        not isinstance(scanner_run, str)
        or not scanner_run.strip()
        or scanner_run != scanner_run.strip()
        or scanner_run.strip() == '...'
        or scanner_run != reconciliation_run
    ):
        failures.append('final scanner and reconciliation run_id do not match')
    if scanner.get('target') != '1-wiki':
        failures.append('final scanner target is not 1-wiki')
    if scanner.get('status') != 0:
        failures.append('final scanner status is not 0')
    if scanner.get('lint_result') != 'clean':
        failures.append('final lint result is not clean')
    if _integer(row=scanner, key='audit_blocking_count') != 0:
        failures.append('final audit-blocking count is non-zero')
    if scanner.get('stdout_json') is not True:
        failures.append('final scanner stdout is not parseable JSON')
    if scanner.get('stderr_runtime_error') is not False:
        failures.append('final scanner has a runtime error')
    if scanner.get('terminal') is not True:
        failures.append('final scanner row is not terminal')
    for key in (
        'warning_count',
        'carried_warning_count',
        'introduced_warning_count',
        'stale_target_applications',
    ):
        if _integer(row=scanner, key=key) != 0:
            failures.append(f'{key} is non-zero')

    overall_pending = _integer(row=reconciliation, key='pending')
    initial = _integer(row=reconciliation, key='initial_warning_findings')
    nonmention = _integer(
        row=reconciliation, key='initial_nonmention_warning_fingerprints'
    )
    mention_groups = _integer(row=reconciliation, key='initial_mention_groups')
    expanded_mentions = _integer(
        row=reconciliation, key='expanded_mention_occurrences'
    )
    zero_match_defects = _integer(
        row=reconciliation, key='zero_match_scanner_defects'
    )
    introduced = _integer(
        row=reconciliation, key='introduced_warning_findings'
    )
    introduced_nonmention = _integer(
        row=reconciliation, key='introduced_nonmention_warning_fingerprints'
    )
    introduced_mention_groups = _integer(
        row=reconciliation, key='introduced_mention_groups'
    )
    introduced_mentions = _integer(
        row=reconciliation, key='introduced_mention_occurrences'
    )
    terminal_nonmention = _integer(
        row=reconciliation, key='terminal_nonmention_warning_fingerprints'
    )
    pending_nonmention = _integer(
        row=reconciliation, key='pending_nonmention_warning_fingerprints'
    )
    terminal_mentions = _integer(
        row=reconciliation, key='terminal_mention_occurrences'
    )
    pending_mentions = _integer(
        row=reconciliation, key='pending_mention_occurrences'
    )
    reconciliation_counts = {
        'pending': overall_pending,
        'initial_warning_findings': initial,
        'initial_nonmention_warning_fingerprints': nonmention,
        'initial_mention_groups': mention_groups,
        'expanded_mention_occurrences': expanded_mentions,
        'zero_match_scanner_defects': zero_match_defects,
        'introduced_warning_findings': introduced,
        'introduced_nonmention_warning_fingerprints': introduced_nonmention,
        'introduced_mention_groups': introduced_mention_groups,
        'introduced_mention_occurrences': introduced_mentions,
        'terminal_nonmention_warning_fingerprints': terminal_nonmention,
        'pending_nonmention_warning_fingerprints': pending_nonmention,
        'terminal_mention_occurrences': terminal_mentions,
        'pending_mention_occurrences': pending_mentions,
    }
    for key, value in reconciliation_counts.items():
        if value < 0:
            failures.append(f'{key} is negative')
    if overall_pending != 0:
        failures.append('ledger pending is non-zero')
    if pending_nonmention != 0:
        failures.append('pending non-mention Warning fingerprints is non-zero')
    if pending_mentions != 0:
        failures.append('pending mention occurrences is non-zero')
    if zero_match_defects != 0:
        failures.append('zero-match scanner defects is non-zero')
    if initial != nonmention + mention_groups:
        failures.append('initial Warning group arithmetic does not balance')
    if introduced != introduced_nonmention + introduced_mention_groups:
        failures.append('introduced Warning group arithmetic does not balance')
    if expanded_mentions < mention_groups:
        failures.append('initial mention groups were not fully expanded')
    if introduced_mentions < introduced_mention_groups:
        failures.append('introduced mention groups were not fully expanded')
    if (
        nonmention + introduced_nonmention
        != terminal_nonmention + pending_nonmention
    ):
        failures.append('non-mention Warning arithmetic does not balance')
    if (
        expanded_mentions + introduced_mentions
        != terminal_mentions + pending_mentions
    ):
        failures.append('mention occurrence arithmetic does not balance')
    worklist_failures, worklist_summary = _validate_exact_worklist(
        reconciliation=reconciliation,
        run_id=scanner_run,
        ledger_rows=rows,
        root=root,
        baseline=baseline,
    )
    failures.extend(worklist_failures)

    result = {
        'status': 'ok' if not failures else 'findings',
        'result': frontmatter.get('result'),
        'report': str(report),
        'failures': failures,
        'warning_count': scanner['warning_count'],
        'pending': overall_pending,
        'run_id': scanner_run,
        'inherited_markers': {
            'cleared': inherited_cleared,
            'inherited': inherited_total,
        },
        'exact_worklist': worklist_summary,
        'warning_group_census': {
            'initial': initial,
            'introduced': introduced,
            'initial_mention_groups': mention_groups,
            'introduced_mention_groups': introduced_mention_groups,
        },
        'nonmention_arithmetic': {
            'initial': nonmention,
            'introduced': introduced_nonmention,
            'terminal': terminal_nonmention,
            'pending': pending_nonmention,
        },
        'mention_arithmetic': {
            'groups': mention_groups,
            'expanded': expanded_mentions,
            'introduced': introduced_mentions,
            'terminal': terminal_mentions,
            'pending': pending_mentions,
            'zero_match_scanner_defects': zero_match_defects,
        },
    }
    return not failures, result


def _run_full_ledger_validator(
    report: Path, repo_root: Path
) -> subprocess.CompletedProcess[str]:
    validator = (
        repo_root
        / '.claude/skills/multi-skill/scripts/validate_verification_ledger.py'
    )
    if not validator.is_file():
        raise ValueError(f'full ledger validator missing: {validator}')
    return subprocess.run(
        [
            sys.executable,
            str(validator),
            str(report),
            '--repo-root',
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _full_ledger_is_clean(
    full: subprocess.CompletedProcess[str],
    *,
    expected_result: str,
) -> bool:
    """Require silent, parseable terminal success from the full validator."""
    if full.returncode != 0 or full.stderr.strip():
        return False
    try:
        payload = json.loads(full.stdout)
    except json.JSONDecodeError:
        return False
    return (
        isinstance(payload, dict)
        and expected_result in {'complete', 'unconverged'}
        and payload.get('result') == expected_result
        and payload.get('pending') == 0
    )


def _run_live_checker(checker: Path, wiki_root: Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(checker), str(wiki_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        findings = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise ValueError(
            'live final checker stdout is not parseable JSON'
        ) from error
    if not isinstance(findings, list) or any(
        not isinstance(finding, dict) for finding in findings
    ):
        raise ValueError('live final checker output is not a finding array')
    return {
        'status': proc.returncode,
        'warning_count': sum(
            finding.get('severity') == 'warning' for finding in findings
        ),
        'finding_count': len(findings),
        'stderr': proc.stderr.strip(),
    }


def _live_checker_is_clean(live: dict[str, Any]) -> bool:
    """Require a successful, Warning-free checker with silent stderr."""
    return (
        live.get('status') == 0
        and live.get('warning_count') == 0
        and live.get('stderr') == ''
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        valid, result = validate(
            report=args.report, repo_root=args.repo_root.resolve()
        )
        if valid:
            full = _run_full_ledger_validator(
                report=args.report, repo_root=args.repo_root.resolve()
            )
            result['full_ledger_validator_status'] = full.returncode
            result['full_ledger_validator_stdout'] = full.stdout.strip()
            result['full_ledger_validator_stderr'] = full.stderr.strip()
            if not _full_ledger_is_clean(
                full=full, expected_result=result['result']
            ):
                valid = False
                result['status'] = 'findings'
                result['failures'].append(
                    'final full-ledger validator failed, emitted stderr, or '
                    'returned nonterminal output'
                )
        if valid:
            root = args.repo_root.resolve()
            live = _run_live_checker(
                checker=root
                / '.claude/skills/multi-skill/scripts/check_wiki.py',
                wiki_root=root / '1-wiki',
            )
            result['live_final_checker'] = live
            if not _live_checker_is_clean(live=live):
                valid = False
                result['status'] = 'findings'
                result['failures'].append(
                    'live final checker failed, emitted stderr, or still has '
                    'Warnings'
                )
        print(json.dumps(result, sort_keys=True))
        return 0 if valid else 1
    except Exception as error:
        print(
            json.dumps(
                {'status': 'error', 'error': str(error)}, sort_keys=True
            )
        )
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
