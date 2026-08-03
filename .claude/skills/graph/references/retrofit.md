# Retrofitting the map into a populated, drifted vault

The template ships this map already wired. A vault that was created from
the template months ago and has since ingested real sources and edited its
own schema is a different problem: its `.obsidian/` files carry the
adopter's own settings, and its `1-wiki/` may hold page directories the
template never had.

The governing rule is **merge, never overwrite**. `.obsidian/graph.json` is
tracked in git, so a template-to-vault pull can silently replace live view
state with the template's. That is the most destructive step in this
procedure and the one most easily done by accident.

## What actually drifts

Moving delivery into Obsidian's native surfaces removes most of the drift
surface a custom parser would have had. Obsidian is the reference
implementation of `[[wikilink]]`; the metric script supports the documented
subset it can reproduce safely: unique path-qualified, bare, extensionless,
and case-variant targets. Ambiguous names are not guessed. They emit
`page_link_ambiguous`; missing targets emit `page_link_unresolved`; both are
excluded from computed edges and make the metrics a documented lower bound.

What replaces parse drift is **config drift**, and it fails quietly:

- A `colorGroups` query is free text. A query matching nothing colours
  nothing and reports nothing. Add a page directory and its pages render
  in default grey.
- A Bases filter keys on property names and value shapes. A renamed or
  newly-quoted property yields fewer rows, and a view with zero rows looks
  exactly like a view with nothing to report.
- `userIgnoreFilters` in `.obsidian/app.json` uses prefix matching, so a
  new file whose name begins with an excluded prefix disappears from
  search and graph without notice.
- `cluster:` and `betweenness:`, if used, are stale from the next ingest
  onward and carry no native staleness warning beyond `graph_computed:`.

## Phase 0 — baseline

1. Confirm a clean working tree. If `.obsidian/graph.json` is untracked in
   this vault, commit it first. That commit is the undo button for
   everything below.
2. Record ground truth, at any depth, so later coverage numbers mean
   something:

   ```bash
   find 1-wiki -name '*.md' | wc -l
   ```

## Phase 1 — detect before deciding

3. Run the dry pass from the vault root:

   ```bash
   python3 .claude/skills/graph/scripts/graph_metrics.py .
   ```

4. **Read the coverage line before any finding.** If `pages` is below the
   Phase 0 count, stop — the run cannot see the vault and nothing below is
   trustworthy. Exit code 2 means it did not run; zero pages or zero links
   is never reported as clean.

5. Triage each finding as a decision, not a to-do:
   - `graph_colour_dir_uncovered` / `bases_dir_uncovered` — pages in the
     directory already contribute to metrics, but the named native surface
     lacks proven positive coverage. Add a simple path group or a positive
     `file.inFolder(...)` leaf to the top-level flat `or:` union.
   - `graph_coverage_ambiguous` / `bases_coverage_ambiguous` — the consumer
     uses Boolean, negated, mixed, or unfamiliar scope syntax. Do not infer
     missing directories until a human reads that expression.
   - `nested_page_dir_unsupported` — Markdown exists only below a nested
     subdirectory; it is not silently flattened into the direct-page graph.
   - `frontmatter_unreadable` — usually a CRLF line ending, a byte-order
     mark, or a missing closing fence. Fix the page; do not work around it.
   - `page_link_ambiguous` — the target names several collected pages. It
     contributes no guessed edge; path-qualify it.
   - `page_link_unresolved` — the page-intent target names no collected
     page. Correct it or accept that the computed graph is a lower bound.

## Phase 2 — apply, merging

6. **`.obsidian/graph.json`: do not replace the file.** Merge `colorGroups`
   only, one entry per page directory that exists **on disk**, derived from
   the filesystem rather than a hardcoded list. Leave `scale`, `close`, and
   the four force values alone unless the adopter asks — those are their
   view state, and the template's forces are tuned for a few hundred pages.

7. **`.obsidian/app.json`: add to `userIgnoreFilters`, do not replace it.**
   The array should cover `0-raw/`, `2-outputs/`, `a-archive/`, and the
   three orientation files `1-wiki/hot.md`, `1-wiki/index.md`, and
   `1-wiki/log.md`. Obsidian matches these on prefix, so the entries for
   the three files are written without the extension. Without the index
   entry, that file links to every page and flattens the graph into a
   starburst.

8. Copy `1-wiki/graph.base` in, then widen its `filters:` block to
   include any page directory Phase 1 reported as unknown.

9. Decide `hideUnresolved` deliberately rather than inheriting it. `true`
   hides dangling `authors:` links the schema creates on purpose, and also
   hides genuinely broken ones. Broken links are a linter's job, not the
   graph's.

## Phase 3 — verify

10. Open the graph. **Every node should carry a group colour.** Grey is the
    native equivalent of a coverage gap and takes seconds to spot.

11. Open each Bases view and confirm it renders rows. Compare the row count
    against the Phase 0 page count; an empty view is indistinguishable from
    an empty result.

12. Pick three pages with `sources:` frontmatter. Confirm each source
    appears under Outgoing Links and the page under that source's
    Backlinks. If not, this Obsidian version does not index frontmatter
    links and the support-related views will under-report.

13. `git diff .obsidian/` before committing. Anything outside
    `colorGroups` and `userIgnoreFilters` is Obsidian having rewritten the
    file behind you — edit these files with Obsidian closed.

## Failure modes and their tells

| Tell | Cause |
| --- | --- |
| Your edit reverts on quit | Obsidian was open while the file was edited |
| Grey nodes in the graph | A page directory no colour group covers |
| The graph is a starburst | The index file is missing from `userIgnoreFilters` |
| A Bases view is empty | A filter keys on a property this vault renamed |
| Source pages look under-connected | Frontmatter links are not being indexed |
| Coverage reads 0 pages | Run from the vault root, not from the script's directory |
