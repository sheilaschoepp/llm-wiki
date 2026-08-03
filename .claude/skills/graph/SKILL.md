---
name: graph
description: Set up, refresh, or retrofit the vault's native Obsidian map — the graph view's colour groups and force settings, the Bases views in 1-wiki/graph.base, and the two link-graph metrics Obsidian cannot compute (Louvain communities and Brandes betweenness), which are written to page frontmatter by a script. Use when the user asks to see the shape of the vault, find hub or bridge or neglected pages, colour or tune the graph view, refresh the cluster and betweenness values after an ingest, or add this map to an existing vault whose schema has drifted from the template's. Not for structural page checks (lint), semantic review (audit), whole-wiki direction (reflect), or answering a research question (query).
---

# Graph

Give the vault a map that lives inside Obsidian. Three surfaces, in
descending order of how much they can be trusted:

1. **The graph view** (`.obsidian/graph.json`) — live, computed by Obsidian,
   never stale. Colour groups per page type, forces tuned to keep groups
   legible instead of collapsing into one hairball.
2. **Bases views** (`1-wiki/graph.base`) — three tables: Hubs, Bridges,
   Neglected. Bases is the only native surface that produces a sorted
   ranking, which is the whole reason it is here; the graph draws structure
   but cannot rank, and search filters but cannot sort by a number. Status
   and support-depth views are deliberately absent — a linter already owns
   those, and a second copy is just somewhere for the two to disagree.
3. **Two computed properties** (`cluster:`, `betweenness:`) — written into
   frontmatter by `scripts/graph_metrics.py`, and **stale the moment
   anything is ingested**. These exist because Obsidian genuinely cannot
   compute them; everything else here is live.

There is no generated HTML page, no build artifact in git, and nothing to
open outside Obsidian. That is deliberate: this vault sets
`"webviewer": false`, so a generated page could not be opened in the app
at all.

## When to invoke

- Setting up the map in a new vault, or adding it to an existing one.
- After an ingest, to refresh `cluster:` and `betweenness:`.
- When the user asks which pages are hubs, bridges, or neglected.
- When the graph view is an unreadable hairball, or a page type renders in
  default grey because no colour group covers it.
- To retrofit the map into a populated vault whose schema has drifted.

## When not to invoke

- Structural page checks, index drift, broken links → `lint`.
- Whether notes are any good, atomic, or source-supported → `audit`.
- What the wiki is becoming, what to read next → `reflect`.
- Answering a research question from the wiki → `query`.

## What Obsidian can and cannot do

Established by reading Obsidian's own documentation, not assumed. Do not
re-derive this each run, and do not promise an adopter more than this.

| Measure | Native? |
| --- | --- |
| Force-directed graph, filter, search | Yes — and the search grammar beats any hand-rolled box |
| Hubs (in-degree) | Yes, exactly — `file.backlinks.length`, sortable in Bases |
| Thinnest-connected pages | Yes — the same formula, ascending |
| Support depth, status, freshness | Yes — ordinary frontmatter |
| Raw citation load | Degraded — Bases counts distinct citing notes, not `#page=` locators, and `0-raw/` sits in `userIgnoreFilters` |
| Louvain communities | **No** — Bases forbids a self-referencing formula, so nothing can iterate to convergence |
| Brandes betweenness | **No** — needs all-pairs shortest paths |
| Frontmatter-vs-inline support trail | **No, at any price** — `file.links` includes frontmatter, and the `Sources` callout re-lists every frontmatter source, so the set difference cannot isolate "declared but never cited" |

The last row is a check, not a view: a measure that reads zero on a healthy
vault belongs in a linter.

## Procedure

```
Graph progress:
- [ ] Step 1: Read memory; establish what the vault actually contains
- [ ] Step 2: Cover every page directory with a colour group
- [ ] Step 3: Install or refresh the Bases views
- [ ] Step 4: Recompute cluster: and betweenness: (only if wanted)
- [ ] Step 5: Verify in Obsidian, and report honestly
```

1. **Read memory and establish the vault's shape.**

   Read `.claude/skills/graph/graph-memory.md` and
   `.claude/skills/multi-skill/multi-skill-memory.md` first.

   Then run the dry-run pass, which reports coverage before it reports
   anything else:

   ```bash
   python3 .claude/skills/graph/scripts/graph_metrics.py .
   ```

   **Read the denominators before the findings.** `pages`,
   `frontmatter_parsed`, and `links_total` say whether the run saw the
   vault at all. Exit code 2 means it did not run — zero pages or zero
   links is reported as did-not-run, never as clean, because a silently
   empty parse is exactly the failure this script exists not to repeat.

   Page discovery is disk-authoritative: every immediate directory under
   `1-wiki/` except `attachments/` that contains direct Markdown pages
   enters the metrics. Empty directories are silent. A directory with only
   nested Markdown emits `nested_page_dir_unsupported` instead of silently
   flattening a layout the resolver does not model.

   Native coverage is checked separately. `graph_colour_dir_uncovered` and
   `bases_dir_uncovered` mean an active metric directory has no proven
   positive coverage in the corresponding consumer. The parser proves only
   simple positive graph path literals and a single positive Bases folder
   leaf or flat `or:` union; conjunction, negation, mixed, or unfamiliar
   syntax emits `*_coverage_ambiguous` and suppresses per-directory
   conclusions. Exact and ancestor paths count as coverage. A configured
   path is stale only when it no longer exists on disk; an existing empty
   directory remains silent.

   The computed edge resolver accepts unique path-qualified, extensionless,
   case-variant, and bare-basename page links. It never guesses among
   collisions: `page_link_ambiguous` names every candidate and
   `page_link_unresolved` names a target with no collected page; neither
   creates an edge. Report those denominators. When either is nonzero, the
   computed graph is a documented lower bound, not the complete Obsidian
   graph.

2. **Cover every page directory with a colour group.**

   In `.obsidian/graph.json`, every active page directory under `1-wiki/`
   pages needs a `colorGroups` entry, or those pages render in default grey
   and read as "other" with nothing saying so. Derive the list from what is
   on disk, never from a hardcoded set — a hardcoded list is how syntheses
   went uncoloured for as long as it did.

   Colours currently in use, chosen so the four share a component
   vocabulary: sources `#D65C5C` (14048348), concepts `#5C81D6` (6062550),
   entities `#ADD65C` (11392604), syntheses `#D6AD5C` (14069084).

   Forces: `linkStrength` 0.3, `centerStrength` 0.12, `repelStrength` 18,
   `linkDistance` 250. These are a starting point. Push `linkStrength`
   toward 0.2 if groups still read as merged; ease `repelStrength` back
   toward 12 if they scatter into unreadable islands. On a vault under
   about fifty pages, loosen them — the defaults are tuned for a few
   hundred.

   Leave `hideUnresolved: true` alone unless asked. It suppresses dangling
   `authors:` links to collaborators with no entity page, which the schema
   creates on purpose; turning it off floods the graph with phantom nodes.

   Colouring by page type and colouring by community are **mutually
   exclusive**. Node colour is Obsidian's only free channel — size is
   hardwired to inbound links — so the graph shows one or the other, never
   both. Page type is the better default: it is live, it needs no script,
   and it never goes stale. Switch to community colouring only when the
   question is "what are the regions of this vault", using Step 4's
   `--colour-clusters`, and switch back by restoring the four `path:`
   groups above.

3. **Install or refresh the Bases views.**

   `1-wiki/graph.base` carries three views: Hubs and Neglected are live,
   computed by Obsidian from frontmatter the schema already requires;
   Bridges reads the `betweenness:` and `cluster:` properties Step 4
   writes, so it is a snapshot and carries `graph_computed:` as a column
   saying so.

   Bridges earns its place by showing what the graph hides. Obsidian sizes
   a node by inbound links, so a page joining two regions while almost
   nothing cites it renders as one of the smallest dots on the map — in a
   real 341-page vault the third- and ninth-ranked bridges had in-degree 2
   and 3, both synthesis pages.

   Filters key off a flat positive `or:` union of `file.inFolder(...)`, so
   the coverage check is mechanically decidable and the views survive frontmatter
   drift and break only on a folder rename — and when that happens the rows
   do not vanish silently, they stop matching a filter the Step 1 report
   already named.

   Before shipping a change to it, check that every `formula.X` referenced
   in a view is defined in the `formulas:` block. An undefined reference
   fails silently in Bases.

   Obsidian rewrites a `.base` file when a view is edited in the app: keys
   get reordered and comments are stripped. Keep explanation in this skill,
   not only in the YAML.

4. **Recompute the two non-native metrics, only if the user wants them.**

   ```bash
   python3 .claude/skills/graph/scripts/graph_metrics.py . --write
   ```

   This writes `cluster:`, `betweenness:`, and `graph_computed:` and
   nothing else. It does not touch `updated:` — that records content
   recency, and a whole-vault recompute would reset it everywhere. It does
   not touch the body, so `verified_hash` still matches and a verified page
   stays verified.

   Both values are global: they change on page A because page B was
   edited. On a vault under roughly 160 pages, one ingest rewrites the
   cluster of most pages. Say so when reporting, and treat the betweenness
   *ranking* as the signal — individual values move far more than the order
   does.

   Nothing recomputes these automatically, and an ingest will not: writing
   every page's frontmatter as a side effect of adding one source is too
   large a hidden action. Staleness is surfaced instead — `lint`'s
   `graph_metrics_stale` reports when a page carries an `updated:` later
   than the newest `graph_computed:` stamp, or when a page has no stamp
   while others do.

   `cluster:` stores the community's anchor page slug, never a community
   index. Indices are renumbered by size rank on every run, so a stored
   integer can name a different community tomorrow while looking unchanged.

   The dry run prints both rankings — top hubs by distinct inbound links,
   and top bridges by betweenness — so neither measure requires opening the
   vault to read. In-degree and undirected degree are reported as separate
   columns because they differ whenever a link is not reciprocated, and the
   Bases `inbound` column is in-degree.

   To drive the graph view's colours from the computed communities:

   ```bash
   python3 .claude/skills/graph/scripts/graph_metrics.py . --colour-clusters
   ```

   This implies `--write`, then rewrites only the `colorGroups` array in
   `.obsidian/graph.json` to one group per community, keyed
   `["cluster":"<anchor>"]`. Every other key — the forces, the saved zoom,
   the display toggles — is left exactly as found, because those are the
   reader's view state and not this script's to set. It replaces page-type
   colouring, per Step 2. Eight distinct colours are available; a ninth
   community reuses the first colour rather than inventing one.

5. **Verify in Obsidian, and report honestly.**

   Three checks that take a minute and catch most of what can go wrong:

   - Open the graph. Every node should carry a group colour. **A grey node
     is a page in a directory no colour group covers** — the fastest drift
     signal available.
   - Open `1-wiki/graph.base`. Each view should render rows, not an
     empty table. An empty Bases view and a Bases view with nothing to
     report look identical, so compare against the Step 1 page count.
   - Pick a page with `sources:` frontmatter and confirm the source shows
     under Outgoing Links, and the page under that source's Backlinks.

   Report the denominators, not just the findings. Name anything the map
   cannot see.

For adding this to a populated vault whose schema has already diverged, see
`references/retrofit.md` — the merge-don't-overwrite procedure, which
matters because `.obsidian/graph.json` is tracked and replacing it destroys
the adopter's own view state.

Regression tests for the script live in `scripts/tests/test_graph_metrics.py`
— they pin the link-bucket classifier, the link-conservation invariant, the
unique indexed resolver and its ambiguity boundary, the zero-denominator
exits, the drift findings, the frontmatter upsert leaving
the body byte-identical, and the betweenness and Louvain maths against
hand-checked graphs. After changing `scripts/graph_metrics.py`, run:

```bash
pytest .claude/skills/graph/scripts/tests/ -q
```

## Limits

- Never writes to `0-raw/`.
- Writes only `cluster:`, `betweenness:`, and `graph_computed:` into page
  frontmatter, only on `--write`, and never touches a page body.
- Never replaces `.obsidian/graph.json` wholesale on a populated vault;
  merges `colorGroups` and leaves view state alone.
- Does not create, promote, or edit wiki page content.
- Reuses the shared frontmatter parser rather than reimplementing one. A
  second reader of this format is what produced the silent parse bug this
  script's guards exist to prevent.
- Edit `.obsidian/graph.json` with Obsidian closed. Obsidian holds graph
  settings in memory and rewrites the file on quit.

## Self-report

Every run ends with a short, honest account of the limitations hit this run
and how this skill should be upgraded, per
`.claude/skills/multi-skill/references/self-report.md`. When the run hit no
limitation, it reads `none noted this run`.
