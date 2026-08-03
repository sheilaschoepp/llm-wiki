"""Tests for the graph graph metrics script.

The guards matter more than the maths here. A metric that is slightly off
is a nuisance; a parse that silently sees nothing and reports "clean" is
the failure this script was written to avoid, so the zero-denominator and
link-conservation paths carry the most tests.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph_metrics as gm  # noqa: E402

PAGE = """---
type: concept
status: verified
updated: 2026-01-01
verified_hash: deadbeef
---

# A page

> [!idea] Idea
>
> - Links to [[1-wiki/concepts/other.md|other]].
> ^idea
"""


def write_vault(root: Path, pages: dict[str, str]) -> None:
    (root / '1-wiki').mkdir(parents=True, exist_ok=True)
    for rel, text in pages.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding='utf-8')


def write_native_coverage(
    root: Path, graph_queries: list[str], base_filter_lines: list[str]
) -> None:
    (root / '.obsidian').mkdir(parents=True, exist_ok=True)
    (root / '.obsidian' / 'graph.json').write_text(
        json.dumps(
            {
                'colorGroups': [
                    {'query': query, 'color': {}} for query in graph_queries
                ]
            }
        ),
        encoding='utf-8',
    )
    (root / '1-wiki' / 'graph.base').write_text(
        'filters:\n' + '\n'.join(base_filter_lines) + '\nviews:\n',
        encoding='utf-8',
    )


class TestPageIndex:
    def test_supported_unique_forms_resolve_to_one_page(self) -> None:
        index = gm.PageIndex({'1-wiki/concepts/foo.md'})
        for target in (
            '1-wiki/concepts/foo.md|Foo',
            '/1-wiki/concepts/FOO#^idea',
            'concepts/foo',
            'foo',
            'FOO.md',
        ):
            assert index.resolve(target) == (
                'page',
                '1-wiki/concepts/foo.md',
            ), target

    def test_duplicate_bare_stem_is_ambiguous(self) -> None:
        index = gm.PageIndex(
            {'1-wiki/concepts/foo.md', '1-wiki/entities/foo.md'}
        )
        assert index.resolve('FOO') == (
            'ambiguous',
            ('1-wiki/concepts/foo.md', '1-wiki/entities/foo.md'),
        )
        assert index.resolve('concepts/FOO') == (
            'page',
            '1-wiki/concepts/foo.md',
        )

    def test_non_page_buckets_remain_distinct(self) -> None:
        index = gm.PageIndex(set())
        assert index.resolve('0-raw/papers/X.pdf')[0] == 'raw'
        assert index.resolve('1-wiki/attachments/X/f.png')[0] == 'attachment'
        assert index.resolve('1-wiki/index.md')[0] == 'wiki_meta'
        assert index.resolve('2-outputs/query/q.md')[0] == 'outside'
        assert index.resolve('missing-page')[0] == 'unresolved'


class TestSlugify:
    def test_kebabs_and_lowercases(self) -> None:
        assert (
            gm.slugify('Jhangiani2019ResearchMI') == 'jhangiani2019researchmi'
        )
        assert gm.slugify('fine-tuning') == 'fine-tuning'
        assert gm.slugify('!!!') == 'unnamed'


class TestZeroDenominators:
    def test_empty_vault_is_did_not_run_not_clean(self, tmp_path) -> None:
        write_vault(tmp_path, {})
        findings, stats, code = gm.run(tmp_path, write=False)
        assert code == 2, 'an empty vault must never report clean'
        assert stats['pages'] == 0
        assert any(f.check_id == 'no_pages' for f in findings)

    def test_missing_wiki_dir_is_did_not_run(self, tmp_path) -> None:
        findings, _, code = gm.run(tmp_path, write=False)
        assert code == 2
        assert any(f.check_id == 'vault_unreadable' for f in findings)

    def test_pages_but_no_links_is_did_not_run(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {'1-wiki/concepts/a.md': '---\ntype: concept\n---\n\n# A\n'},
        )
        findings, _, code = gm.run(tmp_path, write=False)
        assert code == 2, 'zero links is a parse failure, not a clean vault'
        assert any(f.check_id == 'no_links' for f in findings)


class TestDriftDetection:
    def test_new_direct_page_dir_is_included_in_metrics(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/methods/m.md': (
                    '---\ntype: concept\n---\n\n# M\n\n'
                    '[[1-wiki/concepts/a.md|a]]\n'
                ),
            },
        )
        _, stats, _ = gm.run(tmp_path, write=False)
        assert stats['pages'] == 2
        assert stats['page_dirs'] == ['concepts', 'methods']
        assert stats['links_page'] == 1

    def test_empty_archive_is_silent(self, tmp_path) -> None:
        write_vault(tmp_path, {'1-wiki/concepts/a.md': PAGE})
        (tmp_path / '1-wiki' / 'archive').mkdir()
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert 'archive' not in stats['page_dirs']
        assert not any('archive' in f.file for f in findings)

    def test_nested_only_page_layout_is_visible(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/methods/nested/m.md': (
                    '---\ntype: concept\n---\n\n# M\n'
                ),
            },
        )
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert 'methods' not in stats['page_dirs']
        assert any(
            f.check_id == 'nested_page_dir_unsupported' for f in findings
        )

    def test_exact_and_ancestor_native_coverage(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/methods/m.md': (
                    '---\ntype: concept\n---\n\n# M\n\n'
                    '[[1-wiki/concepts/a.md|a]]\n'
                ),
            },
        )
        write_native_coverage(
            tmp_path,
            ['path:1-wiki'],
            ['  or:', '    - file.inFolder("1-wiki")'],
        )
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert stats['graph_dirs_covered'] == [
            '1-wiki/concepts',
            '1-wiki/methods',
        ]
        assert stats['bases_dirs_covered'] == [
            '1-wiki/concepts',
            '1-wiki/methods',
        ]
        assert not any('uncovered' in f.check_id for f in findings)

    def test_conjunction_is_ambiguous_not_false_coverage(
        self, tmp_path
    ) -> None:
        write_vault(tmp_path, {'1-wiki/concepts/a.md': PAGE})
        write_native_coverage(
            tmp_path,
            ['path:1-wiki/concepts'],
            [
                '  and:',
                '    - file.inFolder("1-wiki")',
                '    - file.inFolder("1-wiki/concepts")',
            ],
        )
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert any(
            f.check_id == 'bases_coverage_ambiguous' for f in findings
        )
        assert stats['bases_dirs_covered'] == []
        assert not any(f.check_id == 'bases_dir_uncovered' for f in findings)

    def test_empty_configured_dir_is_silent_but_absent_is_stale(
        self, tmp_path
    ) -> None:
        write_vault(tmp_path, {'1-wiki/concepts/a.md': PAGE})
        (tmp_path / '1-wiki' / 'archive').mkdir()
        write_native_coverage(
            tmp_path,
            ['path:1-wiki/concepts', 'path:1-wiki/archive'],
            [
                '  or:',
                '    - file.inFolder("1-wiki/concepts")',
                '    - file.inFolder("1-wiki/archive")',
            ],
        )
        findings, _, _ = gm.run(tmp_path, write=False)
        assert not any('stale' in f.check_id for f in findings)
        (tmp_path / '1-wiki' / 'archive').rmdir()
        findings, _, _ = gm.run(tmp_path, write=False)
        assert {f.check_id for f in findings} >= {
            'graph_colour_dir_stale',
            'bases_dir_stale',
        }

    def test_unresolved_link_is_named_not_dropped(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/concepts/other.md': (
                    '---\ntype: concept\n---\n\n# Other\n\n[[bare]]\n'
                ),
            },
        )
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert stats['links_page_unresolved'] == 1
        assert any(f.check_id == 'page_link_unresolved' for f in findings)

    def test_link_conservation_holds(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/concepts/other.md': (
                    '---\ntype: concept\n---\n\n# Other\n\n'
                    '[[1-wiki/concepts/a.md|a]] '
                    '[[0-raw/papers/X.pdf#page=1|p. 1]] '
                    '![[1-wiki/attachments/X/f.png]] [[bare]]\n'
                ),
            },
        )
        _, stats, _ = gm.run(tmp_path, write=False)
        buckets = (
            stats['links_page']
            + stats['links_raw']
            + stats['links_attachment']
            + stats['links_wiki_meta']
            + stats['links_page_ambiguous']
            + stats['links_page_unresolved']
            + stats['links_outside']
        )
        assert buckets == stats['links_total']

    def test_unreadable_frontmatter_is_reported(self, tmp_path) -> None:
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': PAGE,
                '1-wiki/concepts/other.md': (
                    '﻿---\ntype: concept\n---\n\n'
                    '# Other\n\n[[1-wiki/concepts/a.md|a]]\n'
                ),
            },
        )
        findings, stats, _ = gm.run(tmp_path, write=False)
        assert stats['frontmatter_parsed'] == 1
        assert any(f.check_id == 'frontmatter_unreadable' for f in findings)


class TestUpsertFrontmatter:
    def test_appends_new_keys_and_leaves_body_byte_identical(self) -> None:
        out = gm.upsert_frontmatter(
            PAGE, {'cluster': 'x', 'betweenness': '0.1000'}
        )
        assert 'cluster: x' in out
        assert 'betweenness: 0.1000' in out
        assert out.split('---', 2)[2] == PAGE.split('---', 2)[2]

    def test_overwrites_an_existing_key_in_place(self) -> None:
        once = gm.upsert_frontmatter(PAGE, {'cluster': 'a'})
        twice = gm.upsert_frontmatter(once, {'cluster': 'b'})
        assert twice.count('cluster:') == 1
        assert 'cluster: b' in twice

    def test_does_not_touch_updated_or_verified_hash(self) -> None:
        out = gm.upsert_frontmatter(PAGE, {'cluster': 'x'})
        assert 'updated: 2026-01-01' in out
        assert 'verified_hash: deadbeef' in out

    def test_raises_on_a_page_with_no_frontmatter(self) -> None:
        try:
            gm.upsert_frontmatter('# No frontmatter\n', {'cluster': 'x'})
        except ValueError:
            return
        raise AssertionError('expected ValueError')


class TestGraphMaths:
    def test_betweenness_on_a_path_of_five(self) -> None:
        adj = [{1}, {0, 2}, {1, 3}, {2, 4}, {3}]
        got = [round(v, 4) for v in gm.betweenness(5, adj)]
        assert got == [0.0, 0.5, 0.6667, 0.5, 0.0]

    def test_betweenness_on_a_star_hub_is_one(self) -> None:
        adj = [{1, 2, 3}, {0}, {0}, {0}]
        assert round(gm.betweenness(4, adj)[0], 4) == 1.0

    def test_louvain_separates_two_disjoint_triangles(self) -> None:
        links = [
            (0, 1, 1.0),
            (1, 2, 1.0),
            (0, 2, 1.0),
            (3, 4, 1.0),
            (4, 5, 1.0),
            (3, 5, 1.0),
        ]
        got = gm.louvain(6, links)
        assert got[0] == got[1] == got[2]
        assert got[3] == got[4] == got[5]
        assert got[0] != got[3]

    def test_louvain_is_deterministic(self) -> None:
        links = [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0)]
        assert gm.louvain(4, links) == gm.louvain(4, links)

    def test_louvain_survives_an_empty_graph(self) -> None:
        assert gm.louvain(0, []) == []


class TestColourGroups:
    def test_palette_entries_are_distinct(self) -> None:
        assert len(set(gm.PALETTE)) == len(gm.PALETTE)

    def test_groups_key_on_the_cluster_property(self) -> None:
        groups = gm.cluster_colour_groups(['alpha', 'beta'])
        assert groups[0]['query'] == '["cluster":"alpha"]'
        assert groups[1]['query'] == '["cluster":"beta"]'
        assert groups[0]['color']['rgb'] != groups[1]['color']['rgb']

    def test_palette_cycles_rather_than_running_out(self) -> None:
        groups = gm.cluster_colour_groups([f'c{i}' for i in range(10)])
        assert len(groups) == 10
        assert groups[8]['color']['rgb'] == groups[0]['color']['rgb']

    def test_write_preserves_every_other_key(self, tmp_path) -> None:
        cfg = {
            'colorGroups': [{'query': 'path:1-wiki/sources', 'color': {}}],
            'centerStrength': 0.12,
            'repelStrength': 18,
            'scale': 0.88,
            'hideUnresolved': True,
        }
        (tmp_path / '.obsidian').mkdir()
        target = tmp_path / '.obsidian' / 'graph.json'
        target.write_text(json.dumps(cfg), encoding='utf-8')

        ok, _ = gm.write_colour_groups(tmp_path, ['alpha', 'beta'])
        assert ok
        after = json.loads(target.read_text(encoding='utf-8'))
        assert len(after['colorGroups']) == 2
        for key in (
            'centerStrength',
            'repelStrength',
            'scale',
            'hideUnresolved',
        ):
            assert after[key] == cfg[key], key

    def test_missing_graph_json_is_reported_not_raised(self, tmp_path) -> None:
        ok, message = gm.write_colour_groups(tmp_path, ['alpha'])
        assert ok is False
        assert 'does not exist' in message

    def test_malformed_graph_json_is_reported_not_raised(
        self, tmp_path
    ) -> None:
        (tmp_path / '.obsidian').mkdir()
        (tmp_path / '.obsidian' / 'graph.json').write_text(
            '{not json', encoding='utf-8'
        )
        ok, message = gm.write_colour_groups(tmp_path, ['alpha'])
        assert ok is False
        assert 'not valid JSON' in message


class TestInDegreeIsNotDegree:
    def test_unreciprocated_link_gives_different_in_and_degree(
        self, tmp_path
    ) -> None:
        # a -> b only. b has in-degree 1, a has in-degree 0, both degree 1.
        write_vault(
            tmp_path,
            {
                '1-wiki/concepts/a.md': (
                    '---\ntype: concept\n---\n\n# A\n\n'
                    '[[1-wiki/concepts/b.md|b]]\n'
                ),
                '1-wiki/concepts/b.md': '---\ntype: concept\n---\n\n# B\n',
            },
        )
        _, stats, _ = gm.run(tmp_path, write=False)
        by_page = {h['page']: h for h in stats['top_hubs']}
        assert by_page['b']['inbound'] == 1
        assert by_page['a']['inbound'] == 0
        assert by_page['a']['degree'] == 1, 'degree counts the edge both ways'
