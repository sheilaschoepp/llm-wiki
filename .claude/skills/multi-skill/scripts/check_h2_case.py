#!/usr/bin/env python3
"""
check_h2_case.py — flag title-case H2 headings in SKILL.md and refs.

Why a separate script? The H2 sentence-case rule
(.claude/skills/multi-skill/references/skill-authoring-checklist.md
`h2_heading_case`) is meant to apply to SKILL.md AND every
references/*.md sibling. As a judgement check, it depended on the agent
remembering to scan every reference file every pass — and the agent kept
forgetting, fixing SKILL.md while leaving title-case H2s in
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

# Words that legitimately keep a capital mid-heading under sentence
# case: proper nouns, product names, and the numbered procedure labels
# this repo capitalizes in prose ("Step 4", "Council 1"). Everything
# else capitalized after the first word is a title-case remnant.
#
# Acronyms need no entry — the flag pattern only matches Capitalized
# words whose remainder is lowercase, so LLM, PDF, IDs, and TL;DR are
# structurally excluded.
PROPER_NOUNS = frozenset(
    {
        'Anthropic',
        'Bash',
        'BibTeX',
        'Canadian',
        'Claude',
        'Council',
        'English',
        'GitHub',
        'LaTeX',
        'Layer',
        'Markdown',
        'Obsidian',
        'Overleaf',
        'Part',
        'Pattern',
        'Python',
        'Step',
        'Steps',
    }
)

# A title-case remnant: capital first letter, lowercase remainder.
# Deliberately excludes ALLCAPS and mixedCase tokens.
TITLE_CASE_WORD_RE = re.compile(r"^[A-Z][a-z]+(?:[-'][A-Za-z]+)*$")

H2_RE = re.compile(r'^##\s+(.+?)\s*$')


def find_identifier_indices(words: list[str]) -> set[int]:
    """
    Return indices of words that are identifiers, not prose.

    A heading may name a literal argument the skill is invoked with
    (`## Packet: schema-language`). Title-casing such a token would
    rename the thing it points at, so it carries no case to correct and
    must be skipped rather than flagged — the same carve-out the
    checklist already makes for backticked code tokens, extended to the
    bare slugs this repo writes after a `Label:` word.

    A word qualifies only when BOTH hold:

    - it follows a colon-terminated label earlier in the same heading
      (`Packet:`, `Mode:`), and
    - it is entirely lowercase, and either contains a hyphen
      (`schema-language`) or is the only word after the colon
      (`naming`).

    The two conditions together keep prose out. `## Note: this is prose`
    has three unhyphenated words after the colon, so none is treated as
    an identifier and every one is still checked. A hyphenated compound
    in ordinary prose (`## Working with well-formed pages`) follows no
    colon, so it is untouched.
    """
    colon_index = next(
        (i for i, word in enumerate(words) if word.endswith(':')),
        None,
    )
    if colon_index is None:
        return set()
    tail = list(range(colon_index + 1, len(words)))
    if not tail:
        return set()
    single = len(tail) == 1
    identifiers = set()
    for index in tail:
        word = words[index]
        if word != word.lower():
            continue
        if '-' in word or single:
            identifiers.add(index)
    return identifiers


def find_title_case_words(heading: str) -> list[str]:
    """
    Return the words in `heading` that carry a title-case capital.

    Rules
    -----
    - The first word is exempt — sentence case capitalizes it.
    - A later word is flagged only when it matches
      TITLE_CASE_WORD_RE (capital, then lowercase), which structurally
      excludes acronyms (LLM, IDs) and mixedCase identifiers.
    - Words in PROPER_NOUNS are exempt.
    - Words starting with a non-letter (digits, punctuation, backticks)
      are skipped — they carry no case.
    - Identifier tokens after a `Label:` word are skipped; see
      find_identifier_indices.
    """
    words = heading.split()
    if not words:
        return []
    identifier_indices = find_identifier_indices(words=words)
    flagged = []
    for index, word in enumerate(words):
        if index == 0 or index in identifier_indices:
            continue
        if not word[0].isalpha():
            continue
        bare = word.strip('.,:;!?()[]')
        if bare in PROPER_NOUNS:
            continue
        if TITLE_CASE_WORD_RE.match(bare):
            flagged.append(bare)
    return flagged


def find_h2_case_issues(file_path: Path) -> list[dict]:
    """
    Walk one markdown file and return findings for title-case H2s.

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
        offenders = find_title_case_words(heading=heading_text)
        if not offenders:
            continue
        findings.append(
            {
                'severity': 'suggestion',
                'check_id': 'h2_heading_case',
                'file': file_path.name,
                'line': line_index,
                'message': (
                    f"H2 heading '## {heading_text}' uses title case; "
                    f'project convention is sentence case '
                    f'(capitalized: {", ".join(offenders)}).'
                ),
                'fix_hint': (
                    'Rewrite as sentence case: capitalize only the first '
                    'word, plus proper nouns and acronyms. Never re-case '
                    'a backticked code token or an identifier after a '
                    '`Label:` word. See '
                    '.claude/skills/multi-skill/references/'
                    'skill-authoring-checklist.md `h2_heading_case`.'
                ),
            }
        )
    return findings


def resolve_target_files(target: Path) -> list[Path]:
    """
    Return the list of .md files to scan for a given input path.

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
    """
    Rewrite each finding's 'file' field to be relative to skill_root.

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
                # An unreadable PRIMARY SKILL.md is a hard failure (exit
                # 2), matching check_synonyms / check_musts — never a
                # silent clean [] that would let the lint loop falsely
                # converge (the exact anti-pattern the SKILL.md
                # self-lint caveat warns about). Only an unreadable
                # reference sibling is skipped.
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
