---
name: synthesis
description: "Create or update durable synthesis pages as topic entry points in 1-wiki/syntheses/. Use when the user asks to synthesize a topic, promote a query/brief/reflect result, find missing synthesis pages, or scan the wiki for topics that have enough support to become synthesis pages. Also use when the user asks to consolidate concept/entity pages into a topic page, turn a debate or open thread into a durable entry point, or merge overlapping syntheses. Not for first contact with a raw source (use ingest), a one-shot answer to a single question (use query), a broad read-only orientation (use brief), a side-by-side of 2-4 named pages (use compare), or a semantic quality review (use audit)."
---

# synthesis

Create or update synthesis pages as entry points into developed topics.

## Purpose

Synthesis turns clusters of supported wiki pages into durable entry points. It is not an automatic topic dump: it proposes candidate synthesis pages, then writes only approved pages or updates.

## Conventions (Recap From CLAUDE.md)

- A synthesis page needs at least two distinct sources. Distinct means distinct underlying works: chapter/section-split source pages sharing a base stem (`X-ch01` / `X-ch02`) are one work, and two source pages whose `file:` resolves to the same raw are one work — collapse them before counting. Two chapters of one book do not clear the floor. Exactly one source is allowed only as a deliberate stub (`single_source_stub: true`); see Step 6.
- Synthesis page filenames are kebab-case lowercase: `1-wiki/syntheses/{kebab-case-slug}.md`.
- Every wikilink is path-qualified from the repo root, includes `.md`, and uses a pipe-rendered display name. Example: `[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]`. Authors: `[[1-wiki/entities/ashish-vaswani.md|Ashish Vaswani]]`. The pipe-rendered display is required on every wikilink; attachment embeds `![[...]]` take the path but no pipe.
- No bold and no italic in the wiki body. LaTeX math and the bullet markers `*\[unverified\]*` / `*\[tentative\]*` / `*\[disputed — see Contradictions\]*` are the only structural exceptions. Inline backticks for paths and code are fine.
- Use `AskUserQuestion` for every user-facing decision: one decision per call, never batched, and each question marks its recommended option `(Recommended)` and orders it first (or states plainly that there is no lean) (CLAUDE.md → Workflow Rules). Step 5 enumerates which decisions.

## When To Invoke

Use when the user asks to:

- create or update a synthesis page.
- turn a topic, question, query, brief, or reflection into a durable entry point.
- scan the wiki for missing synthesis pages.
- identify topics that have enough support to synthesize.

## When Not To Invoke

- First contact with a raw source. Use `ingest` (deep mode for foundational sources).
- A quick answer to a question. Use `query`.
- A broad read-only orientation. Use `brief`.
- A side-by-side of 2-4 named same-type pages. Use `compare`.
- A semantic quality review. Use `audit`.

## Procedure

```text
Synthesis Progress:
- [ ] Step 1: Load hot.md and index.md
- [ ] Step 2: Choose focused or discovery mode
- [ ] Step 3: Find candidate topic clusters
- [ ] Step 4: Read relevant pages
- [ ] Step 5: Propose synthesis plan
- [ ] Step 6: Draft approved synthesis page changes
- [ ] Step 7: Apply approved wiki edits
- [ ] Step 8: Read back the synthesis and verify
- [ ] Step 9: Update hot.md (index entry is written in Step 7)
- [ ] Step 10: Write synthesis report and prepend log.md entry
```

1. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/synthesis/synthesis-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Note existing synthesis pages so you update entry points instead of duplicating them. Use both memory files to apply prior corrections about scope, framing, and source-supportedness before drafting any synthesis content; both files may be empty, in which case the procedure below applies unchanged.

2. **Choose mode.**
   - **Focused mode:** If the user gives a topic, question, page, cluster, or output file, restrict discovery to that topic and its one- to two-hop connections.
   - **Discovery mode:** If no topic is given, scan all index sections and `hot.md` (Recent activity, Open threads), existing syntheses, and high-support or connected concept/entity pages for candidate topics.

3. **Find candidate topic clusters.**
   Look for:
   - multiple concept/entity pages connected by shared sources, reciprocal links, or repeated terms.
   - two or more source pages supporting the same question, method, debate, system, or phenomenon.
   - hot/open threads that already name a tension, gap, or repeated topic.
   - query, brief, compare, or reflect outputs that point to a reusable cross-source answer.
   - concept/entity pages with enough connections to serve as a topic entry point but no matching synthesis.

   Mechanically: read `1-wiki/index.md` to enumerate the concept/entity/synthesis pages; for shared-source clusters, read each `1-wiki/concepts/*.md` and `1-wiki/entities/*.md` page's `sources:` frontmatter block and group pages that share source pages, keeping a group only where two or more pages cite two or more of the same source pages; for reciprocal-link clusters, follow `Connections` wikilinks; cross-check `hot.md` Open threads for already-named tensions. Before proposing a candidate, cross-check its source set and question against every existing synthesis's `sources:` and `Question` — a candidate is a duplicate if it shares at least half its `sources:` with an existing synthesis, or targets the same topic/question as one (even when worded differently or resting on a mostly-new source set); route it to update/merge (Step 5 item 2 / 2a), not a new page. Run this cross-check in focused mode too, so a differently-named existing entry point routes to an update rather than a second page on the same question.

   A candidate is strong when it carries a reusable topic or question (not just a keyword) plus a tension, pattern, debate, or answer that helps the user re-enter the topic later — a bare keyword cluster is not enough. Skip candidates that are only one source, unless the user explicitly asks for a single-source stub.

4. **Read relevant pages.**
   - Read the candidate concept/entity pages first.
   - Read existing syntheses that overlap.
   - Read supporting source pages for evidence and tensions.
   - For each supporting source, note its position on the synthesis question explicitly, then diff the positions. A disagreement between sources goes in `Tensions` even when the cleaner framing is a consensus — do not smooth it away (CLAUDE.md → Known Limitations: smooth prose hides disagreement). Record each source's position and the disagreements among them in the Step 5 context post, so the Step 8 Tensions check has a concrete list to verify against rather than re-deriving from memory — that check can only confirm a disagreement surfaced here.
   - When `origin:` (the frontmatter field recording where the page was promoted from, set in Step 7) is a promoted `2-outputs/` artifact (query/brief/reflect/compare), do not carry its claims forward verbatim — re-derive the answer against the current wiki pages and re-trace each load-bearing claim to its source page, since the artifact is a frozen snapshot whose supports may since have been superseded, forgotten, or flipped to `needs-update`. Promote what the wiki supports now, not what the artifact asserted then.
   - Reopen raw sources if a source page is too thin, the synthesis is high-stakes, or two source pages disagree on the synthesis question — in the disagreement case, confirm the tension is genuine and not an extraction artifact in one page (CLAUDE.md → Known Limitations: a source page can be wrong if its extraction was wrong) before writing it into `Tensions`.
   - Note the `status:` of each supporting page, and treat an `*[unverified]*` claim on an otherwise-`verified` page as draft content (CLAUDE.md → Page Status: verification is claim-level). Drafts are unreviewed (CLAUDE.md draft-exclusion rule), and a synthesis becomes a durable entry point, so it is higher-stakes than a transient query. Two triggers fire the isolated draft-grounding question (Step 5 item 6): more than half the supporting pages are `status: draft` (the "mostly drafts" threshold everywhere it recurs below), or any load-bearing `Answer` clause rests solely on a `draft` or `*[unverified]*` support — a single load-bearing draft counts even when the overall page fraction is under half. Surface whichever trigger fires in the Step 5 context post.

5. **Propose the synthesis plan before writing, then ask every decision via `AskUserQuestion`.** Post a single chat context message first so the user sees the picture, then fire one `AskUserQuestion` per decision (one decision per call, see Conventions).

   Context post (chat text, no questions yet):
   - Candidate title and reusable question.
   - Whether this creates a new synthesis or updates an existing one.
   - Likely answer shape, tensions, and open questions.
   - Why the page would be a useful topic entry point.
   - Support maturity: which supporting pages are verified vs. draft.
   - Each source's position on the question and the disagreements among them (from Step 4; this is the concrete list the Step 8 Tensions check verifies against).
   - The decision slate: name the questions about to fire — candidate(s), create/update, any merge, the supporting page(s), scope — and invite the user to pre-empt any in chat now ("include all the concept pages, only ask me about scope"), skipping those prompts. Naming all pending questions up front, before firing them one at a time, keeps one-decision-per-call intact while letting the user collapse the obvious ones. In discovery mode, present candidates as a ranked shortlist and pursue the top ~3 this run, deferring the rest to Open threads.

   Then the questions (one `AskUserQuestion` call each):
   1. In discovery mode: one question per candidate, e.g., "Draft synthesis on `{topic}`?" Options: draft (Recommended) / skip / other — a candidate surfaced by Step 3 is one the scan already judged worth drafting.
   2. In focused mode: one question on creating-or-updating, e.g., "Create new synthesis for `{topic}`?" or "Update existing synthesis `{slug}`?" Options: create / update existing / skip / other — order the option the Step 3 cross-check indicates first and mark it `(Recommended)`: update when a matching synthesis exists, create when none does.
   2a. When two existing syntheses overlap, one question on the merge, e.g., "Merge `{slug-a}` and `{slug-b}` into a single synthesis?" Options: merge into A / merge into B / keep separate / other — order the stronger-survivor option first and mark it `(Recommended)` (stronger = the `verified` page, else the higher `source_count`, else ask). On a keep-separate answer, cross-link the two syntheses in each other's `Connections` and stop. On a merge answer, invoke the `supersede` skill on the merge (do not absorb-then-delete inline) and let it run its full Merge procedure; supersede owns the mechanics — survivor kept, absorbed content moved in and preserved under `2-outputs/supersede/preserve/`, inbound `1-wiki/` wikilinks re-pointed at the survivor, absorbed page deleted. When it returns, resume at Step 6 to finish what supersede does not own:
      - Distinct-works `source_count`: supersede syncs the survivor's `source_count` to its merged `sources:` list, but it counts list entries, not distinct works. Re-derive `source_count` as the count of distinct works in that union (see Conventions), then subtract any source dropped in items 3-4 of this run, which supersede did not see.
      - Two-source floor: if that distinct-works count lands at one, fire the single_source_stub drop-to-one question (Step 6) before writing — the merge path is not exempt.
      - Survivor status: supersede keeps a `verified` survivor `verified` with the moved-in claims marked `*[unverified]*` (it demotes to `draft` only on a whole-page replacement, not a merge). So if your own Step 6 edits then change unmarked verified content — dropping an Evidence-map line, dropping a source — demote the survivor to `draft` and strip `verified_hash:` yourself, since Step 8's scoped lint does not re-check the hash.
      - Evidence map: keep only the Evidence-map lines (the `Evidence`-callout lines tying a source to the `Answer` clause it backs) whose source still maps to a claim the merged `Answer` makes; drop a mapping whose claim is gone, but the source stays in `sources:` if it still backs the page (an Evidence-map line and `sources:` membership are separate).
      - Frozen danglers: a `2-outputs/` artifact that links the absorbed page (a query or brief the page was promoted from) becomes a frozen dangler — `2-outputs/` snapshots are not repaired, so leave it as is.

      Use `forget` instead of a merge only if the user wants the overlapping page removed outright with no preserved view.
   3. One question per supporting concept/entity page, e.g., "Include `[[1-wiki/concepts/page.md|page]]` as supporting?" Options: include (Recommended) / drop / other — a page already in the candidate cluster is normally wanted.
   4. One question presenting the full inherited source set (the sources behind the approved supporting pages), e.g., "Include all {N} as `sources:` / Evidence, or let me drop some?" Options: include all (Recommended) / let me pick / other. Gate individually only the sources the user chooses to review — a source backing an approved concept page is almost always wanted, so per-source yes-prompts mostly train rubber-stamping. Dropping a source still has real downstream effect (source_count, the two-source floor), so the drop option stays.
   5. One question on scope qualification, e.g., "Restrict scope to `{X}`?" Options: yes / no / other — no fixed lean here; whether to restrict scope depends on the topic, so state that you have no recommendation rather than marking one.
   6. When the supporting pages are mostly `status: draft`: one isolated question, e.g., "This synthesis would rest on {N} unverified draft pages — drafts may be wrong and this becomes a re-cited entry point. Proceed, or audit the supports first?" Options: audit supports first (Recommended) / proceed on drafts / skip / other. This makes the draft-grounding warning a selectable branch, not a prose aside in the context post.

   Example focused-mode context post:

   ```markdown
   - Title: Attention vs Recurrence
   - Question: When does self-attention beat recurrence for sequence transduction?
   - Mode: new synthesis
   - Why entry point: multiple sources converge on the long-range-dependency question and the self-attention and recurrence concept pages currently overlap on it.
   - Likely answer shape: self-attention wins when the sequence is shorter than the representation dimension and parallelism matters; recurrence can still pay off for very long sequences.
   - Likely tension to surface: the sources disagree on whether constant-path self-attention captures long-range dependencies better than sequential recurrence.
   ```

   Then the per-decision `AskUserQuestion` calls follow. Only approved items become part of the synthesis page.

6. **Draft approved synthesis page changes.**
   - New page path: `1-wiki/syntheses/{kebab-case-slug}.md` (kebab-case lowercase per `CLAUDE.md`).
   - Existing page: preserve `created:` and update only the approved sections.
   - Use the synthesis template from `CLAUDE.md` → `## Synthesis Pages` (the frontmatter shape and the nine required callouts in order). Each callout ends with its block ID — the kebab-case of its display title — as the last line inside the `>` block (`> ^question`, `> ^answer`, …). The one divergence to watch: the abbreviated `[!what-would-change-this]` type spells its block ID out to the full title, `> ^what-would-change-this-answer` (see `CLAUDE.md` → Callout Block IDs).
   - When the synthesis cites a specific section of a source or concept/entity page, link the callout block ID: `[[path#^block-id|Display]]` (e.g. `#^evidence`, `#^appraisal`, `#^disconfirming-evidence`). Obsidian does not anchor to callout titles, so `[[page#Section Title]]` will not resolve.
   - A page/section/figure citation uses the two-form canonical citation (`CLAUDE.md` → Source Support And Verification): the source-page wikilink names which source, paired with a `#page=N` raw-file deep-link whose display carries both a structural anchor and the page (`sec. 3.2, p. 5`, `fig. 2, p. 6`). Form 1 (attributive): `[[1-wiki/sources/X.md|X]] ([[0-raw/papers/X.pdf#page=5|sec. 3.2, p. 5]]) shows …`. Form 2 (parenthetical): `… claim ([[1-wiki/sources/X.md|X]]; [[0-raw/papers/X.pdf#page=5|sec. 3.2, p. 5]]).`. N is the physical PDF page, found by opening the PDF — proceedings/article pagination differs from physical, so compute `N = printed − (first_printed − 1)` (read the printed number on the PDF's first physical page; do not guess the offset from the cited range, which may not start at the paper's first page). A general attribution without a locator, and a reference to a wiki page's own callout (`#^appraisal`), stay bare source-page links.
   - `single_source_stub:` flag: when the user explicitly asks for a single-source synthesis stub, set `single_source_stub: true` in the frontmatter. Lint warns on synthesis pages with `source_count: 1` that lack the flag; the flag tells lint the 1-source state is deliberate. Omit the field entirely on multi-source (≥2-source) syntheses; set it (`true`) only on a deliberate single-source stub (CLAUDE.md → Synthesis Pages). If any write path — an item-4 source drop, or a merge whose deduped distinct-works union collapses to one — leaves exactly one distinct work, that violates the two-source rule: surface an `AskUserQuestion` to set `single_source_stub: true`, keep the dropped source, or hand the removal to `forget`/`supersede`; do not write back a lint-failing single-source synthesis. The drop-to-one guard fires on every path that lands at one source, not only the item-4 drop.
   - Fill each of the nine callouts per the CLAUDE.md descriptions, leaving honest `> - None yet` placeholders where a section has nothing genuine to say. Hold the synthesis-specific distinctions rather than re-deriving the whole template: `Evidence` maps source pages to the parts of `Answer` they support (not a generic source dump); `Scope` states where the answer applies and where it does not, keeping the aggregated claim honest; `Tensions` preserves present-tense disagreement and the user's own disconfirming evidence (concept/entity pages have a separate `Disconfirming Evidence` callout — syntheses fold both into `Tensions`); `What Would Change This Answer` is future evidence that would revise it, distinct from `Tensions`.
   - Non-obvious factual claims in `Answer`, `Scope`, and `Tensions` carry an inline citation to the specific source they draw from, in one of the two canonical forms (the source-page wikilink paired with the located raw deep-link; see the citation note above and CLAUDE.md → Source Support And Verification), and each is faithful to that source. Obvious or definitional bullets and the user's own marked judgement need none; a cross-source generalization in `Answer` cites each source it rests on and keeps its scope within the union of those sources — citing each source is necessary but not sufficient, since a claim faithful to every source severally can still over-generalize their composition, which is exactly where over-generalization hides.
   - `Connections` should link related synthesis pages where they exist (`[[1-wiki/syntheses/other-topic.md|Other Topic]]`), not only concept/entity pages — syntheses are topic entry points, and cross-linking them is how a reader navigates between developed topics.
   - Length: keep the page under the 600-word soft cap (CLAUDE.md → Length) — a synthesis over 600 words is usually doing topic-dump work that belongs in the underlying concept/entity pages. Review any single bullet over ~35 words.
   - New and updated synthesis pages stay `status: draft`; the Step 8 verification is a safety pass, not a status promotion to `verified` — only a later `audit` sets `verified` (per `verification.md`, verification never sets `verified`; audit is the independent second layer). Editing a `verified` synthesis is claim-level for additions (CLAUDE.md → Page Status): mark each newly-added non-obvious claim `*[unverified]*` and the page stays `verified` with that added claim as the pending delta; a change to an existing claim moves the hash and resets the page to `draft` (marking does not hold it `verified`).
   - No bold and no italic in the page body. For technical terms the page introduces (jargon a reader might not recognize), wikilink inline in pipe-rendered form with a short gloss: `the [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] — runs several attention functions in parallel over different learned projections of queries, keys, and values`, or embed the gloss in the sentence. Subsequent uses on the same page need no gloss.

7. **Apply only approved substantive edits.** Mechanical fields do not need separate approval:
   - `created:` for new pages.
   - `updated:` for touched pages.
   - `source_count:` to match `sources:`.
   - `origin:` — when the synthesis was promoted from a specific `2-outputs/` artifact (a query/brief/reflect/compare file), set it to a path-qualified pipe-rendered wikilink to that file, e.g. `origin: "[[2-outputs/query/query-2026-06-05-1430-attention.md|query-2026-06-05-1430-attention]]"`. When there is no single originating file, use a bare token: `direct` (user named the topic) or `synthesis-scan` (discovery mode). On an update to an existing synthesis, preserve the existing `origin:` as-is — it records where the page first came from, not this run. Lint requires `origin:` present but does not validate its form, so the link must be right at authoring time.
   - `1-wiki/index.md` entry for new synthesis pages.

8. **Verify against the raw sources, then read back before touching the log.** Synthesis pages are durable cross-source argument pages, so they get the same verification the ingest family runs, not a lighter self-check: run the two packets in the shared `.claude/skills/multi-skill/references/verification.md` (Source-Faithfulness + Note-Quality and Coverage) — their independence supplied by the tiered independent-refuter model (`verification.md` → Tiered Independent-Refuter Verification), run at the draft tier here; the full Tier-3 quorum that earns `verified` runs later at `audit` — over the synthesis page and the raw sources its `Answer` draws on, reading the source-page-specific bullets as their synthesis analogues (the `Answer` / `Scope` / `Tensions` claims in place of a source page's TL;DR and Key Claims). Re-derive each load-bearing claim from the raw — not from the source page or the drafted answer — including at least one late-section detail as proof the raw was re-read this pass, and spot-check at least one `#page=N` deep-link per distinct raw. Both packets must come back clean in the same round; a fix re-runs both. The page then stays `status: draft` for a later `audit` to re-check independently against the raw — the two-layer model (synthesis self-validates here; audit validates again). Record the two packet results (per-packet late-section detail, the `#page=N` spot-check, any fixes) in the Step 10 log entry. Beyond the shared packets, confirm the synthesis-specific points they do not cover:
   - Every supporting source page listed in `sources:` actually appears in `Sources` and was named in `Evidence`.
   - `source_count` matches the count of distinct works in `sources:` (collapse `X-ch01`/`X-ch02` splits and same-`file:` duplicates per Conventions), and that count is at least 2 (or `single_source_stub: true`). Lint's `synthesis_under_supported` only counts `len(sources)`, so collapsing to distinct works is the skill's job at create time, not only on a merge.
   - `Tensions` preserves disagreements rather than blending them, in both directions and checked against the source positions recorded in the Step 5 context post (not from memory): every source-vs-source disagreement noted in the Step 4 position-diff appears in `Tensions`, and any source that disagrees with the `Answer` is named.
   - `Connections` wikilinks resolve.
   - `Evidence` maps source pages to specific parts of `Answer` rather than dumping a generic source list: every load-bearing `Answer` clause has at least one `Evidence` line naming the clause it supports and its source + locator, and no `Evidence` line floats free of a claim the `Answer` actually makes. (Lint does not detect a dump; this is a manual read.)
   - Composition fidelity (synthesis-specific, beyond the packet's per-claim faithfulness check): for a claim in `Answer` citing more than one source, confirm its generalized scope does not exceed what the cited sources jointly (their union) support — a claim the packet finds faithful to each source severally can still over-reach the composition, and catching that is synthesis's signature check, since it composes a new argument that can drift even when every input page is faithful.
   - `Scope` bounds the `Answer`: a sweeping or unrestricted `Answer` clause carries a genuine `Scope` line qualifying where it holds, not a `> - None yet` placeholder — the aggregate-honesty counterpart to the union rule in the drafting step.
   - For new pages: `created:` is set; for updated pages: `created:` is preserved and `updated:` is touched.
   - Run `check_wiki.py` (which prints a JSON array of finding objects, each with `check_id`, `severity`, and `file`) and filter to the touched page by parsing the JSON rather than line-grepping (a `grep -B1` recipe catches `check_id` only by field-ordering luck and drops `severity`): `python3 .claude/skills/lint/scripts/check_wiki.py "1-wiki" | python3 -c "import json,sys; [print(o['severity'], o['check_id']) for o in json.load(sys.stdin) if o['file']=='1-wiki/syntheses/{slug}.md']"`. Confirm that page has zero `embed_unresolved`, `zero_source_page`, `synthesis_under_supported`, `source_count_mismatch`, `source_link_unresolved`, or `section_order` findings. An empty result means zero findings only if the page is scanned at all — a freshly written page absent from the whole-tree output was not seen (re-run after confirming the file is on disk), which is not the same as clean. (The script reports the whole tree, so scope to the touched page rather than diffing against a baseline you never captured.)

   Fix anything that doesn't pass before continuing. If a check would require approval beyond the synthesis scope, stop and surface it.

9. **Update `1-wiki/hot.md`.** Capture the timestamp first with `TZ='UTC' date '+%Y-%m-%d-%H%M'` (24-hour UTC — the session gives the date but not the current minute, and a bare `date` records the runner's local time); reuse the one captured stamp for the hot line here and the log heading in Step 10.
   - Prepend Recent activity: `- [YYYY-MM-DD HH:MM] synthesis | {topic}`.
   - Add remaining high-value synthesis candidates to Open threads.
   - Never edit Active focus unless explicitly asked; it is user-owned and the agent's edits there feel intrusive.

10. **Write the synthesis report, then prepend `1-wiki/log.md`.** First save the operation report to `2-outputs/synthesis/synthesis-YYYY-MM-DD-HHMM-{topic}.md` (create the folder if needed; timestamp from `TZ='UTC' date '+%Y-%m-%d-%H%M'`, the same stamp as the log heading; `{topic}` is a short kebab slug of the topic). The report carries the operation summary and the `## Self-report` section (per `.claude/skills/multi-skill/references/self-report.md`); the log entry then links it. Report shape:

```markdown
---
kind: synthesis
date: YYYY-MM-DD
topic: {topic}
---
# Synthesis: {topic}

- Created: [[1-wiki/syntheses/new-synthesis.md|new synthesis]] (or "none")
- Updated: [[1-wiki/syntheses/existing-synthesis.md|existing synthesis]] (or "none")
- Candidates considered: {N}
- Verification: both packets clean (late-section detail re-read: {…}; #page=N spot-check: {physical page N + printed page seen, or n/a}; fixes: {…or none}) — page left `status: draft` for audit.
- Notable: {why this topic is now a useful entry point}

## Self-report
- {a specific limitation that bit synthesis this run — a topic it couldn't scope, a cross-source tension it flattened, a candidate it had to stop at} → upgrade: {how the synthesis skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Then prepend the `log.md` entry, which links the report:

```markdown
## [YYYY-MM-DD HH:MM] synthesis | {topic}
- Report: [[2-outputs/synthesis/synthesis-YYYY-MM-DD-HHMM-{topic}.md|synthesis-YYYY-MM-DD-HHMM-{topic}]]
- Created: [[1-wiki/syntheses/new-synthesis.md|new synthesis]] (or "none")
- Updated: [[1-wiki/syntheses/existing-synthesis.md|existing synthesis]] (or "none")
- Candidates considered: {N}
- Verification: both packets clean (late-section detail re-read: {…}; #page=N spot-check: {physical page N + printed page seen, or n/a}; fixes: {…or none}) — page left `status: draft` for audit.
- Notable: {why this topic is now a useful entry point}
```

## Edge Cases

- No strong candidates: save no page. Report the best near-candidates and what source or concept/entity support is missing.
- Existing synthesis overlaps: update the existing page, or propose a merge (Step 5 item 2a) instead of creating a duplicate.
- Topic is too broad: split into 2-3 candidate questions and ask which one to pursue.
- Topic is too thin: recommend `ingest`, `query`, or `brief` before synthesis.
- Existing synthesis already stale on read: when update or discovery mode opens an existing synthesis, check it against the current state of its supports — a listed source now `needs-update` or superseded and disagreeing with the `Answer`, or a `Connections`/`Evidence` link that now dangles. `forget`/`supersede` own the source-set cascade on a removal event (see Limits), but they do not catch rot this run is the first to see. Surface the staleness and offer to fix it in this run (re-derive the affected part, re-point or drop the dangling link) rather than silently re-saving a stale entry point.
- Support is mostly drafts (the threshold and rationale are at Step 4; the branching question is Step 5 item 6): recommend `audit` on the supports first, or proceed only on explicit user acceptance.

## Limits

- Do not create or update synthesis pages without approval.
- Do not create synthesis pages from model memory — synthesis must be source-grounded, and unsupported claims undermine the wiki's audit trail.
- Do not make syntheses exhaustive topic dumps.
- Keeping an existing synthesis's `sources:` / `source_count` in sync when a supporting source is later removed is owned by `forget` and `supersede` (which cascade into synthesis pages and guard the drop-to-one-source case), not by this skill — synthesis manages the source set only at create / update / merge time.
- Never modify `0-raw/`.
