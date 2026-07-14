---
name: compare
description: "Create a structured side-by-side comparison of 2-4 same-type wiki pages: sources, concepts, entities, or syntheses. Use when the user names 2-4 same-type pages and asks to compare, contrast, diff, or look at them side-by-side, asks 'how do X and Y differ', 'what do A B and C agree on', phrases it as 'X vs Y', asks 'which of these is better' or 'how does X stack up against Y', or wants a comparison table. Not for a single page or fewer than two targets (use query or brief), mixed-type pages, more than four targets, a specific research question (use query), broad topic orientation (use brief), or a durable cross-source argument (use synthesis). Reads concept/entity, source, and synthesis pages; surfaces agreements, differences, and source-support strength; marks draft targets; states a verdict; then saves to 2-outputs/compare/. Pure output, no wiki integration."
---

# compare

Compare a small set of same-type wiki pages.

## Purpose

A comparison makes differences visible without turning them into a durable synthesis automatically.

## When To Invoke

Use when the user names 2-4 pages that are all the same type (all sources, all concepts, all entities, or all syntheses) and asks to compare them. Confirm the pages exist and share one type before proceeding (Step 1 carries the guard).

## When Not To Invoke

- Fewer than two, or more than four, targets. Compare handles 2-4 same-type pages.
- Mixed page types. Compare needs one shared category; drop the odd-type target or route the set out — there is no informal mixed-type mode.
- A specific research question, or a which-is-*correct* (truth) question. Use `query` (or `audit`).
- Broad topic orientation with no named pairing. Use `brief`.
- A durable cross-source argument or topic entry point. Use `synthesis`.

## Procedure

```text
Compare Progress
- [ ] 1. Confirm targets (exist, 2-4 count, same type, record status)
- [ ] 2. Load orientation (hot.md, index.md, compare-memory.md, multi-skill-memory.md)
- [ ] 3. Read target pages
- [ ] 4. Choose dimensions
- [ ] 5. Save the comparison
- [ ] 6. Verify the comparison
- [ ] 7. Flag follow-ups (no wiki integration)
- [ ] 8. Update hot and log
```

1. **Confirm targets.** Verify every named page exists and identify each one's type, reading only frontmatter at this step (the full-body read is Step 3). Resolve existence against the file on disk; `index.md` (loaded in Step 2 — read it first if a name is ambiguous here) is for suggesting the closest match, not the authority on existence. A target's comparison *category* is one of `source | concept | entity | synthesis`, read from frontmatter, not folder or H1: a `concept` / `entity` / `synthesis` page's category is its `type:` value directly, but every page under `1-wiki/sources/` is category `source` regardless of its `type: paper` / `article` / `media` / `other` sub-type (all source pages share one callout set, so a paper and an article compare cleanly). This category — not the raw `type:` — is what the same-type guard below checks and what Step 5 records as `target_type`.
   - Every stop-and-ask branch below uses `AskUserQuestion`, ordering the recommended option first and marking it `(Recommended)` (CLAUDE.md → Communication style), or stating "no recommendation" for a genuine no-lean.
   - If a named page does not exist or is ambiguous, stop and ask which page they mean — offer the closest `index.md` match first, marked `(Recommended)`; do not substitute a near-match or silently proceed with fewer targets.
   - If more than four targets are named, stop and ask which 2-4 to compare (which of the user's pages to keep is their call — no recommendation). If fewer than two same-category targets remain — including after dropping a nonexistent or odd-category one — stop and ask for a second same-category page; a one-page "comparison" is a `query` / `audit` job, not compare.
   - If the confirmed targets are not all the same category, stop and ask whether to drop the odd-category target (recommended — compare needs one shared category). There is no informal mixed-type mode, so a set that stays mixed routes out; after a drop, re-confirm at least two same-category targets remain.
   - If the request is really which-is-*correct* (which page states the truth) rather than which-is-better-*supported*, stop and route to `query` / `audit`: compare ranks on-page support and page state, never source-level truth.
   - Record each target's `status:` (`draft` / `needs-update` / `verified`). It feeds the Support row and Support strength section in Step 5 so the comparison never presents an unverified page as equal to a verified one. (Two markers appear later, distinct: `*[from draft]*` marks a value drawn from a whole-page `status: draft` target; `*[unverified]*` marks an individual pending claim carried from an otherwise-`verified` page — CLAUDE.md → Page Status / Bullet Markers.)
   - Near-duplicate targets (the table would be all-agreement with no genuine differences) are assessed after the Step 3 body read, not at this frontmatter step, which lacks the data. When Step 3 reveals near-duplication, do not manufacture contrasts: produce the comparison but lead the `Takeaway` with the near-duplication and record a `supersede` / merge candidate in `Next steps` (Step 7).

2. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/compare/compare-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Use the memory files to apply prior corrections about comparison scope, dimensions, and framing — typically: which dimensions to skip for thin pages, how to format the table, when to merge agreement and differences sections.

3. **Read target pages.**
   - Read every target page's full body first (needed for the always-present Support row and the per-type dimensions); then follow the type-specific secondary reads below. As you read, record which bullets carry an `*[unverified]*` marker, so Step 6 can confirm any such claim reproduced in a cell, `Differences`, or `Takeaway` keeps it.
   - Concept/entity pages: read their listed source pages to populate the Support row and Support strength section (always present), and to judge support strength. Capture each listed source page's own `status:` too — a `verified` target page can rest on `draft`/`needs-update` source pages, and the Support strength section must surface that (Step 5) rather than reporting the target as solidly supported. Also note which source pages two or more targets hold in common versus independently, and whether a target's multiple sources are one work — a shared base stem (`Stem-ch01` / `Stem-ch02`) or two source pages whose `file:` frontmatter resolves to the same raw — since one work is not independent corroboration whatever the raw source count.
   - Source pages: a source target is a primary source, not source-backed — its Support cell is its own `status:` (optionally with the count of concept/entity pages it supports downstream), never a "source count," and Support strength names its downstream support and status. Read its linked concept/entity pages when the comparison dimensions include "supported concept/entity pages" or contradictions.
   - Synthesis pages: read source pages behind their evidence map.

4. **Choose dimensions.** Entities use the same dimension set as concepts (their pages share the same callouts). The table always carries a `Support` row on top of the type's dimensions, for every target type — its cell is the distinct-work source count plus status per target (chapter-splits, or two pages whose `file:` resolves to one raw, counted as a single work, never a raw page count), except a source target, whose Support cell is its own status per Step 3.
   - Concepts/entities: idea, why it matters, not this, examples, disconfirming evidence, contradictions, open questions, connections. (For concepts/entities this equals the type's required callout set minus `sources`, whose support is captured in the Support strength section and the Support row.)
   - Sources: contribution, key claims, evidence, supported concept/entity pages, limitations, open questions.
   - Syntheses: question, answer, evidence, tensions, open questions.
   - These three lists are fixed, curated subsets — use them verbatim; do not re-derive them from the callout set (only the concept/entity list happens to equal required-minus-`sources`; the source and synthesis lists deliberately omit further callouts). Add a type callout as an extra dimension only when it is central to *this* comparison (e.g. `method` for a methods-focused source compare), naming it explicitly.
   - Drop a dimension from the table only when it is an empty placeholder (`None yet` / `None noted`) for every target. When it is empty for some targets but not others, fill those cells with `—`. Never invent content to fill a cell. The `Support` row is never dropped.

5. **Save the comparison** to `2-outputs/compare/compare-YYYY-MM-DD-HHMM-{slug}.md`, where `HHMM` is the 24-hour UTC obtained at save time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context gives the date but not the current minute), and `{slug}` is the kebab-case target stems joined by `-vs-` (lowercase a non-kebab source stem to ASCII, e.g. `Vaswani2017AttentionIA` → `vaswani2017attentionia`; when there are more than two targets, or the joined slug would exceed 60 characters, use the first two stems plus `-etc`). Capture the full filename stem `compare-YYYY-MM-DD-HHMM-{slug}` once here and reuse that exact string for the `Saved:` links in Step 8; the `[YYYY-MM-DD HH:MM]` timestamp that Step 8's hot bullet and log header begin with is the same captured `HHMM` reformatted to colon form (`1430` → `14:30`). Do not re-run `date` later, or the minute may differ and the links will dangle. The table has one Dimension column plus one column per target, so it scales to 2-4 value columns; add a column for each third or fourth target. The template below uses a concrete concept-vs-concept example so the saved shape is anchored on a real comparison; substitute your own targets, dimensions, and bullets when you save the file. When authoring the cells and `Takeaway`: the verdict ranks on-page support and page state, never source-level truth (never declare a page right or wrong — route a which-is-correct question to `query` / `audit`); carry every `*[from draft]*` / `*[unverified]*` marker into any cell, `Differences`, or `Takeaway` bullet that reproduces a draft-target or pending claim; and when every target is `draft` / `needs-update`, the `Takeaway`'s opening line states the whole comparison rests on unreviewed pages (mirroring brief's up-front caveat).

```markdown
---
type: compare
targets:
  - "[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]"
  - "[[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]]"
target_type: concept
date: YYYY-MM-DD
---

# Compare: Scaled Dot-Product Attention vs Multi-Head Attention

## Takeaway
- Multi-Head Attention is the more general construct; Scaled Dot-Product Attention is the primitive it runs in parallel. Read [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] first for the architecture, then [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] for the inner operation. Both rest on the same single source, so neither is independently corroborated.

## Table

| Dimension | Scaled Dot-Product Attention | Multi-Head Attention (draft) |
|---|---|---|
| Idea | Weights values by the softmax of query·key dot products, scaled by 1/√d_k | Runs several Scaled Dot-Product Attention functions in parallel over different learned projections, then concatenates |
| Why it matters | The core operation every attention block computes | Lets the model attend to several representation subspaces at once |
| Support | 1 source, verified | 1 source, draft |

## Agreement
- Both compute attention as a weighted sum of values, with the weights derived from query-key interactions.

## Differences
- Scaled Dot-Product Attention is a single attention function; Multi-Head Attention runs several of them in parallel over different learned projections and concatenates the results, so it can attend to multiple representation subspaces at once. (For 3-4 targets, name the pages each bullet separates instead of writing a single pairwise contrast.)

## Support strength
- Scaled Dot-Product Attention — verified; 1 source: [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]].
- Multi-Head Attention — draft; 1 source: [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] *[from draft]*.
- Both rest on the same single source, so neither independently corroborates the other (one source, not two distinct ones).

## Gaps
- No wiki page yet measures sample-efficiency tradeoffs between the two.

## Next steps
- None. (When a comparison surfaces a synthesis candidate, duplicate page, or contradiction, record the suggested `synthesis` / `supersede` / `audit` move here so it survives in the file.)

## Self-report
- {a specific limitation that bit the compare skill this run — a dimension it couldn't fill, a support call it couldn't make, a target mismatch it had to work around} → upgrade: {how the compare skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Schema note: `target_type` is one of `source | concept | entity | synthesis` (a source target's `target_type` is `source`, not its `paper` / `article` / `media` sub-type); list 2-4 targets in `targets:` as wikilinks, one table value column per target.

6. **Verify the comparison.** Before logging, read back the saved file and confirm:
   - `targets:` holds 2-4 entries and they all share one `target_type`.
   - Every target named in `targets:` frontmatter appears as its own column in the table.
   - The dimensions in the table match the target type's expected dimensions from Step 4, minus any dimension dropped because it was an empty placeholder for every target (concept/entity dimensions for concept/entity targets, source dimensions for source targets, etc.).
   - The `Support` row and `Support strength` section name specific source pages, not generic "well supported" claims, and mark every `draft` / `needs-update` target as such — and each such target's table column header also carries its status (e.g. `Multi-Head Attention (draft)`), so an unverified cell is never read as equal to a verified one. Where a target page is itself `verified` but rests on `draft`/`needs-update` source pages, Support strength flags that too (the page is checked, its evidence is not), so a target is not reported as solidly grounded on unverified sources.
   - Any claim reproduced from a target page that carries an `*[unverified]*` marker is carried into the comparison with that marker (a `verified` page can hold pending `*[unverified]*` bullets per `CLAUDE.md` → Page Status); a pending claim is never shown as verified in a cell, `Differences`, or `Takeaway`. Re-scan each target for the `*[unverified]*` bullets recorded in Step 3 and confirm every reproduced claim tracing to one keeps the marker; likewise a claim drawn from a `draft` / `needs-update` target and restated in `Agreement`, `Differences`, or `Takeaway` prose carries `*[from draft]*` inline — the column-header status marks the table, not the prose below it.
   - `Agreement` and `Differences` each either carry genuine bullets or explicitly state none on that axis — never a bullet padded to avoid an empty section; for 3-4 targets, an `Agreement` bullet states whether all targets share the point or only a named subset, and a `Differences` bullet names the pages it distinguishes, rather than reading as a single pairwise contrast. A genuine cross-target contradiction (one target claims X, another claims not-X) is labelled as such, distinct from a mere difference, and a verified-vs-verified contradiction between targets is recorded as an `audit` candidate in `Next steps`.
   - `Takeaway` states a source-grounded verdict (which is better-supported, where they conflict, which to read first) without claiming more than the evidence carries. The verdict ranks on-page support and page state, not source-level truth: `verified` means a page was last fact-checked against its raw, never that it is correct (`CLAUDE.md` → Known Limitations: the wiki is a synthesis layer, not the source of truth), so do not declare a page right or wrong — route a genuine which-is-correct question to `query` or `audit`. A "better-supported" or "independently corroborated" verdict requires *distinct* sources behind the targets, not a higher count of the same source or chapter-splits of one work. A target that is itself `verified` but rests on `draft` / `needs-update` source pages is not ranked "better-supported" on its own status — the verdict reconciles with the Support-strength flag (checked page, unchecked evidence). When every target is `draft` / `needs-update`, the `Takeaway`'s opening line states the whole comparison rests on unreviewed pages and any relative verdict ranks unverified evidence only.
   - Every `Takeaway`, `Agreement`, `Differences`, and `Support strength` claim is borne out by the target pages actually read (and the source pages behind the support claims) — a well-formatted verdict the pages do not support fails here. Any `Gaps` absence claim ("no wiki page yet covers X") is checked against an actual `1-wiki/` directory listing, not impression.
   - The prose carries no AI-writing tells (scanned against `a-archive/style/ai-writing-tells.md`) and uses Canadian spelling.

   Fix anything missing, then re-run these checks on the saved file before continuing to Step 7.

7. **Flag follow-ups (no wiki integration).** If the comparison surfaces a synthesis candidate, duplicate page, or contradiction worth acting on, record the suggested move in the saved file's `Next steps` section and offer it to the user in chat as a user-triggered action (e.g. "worth a `synthesis` on X", "these two look like a `supersede`/merge", "send to `audit`"). The file note survives the session; the chat offer prompts the user now.

8. **Update hot and log.** Prepend a Recent activity bullet to `1-wiki/hot.md` and a dated entry to `1-wiki/log.md`. Touch only `hot.md`'s Recent activity (and Open threads / Watchlist where relevant).

Recent activity bullet (prepend in `1-wiki/hot.md`):

```markdown
- [YYYY-MM-DD HH:MM] compare | [[1-wiki/concepts/target-a.md|target-a]] vs [[1-wiki/concepts/target-b.md|target-b]] → [[2-outputs/compare/compare-YYYY-MM-DD-HHMM-{slug}.md|compare-YYYY-MM-DD-HHMM-{slug}]]
```

Log entry (prepend in `1-wiki/log.md`):

```markdown
## [YYYY-MM-DD HH:MM] compare | {target-a} vs {target-b} (+N more)
- Saved: [[2-outputs/compare/compare-YYYY-MM-DD-HHMM-{slug}.md|compare-YYYY-MM-DD-HHMM-{slug}]]
- Targets: list every one of the 2-4 targets as a wikilink, e.g. [[1-wiki/concepts/target-a.md|target-a]], [[1-wiki/concepts/target-b.md|target-b]]
```

## Limits

- Pure output — compare never creates, modifies, or promotes wiki pages.
- Do not answer from model memory; read the actual pages.
- Compare reads wiki pages (and their listed source pages for support judgement) only; it does not reopen `0-raw/` to re-adjudicate a comparison.
- Never edit `hot.md` Active focus unless explicitly asked.
- Never modify `0-raw/`.
