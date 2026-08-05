#!/usr/bin/env python3
"""Build stable same-digest reader batches for suppression candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


MAX_BATCH_SIZE = 25
HEX64 = re.compile(r'^[0-9a-f]{64}$')
IDENTITY_FIELDS = (
    'check_id',
    'page_path',
    'page_preimage_sha256',
    'target_path',
    'target_stem',
    'matched_text',
    'start_byte',
    'end_byte',
    'line_sha256',
    'callout_id',
    'occurrence_ordinal',
)
CANDIDATE_FIELDS = frozenset((*IDENTITY_FIELDS, 'occurrence_id'))
REVIEW_KINDS = {'generic_suppression', 'graph_ignore'}


def _canonical_line(row: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            row,
            ensure_ascii=False,
            sort_keys=True,
            separators=(',', ':'),
        )
        + '\n'
    ).encode('utf-8')


def expected_occurrence_id(row: dict[str, Any]) -> str:
    payload = {key: row.get(key) for key in IDENTITY_FIELDS}
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def _canonical_repo_path(value: Any) -> bool:
    """Return whether value is a canonical relative path below 1-wiki/."""
    if not isinstance(value, str) or not value.startswith('1-wiki/'):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and '..' not in path.parts
        and path.as_posix() == value
    )


def validate_candidate(row: dict[str, Any]) -> None:
    """Validate one exact enumerator row with no coordinator-added fields."""
    missing = [key for key in IDENTITY_FIELDS if key not in row]
    if missing:
        raise ValueError(f'candidate is missing identity fields: {missing}')
    if 'occurrence_id' not in row:
        raise ValueError('candidate is missing occurrence_id')
    extra = sorted(set(row) - CANDIDATE_FIELDS)
    if extra:
        raise ValueError(f'candidate has unexpected fields: {extra}')
    if row['check_id'] != 'unlinked_page_mention':
        raise ValueError('candidate check_id is not unlinked_page_mention')
    for key in ('page_path', 'target_path'):
        value = row[key]
        if not _canonical_repo_path(value=value):
            raise ValueError(f'candidate {key} is not a wiki path')
    if PurePosixPath(row['target_path']).stem != row['target_stem']:
        raise ValueError('candidate target_path does not match target_stem')
    for key in ('page_preimage_sha256', 'line_sha256'):
        if not isinstance(row[key], str) or not HEX64.fullmatch(row[key]):
            raise ValueError(f'candidate {key} is not a SHA-256 digest')
    for key in ('target_stem', 'matched_text', 'callout_id'):
        if not isinstance(row[key], str) or not row[key]:
            raise ValueError(f'candidate {key} is empty or non-text')
    start = row['start_byte']
    end = row['end_byte']
    ordinal = row['occurrence_ordinal']
    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
        or start < 0
        or end <= start
    ):
        raise ValueError('candidate UTF-8 byte span is invalid')
    if (
        isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or ordinal < 1
    ):
        raise ValueError('candidate occurrence_ordinal is invalid')
    identity = row.get('occurrence_id')
    if not isinstance(identity, str) or not HEX64.fullmatch(identity):
        raise ValueError('candidate occurrence_id is not a SHA-256 digest')
    if identity != expected_occurrence_id(row=row):
        raise ValueError(
            'candidate occurrence_id does not match its identity fields'
        )


def expected_batch_digest(
    *,
    rows: list[dict[str, Any]],
    review_kind: str,
    evidence_context_sha256: str,
    input_sha256: str,
    batch_number: int,
) -> str:
    """Bind the exact candidate slate and its reader question together."""
    if review_kind not in REVIEW_KINDS:
        raise ValueError(f'invalid suppression review kind: {review_kind!r}')
    if (
        not isinstance(evidence_context_sha256, str)
        or not HEX64.fullmatch(evidence_context_sha256)
    ):
        raise ValueError('invalid evidence-context SHA-256')
    if not isinstance(input_sha256, str) or not HEX64.fullmatch(input_sha256):
        raise ValueError('invalid candidate-input SHA-256')
    if (
        isinstance(batch_number, bool)
        or not isinstance(batch_number, int)
        or batch_number < 1
    ):
        raise ValueError('invalid batch number')
    header = {
        'schema_version': 1,
        'review_kind': review_kind,
        'evidence_context_sha256': evidence_context_sha256,
        'input_sha256': input_sha256,
        'batch_number': batch_number,
    }
    payload = _canonical_line(row=header) + b''.join(
        _canonical_line(row=row) for row in rows
    )
    return hashlib.sha256(payload).hexdigest()


def expected_input_sha256(
    *,
    rows: list[dict[str, Any]],
    review_kind: str,
    evidence_context_sha256: str,
) -> str:
    """Hash the canonical header plus the full ordered candidate row stream."""
    if review_kind not in REVIEW_KINDS:
        raise ValueError(f'invalid suppression review kind: {review_kind!r}')
    if (
        not isinstance(evidence_context_sha256, str)
        or not HEX64.fullmatch(evidence_context_sha256)
    ):
        raise ValueError('invalid evidence-context SHA-256')
    header = {
        'schema_version': 1,
        'review_kind': review_kind,
        'evidence_context_sha256': evidence_context_sha256,
    }
    payload = _canonical_line(row=header) + b''.join(
        _canonical_line(row=row) for row in rows
    )
    return hashlib.sha256(payload).hexdigest()


def build_batches(
    *,
    rows: list[dict[str, Any]],
    review_kind: str = 'generic_suppression',
    evidence_context_sha256: str,
) -> list[dict[str, Any]]:
    if review_kind not in REVIEW_KINDS:
        raise ValueError(f'invalid suppression review kind: {review_kind!r}')
    for row in rows:
        validate_candidate(row=row)
    identities = [row.get('occurrence_id') for row in rows]
    if len(set(identities)) != len(identities):
        raise ValueError('candidate occurrence_id values are not unique')
    order = [
        (row['page_path'], row['target_stem'], row['start_byte'])
        for row in rows
    ]
    if order != sorted(order):
        raise ValueError(
            'candidates are not in canonical occurrence-ledger order'
        )

    input_sha256 = expected_input_sha256(
        rows=rows,
        review_kind=review_kind,
        evidence_context_sha256=evidence_context_sha256,
    )
    batches: list[dict[str, Any]] = []
    for offset in range(0, len(rows), MAX_BATCH_SIZE):
        batch_rows = rows[offset : offset + MAX_BATCH_SIZE]
        batches.append(
            {
                'batch_number': len(batches) + 1,
                'review_kind': review_kind,
                'evidence_context_sha256': evidence_context_sha256,
                'input_sha256': input_sha256,
                'batch_digest': expected_batch_digest(
                    rows=batch_rows,
                    review_kind=review_kind,
                    evidence_context_sha256=evidence_context_sha256,
                    input_sha256=input_sha256,
                    batch_number=len(batches) + 1,
                ),
                'size': len(batch_rows),
                'occurrence_ids': [row['occurrence_id'] for row in batch_rows],
                'rows': batch_rows,
            }
        )
    return batches


def _read_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(payload, dict):
        payload = payload.get('occurrences')
    if not isinstance(payload, list) or any(
        not isinstance(row, dict) for row in payload
    ):
        raise ValueError(
            'input must be an occurrence array or object with occurrences'
        )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument(
        '--review-kind',
        choices=sorted(REVIEW_KINDS),
        default='generic_suppression',
    )
    parser.add_argument('--evidence-context-sha256', required=True)
    args = parser.parse_args()
    try:
        rows = _read_rows(path=args.input)
        batches = build_batches(
            rows=rows,
            review_kind=args.review_kind,
            evidence_context_sha256=args.evidence_context_sha256,
        )
        input_sha256 = expected_input_sha256(
            rows=rows,
            review_kind=args.review_kind,
            evidence_context_sha256=args.evidence_context_sha256,
        )
        print(
            json.dumps(
                {
                    'status': 'ok',
                    'candidate_count': len(rows),
                    'input_sha256': input_sha256,
                    'batch_count': len(batches),
                    'max_batch_size': MAX_BATCH_SIZE,
                    'batches': batches,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 0
    except Exception as error:
        print(
            json.dumps(
                {'status': 'error', 'error': str(error)}, sort_keys=True
            )
        )
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
