#!/usr/bin/env python3
"""
check_synonyms.py — flag inconsistent-terminology candidates in SKILL.md.

Why a separate script? "Inconsistent terminology" is a known blind spot for
judgement-only review: when a body uses 'image', 'photo', and 'picture'
interchangeably in casual prose, the model often shrugs because they're
near-synonyms in English. But for a skill, switching between them creates
unnecessary friction for the reader. A deterministic scan of common synonym
groups surfaces every candidate so the LLM only has to decide *which* ones
genuinely refer to the same thing — not whether to look in the first place.

Output is the same JSON-finding shape as check_structure.py, but at severity
'suggestion' and with a special check_id 'terminology_candidate'. The
calling agent should review each candidate and decide whether to keep the
finding (genuine inconsistency) or discard it (the terms refer to different
things in this skill's domain).

Usage:
    python check_synonyms.py <skill-dir-or-SKILL.md>
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Each group is a set of terms commonly used interchangeably. The script
# flags any group where 2+ terms each appear at least MIN_OCCURRENCES
# times in the SKILL.md body. Sources: common patterns from real skills
# + the best-practices doc's example pairs.
SYNONYM_GROUPS: list[list[str]] = [
    # Visual content
    ['image', 'photo', 'picture'],
    # Users and customers
    ['customer', 'client', 'user', 'buyer'],
    # Documents
    ['document', 'file', 'doc'],
    # Records and entries
    ['record', 'row', 'entry', 'item'],
    # Form and field-like things
    ['field', 'box', 'element', 'cell'],
    # Web targets
    ['endpoint', 'route', 'url', 'path'],
    # Vendor/seller variants
    ['vendor', 'seller', 'supplier', 'merchant'],
    # Verbs: get/fetch
    ['extract', 'pull', 'get', 'retrieve', 'fetch'],
    # Verbs: save/store
    ['save', 'store', 'write', 'persist'],
    # Verbs: send/submit
    ['send', 'submit', 'post'],
    # Tickets/issues
    ['ticket', 'issue', 'case', 'incident'],
    # Orders/transactions
    ['order', 'purchase', 'transaction'],
]

# A single passing mention isn't enough to be inconsistent; the term must
# appear at least twice before we treat it as part of the body's
# vocabulary rather than a one-off reference.
MIN_OCCURRENCES = 2


def count_term(body_lower: str, term: str) -> int:
    """Count occurrences of `term` allowing simple inflections.

    e.g. 'image' matches 'image', 'images', "image's", "images'".
    """
    pattern = r'\b' + re.escape(term) + r"(?:s|'s|s')?\b"
    return len(re.findall(pattern, body_lower))


def find_synonym_clashes(body: str) -> list[dict]:
    """Return a list of finding dicts for groups where 2+ terms appear."""
    body_lower = body.lower()
    findings = []
    for group in SYNONYM_GROUPS:
        present = []
        for term in group:
            n = count_term(body_lower=body_lower, term=term)
            if n >= MIN_OCCURRENCES:
                present.append((term, n))
        if len(present) >= 2:
            terms_str = ', '.join(f"'{t}' ({n}x)" for t, n in present)
            # Arbitrary choice; the agent should make the real call.
            primary = present[0][0]
            findings.append({
                'severity': 'suggestion',
                'check_id': 'terminology_candidate',
                'file': 'SKILL.md',
                'line': None,
                'message': (
                    f'Body uses multiple near-synonyms that may refer '
                    f'to the same concept: {terms_str}.'
                ),
                'fix_hint': (
                    f"If these all refer to the same thing in your "
                    f"skill's domain, pick one term (e.g., '{primary}') "
                    f'and use it consistently throughout. If they refer '
                    f"to distinct things, briefly distinguish them so a "
                    f"reader doesn't have to guess."
                ),
            })
    return findings


def load_body(path: Path) -> str:
    """Strip YAML frontmatter and return the body text."""
    text = path.read_text(encoding='utf-8')
    lines = text.splitlines()
    if not lines or lines[0].strip() != '---':
        return text
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            return '\n'.join(lines[i + 1:])
    # Malformed frontmatter — return whole text rather than nothing.
    return text


def main() -> int:
    if len(sys.argv) != 2:
        print(
            'Usage: python check_synonyms.py <skill-dir-or-SKILL.md>',
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
        body = load_body(path=skill_md)
    except (OSError, UnicodeDecodeError) as exc:
        print(f'Error: cannot read {skill_md}: {exc}', file=sys.stderr)
        return 2
    findings = find_synonym_clashes(body=body)
    print(json.dumps(findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
