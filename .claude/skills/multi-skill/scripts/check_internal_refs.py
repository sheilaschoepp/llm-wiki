#!/usr/bin/env python3
"""
check_internal_refs.py — flag a skill's cross-references to its own
steps that no longer resolve.

Why this exists. A skill is edited far more often than it is rewritten,
and a common kind of damage from an edit is prose left pointing at
something the edit renumbered. The prose stays grammatical and
internally plausible, so no spell-check, link-check, or heading-check
sees it; only a reader who looks up the named step notices it is gone.
A real instance: a procedure grew a sub-step, the later sub-steps
shifted down, and a "carry the pointer forward to 8.4" line kept
pointing one step past its target.

One deterministic check:

- stale_step_reference — a `Step N` or sub-step `N.M` reference whose
  target is not among the numbered steps or bolded sub-step labels the
  same file defines. Runs only on SKILL.md, which is the file that
  defines a procedure; a reference file legitimately cites its parent's
  steps and defines none of its own.

Scope limits, stated so the check is not mistaken for more than it is.
It is an existence check: it cannot catch a reference that resolves to
the wrong existing step (`8.4` when `8.3` was meant), which needs a
reader. And it deliberately does not check renamed template *fields* (a
`Ledger:` line that became `Removed:`). That was tried and cut: a
backticked field in a skill's prose is usually a field of some other
document — a wiki page's `sources:`, a report's `result:` — so the check
fired on all fourteen skills in this repo without finding a single real
defect. Distinguishing a field this skill's own template dropped from a
field it never had needs the file's prior state, which a single-file
scanner does not have; a git-diff-based variant is the way to revive it.

Output is the same JSON-finding shape as check_structure.py, severity
'warning' — a dangling step reference is a factual error in the
procedure, not a style preference.

Usage:
    python check_internal_refs.py <skill-dir-or-SKILL.md>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# 'Step 7', 'Steps 7-8', 'Step 8.4', and bare sub-step '8.4' when it is
# not part of a version or a decimal in prose.
STEP_REF_RE = re.compile(r'\bSteps?\s+(\d+(?:\.\d+)?)(?:\s*[-–—]\s*(\d+(?:\.\d+)?))?')

# A numbered step at the start of a line: '1. **Load memory...'
STEP_DEF_RE = re.compile(r'^(\d+)\.\s+\*\*')

# A bolded sub-step label: '**8.0 — Resolve...' or '**8.1 — For each...'
SUBSTEP_DEF_RE = re.compile(r'\*\*(\d+\.\d+)\s*[—\-–]')


def split_fenced_and_prose(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    """
    Split a markdown file into fenced-block lines and prose lines.

    Returns
    -------
    fenced
        Every line inside a ``` fence, content only.
    prose
        (line_number, line) for every line outside a fence.
    """
    fenced: list[str] = []
    prose: list[tuple[int, str]] = []
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            fenced.append(line)
        else:
            prose.append((line_number, line))
    return fenced, prose


def collect_defined_steps(text: str) -> set[str]:
    """
    Return every step and sub-step number the file defines.
    """
    defined: set[str] = set()
    for line in text.splitlines():
        step_match = STEP_DEF_RE.match(line)
        if step_match:
            defined.add(step_match.group(1))
        for substep in SUBSTEP_DEF_RE.findall(line):
            defined.add(substep)
    return defined


def find_stale_step_references(
    prose: list[tuple[int, str]],
    defined: set[str],
    file_name: str,
    defines_procedure: bool,
) -> list[dict]:
    """
    Flag Step/sub-step cross-references with no matching definition.

    Only meaningful in a file that defines its own numbered procedure. A
    reference file legitimately cites its parent SKILL.md's steps
    ("SKILL.md Step 3 names each entry's home") and defines none of its
    own, so running the check there flags every such citation — the
    scanner's other dominant false positive.
    """
    if not defined or not defines_procedure:
        return []
    findings = []
    seen: set[str] = set()
    for line_number, line in prose:
        for match in STEP_REF_RE.finditer(line):
            for target in (match.group(1), match.group(2)):
                if target is None or target in seen:
                    continue
                if target in defined:
                    continue
                seen.add(target)
                findings.append(
                    {
                        'severity': 'warning',
                        'check_id': 'stale_step_reference',
                        'file': file_name,
                        'line': line_number,
                        'message': (
                            f'Reference to Step {target}, but this file '
                            f'defines no such step or sub-step — the '
                            f'procedure was likely renumbered.'
                        ),
                        'fix_hint': (
                            'Repoint the reference at the step that now '
                            'holds the named work, or restore the '
                            'missing step.'
                        ),
                    }
                )
    return findings


def check_file(file_path: Path, display_name: str) -> list[dict]:
    """
    Run both checks over one markdown file.
    """
    text = file_path.read_text(encoding='utf-8')
    _, prose = split_fenced_and_prose(text=text)
    defined = collect_defined_steps(text=text)
    findings = list(
        find_stale_step_references(
            prose=prose,
            defined=defined,
            file_name=display_name,
            defines_procedure=file_path.name == 'SKILL.md',
        )
    )
    return findings


def resolve_target_files(target: Path) -> list[Path]:
    """
    Return the .md files to scan.

    A directory yields SKILL.md plus every references/*.md sibling; a
    single SKILL.md yields only itself. Mirrors check_h2_case.py so both
    scanners cover the same surface.
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


def main() -> int:
    if len(sys.argv) != 2:
        print(
            'Usage: python check_internal_refs.py <skill-dir-or-SKILL.md>',
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
            file_findings = check_file(
                file_path=file_path,
                display_name=str(file_path.relative_to(skill_root)),
            )
        except (OSError, UnicodeDecodeError):
            if file_path.name == 'SKILL.md':
                # An unreadable primary SKILL.md is a hard failure, so a
                # lint loop cannot converge on a silent empty result.
                print(f'Error: cannot read {file_path}', file=sys.stderr)
                return 2
            continue
        all_findings.extend(file_findings)

    print(json.dumps(all_findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
