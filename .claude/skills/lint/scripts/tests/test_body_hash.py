"""Tests for body_hash.py — the script whose output drives every verified->draft
demotion, so a wrong hash silently mis-demotes or wrongly preserves a verified page.

These pin the load-bearing behaviour the module docstring promises:
- the body excludes frontmatter (mechanical metadata edits do not move the hash);
- every line carrying `*[unverified]*` is masked, so a marked claim can change
  freely while the page stays verified;
- the mask is line-scoped, so a marked claim's continuation line still counts
  (the "keep a marked claim to its single bullet line" contract);
- CRLF and LF inputs hash identically (existing stamps stay valid across line
  endings);
- a page with no markers hashes exactly as the same body without the masking;
- a frontmatter block opened but never closed raises ValueError rather than
  hashing the whole file and returning a valid-looking hash.

Run from anywhere:

    python3 -m unittest discover -s .claude/skills/lint/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'body_hash.py'              # scripts/body_hash.py

spec = importlib.util.spec_from_file_location('body_hash', SCRIPT)
bh = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bh)


def sha(body: str) -> str:
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


FM = '---\ntitle: X\nstatus: verified\n---\n'


class TestBodyHash(unittest.TestCase):
    """body_hash.body_hash: frontmatter exclusion, *[unverified]* masking, line endings, malformed frontmatter."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def write(self, text: str) -> str:
        """Write a page and return its path as a str (the module takes a path str)."""
        page = self.tmp / 'page.md'
        page.write_text(text, encoding='utf-8')
        return str(page)

    # --- frontmatter exclusion ---

    def test_frontmatter_excluded_from_hash(self) -> None:
        body = '# Title\n\nbody line\n'
        assert bh.body_hash(path=self.write(FM + body)) == sha(body)

    def test_frontmatter_edit_does_not_change_hash(self) -> None:
        body = '# Title\n\nbody line\n'
        a = bh.body_hash(path=self.write(FM + body))
        other = '---\ntitle: X\nstatus: draft\nupdated: 2026-01-01\n---\n'
        b = bh.body_hash(path=self.write(other + body))
        assert a == b

    def test_no_frontmatter_hashes_whole_file(self) -> None:
        text = '# Title\n\nno frontmatter here\n'
        assert bh.body_hash(path=self.write(text)) == sha(text)

    # --- *[unverified]* masking ---

    def test_marked_line_is_excluded(self) -> None:
        """A page with one marked claim hashes equal to the same page with that line gone."""
        marked = FM + '# T\n\n- plain claim\n- pending claim *[unverified]*\n'
        without = FM + '# T\n\n- plain claim\n'
        assert bh.body_hash(path=self.write(marked)) == bh.body_hash(path=self.write(without))

    def test_editing_marked_claim_does_not_move_hash(self) -> None:
        a = FM + '# T\n\n- pending one *[unverified]*\n'
        b = FM + '# T\n\n- a completely different pending claim *[unverified]*\n'
        assert bh.body_hash(path=self.write(a)) == bh.body_hash(path=self.write(b))

    def test_editing_unmarked_claim_moves_hash(self) -> None:
        a = FM + '# T\n\n- checked claim one\n'
        b = FM + '# T\n\n- checked claim two\n'
        assert bh.body_hash(path=self.write(a)) != bh.body_hash(path=self.write(b))

    def test_mask_is_line_scoped_continuation_still_counts(self) -> None:
        """Only the marker-bearing line is dropped; a continuation line still counts,
        so two pages differing only on a marked claim's continuation hash differently."""
        a = FM + '# T\n\n- claim *[unverified]*\n  continuation alpha\n'
        b = FM + '# T\n\n- claim *[unverified]*\n  continuation beta\n'
        assert bh.body_hash(path=self.write(a)) != bh.body_hash(path=self.write(b))

    def test_no_marker_page_unchanged_by_masking(self) -> None:
        body = '# T\n\n- a\n- b\n- c\n'
        assert bh.body_hash(path=self.write(FM + body)) == sha(body)

    def test_marker_inside_inline_code_is_not_masked(self) -> None:
        """A `*[unverified]*` MENTION inside inline code is documentation, not a
        pending claim, so the line's real content still counts toward the hash
        (mirrors check_wiki.py, which counts markers only outside code spans)."""
        a = FM + '# T\n\n- the `*[unverified]*` marker means pending -- alpha\n'
        b = FM + '# T\n\n- the `*[unverified]*` marker means pending -- beta\n'
        # editing the non-code content moves the hash: the line is not masked away
        assert bh.body_hash(path=self.write(a)) != bh.body_hash(path=self.write(b))
        # and the line is not dropped: the page does not hash as if the line were gone
        assert bh.body_hash(path=self.write(a)) != bh.body_hash(path=self.write(FM + '# T\n\n'))

    # --- line endings ---

    def test_crlf_and_lf_hash_identically(self) -> None:
        lf = FM + '# T\n\n- a\n- b\n'
        crlf = lf.replace('\n', '\r\n')
        assert bh.body_hash(path=self.write(lf)) == bh.body_hash(path=self.write(crlf))

    # --- malformed frontmatter ---

    def test_unterminated_frontmatter_raises(self) -> None:
        text = '---\ntitle: X\nstatus: verified\n# no closing delimiter, just body\n'
        with self.assertRaises(ValueError):
            bh.body_hash(path=self.write(text))


if __name__ == '__main__':
    unittest.main()
