"""Live-wiki acceptance tests for ``check_wiki.py``.

Run explicitly from any working copy whose current ``1-wiki`` content should
satisfy all repository-health anchors:

    python3 .claude/skills/multi-skill/scripts/acceptance_check_wiki.py

These checks intentionally read the working wiki. They are separate from the
fixture-based regression suite so a real maintenance backlog is reported as
vault health, not misattributed to a code change.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parent / 'check_wiki.py'
REPO = HERE.parents[4]
WIKI = REPO / '1-wiki'

spec = importlib.util.spec_from_file_location('check_wiki', SCRIPT)
cw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cw)


class TestLiveWikiAcceptance(unittest.TestCase):
    """Require the current working wiki to satisfy content-health anchors."""

    @staticmethod
    def _page_findings(check_id: str) -> list[dict]:
        findings: list[dict] = []
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            directory = WIKI / folder
            if not directory.exists():
                continue
            for page in sorted(directory.glob('*.md')):
                findings.extend(
                    finding
                    for finding in cw.check_page(path=page, wiki_root=WIKI)
                    if finding['check_id'] == check_id
                )
        return findings

    def test_real_wiki_has_no_square_citations(self) -> None:
        self.assertEqual(self._page_findings('citation_bracket_style'), [])

    def test_real_wiki_has_no_unisolated_embeds(self) -> None:
        self.assertEqual(self._page_findings('embed_not_isolated'), [])

    def test_real_wiki_has_no_hyphenated_open_compounds(self) -> None:
        self.assertEqual(self._page_findings('hyphenated_open_compound'), [])

    def test_real_wiki_has_no_hyphenated_open_compound_nouns(self) -> None:
        self.assertEqual(
            self._page_findings('hyphenated_open_compound_noun'), []
        )

    def test_real_wiki_log_hot_timed_and_sorted(self) -> None:
        findings = [
            finding
            for finding in cw.check_chronology(wiki_root=WIKI)
            if finding['check_id'].startswith('chronology')
        ]
        self.assertEqual(findings, [])


if __name__ == '__main__':
    unittest.main()
