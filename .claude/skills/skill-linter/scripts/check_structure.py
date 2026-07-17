#!/usr/bin/env python3
"""
check_structure.py — deterministic structural checks for a skill.

Emits a JSON list of findings to stdout. Each finding:
  {
    "severity": "error" | "warning" | "suggestion",
    "check_id": "<stable id>",
    "file": "<path relative to skill root, or absolute if outside>",
    "line": <int or null>,
    "message": "<what's wrong, one sentence>",
    "fix_hint": "<concrete suggested fix>"
  }

Usage:
    python check_structure.py <skill-dir-or-SKILL.md> [--single-file]

Flags:
    --single-file    Lint only the SKILL.md file; do not traverse references/.
                     Use this when the user explicitly pointed at a single file
                     rather than a skill directory.

Exit codes:
    0 = ran successfully (findings may be present in JSON)
    2 = bad invocation / path not found / no SKILL.md

The script intentionally does NOT make judgement calls about content quality —
that's done by the LLM in a separate pass. This script only flags issues
that can be checked mechanically with high confidence.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

# Best-practices thresholds from the Anthropic skill-authoring guide.
# SKILL.md body length budget; longer bodies eat context and signal that
# detail should move into references/.
SKILL_MD_MAX_LINES = 500
# Word-count budget, the primary length signal. The guide's stated rule is
# "SKILL.md body under 500 lines" (skill-authoring-best-practices.md ->
# Token budgets), and its real concern is token/context cost — "every token
# competes with conversation history". This repo writes each paragraph as one
# physical line (no hard wrap), so the physical-line count under-measures that
# cost (a 200-line SKILL.md can carry 11k words). The word budget approximates
# the guide's 500 *normally-wrapped* lines (~13 words/line) — the repo-specific
# proxy for the token concern the line rule stands in for. Flag when either
# measure is exceeded.
SKILL_MD_MAX_WORDS = 6500
# Reference files longer than this should have a table of contents so a
# `head`-style preview surfaces the section list.
REFERENCE_TOC_THRESHOLD = 100
# How far down a reference file we look for a TOC heading. Matches the
# `head -100` preview window the guide assumes (and the TOC trigger
# threshold), so a TOC anywhere in the previewable region counts; a TOC
# below it would not be surfaced by the preview anyway.
TOC_PREVIEW_LINES = REFERENCE_TOC_THRESHOLD
# Hard cap on the frontmatter `name:` field per the skill schema.
NAME_MAX_CHARS = 64
# Hard cap on the frontmatter `description:` field per the skill schema;
# the description is injected into the system prompt, so longer text
# crowds the context budget.
DESCRIPTION_MAX_CHARS = 1024
RESERVED_NAME_WORDS = ('anthropic', 'claude')


def load_skill_md(
    skill_md_path: Path,
) -> tuple[dict[str, Any] | None, int, list[str]]:
    """Read SKILL.md and return (frontmatter_dict_or_None, end_line, body).

    body_lines is a list of lines AFTER the closing '---' of frontmatter
    (1-indexed line numbers in SKILL.md correspond to
    (frontmatter_end_line + i + 1) for body_lines[i]).
    """
    # Guard the read like the reference-file read below: a non-UTF-8 / binary
    # SKILL.md should surface as a frontmatter_missing finding (fm=None), not
    # crash the scanner with an uncaught UnicodeDecodeError and block the loop.
    try:
        lines = skill_md_path.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeDecodeError):
        return None, 0, []

    if not lines or lines[0].strip() != '---':
        return None, 0, lines

    # Find the closing '---' for frontmatter.
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    if end_idx is None:
        return None, 0, lines

    frontmatter_text = '\n'.join(lines[1:end_idx])
    body_lines = lines[end_idx + 1:]

    # Try parsing with PyYAML; fall back to a tiny key:value parser.
    fm: dict[str, Any] | None
    try:
        import yaml  # type: ignore
        try:
            parsed = yaml.safe_load(frontmatter_text)
            fm = parsed if isinstance(parsed, dict) else None
        except yaml.YAMLError:
            fm = None
    except ImportError:
        fm = _naive_yaml(text=frontmatter_text)

    # +1 -> 1-indexed line of the body's first line.
    return fm, end_idx + 1, body_lines


def _naive_yaml(text: str) -> dict[str, Any]:
    """Tiny `key: value` parser for environments without PyYAML.

    Only used as a fallback. Handles plain scalars and quoted strings;
    folded/literal multi-line scalars and nested mappings degrade to
    strings.
    """
    out: dict[str, Any] = {}
    current_key: str | None = None
    current_buffer: list[str] = []
    for line in text.splitlines():
        m = re.match(r'^([A-Za-z_][\w-]*)\s*:\s*(.*)$', line)
        if m:
            if current_key is not None:
                joined = '\n'.join(current_buffer).strip()
                out[current_key] = joined.strip('"').strip("'")
            current_key = m.group(1)
            current_buffer = [m.group(2)]
        else:
            if current_key is not None:
                current_buffer.append(line)
    if current_key is not None:
        joined = '\n'.join(current_buffer).strip()
        out[current_key] = joined.strip('"').strip("'")
    return out


def check_frontmatter(
    fm: dict[str, Any] | None,
    skill_md_rel: str,
) -> list[dict[str, Any]]:
    """Validate the YAML frontmatter against the documented schema."""
    findings: list[dict[str, Any]] = []
    if fm is None:
        findings.append({
            'severity': 'error',
            'check_id': 'frontmatter_missing',
            'file': skill_md_rel,
            'line': 1,
            'message': (
                "SKILL.md has no parseable YAML frontmatter "
                "(must start with '---' and close with '---')."
            ),
            'fix_hint': (
                'Add a YAML frontmatter block at the top of SKILL.md '
                "with at least 'name' and 'description'."
            ),
        })
        return findings

    # name
    name = fm.get('name')
    if not isinstance(name, str) or not name.strip():
        findings.append({
            'severity': 'error',
            'check_id': 'name_missing',
            'file': skill_md_rel,
            'line': None,
            'message': "Frontmatter is missing the required 'name' field.",
            'fix_hint': (
                "Add a 'name' field "
                '(lowercase letters, digits, hyphens; ≤64 chars).'
            ),
        })
    else:
        if len(name) > NAME_MAX_CHARS:
            findings.append({
                'severity': 'error',
                'check_id': 'name_too_long',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    f"Frontmatter 'name' is {len(name)} characters; "
                    f'the maximum is {NAME_MAX_CHARS}.'
                ),
                'fix_hint': 'Shorten the name to ≤64 characters.',
            })
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', name):
            findings.append({
                'severity': 'error',
                'check_id': 'name_invalid_chars',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    "Frontmatter 'name' must be lowercase kebab-case "
                    '(letters, digits, single hyphens).'
                ),
                'fix_hint': (
                    'Rename to use only [a-z0-9-], '
                    'no leading/trailing/double hyphens.'
                ),
            })
        if any(reserved in name.lower() for reserved in RESERVED_NAME_WORDS):
            findings.append({
                'severity': 'error',
                'check_id': 'name_reserved_word',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    f"Frontmatter 'name' contains a reserved word "
                    f"({', '.join(RESERVED_NAME_WORDS)})."
                ),
                'fix_hint': (
                    "Rename the skill so it doesn't contain "
                    "'anthropic' or 'claude'."
                ),
            })

    # description
    desc = fm.get('description')
    if not isinstance(desc, str) or not desc.strip():
        findings.append({
            'severity': 'error',
            'check_id': 'description_missing',
            'file': skill_md_rel,
            'line': None,
            'message': (
                "Frontmatter is missing the required 'description' field."
            ),
            'fix_hint': (
                "Add a non-empty 'description' that says what the skill "
                'does AND when to use it.'
            ),
        })
    else:
        if len(desc) > DESCRIPTION_MAX_CHARS:
            findings.append({
                'severity': 'error',
                'check_id': 'description_too_long',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    f"Frontmatter 'description' is {len(desc)} characters;"
                    f' the maximum is {DESCRIPTION_MAX_CHARS}.'
                ),
                'fix_hint': (
                    'Trim the description to ≤1024 characters; '
                    'move detail into the SKILL.md body.'
                ),
            })
        if '<' in desc or '>' in desc:
            findings.append({
                'severity': 'error',
                'check_id': 'description_xml_tags',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    "Frontmatter 'description' contains '<' or '>' "
                    'which are disallowed (XML tags break injection).'
                ),
                'fix_hint': 'Remove or rephrase to avoid angle brackets.',
            })

        # First-person red flag: the description gets injected into the
        # system prompt, so 'I' / 'we' / 'you can use this' is a known
        # failure mode.
        first_person_match = re.search(
            r'\b(I (can|will|am)|we (can|will)|let me'
            r'|you can use (this|it))\b',
            desc,
            flags=re.IGNORECASE,
        )
        if first_person_match:
            findings.append({
                'severity': 'warning',
                'check_id': 'description_first_person',
                'file': skill_md_rel,
                'line': None,
                'message': (
                    'Description appears to be written in first or '
                    'second person; descriptions should be third person.'
                ),
                'fix_hint': (
                    'Rewrite as a third-person statement of capability, '
                    "e.g. 'Processes X and produces Y'."
                ),
            })

    return findings


def check_body_length(
    body_lines: list[str],
    frontmatter_end_line: int,
    skill_md_rel: str,
) -> list[dict[str, Any]]:
    """Flag SKILL.md bodies that exceed the length budget.

    Two measures because this repo writes each paragraph as one physical
    line (no hard wrap): the physical-line count under-counts a dense body,
    so a word count is the primary signal and the line count is a backstop
    for a genuinely many-lined file. Flag when either budget is exceeded.

    The word count deliberately includes fenced code and tables, unlike the
    prose-hunting sibling checks: the budget is a token-cost proxy, and code
    and tables cost context tokens on load just as prose does, so stripping
    them would under-count the real load.
    """
    n_lines = len(body_lines)
    n_words = sum(len(line.split()) for line in body_lines)
    over_words = n_words > SKILL_MD_MAX_WORDS
    over_lines = n_lines > SKILL_MD_MAX_LINES
    if not (over_words or over_lines):
        return []
    parts: list[str] = []
    if over_words:
        parts.append(f'{n_words} words (budget {SKILL_MD_MAX_WORDS})')
    if over_lines:
        parts.append(f'{n_lines} lines (budget {SKILL_MD_MAX_LINES})')
    # The explanatory tail depends on which budget tripped. Word count is
    # the primary signal, and because this repo writes each paragraph as one
    # physical line the line count alone under-measures a dense body; but on
    # a line-only trip the word count is within budget, so do not claim the
    # line count under-measures there.
    if over_words:
        tail = (
            ' Word count is the primary signal; because this repo writes '
            'each paragraph as one physical line, the line count alone '
            'under-measures a dense body.'
        )
    else:
        tail = ' The word count is within budget; the line budget tripped.'
    return [{
        'severity': 'warning',
        'check_id': 'body_over_length',
        'file': skill_md_rel,
        'line': frontmatter_end_line + n_lines,
        'message': (
            f'SKILL.md body is {"; ".join(parts)}; a dense body eats '
            f'context.{tail}'
        ),
        'fix_hint': (
            'Move detail into separate files under references/ '
            'and link from SKILL.md.'
        ),
    }]


# Match Markdown links of the form [text](target) where target is a
# relative path. We deliberately ignore http(s):// and absolute paths.
MD_LINK_RE = re.compile(r'\[[^\]]+\]\(([^)\s]+)\)')
# Match Windows-style backslash separators in path-like contexts
# (anything with .md, .py, .json, .txt extensions or one of the
# conventional skill folders).
WINDOWS_PATH_RE = re.compile(
    r'(?:[A-Za-z0-9_\-\.]+\\)+'
    r'[A-Za-z0-9_\-\.]+\.(?:md|py|json|txt|yaml|yml|csv|html|sh)',
)

# Raw HTML in skill prose is not portable Markdown and is hard for
# downstream linters to reason about. Keep this to real HTML tags so
# placeholders such as `<skill-path>` in examples do not become noisy
# false positives.
HTML_TAG_RE = re.compile(r'<\s*/?\s*([A-Za-z][A-Za-z0-9:-]*)\b[^>]*>')
HTML_TAGS = {
    'a', 'abbr', 'address', 'article', 'aside', 'audio', 'b', 'blockquote',
    'br', 'button', 'caption', 'cite', 'code', 'col', 'colgroup', 'dd',
    'del', 'details', 'dfn', 'dialog', 'div', 'dl', 'dt', 'em', 'figcaption',
    'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'header', 'hr', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'label',
    'legend', 'li', 'main', 'mark', 'nav', 'ol', 'option', 'p', 'picture',
    'pre', 'q', 's', 'samp', 'script', 'section', 'select', 'small',
    'source', 'span', 'strong', 'sub', 'summary', 'sup', 'svg', 'table',
    'tbody', 'td', 'textarea', 'tfoot', 'th', 'thead', 'time', 'tr', 'u',
    'ul', 'var', 'video',
}

# Bash process substitution `<(...)` outside a code fence is rejected by the
# cowork skill-upload pipeline (it reads as a malformed HTML tag), so it is an
# upload-breaking defect — see CLAUDE.md -> Skill Authoring. The HTML_TAG_RE
# above never matches it (it requires a letter after `<`), so it needs its own
# pattern.
PROC_SUBST_RE = re.compile(r'<\(')


def strip_inline_code(line: str) -> str:
    """Remove inline-code spans before prose checks."""
    return re.sub(r'`[^`]*`', '', line)


def check_html_tags(
    markdown_lines: list[str],
    line_offset: int,
    file_rel: str,
) -> list[dict[str, Any]]:
    """Flag raw HTML tags outside fenced code blocks."""
    findings: list[dict[str, Any]] = []
    in_code_fence = False
    for i, line in enumerate(markdown_lines):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        prose = strip_inline_code(line=line)
        for match in HTML_TAG_RE.finditer(prose):
            tag = match.group(1).lower()
            if tag not in HTML_TAGS:
                continue
            findings.append({
                'severity': 'warning',
                'check_id': 'html_tag',
                'file': file_rel,
                'line': line_offset + i + 1,
                'message': (
                    f"Line contains raw HTML tag '<{tag}>'; "
                    'skill text should stay portable Markdown.'
                ),
                'fix_hint': (
                    'Replace the raw HTML with plain Markdown, a normal '
                    'heading, or a fenced code example.'
                ),
            })
            break
        if PROC_SUBST_RE.search(prose):
            findings.append({
                'severity': 'error',
                'check_id': 'process_substitution',
                'file': file_rel,
                'line': line_offset + i + 1,
                'message': (
                    'Line contains bash process substitution `<(...)`; the '
                    'skill-upload pipeline rejects it as a malformed HTML tag.'
                ),
                'fix_hint': (
                    'Replace `<(...)` with a temp file or a pipe '
                    '(CLAUDE.md -> Skill Authoring).'
                ),
            })
    return findings


def check_paths(
    body_lines: list[str],
    frontmatter_end_line: int,
    skill_md_rel: str,
) -> list[dict[str, Any]]:
    """Flag Windows-style backslash paths in the SKILL.md body.

    Lines inside fenced code blocks are skipped: a backslash path in a
    PowerShell / cmd example is legitimate, not a portability defect. The
    check is otherwise intentionally light — false positives are noisy.
    """
    findings = []
    in_code_fence = False
    for i, line in enumerate(body_lines):
        if line.strip().startswith('```'):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if WINDOWS_PATH_RE.search(line):
            findings.append({
                'severity': 'warning',
                'check_id': 'windows_path',
                'file': skill_md_rel,
                'line': frontmatter_end_line + i + 1,
                'message': (
                    'Line contains a Windows-style path '
                    '(backslash separators); use forward slashes for '
                    'cross-platform compatibility.'
                ),
                'fix_hint': "Replace '\\' with '/' in the path on this line.",
            })
    return findings


def check_reference_depth_and_toc(
    skill_dir: Path,
    body_text: str,
) -> list[dict[str, Any]]:
    """For each reference file linked from SKILL.md, check it's one level
    deep AND has a table of contents if longer than the threshold."""
    findings: list[dict[str, Any]] = []

    # Collect references linked directly from SKILL.md.
    direct_refs: list[Path] = []
    for m in MD_LINK_RE.finditer(body_text):
        target = m.group(1).split('#', 1)[0]  # strip anchors
        if not target or target.startswith(
            ('http://', 'https://', 'mailto:')
        ):
            continue
        # Only check .md targets (we don't follow into scripts/).
        if not target.endswith('.md'):
            continue
        ref_path = (skill_dir / target).resolve()
        if not ref_path.exists():
            findings.append({
                'severity': 'warning',
                'check_id': 'broken_md_link',
                'file': 'SKILL.md',
                'line': None,
                'message': (
                    f"SKILL.md links to '{target}' but the file "
                    "doesn't exist in the skill directory."
                ),
                'fix_hint': (
                    f"Either create '{target}' or update the link to "
                    'point to an existing file.'
                ),
            })
            continue
        if not ref_path.is_relative_to(skill_dir):
            # A reference resolving outside the skill folder (e.g. a
            # shared ../multi-skill/references/ file) is legitimate and
            # not this skill's own reference to depth/TOC-check; skip it.
            # This also avoids a relative_to() crash on the line below.
            continue
        direct_refs.append(ref_path)

    # For each reference file: check that IT does not link out to other
    # markdown files (depth-2 problem), and that long ones have a TOC.
    for ref in direct_refs:
        rel = ref.relative_to(skill_dir).as_posix()
        try:
            content = ref.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        findings += check_html_tags(
            markdown_lines=content.splitlines(),
            line_offset=0,
            file_rel=rel,
        )

        # Depth check: links from a reference file to another markdown
        # file are problematic.
        for m in MD_LINK_RE.finditer(content):
            target = m.group(1).split('#', 1)[0]
            if not target or target.startswith(
                ('http://', 'https://', 'mailto:')
            ):
                continue
            if target.endswith('.md'):
                findings.append({
                    'severity': 'warning',
                    'check_id': 'nested_reference',
                    'file': rel,
                    'line': None,
                    'message': (
                        f"Reference file links to another markdown file "
                        f"('{target}'); references should be one level "
                        'deep from SKILL.md.'
                    ),
                    'fix_hint': (
                        f"Move '{target}' so it's linked directly from "
                        'SKILL.md, or inline the relevant content.'
                    ),
                })
                break  # one finding per file is enough

        # TOC check on long files.
        line_count = len(content.splitlines())
        if line_count > REFERENCE_TOC_THRESHOLD:
            # Heuristic: a TOC is a '## Contents' / '## Table of
            # contents' heading OR a bulleted list near the top whose
            # items reference subsequent headings.
            head = '\n'.join(
                content.splitlines()[:TOC_PREVIEW_LINES]
            ).lower()
            has_toc_heading = bool(re.search(
                r'^\s*##\s+(contents|table of contents|toc)\b',
                head,
                re.MULTILINE,
            ))
            if not has_toc_heading:
                findings.append({
                    'severity': 'suggestion',
                    'check_id': 'missing_toc',
                    'file': rel,
                    'line': 1,
                    'message': (
                        f'Reference file is {line_count} lines but has '
                        'no table of contents; Claude may only '
                        'partially read it.'
                    ),
                    'fix_hint': (
                        "Add a '## Contents' section near the top "
                        'listing the major sections.'
                    ),
                })

    return findings


# Inline-code path references. `check_reference_depth_and_toc` above only sees
# Markdown-hyperlink references `[text](path)`; these skills cite references
# and scripts as inline-code paths (`.claude/skills/forget/references/foo.md`,
# the abbreviated `forget/references/foo.md`, or the skill-relative
# `references/foo.md`), which that check misses. This scan verifies those
# skill-infrastructure paths resolve on disk. It also catches the bare
# abbreviated form that drops the `references/`/`scripts/` segment (a broken
# `forget/removal-mechanics.md` for `forget/references/removal-mechanics.md`),
# disk-gated on the leading segment naming a real skill dir (see
# `_is_bare_skill_ref`), which is the gap that let such a path ship before.
# Scoped to `.md`/`.py` skill files; wiki/raw/output/archive paths are excluded
# because they carry legitimate template examples that need not exist on disk.
INLINE_CODE_RE = re.compile(r'`([^`]+)`')
_SKILL_REF_EXCLUDE_PREFIXES = ('1-wiki/', '0-raw/', '2-outputs/', 'a-archive/')
_SKILL_REF_TEMPLATE_CHARS = set('{}<>*$…')


def _looks_like_skill_ref(token: str) -> bool:
    """True if `token` is a concrete skill-infra path worth resolving."""
    if not (token.endswith('.md') or token.endswith('.py')):
        return False
    if '/' not in token:
        return False
    if any(c in token for c in _SKILL_REF_TEMPLATE_CHARS):
        return False
    if token.startswith(_SKILL_REF_EXCLUDE_PREFIXES):
        return False
    return (
        token.startswith('.claude/')
        or token.startswith(('references/', 'scripts/'))
        or '/references/' in token
        or '/scripts/' in token
        or token.endswith('/SKILL.md')
    )


def _is_bare_skill_ref(token: str, repo_root: Path) -> bool:
    """True if `token` is a bare `<skill>/<file>.md|.py` reference.

    The abbreviated citation form drops the `references/`/`scripts/`
    segment, so `_looks_like_skill_ref` misses it. Disk-gate on the leading
    segment naming a real skill directory, so only a genuine skill
    reference (not an arbitrary two-segment path in prose) is a candidate.
    """
    if not (token.endswith('.md') or token.endswith('.py')):
        return False
    if token.count('/') != 1:
        return False
    if any(c in token for c in _SKILL_REF_TEMPLATE_CHARS):
        return False
    if token.startswith(_SKILL_REF_EXCLUDE_PREFIXES):
        return False
    first_segment = token.split('/', 1)[0]
    return (repo_root / '.claude' / 'skills' / first_segment).is_dir()


def _skill_ref_resolves(
    token: str, skill_dir: Path, repo_root: Path
) -> bool:
    """True if `token` resolves under the repo root, .claude/skills/,
    or the skill dir.
    """
    bases = (repo_root, repo_root / '.claude' / 'skills', skill_dir)
    return any((base / token).exists() for base in bases)


def check_inline_code_refs(
    skill_dir: Path,
    repo_root: Path,
    files: list[tuple[str, list[str], int]],
) -> list[dict[str, Any]]:
    """Flag inline-code skill-infra paths (.md/.py) that resolve nowhere.

    `files` is a list of (file_rel, lines, line_offset) to scan — SKILL.md
    (body lines, offset = frontmatter end) plus each reference file (full
    lines, offset 0). Fenced code blocks are skipped: a path inside a bash
    example is illustrative, not a reference. One finding per distinct
    broken token.
    """
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for file_rel, lines, line_offset in files:
        in_code_fence = False
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                in_code_fence = not in_code_fence
                continue
            if in_code_fence:
                continue
            for span in INLINE_CODE_RE.findall(line):
                for raw in span.split():
                    # Drop an anchor, leading brackets, and trailing
                    # sentence punctuation — but NOT a leading '.', which is
                    # part of `.claude/…` paths.
                    token = (
                        raw.split('#', 1)[0].lstrip('([').rstrip('.,;:)]')
                    )
                    if not (
                        _looks_like_skill_ref(token=token)
                        or _is_bare_skill_ref(
                            token=token, repo_root=repo_root
                        )
                    ):
                        continue
                    if _skill_ref_resolves(
                        token=token, skill_dir=skill_dir, repo_root=repo_root
                    ):
                        continue
                    if token in seen:
                        continue
                    seen.add(token)
                    findings.append({
                        'severity': 'warning',
                        'check_id': 'broken_inline_ref',
                        'file': file_rel,
                        'line': line_offset + i + 1,
                        'message': (
                            f"Inline-code path '{token}' references a skill "
                            'file that resolves nowhere on disk (checked repo '
                            'root, .claude/skills/, and the skill dir).'
                        ),
                        'fix_hint': (
                            f"Fix the path to an existing file, or if "
                            f"'{token}' is illustrative, put it in a fenced "
                            'code block.'
                        ),
                    })
    return findings


def find_repo_root(skill_dir: Path) -> Path | None:
    """Walk up from the skill dir to the repo root.

    The repo root is the ancestor holding both `.claude/` and `CLAUDE.md`.
    """
    for anc in [skill_dir, *skill_dir.parents]:
        if (anc / '.claude').is_dir() and (anc / 'CLAUDE.md').exists():
            return anc
    return None


def main() -> int:
    args = sys.argv[1:]
    single_file = False
    if '--single-file' in args:
        single_file = True
        args = [a for a in args if a != '--single-file']
    if len(args) != 1:
        print(
            'Usage: python check_structure.py '
            '<skill-dir-or-SKILL.md> [--single-file]',
            file=sys.stderr,
        )
        return 2

    target = Path(args[0]).expanduser().resolve()
    if not target.exists():
        print(f'Error: path not found: {target}', file=sys.stderr)
        return 2

    if target.is_dir():
        skill_dir = target
        skill_md = target / 'SKILL.md'
    elif target.name == 'SKILL.md':
        skill_dir = target.parent
        skill_md = target
    else:
        # Could be a path like /path/to/skill-dir/SKILL.md misnamed;
        # bail loudly.
        print(
            f'Error: input must be a skill directory or a SKILL.md file '
            f'(got {target.name})',
            file=sys.stderr,
        )
        return 2

    if not skill_md.exists():
        print(f'Error: SKILL.md not found at {skill_md}', file=sys.stderr)
        return 2

    fm, fm_end, body_lines = load_skill_md(skill_md_path=skill_md)

    findings: list[dict[str, Any]] = []
    findings += check_frontmatter(fm=fm, skill_md_rel='SKILL.md')
    findings += check_body_length(
        body_lines=body_lines,
        frontmatter_end_line=fm_end,
        skill_md_rel='SKILL.md',
    )
    findings += check_html_tags(
        markdown_lines=body_lines,
        line_offset=fm_end,
        file_rel='SKILL.md',
    )
    findings += check_paths(
        body_lines=body_lines,
        frontmatter_end_line=fm_end,
        skill_md_rel='SKILL.md',
    )

    # Reference checks only run on full-directory mode. In single-file
    # mode we treat the input as a standalone file and don't touch
    # siblings on disk.
    if not single_file:
        body_text = '\n'.join(body_lines)
        findings += check_reference_depth_and_toc(
            skill_dir=skill_dir,
            body_text=body_text,
        )
        # Inline-code path references (the syntax this repo's skills use to
        # cite refs/scripts) — resolve them across SKILL.md and every
        # reference file. Needs the repo root to resolve `.claude/…` and
        # abbreviated `<skill>/references/…` paths; skip if not found.
        repo_root = find_repo_root(skill_dir=skill_dir)
        if repo_root is not None:
            scan_files: list[tuple[str, list[str], int]] = [
                ('SKILL.md', body_lines, fm_end),
            ]
            for ref in sorted(skill_dir.glob('references/*.md')):
                try:
                    ref_lines = ref.read_text(encoding='utf-8').splitlines()
                except (OSError, UnicodeDecodeError):
                    continue
                scan_files.append(
                    (ref.relative_to(skill_dir).as_posix(), ref_lines, 0)
                )
            findings += check_inline_code_refs(
                skill_dir=skill_dir,
                repo_root=repo_root,
                files=scan_files,
            )

    print(json.dumps(findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
