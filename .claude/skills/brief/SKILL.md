---
name: brief
description: Create a one-shot topical orientation brief from the LLM knowledge base. Reads hot.md, index.md, relevant concept/entity pages, syntheses, and source pages as needed; saves to 2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md. Use when the user wants a broad lay-of-the-land note rather than a specific research answer. Also use when the user asks for an overview, the lay of the land, "orient me on X", "catch me up on X", "bring me up to speed on X", "state of the wiki on X", "where are we on X", or a topic primer. Not for a specific research question (use query), a side-by-side of 2-4 named pages (use compare), or whole-wiki direction and blind spots (use reflect). Output only — no new or modified concept/entity/synthesis pages; hot.md and log.md bookkeeping is expected.
---

# brief

Create a short brief.

## Purpose

A brief helps the user see the current state of a topic without promoting new wiki content.

## When To Invoke

Use when the user asks for broad orientation on a topic: "lay of the land on X," "orient me on X," "catch me up on X," "state of the wiki on X," "give me an overview of X," "an X primer." Keep this set in sync with the frontmatter description's phrasings.

Pick `brief` over `query` when the user wants the lay of the land across a topic, not an answer to one question; if there is a single answerable question, use `query`.

## When Not To Invoke

- Specific research question. Use `query`.
- Side-by-side comparison. Use `compare`.
- Source ingestion. Use `ingest`.
- Whole-wiki direction, blind spots, or what to read next across the wiki (not one topic). Use `reflect`. The discriminator is scope: brief is a topic-scoped lay of the land of existing pages; reflect is a wiki-scoped compass about direction and growth.
- No wiki page bears on the topic at all (draft or not) — the only decline case. See the Step 2 coverage gate for the canonical rule (thin-but-present coverage still produces a brief under the unverified framing).

## Procedure

```text
Brief Progress:
- [ ] Step 1: Load orientation (hot.md, index.md, brief-memory.md, multi-skill-memory.md)
- [ ] Step 2: Read relevant concept/entity, synthesis, source pages
- [ ] Step 3: Save the brief at 2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md (output only)
- [ ] Step 4: Verify file, sections, wikilinks, claims trace to pages read, Canadian spelling, AI-writing tells, word target
- [ ] Step 5: Bookkeeping — update hot.md and log.md
```

1. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/brief/brief-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Use the memory files to apply prior corrections about scope and framing — typically: which page types to include by default, how aggressively to mention drafts, target word count for the brief.

2. **Read relevant pages.** Identify candidate pages first: search `index.md` and page titles for the topic and its aliases, then follow `Connections` and `Sources` wikilinks one hop out from each hit, so an adjacent page a keyword match misses is still caught. Start with concept/entity and synthesis pages. (A page's support level is its `source_count` frontmatter — 1 is single-source/tentative, ≥2 is multi-source. `source_count` is a count, not a verification guarantee: a `verified` concept page can still rest on `draft` source pages, so "solid multi-source support" requires both ≥2 sources *and* those source pages non-draft — when the supporting source pages are themselves draft/`needs-update`, report it as "multi-source but unverified" rather than solid.) Read source pages when evidence or source context matters. The source page is normally sufficient for an orientation brief; open the raw source only when a support-level claim the brief must state (e.g. whether a claim is single-source) has no locator or evidence on the source page — a routine brief notes the thin support instead of reopening raw.

   **Exclude `status: draft` pages by default.** Drafts are unreviewed; their claims have not been verified. Include them only when the user explicitly asks or when no non-draft page covers the topic. When a draft is the only coverage, surface it under a "Drafts (unverified)" sub-bullet, or mark the individual bullet `*[from draft]*` inline (the marker `query` and `compare` use), so the reader knows the support level. If the entire topic is covered only by drafts, still produce the brief but state up front that all support is unverified: the TL;DR's opening bullet itself carries the unverified caveat (do not defer it to a lower section), and Suggested reading flags any draft target — do not present it as settled state of the wiki, and do not silently decline.

   **Apply the same discipline at the claim level.** Verification is claim-level, not all-or-nothing for the page (`CLAUDE.md` → Page Status), so a `verified` page may still carry individual bullets marked `*[unverified]*` — the pending delta from edits made since its last fact-check. A `verified` status does not guarantee every bullet is checked: check the specific bullets you draw on for the `*[unverified]*` marker. Treat an `*[unverified]*` claim like draft content — exclude it by default, even on an otherwise-`verified` page. Include it only when it is the only coverage of a sub-topic the brief must state; then surface it separately and flagged (carry the `*[unverified]*` marker through, or place it under the "Drafts (unverified)" framing) so the reader knows it is not yet fact-checked.

   **Treat `needs-update` pages like drafts.** A page marked `status: needs-update` (a known contradiction, stale support, or coverage gap per `CLAUDE.md` → Page Status) is not settled state. Do not present its claims as solid; surface it separately under the unverified framing and carry its `needs_update_reason` (or the live `Contradictions`/`Tensions` entry) so the reader sees what is unresolved.

   **Coverage gate (before Step 3).** First, if the topic is over-broad (a keyword sweep hits a large fraction of the index) or ambiguous (multiple distinct readings), narrow it to the dominant cluster and state the narrowing in the brief's TL;DR, or ask one focused clarifying question — never silently truncate a whole-wiki-sized topic to fit the word target (that census is `reflect`'s job). Then decide the outcome by a countable test: one or more pages (any status) bear on the topic → produce the brief, framing draft/`needs-update`/`*[unverified]*`-only coverage as unverified per the rules above; zero pages bear on the topic at all → do not write a brief file, but still log the declined topic in Step 5 (CLAUDE.md logs every operation), say so, and suggest sources to ingest — naming only sources you are confident genuinely exist, marking any uncertain one `(verify exists)`, never fabricating a title, author, or venue (CLAUDE.md academic-integrity rule). This is the single decline rule: it fires only on the zero-page case, not thin-but-present coverage (which still produces a brief, with the thin support named in State of the wiki/Gaps).

3. **Save the brief** at `2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md`, where `HHMM` is the 24-hour UTC obtained at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context gives the date but not the current minute). `{topic}` in the filename is a short kebab-case slug (lowercase ASCII, hyphens, no spaces or punctuation); the `topic:` frontmatter and `# Brief:` H1 use the readable form. Capture the full `YYYY-MM-DD-HHMM-{topic}` stem once and reuse it for the filename; the Step 5 log entry and hot.md bullet reuse the same captured `HHMM` reformatted to the colon form `[YYYY-MM-DD HH:MM]` (`1430` → `14:30`) — do not re-run `date` or re-derive the slug, so all three timestamps agree. If the brief reveals a reusable topic entry point or missing concept/entity page, suggest `synthesis` or the relevant follow-up at the bottom of the brief (output-only — the no-page-creation rule is in Limits).

```markdown
---
type: brief
topic: {topic}
sources_used:
  - "[[1-wiki/concepts/page-name.md|page-name]]"
date: YYYY-MM-DD
---

# Brief: {topic}

## TL;DR
- 2-4 bullets on the current shape of the topic.

## Core ideas
- Key concept/entity pages, in simple language.

## State of the wiki
- What has solid source support.
- What is single-source or tentative.
- What syntheses exist.

## Open questions
- Questions the wiki cannot yet answer.

## Suggested reading
- Wiki pages and source pages to read next.

## Gaps
- Missing source pages, missing concept/entity pages, or thin connections.
```

Section discipline: write each section only where the wiki genuinely has content — leave it out or write "None in the wiki yet" rather than padding. State of the wiki describes coverage that exists (solid / single-source / which syntheses); Gaps names coverage that is missing or thin — do not repeat the same support-level fact in both. Order Suggested reading by orientation value: synthesis page first if one exists, then high-support concept/entity pages, then source/raw pages only for evidence. Briefs cite pages as page-level wikilinks; when a brief cites a specific source location (a `sec.`/`p.`/`fig.` locator) use CLAUDE.md's canonical citation form (source-page wikilink + `#page=N` raw deep-link) — a bullet that needs a raw locator usually means the request was really a `query`.

Example of a finished TL;DR + Core ideas + Gaps block (topic: attention):

```markdown
## TL;DR
- The wiki frames the topic mainly around Scaled Dot-Product Attention.
- Scaled Dot-Product Attention is the dominant approach in the corpus; alternatives have thinner support.
- One sub-area is single-source; most evidence clusters on the main thread.

## Core ideas
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]: weights values by the scaled dot products of queries and keys.
- [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]]: runs several attention functions in parallel over different learned projections.

## State of the wiki
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] has solid multi-source support across the corpus.
- [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] is single-source and tentative.
- One synthesis page exists: [[1-wiki/syntheses/attention-vs-recurrence.md|Attention vs Recurrence]].

## Open questions
- Does self-attention match recurrence on very long sequences?

## Suggested reading
- Start with [[1-wiki/syntheses/attention-vs-recurrence.md|Attention vs Recurrence]], then [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] for evidence.

## Gaps
- No concept page on additive (Bahdanau) attention — the corpus only covers the dot-product form.
- [[1-wiki/syntheses/attention-vs-recurrence.md|Attention vs Recurrence]] rests on a single synthesis; long-sequence behaviour is single-source — ingest a second.
```

A topic with draft-only coverage of one sub-area surfaces it honestly rather than dropping it:

```markdown
## TL;DR
- Support on the draft-only sub-area below is unverified — treat it as coverage that exists, not settled state of the wiki.

## State of the wiki
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] has solid multi-source support.
- Drafts (unverified): [[1-wiki/concepts/rotary-position-embedding.md|Rotary Position Embedding]] is draft-only — surfaced so the reader sees the coverage exists, but its claims are not yet fact-checked.
```

4. **Verify.** Confirm the file exists at the expected path and every section that is present carries real content or the explicit "None in the wiki yet" placeholder (sections may be omitted per Section discipline; the placeholder counts). For each wikilink, confirm the target file exists under `1-wiki/` on disk (or is listed in `index.md`); a link to a non-existent page must either be corrected to the right page or moved into the Gaps section as a missing page, never left as a silent dangler in Core ideas or Suggested reading. Confirm every non-obvious claim — especially corpus-scope absolutes in State of the wiki and Gaps ("solid multi-source support", "no page covers X", "no synthesis exists") — traces to a page actually read this run, re-checking any corpus-scope absolute ("no page covers X", "no synthesis exists") by listing the actual `1-wiki/concepts/`, `entities/`, `syntheses/`, or `sources/` directory on disk rather than trusting `index.md` (which can itself be stale) or impression, and re-checking a per-page support-level absolute ("solid multi-source support") against that page's own `sources:`/`source_count` and the status of those source pages, not `index.md`; do not answer from model memory. An absence/support absolute not backed by an actual directory listing (or the page's own `sources:`) this run is cut from the brief, not shipped on impression. Confirm the prose uses Canadian spelling and carries no AI-writing tells (scanned against `a-archive/style/ai-writing-tells.md`), and the word count is at or under the 600-word target (a brief-skill target; CLAUDE.md sets no length cap on 2-outputs artifacts). Fix or note any gaps before logging.

5. **Bookkeeping — update hot and log.** This is tracking, not wiki integration. Populate the brief's `sources_used:` frontmatter and the log `Used:` line with the same set of pages read in Step 2.

Recent activity bullet (prepend at the top of the `## Recent activity` section in `1-wiki/hot.md`). `hot.md` has four H2 sections — Recent activity, Open threads, Active focus, Watchlist; only the first, second, and fourth may be touched, and Active focus is user-owned (CLAUDE.md).

```markdown
- [YYYY-MM-DD HH:MM] brief | {topic} → [[2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md|brief-YYYY-MM-DD-HHMM-{topic}]]
```

Log entry (prepend in `1-wiki/log.md`):

```markdown
## [YYYY-MM-DD HH:MM] brief | {topic}
- Saved: [[2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md|brief-YYYY-MM-DD-HHMM-{topic}]]
- Used: [[1-wiki/concepts/page-name-one.md|page-name-one]], [[1-wiki/concepts/page-name-two.md|page-name-two]]
```

## Limits

- Output-only: do not create or modify concept/entity/synthesis pages. hot.md and log.md bookkeeping is expected.
- Do not answer from model memory.
- Target under about 600 words.
- Never modify `0-raw/`.
