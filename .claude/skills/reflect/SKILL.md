---
name: reflect
description: "Create a short compass note about the LLM knowledge base's direction, blind spots, overloaded notes, emerging clusters, and next research moves. Reads hot.md, index.md, recent log entries, and a sample of high-support, low-support, and needs-update pages. Saves to 2-outputs/reflect/. Pure output, no wiki integration. Use when the user asks what the wiki is becoming, what is missing, what to read next, or what to sit with. Also use when the user asks to step back, take stock, scan for blind spots, or which notes are overloaded, even if they do not say 'reflect'. Not for a topic-scoped orientation of existing pages (use brief), a specific research question (use query), or a structural or semantic page check (use lint or audit) — the brief boundary is scope: brief orients on one topic, reflect maps whole-wiki direction; and surfacing which notes are overloaded is a whole-wiki scan here, not the per-page fix that audit performs."
---

# reflect

Write a short compass note — a brief, sampled read of where the whole wiki is heading (its growing clusters, thin spots, and the question worth pursuing next), not a review of any single page.

## Purpose

Reflection helps notice where the note network is growing, where it is thin, and which questions are becoming important.

## When To Invoke

Use when the user asks what the wiki is becoming, what is missing, what to read next, or what questions are worth sitting with.

## When Not To Invoke

- Structural check. Use `lint`.
- Semantic page review. Use `audit`.
- Topic orientation. Use `brief`. The discriminator is scope: brief is a topic-scoped lay of the land of existing pages; reflect is a wiki-scoped compass about direction and growth.
- Specific question. Use `query`.
- Wiki too small to have direction yet (the floor) — no concept/entity page draws on more than one source (nothing is compounding yet), or fewer than 5 source pages. Say so and suggest ingesting more before reflecting; do not produce a padded note.

## Procedure

```
Reflect Progress:
- [ ] Step 1: Load orientation (hot, index, recent log, prior reflect, reflect-memory, multi-skill-memory); check the floor and decline if below it
- [ ] Step 2: Sample pages across support tiers and clusters
- [ ] Step 3: Save reflection to 2-outputs/reflect/ (save only — do not integrate)
- [ ] Step 4: Verify the note
- [ ] Step 5: Update hot and log
```

1. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, recent `1-wiki/log.md` (the most recent ~20 entries, or the last ~30 days, whichever is shorter), `.claude/skills/reflect/reflect-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Use the memory files to apply prior corrections about reflection scope and framing — typically: how many sampled pages, whether to surface needs-update pages prominently, depth of the One Question section. Also read the most recent prior note in `2-outputs/reflect/` if one exists, so this pass can name what changed since — a flagged thin sub-area that thickened, a weak spot resolved, a named contradiction still open. Compare against it; do not just re-snapshot, and ground each "what changed" claim in the objective record (a log op, a `created:` date, a status transition), never in the bare difference between this sample and the prior note's — two different draws differ by sampling churn, not only real change. Then apply the floor (When Not To Invoke) before sampling: if no concept/entity page draws on more than one source, or there are fewer than 5 source pages, decline and stop — say the wiki is too small to have a direction yet and suggest ingesting more, rather than producing a padded note.

2. **Sample pages.** Find these tiers from `index.md` (its per-page glosses cluster by topic) and a frontmatter scan of `1-wiki/sources/`, `1-wiki/concepts/`, `1-wiki/entities/`, and `1-wiki/syntheses/` for `source_count`, `status`, and `created` (these are frontmatter fields; `Contradictions` is a callout section on source/concept/entity pages and `Tensions` its synthesis-page counterpart). Scan recursively over the directories, not a `*.md` glob — `grep -rl "status: needs-update" 1-wiki/sources 1-wiki/concepts 1-wiki/entities 1-wiki/syntheses` (source pages carry `status:` too and can be `needs-update`; a bare `1-wiki/**/*.md` glob aborts under zsh `nomatch` when a dir such as `syntheses/` holds only `.gitkeep`, and sweeps in non-page top-level files). Sample, do not read every page. Default sample size by index size (the reflect-memory file overrides these): 15 pages when `index.md` lists under 40, 20 when 40–100, 25 when over 100 (a fixed 20-page sample is unrepresentative on a large wiki) — but on a wiki barely above the floor, sampling most of it beats a smaller fixed count (the Worked Example's 18 of 20 is that case), so read these as a coverage floor, not a cap. Spread the sample across non-empty tiers rather than filling it from one. A page often satisfies several tiers (a high-`source_count` page can also be `needs-update` and carry `Contradictions`); assign each sampled page to its single highest-priority matching tier and count it once, so overlapping tiers do not inflate the count — the five selection tiers below rank `needs-update` > real `Contradictions`/`Tensions` > single-source > high-`source_count` > recently-created (problem and salience tiers outrank the volume tiers), so a page that is both high-`source_count` and `needs-update` counts under `needs-update`; the last two bullets (synthesis-cluster and status) are analysis overlays applied to sampled pages, not selection tiers. Lower the confidence of direction claims when the sampled fraction is small — under roughly 20% of the index. The sample is deliberately stratified by salience (it over-weights the problem and mature tiers), so its own topic concentration is not by itself evidence of a whole-wiki skew: before naming any wiki-wide direction, compare the sample's sub-area mix against the index's actual topic spread (read in Step 1), and scope the direction to a sub-area ("this sample skews toward X") whenever the sample over-represents that sub-area relative to the index — not merely whenever more than half the sample happens to sit there.
   - High `source_count` concept/entity pages (`source_count` ≥ 3, or the top of the distribution when few reach 3 — the compounding candidates, distinct from the single-source tier below).
   - Single-source concept/entity pages.
   - `needs-update` pages.
   - Notes with real `Contradictions` or synthesis `Tensions`.
   - Pages created in roughly the last 30 days — compute the cutoff (today − 30 days) and find pages with `created:` on or after it — `grep` is a string matcher, not a date comparator, so grep every `created:` line (`grep -rh "created:" 1-wiki/sources 1-wiki/concepts 1-wiki/entities`) and filter by ISO-date string compare (ISO dates sort lexically) across `1-wiki/sources/`, `concepts/`, and `entities/` (a burst of recent concept/entity creation is itself a direction signal, not just recent sources); an exact boundary is not required.
   - Topic clusters that may deserve synthesis entry points (a synthesis page is a durable cross-source page that anchors a topic). Before naming a cluster synthesis-ready, count its distinct supporting source *works* — the union of the `sources:` lists across the cluster's concept/entity pages, not the page count (collect every source-page wikilink from those pages' `sources:` frontmatter, dedupe by stem, then collapse to one work any pages that resolve to the same raw — chapter/section splits (`{stem}-ch01`, `{stem}-ch02`) and two differently-named source pages whose `file:` frontmatter points at the same raw — matching how `synthesis` counts distinct works, so reflect never announces a cluster `/synthesis` will then decline; count distinct works; cluster membership is your judgement from the pages' shared `sources:` and reciprocal `Connections`, not gloss words alone — two pages sharing a topic word are not a cluster) — and recommend `/synthesis` only when that union is ≥ 2 distinct works. A cluster of N concept pages all citing one work (or that work's chapter-splits) does not qualify; saying so ("thick on pages, thin on sources — needs a second source first") is the correct honest outcome. When the ≥ 2 union sources are themselves `draft`/`needs-update`, note that the cluster clears the page-count floor but its evidence is unverified, rather than presenting it as solidly synthesis-ready. Reflect only names a candidate cluster and defers the actual discovery scan and page drafting to `/synthesis` — it does not itself enumerate or draft synthesis pages.
   - Note each sampled page's `status`. A draft page may be named, but characterize its claims as unverified ("draft — not yet audited") rather than as settled strength; a draft is fair game as a weak spot but not as confirmed compounding support. "Compounding" means an idea now drawing on multiple distinct, independent sources and linking out to several pages (gaining mass) — name a page as compounding only when that convergence rests on at least one non-draft page; an all-draft convergence is labelled "unverified convergence", and a high-`source_count` page that is itself `draft` carries a draft tag even when most of the sample is not draft. Apply the same discipline at the claim level: a `verified` page can carry individual `*[unverified]*` bullets (`CLAUDE.md` → Page Status), so a compounding claim resting on an `*[unverified]*` bullet is not settled support even though its page is non-draft — treat an `*[unverified]*` bullet like a draft one (fair game as a weak spot, not confirmed compounding), so "rests on at least one non-draft page" means the compounding-relevant bullet itself is not `*[unverified]*`. When most of the sample (over half the sampled pages) is draft, open Current Direction with an overall-confidence caveat ("this pass rests mostly on unverified drafts"), not only per-bullet draft tags.

3. **Save reflection** to `2-outputs/reflect/reflect-YYYY-MM-DD-HHMM.md`. Obtain the timestamp at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context provides the date but not the current minute. Capture the full `YYYY-MM-DD-HHMM` stem once and reuse the identical string for the filename, the Step 5 log entry, and the hot bullet — do not re-run `date`, or the bookkeeping links will dangle. Save only — reflect is a compass note, not a wiki edit; promotion to concept/entity/synthesis pages is a separate, user-approved step. Mention potential follow-up operations at the bottom of the note if useful.

```markdown
---
type: reflect
date: YYYY-MM-DD
sample_size: {N pages sampled}
---

# Reflect - YYYY-MM-DD-HHMM

## Current Direction
- Sampled {N} of {total in index.md} pages; every section below reports what this sample shows, not a whole-wiki census — read "compounding" and "weak" as sample-scoped.
- What the wiki is increasingly about.
- (If a prior reflect exists) What changed since the last reflect.

## What Is Compounding
- Ideas with multiple sources and useful connections.

## Weak Spots
- Thin, overloaded, duplicate, or unsupported notes.

## One Question Worth Sitting With
- A question that could organize the next round of reading.

## Suggested Next Moves
- The smallest honest set of concrete moves.
- Candidate synthesis pages only for clusters whose union of sources is ≥ 2 distinct works (chapter-splits and same-raw pages collapsed, per Step 2); otherwise name the missing-source gap instead.

## Self-report
- {a specific limitation that bit reflect this run — a blind spot in the sample, a signal it couldn't read, a call it couldn't make} → upgrade: {how the reflect skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Write each section only where the sample genuinely supports it. Just past the floor, Current Direction and What Is Compounding may honestly be thin — "too early to call a direction; one page is starting to compound" is the correct content, not a manufactured trend. A healthy wiki legitimately has few or no Weak Spots — write "- None notable this pass" rather than inventing one; skip the One Question if no real organizing question emerged rather than manufacturing a profound-sounding one. Keep Suggested Next Moves to the smallest honest set, never padded to a quota.

4. **Verify the note.** Confirm the file exists at the expected path and every wikilink resolves to a real page file under `1-wiki/` — fix or drop danglers (a stale `index.md` entry is not proof a page exists). Confirm every direction, compounding, weak-spot, and One-Question claim names at least one page actually in the sample, and that the named page genuinely carries the claim attributed to it, confirmed against the page's body, not the `index.md` gloss that seeded it (re-reading the draft against itself is not verification). A direction, cluster, or trend bullet needs the Limits floor met — 2–3 sampled pages with independent sources actually converging on it, not a single on-topic page — and any "increasingly"/"growing" claim is grounded in the objective record (`created:` dates or the Step 1 log read), never asserted from a static snapshot, since no single page carries "increasingly". "Where load-bearing" is not an exemption — an unnamed trend bullet is invented and must be cut, not downgraded to `*\[tentative\]*` (tentative is for thin support from a real sampled page, not for laundering an out-of-sample claim). Confirm Canadian spelling, no AI-writing tells (scanned against `a-archive/style/ai-writing-tells.md`), and the note is under about 400 words.

5. **Update hot and log.** Only Recent activity, Open threads, or Watchlist may be touched; Active focus is user-owned.

   Log entry (prepend to `log.md`):

```markdown
## [YYYY-MM-DD HH:MM] reflect | {one-line summary}
- Saved: [[2-outputs/reflect/reflect-YYYY-MM-DD-HHMM.md|reflect-YYYY-MM-DD-HHMM]]
- Sampled: {N} pages
```

   Hot Recent activity bullet (prepend in `hot.md`):

```markdown
- [YYYY-MM-DD HH:MM] reflect | wiki direction → [[2-outputs/reflect/reflect-YYYY-MM-DD-HHMM.md|reflect-YYYY-MM-DD-HHMM]]
```

## Worked Example

This example assumes a moderately built wiki (14 concept/entity pages, 5 sources, 1 synthesis — 20 pages). With a wiki just past the floor in When Not To Invoke, reflect is shorter and the **Suggested Next Moves** are mostly "ingest more" — that's the correct outcome, not a sign reflect was premature. Below the floor, decline rather than padding.

```markdown
---
type: reflect
date: 2026-05-08
sample_size: 18
---

# Reflect - 2026-05-08-1430

## Current Direction
- Sampled 18 of 20 pages; the claims below are what this sample suggests, not settled fact.
- The wiki is consolidating around one main topic, with two sub-threads recurring.
- Coverage is thickening on the main sub-area; a neighbouring sub-area is still thin.

## What Is Compounding
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] now has three independent sources and connects out to four other concept pages.
- [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] is the strongest entry point — most ingested papers eventually link to it.

## Weak Spots
- Five single-source concept pages on one narrow sub-topic. Need a second source or a merge with [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]].
- [[1-wiki/concepts/positional-encoding.md|Positional encoding]] is `needs-update` after a contradicting source landed last week and hasn't been revisited.
- No synthesis page yet for the main cluster, even though six concept pages converge on it.

## One Question Worth Sitting With
- The positional-encoding contradiction pits learned against fixed encodings — which does the corpus actually favour, and on what evidence?

## Suggested Next Moves
- Ingest a follow-up paper on receiver-side filtering to thicken support.
- Run `/synthesis` on the main cluster — its six concept pages cite three distinct source works (union of their `sources:` lists, distinct from the five single-source sub-topic pages above), clearing the ≥ 2 floor to anchor a topic entry point.
- Resolve the [[1-wiki/concepts/positional-encoding.md|positional encoding]] contradiction before it propagates further into syntheses.
```

## Limits

- Name a direction, cluster, or trend only when 2–3 pages with independent sources actually converge on it; two pages sharing a word are not a cluster.
- Do not answer from model memory; reflect interprets only sampled pages (Step 4 enforces tracing every claim to a named sampled page and cutting out-of-sample trends).
- Never edit `hot.md` Active focus unless explicitly asked.
- Never modify `0-raw/`.
