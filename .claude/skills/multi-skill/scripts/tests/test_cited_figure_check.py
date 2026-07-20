"""Tests for cited_figure_check.py — the standalone cross-source mis-location
backstop.

Covers the pure parsing/matching helpers (mask_spans, extract_figures,
extract_deeplinks, figure_present) and check_page driven by a fake page-text
cache, so no real PDF is opened. The PDF-reading path (RawTextCache._extract) is
integration glue over PyMuPDF and is not unit-tested here.

Run from anywhere:

    python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'cited_figure_check.py'     # scripts/cited_figure_check.py
REPO = HERE.parents[5]                                 # repo root

spec = importlib.util.spec_from_file_location('cited_figure_check', SCRIPT)
cfc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cfc)


DEEPLINK = '[[0-raw/papers/SrcA.pdf#page=4|sec. 3.1, p. 4]]'
DEEPLINK_B = '[[0-raw/papers/SrcB.pdf#page=2|sec. 1, p. 2]]'


class FakeCache:
    """Stand-in for RawTextCache: returns preset text per (raw_rel, page_n)."""

    def __init__(self, pages: dict[tuple[str, int], str | None]) -> None:
        self._pages = pages

    def page_text(self, *, raw_rel: str, page_n: int) -> str | None:
        return self._pages.get((raw_rel, page_n))


class TestMaskSpans(unittest.TestCase):

    def test_blanks_wikilink_and_preserves_length(self) -> None:
        line = f'gap of 37.2% ({DEEPLINK})'

        masked = cfc.mask_spans(line=line)

        self.assertEqual(len(masked), len(line),
                         msg='mask must preserve column offsets')
        self.assertNotIn('page=4', masked,
                         msg='wikilink internals must be blanked')
        self.assertIn('37.2%', masked,
                      msg='prose outside the wikilink must survive')

    def test_blanks_inline_code(self) -> None:
        masked = cfc.mask_spans(line='holds `3.14` in code')

        self.assertNotIn('3.14', masked)


class TestExtractFigures(unittest.TestCase):

    def test_finds_decimal_and_percentage(self) -> None:
        figs = cfc.extract_figures(line='rose 18.3 to 37.2% overall')

        self.assertEqual(set(figs), {'18.3', '37.2%'})

    def test_skips_bare_integer(self) -> None:
        self.assertEqual(cfc.extract_figures(line='across 48 datasets'), [])

    def test_skips_version_and_model_ids(self) -> None:
        line = 'gpt-3.5 and v2.0 and 3.1.4 release'

        self.assertEqual(cfc.extract_figures(line=line), [],
                         msg='ids with a leading letter/hyphen/dot are not figures')

    def test_keeps_sentence_final_decimal(self) -> None:
        # A trailing period must not defeat the version-string guard.
        self.assertEqual(cfc.extract_figures(line='the gain was 37.2.'), ['37.2'])

    def test_ignores_locator_number_inside_deeplink(self) -> None:
        # The only decimals here (`3.1`, `4`) live inside the masked deep-link.
        figs = cfc.extract_figures(line=f'a qualitative claim ({DEEPLINK})')

        self.assertEqual(figs, [],
                         msg='a locator number must not be read as a claim figure')


class TestExtractDeeplinks(unittest.TestCase):

    def test_parses_path_and_page(self) -> None:
        links = cfc.extract_deeplinks(line=f'x ({DEEPLINK})')

        self.assertEqual(links, [('0-raw/papers/SrcA.pdf', 4)])

    def test_parses_multiple(self) -> None:
        links = cfc.extract_deeplinks(line=f'x ({DEEPLINK}; {DEEPLINK_B})')

        self.assertEqual(
            links,
            [('0-raw/papers/SrcA.pdf', 4), ('0-raw/papers/SrcB.pdf', 2)])

    def test_no_deeplink_returns_empty(self) -> None:
        self.assertEqual(cfc.extract_deeplinks(line='no citation here'), [])


class TestFigurePresent(unittest.TestCase):

    def test_present_exact(self) -> None:
        self.assertTrue(cfc.figure_present(token='37.2%', page_text='is 37.2%.'))

    def test_present_via_decimal_core_of_percentage(self) -> None:
        self.assertTrue(
            cfc.figure_present(token='37.2%', page_text='value 37.2 reported'))

    def test_present_whitespace_tolerant(self) -> None:
        self.assertTrue(
            cfc.figure_present(token='37.2%', page_text='37.2\n%'))

    def test_absent(self) -> None:
        self.assertFalse(
            cfc.figure_present(token='37.2%', page_text='no such number, 18.3'))


class TestCheckPage(unittest.TestCase):

    def _write(self, body: str) -> Path:
        tmp = Path(tempfile.mkdtemp()) / '1-wiki' / 'concepts'
        tmp.mkdir(parents=True)
        page = tmp / 'demo.md'
        page.write_text(body, encoding='utf-8')
        return page

    def _run(self, body: str,
             pages: dict[tuple[str, int], str | None]) -> list[dict]:
        page = self._write(body)
        repo_root = page.parents[2]
        return cfc.check_page(path=page, repo_root=repo_root,
                              cache=FakeCache(pages))

    def test_figure_on_cited_page_no_finding(self) -> None:
        body = f'> - gap of 37.2% ({DEEPLINK})\n'
        pages = {('0-raw/papers/SrcA.pdf', 4): 'we drop 37.2% of items'}

        self.assertEqual(self._run(body, pages), [])

    def test_figure_off_cited_page_flags(self) -> None:
        body = f'> - gap of 37.2% ({DEEPLINK})\n'
        pages = {('0-raw/papers/SrcA.pdf', 4): 'unrelated text, no figure'}

        findings = self._run(body, pages)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['check_id'], 'cited_figure_off_page')
        self.assertEqual(findings[0]['severity'], 'warning')
        self.assertIn('37.2%', findings[0]['message'])

    def test_two_cited_pages_figure_on_one_no_finding(self) -> None:
        body = f'> - contrast 37.2% ({DEEPLINK}; {DEEPLINK_B})\n'
        pages = {
            ('0-raw/papers/SrcA.pdf', 4): 'nothing here',
            ('0-raw/papers/SrcB.pdf', 2): 'the 37.2% appears here',
        }

        self.assertEqual(self._run(body, pages), [],
                         msg='present on either cited page must pass')

    def test_two_cited_pages_figure_on_neither_flags(self) -> None:
        # The mis-location signature: a figure cited to two pages, on neither.
        body = f'> - contrast 37.2% ({DEEPLINK}; {DEEPLINK_B})\n'
        pages = {
            ('0-raw/papers/SrcA.pdf', 4): 'nothing here',
            ('0-raw/papers/SrcB.pdf', 2): 'nor here',
        }

        self.assertEqual(len(self._run(body, pages)), 1)

    def test_unreadable_cited_page_skipped(self) -> None:
        body = f'> - gap of 37.2% ({DEEPLINK})\n'
        pages = {('0-raw/papers/SrcA.pdf', 4): None}

        self.assertEqual(self._run(body, pages), [],
                         msg='an unreadable page is "cannot check", not off-page')

    def test_bullet_without_deeplink_ignored(self) -> None:
        body = '> - a bare 37.2% with no citation\n'

        self.assertEqual(self._run(body, {}), [])


if __name__ == '__main__':
    unittest.main()
