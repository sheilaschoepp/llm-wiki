"""
Regression tests for check_internal_refs.py.

Pins the two behaviours that make the check worth running: it catches a
cross-reference to a step the file does not define (the renumbering
damage it exists for), and it stays silent on a file whose references
all resolve. Also pins the reference-file carve-out — a references/*.md
sibling cites its parent SKILL.md's steps and defines none of its own,
so running the check there would flag every legitimate citation.

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
SCRIPT = HERE.parents[1] / 'check_internal_refs.py'

spec = importlib.util.spec_from_file_location('check_internal_refs', SCRIPT)
cir = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cir)

RENUMBERED = """# fixture

## Procedure

1. **First step.** Nothing here.

2. **Second step.** See Step 9 for the follow-up.

   **2.0 — A sub-step.** Carry the pointer forward to 2.7.
"""

RESOLVING = """# fixture

## Procedure

1. **First step.** See Step 2.

2. **Second step.** See Step 1, and Steps 1-2 together.

   **2.1 — A sub-step.** Carry the pointer forward to 2.1.
"""

REFERENCE_FILE = """# A reference file

SKILL.md Step 3 names each entry's home. Step 7 gates the removal, and
Step 8.1 confirms it. This file defines no steps of its own.
"""


class TestStaleStepReference(unittest.TestCase):
    def check(self, text: str, *, name: str = 'SKILL.md') -> list[dict]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(text, encoding='utf-8')
            return cir.check_file(file_path=path, display_name=name)

    def test_flags_reference_to_undefined_step(self) -> None:
        # 'Step 9' has no definition; the file stops at step 2.
        findings = self.check(RENUMBERED)
        targets = {f['message'].split('Step ')[1].split(',')[0] for f in findings}
        self.assertIn('9', targets)
        self.assertTrue(
            all(f['check_id'] == 'stale_step_reference' for f in findings)
        )
        self.assertTrue(all(f['severity'] == 'warning' for f in findings))

    def test_silent_when_every_reference_resolves(self) -> None:
        self.assertEqual(self.check(RESOLVING), [])

    def test_reference_file_citing_parent_steps_is_exempt(self) -> None:
        # A references/*.md sibling defines no procedure of its own, so
        # its citations of the parent's steps must not be flagged.
        self.assertEqual(self.check(REFERENCE_FILE, name='memory-notes.md'), [])

    def test_defined_steps_include_substeps(self) -> None:
        defined = cir.collect_defined_steps(text=RESOLVING)
        self.assertIn('1', defined)
        self.assertIn('2', defined)
        self.assertIn('2.1', defined)

    def test_fenced_references_are_not_scanned(self) -> None:
        # A 'Step 99' inside a fence is example content, not a live
        # cross-reference.
        text = '# f\n\n1. **A.** ok\n\n```text\nSee Step 99.\n```\n'
        self.assertEqual(self.check(text), [])


class TestH2IdentifierCarveOut(unittest.TestCase):
    """
    The sibling h2-case rule shares this file's motivation: a heading
    segment that names a literal argument carries no case to correct.
    """

    def setUp(self) -> None:
        h2_script = HERE.parents[1] / 'check_h2_case.py'
        h2_spec = importlib.util.spec_from_file_location('check_h2_case', h2_script)
        self.h2 = importlib.util.module_from_spec(h2_spec)
        assert h2_spec and h2_spec.loader
        h2_spec.loader.exec_module(self.h2)

    def test_identifier_after_label_is_not_flagged(self) -> None:
        for heading in (
            'Packet: schema-language',
            'Packet: naming',
            'Packet: ai-writing-tells',
            'Mode: full',
        ):
            self.assertTrue(
                self.h2.is_title_case(heading=heading),
                msg=f'{heading!r} should be treated as an identifier',
            )

    def test_prose_after_a_colon_is_still_flagged(self) -> None:
        # Several unhyphenated words after the colon are prose, not a slug.
        self.assertFalse(self.h2.is_title_case(heading='Note: this is prose'))

    def test_hyphenated_prose_without_a_label_is_still_flagged(self) -> None:
        self.assertFalse(
            self.h2.is_title_case(heading='Working with well-formed pages')
        )

    def test_ordinary_headings_unaffected(self) -> None:
        self.assertTrue(self.h2.is_title_case(heading='The Five Categories'))
        self.assertFalse(self.h2.is_title_case(heading='The five categories'))


if __name__ == '__main__':
    unittest.main()
