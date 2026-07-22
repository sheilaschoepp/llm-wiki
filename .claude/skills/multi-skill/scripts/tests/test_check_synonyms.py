"""Regression tests for check_synonyms.py.

Pins the per-skill allow-list behaviour a two-council review scrutinized:
subset-match suppression (a recorded confirmed-distinct group suppresses a
subset, but a newly-appearing term re-surfaces the candidate), and the
` — rationale` tail split that must NOT mis-split a hyphenated term such as
`belief-state`. Run from anywhere:

    python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'check_synonyms.py'

spec = importlib.util.spec_from_file_location('check_synonyms', SCRIPT)
cy = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cy)

RECORD_ENTRY = 'a record and a record, then an entry and one more entry'


def _has_candidate(findings: list[dict]) -> bool:
    return any(f['check_id'] == 'terminology_candidate' for f in findings)


class TestSubsetSuppression(unittest.TestCase):
    def test_candidate_fires_without_ignore(self) -> None:
        assert _has_candidate(cy.find_synonym_clashes(body=RECORD_ENTRY))

    def test_subset_is_suppressed(self) -> None:
        found = cy.find_synonym_clashes(
            body=RECORD_ENTRY,
            ignore_groups=[frozenset({'record', 'entry'})],
        )
        assert found == [], found

    def test_new_term_resurfaces_past_a_narrow_ignore(self) -> None:
        # 'row' joins the recorded record/entry pair -> present terms are no
        # longer a subset of the allow-list entry, so it re-surfaces.
        body = 'record and record, entry and entry, a row and a row'
        found = cy.find_synonym_clashes(
            body=body,
            ignore_groups=[frozenset({'record', 'entry'})],
        )
        assert _has_candidate(found), found


class TestLoadSynonymIgnore(unittest.TestCase):
    def test_drops_rationale_and_preserves_hyphens(self) -> None:
        text = (
            '# header\n\n'
            '## testskill\n\n'
            '- belief-state / multi-step — a hyphenated rationale tail\n'
            '- record / entry\n'
        )
        original = cy.SYNONYM_IGNORE_FILE
        try:
            with tempfile.NamedTemporaryFile(
                'w', suffix='.md', delete=False, encoding='utf-8'
            ) as fh:
                fh.write(text)
                tmp = Path(fh.name)
            cy.SYNONYM_IGNORE_FILE = tmp
            groups = cy.load_synonym_ignore(skill_name='testskill')
        finally:
            cy.SYNONYM_IGNORE_FILE = original
            tmp.unlink()
        assert frozenset({'belief-state', 'multi-step'}) in groups, groups
        assert frozenset({'record', 'entry'}) in groups, groups
        # Hyphenated terms kept whole, not split on the hyphen.
        flat = {term for g in groups for term in g}
        assert 'belief' not in flat and 'state' not in flat, flat
        # The rationale tail was dropped, not parsed as terms.
        assert 'rationale' not in flat and 'tail' not in flat, flat

    def test_unknown_skill_returns_empty(self) -> None:
        assert cy.load_synonym_ignore(skill_name='no-such-skill-xyz') == []


if __name__ == '__main__':
    unittest.main()
