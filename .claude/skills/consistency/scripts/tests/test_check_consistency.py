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
SCRIPT = HERE.parents[1] / 'check_consistency.py'        # scripts/check_consistency.py
REPO = HERE.parents[5]                                   # repo root

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


def _write_pagination_map(root: Path, body: str) -> None:
    # Every pagination-map fixture plants the file at the one path the check
    # reads, so the fixtures state only what varies: the file's content.
    path = root / cc.PAGINATION_MAP_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding='utf-8')


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

    # --- deterministic CLI behaviour (repository cleanliness is a separate,
    # explicit live-vault acceptance suite) ---

    def test_battery_output_is_deterministic(self) -> None:
        (self.tmp / '.claude/skills/consistency').mkdir(parents=True)
        (self.tmp / 'CLAUDE.md').write_text(
            '# Project schema\n', encoding='utf-8'
        )
        (self.tmp / '.claude/skills/consistency/SKILL.md').write_text(
            '---\nname: consistency\ndescription: fixture\n---\n',
            encoding='utf-8',
        )
        r1 = subprocess.run([sys.executable, str(SCRIPT), str(self.tmp)],
                            capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, str(SCRIPT), str(self.tmp)],
                            capture_output=True, text=True)
        # A sparse synthetic repository has findings, but it is still a valid
        # completed battery. Exit 2 (invocation error or crash) fails this test.
        assert r1.returncode in (0, 1), r1.stderr
        assert isinstance(json.loads(r1.stdout), list)
        assert r1.stdout == r2.stdout          # stable order, not just stable set

    def test_catalogue_matches_manifest_clean(self) -> None:
        assert cc.check_catalogue_matches_manifest(REPO) == []

    # --- regression: directory-tree detection follows the checkout name ---

    def test_dir_tree_drift_uses_actual_repo_folder_name(self) -> None:
        root = self.tmp / 'renamed-wiki'
        root.mkdir()
        (root / 'docs').mkdir()
        (root / 'CLAUDE.md').write_text(
            '## Directory Structure\n\n'
            '```text\n'
            'renamed-wiki/\n'
            '└── CLAUDE.md\n'
            '```\n',
            encoding='utf-8',
        )

        out = cc.check_dir_tree_drift(root)

        # The renamed tree must be parsed and compared with disk: docs exists
        # but is absent from the fixture tree. A hardcoded `llm-wiki/` search
        # returns only "tree block not found" and never reaches this finding.
        assert len(out) == 1, out
        assert '`docs` exists on disk but is missing' in out[0]['message']

    # --- regression: crash on a missing wiki subfolder ---

    def test_index_drift_does_not_crash_on_missing_subfolder(self) -> None:
        wiki = self.tmp / '1-wiki'
        wiki.mkdir()
        (wiki / 'index.md').write_text(
            '## Sources\n## Entities\n## Concepts\n## Syntheses\n')
        (wiki / 'sources').mkdir()           # entities/concepts/syntheses absent
        # Must return a list, not raise FileNotFoundError.
        assert isinstance(cc.check_index_vs_files_drift(self.tmp), list)

    # --- regression: backtick scan inside a non-shell fence ---

    def test_referenced_paths_skips_non_bash_fence(self) -> None:
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: dummy\n---\n')
        (self.tmp / 'README.md').write_text(
            '```python\nx = ".claude/nope/fake.py"\n```\n\n'
            '`0-raw/real-fake.md` outside a fence.\n')
        msgs = [f['message'] for f in cc.check_referenced_paths_exist(self.tmp)]
        assert any('0-raw/real-fake.md' in m for m in msgs)   # out-of-fence flagged
        assert not any('fake.py' in m for m in msgs)          # in-fence suppressed

    # --- regression: the gap between the two reference checks ---
    # A path-shaped reference with no schema prefix fell between them:
    # filename_references_resolve skipped it (it holds a slash) and
    # referenced_paths_exist skipped it (no known prefix), so dead references
    # rode through. Judged by basename, and only when it resolves nowhere.

    def test_referenced_paths_catches_unprefixed_relative_ref(self) -> None:
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        (skill / 'references').mkdir(parents=True)
        (skill / 'references' / 'real-sibling.md').write_text('x\n')
        (skill / 'SKILL.md').write_text(
            '---\nname: dummy\n---\n'
            'See `references/gone-forever.md` and `references/real-sibling.md`.\n')
        msgs = [f['message'] for f in cc.check_referenced_paths_exist(self.tmp)]
        assert any('gone-forever.md' in m for m in msgs)      # resolves nowhere
        assert not any('real-sibling.md' in m for m in msgs)  # names a real file

    def test_referenced_paths_relative_fallback_ignores_urls(self) -> None:
        # A URL is slash-bearing and can end in a doc-looking suffix.
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: dummy\n---\n')
        (self.tmp / 'README.md').write_text('Built for [Obsidian](https://obsidian.md).\n')
        msgs = [f['message'] for f in cc.check_referenced_paths_exist(self.tmp)]
        assert not any('obsidian.md' in m for m in msgs)

    # --- regression: bare (unbackticked) filename mentions in prose ---

    def test_filename_references_catches_bare_prose_mention(self) -> None:
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(
            '---\nname: dummy\n---\n'
            'Guard against the modes in the project style-guide-gone.md: drift.\n')
        msgs = [f['message'] for f in cc.check_filename_references_resolve(self.tmp)]
        assert any('style-guide-gone.md' in m for m in msgs)

    def test_filename_references_bare_scan_excludes_prose_compounds(self) -> None:
        # "an in-SKILL.md roster" is a hyphenated modifier on a real filename,
        # not a reference to a file named in-SKILL.md. Nor should a token
        # inside a path or a backtick span reach the bare scan.
        skill = self.tmp / '.claude' / 'skills' / 'dummy'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(
            '---\nname: dummy\n---\n'
            'An in-SKILL.md roster drifts; see .claude/skills/dummy/SKILL.md.\n')
        assert cc.check_filename_references_resolve(self.tmp) == []

    # --- regression: section-list parser misattribution ---

    def test_section_parser_does_not_misattribute_stray_list(self) -> None:
        txt = ('### Required Callout Sections\n\n'
               'Source pages:\n\n1. `tldr` - TL;DR\n\n'
               'Glossary pages:\n\n1. `term` - Term\n2. `definition` - Definition\n\n'
               '## Next\n')
        parsed, unrecognized = cc._parse_claude_section_lists(txt)
        assert parsed.get('source') == ['tldr']
        assert 'glossary pages' in unrecognized
        flat = [slug for slugs in parsed.values() for slug in slugs]
        assert 'term' not in flat and 'definition' not in flat

    def test_section_parser_surfaces_malformed_slug(self) -> None:
        txt = ('### Required Callout Sections\n\nSource pages:\n\n'
               '1. `tldrX` - TL;DR\n\n## Next\n')
        parsed, _ = cc._parse_claude_section_lists(txt)
        assert parsed['source'] == ['tldrX']   # raw token captured, not dropped

    def test_section_check_detects_drift(self) -> None:
        src = (REPO / 'CLAUDE.md').read_text()
        (self.tmp / 'CLAUDE.md').write_text(
            src.replace('1. `tldr` - TL;DR', '1. `summary` - TL;DR', 1))
        out = cc.check_section_lists_match_schema(self.tmp)
        assert any('source' in f['message'] for f in out)

    # --- domain_literature_leakage: corpus citations in generic infra ---

    def test_domain_literature_leakage_exempts_agent_data_files(self) -> None:
        # The agent-writable curated DATA files (CLAUDE.md -> Stay In Your Lane)
        # are data, not skill logic, and their content is BY CONSTRUCTION the
        # vault's own -- e.g. pagination-map.md sections are keyed on the vault's
        # raw stems, every one a corpus bibkey. Requiring placeholder bibkeys
        # there is incoherent; same rationale as the `-memory.md` journals.
        leaked = _synthetic_bibkey(author='Corpus', year='2097', title='GammaEF')
        lint = self.tmp / '.claude' / 'skills' / 'lint'
        lint.mkdir(parents=True)
        (lint / 'SKILL.md').write_text('A lint skill.\n')
        for name in cc.AGENT_DATA_FILES:
            (lint / name).write_text(f'## 0-raw/papers/{leaked}.pdf\n- 1 = 1\n')
        flagged = {f['file'] for f in cc.check_domain_literature_leakage(self.tmp)}
        for name in cc.AGENT_DATA_FILES:
            assert f'.claude/skills/lint/{name}' not in flagged, name
        # ...but an ordinary file in the SAME folder is still scanned.
        (lint / 'references.md').write_text(f'See `{leaked}`.\n')
        flagged = {f['file'] for f in cc.check_domain_literature_leakage(self.tmp)}
        assert '.claude/skills/lint/references.md' in flagged

    def test_agent_data_files_constant_matches_disk(self) -> None:
        # The constant is the script's copy of a CLAUDE.md declaration; if a data
        # file is renamed or added without updating it, the exemption silently
        # stops applying (or applies to nothing). Pin it to what ships. The three
        # curated data files now live in multi-skill/ (shared with the sibling
        # skills that read check_wiki.py), not lint/.
        data_dir = REPO / '.claude' / 'skills' / 'multi-skill'
        for name in cc.AGENT_DATA_FILES:
            assert (data_dir / name).exists(), f'{name} declared exempt but not on disk'

    def test_domain_literature_leakage_flags_and_exempts(self) -> None:
        placeholder = next(iter(cc.PLACEHOLDER_BIBKEYS))      # allowlisted, fetched at runtime
        leaked_a = _synthetic_bibkey(author='Corpus', year='2099', title='AlphaAB')
        leaked_b = _synthetic_bibkey(author='Corpus', year='2098', title='BetaCD')
        exempt_mem = _synthetic_bibkey(author='Corpus', year='2096', title='DeltaGH')
        # CLAUDE.md: a placeholder (ok) plus a leaked corpus citation (flag).
        (self.tmp / 'CLAUDE.md').write_text(
            f'Example source `{placeholder}` is fine.\n'
            f'But `{leaked_a}` is corpus literature.\n')
        skills = self.tmp / '.claude' / 'skills'
        # A skill leaking a corpus citation in its script -> flagged (scripts scanned).
        normal = skills / 'dummy'
        (normal / 'scripts').mkdir(parents=True)
        (normal / 'SKILL.md').write_text('A dummy skill.\n')
        (normal / 'scripts' / 'run.py').write_text(f'KEY = "{leaked_b}"\n')
        # A memory journal citing a real past paper -> the one structural exemption.
        (skills / 'multi-skill-memory.md').write_text(
            f'During the `{exempt_mem}` ingest we learned X.\n')

        flagged = {(f['file'], f['message']) for f in
                   cc.check_domain_literature_leakage(self.tmp)}
        files = {f for f, _ in flagged}
        assert 'CLAUDE.md' in files                              # leaked key flagged
        assert '.claude/skills/dummy/scripts/run.py' in files    # script scanned + flagged
        # The memory journal and the placeholder produce no findings.
        assert not any('memory.md' in f for f in files)
        assert not any(placeholder in m for _, m in flagged)

    # --- regression: orphan-script scan skips cache dirs ---

    def test_orphan_skill_scripts_skips_cache_dirs(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        skill = skills / 'dummy'
        (skill / 'scripts').mkdir(parents=True)
        # A backticked, referenced script -> not orphan.
        (skill / 'SKILL.md').write_text('Run `scripts/run.py` to do the thing.\n')
        (skill / 'scripts' / 'run.py').write_text('print("hi")\n')
        # Transient pytest cache under scripts/ -> must be skipped, not flagged.
        cache = skill / 'scripts' / '.pytest_cache' / 'v' / 'cache'
        cache.mkdir(parents=True)
        (skill / 'scripts' / '.pytest_cache' / 'CACHEDIR.TAG').write_text('x\n')
        (cache / 'lastfailed').write_text('{}\n')
        # A genuinely unreferenced script -> still flagged.
        (skill / 'scripts' / 'orphan.py').write_text('print("orphan")\n')

        files = {f['file'] for f in cc.check_orphan_skill_scripts(self.tmp)}
        assert '.claude/skills/dummy/scripts/orphan.py' in files       # real orphan flagged
        assert not any('.pytest_cache' in f for f in files)            # cache skipped
        assert '.claude/skills/dummy/scripts/run.py' not in files      # referenced, not orphan

    def test_orphan_skill_scripts_parses_commands_and_test_companions(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        skill = skills / 'dummy'
        tests = skill / 'scripts' / 'tests'
        tests.mkdir(parents=True)
        (skill / 'SKILL.md').write_text(
            'Run `python3 .claude/skills/dummy/scripts/run.py --strict`.\n')
        (skill / 'scripts' / 'run.py').write_text('print("run")\n')
        (tests / 'test_run.py').write_text('pass\n')
        (skill / 'scripts' / 'orphan.py').write_text('print("orphan")\n')
        (tests / 'test_orphan.py').write_text('pass\n')

        files = {f['file'] for f in cc.check_orphan_skill_scripts(self.tmp)}
        assert '.claude/skills/dummy/scripts/run.py' not in files
        assert '.claude/skills/dummy/scripts/tests/test_run.py' not in files
        assert '.claude/skills/dummy/scripts/orphan.py' in files
        assert '.claude/skills/dummy/scripts/tests/test_orphan.py' in files

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
        src = (REPO / '.claude/skills/consistency/references/checks.md').read_text()
        broken = re.sub(r'\d+ checks across', '99 checks across', src, count=1)
        assert broken != src           # the substitution actually landed
        dest = self.tmp / '.claude/skills/consistency/references'
        dest.mkdir(parents=True)
        (dest / 'checks.md').write_text(broken)
        out = cc.check_catalogue_matches_manifest(self.tmp)
        assert any('99' in f['message'] for f in out)

    # --- direct coverage for the remaining consistency checks ---

    def test_retired_feature_mentions_flags_prose_but_skips_history(self) -> None:
        (self.tmp / 'README.md').write_text('Use the working_copy now.\n')
        archive = self.tmp / '1-wiki' / 'archive'
        archive.mkdir(parents=True)
        (archive / 'log-2026-01.md').write_text('Retired working copy history.\n')

        out = cc.check_retired_feature_mentions(self.tmp)

        assert [f['file'] for f in out] == ['README.md']

    def test_working_skill_count_prose_compares_with_skill_folders(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        (skills / 'query').mkdir(parents=True)
        (skills / 'query' / 'SKILL.md').write_text('A query skill.\n')
        (skills / 'consistency').mkdir()
        (skills / 'consistency' / 'SKILL.md').write_text(
            'The ten operation skills are checked here.\n')
        (self.tmp / 'README.md').write_text('The ten operation skills run.\n')

        out = cc.check_working_skill_count_prose(self.tmp)

        assert len(out) == 1
        assert out[0]['file'] == 'README.md'
        assert 'actual working-skill count (1)' in out[0]['message']

    def test_old_schema_wording_ignores_inline_code_examples(self) -> None:
        (self.tmp / 'README.md').write_text('Migrate every source note now.\n')
        (self.tmp / 'CLAUDE.md').write_text(
            'The token `source note` is an inert example.\n')

        out = cc.check_old_schema_wording(self.tmp)

        assert [f['file'] for f in out] == ['README.md']

    def test_placeholder_consistency_flags_only_mixed_page(self) -> None:
        concepts = self.tmp / '1-wiki' / 'concepts'
        concepts.mkdir(parents=True)
        (concepts / 'mixed.md').write_text(
            '> - None identified.\n> - None documented.\n')
        (concepts / 'uniform.md').write_text(
            '> - None identified.\n> - None identified.\n')

        out = cc.check_placeholder_consistency(self.tmp)

        assert [f['file'] for f in out] == ['1-wiki/concepts/mixed.md']

    def test_body_section_order_accepts_schema_and_flags_reordering(self) -> None:
        concepts = self.tmp / '1-wiki' / 'concepts'
        concepts.mkdir(parents=True)
        expected = cc.EXPECTED_SECTIONS['concept']
        (concepts / 'ordered.md').write_text(
            ''.join(f'> [!{slug}]\n' for slug in expected))
        (concepts / 'reordered.md').write_text(
            ''.join(f'> [!{slug}]\n' for slug in reversed(expected)))

        out = cc.check_body_section_order(self.tmp)

        assert [f['file'] for f in out] == ['1-wiki/concepts/reordered.md']

    def test_source_venue_year_split_flags_venue_year_only(self) -> None:
        sources = self.tmp / '1-wiki' / 'sources'
        sources.mkdir(parents=True)
        (sources / 'bad.md').write_text(
            'title: Bad\nvenue: NeurIPS 2017\nyear: 2017\n')
        (sources / 'good.md').write_text(
            'title: Good\nvenue: NeurIPS\nyear: 2017\n')

        out = cc.check_source_venue_year_split(self.tmp)

        assert [f['file'] for f in out] == ['1-wiki/sources/bad.md']
        assert out[0]['line'] == 2

    def test_attachments_folder_coverage_handles_missing_and_orphaned(self) -> None:
        missing = cc.check_attachments_folder_coverage(self.tmp)
        assert len(missing) == 1
        assert 'is missing' in missing[0]['message']

        attachments = self.tmp / '1-wiki' / 'attachments'
        sources = self.tmp / '1-wiki' / 'sources'
        (attachments / 'kept').mkdir(parents=True)
        (attachments / 'orphan').mkdir()
        sources.mkdir()
        (sources / 'kept.md').write_text('x\n')

        out = cc.check_attachments_folder_coverage(self.tmp)

        assert [f['file'] for f in out] == ['1-wiki/attachments/orphan']

    def test_callout_css_coverage_reports_only_missing_styles(self) -> None:
        missing_file = cc.check_callout_css_coverage(self.tmp)
        assert len(missing_file) == 1
        assert 'stylesheet is missing' in missing_file[0]['message']

        css = self.tmp / '.obsidian' / 'snippets' / 'custom_callouts.css'
        css.parent.mkdir(parents=True)
        omitted = cc.REQUIRED_CALLOUTS[0]
        css.write_text('\n'.join(
            f'.callout[data-callout="{slug}"] {{}}'
            for slug in cc.REQUIRED_CALLOUTS if slug != omitted))

        out = cc.check_callout_css_coverage(self.tmp)

        assert len(out) == 1
        assert f'`{omitted}`' in out[0]['message']

    def test_ai_writing_tells_flags_docs_and_skips_self_documentation(self) -> None:
        (self.tmp / 'README.md').write_text('This pivotal result matters.\n')
        self_doc = self.tmp / '.claude' / 'skills' / 'consistency' / 'SKILL.md'
        self_doc.parent.mkdir(parents=True)
        self_doc.write_text('The pivotal pattern is documented here.\n')

        out = cc.check_ai_writing_tells(self.tmp)

        assert [f['file'] for f in out] == ['README.md']
        assert 'high-density AI vocabulary' in out[0]['message']

    def test_file_naming_consistency_flags_only_nonexempt_names(self) -> None:
        raw = self.tmp / '0-raw' / 'papers'
        source = self.tmp / '1-wiki' / 'sources'
        concepts = self.tmp / '1-wiki' / 'concepts'
        attachments = self.tmp / '1-wiki' / 'attachments' / 'MixedCase'
        outputs = self.tmp / '2-outputs' / 'query'
        skills = self.tmp / '.claude' / 'skills' / 'Bad_Name'
        for folder in (raw, source, concepts, attachments, outputs, skills):
            folder.mkdir(parents=True, exist_ok=True)
        (raw / 'MixedCase.pdf').write_text('raw\n')
        (source / 'MixedCase.md').write_text('source\n')
        (concepts / 'Bad_Name.md').write_text('concept\n')
        (attachments / 'Bad_Image.PNG').write_text('image\n')
        (outputs / 'bad.md').write_text('output\n')

        files = {f['file'] for f in cc.check_file_naming_consistency(self.tmp)}

        assert files == {
            '1-wiki/concepts/Bad_Name.md',
            '1-wiki/attachments/MixedCase/Bad_Image.PNG',
            '2-outputs/query/bad.md',
            '.claude/skills/Bad_Name',
        }
        assert '1-wiki/sources/MixedCase.md' not in files
        assert '1-wiki/attachments/MixedCase' not in files

    def test_memory_file_graduation_prompt_respects_caps_and_index(self) -> None:
        memory = self.tmp / 'MEMORY.md'
        memory.write_text(
            '## Index\n' + ''.join(f'## Entry {i}\n' for i in range(15)))
        assert cc.check_memory_file_graduation_prompt(self.tmp) == []

        memory.write_text(memory.read_text() + '## Entry 15\n')
        out = cc.check_memory_file_graduation_prompt(self.tmp)

        assert len(out) == 1
        assert out[0]['file'] == 'MEMORY.md'
        assert '16 entries' in out[0]['message']

    def test_unbackticked_paths_resolve_owns_only_prose_paths(self) -> None:
        wiki = self.tmp / '1-wiki'
        wiki.mkdir()
        (wiki / 'existing.md').write_text('x\n')
        (self.tmp / 'CLAUDE.md').write_text(
            'Existing 1-wiki/existing.md and missing 1-wiki/missing.md.\n'
            'Backticked `1-wiki/backticked-missing.md` is owned elsewhere.\n'
            '```text\n1-wiki/fenced-missing.md\n```\n')

        out = cc.check_unbackticked_paths_resolve(self.tmp)

        assert len(out) == 1
        assert '`1-wiki/missing.md`' in out[0]['message']

    def test_operations_list_matches_skills_flags_both_directions(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        for name in ('listed', 'missing', 'graph'):
            (skills / name).mkdir(parents=True)
            (skills / name / 'SKILL.md').write_text(f'{name}\n')
        (self.tmp / 'CLAUDE.md').write_text(
            '## Operations\n\n'
            '- `listed` - present\n'
            '- `stale` - absent\n'
            '- `graph` - standalone\n\n'
            '## Next\n')

        out = cc.check_operations_list_matches_skills(self.tmp)
        messages = [f['message'] for f in out]

        assert len(out) == 2
        assert any('lists `stale`' in message for message in messages)
        assert any('skills/missing/' in message for message in messages)
        assert not any('graph' in message for message in messages)

    def test_retired_skill_references_distinguishes_mode_vocabulary(self) -> None:
        (self.tmp / 'README.md').write_text(
            'Route `/reingest` or `ingest-deep`; a plain reingest appends.\n')
        skills = self.tmp / '.claude' / 'skills' / 'live'
        skills.mkdir(parents=True)
        (skills / 'SKILL.md').write_text(
            'Required operation skills `live`, `ghost`.\n')

        out = cc.check_retired_skill_references(self.tmp)
        messages = [f['message'] for f in out]

        assert len(out) == 3, out
        assert sum('`reingest`' in message for message in messages) == 1
        assert sum('`ingest-deep`' in message for message in messages) == 1
        assert any('`ghost`' in message for message in messages)

    def test_shared_reference_integrity_flags_duplicates_and_underuse(self) -> None:
        skills = self.tmp / '.claude' / 'skills'
        shared = skills / 'multi-skill' / 'references'
        shared.mkdir(parents=True)
        (shared / 'shared.md').write_text('shared\n')
        (shared / 'lonely.md').write_text('lonely\n')
        for name, text in (
            ('alpha', 'Use shared.md and lonely.md.\n'),
            ('beta', 'Use shared.md.\n'),
        ):
            (skills / name / 'references').mkdir(parents=True)
            (skills / name / 'SKILL.md').write_text(text)
        (skills / 'alpha' / 'references' / 'shared.md').write_text('copy\n')

        out = cc.check_shared_reference_integrity(self.tmp)
        messages = [f['message'] for f in out]

        assert len(out) == 2, out
        assert any('also copied' in message for message in messages)
        assert any('`lonely.md` is cited by 1 skill(s)' in message
                   for message in messages)

    # --- exit codes ---

    def test_bad_path_exits_2(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '/no/such/path'],
                           capture_output=True, text=True)
        assert r.returncode == 2
        # The empty-stdout-on-invocation-error is the trap audit's `result:`
        # gate depends on: a genuinely clean run prints '[]' (exit 0), so an
        # empty stdout must never be read as clean. Pin both halves.
        assert r.stdout.strip() == ''
        assert r.stderr.strip() != ''

    def test_wrong_existing_roots_exit_2(self) -> None:
        file_root = self.tmp / 'not-a-directory'
        file_root.write_text('not a project root\n')
        directory_root = self.tmp / 'not-a-project'
        directory_root.mkdir()
        for root in (file_root, directory_root):
            r = subprocess.run(
                [sys.executable, str(SCRIPT), str(root)],
                capture_output=True,
                text=True,
            )
            assert r.returncode == 2, root
            assert r.stdout.strip() == '', root
            assert 'not a consistency project root' in r.stderr, root

    def test_bad_packet_and_bad_checks_exit_2(self) -> None:
        for args in (['.', '--packet', 'no-such-packet'],
                     ['.', '--checks', 'no_such_check']):
            r = subprocess.run([sys.executable, str(SCRIPT), *args],
                               capture_output=True, text=True, cwd=str(REPO))
            assert r.returncode == 2, args
            assert r.stdout.strip() == '', args

    def test_empty_checks_selection_exits_2(self) -> None:
        # A comma- or whitespace-only --checks resolves to zero checks. Without
        # the guard the battery runs nothing and exits 0 — a vacuous "clean" the
        # audit gate would trust. It must fail loud (exit 2, empty stdout) like
        # the other invocation errors.
        for value in ('', ',', '   '):
            r = subprocess.run(
                [sys.executable, str(SCRIPT), '.', '--checks', value],
                capture_output=True, text=True, cwd=str(REPO))
            assert r.returncode == 2, value
            assert r.stdout.strip() == '', value
        combined = subprocess.run(
            [sys.executable, str(SCRIPT), '.', '--checks', '',
             '--packet', 'schema-language'],
            capture_output=True,
            text=True,
            cwd=str(REPO),
        )
        assert combined.returncode == 2
        assert combined.stdout.strip() == ''

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
            sys.argv = ['check_consistency.py', str(REPO),
                        '--checks', 'gitkeep_coverage']
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
        # Real-shaped addresses — ccTLDs, subdomains, +tags, uppercase — still
        # match after the alphabetic-TLD guard was added. Composed via _addr so
        # no literal address sits in this source (personal_info_leakage scans
        # it). Sample values only: the regex cares about shape, not identity,
        # so nobody's actual address needs to appear here.
        for addr in (_addr('jdoe', 'example.ca'), _addr('user', 'example.com'),
                     _addr('first.last+tag', 'mail.example.co.uk'),
                     _addr('noreply', 'github.com'), _addr('USER', 'EXAMPLE.COM')):
            assert cc.EMAIL_RE.search(addr), f'should match: {addr}'

    def test_email_re_rejects_numeric_tld_metric_notation(self) -> None:
        # The guard's purpose: metric notation like acc@5.2 or mAP@0.5 has a
        # numeric final label, so it must not be misread as an email.
        for token in ('acc@5', 'acc@5.2', 'mAP@0.5', 'recall@0.95',
                      'hits@10.5', 'foo@bar.123', 'x@y.3'):
            assert not cc.EMAIL_RE.search(token), f'should not match: {token}'

    def test_personal_info_leakage_ignores_metric_notation(self) -> None:
        # End to end: metric notation raises no email finding, a real address
        # still does.
        (self.tmp / 'note.md').write_text(
            'Top-5 result mAP@0.5 and recall@0.95 improved.\n', encoding='utf-8')
        assert cc.check_personal_info_leakage(self.tmp) == []

        target = _addr('jane.doe', 'example.com')
        (self.tmp / 'leak.md').write_text(
            f'Reach me at {target} please.\n', encoding='utf-8')
        msgs = [f['message'] for f in cc.check_personal_info_leakage(self.tmp)]
        assert any(target in m for m in msgs), msgs

    # --- pagination-map structural integrity ---

    def test_pagination_map_flags_section_with_no_entry_lines(self) -> None:
        # The silent case: the `## 0-raw/...` heading survives but its entry
        # lines are gone. check_wiki.py's loader registers the raw from the
        # heading alone, so printed_page answers 'unregistered' for every page
        # while lint's pagination_map_unregistered nudge — a map-membership
        # test — sees a member and stays quiet. The raw drops out of both, and
        # before this check nothing in the battery read it as pagination
        # data.
        _write_pagination_map(
            root=self.tmp,
            body='## Registered raws\n\n'
                 '## 0-raw/papers/example-raw.pdf\n\n'
                 'Prose about the raw survived; the entry lines did not.\n',
        )

        out = cc.check_pagination_map_integrity(self.tmp)

        assert len(out) == 1, out
        assert out[0]['check_id'] == 'pagination_map_integrity'
        # Must route root-level (SKILL.md Step 7.3 classifies by target file);
        # a finding against a wiki page would become auto-fixable.
        assert out[0]['file'] == cc.PAGINATION_MAP_PATH
        assert '0-raw/papers/example-raw.pdf' in out[0]['message']

    def test_pagination_map_silent_on_roman_and_none_printed_values(self) -> None:
        # Roman folios, `none`, and an unresolved review(...) proposal are all
        # legitimate content of the printed side. The check must never read
        # that side, so a populated section is silent whatever it prints —
        # structurally, not by allowlist. A fix hint that named a printed page
        # would license overwriting a correct folio.
        _write_pagination_map(
            root=self.tmp,
            body='## 0-raw/books/example-book.pdf\n\n'
                 'Roman front matter, then a body offset.\n\n'
                 '- 1-10 = none\n'
                 '- 11 = viii\n'
                 '- 12-19 = ix-xvi\n'
                 '- 20 = review(header=3|4,footer=none)\n',
        )

        assert cc.check_pagination_map_integrity(self.tmp) == []

    def test_pagination_map_silent_when_no_raw_is_registered(self) -> None:
        # A fresh vault registers a raw only when it ingests one, so a map with
        # no `## 0-raw/` section is correct, not drift. The template vault ships
        # in exactly this state; flagging it would fire on every new clone.
        # The fenced placeholder heading and the commented example are inert
        # here for the same reason they are inert in check_wiki.py's loader.
        _write_pagination_map(
            root=self.tmp,
            body='# Pagination map\n\n'
                 '```text\n'
                 '## <raw path — e.g. 0-raw/papers/Example.pdf>\n'
                 '- 1 = 1\n'
                 '```\n\n'
                 '## Registered raws\n\n'
                 '<!--\n# ## 0-raw/papers/x.pdf\n# - 1-16 = 4171-4186\n-->\n',
        )

        assert cc.check_pagination_map_integrity(self.tmp) == []

    def test_pagination_map_absence_fails_loud(self) -> None:
        # Absence must never be a silent `return []` — a vanished, undecodable,
        # or contentless map degrades every raw to unregistered, which is the
        # exact condition this check exists to surface. UnicodeDecodeError is a
        # ValueError, not an OSError, so it needs its own except clause for the
        # "unreadable" wording to actually cover it.
        assert len(cc.check_pagination_map_integrity(self.tmp)) == 1

        _write_pagination_map(root=self.tmp, body='\n   \n')
        assert len(cc.check_pagination_map_integrity(self.tmp)) == 1

        (self.tmp / cc.PAGINATION_MAP_PATH).write_bytes(
            b'## 0-raw/papers/example-raw.pdf\n- 1 = \xff\xfe\n')
        out = cc.check_pagination_map_integrity(self.tmp)
        assert len(out) == 1, out
        assert 'UnicodeDecodeError' in out[0]['message']

    def test_pagination_map_flags_duplicate_raw_heading(self) -> None:
        # The loader merges two same-named sections into one page map, so a
        # physical page listed in both silently takes the value read last.
        _write_pagination_map(
            root=self.tmp,
            body='## 0-raw/papers/example-raw.pdf\n- 1 = 1\n\n'
                 '## 0-raw/papers/example-raw.pdf\n- 1 = 9\n',
        )

        out = cc.check_pagination_map_integrity(self.tmp)

        assert len(out) == 1, out
        assert 'under 2 separate headings' in out[0]['message']

    def test_pagination_map_integrity_clean_on_this_repo(self) -> None:
        # Pins the silent-on-an-intact-vault half of the contract, the way
        # test_catalogue_matches_manifest_clean pins the catalogue's.
        assert cc.check_pagination_map_integrity(REPO) == []


if __name__ == '__main__':
    unittest.main()
