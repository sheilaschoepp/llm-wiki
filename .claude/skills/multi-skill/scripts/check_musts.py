#!/usr/bin/env python3
"""
check_musts.py — flag candidate heavy-handed imperatives in SKILL.md body.

Why a separate script? "ALWAYS X / NEVER X / MUST X" without an explanation
of *why* is a known antipattern: today's models follow rules better when
they understand the reason, and rules without reasons read as scolding. But
judgement-only review misses these about 75% of the time once the lint pass
has other findings to focus on (we measured this).

This script scans the body for ALL-CAPS imperatives. For each one, it checks
whether the surrounding paragraph contains an explanation cue ('because',
'so that', 'to avoid', 'otherwise', '—', etc.). Imperatives WITHOUT such a
cue are emitted as 'heavy_handed_must_candidate' findings for the agent to
confirm.

The agent's job, on receiving these candidates: read each one in context
and decide whether the imperative genuinely needs more reasoning or
whether the why is implicit/obvious. Drop the candidate if it's fine,
keep it (ideally as 'heavy_handed_musts') if the directive really would
land better with a brief explanation.

Usage:
    python check_musts.py <skill-dir-or-SKILL.md>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Imperative tokens we look for. Word boundaries on both sides;
# case-sensitive so we only match the all-caps form (we don't want to
# flag "must" in normal prose).
IMPERATIVE_RE = re.compile(
    r"\b(?:ALWAYS|NEVER|MUST(?:\s+NOT)?|DO\s+NOT|DON'T)\b"
)

# Words/phrases that signal an explanation is nearby. Case-insensitive.
# The em-dash and parenthetical are good signals because authors often
# attach reasoning after them.
EXPLANATION_CUES = [
    r'\bbecause\b',
    r'\bsince\b',
    r'\bso that\b',
    r'\bto avoid\b',
    r'\bto prevent\b',
    r'\bto ensure\b',
    r'\botherwise\b',
    r'\botherwise[,:]',
    r"\bif you don'?t\b",
    r'\bif not\b',
    r'\bthis is because\b',
    # Em-dash often precedes reasoning.
    r'—',
    # En-dash, ditto.
    r'–',
    # Parenthetical aside on the same line.
    r'\(.*\)',
]
EXPLANATION_RE = re.compile('|'.join(EXPLANATION_CUES), re.IGNORECASE)


def strip_inline_code(text: str) -> str:
    """Blank out inline-code spans, preserving length and newlines.

    A backticked token such as `NEVER` documents the imperative
    literally rather than issuing it, so it must not be matched as a
    prose imperative (mirrors check_structure.py's prose handling).
    Blanking to equal-length spaces — and keeping newlines — leaves every
    later character offset and line count unchanged, so the imperative's
    reported line stays correct.
    """

    def _blank(match: re.Match) -> str:
        return ''.join(
            '\n' if char == '\n' else ' ' for char in match.group(0)
        )

    return re.sub(r'`[^`]*`', _blank, text)


def load_body_with_offsets(skill_md: Path) -> tuple[str, int]:
    """Return (body_text, body_start_line) where body_start_line is the
    1-indexed line in the original file at which the body begins (i.e.
    the line right after the closing `---` of frontmatter, or 1 if
    there's no frontmatter)."""
    text = skill_md.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return text, 1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            # +2: line after the closing ---
            return '\n'.join(lines[i + 1 :]), i + 2
    return text, 1


def split_paragraphs(
    body: str,
    body_start_line: int,
) -> list[tuple[int, str]]:
    """Split body into paragraphs separated by blank lines.

    Returns list of (start_line_in_file, paragraph_text). Paragraph
    boundaries are at blank lines OR at fenced code-block boundaries
    (we don't want to treat code as prose).
    """
    paragraphs = []
    current_lines: list[str] = []
    current_start = body_start_line
    in_code_fence = False

    for offset, line in enumerate(body.splitlines()):
        line_no = body_start_line + offset
        stripped = line.strip()

        if stripped.startswith('```'):
            # Flush any in-progress paragraph before/after a fence.
            if current_lines:
                paragraphs.append((current_start, '\n'.join(current_lines)))
                current_lines = []
            in_code_fence = not in_code_fence
            current_start = line_no + 1
            continue

        if in_code_fence:
            continue  # skip code content entirely

        if not stripped:
            if current_lines:
                paragraphs.append((current_start, '\n'.join(current_lines)))
                current_lines = []
            current_start = line_no + 1
            continue

        if not current_lines:
            current_start = line_no
        current_lines.append(line)

    if current_lines:
        paragraphs.append((current_start, '\n'.join(current_lines)))
    return paragraphs


def find_unexplained_imperatives(skill_md: Path) -> list[dict]:
    body, body_start = load_body_with_offsets(skill_md=skill_md)
    findings = []

    for para_start_line, para_text in split_paragraphs(
        body=body,
        body_start_line=body_start,
    ):
        prose_text = strip_inline_code(text=para_text)
        imperatives = list(IMPERATIVE_RE.finditer(prose_text))
        if not imperatives:
            continue
        if EXPLANATION_RE.search(prose_text):
            # Paragraph already contains reasoning; assume it's fine.
            continue

        # Find the line of the first imperative within the paragraph for
        # a useful pointer. prose_text preserves para_text's offsets and
        # newlines, so this line math stays correct.
        first = imperatives[0]
        line_offset = prose_text[: first.start()].count('\n')
        line_in_file = para_start_line + line_offset
        words = sorted({m.group(0) for m in imperatives})
        findings.append(
            {
                'severity': 'suggestion',
                'check_id': 'heavy_handed_must_candidate',
                'file': 'SKILL.md',
                'line': line_in_file,
                'message': (
                    f'Paragraph contains all-caps imperative(s) '
                    f'({", ".join(words)}) but no obvious explanation of why.'
                ),
                'fix_hint': (
                    'If the rule has a non-obvious reason, add a brief '
                    "'because ...' or '— otherwise ...' so the model reading "
                    'this understands the why. Models follow well-justified '
                    'rules more reliably than bare directives. If the '
                    'reasoning is already obvious from context, you can '
                    'drop this candidate.'
                ),
            }
        )
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(
            'Usage: python check_musts.py <skill-dir-or-SKILL.md>',
            file=sys.stderr,
        )
        return 2

    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.exists():
        print(f'Error: path not found: {target}', file=sys.stderr)
        return 2

    if target.is_dir():
        skill_md = target / 'SKILL.md'
    elif target.name == 'SKILL.md':
        skill_md = target
    else:
        print(
            f'Error: input must be a skill directory or a SKILL.md '
            f'file (got {target.name})',
            file=sys.stderr,
        )
        return 2

    if not skill_md.exists():
        print(f'Error: SKILL.md not found at {skill_md}', file=sys.stderr)
        return 2

    try:
        findings = find_unexplained_imperatives(skill_md=skill_md)
    except (OSError, UnicodeDecodeError) as exc:
        print(f'Error: cannot read {skill_md}: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
