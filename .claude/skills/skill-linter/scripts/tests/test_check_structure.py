"""Regression tests for check_structure.py.

Pins the defects a two-council review found in the freshly-shipped checks:
the `broken_inline_ref` recognizer was blind to the bare `<skill>/<file>.md`
shape it documented itself as catching (false negative), and it must NOT
fire on a fenced illustrative path (false positive); `body_over_length`
deliberately counts fenced code and tables (a token-cost proxy, not a prose
count) and its explanatory message tail must match the budget that tripped.
Run from anywhere:

    python3 -m unittest discover -s .claude/skills/skill-linter/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'check_structure.py'
REPO = HERE.parents[5]                                   # repo root
SKILL_DIR = REPO / '.claude' / 'skills' / 'skill-linter'

spec = importlib.util.spec_from_file_location('check_structure', SCRIPT)
cs = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cs)

FQ_REF = '.claude/skills/forget/references/removal-mechanics.md'


class TestSkillRefRecognizers(unittest.TestCase):
    def test_looks_like_skill_ref_standard_forms(self) -> None:
        looks = cs._looks_like_skill_ref
        assert looks(token='references/checks.md')
        assert looks(token='scripts/check_structure.py')
        assert looks(token=FQ_REF)
        assert looks(token='forget/references/x.md')
        assert looks(token='some-skill/SKILL.md')

    def test_looks_like_skill_ref_rejects(self) -> None:
        # The bare 2-segment abbreviated form is NOT matched here — that is
        # the blind spot _is_bare_skill_ref was added to cover.
        looks = cs._looks_like_skill_ref
        assert not looks(token='forget/removal-mechanics.md')
        assert not looks(token='<skill>/x.md')      # template char
        assert not looks(token='1-wiki/foo.md')     # excluded prefix
        assert not looks(token='plain.md')          # no slash

    def test_is_bare_skill_ref_disk_gated(self) -> None:
        # The founding-bug shape: real skill dir, dropped segment.
        bare = cs._is_bare_skill_ref
        assert bare(token='forget/removal-mechanics.md', repo_root=REPO)
        assert bare(token='multi-skill/multi-skill-memory.md', repo_root=REPO)

    def test_is_bare_skill_ref_declines_non_candidates(self) -> None:
        # Leading segment is not a real skill dir -> not a candidate, so an
        # ordinary two-segment path in prose is never flagged.
        bare = cs._is_bare_skill_ref
        assert not bare(token='notaskill/foo.md', repo_root=REPO)
        assert not bare(token='<skill>/x.md', repo_root=REPO)  # template
        assert not bare(token='a/b/c.md', repo_root=REPO)      # two slashes
        assert not bare(token='SKILL.md', repo_root=REPO)      # no slash


class TestBrokenInlineRefIntegration(unittest.TestCase):
    def _scan(self, lines: list[str]) -> list[dict]:
        return cs.check_inline_code_refs(
            skill_dir=SKILL_DIR,
            repo_root=REPO,
            files=[('SKILL.md', lines, 0)],
        )

    def test_flags_bare_broken_two_segment_ref(self) -> None:
        # Regression: the bare form that ships broken must now be caught.
        found = self._scan(['see `forget/removal-mechanics.md` here'])
        msgs = [f['message'] for f in found]
        assert any('forget/removal-mechanics.md' in m for m in msgs), found

    def test_does_not_flag_resolvable_ref(self) -> None:
        found = self._scan(['see `references/checks.md` for detail'])
        assert found == [], found

    def test_does_not_flag_fenced_illustrative_path(self) -> None:
        # A path inside a fenced block is an example, not a reference.
        found = self._scan(
            ['```', 'a broken `forget/removal-mechanics.md`', '```']
        )
        assert found == [], found

    def test_does_not_flag_templated_path(self) -> None:
        found = self._scan(['the abbreviated `<skill>/removal-mechanics.md`'])
        assert found == [], found


class TestBodyLength(unittest.TestCase):
    def _run(self, body: list[str]) -> list[dict]:
        return cs.check_body_length(
            body_lines=body, frontmatter_end_line=1, skill_md_rel='SKILL.md'
        )

    def test_fenced_code_is_counted(self) -> None:
        # The word budget is a token-cost proxy: fenced content costs tokens,
        # so it is counted (NOT stripped). A body over budget only because of
        # a fenced block must still trip.
        big = ' '.join(['x'] * (cs.SKILL_MD_MAX_WORDS + 1))
        found = self._run(['```', big, '```'])
        assert found and found[0]['check_id'] == 'body_over_length', found

    def test_message_tail_word_trip(self) -> None:
        big = ' '.join(['x'] * (cs.SKILL_MD_MAX_WORDS + 1))
        msg = self._run([big])[0]['message']
        assert 'primary signal' in msg, msg
        assert 'under-measures' in msg, msg

    def test_message_tail_line_only_trip(self) -> None:
        # >500 short lines but under the word budget: the line count is what
        # tripped, so the tail must NOT claim the line count under-measures.
        msg = self._run(['w'] * (cs.SKILL_MD_MAX_LINES + 1))[0]['message']
        assert 'under-measures' not in msg, msg
        assert 'within budget' in msg, msg

    def test_under_budget_is_clean(self) -> None:
        assert self._run(['a few words']) == []


class TestFindRepoRoot(unittest.TestCase):
    def test_finds_real_repo_root(self) -> None:
        assert cs.find_repo_root(skill_dir=SKILL_DIR) == REPO


if __name__ == '__main__':
    unittest.main()
