#!/usr/bin/env python3
"""Enumerate exact unlinked-page-mention spans with native-checker parity."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any


def _load_checker(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        'audit_native_check_wiki', path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot load checker: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _callout_id(body: str, char_start: int) -> str:
    lines = body.splitlines()
    line_index = body.count('\n', 0, char_start)
    if line_index >= len(lines) or not lines[line_index].startswith('>'):
        return 'body'
    first = line_index
    while first > 0 and lines[first - 1].startswith('>'):
        first -= 1
    last = line_index
    while last + 1 < len(lines) and lines[last + 1].startswith('>'):
        last += 1
    for line in lines[first : last + 1]:
        match = re.match(r'^>\s*\^([A-Za-z0-9_-]+)\s*$', line)
        if match:
            return match.group(1)
    return 'callout-unidentified'


def _native_groups(
    checker: Any, wiki_root: Path
) -> dict[tuple[str, str], int]:
    groups: dict[tuple[str, str], int] = {}
    for finding in checker.check_unlinked_page_mentions(wiki_root=wiki_root):
        if finding.get('check_id') != 'unlinked_page_mention':
            continue
        message = str(finding.get('message', ''))
        parsed = re.search(
            r'Existing page `([^`]+)` is mentioned unlinked (\d+)×', message
        )
        if not parsed:
            raise RuntimeError(f'cannot parse native finding: {finding!r}')
        groups[(str(finding.get('file', '')), parsed.group(1))] = int(
            parsed.group(2)
        )
    return groups


def enumerate_occurrences(checker: Any, wiki_root: Path) -> dict[str, Any]:
    repo_root = wiki_root.parent
    ignore_by_key: dict[tuple[str, str], list[int]] = {}
    for index, entry in enumerate(checker.UNLINKED_MENTION_IGNORE):
        ignore_by_key.setdefault((entry['page'], entry['target']), []).append(
            index
        )

    form_to_stem: dict[str, str] = {}
    own_forms: dict[str, set[str]] = {}
    page_paths: dict[str, Path] = {}
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            frontmatter, _ = checker.parse_frontmatter(
                text=page.read_text(encoding='utf-8')
            )
            forms = checker._display_forms_for(
                stem=page.stem, fm=frontmatter or {}
            )
            own_forms[page.stem] = forms
            page_paths[page.stem] = page
            for form in forms:
                form_to_stem.setdefault(form, page.stem)

    if not form_to_stem:
        return {
            'groups': [],
            'occurrences': [],
            'zero_match_scanner_defects': 0,
        }

    alternatives = '|'.join(
        re.escape(form) for form in sorted(form_to_stem, key=len, reverse=True)
    )
    mention_re = re.compile(
        r'(?<![\w-])(' + alternatives + r')(?![\w-])(?!\.\w)', re.IGNORECASE
    )
    occurrences: list[dict[str, Any]] = []
    expanded_groups: dict[tuple[str, str], int] = {}

    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            page_bytes = page.read_bytes()
            text = page_bytes.decode('utf-8')
            _, frontmatter_end = checker.parse_frontmatter(text=text)
            split_lines = text.split('\n')
            body_start_char = sum(
                len(line) + 1 for line in split_lines[: frontmatter_end + 1]
            )
            body = '\n'.join(split_lines[frontmatter_end + 1 :])
            scan = checker._mask_noscan_spans(text=body)
            scan = re.sub(
                r'"[^"\n]*"', lambda match: ' ' * len(match.group(0)), scan
            )
            scan = re.sub(
                r'(?m)^#[ ].*$', lambda match: ' ' * len(match.group(0)), scan
            )
            self_forms = own_forms.get(page.stem, set())
            page_rel = str(page.relative_to(repo_root))

            ignored_spans: dict[str, list[tuple[int, int, int]]] = {}
            for (ignore_page, ignore_target), indexes in ignore_by_key.items():
                if ignore_page != page_rel:
                    continue
                spans = ignored_spans.setdefault(ignore_target, [])
                for index in indexes:
                    spans.extend(
                        (match.start(), match.end(), index)
                        for match in checker.UNLINKED_MENTION_IGNORE[index][
                            'pattern'
                        ].finditer(scan)
                    )

            ordinals: dict[str, int] = {}
            page_sha = _sha256_bytes(data=page_bytes)
            for match in mention_re.finditer(scan):
                form = match.group(1).lower()
                target = form_to_stem.get(form)
                if target is None or target == page.stem or form in self_forms:
                    continue
                covering = [
                    index
                    for start, end, index in ignored_spans.get(target, ())
                    if start <= match.start() and match.end() <= end
                ]
                if covering:
                    continue

                ordinals[target] = ordinals.get(target, 0) + 1
                expanded_groups[(page_rel, target)] = (
                    expanded_groups.get((page_rel, target), 0) + 1
                )
                full_start_char = body_start_char + match.start()
                full_end_char = body_start_char + match.end()
                start_byte = len(text[:full_start_char].encode('utf-8'))
                end_byte = len(text[:full_end_char].encode('utf-8'))
                line_start = body.rfind('\n', 0, match.start()) + 1
                line_end = body.find('\n', match.end())
                if line_end < 0:
                    line_end = len(body)
                record = {
                    'check_id': 'unlinked_page_mention',
                    'page_path': page_rel,
                    'page_preimage_sha256': page_sha,
                    'target_path': str(
                        page_paths[target].relative_to(repo_root)
                    ),
                    'target_stem': target,
                    'matched_text': body[match.start() : match.end()],
                    'start_byte': start_byte,
                    'end_byte': end_byte,
                    'line_sha256': _sha256_bytes(
                        data=body[line_start:line_end].encode('utf-8')
                    ),
                    'callout_id': _callout_id(
                        body=body, char_start=match.start()
                    ),
                    'occurrence_ordinal': ordinals[target],
                }
                canonical = json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(',', ':'),
                )
                record['occurrence_id'] = _sha256_bytes(
                    data=canonical.encode('utf-8')
                )
                occurrences.append(record)

    native_groups = _native_groups(checker=checker, wiki_root=wiki_root)
    if native_groups != expanded_groups:
        raise RuntimeError(
            'native group parity failed: '
            + json.dumps(
                {
                    'native': {
                        f'{page}::{target}': count
                        for (page, target), count in native_groups.items()
                    },
                    'expanded': {
                        f'{page}::{target}': count
                        for (page, target), count in expanded_groups.items()
                    },
                },
                sort_keys=True,
            )
        )

    groups = [
        {'page_path': page, 'target_stem': target, 'exact_occurrences': count}
        for (page, target), count in sorted(expanded_groups.items())
    ]
    occurrences.sort(
        key=lambda row: (
            row['page_path'],
            row['target_stem'],
            row['start_byte'],
        )
    )
    return {
        'groups': groups,
        'occurrences': occurrences,
        'zero_match_scanner_defects': 0,
    }


def main() -> int:
    default_repo = Path(__file__).resolve().parents[4]
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, default=default_repo)
    parser.add_argument(
        '--checker',
        type=Path,
        default=default_repo
        / '.claude/skills/multi-skill/scripts/check_wiki.py',
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    try:
        checker = _load_checker(path=args.checker.resolve())
        result = enumerate_occurrences(
            checker=checker, wiki_root=repo_root / '1-wiki'
        )
        result.update(
            {
                'status': 'ok',
                'mention_groups': len(result['groups']),
                'exact_occurrences': len(result['occurrences']),
            }
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
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
