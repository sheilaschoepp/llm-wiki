"""Regression tests for check_consistency.py.

Pins the bug classes two review panels rediscovered (crash on missing wiki
subfolder, fence false positives, nondeterministic output, parser
misattribution) plus the script's own wiring invariants. Run from anywhere:

    python3 -m unittest discover -s .claude/skills/consistency/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPT = (
    HERE.parents[1] / 'check_consistency.py'
)  # scripts/check_consistency.py
REPO = HERE.parents[5]  # repo root

spec = importlib.util.spec_from_file_location('check_consistency', SCRIPT)
cc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cc)


def _synthetic_bibkey(author: str, year: str, title: str) -> str:
    # Compose at call time so this source file holds no literal bibkey token —
    # domain_literature_leakage scans test scripts too, and a literal corpus key
    # here would (correctly) flag this very file.
    return f'{author}{year}{title}'


def _addr(local: str, domain: str) -> str:
    # Compose at call time so no literal email sits in this source —
    # personal_info_leakage scans test scripts too and would (correctly) flag
    # a real-looking address here, exactly as _synthetic_bibkey guards a bibkey.
    return f'{local}@{domain}'


class TestCheckConsistency(unittest.TestCase):
    """Regression + wiring tests for check_consistency.py (one cohesive suite per script)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # --- wiring invariants ---

    def test_manifest_parity_is_sound(self) -> None:
        assert cc._assert_manifest_consistency() == []

    def test_parse_check_ids_dedupes_preserving_order(self) -> None:
        assert cc.parse_check_ids('a, a, b ,a') == ['a', 'b']

    # --- clean-state anchors (the committed repo passes) ---

    def test_real_repo_is_clean(self) -> None:
        findings: list = []
        for fn in cc.CHECK_FUNCTIONS.values():
            findings.extend(fn(REPO))
        assert findings == [], findings

    def test_battery_output_is_deterministic_and_clean(self) -> None:
        r1 = subprocess.run(
            [sys.executable, str(SCRIPT), str(REPO)],
            capture_output=True,
            text=True,
        )
        r2 = subprocess.run(
            [sys.executable, str(SCRIPT), str(REPO)],
            capture_output=True,
            text=True,
        )
        assert r1.returncode == 0
        assert r1.stdout == r2.stdout  # stable order, not just stable set

    def test_catalogue_matches_manifest_clean(self) -> None:
        assert cc.check_catalogue_matches_manifest(REPO) == []

    # --- regression: crash on a missing wiki subfolder ---

    def test_index_drift_does_not_crash_on_missing_subfolder(self) -> None:
        wiki = self.tmp / '1-wiki'
        wiki.mkdir()
        (wiki / 'index.md').write_text(
            '## Sources\n## Entities\n## Concepts\n## Syntheses\n'
        )
        (wiki / 'sources').mkdir()  # entities/concepts/syntheses absent
        # Must return a list, not raise FileNotFoundError.
        assert isinstance(cc.check_index_vs_files_drift(self.tmp), list)

    # --- regression: backtick scan inside a non-shell fence ---

    def test_referenced_paths_skips_non_bash_fence(self) -> None:
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: dummy\n---\n')
        (self.tmp / 'README.md').write_text(
            '```python\nx = ".claude/nope/fake.py"\n```\n\n'
            '`0-raw/real-fake.md` outside a fence.\n'
        )
        msgs = [
            f['message'] for f in cc.check_referenced_paths_exist(self.tmp)
        ]
        assert any(
            '0-raw/real-fake.md' in m for m in msgs
        )  # out-of-fence flagged
        assert not any('fake.py' in m for m in msgs)  # in-fence suppressed

    # --- regression: section-list parser misattribution ---

    def test_section_parser_does_not_misattribute_stray_list(self) -> None:
        txt = (
            '### Required Callout Sections\n\n'
            'Source pages:\n\n1. `tldr` - TL;DR\n\n'
            'Glossary pages:\n\n1. `term` - Term\n2. `definition` - Definition\n\n'
            '## Next\n'
        )
        parsed, unrecognized = cc._parse_claude_section_lists(txt)
        assert parsed.get('source') == ['tldr']
        assert 'glossary pages' in unrecognized
        flat = [slug for slugs in parsed.values() for slug in slugs]
        assert 'term' not in flat and 'definition' not in flat

    def test_section_parser_surfaces_malformed_slug(self) -> None:
        txt = (
            '### Required Callout Sections\n\nSource pages:\n\n'
            '1. `tldrX` - TL;DR\n\n## Next\n'
        )
        parsed, _ = cc._parse_claude_section_lists(txt)
        assert parsed['source'] == ['tldrX']  # raw token captured, not dropped

    def test_section_check_detects_drift(self) -> None:
        src = (REPO / 'CLAUDE.md').read_text()
        (self.tmp / 'CLAUDE.md').write_text(
            src.replace('1. `tldr` - TL;DR', '1. `summary` - TL;DR', 1)
        )
        out = cc.check_section_lists_match_schema(self.tmp)
        assert any('source' in f['message'] for f in out)

    # --- domain_literature_leakage: corpus citations in generic infra ---

    def test_domain_literature_leakage_exempts_agent_data_files(self) -> None:
        # The agent-writable curated DATA files (CLAUDE.md -> Stay In Your Lane)
        # are data, not skill logic, and their content is BY CONSTRUCTION the
        # vault's own -- e.g. pagination-map.md sections are keyed on the vault's
        # raw stems, every one a corpus bibkey. Requiring placeholder bibkeys
        # there is incoherent; same rationale as the `-memory.md` journals.
        leaked = _synthetic_bibkey(
            author='Corpus', year='2097', title='GammaEF'
        )
        lint = self.tmp / '.claude' / 'skills' / 'lint'
        lint.mkdir(parents=True)
        (lint / 'SKILL.md').write_text('A lint skill.\n')
        for name in cc.AGENT_DATA_FILES:
            (lint / name).write_text(
                f'## 0-raw/papers/{leaked}.pdf\n- 1 = 1\n'
            )
        flagged = {
            f['file'] for f in cc.check_domain_literature_leakage(self.tmp)
        }
        for name in cc.AGENT_DATA_FILES:
            assert f'.claude/skills/lint/{name}' not in flagged, name
        # ...but an ordinary file in the SAME folder is still scanned.
        (lint / 'references.md').write_text(f'See `{leaked}`.\n')
        flagged = {
            f['file'] for f in cc.check_domain_literature_leakage(self.tmp)
        }
        assert '.claude/skills/lint/references.md' in flagged

    def test_agent_data_files_constant_matches_disk(self) -> None:
        # The constant is the script's copy of a CLAUDE.md declaration; if a data
        # file is renamed or added without updating it, the exemption silently
        # stops applying (or applies to nothing). Pin it to what ships. The three
        # curated data files now live in multi-skill/ (shared with the sibling
        # skills that read check_wiki.py), not lint/.
        data_dir = REPO / '.claude' / 'skills' / 'multi-skill'
        for name in cc.AGENT_DATA_FILES:
            assert (data_dir / name).exists(), (
                f'{name} declared exempt but not on disk'
            )

    def test_domain_literature_leakage_flags_and_exempts(self) -> None:
        placeholder = next(
            iter(cc.PLACEHOLDER_BIBKEYS)
        )  # allowlisted, fetched at runtime
        leaked_a = _synthetic_bibkey(
            author='Corpus', year='2099', title='AlphaAB'
        )
        leaked_b = _synthetic_bibkey(
            author='Corpus', year='2098', title='BetaCD'
        )
        exempt_mem = _synthetic_bibkey(
            author='Corpus', year='2096', title='DeltaGH'
        )
        # CLAUDE.md: a placeholder (ok) plus a leaked corpus citation (flag).
        (self.tmp / 'CLAUDE.md').write_text(
            f'Example source `{placeholder}` is fine.\n'
            f'But `{leaked_a}` is corpus literature.\n'
        )
        skills = self.tmp / '.claude' / 'skills'
        # A skill leaking a corpus citation in its script -> flagged (scripts scanned).
        normal = skills / 'dummy'
        (normal / 'scripts').mkdir(parents=True)
        (normal / 'SKILL.md').write_text('A dummy skill.\n')
        (normal / 'scripts' / 'run.py').write_text(f'KEY = "{leaked_b}"\n')
        # A memory journal citing a real past paper -> the one structural exemption.
        (skills / 'multi-skill-memory.md').write_text(
            f'During the `{exempt_mem}` ingest we learned X.\n'
        )

        flagged = {
            (f['file'], f['message'])
            for f in cc.check_domain_literature_leakage(self.tmp)
        }
        files = {f for f, _ in flagged}
        assert 'CLAUDE.md' in files  # leaked key flagged
        assert (
            '.claude/skills/dummy/scripts/run.py' in files
        )  # script scanned + flagged
        # The memory journal and the placeholder produce no findings.
        assert not any('memory.md' in f for f in files)
        assert not any(placeholder in m for _, m in flagged)

    # --- regression: orphan-script scan skips cache dirs ---

    def test_orphan_skill_scripts_skips_cache_dirs(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        skill = skills / 'dummy'
        (skill / 'scripts').mkdir(parents=True)
        # A backticked, referenced script -> not orphan.
        (skill / 'SKILL.md').write_text(
            'Run `scripts/run.py` to do the thing.\n'
        )
        (skill / 'scripts' / 'run.py').write_text('print("hi")\n')
        # Transient pytest cache under scripts/ -> must be skipped, not flagged.
        cache = skill / 'scripts' / '.pytest_cache' / 'v' / 'cache'
        cache.mkdir(parents=True)
        (skill / 'scripts' / '.pytest_cache' / 'CACHEDIR.TAG').write_text(
            'x\n'
        )
        (cache / 'lastfailed').write_text('{}\n')
        # A genuinely unreferenced script -> still flagged.
        (skill / 'scripts' / 'orphan.py').write_text('print("orphan")\n')

        files = {f['file'] for f in cc.check_orphan_skill_scripts(self.tmp)}
        assert (
            '.claude/skills/dummy/scripts/orphan.py' in files
        )  # real orphan flagged
        assert not any('.pytest_cache' in f for f in files)  # cache skipped
        assert (
            '.claude/skills/dummy/scripts/run.py' not in files
        )  # referenced, not orphan

    # --- regression: output-kind coverage ---

    def test_output_kinds_flags_unlisted_dir(self) -> None:
        (self.tmp / '2-outputs' / 'weirdkind').mkdir(parents=True)
        out = cc.check_output_kinds_match_disk(self.tmp)
        assert any('weirdkind' in f['message'] for f in out)

    def test_output_kinds_stale_direction_gated_on_skill(self) -> None:
        # A listed kind with no folder AND no owning skill must not flag (fresh vault).
        (self.tmp / '2-outputs' / 'query').mkdir(parents=True)
        out = cc.check_output_kinds_match_disk(self.tmp)
        assert not any('does not exist on disk' in f['message'] for f in out)

    def test_catalogue_detects_count_drift(self) -> None:
        import re

        src = (
            REPO / '.claude/skills/consistency/references/checks.md'
        ).read_text()
        broken = re.sub(r'\d+ checks across', '99 checks across', src, count=1)
        assert broken != src  # the substitution actually landed
        dest = self.tmp / '.claude/skills/consistency/references'
        dest.mkdir(parents=True)
        (dest / 'checks.md').write_text(broken)
        out = cc.check_catalogue_matches_manifest(self.tmp)
        assert any('99' in f['message'] for f in out)

    # --- exit codes ---

    def test_bad_path_exits_2(self) -> None:
        r = subprocess.run(
            [sys.executable, str(SCRIPT), '/no/such/path'],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 2
        # The empty-stdout-on-invocation-error is the trap audit's `result:`
        # gate depends on: a genuinely clean run prints '[]' (exit 0), so an
        # empty stdout must never be read as clean. Pin both halves.
        assert r.stdout.strip() == ''
        assert r.stderr.strip() != ''

    def test_bad_packet_and_bad_checks_exit_2(self) -> None:
        for args in (
            ['.', '--packet', 'no-such-packet'],
            ['.', '--checks', 'no_such_check'],
        ):
            r = subprocess.run(
                [sys.executable, str(SCRIPT), *args],
                capture_output=True,
                text=True,
                cwd=str(REPO),
            )
            assert r.returncode == 2, args
            assert r.stdout.strip() == '', args

    def test_empty_checks_selection_exits_2(self) -> None:
        # A comma- or whitespace-only --checks resolves to zero checks. Without
        # the guard the battery runs nothing and exits 0 — a vacuous "clean" the
        # audit gate would trust. It must fail loud (exit 2, empty stdout) like
        # the other invocation errors.
        for value in (',', '   '):
            r = subprocess.run(
                [sys.executable, str(SCRIPT), '.', '--checks', value],
                capture_output=True,
                text=True,
                cwd=str(REPO),
            )
            assert r.returncode == 2, value
            assert r.stdout.strip() == '', value

    def test_crash_exits_2_with_populated_internal_finding(self) -> None:
        # The crash-blocked path: a mid-battery crash exits 2 but prints a
        # POPULATED array carrying a file='(internal)' finding — distinct from an
        # invocation error's empty stdout. The gate relies on that distinction, so
        # pin it (previously untested).
        def boom(root: Path) -> list:
            raise RuntimeError('kaboom')

        original = cc.CHECK_FUNCTIONS.copy()
        cc.CHECK_FUNCTIONS['gitkeep_coverage'] = boom
        old_argv = sys.argv
        buf = io.StringIO()
        try:
            sys.argv = [
                'check_consistency.py',
                str(REPO),
                '--checks',
                'gitkeep_coverage',
            ]
            with redirect_stdout(buf):
                rc = cc.main()
        finally:
            sys.argv = old_argv
            cc.CHECK_FUNCTIONS.clear()
            cc.CHECK_FUNCTIONS.update(original)

        assert rc == 2
        findings = json.loads(buf.getvalue())
        assert findings, 'crash must print a populated array, not empty stdout'
        assert any(f['file'] == '(internal)' for f in findings)

    # --- identity-source fail-loud ---

    def test_identity_source_unloadable_fails_loud(self) -> None:
        # A missing/unparseable identity source must surface an advisory, not
        # pass vacuously — the highest-stakes personal-info scan going silent
        # is the failure mode. (On a real vault about-me loads, so this fires
        # only when the source is genuinely absent.)
        with tempfile.TemporaryDirectory() as d:
            out = cc.check_identity_term_leakage(Path(d))
        assert len(out) == 1
        assert out[0]['check_id'] == 'identity_term_leakage'
        assert 'INACTIVE' in out[0]['message']

    # --- personal-info email regex: alphabetic-TLD guard ---

    def test_email_re_matches_real_addresses(self) -> None:
        # Real addresses — subdomains, +tags, uppercase — still match after
        # the alphabetic-TLD guard was added. Composed via _addr so no literal
        # address sits in this source (personal_info_leakage scans it).
        for addr in (
            _addr('sschoepp', 'ualberta.ca'),
            _addr('user', 'example.com'),
            _addr('first.last+tag', 'mail.example.co.uk'),
            _addr('noreply', 'github.com'),
            _addr('USER', 'EXAMPLE.COM'),
        ):
            assert cc.EMAIL_RE.search(addr), f'should match: {addr}'

    def test_email_re_rejects_numeric_tld_metric_notation(self) -> None:
        # The guard's purpose: metric notation like acc@5.2 or mAP@0.5 has a
        # numeric final label, so it must not be misread as an email.
        for token in (
            'acc@5',
            'acc@5.2',
            'mAP@0.5',
            'recall@0.95',
            'hits@10.5',
            'foo@bar.123',
            'x@y.3',
        ):
            assert not cc.EMAIL_RE.search(token), f'should not match: {token}'

    def test_personal_info_leakage_ignores_metric_notation(self) -> None:
        # End to end: metric notation raises no email finding, a real address
        # still does.
        (self.tmp / 'note.md').write_text(
            'Top-5 result mAP@0.5 and recall@0.95 improved.\n',
            encoding='utf-8',
        )
        assert cc.check_personal_info_leakage(self.tmp) == []

        target = _addr('jane.doe', 'example.com')
        (self.tmp / 'leak.md').write_text(
            f'Reach me at {target} please.\n', encoding='utf-8'
        )
        msgs = [f['message'] for f in cc.check_personal_info_leakage(self.tmp)]
        assert any(target in m for m in msgs), msgs


if __name__ == '__main__':
    unittest.main()
