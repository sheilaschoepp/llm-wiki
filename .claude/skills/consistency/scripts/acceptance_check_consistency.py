"""Live-repository acceptance tests for ``check_consistency.py``.

Run explicitly from any working copy whose current content should satisfy the
repository schema:

    python3 .claude/skills/consistency/scripts/acceptance_check_consistency.py

These checks intentionally read the working repository. They are separate from
the fixture-based regression suite so a populated vault can run unit tests
without treating its live maintenance backlog as a code regression.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = HERE.parent / 'check_consistency.py'
REPO = HERE.parents[4]

spec = importlib.util.spec_from_file_location('check_consistency', SCRIPT)
cc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cc)


class TestLiveRepositoryAcceptance(unittest.TestCase):
    """Require the current working repository to satisfy the schema."""

    EXPECTED_BASELINE_CHECK_IDS = frozenset({'identity_term_leakage'})
    EXPECTED_BASELINE_MARKER = 'INACTIVE'

    @classmethod
    def _beyond_baseline(cls, findings: list[dict]) -> list[dict]:
        """Exclude only the distributable about-me template advisory."""
        return [
            finding
            for finding in findings
            if (
                finding.get('check_id')
                not in cls.EXPECTED_BASELINE_CHECK_IDS
                or cls.EXPECTED_BASELINE_MARKER
                not in finding.get('message', '')
            )
        ]

    def test_real_repo_is_clean(self) -> None:
        findings: list[dict] = []
        for check in cc.CHECK_FUNCTIONS.values():
            findings.extend(check(REPO))
        regressions = self._beyond_baseline(findings)
        self.assertEqual(regressions, [])

    def test_battery_output_is_clean(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(REPO)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        regressions = self._beyond_baseline(json.loads(result.stdout))
        self.assertEqual(regressions, [])


if __name__ == '__main__':
    unittest.main()
