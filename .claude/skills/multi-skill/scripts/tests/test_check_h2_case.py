"""
Regression tests for check_h2_case.py.

Pins the direction of the check and its four carve-outs. The direction
matters most: this check was inverted (it once flagged sentence case as
the defect), and an inverted scanner that silently returns [] on bad
input converges falsely — the failure mode the skill-linter loop cannot
catch on its own. So the suite asserts both that a title-case heading
IS flagged and that each exempt shape is NOT.

Run from anywhere:

python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests

The module is loaded by path so the tests do not depend on cwd or
packaging.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'check_h2_case.py'

spec = importlib.util.spec_from_file_location('check_h2_case', SCRIPT)
chc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(chc)


class TestFlagsTitleCase(unittest.TestCase):
    def test_flags_every_title_cased_word(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(heading='When To Invoke'),
            ['To', 'Invoke'],
        )

    def test_flags_a_single_offender(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(heading='Edge Cases'),
            ['Cases'],
        )

    def test_flags_hyphenated_compound(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(heading='The Hard Carve-Out'),
            ['Hard', 'Carve-Out'],
        )


class TestAcceptsSentenceCase(unittest.TestCase):
    def test_plain_sentence_case_is_clean(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(heading='Working with well-formed pages'),
            [],
        )

    def test_first_word_capital_is_exempt(self) -> None:
        self.assertEqual(chc.find_title_case_words(heading='Procedure'), [])


class TestCarveOuts(unittest.TestCase):
    """The four shapes that keep a capital without being a defect."""

    def test_acronyms_are_structurally_excluded(self) -> None:
        # No allowlist entry needed: the pattern requires a lowercase
        # remainder, so ALLCAPS and mixedCase never match.
        self.assertEqual(
            chc.find_title_case_words(heading='Handling LLM and PDF IDs'),
            [],
        )

    def test_proper_nouns_are_exempt(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(heading='Verify against Claude and Anthropic'),
            [],
        )

    def test_numbered_procedure_labels_are_exempt(self) -> None:
        # "Step 4" is capitalized in prose throughout the repo; a
        # heading reading "(step 4)" would be the drift, not the fix.
        self.assertEqual(
            chc.find_title_case_words(heading='Apply the fixes (Step 4)'),
            [],
        )

    def test_code_token_is_not_recased(self) -> None:
        self.assertEqual(
            chc.find_title_case_words(
                heading='What `check_structure.py` catches'
            ),
            [],
        )

    def test_identifier_after_label_is_exempt(self) -> None:
        for heading in (
            'Packet: schema-language',
            'Packet: naming',
            'Packet: ai-writing-tells',
            'Mode: full',
        ):
            self.assertEqual(
                chc.find_title_case_words(heading=heading),
                [],
                msg=f'{heading!r} should be treated as an identifier',
            )

    def test_prose_after_a_colon_is_still_checked(self) -> None:
        # Several unhyphenated words after the colon are prose, not a
        # slug, so the identifier carve-out must not swallow them.
        # No stopword exemptions under sentence case: "Is" is flagged
        # like any other non-first capital. That is the asymmetry with
        # the old title-case rule, which spared short words.
        self.assertEqual(
            chc.find_title_case_words(heading='Note: This Is Prose'),
            ['This', 'Is', 'Prose'],
        )
        self.assertEqual(
            chc.find_title_case_words(heading='Note: this is prose'),
            [],
        )


class TestFileWalk(unittest.TestCase):
    def walk(self, text: str) -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'SKILL.md'
            path.write_text(text, encoding='utf-8')
            return chc.find_h2_case_issues(file_path=path)

    def test_flags_title_case_h2_in_a_file(self) -> None:
        out = self.walk('# fixture\n\n## When To Invoke\n')
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['check_id'], 'h2_heading_case')
        self.assertEqual(out[0]['severity'], 'suggestion')
        self.assertIn('sentence case', out[0]['message'])

    def test_silent_on_sentence_case_file(self) -> None:
        self.assertEqual(self.walk('# fixture\n\n## When to invoke\n'), [])

    def test_fenced_headings_are_ignored(self) -> None:
        # A markdown example inside a fence is content, not a header.
        text = '# fixture\n\n```markdown\n## When To Invoke\n```\n'
        self.assertEqual(self.walk(text), [])


if __name__ == '__main__':
    unittest.main()
