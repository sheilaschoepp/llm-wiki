#!/usr/bin/env python3
"""Capture Audit's immutable, pre-edit Warning evidence baseline."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict


SCRIPT_DIR = Path(__file__).resolve().parent
CANONICAL_RULE_PATHS = (
    '.claude/skills/audit/references/unlinked-mention-occurrences.md',
    '.claude/skills/multi-skill/references/verification-neutral-fixes.md',
)
RELATIONSHIP_RULE_PATHS = (
    '.claude/skills/multi-skill/references/relationship-sweep.md',
)
IGNORE_PATH = (
    '.claude/skills/multi-skill/unlinked-mention-ignore.md'
)
CANONICAL_CHECKER_PATH = (
    '.claude/skills/multi-skill/scripts/check_wiki.py'
)
BASELINE_DIRECTORY = '2-outputs/audit/baselines'


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def _load_enumerator(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        'audit_capture_occurrence_enumerator', path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError('cannot load occurrence enumerator: {}'.format(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _run_checker(*, checker: Path, wiki_root: Path) -> Dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(checker), str(wiki_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.stderr.strip():
        raise RuntimeError(
            'initial checker emitted stderr: {}'.format(proc.stderr.strip())
        )
    if proc.returncode not in {0, 1}:
        raise RuntimeError(
            'initial checker failed with exit {}'.format(proc.returncode)
        )
    try:
        findings = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError('initial checker stdout is not JSON') from error
    if not isinstance(findings, list) or any(
        not isinstance(row, dict) for row in findings
    ):
        raise RuntimeError('initial checker output is not a finding array')
    return {'status': proc.returncode, 'findings': findings}


def _warning_fingerprint(finding: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'origin': 'initial',
        'check_id': finding.get('check_id'),
        'page_path': finding.get('file'),
        'target': finding.get('target', ''),
        'message_sha256': _sha256(
            data=str(finding.get('message', '')).encode('utf-8')
        ),
    }


def _frontmatter_value(*, text: str, key: str) -> str:
    match = re.search(
        r'^{}:\s*([^\n#]+)'.format(re.escape(key)), text, re.MULTILINE
    )
    return '' if match is None else match.group(1).strip().strip('"\'')


def _hash_paths(*, repo_root: Path, paths: tuple) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for relative in paths:
        path = repo_root / relative
        data = path.read_bytes()
        result[relative] = _sha256(data=data)
    return result


def _git_snapshot(*, repo_root: Path) -> Dict[str, Any]:
    head = subprocess.run(
        ['git', '-C', str(repo_root), 'rev-parse', 'HEAD'],
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ['git', '-C', str(repo_root), 'status', '--porcelain=v1', '-z'],
        capture_output=True,
        check=False,
    )
    return {
        'head': head.stdout.strip() if head.returncode == 0 else 'unavailable',
        'status_sha256': _sha256(data=status.stdout),
        'status_bytes_base64': base64.b64encode(status.stdout).decode('ascii'),
    }


def _dirty_paths(*, status_bytes: bytes) -> set:
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


def _trusted_checker_sha256(
    *, repo_root: Path, head: str, checker_path: Path
) -> str:
    if head == 'unavailable':
        return _sha256(data=checker_path.read_bytes())
    committed = subprocess.run(
        [
            'git',
            '-C',
            str(repo_root),
            'show',
            '{}:{}'.format(head, CANONICAL_CHECKER_PATH),
        ],
        capture_output=True,
        check=False,
    )
    if committed.returncode != 0:
        raise RuntimeError(
            'canonical checker is absent from the frozen Git HEAD'
        )
    trusted_sha = _sha256(data=committed.stdout)
    if trusted_sha != _sha256(data=checker_path.read_bytes()):
        raise RuntimeError('canonical checker differs from the frozen Git HEAD')
    return trusted_sha


def build_baseline(
    *, repo_root: Path, checker_path: Path, run_id: str, baseline_id: str
) -> Dict[str, Any]:
    """Build one complete baseline from current bytes without writing it."""
    git_snapshot = _git_snapshot(repo_root=repo_root)
    status_bytes = base64.b64decode(
        git_snapshot['status_bytes_base64'], validate=True
    )
    protected_dirty = _dirty_paths(status_bytes=status_bytes) & {
        CANONICAL_CHECKER_PATH,
    }
    if protected_dirty:
        raise RuntimeError(
            'baseline capture has dirty protected inputs: {}'.format(
                sorted(protected_dirty)
            )
        )
    trusted_checker_sha = _trusted_checker_sha256(
        repo_root=repo_root,
        head=git_snapshot['head'],
        checker_path=checker_path,
    )
    checker_result = _run_checker(
        checker=checker_path, wiki_root=repo_root / '1-wiki'
    )
    enumerator = _load_enumerator(
        path=SCRIPT_DIR / 'enumerate_unlinked_mentions.py'
    )
    checker = enumerator._load_checker(path=checker_path)
    enumeration = enumerator.enumerate_occurrences(
        checker=checker, wiki_root=repo_root / '1-wiki'
    )
    enumeration.update(
        {
            'status': 'ok',
            'mention_groups': len(enumeration['groups']),
            'exact_occurrences': len(enumeration['occurrences']),
        }
    )

    warning_findings = [
        finding
        for finding in checker_result['findings']
        if finding.get('severity') == 'warning'
    ]
    nonmention_findings = [
        finding
        for finding in warning_findings
        if finding.get('check_id') != 'unlinked_page_mention'
    ]
    affected_paths = {
        str(finding.get('file'))
        for finding in warning_findings
        if isinstance(finding.get('file'), str)
        and str(finding.get('file')).startswith('1-wiki/')
    }
    affected_paths.update(
        row['page_path'] for row in enumeration['occurrences']
    )
    page_preimages: Dict[str, Dict[str, Any]] = {}
    for relative in sorted(affected_paths):
        path = repo_root / relative
        data = path.read_bytes()
        text = data.decode('utf-8')
        page_preimages[relative] = {
            'sha256': _sha256(data=data),
            'bytes_base64': base64.b64encode(data).decode('ascii'),
            'status': _frontmatter_value(text=text, key='status'),
            'verified_hash': _frontmatter_value(
                text=text, key='verified_hash'
            ),
        }

    target_paths = []
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        target_paths.extend(
            path.relative_to(repo_root).as_posix()
            for path in (repo_root / '1-wiki' / folder).glob('*.md')
        )
    target_hashes = _hash_paths(
        repo_root=repo_root, paths=tuple(sorted(target_paths))
    )
    canonical_hashes = _hash_paths(
        repo_root=repo_root, paths=CANONICAL_RULE_PATHS
    )
    relationship_hashes = _hash_paths(
        repo_root=repo_root, paths=RELATIONSHIP_RULE_PATHS
    )
    ignore_bytes = (repo_root / IGNORE_PATH).read_bytes()
    evidence_context = {
        'canonical_rule_hashes': canonical_hashes,
        'relationship_rule_hashes': relationship_hashes,
        'target_page_hashes': target_hashes,
        'initial_ignore_sha256': _sha256(data=ignore_bytes),
    }
    return {
        'schema_version': 1,
        'kind': 'audit-warning-baseline',
        'run_id': run_id,
        'baseline_id': baseline_id,
        'git_pre_edit': git_snapshot,
        'checker': {
            'path': checker_path.relative_to(repo_root).as_posix(),
            'sha256': trusted_checker_sha,
            'status': checker_result['status'],
            'findings': checker_result['findings'],
            'warning_findings': warning_findings,
        },
        'warning_fingerprints': [
            _warning_fingerprint(finding=finding)
            for finding in nonmention_findings
        ],
        'enumerator': enumeration,
        'affected_page_preimages': page_preimages,
        'ignore_file': {
            'path': IGNORE_PATH,
            'sha256': _sha256(data=ignore_bytes),
            'bytes_base64': base64.b64encode(ignore_bytes).decode('ascii'),
        },
        'canonical_rule_hashes': canonical_hashes,
        'relationship_rule_hashes': relationship_hashes,
        'target_page_hashes': target_hashes,
        'evidence_context_sha256': _sha256(
            data=_canonical_json(value=evidence_context)
        ),
    }


def capture_baseline(
    *, output: Path, repo_root: Path, checker_path: Path, run_id: str
) -> Dict[str, Any]:
    """Exclusively create a canonical baseline; never replace an old one."""
    root = repo_root.resolve()
    checker = checker_path.resolve()
    canonical_checker = (root / CANONICAL_CHECKER_PATH).resolve()
    if checker != canonical_checker or not checker.is_file():
        raise ValueError('baseline capture requires the canonical checker')
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
        or run_id == '...'
    ):
        raise ValueError('baseline capture requires a non-placeholder run ID')
    output = output.resolve()
    expected_parent = (root / BASELINE_DIRECTORY).resolve()
    if output.parent != expected_parent or output.suffix != '.json':
        raise ValueError(
            'baseline output must be a JSON file directly under {}'.format(
                BASELINE_DIRECTORY
            )
        )
    baseline_id = uuid.uuid4().hex
    payload = build_baseline(
        repo_root=root,
        checker_path=checker,
        run_id=run_id,
        baseline_id=baseline_id,
    )
    encoded = _canonical_json(value=payload) + b'\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644
    )
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(encoded)
    except Exception:
        try:
            os.close(descriptor)
        except OSError:
            pass
        try:
            output.unlink()
        except OSError:
            pass
        raise
    return {
        'status': 'ok',
        'path': output.relative_to(repo_root).as_posix(),
        'sha256': _sha256(data=encoded),
        'baseline_id': baseline_id,
        'run_id': run_id,
        'warnings': len(payload['checker']['warning_findings']),
        'mention_groups': payload['enumerator']['mention_groups'],
        'mention_occurrences': payload['enumerator']['exact_occurrences'],
        'evidence_context_sha256': payload['evidence_context_sha256'],
    }


def main() -> int:
    default_repo = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--repo-root', type=Path, default=default_repo)
    parser.add_argument('--checker', type=Path)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    checker = (
        args.checker.resolve()
        if args.checker is not None
        else root / '.claude/skills/multi-skill/scripts/check_wiki.py'
    )
    output = args.output
    if not output.is_absolute():
        output = root / output
    try:
        result = capture_baseline(
            output=output,
            repo_root=root,
            checker_path=checker,
            run_id=args.run_id,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        print(json.dumps({'status': 'error', 'error': str(error)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
