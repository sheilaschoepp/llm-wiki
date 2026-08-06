#!/usr/bin/env python3
"""Validate a report's verification-ledger JSONL without judging semantics."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote


START = '<!-- verification-ledger:start -->'
END = '<!-- verification-ledger:end -->'
HEX64 = re.compile(r'^[0-9a-f]{64}$')
GIT_OID = re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
VALID_RESULTS = {'complete', 'unconverged', 'incomplete'}
REQUIRED_ROLES = {'locator_bullet', 'entailment_bullet'}
BULLET_COUNTERPART = {
    'locator_bullet': 'entailment_bullet',
    'entailment_bullet': 'locator_bullet',
}
PAGE_ROLES = {'locator_page', 'entailment_argument_page'}
PAGE_COUNTERPART = {
    'locator_page': 'entailment_argument_page',
    'entailment_argument_page': 'locator_page',
}
PAGE_DEFECT_SCOPES = {'bullet_local', 'cross_bullet', 'page_only'}
PAGE_STATUSES = {'verified', 'draft', 'needs-update'}
MARKER_ACTIONS = {'none', 'added', 'retained', 'cleared'}
READY_EPOCH = re.compile(r'^READY\(\d+\)$')
PROCESS_MARKER = re.compile(
    r'(?m)^(> -[ \t]+)\*\[unverified\]\*[ \t]?'
)
MARKDOWN_FENCE = re.compile(
    r'^((?: {0,3}> ?)* {0,3})(`{3,}|~{3,})(.*)$'
)
MECHANICAL_FRONTMATTER_KEYS = {
    'created',
    'updated',
    'status',
    'verified_hash',
    'needs_update_reason',
}
CALLOUT_BULLET_START = re.compile(r'^> -\s+')
CALLOUT_HEADER = re.compile(r'^>\s*\[!([A-Za-z0-9_-]+)\]')
CALLOUT_ID = re.compile(r'^>\s*\^([A-Za-z0-9_-]+)\s*$')
CALLOUT_BOUNDARY = re.compile(r'^>\s*(?:$|\[!|!\[\[|\^[A-Za-z0-9_-]+\s*$)')
RAW_WIKILINK = re.compile(
    r'\[\[(0-raw/[^\]#|]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]'
)
RAW_LOCATOR_WIKILINK = re.compile(
    r'\[\[(0-raw/[^\]#|]+)#([^\]|]+)(?:\|([^\]]*))?\]\]'
)
WIKILINK_TARGET = re.compile(r'\[\[([^\]#|]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]')
TERMINAL_VERDICTS = {'hold', 'refute', 'cannot_confirm'}
VERIFICATION_SCOPES = {'ordinary', 'exhaustive_negative'}
QUANTIFIED_SCOPE_KEYS = {
    'raw_population',
    'population',
    'searched_members',
    'counterexamples',
    'search_summary',
}
EXHAUSTIVE_NEGATIVE = re.compile(
    r'\b(?:no|not|only|sole|without|absent|zero|none|neither|never|'
    r'lacks?|lacked|lacking|omits?|omitted|omitting|excludes?|excluded|'
    r'excluding)\b|'
    r'\bnone\s+of\b|\bneither\b|\bnever\b|\bwithout\s+any\b|'
    r'\bonly\s+(?:one|a\s+single|the\s+sole)\b|'
    r'\bjust\s+(?:one|a\s+single)\b|\b(?:an?\s+|the\s+)?absence\s+of\b|'
    r'\bzero\s+(?:source|stud(?:y|ie)|paper|experiment|evaluation|ablation|'
    r'measurement|result|benchmark|dataset|condition|task|run|analysis|'
    r'comparison)s?\b|'
    r'\bno\s+(?:source|stud(?:y|ie)|paper|experiment|evaluation|ablation|'
    r'measurement|evidence|result|benchmark|dataset|condition|task|run|'
    r'analysis|comparison)s?\b|'
    r'\b(?:does|do|did|is|are|was|were)\s+not\s+'
    r'(?:measure|report|include|evaluate|test|perform|run|contain|use)\b|'
    r'\b(?:lack(?:s|ed)?|omit(?:s|ted)?|exclude[sd]?|fail(?:s|ed)?\s+to)'
    r'\s+(?:report|include|measure|test|run|contain|use|an?|any|all|the)\b|'
    r'\b(?:all|every|each)\b.{0,80}\b(?:does|do|did)\s+not\b',
    re.IGNORECASE,
)
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
REQUIRED_CLAIM_DISPOSITIONS = {
    'reused_hold',
    'backfilled_hold',
    'refute',
    'cannot_confirm',
    'invalidated',
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
LOCATOR_COORDINATE_KEYS = (
    'physical_page',
    'physical_page_start',
    'physical_page_end',
    'printed_page',
    'printed_page_start',
    'printed_page_end',
    'structural_anchor',
)
MAINTAINED_WIKI_FOLDERS = ('sources', 'entities', 'concepts', 'syntheses')
AUDIT_BASELINE_DIRECTORY = PurePosixPath('2-outputs/audit/baselines')
NEUTRAL_TRANSACTION_FIELDS = {
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


class LedgerError(ValueError):
    """A deterministic ledger validation failure."""


def markdown_fence_match(
    line: str, fence_character: str | None
) -> re.Match[str] | None:
    """Match a CommonMark fence; backtick info strings cannot use backticks."""
    fence = MARKDOWN_FENCE.match(line)
    if (
        fence is not None
        and fence_character is None
        and fence.group(2)[0] == '`'
        and '`' in fence.group(3)
    ):
        return None
    return fence


def mask_inline_code_spans(line: str) -> str:
    """Blank complete same-length backtick spans on one physical line."""
    masked = list(line)
    index = 0
    while index < len(line):
        if line[index] != '`':
            index += 1
            continue
        run_end = index + 1
        while run_end < len(line) and line[run_end] == '`':
            run_end += 1
        run_length = run_end - index
        search = run_end
        closing_end = -1
        while search < len(line):
            next_tick = line.find('`', search)
            if next_tick < 0:
                break
            candidate_end = next_tick + 1
            while candidate_end < len(line) and line[candidate_end] == '`':
                candidate_end += 1
            if candidate_end - next_tick == run_length:
                closing_end = candidate_end
                break
            search = candidate_end
        if closing_end < 0:
            index = run_end
            continue
        masked[index:closing_end] = ' ' * (closing_end - index)
        index = closing_end
    return ''.join(masked)


def html_comment_state(line: str, in_comment: bool) -> bool:
    """Return HTML-comment state, ignoring delimiters in inline code."""
    scan = line if in_comment else mask_inline_code_spans(line=line)
    position = 0
    while position < len(scan):
        if in_comment:
            closing = scan.find('-->', position)
            if closing < 0:
                return True
            in_comment = False
            position = closing + len('-->')
            scan = scan[:position] + mask_inline_code_spans(
                line=scan[position:]
            )
            continue
        opening = scan.find('<!--', position)
        if opening < 0:
            return False
        in_comment = True
        position = opening + len('<!--')
    return in_comment


def strip_html_comments_from_line(
    line: str, in_comment: bool
) -> tuple[str, bool]:
    """Remove only HTML-comment spans while retaining visible Markdown."""
    visible: list[str] = []
    position = 0
    while position < len(line):
        if in_comment:
            closing = line.find('-->', position)
            if closing < 0:
                return ''.join(visible), True
            in_comment = False
            position = closing + len('-->')
            continue
        masked = mask_inline_code_spans(line=line[position:])
        opening = masked.find('<!--')
        if opening < 0:
            visible.append(line[position:])
            break
        visible.append(line[position : position + opening])
        in_comment = True
        position += opening + len('<!--')
    return ''.join(visible), in_comment


def _process_markers(text: str, *, remove: bool) -> tuple[str, int]:
    """Transform/count canonical markers while preserving fenced literals."""
    output: list[str] = []
    count = 0
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth = 0
    in_html_comment = False
    for line in text.splitlines(keepends=True):
        if in_html_comment:
            in_html_comment = html_comment_state(
                line=line, in_comment=True
            )
            output.append(line)
            continue
        fence = markdown_fence_match(
            line=line, fence_character=fence_character
        )
        if fence:
            quote_depth = fence.group(1).count('>')
            marker = fence.group(2)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                fence_quote_depth = quote_depth
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and quote_depth == fence_quote_depth
                and not fence.group(3).strip()
            ):
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
            output.append(line)
            continue
        if fence_character is None and PROCESS_MARKER.match(line):
            count += 1
            if remove:
                line = PROCESS_MARKER.sub(r'\1', line)
        output.append(line)
        if fence_character is None:
            in_html_comment = html_comment_state(
                line=line, in_comment=False
            )
    return ''.join(output), count


def strip_process_marker(text: str) -> str:
    """Remove only a marker in the canonical callout-bullet position."""
    transformed, _ = _process_markers(text=text, remove=True)
    return transformed


def count_process_markers(text: str) -> int:
    """Count canonical process markers outside Markdown fences."""
    _, count = _process_markers(text=text, remove=False)
    return count


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')


def semantic_page_digest(page: Path) -> str:
    """Hash semantic page text while ignoring terminal audit bookkeeping."""
    text = page.read_text(encoding='utf-8')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if text.startswith('---\n'):
        end = text.find('\n---\n', 4)
        if end < 0:
            raise LedgerError(f'page frontmatter is unclosed: {page}')
        semantic_frontmatter = []
        for line in text[4:end].splitlines():
            match = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):', line)
            if match and match.group(1) in MECHANICAL_FRONTMATTER_KEYS:
                continue
            semantic_frontmatter.append(line)
        body = text[end + len('\n---\n') :]
        text = '---\n' + '\n'.join(semantic_frontmatter) + '\n---\n' + body
    canonical = strip_process_marker(text=text)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verified_body_hash(page: Path) -> str:
    """Run the shared body-hash authority for one retained wiki page."""
    script = Path(__file__).with_name('body_hash.py')
    proc = subprocess.run(
        [sys.executable, str(script), str(page)],
        capture_output=True,
        text=True,
        check=False,
    )
    digest = proc.stdout.strip()
    if proc.returncode != 0 or not HEX64.fullmatch(digest):
        raise LedgerError(
            f'body hash failed for {page}: {proc.stderr.strip() or digest}'
        )
    return digest


def split_page(page: Path) -> tuple[dict[str, Any], str]:
    """Return minimal wiki frontmatter and LF-normalized retained body."""
    text = page.read_text(encoding='utf-8')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if not text.startswith('---\n'):
        return {}, text
    end = text.find('\n---\n', 4)
    if end < 0:
        raise LedgerError(f'page frontmatter is unclosed: {page}')
    frontmatter: dict[str, Any] = {}
    current_key: str | None = None
    for raw in text[4:end].splitlines():
        if not raw.strip() or raw.strip().startswith('#'):
            continue
        if raw.lstrip().startswith('- ') and current_key is not None:
            value = raw.lstrip()[2:].strip().strip('"').strip("'")
            existing = frontmatter.get(current_key)
            if isinstance(existing, list):
                existing.append(value)
            else:
                frontmatter[current_key] = [value]
            continue
        match = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', raw)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        current_key = key
        if not value:
            frontmatter[key] = []
        elif value.startswith('[') and value.endswith(']'):
            inner = value[1:-1].strip()
            parts = re.findall(r'"[^"]*"|\'[^\']*\'|[^,"\']+', inner)
            stripped = [part.strip().strip('"').strip("'") for part in parts]
            frontmatter[key] = (
                [item for item in stripped if item] if inner else []
            )
        else:
            frontmatter[key] = value.strip('"').strip("'")
    return frontmatter, text[end + len('\n---\n') :]


def retained_page_context(page: Path) -> dict[str, Any]:
    """Build the canonical, recomputable audit claim-context payload."""
    frontmatter, body = split_page(page=page)
    title = frontmatter.get('title')
    if not isinstance(title, str) or not title:
        heading = re.search(r'^#\s+(.+?)\s*$', body, flags=re.MULTILINE)
        title = heading.group(1) if heading else ''
    semantic_frontmatter = {
        key: value
        for key, value in frontmatter.items()
        if key not in MECHANICAL_FRONTMATTER_KEYS | {'type', 'title'}
    }
    return {
        'page_type': frontmatter.get('type', ''),
        'page_title': title,
        'semantic_frontmatter': semantic_frontmatter,
        'context_digest': semantic_page_digest(page=page),
    }


def maintained_wiki_pages(repo_root: Path) -> set[str]:
    """Return every maintained wiki page path in canonical repository form."""
    pages: set[str] = set()
    wiki_root = repo_root.resolve(strict=True) / '1-wiki'
    for folder_name in MAINTAINED_WIKI_FOLDERS:
        folder = wiki_root / folder_name
        if not folder.exists():
            continue
        for page in folder.glob('*.md'):
            resolved = page.resolve(strict=True)
            if wiki_root.parent not in resolved.parents:
                raise LedgerError(f'wiki page escapes repository: {page}')
            pages.add(resolved.relative_to(wiki_root.parent).as_posix())
    return pages


def changed_raw_paths(repo_root: Path) -> set[str]:
    """Return staged, unstaged, and untracked raw paths.

    Rename detection stays disabled so both sides remain visible.
    """
    root = repo_root.resolve(strict=True)
    probe = subprocess.run(
        ['git', '-C', str(root), 'rev-parse', '--is-inside-work-tree'],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != 'true':
        return set()
    commands = (
        ['diff', '--no-renames', '--name-only', '-z', '--', '0-raw'],
        [
            'diff',
            '--cached',
            '--no-renames',
            '--name-only',
            '-z',
            '--',
            '0-raw',
        ],
        ['ls-files', '--others', '--exclude-standard', '-z', '--', '0-raw'],
    )
    changed: set[str] = set()
    for arguments in commands:
        proc = subprocess.run(
            ['git', '-C', str(root), *arguments],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise LedgerError(
                f'git raw-drift query failed: {proc.stderr.decode().strip()}'
            )
        changed.update(
            item.decode('utf-8') for item in proc.stdout.split(b'\0') if item
        )
    return changed


def latest_path_commits(repo_root: Path) -> dict[str, str]:
    """Return each retained page/raw path's latest reachable commit OID."""
    root = repo_root.resolve(strict=True)
    proc = subprocess.run(
        [
            'git',
            '-C',
            str(root),
            'log',
            '--format=@@%H',
            '--name-only',
            '--',
            '0-raw',
            '1-wiki/sources',
            '1-wiki/entities',
            '1-wiki/concepts',
            '1-wiki/syntheses',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return {}
    commits: dict[str, str] = {}
    current_commit = ''
    for line in proc.stdout.splitlines():
        if line.startswith('@@'):
            current_commit = line[2:]
        elif (
            line.startswith(('0-raw/', '1-wiki/'))
            and line not in commits
            and GIT_OID.fullmatch(current_commit)
        ):
            commits[line] = current_commit
    return commits


def commit_is_ancestor_or_equal(
    repo_root: Path, older: str, newer: str
) -> bool:
    """Compare immutable commit topology, not editable dates/timestamps."""
    if older == newer:
        return True
    proc = subprocess.run(
        [
            'git',
            '-C',
            str(repo_root),
            'merge-base',
            '--is-ancestor',
            older,
            newer,
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode not in {0, 1}:
        raise LedgerError(
            'git commit-ancestry query failed: '
            f'{proc.stderr.decode().strip()}'
        )
    return proc.returncode == 0


def retained_page_links(text: str, page_paths: set[str]) -> set[str]:
    """Resolve canonical and unique bare links to maintained pages."""
    paths_by_stem: dict[str, set[str]] = defaultdict(set)
    for page_path in page_paths:
        paths_by_stem[Path(page_path).stem].add(page_path)
    resolved: set[str] = set()
    for target in WIKILINK_TARGET.findall(text):
        normalized = target.strip()
        if normalized in page_paths:
            resolved.add(normalized)
            continue
        with_suffix = f'{normalized}.md'
        if with_suffix in page_paths:
            resolved.add(with_suffix)
            continue
        if normalized.startswith(('0-raw/', '1-wiki/attachments/')):
            continue
        candidates = paths_by_stem.get(Path(normalized).stem, set())
        if len(candidates) == 1:
            resolved.update(candidates)
    return resolved


def retained_page_raw_closure(repo_root: Path) -> dict[str, set[str]]:
    """Return every maintained page's direct and transitive raw dependency set."""
    page_paths = maintained_wiki_pages(repo_root=repo_root)
    page_text = {
        page_path: resolve_repo_path(
            repo_root=repo_root, value=page_path
        ).read_text(encoding='utf-8')
        for page_path in page_paths
    }
    page_links = {
        page_path: retained_page_links(text=text, page_paths=page_paths)
        for page_path, text in page_text.items()
    }
    raw_closure = {
        page_path: set(RAW_WIKILINK.findall(text))
        for page_path, text in page_text.items()
    }
    while True:
        expanded = {
            page_path: raw_paths
            | {
                raw_path
                for dependency in page_links[page_path]
                for raw_path in raw_closure[dependency]
            }
            for page_path, raw_paths in raw_closure.items()
        }
        if expanded == raw_closure:
            return raw_closure
        raw_closure = expanded


def normalized_raw_manifest(
    value: Any, *, label: str
) -> list[dict[str, str]]:
    """Validate one exact sorted raw path/SHA manifest."""
    if not isinstance(value, list):
        raise LedgerError(f'{label} raw_manifest is not a list')
    manifest: list[dict[str, str]] = []
    for item in value:
        if (
            not isinstance(item, dict)
            or set(item) != {'raw_path', 'sha256'}
            or not isinstance(item.get('raw_path'), str)
            or not item['raw_path'].startswith('0-raw/')
            or not HEX64.fullmatch(str(item.get('sha256')))
        ):
            raise LedgerError(f'{label} raw_manifest is malformed')
        manifest.append(
            {'raw_path': item['raw_path'], 'sha256': item['sha256']}
        )
    if manifest != sorted(manifest, key=lambda item: item['raw_path']) or len(
        {item['raw_path'] for item in manifest}
    ) != len(manifest):
        raise LedgerError(f'{label} raw_manifest is not unique and sorted')
    return manifest


def _git_blob(
    *, repo_root: Path, revision: str, repo_path: str
) -> bytes | None:
    """Read one committed blob without consulting working-tree bytes."""
    proc = subprocess.run(
        ['git', '-C', str(repo_root), 'show', f'{revision}:{repo_path}'],
        capture_output=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _report_commit(repo_root: Path, report_path: str) -> str | None:
    """Return the newest HEAD-ancestor commit that changed a report."""
    proc = subprocess.run(
        [
            'git', '-C', str(repo_root), 'log', '-1', '--format=%H',
            'HEAD', '--', report_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = proc.stdout.strip()
    return commit if proc.returncode == 0 and GIT_OID.fullmatch(commit) else None


def _direct_report_type(report_path: str) -> str | None:
    """Return the only report type allowed for one exact direct path."""
    pure = PurePosixPath(report_path)
    parts = pure.parts
    if (
        report_path != pure.as_posix()
        or len(parts) != 3
        or parts[0] != '2-outputs'
        or parts[1] not in {'audit', 'ingest'}
        or pure.suffix != '.md'
    ):
        return None
    return 'audit' if parts[1] == 'audit' else 'ingest-report'


def _maintained_page_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    pure = PurePosixPath(value)
    parts = pure.parts
    if (
        value != pure.as_posix()
        or len(parts) != 3
        or parts[0] != '1-wiki'
        or parts[1] not in MAINTAINED_WIKI_FOLDERS
        or pure.suffix != '.md'
    ):
        return None
    return value


def _page_parts_from_bytes(
    data: bytes, *, label: str
) -> tuple[dict[str, str], str]:
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError as error:
        raise LedgerError(f'{label} is not UTF-8') from error
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if not text.startswith('---\n'):
        raise LedgerError(f'{label} lacks frontmatter')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise LedgerError(f'{label} frontmatter is unclosed')
    return parse_frontmatter(text), text[end + len('\n---\n') :]


def _semantic_digest_from_bytes(data: bytes, *, label: str) -> str:
    frontmatter, body = _page_parts_from_bytes(data, label=label)
    text = data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    end = text.find('\n---\n', 4)
    semantic_frontmatter = []
    for line in text[4:end].splitlines():
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):', line)
        if match and match.group(1) in MECHANICAL_FRONTMATTER_KEYS:
            continue
        semantic_frontmatter.append(line)
    canonical = (
        '---\n' + '\n'.join(semantic_frontmatter) + '\n---\n' + body
    )
    del frontmatter
    return hashlib.sha256(
        strip_process_marker(text=canonical).encode('utf-8')
    ).hexdigest()


def _neutral_semantic_bytes(data: bytes, *, label: str) -> bytes:
    """Remove only fields a neutral transaction is allowed to rewrite."""
    _page_parts_from_bytes(data, label=label)
    text = data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    end = text.find('\n---\n', 4)
    frontmatter = [
        line
        for line in text[4:end].splitlines()
        if not line.startswith(('updated:', 'verified_hash:'))
    ]
    body = text[end + len('\n---\n') :]
    return (
        '---\n' + '\n'.join(frontmatter) + '\n---\n' + body
    ).encode('utf-8')


def _status_proves_committed_page(
    *, row: dict[str, Any], page_data: bytes, epoch: str | None
) -> bool:
    """Validate proof-specific status semantics against its committed page."""
    page_path = _maintained_page_path(row.get('page_path'))
    generation = row.get('page_generation')
    if (
        page_path is None
        or not HEX64.fullmatch(str(generation))
        or row.get('pre_semantic_hash') != generation
        or row.get('post_semantic_hash') != generation
        or row.get('before_status') not in PAGE_STATUSES
        or row.get('after_status') != 'verified'
        or (epoch is not None and row.get('relationship_epoch') != epoch)
    ):
        return False
    pre_count = row.get('pre_marker_count')
    post_count = row.get('post_marker_count')
    action = row.get('marker_action')
    if (
        isinstance(pre_count, bool)
        or not isinstance(pre_count, int)
        or pre_count < 0
        or post_count != 0
        or action not in {'none', 'cleared'}
        or (action == 'none' and pre_count != 0)
        or (action == 'cleared' and pre_count <= 0)
    ):
        return False
    try:
        frontmatter, body = _page_parts_from_bytes(
            page_data, label=f'raw proof page {page_path}'
        )
        marker_count = count_process_markers(text=body)
        body_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        semantic_hash = _semantic_digest_from_bytes(
            page_data, label=f'raw proof page {page_path}'
        )
    except LedgerError:
        return False
    retained_hash = frontmatter.get('verified_hash')
    return (
        frontmatter.get('status') == 'verified'
        and marker_count == post_count
        and HEX64.fullmatch(str(retained_hash)) is not None
        and row.get('verified_hash') == retained_hash == body_hash
        and semantic_hash == generation
    )


def _neutral_edges_from_report(
    *,
    repo_root: Path,
    run_id: str,
    reconciliation: dict[str, Any],
) -> dict[tuple[str, str], tuple[str, set[str]]]:
    """Validate current Audit neutral edges from pre- to post-generation."""
    transactions = reconciliation.get('neutral_page_transactions', [])
    if not isinstance(transactions, list) or not transactions:
        return {}
    baseline_path = reconciliation.get('warning_baseline_path')
    pure_baseline = (
        PurePosixPath(baseline_path)
        if isinstance(baseline_path, str)
        else PurePosixPath('.')
    )
    if (
        not isinstance(baseline_path, str)
        or baseline_path != pure_baseline.as_posix()
        or pure_baseline.parent != AUDIT_BASELINE_DIRECTORY
        or pure_baseline.suffix != '.json'
    ):
        return {}
    baseline_file = repo_root / baseline_path
    try:
        baseline_data = baseline_file.read_bytes()
    except OSError:
        return {}
    expected_sha = reconciliation.get('warning_baseline_sha256')
    if (
        baseline_data is None
        or not HEX64.fullmatch(str(expected_sha))
        or hashlib.sha256(baseline_data).hexdigest() != expected_sha
    ):
        return {}
    try:
        baseline = json.loads(baseline_data)
    except json.JSONDecodeError:
        return {}
    if (
        not isinstance(baseline, dict)
        or baseline.get('schema_version') != 1
        or baseline.get('kind') != 'audit-warning-baseline'
        or baseline.get('run_id') != run_id
        or not isinstance(baseline.get('baseline_id'), str)
        or not baseline['baseline_id'].strip()
        or reconciliation.get('warning_baseline_id')
        != baseline['baseline_id']
        or reconciliation.get('evidence_context_sha256')
        != baseline.get('evidence_context_sha256')
    ):
        return {}
    preimages = baseline.get('affected_page_preimages')
    enumerator = baseline.get('enumerator')
    if (
        not isinstance(preimages, dict)
        or not isinstance(enumerator, dict)
        or not isinstance(enumerator.get('occurrences'), list)
    ):
        return {}
    occurrences = {
        row.get('occurrence_id'): row
        for row in enumerator['occurrences']
        if isinstance(row, dict) and isinstance(row.get('occurrence_id'), str)
    }
    closure_rows = reconciliation.get('mention_occurrences')
    if not isinstance(closure_rows, list):
        return {}
    closed_wraps: set[str] = set()
    for row in closure_rows:
        if not isinstance(row, dict):
            return {}
        if row.get('disposition') == 'genuine_wrap':
            closed_wraps.add(str(row.get('occurrence_id')))
        elif (
            row.get('disposition') == 'rekeyed'
            and row.get('final_disposition') == 'genuine_wrap'
            and isinstance(row.get('rekeyed_from'), str)
        ):
            closed_wraps.add(row['rekeyed_from'])
    edges: dict[tuple[str, str], tuple[str, set[str]]] = {}
    seen_rows: set[str] = set()
    for transaction in transactions:
        if (
            not isinstance(transaction, dict)
            or set(transaction) != NEUTRAL_TRANSACTION_FIELDS
            or transaction.get('schema_version') != 1
            or transaction.get('run_id') != run_id
            or not isinstance(transaction.get('row_id'), str)
            or not transaction['row_id'].strip()
            or transaction['row_id'] in seen_rows
        ):
            return {}
        seen_rows.add(transaction['row_id'])
        before_status = transaction.get('before_status')
        after_status = transaction.get('after_status')
        if before_status != after_status or before_status not in PAGE_STATUSES:
            return {}
        if before_status != 'verified':
            if transaction.get('verified_hash') is not None:
                return {}
            continue
        if not HEX64.fullmatch(str(transaction.get('verified_hash'))):
            return {}
        page_path = _maintained_page_path(transaction.get('page_path'))
        record = preimages.get(page_path) if page_path is not None else None
        ids = transaction.get('baseline_occurrence_ids')
        if (
            page_path is None
            or not isinstance(record, dict)
            or record.get('status') != 'verified'
            or not isinstance(ids, list)
            or not ids
            or len(set(ids)) != len(ids)
            or any(item not in occurrences or item not in closed_wraps for item in ids)
        ):
            return {}
        try:
            preimage = base64.b64decode(
                record.get('bytes_base64', ''), validate=True
            )
        except (TypeError, ValueError):
            return {}
        current_page = repo_root / page_path
        try:
            attested_postimage = base64.b64decode(
                transaction.get('postimage_bytes_base64', ''), validate=True
            )
            postimage = current_page.read_bytes()
        except (OSError, TypeError, ValueError):
            return {}
        if (
            record.get('sha256') != hashlib.sha256(preimage).hexdigest()
            or transaction.get('preimage_sha256') != record.get('sha256')
            or transaction.get('postimage_sha256')
            != hashlib.sha256(postimage).hexdigest()
            or attested_postimage != postimage
        ):
            return {}
        try:
            pre_frontmatter, pre_body = _page_parts_from_bytes(
                preimage, label=f'neutral preimage {page_path}'
            )
            post_frontmatter, post_body = _page_parts_from_bytes(
                postimage, label=f'neutral postimage {page_path}'
            )
        except LedgerError:
            return {}
        if (
            pre_frontmatter.get('status') != 'verified'
            or post_frontmatter.get('status') != 'verified'
            or count_process_markers(text=pre_body) != 0
            or count_process_markers(text=post_body) != 0
            or record.get('verified_hash')
            != hashlib.sha256(pre_body.encode('utf-8')).hexdigest()
            or transaction.get('verified_hash')
            != post_frontmatter.get('verified_hash')
            or transaction.get('verified_hash')
            != hashlib.sha256(post_body.encode('utf-8')).hexdigest()
        ):
            return {}
        ordered = sorted(
            (occurrences[item] for item in ids),
            key=lambda item: (
                item.get('target_stem'),
                item.get('start_byte'),
                item.get('occurrence_id'),
            ),
        )
        if [item.get('occurrence_id') for item in ordered] != ids:
            return {}
        replay = preimage
        previous_start = len(replay) + 1
        for occurrence in sorted(
            ordered, key=lambda item: item.get('start_byte'), reverse=True
        ):
            start = occurrence.get('start_byte')
            end = occurrence.get('end_byte')
            matched = occurrence.get('matched_text')
            target = _maintained_page_path(occurrence.get('target_path'))
            if (
                isinstance(start, bool)
                or not isinstance(start, int)
                or isinstance(end, bool)
                or not isinstance(end, int)
                or not isinstance(matched, str)
                or target is None
                or occurrence.get('page_path') != page_path
            ):
                return {}
            matched_bytes = matched.encode('utf-8')
            if (
                start < 0
                or end <= start
                or end > previous_start
                or replay[start:end] != matched_bytes
            ):
                return {}
            replacement = f'[[{target}|{matched}]]'.encode('utf-8')
            replay = replay[:start] + replacement + replay[end:]
            previous_start = start
        if _neutral_semantic_bytes(
            replay, label=f'neutral replay {page_path}'
        ) != _neutral_semantic_bytes(
            postimage, label=f'neutral postimage {page_path}'
        ):
            return {}
        pre_generation = _semantic_digest_from_bytes(
            preimage, label=f'neutral preimage {page_path}'
        )
        post_generation = _semantic_digest_from_bytes(
            postimage, label=f'neutral postimage {page_path}'
        )
        key = (page_path, post_generation)
        if key in edges:
            return {}
        edges[key] = (
            pre_generation,
            {
                str(occurrences[item]['target_path'])
                for item in ids
            },
        )
    return edges


def _committed_audit_completion_inputs_valid(
    *,
    repo_root: Path,
    report_commit: str,
    run_id: Any,
    rows: list[dict[str, Any]],
    reconciliation: dict[str, Any],
) -> bool:
    """Require the completion-only evidence before trusting an Audit proof."""
    scanners = [
        row
        for row in rows
        if row.get('row_type') == 'scanner'
        and row.get('scanner') == 'final_lint_post_bookkeeping'
    ]
    if len(scanners) != 1:
        return False
    scanner = scanners[0]
    if (
        scanner.get('run_id') != run_id
        or scanner.get('target') != '1-wiki'
        or scanner.get('status') != 0
        or scanner.get('lint_result') != 'clean'
        or scanner.get('audit_blocking_count') != 0
        or scanner.get('stdout_json') is not True
        or scanner.get('stderr_runtime_error') is not False
        or scanner.get('warning_count') != 0
        or scanner.get('terminal') is not True
        or reconciliation.get('planned_scanners') != 1
        or reconciliation.get('terminal_scanners') != 1
        or reconciliation.get('pending_scanners') != 0
    ):
        return False
    baseline_path = reconciliation.get('warning_baseline_path')
    if not isinstance(baseline_path, str):
        return False
    pure = PurePosixPath(baseline_path)
    if (
        baseline_path != pure.as_posix()
        or pure.parent != AUDIT_BASELINE_DIRECTORY
        or pure.suffix != '.json'
    ):
        return False
    baseline_bytes = _git_blob(
        repo_root=repo_root,
        revision=report_commit,
        repo_path=baseline_path,
    )
    expected_sha = reconciliation.get('warning_baseline_sha256')
    if (
        baseline_bytes is None
        or not HEX64.fullmatch(str(expected_sha))
        or hashlib.sha256(baseline_bytes).hexdigest() != expected_sha
    ):
        return False
    try:
        baseline = json.loads(baseline_bytes)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False
    if (
        not isinstance(baseline, dict)
        or baseline.get('schema_version') != 1
        or baseline.get('kind') != 'audit-warning-baseline'
        or baseline.get('run_id') != run_id
        or reconciliation.get('warning_baseline_id')
        != baseline.get('baseline_id')
        or reconciliation.get('evidence_context_sha256')
        != baseline.get('evidence_context_sha256')
    ):
        return False
    for key in (
        'warning_fingerprints',
        'mention_occurrences',
        'suppression_batches',
        'suppression_reader_verdicts',
        'neutral_page_transactions',
    ):
        if not isinstance(reconciliation.get(key), list):
            return False
    return True


def _committed_audit_completion_contract_valid(
    *, repo_root: Path, report_text: str
) -> bool:
    """Run Audit's actual completion validator on the committed report bytes."""
    validator_path = (
        repo_root
        / '.claude/skills/audit/scripts/validate_audit_completion.py'
    )
    if not validator_path.is_file():
        return False
    spec = importlib.util.spec_from_file_location(
        'shared_historical_audit_completion', validator_path
    )
    if spec is None or spec.loader is None:
        return False
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(
            prefix='llm-wiki-audit-proof-'
        ) as directory:
            report = Path(directory) / 'committed-audit.md'
            report.write_text(report_text, encoding='utf-8')
            valid, _ = module.validate(
                report=report, repo_root=repo_root
            )
        return valid is True
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def committed_page_raw_proofs(
    repo_root: Path,
) -> dict[tuple[str, str], dict[str, str]]:
    """Load committed terminal page-verification raw manifests from HEAD."""
    listing = subprocess.run(
        [
            'git',
            '-C',
            str(repo_root),
            'ls-tree',
            '-r',
            '--name-only',
            'HEAD',
            '--',
            '2-outputs/audit',
            '2-outputs/ingest',
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if listing.returncode != 0:
        return {}
    proofs: dict[tuple[str, str], dict[str, str]] = {}
    for report_path in listing.stdout.splitlines():
        expected_type = _direct_report_type(report_path)
        if expected_type is None:
            continue
        report_commit = _report_commit(repo_root, report_path)
        if report_commit is None:
            continue
        shown = subprocess.run(
            ['git', '-C', str(repo_root), 'show', f'HEAD:{report_path}'],
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode != 0:
            continue
        try:
            frontmatter = parse_frontmatter(shown.stdout)
            if (
                frontmatter.get('type') != expected_type
                or frontmatter.get('ledger_schema') != '1'
            ):
                continue
            rows = parse_rows(shown.stdout)
            manifests = [
                row for row in rows if row.get('row_type') == 'manifest'
            ]
            reconciliations = [
                row
                for row in rows
                if row.get('row_type') == 'reconciliation'
            ]
            if len(manifests) != 1 or len(reconciliations) != 1:
                continue
            validate_terminal_reconciliation(
                frontmatter=frontmatter,
                reconciliation=reconciliations[0],
                manifest=manifests[0],
                label=f'raw proof {report_path}',
            )
            run_id = manifests[0].get('run_id')
            row_ids: set[str] = set()
            rows_valid = True
            for row in rows:
                row_id = row.get('row_id')
                if (
                    row.get('schema_version') != 1
                    or isinstance(row.get('schema_version'), bool)
                    or row.get('run_id') != run_id
                    or not isinstance(row_id, str)
                    or not row_id.strip()
                    or row_id.strip() == '...'
                    or row_id in row_ids
                ):
                    rows_valid = False
                    break
                row_ids.add(row_id)
            if not rows_valid:
                continue
            source_rows = [
                row for row in rows if row.get('row_type') == 'source'
            ]
            reader_rows = [
                row for row in rows if row.get('row_type') == 'page_reader'
            ]
            status_rows = [
                row for row in rows if row.get('row_type') == 'status_write'
            ]
            reconciliation = reconciliations[0]
            if (
                reconciliation.get('terminal_sources') != len(source_rows)
                or reconciliation.get('terminal_page_readers')
                != len(reader_rows)
                or reconciliation.get('terminal_status_writes')
                != len(status_rows)
                or reconciliation.get('terminal_pages')
                != len(
                    {
                        row.get('page_path')
                        for row in reader_rows
                        if isinstance(row.get('page_path'), str)
                    }
                )
            ):
                continue
            if expected_type == 'audit':
                epoch = manifests[0].get('relationship_epoch')
                if (
                    frontmatter.get('mode') not in {'partial', 'full'}
                    or manifests[0].get('mode') != frontmatter.get('mode')
                    or not isinstance(epoch, str)
                    or not READY_EPOCH.fullmatch(epoch)
                    or not _committed_audit_completion_inputs_valid(
                        repo_root=repo_root,
                        report_commit=report_commit,
                        run_id=run_id,
                        rows=rows,
                        reconciliation=reconciliation,
                    )
                    or not _committed_audit_completion_contract_valid(
                        repo_root=repo_root, report_text=shown.stdout
                    )
                ):
                    continue
            else:
                epoch = None
            sources: dict[str, str] = {}
            source_rows_valid = True
            for row in source_rows:
                raw_path = row.get('raw_path')
                raw_sha = row.get('sha256')
                if (
                    not isinstance(raw_path, str)
                    or raw_path in sources
                    or not HEX64.fullmatch(str(raw_sha))
                    or row.get('disposition') != 'available'
                    or not isinstance(row.get('evidence'), str)
                    or not row['evidence'].strip()
                ):
                    source_rows_valid = False
                    break
                raw = resolve_raw_path(repo_root=repo_root, value=raw_path)
                if hashlib.sha256(raw.read_bytes()).hexdigest() != raw_sha:
                    source_rows_valid = False
                    break
                sources[raw_path] = str(raw_sha)
            if not source_rows_valid:
                continue
            readers: dict[
                tuple[str, str], dict[str, list[dict[str, str]]]
            ] = defaultdict(dict)
            reader_agents: dict[tuple[str, str], set[str]] = defaultdict(set)
            for row in reader_rows:
                role = row.get('role')
                agent = row.get('agent_id')
                page_path = _maintained_page_path(row.get('page_path'))
                generation = row.get('page_generation')
                if (
                    role not in PAGE_ROLES
                    or page_path is None
                    or not HEX64.fullmatch(str(generation))
                    or row.get('verdict') != 'hold'
                    or row.get('defects') != []
                    or not isinstance(row.get('evidence'), str)
                    or not row['evidence'].strip()
                    or row.get('blind_to') != [PAGE_COUNTERPART.get(role)]
                    or not isinstance(agent, str)
                    or not agent.strip()
                    or (epoch is not None and row.get('relationship_epoch') != epoch)
                ):
                    continue
                key = (page_path, str(generation))
                if role in readers[key]:
                    continue
                readers[key][role] = normalized_raw_manifest(
                    row.get('raw_manifest'),
                    label=f'raw proof reader {row.get("row_id")}',
                )
                reader_agents[key].add(agent.strip())
            statuses_by_key: dict[
                tuple[str, str], list[dict[str, Any]]
            ] = defaultdict(list)
            for row in status_rows:
                page_path = _maintained_page_path(row.get('page_path'))
                if page_path is None:
                    continue
                page_data = _git_blob(
                    repo_root=repo_root,
                    revision=report_commit,
                    repo_path=page_path,
                )
                if page_data is None or not _status_proves_committed_page(
                    row=row, page_data=page_data, epoch=epoch
                ):
                    continue
                key = (page_path, str(row.get('page_generation')))
                statuses_by_key[key].append(row)
            verified = {
                key for key, values in statuses_by_key.items() if len(values) == 1
            }
            for key in verified:
                role_manifests = readers.get(key, {})
                if (
                    set(role_manifests) != PAGE_ROLES
                    or len(reader_agents.get(key, set())) != 2
                ):
                    continue
                values = list(role_manifests.values())
                if values[0] != values[1]:
                    continue
                manifest_map = {
                    item['raw_path']: item['sha256'] for item in values[0]
                }
                if all(sources.get(path) == sha for path, sha in manifest_map.items()):
                    proofs[key] = manifest_map
        except (LedgerError, KeyError, TypeError, ValueError):
            continue
    return proofs


def pages_affected_by_raw_drift(
    repo_root: Path,
    *,
    neutral_edges: dict[
        tuple[str, str], tuple[str, set[str]]
    ] | None = None,
) -> set[str]:
    """Expand raw changes using the last terminal raw-verification proof."""
    changed_raws = changed_raw_paths(repo_root=repo_root)
    raw_closure = retained_page_raw_closure(repo_root=repo_root)
    proofs = committed_page_raw_proofs(repo_root=repo_root)
    bridged_proofs: dict[tuple[str, str], dict[str, str]] = {}
    for key, (pre_generation, target_paths) in (neutral_edges or {}).items():
        page_path, _ = key
        manifest = proofs.get((page_path, pre_generation))
        if manifest is None:
            continue
        combined = dict(manifest)
        valid = True
        for target_path in target_paths:
            if _maintained_page_path(target_path) is None:
                valid = False
                break
            target = resolve_repo_path(
                repo_root=repo_root, value=target_path
            )
            target_generation = semantic_page_digest(page=target)
            target_manifest = proofs.get((target_path, target_generation))
            if target_manifest is None:
                valid = False
                break
            target_current: dict[str, str] = {}
            for raw_path in raw_closure.get(target_path, set()):
                try:
                    raw = resolve_raw_path(
                        repo_root=repo_root, value=raw_path
                    )
                except (LedgerError, OSError):
                    valid = False
                    break
                target_current[raw_path] = hashlib.sha256(
                    raw.read_bytes()
                ).hexdigest()
            if not valid or target_manifest != target_current:
                valid = False
                break
            for raw_path, raw_sha in target_manifest.items():
                if raw_path in combined and combined[raw_path] != raw_sha:
                    valid = False
                    break
                combined[raw_path] = raw_sha
            if not valid:
                break
        if valid and set(combined) == raw_closure.get(page_path, set()):
            bridged_proofs[key] = combined
    affected: set[str] = set()
    for page_path, raw_links in raw_closure.items():
        if not raw_links:
            continue
        if changed_raws & raw_links:
            affected.add(page_path)
            continue
        page = resolve_repo_path(repo_root=repo_root, value=page_path)
        generation = semantic_page_digest(page=page)
        proof = proofs.get((page_path, generation))
        if proof is None:
            proof = bridged_proofs.get((page_path, generation))
        current: dict[str, str] = {}
        for raw_path in raw_links:
            try:
                raw = resolve_raw_path(repo_root=repo_root, value=raw_path)
            except (LedgerError, OSError):
                current = {}
                break
            current[raw_path] = hashlib.sha256(raw.read_bytes()).hexdigest()
        if proof != current:
            affected.add(page_path)
    return affected


def mandatory_partial_wiki_pages(
    repo_root: Path,
    *,
    neutral_edges: dict[
        tuple[str, str], tuple[str, set[str]]
    ] | None = None,
) -> set[str]:
    """Return retained pages that the partial-mode baseline cannot omit."""
    mandatory: set[str] = set()
    for page_path in maintained_wiki_pages(repo_root=repo_root):
        page = resolve_repo_path(repo_root=repo_root, value=page_path)
        frontmatter, body = split_page(page=page)
        tracked = subprocess.run(
            [
                'git', '-C', str(repo_root), 'cat-file', '-e',
                f'HEAD:{page_path}',
            ],
            capture_output=True,
            check=False,
        ).returncode == 0
        if (
            not tracked
            or frontmatter.get('status') != 'verified'
            or count_process_markers(text=body) > 0
        ):
            mandatory.add(page_path)
            continue
        retained_hash = frontmatter.get('verified_hash')
        if (
            not HEX64.fullmatch(str(retained_hash))
            or verified_body_hash(page=page) != retained_hash
        ):
            mandatory.add(page_path)
    return mandatory | pages_affected_by_raw_drift(
        repo_root=repo_root, neutral_edges=neutral_edges
    )


def extract_claim_records(page: Path) -> list[dict[str, str]]:
    """Extract logical bullets with retained callout type and block ID."""
    _, text = split_page(page=page)
    records: list[dict[str, str]] = []
    current: list[str] = []
    current_type = ''
    block_start = 0
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth = 0
    in_html_comment = False

    def flush_bullet() -> None:
        nonlocal current
        if current:
            records.append(
                {
                    'claim_text': '\n'.join(current),
                    'callout_type': current_type,
                    'callout_id': '',
                }
            )
            current = []

    for original_line in text.splitlines():
        line, in_html_comment = strip_html_comments_from_line(
            line=original_line,
            in_comment=in_html_comment,
        )
        if not line:
            continue
        fence = markdown_fence_match(
            line=line, fence_character=fence_character
        )
        if fence:
            quote_depth = fence.group(1).count('>')
            marker = fence.group(2)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                fence_quote_depth = quote_depth
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and quote_depth == fence_quote_depth
                and not fence.group(3).strip()
            ):
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
            if current:
                current.append(line)
            continue
        if fence_character is not None:
            if current:
                current.append(line)
            continue
        header = CALLOUT_HEADER.match(line)
        if header:
            flush_bullet()
            current_type = header.group(1).lower()
            block_start = len(records)
            continue
        if CALLOUT_BULLET_START.match(line):
            flush_bullet()
            current = [line]
            continue
        if (
            current
            and line.startswith('>')
            and not CALLOUT_BOUNDARY.match(line)
        ):
            current.append(line)
            continue
        flush_bullet()
        block_id = CALLOUT_ID.match(line)
        if block_id:
            for record in records[block_start:]:
                record['callout_id'] = block_id.group(1)
    flush_bullet()
    return records


def extract_logical_bullets(page: Path) -> list[str]:
    """Extract exact callout bullets and continuation lines in body order."""
    return [
        record['claim_text'] for record in extract_claim_records(page=page)
    ]


def inventory_claim_text(text: str) -> str:
    """Ignore the process marker when binding claims to retained bullets."""
    return strip_process_marker(text=text)


def canonical_claim_text(text: str) -> str:
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    return strip_process_marker(text=normalized)


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
    if (
        'verification_scope' in row
        or 'quantified_population' in row
    ):
        payload['verification_scope'] = row.get('verification_scope')
        payload['quantified_population'] = row.get('quantified_population')
    payload['claim_text_canonical'] = canonical_claim_text(row['claim_text'])
    return payload


def expected_claim_id(row: dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(claim_identity_payload(row))
    ).hexdigest()


def validate_quantified_role(
    *, claim_id: str, claim: dict[str, Any], row: dict[str, Any]
) -> None:
    """Require reader proof to cover the coordinator-frozen population."""
    scope = row.get('quantified_scope')
    if not isinstance(scope, dict) or set(scope) != QUANTIFIED_SCOPE_KEYS:
        raise LedgerError(
            f'exhaustive-negative role lacks schema-exact population: '
            f'{row.get("row_id")}'
        )
    frozen = claim['quantified_population']
    frozen_members = [
        member['member_id'] for member in frozen['members']
    ]
    raw_population = scope.get('raw_population')
    population = scope.get('population')
    searched = scope.get('searched_members')
    counterexamples = scope.get('counterexamples')
    if any(
        not isinstance(items, list)
        or any(
            not isinstance(item, str)
            or not item.strip()
            or item != item.strip()
            for item in items
        )
        or len(items) != len(set(items))
        for items in (
            raw_population, population, searched, counterexamples
        )
    ):
        raise LedgerError(
            f'exhaustive-negative population is malformed: {claim_id}'
        )
    if (
        raw_population != frozen['raw_paths']
        or population != frozen_members
        or not set(searched).issubset(population)
        or not set(counterexamples).issubset(set(searched))
        or not isinstance(scope.get('search_summary'), str)
        or not scope['search_summary'].strip()
    ):
        raise LedgerError(
            f'exhaustive-negative role differs from frozen population: '
            f'{row.get("row_id")}'
        )
    verdict = row.get('verdict')
    if verdict == 'hold' and (
        searched != population or counterexamples
    ):
        raise LedgerError(
            f'exhaustive-negative HOLD is incomplete: {row.get("row_id")}'
        )
    if verdict == 'refute' and not counterexamples:
        raise LedgerError(
            f'exhaustive-negative REFUTE lacks a counterexample: '
            f'{row.get("row_id")}'
        )
    if verdict == 'cannot_confirm' and counterexamples:
        raise LedgerError(
            f'exhaustive-negative CANNOT_CONFIRM contains a counterexample: '
            f'{row.get("row_id")}'
        )


def validate_quantified_population(
    *, value: Any, expected_raw_paths: list[str], label: str,
) -> list[str]:
    """Validate grounded semantic members covering the complete raw universe."""
    if (
        not isinstance(value, dict)
        or set(value) != {'raw_paths', 'members'}
        or value.get('raw_paths') != expected_raw_paths
        or not expected_raw_paths
        or not isinstance(value.get('members'), list)
    ):
        raise LedgerError(f'{label} lacks a frozen complete population')
    member_ids: list[str] = []
    member_order: list[tuple[str, str]] = []
    covered: set[str] = set()
    for member in value['members']:
        if (
            not isinstance(member, dict)
            or set(member) != {'member_id', 'raw_paths'}
            or not isinstance(member.get('member_id'), str)
            or not member['member_id'].strip()
            or member['member_id'] != member['member_id'].strip()
            or not isinstance(member.get('raw_paths'), list)
            or len(member['raw_paths']) != 1
            or member['raw_paths'][0] not in expected_raw_paths
        ):
            raise LedgerError(f'{label} has a malformed member mapping')
        member_ids.append(member['member_id'])
        member_order.append((member['raw_paths'][0], member['member_id']))
        covered.update(member['raw_paths'])
    if (
        len(member_ids) != len(set(member_ids))
        or covered != set(expected_raw_paths)
        or member_order != sorted(member_order)
    ):
        raise LedgerError(
            f'{label} members are not unique, ordered, and raw-complete'
        )
    return member_ids


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
    opening_boundaries = list(
        re.finditer(rf'(?m)^{re.escape(START)}[ \t]*$', text)
    )
    closing_boundaries = list(
        re.finditer(rf'(?m)^{re.escape(END)}[ \t]*$', text)
    )
    if len(opening_boundaries) != 1 or len(closing_boundaries) != 1:
        raise LedgerError(
            'report must contain exactly one verification-ledger boundary pair'
        )
    opening_boundary = opening_boundaries[0]
    closing_boundary = closing_boundaries[0]
    if opening_boundary.end() >= closing_boundary.start():
        raise LedgerError('verification-ledger boundaries are out of order')
    block = text[opening_boundary.end() : closing_boundary.start()]
    openings = list(re.finditer(r'(?m)^```jsonl[ \t]*$', block))
    closings = list(re.finditer(r'(?m)^```[ \t]*$', block))
    if len(openings) != 1 or len(closings) != 1:
        raise LedgerError('ledger must contain exactly one jsonl fence')
    opening = openings[0]
    closing = closings[0]
    if opening.end() >= closing.start():
        raise LedgerError('ledger jsonl fences are out of order')
    if (block[: opening.start()] + block[closing.end() :]).strip():
        raise LedgerError('ledger boundary contains text outside jsonl fence')
    content_start = opening.end()
    if content_start >= len(block) or block[content_start] != '\n':
        raise LedgerError('ledger jsonl fence has no content line')
    fence_end = closing.start()
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


def validate_terminal_reconciliation(
    *,
    frontmatter: dict[str, str],
    reconciliation: dict[str, Any],
    manifest: dict[str, Any],
    label: str,
) -> None:
    """Validate terminal result and planned/terminal/pending equations."""
    for row_name, row in (
        ('manifest', manifest),
        ('reconciliation', reconciliation),
    ):
        row_id = row.get('row_id')
        if (
            row.get('schema_version') != 1
            or isinstance(row.get('schema_version'), bool)
            or not isinstance(row_id, str)
            or not row_id.strip()
            or row_id.strip() == '...'
        ):
            raise LedgerError(f'{label} {row_name} row is malformed')
    run_id = manifest.get('run_id')
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
        or run_id == '...'
        or reconciliation.get('run_id') != run_id
    ):
        raise LedgerError(f'{label} reconciliation run ID is invalid')
    result = frontmatter.get('result')
    if (
        result not in {'complete', 'unconverged'}
        or reconciliation.get('result') != result
        or reconciliation.get('pending') != 0
    ):
        raise LedgerError(f'{label} reconciliation is not terminal')
    try:
        frontmatter_pending = int(str(frontmatter.get('pending')))
    except ValueError as exc:
        raise LedgerError(f'{label} frontmatter pending is invalid') from exc
    if frontmatter_pending != 0:
        raise LedgerError(f'{label} frontmatter pending is nonzero')
    pending_units = 0
    for prefix in RECONCILIATION_UNITS:
        planned = reconciliation.get(f'planned_{prefix}')
        terminal = reconciliation.get(f'terminal_{prefix}')
        pending = reconciliation.get(f'pending_{prefix}')
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (planned, terminal, pending)
        ):
            raise LedgerError(f'{label} reconciliation lacks {prefix} counts')
        if pending < 0 or planned != terminal + pending:
            raise LedgerError(f'{label} reconciliation mismatches {prefix}')
        if manifest.get(f'planned_{prefix}') != planned:
            raise LedgerError(f'{label} manifest mismatches {prefix}')
        pending_units += pending
    if pending_units != reconciliation['pending']:
        raise LedgerError(f'{label} reconciliation pending does not balance')


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    if not isinstance(value, str) or value != Path(value).as_posix():
        raise LedgerError(f'path is not canonical repo-relative form: {value}')
    candidate = repo_root / value
    resolved = candidate.resolve(strict=True)
    root = repo_root.resolve(strict=True)
    if resolved != root and root not in resolved.parents:
        raise LedgerError(f'path escapes repository: {value}')
    relative = resolved.relative_to(root).as_posix()
    if relative != Path(value).as_posix():
        raise LedgerError(f'path is not canonical repo-relative form: {value}')
    return resolved


def resolve_raw_path(repo_root: Path, value: Any) -> Path:
    """Resolve one canonical evidence file strictly beneath 0-raw/."""
    if (
        not isinstance(value, str)
        or not value.startswith('0-raw/')
        or Path(value).parts[0] != '0-raw'
    ):
        raise LedgerError(f'evidence path is outside 0-raw: {value!r}')
    resolved = resolve_repo_path(repo_root=repo_root, value=value)
    if not resolved.is_file():
        raise LedgerError(f'evidence path is not a file: {value}')
    return resolved


def extract_text_section(text: str, structural_anchor: str) -> str:
    """Extract one Markdown-style section from a non-PDF raw."""
    target = normalized_anchor(structural_anchor)
    headings: list[tuple[int, int, str]] = []
    fence_character: str | None = None
    fence_length = 0
    fence_quote_depth = 0
    in_html_comment = False
    for index, line in enumerate(text.splitlines()):
        if in_html_comment:
            in_html_comment = html_comment_state(
                line=line, in_comment=True
            )
            continue
        fence = markdown_fence_match(
            line=line, fence_character=fence_character
        )
        if fence:
            quote_depth = fence.group(1).count('>')
            marker = fence.group(2)
            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
                fence_quote_depth = quote_depth
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and quote_depth == fence_quote_depth
                and not fence.group(3).strip()
            ):
                fence_character = None
                fence_length = 0
                fence_quote_depth = 0
            continue
        if fence_character is not None:
            continue
        in_html_comment = html_comment_state(
            line=line, in_comment=False
        )
        if in_html_comment:
            continue
        match = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))
    for position, (start, level, heading) in enumerate(headings):
        if normalized_anchor(heading) != target:
            continue
        end = len(text.splitlines())
        for candidate_start, candidate_level, _ in headings[position + 1 :]:
            if candidate_level <= level:
                end = candidate_start
                break
        return '\n'.join(text.splitlines()[start:end])
    raise LedgerError(
        f'raw text lacks declared structural anchor: {structural_anchor}'
    )


def physical_page_span(
    row: dict[str, Any], *, label: str, required: bool
) -> tuple[int, int] | None:
    """Return one coherent physical page or inclusive physical range."""
    single = row.get('physical_page')
    start = row.get('physical_page_start')
    end = row.get('physical_page_end')
    has_single = single is not None
    has_range = start is not None or end is not None
    if has_single and has_range:
        raise LedgerError(f'{label} mixes physical page and range')
    if has_single:
        if (
            isinstance(single, bool)
            or not isinstance(single, int)
            or single < 1
        ):
            raise LedgerError(f'{label} has invalid physical page')
        return single, single
    if has_range:
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 1
            or end < start
        ):
            raise LedgerError(f'{label} has invalid physical page range')
        return start, end
    if required:
        raise LedgerError(f'{label} lacks a physical page or range')
    return None


def printed_page_span(
    row: dict[str, Any], *, label: str
) -> tuple[int, int] | None:
    """Return one coherent printed page or inclusive printed range."""
    single = row.get('printed_page')
    start = row.get('printed_page_start')
    end = row.get('printed_page_end')
    has_single = single is not None
    has_range = start is not None or end is not None
    if has_single and has_range:
        raise LedgerError(f'{label} mixes printed page and range')
    if has_single:
        if (
            isinstance(single, bool)
            or not isinstance(single, int)
            or single < 1
        ):
            raise LedgerError(f'{label} has invalid printed page')
        return single, single
    if has_range:
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 1
            or end < start
        ):
            raise LedgerError(f'{label} has invalid printed page range')
        return start, end
    return None


def display_printed_page_span(display: Any) -> tuple[int, int] | None:
    """Extract one printed page/range from an authored locator display."""
    if not isinstance(display, str):
        return None
    range_match = re.search(
        r'(?<![A-Za-z])pp\.\s*(\d+)\s*[-–]\s*(\d+)',
        display,
        flags=re.IGNORECASE,
    )
    if range_match:
        start, end = map(int, range_match.groups())
        if start < 1 or end < start:
            raise LedgerError('authored locator has invalid printed range')
        return start, end
    single_match = re.search(
        r'(?<![A-Za-z])p\.\s*(\d+)', display, flags=re.IGNORECASE
    )
    if single_match:
        page = int(single_match.group(1))
        return page, page
    return None


def load_pagination_map(repo_root: Path) -> dict[str, dict[int, int | None]]:
    """Load the repository's authoritative physical-to-printed page map."""
    path = repo_root / '.claude/skills/multi-skill/pagination-map.md'
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return {}
    output: dict[str, dict[int, int | None]] = {}
    raw_path: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('## '):
            heading = stripped[3:].strip()
            raw_path = heading if heading.startswith('0-raw/') else None
            if raw_path is not None:
                output.setdefault(raw_path, {})
            continue
        if raw_path is None or not stripped.startswith('- '):
            continue
        item = stripped[2:].split('#', 1)[0].strip()
        match = re.fullmatch(r'(\d+)(?:-(\d+))?\s*=\s*(.+)', item)
        if not match:
            continue
        physical_start = int(match.group(1))
        physical_end = int(match.group(2) or match.group(1))
        physical = list(range(physical_start, physical_end + 1))
        rhs = match.group(3).strip().lower()
        if rhs == 'none':
            for page in physical:
                output[raw_path][page] = None
            continue
        printed_match = re.fullmatch(r'(\d+)(?:-(\d+))?', rhs)
        if not printed_match:
            continue
        printed_start = int(printed_match.group(1))
        printed_end = int(printed_match.group(2) or printed_match.group(1))
        printed = list(range(printed_start, printed_end + 1))
        if len(physical) != len(printed):
            continue
        output[raw_path].update(zip(physical, printed))
    return output


def validate_pagination_coordinates(
    *, repo_root: Path, row: dict[str, Any], label: str
) -> None:
    """Bind declared printed coordinates to the curated pagination map."""
    raw_path = row.get('raw_path') or row.get('quote_raw_path')
    if not isinstance(raw_path, str) or Path(raw_path).suffix.lower() != '.pdf':
        return
    physical = physical_page_span(row, label=label, required=True)
    assert physical is not None
    mapping = load_pagination_map(repo_root=repo_root).get(raw_path)
    if mapping is None:
        if printed_page_span(row, label=label) is not None:
            raise LedgerError(
                f'{label} asserts printed pagination for an unregistered PDF'
            )
        return
    missing = [
        page
        for page in range(physical[0], physical[1] + 1)
        if page not in mapping
    ]
    if missing:
        raise LedgerError(
            f'{label} uses physical pages absent from pagination map: '
            + ', '.join(map(str, missing))
        )
    expected = [mapping[page] for page in range(physical[0], physical[1] + 1)]
    declared = printed_page_span(row, label=label)
    if all(page is None for page in expected):
        if declared is not None:
            raise LedgerError(f'{label} invents pagination on unpaginated pages')
        return
    if any(page is None for page in expected) or declared is None:
        raise LedgerError(f'{label} lacks coherent authoritative pagination')
    declared_pages = list(range(declared[0], declared[1] + 1))
    if declared_pages != expected:
        raise LedgerError(f'{label} contradicts authoritative pagination map')


def extract_quote(raw: Path, row: dict[str, Any]) -> str:
    if raw.suffix.lower() == '.pdf':
        span = physical_page_span(row, label='PDF quote', required=True)
        assert span is not None
        first_page, last_page = span
        proc = subprocess.run(
            [
                'pdftotext',
                '-f',
                str(first_page),
                '-l',
                str(last_page),
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
    text = raw.read_text(encoding='utf-8')
    structural_anchor = row.get('structural_anchor')
    if isinstance(structural_anchor, str) and structural_anchor.strip():
        return extract_text_section(
            text=text,
            structural_anchor=structural_anchor,
        )
    return text


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


def validate_bound_source_rows(
    *,
    repo_root: Path,
    rows: list[dict[str, Any]],
    dependencies: Any,
    run_id: str,
    terminal_source_count: Any,
    label: str,
) -> None:
    """Bind target dependencies to actual source rows in a mini-validator."""
    if not isinstance(dependencies, list) or any(
        not isinstance(dependency, dict) for dependency in dependencies
    ):
        raise LedgerError(f'{label} dependencies are malformed')
    dependency_map: dict[str, str] = {}
    for dependency in dependencies:
        raw_path = dependency.get('raw_path')
        raw_sha = dependency.get('sha256')
        if (
            not isinstance(raw_path, str)
            or raw_path in dependency_map
            or not HEX64.fullmatch(str(raw_sha))
        ):
            raise LedgerError(f'{label} dependencies are malformed')
        dependency_map[raw_path] = str(raw_sha)
    source_rows = [row for row in rows if row.get('row_type') == 'source']
    if (
        isinstance(terminal_source_count, bool)
        or not isinstance(terminal_source_count, int)
        or terminal_source_count != len(source_rows)
    ):
        raise LedgerError(f'{label} source terminal count is self-attested')
    bound: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        raw_path = row.get('raw_path')
        if raw_path not in dependency_map:
            continue
        row_id = row.get('row_id')
        if (
            raw_path in bound
            or row.get('schema_version') != 1
            or isinstance(row.get('schema_version'), bool)
            or row.get('run_id') != run_id
            or not isinstance(row_id, str)
            or not row_id.strip()
            or row_id.strip() == '...'
            or row.get('sha256') != dependency_map[raw_path]
            or row.get('disposition') not in {'available', 'cannot_confirm'}
            or not isinstance(row.get('evidence'), str)
            or not row['evidence'].strip()
            or row['evidence'].strip() == '...'
        ):
            raise LedgerError(f'{label} source terminal row is malformed')
        raw = resolve_raw_path(repo_root=repo_root, value=raw_path)
        if hashlib.sha256(raw.read_bytes()).hexdigest() != row['sha256']:
            raise LedgerError(f'{label} source raw changed: {raw_path}')
        bound[raw_path] = row
    if set(bound) != set(dependency_map):
        raise LedgerError(f'{label} lacks bound source terminal rows')


def valid_conflicting_terminal_pair(
    *,
    repo_root: Path,
    rows: list[dict[str, Any]],
    claim: dict[str, Any],
    terminal: dict[str, Any],
    run_id: Any,
    terminal_source_count: Any,
    relationship_epoch: str | None,
) -> bool:
    """Require a current-schema bound verdict pair for a terminal conflict."""
    claim_id = claim.get('claim_instance_id')
    claim_text = claim.get('claim_text')
    claim_bytes = claim.get('claim_bytes')
    ordinal = claim.get('duplicate_ordinal')
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
        or run_id.strip() == '...'
        or claim.get('schema_version') != 1
        or isinstance(claim.get('schema_version'), bool)
        or claim.get('classification') != 'required'
        or not isinstance(claim.get('row_id'), str)
        or not claim['row_id'].strip()
        or claim['row_id'].strip() == '...'
        or not isinstance(claim_text, str)
        or not claim_text.strip()
        or isinstance(claim_bytes, bool)
        or not isinstance(claim_bytes, int)
        or claim_bytes != len(claim_text.encode('utf-8'))
        or isinstance(ordinal, bool)
        or not isinstance(ordinal, int)
        or ordinal < 1
        or terminal.get('schema_version') != 1
        or isinstance(terminal.get('schema_version'), bool)
        or not isinstance(terminal.get('row_id'), str)
        or not terminal['row_id'].strip()
        or terminal['row_id'].strip() == '...'
        or terminal.get('run_id') != run_id
    ):
        return False
    role_rows = [
        row
        for row in rows
        if row.get('row_type') == 'bullet_verdict'
        and row.get('claim_instance_id') == claim_id
    ]
    by_role = {row.get('role'): row for row in role_rows}
    terminal_role_rows = terminal.get('role_rows')
    if (
        len(role_rows) != len(REQUIRED_ROLES)
        or set(by_role) != REQUIRED_ROLES
        or not isinstance(terminal_role_rows, list)
        or len(terminal_role_rows) != len(REQUIRED_ROLES)
        or len(set(terminal_role_rows)) != len(REQUIRED_ROLES)
        or len({row.get('row_id') for row in role_rows})
        != len(REQUIRED_ROLES)
        or set(terminal_role_rows)
        != {row.get('row_id') for row in role_rows}
    ):
        return False
    agents: set[str] = set()
    for role, row in by_role.items():
        agent = row.get('agent_id')
        if (
            row.get('schema_version') != 1
            or isinstance(row.get('schema_version'), bool)
            or row.get('run_id') != run_id
            or not isinstance(row.get('row_id'), str)
            or not row['row_id'].strip()
            or row['row_id'].strip() == '...'
            or row.get('verdict') not in TERMINAL_VERDICTS
            or not isinstance(agent, str)
            or not agent.strip()
            or agent.strip() == '...'
            or not isinstance(row.get('role_version'), str)
            or not row['role_version'].strip()
            or row['role_version'].strip() == '...'
            or row.get('blind_to') != [BULLET_COUNTERPART[role]]
            or (
                relationship_epoch is not None
                and row.get('relationship_epoch') != relationship_epoch
            )
            or not isinstance(row.get('reasoning'), str)
            or not row['reasoning'].strip()
            or row['reasoning'].strip() == '...'
            or not isinstance(row.get('confidence'), str)
            or not row['confidence'].strip()
            or row['confidence'].strip() == '...'
            or 'correction' not in row
            or (
                row.get('verdict') == 'hold'
                and row.get('quote_validated') is not True
            )
        ):
            return False
        agents.add(agent.strip())
    if len(agents) != len(REQUIRED_ROLES):
        return False
    outcomes = {row['verdict'] for row in role_rows}
    disposition = terminal.get('disposition')
    if disposition == 'refute' and 'refute' not in outcomes:
        return False
    if disposition == 'cannot_confirm' and (
        'refute' in outcomes or 'cannot_confirm' not in outcomes
    ):
        return False
    if disposition not in {'refute', 'cannot_confirm'}:
        return False
    dependency_paths = sorted(
        dependency['raw_path']
        for dependency in claim.get('raw_dependencies', [])
        if isinstance(dependency, dict) and 'raw_path' in dependency
    )
    cannot_confirm_valid = all(
        row.get('searched_raw_paths') == dependency_paths
        and isinstance(row.get('search_summary'), str)
        and row['search_summary'].strip()
        for row in role_rows
        if row.get('verdict') == 'cannot_confirm'
    )
    if not cannot_confirm_valid:
        return False
    try:
        validate_bound_source_rows(
            repo_root=repo_root,
            rows=rows,
            dependencies=claim.get('raw_dependencies'),
            run_id=run_id,
            terminal_source_count=terminal_source_count,
            label=f'conflict claim {claim_id}',
        )
        for dependency in claim.get('raw_dependencies', []):
            raw = resolve_raw_path(repo_root, dependency.get('raw_path'))
            if hashlib.sha256(raw.read_bytes()).hexdigest() != dependency.get(
                'sha256'
            ):
                return False
        validate_hold_raw_binding(
            claim_id=str(claim_id),
            claim=claim,
            role_rows=role_rows,
            repo_root=repo_root,
        )
        for row in role_rows:
            validate_quote(repo_root=repo_root, row=row)
    except (OSError, LedgerError, KeyError, TypeError, ValueError):
        return False
    return True


def conflicting_terminal_reports(
    repo_root: Path,
    claim_id: str,
    producer_report: str,
) -> list[str]:
    """Find committed terminal reports that contradict producer HOLDs."""
    listing = run_git(
        repo_root,
        [
            'ls-tree',
            '-r',
            '--name-only',
            'HEAD',
            '--',
            '2-outputs/audit',
            '2-outputs/ingest',
        ],
    )
    conflicts: list[str] = []
    for report_path in listing.splitlines():
        if not report_path.endswith('.md') or report_path == producer_report:
            continue
        try:
            # Inspect the immutable committed blob. A dirty or deleted working-
            # tree copy must not hide a terminal conflict already present at HEAD.
            text = run_git(repo_root, ['show', f'HEAD:{report_path}'])
            frontmatter = parse_frontmatter(text)
            expected_type = (
                'audit'
                if report_path.startswith('2-outputs/audit/')
                else 'ingest-report'
            )
            if (
                frontmatter.get('ledger_schema') != '1'
                or frontmatter.get('type') != expected_type
            ):
                continue
            rows = parse_rows(text)
            manifests = [
                row for row in rows if row.get('row_type') == 'manifest'
            ]
            reconciliations = [
                row for row in rows if row.get('row_type') == 'reconciliation'
            ]
            if len(manifests) != 1 or len(reconciliations) != 1:
                continue
            validate_terminal_reconciliation(
                frontmatter=frontmatter,
                reconciliation=reconciliations[0],
                manifest=manifests[0],
                label=f'conflict candidate {report_path}',
            )
            matching_claims = [
                row
                for row in rows
                if row.get('row_type') == 'claim'
                and row.get('claim_instance_id') == claim_id
            ]
            if len(matching_claims) != 1:
                continue
            relationship_epoch: str | None = None
            if expected_type == 'audit':
                relationship_epoch = manifests[0].get('relationship_epoch')
                if (
                    frontmatter.get('mode') not in {'partial', 'full'}
                    or manifests[0].get('mode') != frontmatter.get('mode')
                    or not isinstance(relationship_epoch, str)
                    or not READY_EPOCH.fullmatch(relationship_epoch)
                ):
                    continue
            claim = matching_claims[0]
            if expected_claim_id(claim) != claim_id:
                continue
            matching_terminals = [
                row
                for row in rows
                if row.get('row_type') == 'claim_terminal'
                and row.get('claim_instance_id') == claim_id
            ]
            if (
                len(matching_terminals) == 1
                and matching_terminals[0].get('run_id')
                == manifests[0].get('run_id')
                and claim.get('run_id') == manifests[0].get('run_id')
                and valid_conflicting_terminal_pair(
                    repo_root=repo_root,
                    rows=rows,
                    claim=claim,
                    terminal=matching_terminals[0],
                    run_id=manifests[0].get('run_id'),
                    terminal_source_count=reconciliations[0].get(
                        'terminal_sources'
                    ),
                    relationship_epoch=relationship_epoch,
                )
            ):
                conflicts.append(report_path)
        except (LedgerError, KeyError, TypeError, ValueError):
            continue
    return conflicts


def validate_duplicate_ordinals(
    claims: dict[str, dict[str, Any]], repo_root: Path | None = None
) -> None:
    """Require contiguous body-order ordinals for identical bullet groups."""
    groups: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for claim in claims.values():
        group = (
            claim['page_path'],
            claim['callout_id'],
            canonical_claim_text(claim['claim_text']),
        )
        ordinal = claim.get('duplicate_ordinal')
        if (
            isinstance(ordinal, bool)
            or not isinstance(ordinal, int)
            or ordinal < 1
        ):
            raise LedgerError(
                f'invalid duplicate ordinal: {claim["claim_instance_id"]}'
            )
        groups[group].append(ordinal)
    for group, ordinals in groups.items():
        expected = list(range(1, len(ordinals) + 1))
        if ordinals != expected:
            raise LedgerError(
                f'duplicate ordinals are not in contiguous body order for '
                f'{group[:2]}'
            )
        if repo_root is None or len(ordinals) == 1:
            continue
        page_path, callout_id, claim_text = group
        page = resolve_repo_path(repo_root=repo_root, value=page_path)
        retained_count = sum(
            record['callout_id'] == callout_id
            and canonical_claim_text(record['claim_text']) == claim_text
            for record in extract_claim_records(page=page)
        )
        if retained_count != len(ordinals):
            raise LedgerError(
                'duplicate ordinal inventory differs from retained body for '
                f'{group[:2]}'
            )


def validate_reused_pair(
    repo_root: Path,
    claim_id: str,
    terminal: dict[str, Any],
    current_claim: dict[str, Any],
    *,
    recheck_quotes: bool,
    seen_reports: set[Path] | None = None,
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
    report_parts = Path(report_path).parts
    if (
        len(report_parts) != 3
        or report_parts[0] != '2-outputs'
        or report_parts[1] not in {'audit', 'ingest'}
        or not report_parts[2].endswith('.md')
        or report_path != Path(report_path).as_posix()
    ):
        raise LedgerError(
            f'producer report is outside audit/ingest outputs: {report_path}'
        )
    expected_report_type = (
        'audit' if report_parts[1] == 'audit' else 'ingest-report'
    )
    if not isinstance(row_ids, list) or len(row_ids) != 2:
        raise LedgerError(
            f'reused claim lacks two role references: {claim_id}'
        )
    if (
        not isinstance(role_versions, dict)
        or set(role_versions) != REQUIRED_ROLES
        or any(
            not isinstance(version, str)
            or not version.strip()
            or version.strip() == '...'
            for version in role_versions.values()
        )
    ):
        raise LedgerError(f'reused claim lacks role versions: {claim_id}')
    if run_git(repo_root, ['status', '--porcelain', '--', report_path]):
        raise LedgerError(f'producer report is dirty: {report_path}')
    head_blob = run_git(repo_root, ['rev-parse', f'HEAD:{report_path}'])
    if head_blob != producer_blob:
        raise LedgerError(f'producer blob mismatch: {report_path}')
    conflicts = conflicting_terminal_reports(
        repo_root=repo_root,
        claim_id=claim_id,
        producer_report=report_path,
    )
    if conflicts:
        raise LedgerError(
            f'conflicting terminal reports invalidate reuse for {claim_id}: '
            + ', '.join(conflicts)
        )
    text = run_git(repo_root, ['show', f'HEAD:{report_path}'])
    frontmatter = parse_frontmatter(text)
    producer_rows = parse_rows(text)
    reconciliations = [
        row for row in producer_rows if row.get('row_type') == 'reconciliation'
    ]
    if (
        frontmatter.get('type') != expected_report_type
        or frontmatter.get('ledger_schema') != '1'
        or len(reconciliations) != 1
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
    producer_claims = [
        row
        for row in producer_rows
        if row.get('row_type') == 'claim'
        and row.get('claim_instance_id') == claim_id
    ]
    if len(producer_claims) != 1:
        raise LedgerError(f'producer claim row is missing: {claim_id}')
    producer_claim = producer_claims[0]
    producer_text = producer_claim.get('claim_text')
    producer_bytes = producer_claim.get('claim_bytes')
    if (
        not isinstance(producer_text, str)
        or not producer_text.strip()
        or not isinstance(producer_claim.get('row_id'), str)
        or not producer_claim['row_id'].strip()
        or producer_claim['row_id'].strip() == '...'
        or producer_claim.get('schema_version') != 1
        or isinstance(producer_claim.get('schema_version'), bool)
        or isinstance(producer_bytes, bool)
        or not isinstance(producer_bytes, int)
        or producer_bytes != len(producer_text.encode('utf-8'))
        or producer_claim.get('classification') != 'required'
        or expected_claim_id(producer_claim) != claim_id
    ):
        raise LedgerError(f'producer claim identity mismatch: {claim_id}')
    if (
        producer_claim.get('verification_scope')
        != current_claim.get('verification_scope')
        or producer_claim.get('quantified_population')
        != current_claim.get('quantified_population')
    ):
        raise LedgerError(
            f'producer verification scope differs from current claim: '
            f'{claim_id}'
        )
    producer_terminals = [
        row
        for row in producer_rows
        if row.get('row_type') == 'claim_terminal'
        and row.get('claim_instance_id') == claim_id
    ]
    if (
        len(producer_terminals) != 1
        or producer_terminals[0].get('schema_version') != 1
        or isinstance(producer_terminals[0].get('schema_version'), bool)
        or not isinstance(producer_terminals[0].get('row_id'), str)
        or not producer_terminals[0]['row_id'].strip()
        or producer_terminals[0]['row_id'].strip() == '...'
        or producer_terminals[0].get('disposition') != 'backfilled_hold'
        or set(producer_terminals[0].get('role_rows', [])) != set(row_ids)
    ):
        raise LedgerError(f'producer claim terminal is invalid: {claim_id}')
    producer_manifests = [
        row for row in producer_rows if row.get('row_type') == 'manifest'
    ]
    if len(producer_manifests) != 1:
        raise LedgerError(f'producer manifest is invalid: {claim_id}')
    validate_terminal_reconciliation(
        frontmatter=frontmatter,
        reconciliation=reconciliations[0],
        manifest=producer_manifests[0],
        label='producer',
    )
    producer_run = producer_manifests[0].get('run_id')
    bound_rows = [producer_claim, producer_terminals[0], *role_rows.values()]
    if (
        not isinstance(producer_run, str)
        or not producer_run.strip()
        or producer_run != producer_run.strip()
        or producer_run.strip() == '...'
        or any(row.get('run_id') != producer_run for row in bound_rows)
    ):
        raise LedgerError(
            f'producer claim rows have invalid run IDs: {claim_id}'
        )
    if expected_report_type == 'audit':
        producer_epoch = producer_manifests[0].get('relationship_epoch')
        if (
            frontmatter.get('mode') not in {'partial', 'full'}
            or producer_manifests[0].get('mode') != frontmatter.get('mode')
            or not isinstance(producer_epoch, str)
            or not READY_EPOCH.fullmatch(producer_epoch)
            or any(
                row.get('relationship_epoch') != producer_epoch
                for row in role_rows.values()
            )
        ):
            raise LedgerError(
                f'producer audit epoch is invalid: {claim_id}'
            )
    agents = {row['agent_id'].strip() for row in role_rows.values()}
    if len(agents) != 2:
        raise LedgerError(f'producer HOLD roles are not distinct: {claim_id}')
    for role, row in (
        (row.get('role'), row) for row in role_rows.values()
    ):
        if (
            row.get('schema_version') != 1
            or isinstance(row.get('schema_version'), bool)
            or not isinstance(row.get('row_id'), str)
            or not row['row_id'].strip()
            or row['row_id'].strip() == '...'
            or row.get('blind_to') != [BULLET_COUNTERPART[role]]
            or not isinstance(row.get('reasoning'), str)
            or not row['reasoning'].strip()
            or row['reasoning'].strip() == '...'
            or not isinstance(row.get('confidence'), str)
            or not row['confidence'].strip()
            or row['confidence'].strip() == '...'
            or not isinstance(row.get('agent_id'), str)
            or not row['agent_id'].strip()
            or row['agent_id'].strip() == '...'
            or not isinstance(row.get('role_version'), str)
            or not row['role_version'].strip()
            or row['role_version'].strip() == '...'
            or 'correction' not in row
            or row.get('quote_validated') is not True
        ):
            raise LedgerError(
                f'producer HOLD role is malformed: {row.get("row_id")}'
            )
    dependencies = producer_claim.get('raw_dependencies')
    if not isinstance(dependencies, list):
        raise LedgerError(f'producer dependencies are malformed: {claim_id}')
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            raise LedgerError(
                f'producer dependencies are malformed: {claim_id}'
            )
        raw = resolve_raw_path(repo_root, dependency.get('raw_path'))
        if hashlib.sha256(raw.read_bytes()).hexdigest() != dependency.get(
            'sha256'
        ):
            raise LedgerError(f'producer raw dependency changed: {claim_id}')
    validate_bound_source_rows(
        repo_root=repo_root,
        rows=producer_rows,
        dependencies=dependencies,
        run_id=producer_run,
        terminal_source_count=reconciliations[0].get('terminal_sources'),
        label=f'producer claim {claim_id}',
    )
    validate_hold_raw_binding(
        claim_id=claim_id,
        claim=producer_claim,
        role_rows=list(role_rows.values()),
        repo_root=repo_root,
    )
    for row in role_rows.values():
        if row.get('role_version') != role_versions[row['role']]:
            raise LedgerError(f'producer role version mismatch: {claim_id}')
        if recheck_quotes:
            validate_quote(repo_root, row)


def validate_quote(repo_root: Path, row: dict[str, Any]) -> None:
    if row.get('verdict') not in {'hold', 'refute'}:
        return
    quote = row.get('quote')
    raw_path = row.get('quote_raw_path')
    if (
        not isinstance(quote, str)
        or not quote.strip()
        or not isinstance(raw_path, str)
    ):
        raise LedgerError(f'HOLD row {row.get("row_id")} lacks quote/raw path')
    raw = resolve_raw_path(repo_root, raw_path)
    if (
        raw.suffix.lower() != '.pdf'
        and (
            not isinstance(row.get('structural_anchor'), str)
            or not row['structural_anchor'].strip()
        )
    ):
        raise LedgerError(
            f'non-PDF verdict lacks structural anchor: {row.get("row_id")}'
        )
    extracted = extract_quote(raw, row)
    if normalized_literal(quote) not in normalized_literal(extracted):
        raise LedgerError(
            'HOLD quote does not occur at attributed raw page: '
            f'{row.get("row_id")}'
        )


def normalized_anchor(value: Any) -> str:
    """Normalize a wikilink heading fragment for semantic comparison."""
    if not isinstance(value, str):
        return ''
    decoded = unquote(value).strip().casefold()
    return re.sub(r'[-_\s]+', ' ', decoded)


def locator_matches_fragment(locator: dict[str, Any], fragment: str) -> bool:
    """Return whether one declared locator matches an authored fragment."""
    page_match = re.fullmatch(r'page=(\d+)', fragment, flags=re.IGNORECASE)
    if page_match:
        physical_page = int(page_match.group(1))
        return locator.get('physical_page') == physical_page
    return normalized_anchor(locator.get('structural_anchor')) == (
        normalized_anchor(fragment)
    )


def validate_authored_locator_binding(
    *,
    claim_id: str,
    claim_text: Any,
    locators: list[dict[str, Any]],
    repo_root: Path | None = None,
) -> None:
    """Bind declared locator coordinates to raw fragments in claim prose."""
    if not isinstance(claim_text, str):
        raise LedgerError(f'claim lacks text for locator binding: {claim_id}')
    if repo_root is not None:
        for locator in locators:
            validate_pagination_coordinates(
                repo_root=repo_root,
                row=locator,
                label=f'claim locator for {claim_id}',
            )
    authored = [
        (match.group(1), match.group(2), match.group(3))
        for match in RAW_LOCATOR_WIKILINK.finditer(claim_text)
    ]
    if not authored:
        return
    for raw_path, fragment, _ in authored:
        if not any(
            locator.get('raw_path') == raw_path
            and locator_matches_fragment(locator, fragment)
            for locator in locators
        ):
            raise LedgerError(
                'claim locator does not match authored raw wikilink: '
                f'{claim_id}'
            )
    authored_by_path: dict[str, list[str]] = defaultdict(list)
    for raw_path, fragment, _ in authored:
        authored_by_path[raw_path].append(fragment)
    for locator in locators:
        fragments = authored_by_path.get(locator.get('raw_path'))
        if fragments and not any(
            locator_matches_fragment(locator, fragment)
            for fragment in fragments
        ):
            raise LedgerError(
                'declared locator contradicts authored raw wikilink: '
                f'{claim_id}'
            )
    authored_paths = set(authored_by_path)
    authored_locators = [
        locator
        for locator in locators
        if locator.get('raw_path') in authored_paths
    ]
    if len(authored_locators) != len(authored) or any(
        locator.get('raw_path') != raw_path
        or not locator_matches_fragment(locator, fragment)
        for (raw_path, fragment, _), locator in zip(
            authored, authored_locators
        )
    ):
        raise LedgerError(
            f'claim locator order differs from authored wikilinks: {claim_id}'
        )
    for (_, _, display), locator in zip(authored, authored_locators):
        authored_printed = display_printed_page_span(display)
        declared_printed = printed_page_span(
            locator, label=f'claim locator for {claim_id}'
        )
        if authored_printed != declared_printed:
            raise LedgerError(
                f'claim printed locator differs from authored display: '
                f'{claim_id}'
            )


def validate_hold_raw_binding(
    claim_id: str,
    claim: dict[str, Any],
    role_rows: list[dict[str, Any]],
    repo_root: Path | None = None,
) -> None:
    """Require each HOLD quote to come from this claim's declared evidence."""
    dependencies = claim.get('raw_dependencies')
    if not isinstance(dependencies, list) or any(
        not isinstance(dependency, dict) for dependency in dependencies
    ):
        raise LedgerError(f'claim raw dependencies are invalid: {claim_id}')
    dependency_paths = {
        dependency.get('raw_path') for dependency in dependencies
    }
    if None in dependency_paths:
        raise LedgerError(f'claim raw dependency lacks a path: {claim_id}')
    locators = claim.get('locators')
    if not isinstance(locators, list):
        raise LedgerError(f'claim locators are not a list: {claim_id}')
    locator_records: list[dict[str, Any]] = []
    for locator in locators:
        if not isinstance(locator, dict):
            raise LedgerError(f'claim locator is not an object: {claim_id}')
        raw_path = locator.get('raw_path')
        if not isinstance(raw_path, str) or raw_path not in dependency_paths:
            raise LedgerError(
                f'claim locator is outside raw dependencies: {claim_id}'
            )
        if Path(raw_path).suffix.lower() == '.pdf':
            physical_page_span(
                locator,
                label=f'claim locator for {claim_id}',
                required=True,
            )
        printed_page_span(
            locator,
            label=f'claim locator for {claim_id}',
        )
        locator_records.append(locator)
    validate_authored_locator_binding(
        claim_id=claim_id,
        claim_text=claim.get('claim_text'),
        locators=locator_records,
        repo_root=repo_root,
    )
    for row in role_rows:
        verdict = row.get('verdict')
        if verdict not in {'hold', 'refute'}:
            continue
        if (
            not isinstance(row.get('quote'), str)
            or not row['quote'].strip()
            or not any(
                row.get(key) not in {None, ''}
                for key in LOCATOR_COORDINATE_KEYS
            )
        ):
            raise LedgerError(
                f'{verdict.upper()} row lacks located evidence: '
                f'{row.get("row_id")}'
            )
        quote_raw_path = row.get('quote_raw_path')
        if (
            not isinstance(quote_raw_path, str)
            or not quote_raw_path.startswith('0-raw/')
        ):
            raise LedgerError(
                f'verdict evidence is outside 0-raw: {row.get("row_id")}'
            )
        if quote_raw_path not in dependency_paths:
            raise LedgerError(
                f'{verdict.upper()} quote is outside claim raw '
                f'dependencies: {claim_id}'
            )
        if Path(quote_raw_path).suffix.lower() == '.pdf':
            physical_page_span(
                row,
                label=f'PDF {verdict.upper()} {row.get("row_id")}',
                required=True,
            )
        else:
            anchor = row.get('structural_anchor')
            matching_locators = [
                locator
                for locator in locator_records
                if locator.get('raw_path') == quote_raw_path
            ]
            if (
                not isinstance(anchor, str)
                or not anchor.strip()
                or (
                    matching_locators
                    and not any(
                        normalized_anchor(locator.get('structural_anchor'))
                        == normalized_anchor(anchor)
                        for locator in matching_locators
                    )
                )
            ):
                raise LedgerError(
                    f'non-PDF {verdict.upper()} lacks exact structural '
                    f'locator: {row.get("row_id")}'
                )
        printed_page_span(
            row,
            label=f'{verdict.upper()} {row.get("row_id")}',
        )
        if repo_root is not None:
            validate_pagination_coordinates(
                repo_root=repo_root,
                row=row,
                label=f'{verdict.upper()} {row.get("row_id")}',
            )
        if verdict == 'hold' and locator_records and not any(
            quote_raw_path == locator['raw_path']
            and all(
                row.get(key) == locator.get(key)
                for key in LOCATOR_COORDINATE_KEYS
                if key in locator
            )
            for locator in locator_records
        ):
            raise LedgerError(
                f'HOLD quote does not match an exact claim locator: {claim_id}'
            )


def validate(
    report: Path,
    repo_root: Path,
    *,
    recheck_quotes: bool,
    _seen_reports: set[Path] | None = None,
) -> dict[str, int | str]:
    resolved_report = report.resolve(strict=True)
    seen_reports = set() if _seen_reports is None else set(_seen_reports)
    if resolved_report in seen_reports:
        raise LedgerError(f'reused-report cycle detected: {report}')
    seen_reports.add(resolved_report)
    text = report.read_text(encoding='utf-8')
    frontmatter = parse_frontmatter(text)
    report_type = frontmatter.get('type')
    if report_type not in {'audit', 'ingest-report'}:
        raise LedgerError(f'unsupported report type: {report_type!r}')
    result = frontmatter.get('result')
    if result not in VALID_RESULTS:
        raise LedgerError(f'invalid or missing report result: {result!r}')
    if frontmatter.get('ledger_schema') != '1':
        raise LedgerError('report does not declare ledger_schema 1')
    rows = parse_rows(text)

    row_ids: set[str] = set()
    rows_by_id: dict[str, dict[str, Any]] = {}
    claims: dict[str, dict[str, Any]] = {}
    source_rows: dict[str, dict[str, Any]] = {}
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
        if (
            isinstance(row.get('schema_version'), bool)
            or row.get('schema_version') != 1
        ):
            raise LedgerError('every row must use schema_version 1')
        row_id = row.get('row_id')
        if (
            not isinstance(row_id, str)
            or not row_id.strip()
            or row_id in row_ids
        ):
            raise LedgerError(f'missing or duplicate row_id: {row_id!r}')
        row_ids.add(row_id)
        rows_by_id[row_id] = row
        row_type = row.get('row_type')
        if row_type == 'manifest':
            manifests.append(row)
        elif row_type == 'source':
            raw_path = row.get('raw_path')
            raw_sha = row.get('sha256')
            if (
                not isinstance(raw_path, str)
                or raw_path in source_rows
                or not HEX64.fullmatch(str(raw_sha))
                or row.get('disposition')
                not in {'available', 'cannot_confirm'}
                or not isinstance(row.get('evidence'), str)
                or not row['evidence'].strip()
            ):
                raise LedgerError(f'invalid source terminal row: {row_id}')
            raw = resolve_raw_path(repo_root=repo_root, value=raw_path)
            if hashlib.sha256(raw.read_bytes()).hexdigest() != raw_sha:
                raise LedgerError(f'source terminal raw changed: {raw_path}')
            source_rows[raw_path] = row
        elif row_type == 'claim':
            claim_id = row.get('claim_instance_id')
            if claim_id in claims or not isinstance(claim_id, str):
                raise LedgerError(
                    f'missing or duplicate claim_instance_id: {claim_id!r}'
                )
            text_value = row.get('claim_text')
            if not isinstance(text_value, str) or not text_value.strip():
                raise LedgerError(f'claim {claim_id} lacks full claim_text')
            claim_bytes = row.get('claim_bytes')
            if (
                isinstance(claim_bytes, bool)
                or not isinstance(claim_bytes, int)
                or claim_bytes != len(text_value.encode('utf-8'))
            ):
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
                raw = resolve_raw_path(repo_root, raw_path)
                if hashlib.sha256(raw.read_bytes()).hexdigest() != raw_sha:
                    raise LedgerError(f'raw dependency changed: {claim_id}')
            if report_type == 'audit':
                verification_scope = row.get('verification_scope')
                population = row.get('quantified_population')
                if verification_scope not in VERIFICATION_SCOPES:
                    raise LedgerError(
                        f'audit claim lacks verification_scope: {claim_id}'
                    )
                if (
                    row.get('classification') == 'required'
                    and EXHAUSTIVE_NEGATIVE.search(text_value)
                    and verification_scope != 'exhaustive_negative'
                ):
                    raise LedgerError(
                        f'exhaustive-negative claim is labelled ordinary: '
                        f'{claim_id}'
                    )
                if verification_scope == 'ordinary':
                    if population is not None:
                        raise LedgerError(
                            f'ordinary claim carries quantified_population: '
                            f'{claim_id}'
                        )
                else:
                    validate_quantified_population(
                        value=population,
                        expected_raw_paths=dependency_paths,
                        label=f'exhaustive-negative claim {claim_id}',
                    )
            validate_hold_raw_binding(
                claim_id=claim_id,
                claim=row,
                role_rows=[],
                repo_root=repo_root,
            )
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
            if (
                not isinstance(row.get('agent_id'), str)
                or not row['agent_id'].strip()
            ):
                raise LedgerError(f'bullet verdict lacks agent ID: {row_id}')
            if (
                not isinstance(row.get('role_version'), str)
                or not row['role_version'].strip()
            ):
                raise LedgerError(
                    f'bullet verdict lacks role version: {row_id}'
                )
            if row.get('blind_to') != [BULLET_COUNTERPART[role]]:
                raise LedgerError(
                    f'bullet verdict lacks blindness provenance: {row_id}'
                )
            if (
                not isinstance(row.get('reasoning'), str)
                or not row['reasoning'].strip()
            ):
                raise LedgerError(f'bullet verdict lacks reasoning: {row_id}')
            if (
                not isinstance(row.get('confidence'), str)
                or not row['confidence'].strip()
            ):
                raise LedgerError(f'bullet verdict lacks confidence: {row_id}')
            if 'correction' not in row:
                raise LedgerError(
                    f'bullet verdict lacks correction field: {row_id}'
                )
            if (
                row.get('verdict') == 'hold'
                and row.get('quote_validated') is not True
            ):
                raise LedgerError(
                    f'HOLD verdict lacks quote validation: {row_id}'
                )
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
            if (
                not isinstance(row.get('agent_id'), str)
                or not row['agent_id'].strip()
            ):
                raise LedgerError(f'page reader lacks an agent ID: {row_id}')
            if row.get('blind_to') != [PAGE_COUNTERPART[role]]:
                raise LedgerError(
                    f'page reader lacks blindness provenance: {row_id}'
                )
            if not isinstance(row.get('defects'), list):
                raise LedgerError(
                    f'page reader defects are malformed: {row_id}'
                )
            if row.get('verdict') == 'hold' and row['defects']:
                raise LedgerError(
                    f'page reader HOLD contains defects: {row_id}'
                )
            if row.get('verdict') != 'hold' and not row['defects']:
                raise LedgerError(
                    f'non-HOLD page reader lacks defects: {row_id}'
                )
            if any(
                not isinstance(defect, dict)
                or defect.get('scope') not in PAGE_DEFECT_SCOPES
                or not isinstance(defect.get('detail'), str)
                or not defect['detail'].strip()
                for defect in row['defects']
            ):
                raise LedgerError(
                    f'page reader contains a malformed defect: {row_id}'
                )
            if (
                not isinstance(row.get('evidence'), str)
                or not row['evidence'].strip()
            ):
                raise LedgerError(f'page reader lacks full evidence: {row_id}')
            page_roles[key][role] = row
        elif row_type == 'reconciliation':
            reconciliations.append(row)
        elif row_type == 'scanner':
            scanner = row.get('scanner')
            target = row.get('target')
            status = row.get('status')
            result_value = row.get('result')
            if not isinstance(scanner, str) or not scanner.strip():
                raise LedgerError(f'scanner lacks identity: {row_id}')
            if not isinstance(target, str) or not target.strip():
                raise LedgerError(f'scanner lacks target: {row_id}')
            if (
                not isinstance(status, int)
                or isinstance(status, bool)
                or status < 0
            ):
                raise LedgerError(f'scanner lacks valid status: {row_id}')
            if (
                not isinstance(result_value, str)
                or not result_value.strip()
            ):
                raise LedgerError(f'scanner lacks result: {row_id}')
            if not isinstance(row.get('stdout_json'), bool):
                raise LedgerError(
                    f'scanner lacks stdout JSON attestation: {row_id}'
                )
            if not isinstance(row.get('stderr_runtime_error'), bool):
                raise LedgerError(
                    f'scanner lacks stderr attestation: {row_id}'
                )
            if row.get('terminal') is not True:
                raise LedgerError(f'scanner is not terminal: {row_id}')
            scanners.append(row)
        elif row_type == 'status_write':
            status_writes.append(row)
        else:
            raise LedgerError(f'unknown row_type: {row_type!r}')

    if len(manifests) != 1:
        raise LedgerError('report must contain exactly one manifest row')
    manifest = manifests[0]
    run_id = manifest.get('run_id')
    if (
        not isinstance(run_id, str)
        or not run_id.strip()
        or run_id != run_id.strip()
        or run_id.strip() == '...'
    ):
        raise LedgerError('manifest run_id is missing or a placeholder')
    for row in rows:
        if row.get('run_id') != run_id:
            raise LedgerError(
                f'row run_id differs from manifest: {row.get("row_id")}'
            )
    validate_duplicate_ordinals(claims, repo_root=repo_root)
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
        if disposition not in REQUIRED_CLAIM_DISPOSITIONS:
            raise LedgerError(
                f'invalid required-claim disposition: {claim_id}'
            )
        if disposition in {'backfilled_hold', 'refute', 'cannot_confirm'}:
            if set(verdicts[claim_id]) != REQUIRED_ROLES:
                raise LedgerError(
                    f'current evidence does not contain both roles: {claim_id}'
                )
            current_role_row_ids = {
                verdicts[claim_id][role]['row_id'] for role in REQUIRED_ROLES
            }
            terminal_role_row_ids = terminal.get('role_rows')
            if (
                not isinstance(terminal_role_row_ids, list)
                or len(terminal_role_row_ids) != len(REQUIRED_ROLES)
                or set(terminal_role_row_ids) != current_role_row_ids
            ):
                raise LedgerError(
                    f'claim terminal does not bind both role rows: {claim_id}'
                )
            agents = {
                verdicts[claim_id][role]['agent_id'].strip()
                for role in REQUIRED_ROLES
            }
            if len(agents) != 2:
                raise LedgerError(f'bullet roles are not distinct: {claim_id}')
            outcomes = {
                verdicts[claim_id][role]['verdict'] for role in REQUIRED_ROLES
            }
            validate_hold_raw_binding(
                claim_id=claim_id,
                claim=claim,
                role_rows=list(verdicts[claim_id].values()),
                repo_root=repo_root,
            )
            if (
                report_type == 'audit'
                and claim.get('verification_scope') == 'exhaustive_negative'
            ):
                for role_row in verdicts[claim_id].values():
                    validate_quantified_role(
                        claim_id=claim_id,
                        claim=claim,
                        row=role_row,
                    )
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
            for row in verdicts[claim_id].values():
                if row['verdict'] != 'cannot_confirm':
                    continue
                dependency_paths = sorted(
                    dependency['raw_path']
                    for dependency in claim['raw_dependencies']
                )
                if row.get('searched_raw_paths') != dependency_paths:
                    raise LedgerError(
                        'CANNOT_CONFIRM does not cover all raw dependencies: '
                        f'{row["row_id"]}'
                    )
                if (
                    not isinstance(row.get('search_summary'), str)
                    or not row['search_summary'].strip()
                ):
                    raise LedgerError(
                        'CANNOT_CONFIRM lacks exhausted-search evidence: '
                        f'{row["row_id"]}'
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
                claim,
                recheck_quotes=recheck_quotes,
                seen_reports=seen_reports,
            )
        elif verdicts[claim_id]:
            raise LedgerError(
                f'invalidated claim retains current verdict rows: {claim_id}'
            )

    for key, roles in page_roles.items():
        if set(roles) != PAGE_ROLES:
            raise LedgerError(f'page generation lacks both page roles: {key}')
        agents = {roles[role]['agent_id'].strip() for role in PAGE_ROLES}
        if len(agents) != 2:
            raise LedgerError(f'page roles are not distinct: {key}')

    if len(reconciliations) != 1:
        raise LedgerError('report must contain exactly one reconciliation row')
    rec = reconciliations[0]
    if rec.get('result') != result:
        raise LedgerError('frontmatter and reconciliation results differ')
    pending = rec.get('pending')
    if (
        isinstance(pending, bool)
        or not isinstance(pending, int)
        or pending < 0
    ):
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
    pending_units = 0
    for prefix in RECONCILIATION_UNITS:
        planned = rec.get(f'planned_{prefix}')
        terminal = rec.get(f'terminal_{prefix}')
        if (
            isinstance(planned, bool)
            or not isinstance(planned, int)
            or planned < 0
            or isinstance(terminal, bool)
            or not isinstance(terminal, int)
            or terminal < 0
        ):
            raise LedgerError(f'reconciliation lacks integer {prefix} counts')
        pending_unit = rec.get(f'pending_{prefix}')
        if (
            isinstance(pending_unit, bool)
            or not isinstance(pending_unit, int)
            or pending_unit < 0
        ):
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
        'sources': len(source_rows),
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
    if frontmatter.get('type') != 'audit' and rec['planned_pages'] != len(
        claim_pages
    ):
        raise LedgerError('planned page count does not match claim rows')
    claim_raw_paths = {
        dependency['raw_path']
        for claim in claims.values()
        for dependency in claim['raw_dependencies']
    }
    page_role_paths = {page_path for page_path, _ in page_roles}
    raw_closure: dict[str, set[str]] = {}
    if report_type == 'audit':
        raw_closure = retained_page_raw_closure(repo_root=repo_root)
        for claim_id, claim in claims.items():
            if claim.get('verification_scope') != 'exhaustive_negative':
                continue
            complete_page_raws = sorted(
                raw_closure.get(claim['page_path'], set())
            )
            dependency_paths = [
                dependency['raw_path']
                for dependency in claim['raw_dependencies']
            ]
            if dependency_paths != complete_page_raws:
                raise LedgerError(
                    'exhaustive-negative dependencies differ from complete '
                    f'page raw closure: {claim_id}'
                )
            validate_quantified_population(
                value=claim.get('quantified_population'),
                expected_raw_paths=complete_page_raws,
                label=f'exhaustive-negative page universe {claim_id}',
            )
        scoped_raw_paths = {
            raw_path
            for page_path in page_role_paths
            for raw_path in raw_closure.get(page_path, set())
        }
        raw_paths = claim_raw_paths | scoped_raw_paths
    else:
        raw_paths = claim_raw_paths
    if rec['planned_sources'] != len(raw_paths):
        raise LedgerError(
            'planned source count does not match raw dependencies'
        )
    if set(source_rows) != raw_paths:
        raise LedgerError(
            'source terminal inventory does not match raw dependencies'
        )
    if rec['planned_bullet_roles'] != 2 * required_claims:
        raise LedgerError(
            'planned bullet roles do not equal required claim pairs'
        )
    if report_type == 'audit':
        mode = frontmatter.get('mode')
        if mode not in {'partial', 'full'}:
            raise LedgerError(f'audit frontmatter has invalid mode: {mode!r}')
        if manifest.get('mode') != mode:
            raise LedgerError('audit frontmatter and manifest modes differ')
        if mode == 'full' and reused_claims:
            raise LedgerError('audit full mode contains reused HOLD evidence')
        if result in {'complete', 'unconverged'} and any(
            terminal['disposition'] == 'invalidated'
            for terminal in terminals.values()
        ):
            raise LedgerError('terminal audit retains invalidated claim rows')
        epoch = manifest.get('relationship_epoch')
        if not isinstance(epoch, str) or not READY_EPOCH.fullmatch(epoch):
            raise LedgerError('audit manifest lacks a final READY(n) epoch')
        if not all(
            isinstance(page_path, str) for page_path in page_role_paths
        ):
            raise LedgerError('audit page reader lacks a page path')
        if rec['planned_pages'] != len(page_role_paths):
            raise LedgerError(
                'audit planned page count does not match page-reader inventory'
            )
        if not claim_pages <= page_role_paths:
            raise LedgerError(
                'audit claim page is absent from page-reader inventory'
            )
        if mode == 'full':
            retained_inventory = maintained_wiki_pages(repo_root=repo_root)
            if page_role_paths != retained_inventory:
                raise LedgerError(
                    'audit full page inventory differs from retained wiki: '
                    f'missing={sorted(retained_inventory - page_role_paths)}; '
                    f'extra={sorted(page_role_paths - retained_inventory)}'
                )
        else:
            neutral_edges = _neutral_edges_from_report(
                repo_root=repo_root,
                run_id=run_id,
                reconciliation=rec,
            )
            mandatory_partial = mandatory_partial_wiki_pages(
                repo_root=repo_root,
                neutral_edges=neutral_edges,
            )
            if not mandatory_partial <= page_role_paths:
                raise LedgerError(
                    'audit partial page inventory omits mandatory pages: '
                    f'{sorted(mandatory_partial - page_role_paths)}'
                )
        for page_path in page_role_paths:
            page = resolve_repo_path(repo_root=repo_root, value=page_path)
            retained_context = retained_page_context(page=page)
            retained_records = extract_claim_records(page=page)
            manifested_claims = [
                claim
                for claim in claims.values()
                if claim['page_path'] == page_path
            ]
            retained_text = [
                inventory_claim_text(text=record['claim_text'])
                for record in retained_records
            ]
            manifested_text = [
                inventory_claim_text(text=claim['claim_text'])
                for claim in manifested_claims
            ]
            if manifested_text != retained_text:
                raise LedgerError(
                    'audit claim manifest does not match retained page bullet '
                    f'inventory: {page_path}'
                )
            for claim, retained_record in zip(
                manifested_claims, retained_records
            ):
                for key in ('page_type', 'page_title', 'semantic_frontmatter'):
                    if claim.get(key) != retained_context[key]:
                        raise LedgerError(
                            f'audit claim {key} differs from retained page: '
                            f'{claim["claim_instance_id"]}'
                        )
                for key in ('callout_type', 'callout_id'):
                    if claim.get(key) != retained_record[key]:
                        raise LedgerError(
                            f'audit claim {key} differs from retained page: '
                            f'{claim["claim_instance_id"]}'
                        )
                if (
                    claim.get('context_digest')
                    != retained_context['context_digest']
                ):
                    raise LedgerError(
                        'audit claim context_digest differs from retained '
                        'page: '
                        f'{claim["claim_instance_id"]}'
                    )
        for (page_path, _), roles in page_roles.items():
            expected_raw_manifest: list[dict[str, str]] = []
            for raw_path in sorted(raw_closure.get(page_path, set())):
                raw = resolve_raw_path(repo_root=repo_root, value=raw_path)
                expected_raw_manifest.append(
                    {
                        'raw_path': raw_path,
                        'sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
                    }
                )
            for row in roles.values():
                retained_manifest = normalized_raw_manifest(
                    row.get('raw_manifest'),
                    label=f'page reader {row.get("row_id")}',
                )
                if retained_manifest != expected_raw_manifest:
                    raise LedgerError(
                        'page reader raw_manifest differs from complete page '
                        f'raw closure: {row.get("row_id")}'
                    )
            page_claim_ids = sorted(
                claim_id
                for claim_id, claim in claims.items()
                if claim['page_path'] == page_path
            )
            for row in roles.values():
                for defect in row['defects']:
                    if defect['scope'] not in {
                        'bullet_local',
                        'cross_bullet',
                    }:
                        continue
                    dependency_ids = defect.get('claim_instance_ids')
                    minimum = 2 if defect['scope'] == 'cross_bullet' else 1
                    if (
                        not isinstance(dependency_ids, list)
                        or dependency_ids != sorted(set(dependency_ids))
                        or len(dependency_ids) < minimum
                        or not set(dependency_ids) <= set(page_claim_ids)
                    ):
                        raise LedgerError(
                            'page defect lacks exact claim dependency set: '
                            f'{row["row_id"]}'
                        )
                    if defect['scope'] == 'bullet_local':
                        unresolved_targets = [
                            claim_id
                            for claim_id in dependency_ids
                            if terminals[claim_id]['disposition']
                            not in {'refute', 'cannot_confirm'}
                        ]
                        if unresolved_targets:
                            raise LedgerError(
                                'bullet-local page defect lacks a current '
                                'non-HOLD claim pair: '
                                + ', '.join(unresolved_targets)
                            )
        for roles in verdicts.values():
            for row in roles.values():
                if row.get('relationship_epoch') != epoch:
                    row_id = row.get('row_id')
                    raise LedgerError(
                        f'audit bullet verdict has stale epoch: {row_id}'
                    )
        for row in scanners:
            if row.get('relationship_epoch') != epoch:
                raise LedgerError(
                    f'audit scanner has stale epoch: {row.get("row_id")}'
                )
        if result in {'complete', 'unconverged'} and any(
            row['status'] != 0
            or row['result'] != 'clean'
            or row['stdout_json'] is not True
            or row['stderr_runtime_error'] is not False
            for row in scanners
        ):
            raise LedgerError('terminal audit contains failed scanner')
        for key, roles in page_roles.items():
            page_path, page_generation = key
            if not isinstance(page_path, str):
                raise LedgerError('audit page reader lacks a page path')
            resolve_repo_path(repo_root=repo_root, value=page_path)
            if not HEX64.fullmatch(str(page_generation)):
                raise LedgerError(
                    f'audit page reader has invalid generation: {page_path}'
                )
            for row in roles.values():
                if row.get('relationship_epoch') != epoch:
                    row_id = row.get('row_id')
                    raise LedgerError(
                        f'audit page reader has stale epoch: {row_id}'
                    )
        if len(page_roles) != len(page_role_paths):
            raise LedgerError(
                'audit has multiple page-reader generations for one '
                'scoped page'
            )
        status_keys: list[tuple[str, str]] = []
        for row in status_writes:
            page_path = row.get('page_path')
            page_generation = row.get('page_generation')
            if not isinstance(page_path, str):
                raise LedgerError('audit status write lacks a page path')
            page = resolve_repo_path(repo_root=repo_root, value=page_path)
            if not HEX64.fullmatch(str(page_generation)):
                raise LedgerError(
                    f'audit status write has invalid generation: {page_path}'
                )
            if row.get('relationship_epoch') != epoch:
                raise LedgerError(
                    f'audit status write has stale epoch: {row.get("row_id")}'
                )
            after_status = row.get('after_status')
            before_status = row.get('before_status')
            if before_status not in PAGE_STATUSES:
                raise LedgerError(
                    'audit status write has invalid before_status: '
                    f'{page_path}'
                )
            if after_status not in PAGE_STATUSES:
                raise LedgerError(
                    f'audit status write has invalid after_status: {page_path}'
                )
            marker_action = row.get('marker_action')
            if marker_action not in MARKER_ACTIONS:
                raise LedgerError(
                    'audit status write has invalid marker_action: '
                    f'{page_path}'
                )
            pre_marker_count = row.get('pre_marker_count')
            post_marker_count = row.get('post_marker_count')
            if (
                not isinstance(pre_marker_count, int)
                or isinstance(pre_marker_count, bool)
                or pre_marker_count < 0
                or not isinstance(post_marker_count, int)
                or isinstance(post_marker_count, bool)
                or post_marker_count < 0
            ):
                raise LedgerError(
                    'audit status write has invalid marker counts: '
                    f'{page_path}'
                )
            retained_marker_count = count_process_markers(
                text=page.read_text(encoding='utf-8')
            )
            if post_marker_count != retained_marker_count:
                raise LedgerError(
                    'audit status write marker count differs from retained '
                    f'page: {page_path}'
                )
            marker_transition = {
                'none': pre_marker_count == post_marker_count == 0,
                'added': pre_marker_count < post_marker_count,
                'retained': pre_marker_count == post_marker_count > 0,
                'cleared': pre_marker_count > post_marker_count,
            }
            if not marker_transition[marker_action]:
                raise LedgerError(
                    'audit status write marker action contradicts counts: '
                    f'{page_path}'
                )
            page_frontmatter = parse_frontmatter(
                text=page.read_text(encoding='utf-8')
            )
            if page_frontmatter.get('status') != after_status:
                raise LedgerError(
                    'audit status write differs from retained page: '
                    f'{page_path}'
                )
            if (
                row.get('pre_semantic_hash') != page_generation
                or row.get('post_semantic_hash') != page_generation
                or semantic_page_digest(page=page) != page_generation
            ):
                raise LedgerError(
                    'audit page generation is stale or inconsistent: '
                    f'{page_path}'
                )
            roles = page_roles.get((page_path, page_generation), {})
            unresolved_claim_dispositions = {
                terminals[claim_id]['disposition']
                for claim_id, claim in claims.items()
                if claim['page_path'] == page_path
            } & {'refute', 'cannot_confirm', 'invalidated'}
            if (
                unresolved_claim_dispositions
                and after_status != 'needs-update'
            ):
                raise LedgerError(
                    'audit non-HOLD claim lacks needs-update hand-off: '
                    f'{page_path}'
                )
            if any(
                role.get('verdict') != 'hold' for role in roles.values()
            ) and after_status != 'needs-update':
                raise LedgerError(
                    'audit non-HOLD page reader lacks needs-update hand-off: '
                    f'{page_path}'
                )
            if (
                set(roles) == PAGE_ROLES
                and all(
                    role.get('verdict') == 'hold'
                    for role in roles.values()
                )
                and not unresolved_claim_dispositions
                and after_status != 'verified'
            ):
                raise LedgerError(
                    'audit fully held page lacks verified terminal status: '
                    f'{page_path}'
                )
            if after_status == 'verified':
                if set(roles) != PAGE_ROLES or any(
                    role.get('verdict') != 'hold' for role in roles.values()
                ):
                    raise LedgerError(
                        f'audit promotion lacks two page HOLDs: {page_path}'
                    )
                if not HEX64.fullmatch(str(row.get('verified_hash'))):
                    raise LedgerError(
                        'audit verified status lacks verified_hash: '
                        f'{page_path}'
                    )
                if page_frontmatter.get('verified_hash') != row.get(
                    'verified_hash'
                ) or verified_body_hash(page=page) != row.get('verified_hash'):
                    raise LedgerError(
                        'audit verified_hash differs from retained page: '
                        f'{page_path}'
                    )
                non_hold_claims = [
                    claim_id
                    for claim_id, claim in claims.items()
                    if claim['page_path'] == page_path
                    and claim['classification'] == 'required'
                    and terminals[claim_id]['disposition']
                    not in {'backfilled_hold', 'reused_hold'}
                ]
                if non_hold_claims:
                    raise LedgerError(
                        'audit verified status has non-HOLD required claims: '
                        + ', '.join(sorted(non_hold_claims))
                    )
            elif page_frontmatter.get('verified_hash') is not None:
                raise LedgerError(
                    'audit non-verified page retains verified_hash: '
                    f'{page_path}'
                )
            if after_status == 'needs-update':
                reason = row.get('needs_update_reason')
                if (
                    not isinstance(reason, str)
                    or not reason.strip()
                    or page_frontmatter.get('needs_update_reason') != reason
                ):
                    raise LedgerError(
                        'audit needs-update reason differs from page: '
                        f'{page_path}'
                    )
            status_keys.append((page_path, page_generation))
        if len(status_keys) != len(set(status_keys)):
            raise LedgerError(
                'audit has duplicate status-write page generations'
            )
        if set(status_keys) != set(page_roles):
            raise LedgerError(
                'audit status-write path/generation set does not match '
                'page readers'
            )
        try:
            markers_pending = int(str(frontmatter.get('markers_pending')))
        except ValueError as exc:
            raise LedgerError(
                'audit frontmatter markers_pending is invalid'
            ) from exc
        retained_marker_total = sum(
            row['post_marker_count'] for row in status_writes
        )
        if markers_pending != retained_marker_total:
            raise LedgerError(
                'audit frontmatter markers_pending differs from retained '
                'status rows'
            )
        if result in {'complete', 'unconverged'} and markers_pending != 0:
            raise LedgerError('terminal audit retains pending markers')
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
    parser.add_argument('report', type=Path, nargs='?')
    parser.add_argument('--repo-root', type=Path, default=Path.cwd())
    parser.add_argument('--skip-quote-recheck', action='store_true')
    parser.add_argument('--page-generation', type=Path)
    args = parser.parse_args()
    if args.page_generation is not None:
        if args.report is not None:
            parser.error('report and --page-generation are mutually exclusive')
        try:
            print(semantic_page_digest(page=args.page_generation))
            return 0
        except (OSError, LedgerError) as exc:
            print(json.dumps({'status': 'error', 'error': str(exc)}))
            return 1
    if args.report is None:
        parser.error('report is required unless --page-generation is used')
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
