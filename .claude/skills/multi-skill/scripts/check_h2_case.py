#!/usr/bin/env python3
"""
check_h2_case.py — flag sentence-case H2 headings in SKILL.md and refs.

Why a separate script? The H2 title-case rule
(.claude/skills/multi-skill/references/skill-authoring-checklist.md `h2_heading_case`) is meant to apply to SKILL.md
AND every references/*.md sibling. As a judgement check, it depended on
the agent remembering to scan every reference file every pass — and the
agent kept forgetting, fixing SKILL.md while leaving sentence-case H2s in
references/. Promoting the check to a deterministic script makes
coverage mechanical: every file the script walks is checked.

Output is the same JSON-finding shape as check_structure.py, with
check_id 'h2_heading_case' and severity 'suggestion'. H2s inside fenced
code blocks are skipped (markdown examples are content, not real
headings).

Usage:
    python check_h2_case.py <skill-dir-or-SKILL.md>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Words that stay lowercase mid-heading in title case (articles, short
# prepositions, conjunctions). The first word is always capitalized
# even if it appears here. Matches the convention in published style
# guides (Chicago, AP) at the permissive end.
TITLE_CASE_STOPWORDS = frozenset(
    {
        'a',
        'an',
        'and',
        'as',
        'at',
        'but',
        'by',
        'for',
        'in',
        'nor',
        'of',
        'on',
        'or',
        'the',
        'to',
        'up',
        'vs',
        'with',
    }
)

H2_RE = re.compile(r'^##\s+(.+?)\s*$')


def is_title_case(heading: str) -> bool:
    """Return True if `heading` follows the title-case convention.

    Rules
    -----
    - The first word must start with an uppercase letter.
    - Every subsequent word must start with an uppercase letter unless
      it is in TITLE_CASE_STOPWORDS.
    - Words that start with a non-letter (digits, punctuation,
      backticks) are skipped — they have no case.
    """
    words = heading.split()
    if not words:
        return True
    for index, word in enumerate(words):
        first_char = word[0]
        if not first_char.isalpha():
            continue
        if index == 0:
            if not first_char.isupper():
                return False
            continue
        lowered = word.lower().strip('.,:;!?')
        if lowered in TITLE_CASE_STOPWORDS:
            continue
        if not first_char.isupper():
            return False
    return True


def find_h2_case_issues(file_path: Path) -> list[dict]:
    """Walk one markdown file and return findings for sentence-case H2s.

    H2s inside fenced code blocks are ignored — they are markdown
    examples, not real section headers.
    """
    findings = []
    text = file_path.read_text(encoding='utf-8')
    in_code_fence = False
    for line_index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        match = H2_RE.match(line)
        if not match:
            continue
        heading_text = match.group(1)
        if is_title_case(heading=heading_text):
            continue
        findings.append(
            {
                'severity': 'suggestion',
                'check_id': 'h2_heading_case',
                'file': file_path.name,
                'line': line_index,
                'message': (
                    f"H2 heading '## {heading_text}' uses sentence case; "
                    f'project convention is title case.'
                ),
                'fix_hint': (
                    f'Rewrite as title case (capitalize the first letter '
                    f'of every word except short articles, prepositions, '
                    f'and conjunctions). See '
                    f'.claude/skills/multi-skill/references/skill-authoring-checklist.md `h2_heading_case`.'
                ),
            }
        )
    return findings


def resolve_target_files(target: Path) -> list[Path]:
    """Return the list of .md files to scan for a given input path.

    A directory yields SKILL.md plus every references/*.md sibling.
    A single SKILL.md file yields only that file (matches the
    --single-file mode of check_structure.py).
    """
    if target.is_dir():
        skill_md = target / 'SKILL.md'
        if not skill_md.exists():
            return []
        files = [skill_md]
        references_dir = target / 'references'
        if references_dir.is_dir():
            files.extend(sorted(references_dir.glob('*.md')))
        return files
    if target.name == 'SKILL.md' and target.is_file():
        return [target]
    return []


def annotate_findings_with_relative_path(
    findings: list[dict],
    file_path: Path,
    skill_root: Path,
) -> list[dict]:
    """Rewrite each finding's 'file' field to be relative to skill_root.

    SKILL.md stays as 'SKILL.md'; reference files become
    'references/<name>.md' so the output matches the path style used
    elsewhere in the linter (and in skill-linter reports).
    """
    relative = file_path.relative_to(skill_root)
    relative_str = str(relative)
    for finding in findings:
        finding['file'] = relative_str
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(
            'Usage: python check_h2_case.py <skill-dir-or-SKILL.md>',
            file=sys.stderr,
        )
        return 2

    target = Path(sys.argv[1]).expanduser().resolve()
    if not target.exists():
        print(f'Error: path not found: {target}', file=sys.stderr)
        return 2

    files = resolve_target_files(target=target)
    if not files:
        print(
            f'Error: input must be a skill directory containing '
            f'SKILL.md or a SKILL.md file (got {target.name})',
            file=sys.stderr,
        )
        return 2

    skill_root = target if target.is_dir() else target.parent

    all_findings: list[dict] = []
    for file_path in files:
        try:
            file_findings = find_h2_case_issues(file_path=file_path)
        except (OSError, UnicodeDecodeError):
            if file_path.name == 'SKILL.md':
                # An unreadable PRIMARY SKILL.md is a hard failure
                # (exit 2), matching check_synonyms / check_musts — never
                # a silent clean [] that would let the lint loop falsely
                # converge (the exact anti-pattern the SKILL.md self-lint
                # caveat warns about). Only an unreadable reference
                # sibling is skipped.
                print(f'Error: cannot read {file_path}', file=sys.stderr)
                return 2
            continue
        annotate_findings_with_relative_path(
            findings=file_findings,
            file_path=file_path,
            skill_root=skill_root,
        )
        all_findings.extend(file_findings)

    print(json.dumps(all_findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
