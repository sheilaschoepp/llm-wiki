"""Compute link-graph metrics Obsidian cannot, and write them to frontmatter.

Obsidian's native surfaces cover in-degree (Bases `file.backlinks.length`)
and the force-directed view. They cannot compute community structure or
betweenness: Bases forbids self-referencing formulas, so there is no
iteration to convergence, and no native surface enumerates shortest paths.
This script computes those two and stores them as frontmatter properties,
which the graph view's colour groups and Bases views can then read.

Two properties are written, and nothing else:

    cluster:         the anchor page's slug for this page's community
    betweenness:     normalized Brandes betweenness, 4 decimal places

plus a `graph_computed:` date stamp so a stale value is visible as stale.

`cluster:` stores the community ANCHOR SLUG, never the community index.
Louvain communities here are renumbered by size rank on every run, so a
stored integer can name a different community after one ingest even when
membership is unchanged. An anchor slug is stable under renumbering and is
human-readable, so a wrong value reads as wrong instead of reading as fine.

Staleness is real and is not papered over. Both values are global: they
change on page A because page B was edited. Measured on this schema, one
ingest rewrites the cluster of a majority of pages on a vault under ~160
pages. Recompute after any ingest, and read `graph_computed:` before
trusting either field.

`updated:` is deliberately NOT touched. It records content recency, and a
whole-vault recompute would reset it everywhere and destroy that signal.
Frontmatter sits outside `verified_hash` (which covers the body), so these
writes do not demote a verified page.

Usage
-----
    python3 graph_metrics.py [VAULT_ROOT] [--write] [--json]

Default is a dry run that reports what it would write. `--write` applies.

Exit codes
----------
0   ran to completion, no findings
1   ran to completion, findings to report
2   did not run to completion -- a crash, or any zero denominator

Exit 2 on a zero denominator is deliberate. Zero pages scanned or zero
links classified is "did not run", never "clean": a silently empty parse
is the failure mode this whole script exists to avoid reproducing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent.parent / 'multi-skill' / 'scripts'
sys.path.insert(0, str(SHARED))

try:
    from check_wiki import parse_frontmatter
except ImportError as exc:  # pragma: no cover - wiring failure
    raise SystemExit(
        f'cannot import the shared frontmatter parser from {SHARED}: {exc}. '
        'This script deliberately reuses check_wiki.py rather than '
        'reimplementing a second reader of the same format.'
    ) from exc

NON_PAGE_DIRS = {'attachments'}

# Deliberately more permissive than any classifier below, so that
# `classified + unclassified == total` is a real conservation check and
# not a tautology over the same pattern.
ANY_WIKILINK = re.compile(r'!?\[\[([^\]]+)\]\]')

COMPUTED_FIELDS = ('cluster', 'betweenness', 'graph_computed')

TOP_N = 10

# Obsidian stores a colour group's colour as a single packed integer.
# The first four are the page-type palette (red, blue, green, amber); the
# next four extend it in the same 5C/AD/D6 component family so that a vault
# with up to eight communities gets eight distinct colours. Past eight the
# cycle repeats, and two clusters share a colour -- visible, not silent.
PALETTE = (
    14048348,  # D65C5C red
    6062550,  # 5C81D6 blue
    11392604,  # ADD65C green
    14069084,  # D6AD5C amber
    6084269,  # 5CD6AD teal
    11361494,  # AD5CD6 purple
    14048429,  # D65CAD magenta
    6084188,  # 5CD65C bright green
)


class Finding:
    """One reportable observation, in check_consistency.py's shape."""

    def __init__(
        self, check_id: str, file: str, message: str, fix_hint: str = ''
    ) -> None:
        self.check_id = check_id
        self.file = file
        self.message = message
        self.fix_hint = fix_hint

    def as_dict(self) -> dict[str, str]:
        return {
            'check_id': self.check_id,
            'file': self.file,
            'message': self.message,
            'fix_hint': self.fix_hint,
        }


def slugify(stem: str) -> str:
    """Kebab-case an arbitrary page stem for use as a cluster label."""
    out = re.sub(r'[^a-zA-Z0-9]+', '-', stem).strip('-').lower()
    return out or 'unnamed'


class PageIndex:
    """Resolve the supported Obsidian page-link forms without guessing."""

    def __init__(self, page_ids: set[str]) -> None:
        self.paths: dict[str, set[str]] = defaultdict(set)
        self.stems: dict[str, set[str]] = defaultdict(set)
        for page_id in sorted(page_ids):
            normalized = self._normalize(page_id)
            self.paths[normalized].add(page_id)
            self.paths[normalized.removeprefix('1-wiki/')].add(page_id)
            self.stems[Path(page_id).stem.casefold()].add(page_id)

    @staticmethod
    def _target(raw: str) -> str:
        target = raw.split('|', 1)[0].split('#', 1)[0]
        return target.strip().strip('"').replace('\\', '/')

    @staticmethod
    def _normalize(target: str) -> str:
        normalized = target.strip().replace('\\', '/').lstrip('/')
        while normalized.startswith('./'):
            normalized = normalized[2:]
        if normalized.casefold().endswith('.md'):
            normalized = normalized[:-3]
        return normalized.casefold()

    def resolve(self, raw: str) -> tuple[str, str | tuple[str, ...] | None]:
        """Return one exclusive bucket and canonical resolution data."""
        target = self._target(raw)
        folded = target.casefold()
        if not target:
            return 'unresolved', None
        if folded.startswith('0-raw/'):
            return 'raw', None
        if folded.startswith('1-wiki/attachments/'):
            return 'attachment', None
        if folded in {
            '1-wiki/hot.md',
            '1-wiki/index.md',
            '1-wiki/log.md',
        }:
            return 'wiki_meta', None
        key = self._normalize(target)
        candidates = (
            self.paths.get(key, set())
            if '/' in key
            else self.stems.get(key, set())
        )
        ordered = tuple(sorted(candidates))
        if len(ordered) == 1:
            return 'page', ordered[0]
        if len(ordered) > 1:
            return 'ambiguous', ordered
        page_prefixes = (
            '1-wiki/',
            'sources/',
            'concepts/',
            'entities/',
            'syntheses/',
        )
        if folded.startswith(page_prefixes) or '/' not in target:
            return 'unresolved', None
        return 'outside', None


def discover_page_dirs(wiki: Path) -> tuple[tuple[str, ...], list[Finding]]:
    """Return active direct-page directories and unsupported nested layouts."""
    active: list[str] = []
    findings: list[Finding] = []
    for child in sorted(wiki.iterdir()):
        if not child.is_dir() or child.name in NON_PAGE_DIRS:
            continue
        direct = list(child.glob('*.md'))
        if direct:
            active.append(child.name)
            continue
        nested = list(child.glob('**/*.md'))
        if nested:
            findings.append(
                Finding(
                    check_id='nested_page_dir_unsupported',
                    file=f'1-wiki/{child.name}',
                    message=(
                        f'{len(nested)} nested Markdown page(s) have no direct '
                        'page sibling; this direct-directory graph excludes '
                        'them.'
                    ),
                    fix_hint=(
                        'Move the pages to a direct page directory or extend '
                        'the layout deliberately before trusting the metrics.'
                    ),
                )
            )
    return tuple(active), findings


def collect_pages(
    wiki: Path, page_dirs: tuple[str, ...]
) -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    for sub in page_dirs:
        for path in sorted((wiki / sub).glob('*.md')):
            text = path.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            pages[f'1-wiki/{sub}/{path.name}'] = {
                'path': path,
                'stem': path.stem,
                'frontmatter': fm,
                'text': text,
            }
    return pages


def _path_covers(configured: str, page_dir: str) -> bool:
    """Whether one positive folder literal covers a page directory."""
    configured = configured.rstrip('/')
    page_dir = page_dir.rstrip('/')
    return page_dir == configured or page_dir.startswith(f'{configured}/')


def inspect_native_coverage(
    root: Path, page_dirs: tuple[str, ...]
) -> tuple[list[Finding], dict[str, Any]]:
    """Check only proof-bounded positive-union native coverage syntax."""
    findings: list[Finding] = []
    active = tuple(f'1-wiki/{name}' for name in page_dirs)
    stats: dict[str, Any] = {}

    graph_path = root / '.obsidian' / 'graph.json'
    graph_literals: tuple[str, ...] = ()
    graph_decidable = False
    try:
        graph_data = json.loads(graph_path.read_text(encoding='utf-8'))
        groups = graph_data.get('colorGroups')
        if not isinstance(groups, list):
            raise ValueError('colorGroups is not a list')
        queries = [g.get('query') for g in groups if isinstance(g, dict)]
        if len(queries) != len(groups) or not all(
            isinstance(query, str) for query in queries
        ):
            raise ValueError('every color group needs a string query')
        if queries and all(
            re.fullmatch(r'\["cluster":"[^"]+"\]', query)
            for query in queries
        ):
            stats['graph_colour_mode'] = 'cluster'
            graph_decidable = True
        else:
            parsed: list[str] = []
            for query in queries:
                match = re.fullmatch(r'path:(1-wiki(?:/[^\s()]+)?)', query)
                if match is None:
                    break
                parsed.append(match.group(1).rstrip('/'))
            if len(parsed) == len(queries):
                graph_literals = tuple(parsed)
                graph_decidable = True
                stats['graph_colour_mode'] = 'page-type'
            else:
                stats['graph_colour_mode'] = 'ambiguous'
                findings.append(
                    Finding(
                        check_id='graph_coverage_ambiguous',
                        file='.obsidian/graph.json',
                        message=(
                            'colorGroups contains mixed, Boolean, or unfamiliar '
                            'query syntax; directory coverage is not inferred.'
                        ),
                        fix_hint=(
                            'Use simple positive path: literals or all-cluster '
                            'queries before relying on coverage findings.'
                        ),
                    )
                )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        stats['graph_colour_mode'] = 'unreadable'
        findings.append(
            Finding(
                check_id='graph_config_unreadable',
                file='.obsidian/graph.json',
                message=f'graph colour coverage could not be read: {exc}.',
                fix_hint='Repair graph.json before relying on colour coverage.',
            )
        )

    graph_covered: list[str] = []
    if graph_decidable and stats['graph_colour_mode'] == 'page-type':
        for page_dir in active:
            if any(
                _path_covers(configured=item, page_dir=page_dir)
                for item in graph_literals
            ):
                graph_covered.append(page_dir)
            else:
                findings.append(
                    Finding(
                        check_id='graph_colour_dir_uncovered',
                        file=page_dir,
                        message=(
                            f'{page_dir}/ contributes metrics but no positive '
                            'graph path group covers it.'
                        ),
                        fix_hint=f'Add a path:{page_dir} colorGroups query.',
                    )
                )
        for item in graph_literals:
            if item != '1-wiki' and not (root / item).exists():
                findings.append(
                    Finding(
                        check_id='graph_colour_dir_stale',
                        file='.obsidian/graph.json',
                        message=(
                            f'positive graph path group names absent {item}/.'
                        ),
                        fix_hint=(
                            'Remove the obsolete group or restore the '
                            'directory.'
                        ),
                    )
                )
    stats['graph_dirs_covered'] = graph_covered

    base_path = root / '1-wiki' / 'graph.base'
    base_literals: tuple[str, ...] = ()
    base_decidable = False
    try:
        lines = base_path.read_text(encoding='utf-8').splitlines()
        start = lines.index('filters:')
        end = next(
            (
                i
                for i in range(start + 1, len(lines))
                if lines[i] and not lines[i].startswith((' ', '#'))
            ),
            len(lines),
        )
        block = [
            line for line in lines[start + 1 : end]
            if line.strip() and not line.lstrip().startswith('#')
        ]
        leaf = re.compile(r'^\s*- file\.inFolder\("([^"]+)"\)\s*$')
        if len(block) == 1 and (match := leaf.fullmatch(block[0])):
            base_literals = (match.group(1).rstrip('/'),)
            base_decidable = True
        elif block and block[0].strip() == 'or:':
            matches = [leaf.fullmatch(line) for line in block[1:]]
            if matches and all(match is not None for match in matches):
                base_literals = tuple(
                    match.group(1).rstrip('/')
                    for match in matches
                    if match is not None
                )
                base_decidable = True
        if not base_decidable:
            findings.append(
                Finding(
                    check_id='bases_coverage_ambiguous',
                    file='1-wiki/graph.base',
                    message=(
                        'top-level filters are not one positive folder leaf '
                        'or a flat positive OR union; directory coverage is '
                        'not inferred.'
                    ),
                    fix_hint=(
                        'Use the proof-bounded positive-union form before '
                        'relying on coverage findings.'
                    ),
                )
            )
    except (OSError, ValueError) as exc:
        findings.append(
            Finding(
                check_id='bases_config_unreadable',
                file='1-wiki/graph.base',
                message=f'Bases directory coverage could not be read: {exc}.',
                fix_hint='Repair graph.base before relying on Bases coverage.',
            )
        )

    base_covered: list[str] = []
    if base_decidable:
        for page_dir in active:
            if any(
                _path_covers(configured=item, page_dir=page_dir)
                for item in base_literals
            ):
                base_covered.append(page_dir)
            else:
                findings.append(
                    Finding(
                        check_id='bases_dir_uncovered',
                        file=page_dir,
                        message=(
                            f'{page_dir}/ contributes metrics but no positive '
                            'Bases folder filter covers it.'
                        ),
                        fix_hint=(
                            f'Add file.inFolder("{page_dir}") to the top-level '
                            'positive OR union.'
                        ),
                    )
                )
        for item in base_literals:
            if item != '1-wiki' and not (root / item).exists():
                findings.append(
                    Finding(
                        check_id='bases_dir_stale',
                        file='1-wiki/graph.base',
                        message=(
                            f'positive Bases folder filter names absent {item}/.'
                        ),
                        fix_hint=(
                            'Remove the obsolete filter or restore the '
                            'directory.'
                        ),
                    )
                )
    stats['bases_dirs_covered'] = base_covered
    return findings, stats


def build_edges(
    pages: dict[str, dict[str, Any]],
) -> tuple[
    set[tuple[str, str]],
    dict[str, set[str]],
    dict[str, int],
    list[Finding],
]:
    """Return undirected edges, inbound linkers, tallies, and findings.

    `inbound` maps a page to the set of DISTINCT pages linking to it, which
    is the same quantity Bases reports as `file.backlinks.length`. Keeping
    it separate from the undirected degree matters: the two differ whenever
    a link is not reciprocated, and reporting one under the other's name is
    exactly the kind of confident mislabelling this script exists to avoid.
    """
    edges: set[tuple[str, str]] = set()
    inbound: dict[str, set[str]] = {pid: set() for pid in pages}
    tally: dict[str, int] = defaultdict(int)
    findings: list[Finding] = []
    page_index = PageIndex(page_ids=set(pages))

    for pid, page in pages.items():
        for match in ANY_WIKILINK.finditer(page['text']):
            raw = match.group(1)
            bucket, resolution = page_index.resolve(raw)
            tally[bucket] += 1
            tally['total'] += 1
            if bucket != 'page':
                if bucket == 'ambiguous':
                    findings.append(
                        Finding(
                            check_id='page_link_ambiguous',
                            file=pid,
                            message=(
                                f'wikilink [[{raw[:60]}]] resolves to multiple '
                                f'pages: {", ".join(resolution or ())}. It '
                                'contributes no guessed edge.'
                            ),
                            fix_hint=(
                                'Path-qualify the link to one canonical page.'
                            ),
                        )
                    )
                elif bucket == 'unresolved':
                    findings.append(
                        Finding(
                            check_id='page_link_unresolved',
                            file=pid,
                            message=(
                                f'wikilink [[{raw[:60]}]] resolves to no '
                                'collected page, so it contributes no edge.'
                            ),
                            fix_hint=(
                                'Correct the target or path-qualify it to an '
                                'existing page.'
                            ),
                        )
                    )
                continue
            tgt = str(resolution)
            if tgt != pid:
                edges.add((min(pid, tgt), max(pid, tgt)))
                inbound[tgt].add(pid)

    classified = sum(
        tally[k]
        for k in (
            'raw',
            'attachment',
            'wiki_meta',
            'page',
            'ambiguous',
            'unresolved',
            'outside',
        )
    )
    if classified != tally['total']:
        findings.append(
            Finding(
                check_id='(internal)',
                file='(summary)',
                message=(
                    f'link conservation failed: {classified} bucketed vs '
                    f'{tally["total"]} seen. The classifier lost links.'
                ),
                fix_hint=(
                    'This is a bug in PageIndex resolution; do not trust the '
                    'output.'
                ),
            )
        )
    return edges, inbound, dict(tally), findings


def louvain(size: int, links: list[tuple[int, int, float]]) -> list[int]:
    """Modularity optimization by local moving, then aggregation.

    Deterministic: every ordering decision is sorted, and improvement
    requires strictly beating the incumbent by more than an epsilon.
    """
    membership = list(range(size))
    cur_n, cur_links = size, links
    mapping = list(range(size))

    while True:
        nbr: list[dict[int, float]] = [
            defaultdict(float) for _ in range(cur_n)
        ]
        k = [0.0] * cur_n
        m2 = 0.0
        for a, b, w in cur_links:
            if a == b:
                k[a] += 2 * w
                m2 += 2 * w
                continue
            nbr[a][b] += w
            nbr[b][a] += w
            k[a] += w
            k[b] += w
            m2 += 2 * w
        if m2 == 0:
            break

        comm = list(range(cur_n))
        tot = k[:]
        improved = False
        for _ in range(40):
            moved = False
            for i in sorted(range(cur_n), key=lambda x: (-k[x], x)):
                ci = comm[i]
                tot[ci] -= k[i]
                weights: dict[int, float] = defaultdict(float)
                weights[ci] += 0.0
                for j, w in nbr[i].items():
                    weights[comm[j]] += w
                best_c = ci
                best_gain = weights[ci] - tot[ci] * k[i] / m2
                for c, w in sorted(weights.items()):
                    gain = w - tot[c] * k[i] / m2
                    if gain > best_gain + 1e-12:
                        best_c, best_gain = c, gain
                tot[best_c] += k[i]
                comm[i] = best_c
                if best_c != ci:
                    moved = improved = True
            if not moved:
                break
        if not improved:
            break

        labels = sorted(set(comm))
        relabel = {c: i for i, c in enumerate(labels)}
        comm = [relabel[c] for c in comm]
        membership = [comm[mapping[i]] for i in range(size)]
        mapping = membership[:]

        agg: dict[tuple[int, int], float] = defaultdict(float)
        for a, b, w in cur_links:
            x, y = comm[a], comm[b]
            agg[(min(x, y), max(x, y))] += w
        cur_n = len(labels)
        cur_links = [(a, b, w) for (a, b), w in agg.items()]
        if cur_n == size:
            break
    return membership


def betweenness(size: int, adj: list[set[int]]) -> list[float]:
    """Brandes betweenness on an unweighted undirected graph."""
    score = [0.0] * size
    for s in range(size):
        stack: list[int] = []
        pred: list[list[int]] = [[] for _ in range(size)]
        sigma = [0] * size
        dist = [-1] * size
        sigma[s], dist[s] = 1, 0
        queue = deque([s])
        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = [0.0] * size
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                score[w] += delta[w]
    norm = (size - 1) * (size - 2) / 2 if size > 2 else 1
    return [s / 2 / norm for s in score]


def upsert_frontmatter(text: str, values: dict[str, str]) -> str:
    """Set keys in an existing frontmatter block, leaving the body alone.

    Only the named keys are touched. Key order is preserved for keys that
    already exist; new keys are appended just before the closing fence.
    """
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        raise ValueError('page has no frontmatter block')
    end = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == '---'), -1
    )
    if end == -1:
        raise ValueError('page has an unterminated frontmatter block')

    remaining = dict(values)
    for i in range(1, end):
        key = lines[i].split(':', 1)[0].strip()
        if key in remaining:
            lines[i] = f'{key}: {remaining.pop(key)}'
    insert_at = end
    for key, value in remaining.items():
        lines.insert(insert_at, f'{key}: {value}')
        insert_at += 1
    return '\n'.join(lines)


def cluster_colour_groups(anchors: list[str]) -> list[dict[str, Any]]:
    """Build Obsidian colour groups keyed on the computed cluster property."""
    return [
        {
            'query': f'["cluster":"{a}"]',
            'color': {'a': 1, 'rgb': PALETTE[i % len(PALETTE)]},
        }
        for i, a in enumerate(anchors)
    ]


def write_colour_groups(root: Path, anchors: list[str]) -> tuple[bool, str]:
    """Swap graph.json's colorGroups for cluster groups, in place.

    Only `colorGroups` is touched; every other key -- the force values, the
    saved zoom, the display toggles -- is left exactly as found, because
    they are the reader's own view state rather than anything this script
    computed.

    Node colour is Obsidian's only free channel (size is hardwired to
    inbound links), so colouring by community necessarily REPLACES
    colouring by page type. There is no arrangement that shows both.
    """
    path = root / '.obsidian' / 'graph.json'
    if not path.exists():
        return False, f'{path} does not exist'
    try:
        config = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        return False, f'{path} is not valid JSON: {exc}'
    config['colorGroups'] = cluster_colour_groups(anchors=anchors)
    path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    return True, f'wrote {len(anchors)} cluster colour groups'


def run(
    root: Path, write: bool, colour_clusters: bool = False
) -> tuple[list[Finding], dict[str, Any], int]:
    findings: list[Finding] = []
    wiki = root / '1-wiki'
    if not wiki.is_dir():
        findings.append(
            Finding(
                check_id='vault_unreadable',
                file=str(root),
                message=f'no 1-wiki/ directory under {root}.',
                fix_hint=(
                    'Run this from the vault root, or pass the root as the '
                    'first argument.'
                ),
            )
        )
        return findings, {}, 2

    page_dirs, directory_findings = discover_page_dirs(wiki=wiki)
    findings.extend(directory_findings)
    pages = collect_pages(wiki=wiki, page_dirs=page_dirs)
    stats: dict[str, Any] = {
        'pages': len(pages),
        'page_dirs': list(page_dirs),
        'pages_by_dir': {
            page_dir: sum(
                pid.startswith(f'1-wiki/{page_dir}/') for pid in pages
            )
            for page_dir in page_dirs
        },
    }
    if not pages:
        findings.append(
            Finding(
                check_id='no_pages',
                file='(summary)',
                message=(
                    'scanned 0 pages. Nothing to compute; this is expected on '
                    'a fresh template and is reported as "did not run" rather '
                    'than "clean".'
                ),
                fix_hint='Ingest at least one source, then re-run.',
            )
        )
        return findings, stats, 2

    coverage_findings, coverage_stats = inspect_native_coverage(
        root=root, page_dirs=page_dirs
    )
    findings.extend(coverage_findings)
    stats.update(coverage_stats)

    unreadable = [pid for pid, p in pages.items() if p['frontmatter'] is None]
    for pid in unreadable:
        findings.append(
            Finding(
                check_id='frontmatter_unreadable',
                file=pid,
                message=(
                    'frontmatter did not parse, so this page carries no '
                    'metadata into the graph.'
                ),
                fix_hint=(
                    'Check for a CRLF line ending, a byte-order mark, or a '
                    'missing closing --- fence.'
                ),
            )
        )

    edges, inbound, tally, link_findings = build_edges(pages=pages)
    findings.extend(link_findings)
    stats.update(
        {
            'links_total': tally.get('total', 0),
            'links_page': tally.get('page', 0),
            'links_raw': tally.get('raw', 0),
            'links_attachment': tally.get('attachment', 0),
            'links_wiki_meta': tally.get('wiki_meta', 0),
            'links_page_ambiguous': tally.get('ambiguous', 0),
            'links_page_unresolved': tally.get('unresolved', 0),
            'links_outside': tally.get('outside', 0),
            'edges': len(edges),
            'frontmatter_parsed': len(pages) - len(unreadable),
        }
    )

    if tally.get('total', 0) == 0:
        findings.append(
            Finding(
                check_id='no_links',
                file='(summary)',
                message=(
                    f'scanned {len(pages)} pages and found 0 wikilinks. A '
                    'zero link count is treated as a parse failure, not as a '
                    'vault with no links.'
                ),
                fix_hint=(
                    'Confirm pages really do carry [[wikilinks]]; if they do, '
                    'the link pattern has drifted.'
                ),
            )
        )
        return findings, stats, 2

    ids = sorted(pages)
    idx = {pid: i for i, pid in enumerate(ids)}
    n = len(ids)
    adj: list[set[int]] = [set() for _ in range(n)]
    for a, b in edges:
        adj[idx[a]].add(idx[b])
        adj[idx[b]].add(idx[a])
    degree = [len(adj[i]) for i in range(n)]
    indeg = [len(inbound[pid]) for pid in ids]

    weighted = [(idx[a], idx[b], 1.0) for a, b in sorted(edges)]
    community = louvain(size=n, links=weighted)
    scores = betweenness(size=n, adj=adj)

    members: dict[int, list[int]] = defaultdict(list)
    for i, c in enumerate(community):
        members[c].append(i)
    # Anchor = highest-degree member, ties broken by id so the label is
    # deterministic. The anchor slug, not the community index, is stored.
    anchor: dict[int, str] = {}
    for c, group in members.items():
        best = min(group, key=lambda i: (-degree[i], ids[i]))
        anchor[c] = slugify(stem=pages[ids[best]]['stem'])
    stats['communities'] = len(members)
    stats['clusters'] = sorted(
        ({'anchor': anchor[c], 'size': len(g)} for c, g in members.items()),
        key=lambda d: (-d['size'], d['anchor']),
    )

    # Rankings go in the terminal report too, so the two measures Obsidian
    # cannot compute are readable without opening the vault.
    order = sorted(range(n), key=lambda i: (-indeg[i], ids[i]))
    stats['top_hubs'] = [
        {
            'page': pages[ids[i]]['stem'],
            'inbound': indeg[i],
            'degree': degree[i],
        }
        for i in order[:TOP_N]
    ]
    order = sorted(range(n), key=lambda i: (-scores[i], ids[i]))
    stats['top_bridges'] = [
        {
            'page': pages[ids[i]]['stem'],
            'betweenness': round(scores[i], 4),
            'inbound': indeg[i],
            'cluster': anchor[community[i]],
        }
        for i in order[:TOP_N]
    ]

    stamp = date.today().isoformat()
    written = 0
    for i, pid in enumerate(ids):
        page = pages[pid]
        if page['frontmatter'] is None:
            continue
        values = {
            'cluster': anchor[community[i]],
            'betweenness': f'{scores[i]:.4f}',
            'graph_computed': stamp,
        }
        if not write:
            continue
        try:
            new_text = upsert_frontmatter(text=page['text'], values=values)
        except ValueError as exc:
            findings.append(
                Finding(
                    check_id='write_skipped',
                    file=pid,
                    message=str(exc),
                    fix_hint='Fix the frontmatter.',
                )
            )
            continue
        if new_text != page['text']:
            page['path'].write_text(new_text, encoding='utf-8')
            written += 1
    stats['pages_written'] = written if write else 0
    stats['dry_run'] = not write
    stats['cluster_groups'] = [c['anchor'] for c in stats['clusters']]

    if colour_clusters:
        ok, message = write_colour_groups(
            root=root, anchors=stats['cluster_groups']
        )
        stats['colour_groups_written'] = ok
        if not ok:
            findings.append(
                Finding(
                    check_id='colour_groups_skipped',
                    file='.obsidian/graph.json',
                    message=message,
                    fix_hint='Create the file from Obsidian, or fix its JSON.',
                )
            )

    return findings, stats, 1 if findings else 0


def report(findings: list[Finding], stats: dict[str, Any]) -> None:
    print('Link-graph metrics')
    print('-' * 40)
    for key in (
        'pages',
        'frontmatter_parsed',
        'links_total',
        'links_page',
        'links_raw',
        'links_attachment',
        'links_wiki_meta',
        'links_page_ambiguous',
        'links_page_unresolved',
        'links_outside',
        'edges',
        'communities',
    ):
        if key in stats:
            print(f'{key:22s} {stats[key]}')
    if stats.get('page_dirs'):
        print(f'{"page_dirs":22s} {", ".join(stats["page_dirs"])}')
        print(
            f'{"graph_colour_mode":22s} '
            f'{stats.get("graph_colour_mode", "unknown")}'
        )
    if stats.get('clusters'):
        print('\nclusters (anchor slug, size):')
        for c in stats['clusters']:
            print(f'  {c["size"]:4d}  {c["anchor"]}')
    if stats.get('top_hubs'):
        print(f'\ntop {TOP_N} hubs (distinct pages linking in):')
        for h in stats['top_hubs']:
            print(
                f'  in={h["inbound"]:4d}  deg={h["degree"]:4d}  '
                f'{h["page"][:48]}'
            )
    if stats.get('top_bridges'):
        print(f'\ntop {TOP_N} bridges (betweenness):')
        print('  the ranking is the signal; the values move between runs')
        for b in stats['top_bridges']:
            print(
                f'  {b["betweenness"]:.4f}  in={b["inbound"]:3d}  '
                f'{b["page"][:38]}  [{b["cluster"][:18]}]'
            )
    if stats.get('colour_groups_written'):
        print(
            f'\nrewrote .obsidian/graph.json colorGroups: '
            f'{len(stats["cluster_groups"])} cluster groups '
            '(page-type colouring replaced -- node colour is one channel)'
        )
    if stats.get('dry_run'):
        print('\nDRY RUN - no files written. Re-run with --write to apply.')
    else:
        print(f'\nwrote frontmatter on {stats.get("pages_written", 0)} pages')
    if findings:
        print(f'\n{len(findings)} finding(s):')
        for f in findings:
            print(f'  [{f.check_id}] {f.file}: {f.message}')
            if f.fix_hint:
                print(f'      fix: {f.fix_hint}')
    else:
        print('\nno findings')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Compute Louvain communities and Brandes betweenness over the '
            'wiki link graph and store them as frontmatter properties. '
            'Exit 0 clean, 1 findings, 2 did not run (any zero denominator '
            'counts as did-not-run, never as clean).'
        )
    )
    parser.add_argument('root', nargs='?', default='.')
    parser.add_argument(
        '--write',
        action='store_true',
        help='apply the computed values; default is a dry run',
    )
    parser.add_argument(
        '--colour-clusters',
        action='store_true',
        help=(
            'also rewrite .obsidian/graph.json colorGroups to colour by '
            'computed cluster. REPLACES page-type colouring: node colour '
            "is Obsidian's only free channel, so it shows one or the "
            'other, never both. Implies --write.'
        ),
    )
    parser.add_argument(
        '--json', action='store_true', help='emit findings as JSON'
    )
    args = parser.parse_args(argv)

    findings, stats, code = run(
        root=Path(args.root).resolve(),
        write=args.write or args.colour_clusters,
        colour_clusters=args.colour_clusters,
    )
    if args.json:
        print(
            json.dumps(
                {
                    'stats': stats,
                    'findings': [f.as_dict() for f in findings],
                },
                indent=2,
            )
        )
    else:
        report(findings=findings, stats=stats)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
