#!/usr/bin/env python3
"""Exclusively freeze every maintained page before Audit content verification."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


HEX64 = re.compile(r'^[0-9a-f]{64}$')
MAINTAINED_FOLDERS = ('sources', 'entities', 'concepts', 'syntheses')


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _frontmatter_value(*, text: str, key: str) -> str:
    match = re.search(
        r'^{}:\s*([^\n#]+)'.format(re.escape(key)), text, re.MULTILINE
    )
    return '' if match is None else match.group(1).strip().strip('"\'')


def build_checkpoint(
    *, repo_root: Path, run_id: str, warning_baseline_sha256: str,
) -> dict[str, Any]:
    if (
        not isinstance(run_id, str)
        or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', run_id)
        or not HEX64.fullmatch(warning_baseline_sha256)
    ):
        raise ValueError('checkpoint identity is malformed')
    pages: dict[str, dict[str, Any]] = {}
    for folder in MAINTAINED_FOLDERS:
        for path in sorted((repo_root / '1-wiki' / folder).glob('*.md')):
            relative = path.relative_to(repo_root).as_posix()
            data = path.read_bytes()
            text = data.decode('utf-8')
            pages[relative] = {
                'sha256': _sha256(data=data),
                'bytes_base64': base64.b64encode(data).decode('ascii'),
                'status': _frontmatter_value(text=text, key='status'),
                'verified_hash': _frontmatter_value(
                    text=text, key='verified_hash'
                ),
            }
    return {
        'schema_version': 1,
        'kind': 'audit-preverification-page-checkpoint',
        'run_id': run_id,
        'warning_baseline_sha256': warning_baseline_sha256,
        'pages': pages,
    }


def capture_checkpoint(
    *, output: Path, repo_root: Path, run_id: str,
    warning_baseline_sha256: str,
) -> dict[str, Any]:
    root = repo_root.resolve()
    value = build_checkpoint(
        repo_root=root,
        run_id=run_id,
        warning_baseline_sha256=warning_baseline_sha256,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(output, flags, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            output.unlink()
        except OSError:
            pass
        raise
    data = output.read_bytes()
    return {
        'path': output.relative_to(root).as_posix(),
        'sha256': _sha256(data=data),
        'pages': len(value['pages']),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--warning-baseline-sha256', required=True)
    args = parser.parse_args()
    try:
        result = capture_checkpoint(
            output=args.output,
            repo_root=args.repo_root,
            run_id=args.run_id,
            warning_baseline_sha256=args.warning_baseline_sha256,
        )
    except (OSError, UnicodeDecodeError, ValueError) as error:
        print(f'capture_page_checkpoint: {error}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
