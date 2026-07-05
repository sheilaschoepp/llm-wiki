---
name: query
description: Answer a research question from the LLM knowledge base. Read hot.md, index.md, relevant concept/entity pages, synthesis pages, and source pages as needed; save every answer to 2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md. Use when the user asks a specific question the wiki should answer — what the wiki says about a topic, which sources support a claim, whether a claim is true or has evidence, what the wiki's position is on a debate, or asks to back up or confirm a claim against the wiki — and wants a source-grounded answer. Not for a broad lay-of-the-land overview with no specific question (use brief), naming 2-4 pages for a side-by-side (use compare), a durable cross-source argument (use synthesis), whole-wiki direction or blind spots (use reflect), or processing a named raw source (use ingest). Ask before using synthesis to promote reusable answers or updating concept/entity pages.
---

# query

Answer from the wiki first, then reopen source pages or raw sources only when needed.

## Purpose

Queries turn the knowledge base into an answer. They do not silently change the wiki. Every query output is saved, and durable integrations require user approval.

The skill runs read → answer → verify → propose → apply → bookkeep: read the wiki (and raw sources when needed), synthesize and save the query output, verify it with two independent packets, surface durable integrations as a proposal, apply only what the user approves, then do hot/log bookkeeping. The no-silent-edit rule keeps the wiki safe even before promotion; the verification packets keep the saved query output faithful, because query outputs get read and reused without anyone re-checking them against the wiki.

## When To Invoke

Use when the user asks a research question that the wiki should answer or partly answer. Typical shapes:

- "What does the wiki say about X?"
- "Is there evidence for Y in the wiki?"
- "Compare claim A with claim B from the wiki."
- "Which sources support Z?"
- "What's the wiki's position on debate D?"

Pick `query` over `brief` when the request has a specific question, and over `compare` when the user is not naming 2-4 specific pages. Pick `query` over `synthesis` when the answer is a one-shot lookup, not a durable cross-source argument; offer to promote to `synthesis` only if the answer turns out to be a reusable topic entry point. Pick `query` over `ingest` when the user is asking what the wiki says, not naming a new source to process.

## When Not To Invoke

- The user names a raw source to process. Use `ingest` (deep mode for foundational sources).
- The user wants broad orientation without a specific question. Use `brief`.
- The user names 2-4 pages and asks for a side-by-side. Use `compare`.
- The wiki has no relevant notes. Say so and suggest sources to ingest.

## Procedure

```text
Query Progress:
- [ ] Step 1: Load hot.md, index.md, query-memory.md, multi-skill-memory.md
- [ ] Step 2: Read relevant concept/entity and synthesis pages
- [ ] Step 3: Read source pages for evidence
- [ ] Step 4: Reopen raw sources only when needed
- [ ] Step 5: Synthesize and save the query output (with a Recommended ingests section)
- [ ] Step 6: Verify the query output (two independent packets); fix and rerun until both clean
- [ ] Step 7: Propose wiki integrations or synthesis follow-up
- [ ] Step 8: Apply approved changes
- [ ] Step 9: Update hot and log
```

1. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/query/query-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md` first. Use the memory files to apply any prior corrections about query scope and framing (e.g. draft-page treatment, raw-source escalation, single-source flagging); both files may be empty, in which case the procedure below applies unchanged.

2. **Read candidate pages.** Start with relevant concept/entity pages and synthesis pages. Follow connections one to two hops when useful.

   Exclude `status: draft` pages by default. Drafts are unreviewed; their claims have not been verified against source support and may be wrong. Include them only when the user explicitly asks or when no non-draft page answers the question — not merely covers the topic, since a thin on-topic verified page does not displace a draft that actually answers. When a draft is the only available coverage, mark any bullet sourced from it with `*[from draft]*` so the answer is honest about its support level. Drafts are surfaced separately — marked `*[from draft]*` or under a "Drafts (unverified)" sub-bullet — never blended with verified content.

   Apply the same discipline at the claim level. Verification is claim-level, not all-or-nothing for the page (`CLAUDE.md` → Page Status), so a `verified` page may still carry individual bullets marked `*[unverified]*` — the pending delta from edits made since its last fact-check. A `verified` status is no longer a blanket guarantee: check the specific bullets you draw on for the `*[unverified]*` marker. Treat an `*[unverified]*` claim exactly like draft content — exclude it by default, even when its page is otherwise `verified`. Include it only when it is the only thing answering the question; then surface it separately and flagged (carry the `*[unverified]*` marker through to the output, or label it "unverified claim") so the support level is honest, never blended with checked content.

   **Zero-coverage exit.** If no page bears on the question at all — no non-draft page and no draft either (if only drafts bear on it, take the answer path with `*[from draft]*` marking per the rule above, not this exit) — stop the main path here. Before declaring silence, enumerate `1-wiki/` from the filesystem (`sources/`, `concepts/`, `entities/`, `syntheses/`), not from impression or `index.md` (which drifts), and confirm no page bears on the question: "the wiki is silent on this" is a corpus-scope absolute and earns the same filesystem enumeration Step 6 requires of every absolute (reaching this exit by impression + link-following is exactly the unverified-absolute failure that check exists to catch). Capture the `YYYY-MM-DD-HHMM-{topic}` stem first (per Step 5: run `TZ='UTC' date '+%Y-%m-%d-%H%M'`, capture once) for the saved filename and the Step 9 links, since Step 5 is skipped. Save a short query output recording the question, the full query frontmatter with the flow-style empty list `sources_used: []`, a one-line "the wiki is silent on this" body, and a `Recommended ingests` section (Step 5) naming the sources to ingest — under the same honesty guard (only papers you are confident exist; uncertain ones marked `(verify exists)`), which on this path is the section's only gate since Step 6 is skipped, so apply it as carefully as Step 6's existence re-check would. Skip Steps 3–4 and 6–8 (no evidence read, no verification packets, no integration proposal — the reduced Step 5 save above is still done); run Step 9 bookkeeping so the silence is logged. Never answer from model memory.

   When the question is a follow-up to an earlier query, scan `2-outputs/query/` for the relevant prior output and link it from the new output so the thread is traceable — but the wiki, not the prior output, stays the source of truth: re-verify any carried-forward claim against its wiki page in Step 6. If a prior output's answer no longer holds — a wiki page it relied on was changed, superseded, or removed since — note in the new output that the prior output is stale and what changed, so a reader who reaches it from `hot.md` is not misled.

3. **Read source pages.** For claims needing evidence, open the source pages listed in `sources:` and the `Sources` callout. Use their `Evidence` sections to locate precise support.

4. **Raw-source fallback.** Decide the answer's stakes level first (it governs both the triggers here and the Step 6 effort scaling), then reopen raw sources only when:
   - the source page is too thin.
   - the question is high-stakes (the answer will feed a paper draft, a synthesis promotion, an external claim, or any decision where a wrong number or quote would be costly to retract).
   - the answer depends on an exact quote, figure, page, or metric.
   - the answer cites a `p. N` / `fig. N, p. N` locator for a PDF that does not paginate from 1 — the `#page=N` physical-page offset can only be read from the raw (Step 5), and Step 6 spot-checks it.
   - the wiki and source page disagree.

   Do not use raw sources that have no source page unless the user explicitly asks to work outside the wiki.

   Record the answer's stakes level (high-stakes per the triggers above, or routine) in the saved output — not only the working context — so a Step 6 packet run as a separate pass can read it; the raw-fallback triggers above and the Step 6 effort scaling both turn on it.

5. **Synthesize and save the query output** to `2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md`, where `HHMM` is the 24-hour UTC obtained at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context gives the date but not the current minute) and `{topic}` is a short kebab-case slug. Capture the full `YYYY-MM-DD-HHMM-{topic}` stem once and reuse the identical string for the saved filename and the Step 9 hot.md and log.md links — do not re-run `date` or re-derive the slug, or the bookkeeping links will dangle. In the query output:
   - Cite wiki pages used with wikilinks. To point at a specific section of a wiki page, link its callout block ID: `[[path#^block-id|Display]]` (e.g. `#^appraisal`, `#^evidence`, `#^disconfirming-evidence`) — Obsidian does not anchor to callout titles, so name the section in prose if a `#^` anchor is not used.
   - A page/section/figure citation uses the two-form canonical citation (CLAUDE.md → Source Support And Verification): the source-page wikilink names which source, paired with a `#page=N` raw-file deep-link whose display carries both a structural anchor and the page (`sec. 1, p. 4171`, `app. C, tab. 8, p. 4186`). Form 1 (attributive): `[[1-wiki/sources/Devlin2019BERTPO.md|Devlin2019BERTPO]] ([[0-raw/papers/Devlin2019BERTPO.pdf#page=16|app. C, tab. 8, p. 4186]]) reports …`. Form 2 (parenthetical): `… claim ([[1-wiki/sources/Devlin2019BERTPO.md|Devlin2019BERTPO]]; [[0-raw/papers/Devlin2019BERTPO.pdf#page=16|app. C, tab. 8, p. 4186]]).`. N is the physical PDF page, which differs from the printed page for proceedings/article-paginated sources. The formula is `N = printed − (first_printed − 1)`, where `first_printed` is the printed number on the PDF's first physical page — Devlin2019 prints from p. 4171, so its printed p. 4186 is physical page 16 (`#page=16`); a source paginated from 1 has `N = printed`. Read `first_printed` by opening the PDF; do not guess it from the cited range. For a non-PDF source (article, media, other) there is no `#page=N`: pair the source-page wikilink with the per-type locator in a backticked span (`sec. Heading`, `para. 12`, `slide 4`, `00:03:12`), per `CLAUDE.md` → Source Support And Verification (Non-PDF source). A general attribution with no locator, and a reference to a wiki page's own callout (`#^appraisal`), stay bare source-page links. Attribute every locator to its source, since a query draws on more than one.
   - Include exact evidence pointers when source pages/raw sources were used.
   - Distinguish grounding level. A claim confirmed by reopening the raw this run (per Step 4) is raw-verified; a claim resting only on a source page's own locator is wiki-grounded — and the wiki is a synthesis layer whose extraction can be wrong (`CLAUDE.md` → Known Limitations). Do not present a wiki-grounded claim as if the raw were re-checked: when a load-bearing claim is wiki-grounded only, either reopen the raw (Step 4) or flag it (`*[tentative]*`, or note "from the source page, not re-checked against the raw").
   - Flag single-source support as fragile.
   - Preserve disagreements.
   - Say when the wiki is silent, and when it is, name the concrete next step — which source to ingest or which existing source page to deepen so a later query can answer it. A partial answer flags the unanswered part rather than presenting the supported half as complete.
   - **Close with a `Recommended ingests` section.** List the sources that would most improve the wiki's coverage of the queried topic — the gaps *this query* surfaced: a single-source claim wanting a second source, a load-bearing point that is only wiki-grounded, a draft the answer had to lean on, a dangling concept with no primary, or prior work the cited sources lean on but the wiki has not ingested. One entry per paper: author and year, the title, and one line on the gap it fills and which existing page it would strengthen. This is query-derived, not a generic literature dump — list only what this query's gaps point to, and skip a paper already ingested (check `index.md`). This standing section subsumes the silent-wiki next-step note above, so even a fully-answered query records how to deepen the topic. **Honesty guard (the academic-integrity rule applies):** list only papers you are confident genuinely exist — never fabricate a title, author, or venue, and mark any whose existence you are unsure of `(verify exists)` rather than asserting it. Write `none` when the query surfaced no specific next-source — it is not a quota, so do not pad it.

Frontmatter:

```yaml
---
type: query
topic: {topic}
sources_used:
  - "[[1-wiki/concepts/page-1.md|page-1]]"
  - "[[1-wiki/sources/page-2.md|page-2]]"
date: YYYY-MM-DD
---
```

Query outputs live in `2-outputs/` and use this query-specific frontmatter, not the wiki page schema — no `status:`, `created:`, `updated:`, or `tags:` fields.

Example query output:

```markdown
---
type: query
topic: self-attention
sources_used:
  - "[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]"
  - "[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]"
date: 2026-05-04
---

# Query: how does Scaled Dot-Product Attention work?

[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] computes attention weights as `softmax(QK^T / sqrt(d_k))` and uses them to weight the value vectors, scaling by `1/sqrt(d_k)` to keep the dot products from growing large enough to push softmax into low-gradient regions ([[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]; [[0-raw/papers/Vaswani2017AttentionIA.pdf#page=4|sec. 3.2.1, eq. 1, p. 4]]). Vaswani2017 paginates from page 1, so the physical PDF page equals the printed page (`#page=4`). Support is single-source. *\[tentative\]*

The wiki is silent on whether Scaled Dot-Product Attention holds under conditions the listed sources did not test. To close this, ingest a source that probes attention scaling under those conditions — none is in `0-raw/` yet.

## Recommended ingests

- Press & Wolf 2017 — "Using the Output Embedding to Tie Word Embeddings" — would give [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] a second source on the scaling factor's effect, which currently rests on Vaswani2017 alone (single-source). (verify exists)
- none beyond the above — the rest of the answer is multi-source.
```

6. **Verify the query output.** Before proposing any integration, run two independent verification packets over the saved query output and fix what they find. The packets may run as separate passes by one assistant or by separate assistants, but each returns its own result, and the query output is final only once both come back clean. One assistant in separate passes buys independence from self-circularity — the second pass re-checks the output against the wiki, not against the first pass — but not from a shared blind spot, since the same model can repeat one misreading; prefer separate assistants where the stakes justify it. Verification checks the query output, not the wiki pages themselves (`audit` checks those).

   1. **Wiki-faithfulness packet** — over the saved query output, run each check:
      - **Trace every claim.** Read each substantive declarative sentence individually: it either carries a trace to a named `sources_used` page that actually says it, or is explicitly marked as inference / own-voice judgement. An unmarked, uncited bridging or synthesis sentence is a finding, not given the benefit of the doubt — no claim rests on model memory.
      - **Enumerate every absolute from the filesystem.** Any scope claim — "every source", "no page", "none", "all", "the wiki is silent on X" — is re-checked by enumerating the full set it quantifies over from the actual `1-wiki/` directory listing (`sources/`, `concepts/`, `entities/`, `syntheses/`), using `index.md` only as a convenience map, never the authoritative set, since `index.md` drifts and a page on disk but missing from it still falsifies an "every source" claim. Open each and confirm none falsifies it — never against only the pages already in `sources_used`, never from impression; downgrade or qualify any absolute not verified that way. (Shipped failure: an unverified "every source treats the model as the agent" that one source — not in `sources_used` — contradicted; this is why the set is enumerated from the filesystem, not from memory of what was read.)
      - **Resolve and spot-check citations.** Wiki pages link path-qualified; a page/section/figure locator carries a `#page=N` deep-link to the raw at the cited physical PDF page, with the locator as readable text (Step 5); section references use the callout block ID; every locator is attributed to the right source. Spot-check every `#page=N` link on a load-bearing number, quote, or metric by opening the raw at physical page N, confirming the cited content is there, and verifying the structural anchor names the section/figure the content actually sits in (a right-page/wrong-section anchor is a fabricated locator, as wrong as a bad offset), recording (as a transient verification note, not in the saved output) the printed page number visible at physical N plus the located content as the spot-check's proof-of-read — mirroring the strengthened `#page=N link spot-checked` field in `.claude/skills/multi-skill/references/verification.md` (which records the printed page seen at N — the un-fakeable proof the offset is right and the raw was opened, not lifted from the wiki source page); a `#page=N` spot-check asserted with no printed page and content recorded counts as not performed (downgrade the claim to wiki-grounded / `*[tentative]*`). A well-formed link to a guessed-wrong page (e.g. offset zero on a proceedings-paginated source) is a silent-wrong citation, not a pass. A high-stakes answer (Step 4) that cites no `#page=N` link at all is itself a finding (the raw-fallback trigger fired and was not honoured); and a citation that *looks* raw-verified (a `#page=N` deep-link on a load-bearing claim) but whose raw was not actually opened this run is a finding unless the claim is flagged wiki-grounded (Step 5).
      - **Confirm honesty markers.** Single-source support flagged fragile; draft-sourced bullets marked `*[from draft]*` and surfaced separately; any `*[unverified]*` claim carried into the answer (even from an otherwise-`verified` page) surfaced separately and flagged, never blended with checked content (Step 2); inference labelled as inference rather than stated as a source's own claim; contradictions preserved rather than blended away; a partial answer flagging the unanswered part rather than presenting the supported half as complete.
      - **Check the `Recommended ingests` section.** Confirm the Step 5 honesty guard held: no fabricated or unmarked paper (each is one you are confident exists, uncertain ones `(verify exists)`), each entry names a gap *this query* surfaced and is not already ingested, `none` not padded (Step 5).
   2. **Coverage-and-integration packet:** no relevant non-draft page was overlooked — re-scan the `1-wiki/` directory listing (with `index.md` as a convenience map only) for pages bearing on the question and confirm any corpus-scope absolute — "every/all/no/none source", "the wiki is silent on X", "nothing else covers this" — by enumerating the quantified set from the filesystem, not from `index.md` alone (it drifts) and not by assuming it. Confirm the answer surfaces every integration candidate Step 7's trigger (below) would require — a named, reusable idea the answer defines or leans on with no page covering it, even on single-source support (flag the level) — so Step 7 has them and none was silently dropped. (This is the other shipped miss: a sync/async answer that declined promotion although the question literally asked the wiki to define those two reusable terms.) The answer is honest about partial answerability — the supported part answered, the missing note or source named. No AI-writing tells and Canadian spelling throughout, scanned against `a-archive/style/ai-writing-tells.md` and the house Canadian-spelling default.

   Both packets must come back clean in the same round — both pass with no fix applied. Fix clear mistakes, then rerun the affected packet. After at most three fix-and-rerun rounds, if a packet keeps flagging the same item that cannot be resolved from the available pages — or a fix for one packet re-introduces a finding the other just cleared (oscillation) — that is not a blocker: downgrade the affected claim (qualify the absolute, mark the bullet `*\[tentative\]*`, or state the wiki is silent on that part), note that it was softened to converge, and treat the softened output as clean — ship honest about what could not be verified, never on an unverifiable absolute. Softening has four hard limits: it never applies to the "every claim traces to a named page" check — a claim that traces to no `sources_used` page is cut, not marked tentative, because a tentative model-memory claim is still a model-memory claim (Limits); it may never blend a preserved cross-source contradiction into apparent agreement — an unresolvable disagreement ships as both sides preserved (per Edge Cases), not converged away; and it never marks an unconfirmable `#page=N` locator `*\[tentative\]*` to ship it — a deep-link whose cited content cannot be confirmed at physical page N is removed (drop the locator, or restate the claim as wiki-grounded), because a wrong page is a false citation, not weak support, and `*\[tentative\]*` (a support-strength marker) cannot cure a wrong locator; and it never marks a claim the faithfulness check flags as distorting or overstating its cited source `*\[tentative\]*` — a claim that misrepresents a source it does cite is corrected to match the source or cut, never softened, because faithfulness is binary (`CLAUDE.md` → Source Support And Verification: a well-formed, plausibly-worded claim that distorts the source still fails) and `*\[tentative\]*` marks weak support, not a false claim, exactly as it cannot cure a wrong locator. Scale effort to stakes: a high-stakes, multi-source, or absolute-bearing answer gets both packets in full; a trivial single-page lookup that asserts no absolute needs only the non-negotiable checks (every claim traces to a named page; any absolute is enumerated from the filesystem; any `#page=N` link present is spot-checked; and the honesty markers are confirmed — a draft or `*[unverified]*` claim is never silently blended, regardless of stakes), not the full re-scan. The AI-writing-tells and Canadian-spelling scan runs on every output regardless of stakes — it is house policy, not a stakes-scalable check. The gate is on finalizing the saved output; the corrected output is the record, so do not append these Step 6 query-packet results to the answer body or write a separate report (the Step 8 promotion path's `Promotion verification` section is a different artifact, for the different Step 8 ingest packets).

7. **Propose durable integrations.** Surface a candidate whenever the answer defines or leans on a named, reusable idea the wiki uses but has no page for — do not decline silently. The trigger is reusability, not source count: a single-source idea is still surfaced (with its support flagged), and a question that asks the wiki to *define* a term is itself a strong signal that term deserves a page. The conservative-growth guard still applies — a one-off term unlikely to recur is not a candidate — but when in doubt, surface it and let the user decide.
   - New concept/entity page when the answer reveals a reusable one-idea note (single-source allowed; flag the support level).
   - Existing concept/entity page update when the answer clarifies or corrects the idea.
   - Recommend `synthesis` when the answer is a reusable cross-source argument or topic entry point. A synthesis needs at least two sources; a one-source reusable answer goes to a concept/entity page, or a deliberate single-source synthesis stub (`single_source_stub: true`) only on explicit user request.
   - Show the exact note/change and ask before applying — one focused approval per page (`AskUserQuestion`), marking the recommended option `(Recommended)` and ordering it first (a surfaced candidate has a lean — the skill judged it reusable enough to surface; omit the mark only on a genuine no-lean call).

8. **Apply approved changes under ingest discipline.** Approving a page turns this query into a page-authoring pass — a full raw re-read plus the two ingest verification packets, heavier than the pure-output common case. A new or substantively edited concept/entity/synthesis page is new durable wiki content, so author it as such: build the page to its `CLAUDE.md` template (the concept/entity or synthesis frontmatter and required callouts), fully re-read the supporting raw source(s) — the original papers, not just the wiki source pages — then run the two ingest verification packets (distinct from this skill's Step 6 query packets) as specified in the shared `.claude/skills/multi-skill/references/verification.md` over every touched page and fix what they find before finalizing. The page work is complete only when both ingest packets come back clean in the same round — both pass with no fix applied — not merely after one corrective pass each. New pages stay `status: draft` for a later `audit` to verify. Record the two packets' results — the per-packet late-section detail, the `#page=N` spot-check, and any fixes — as a short `Promotion verification` section appended to the query output saved in Step 5; do not write a separate report file, and never one under `2-outputs/ingest/` (the shared `verification.md` routes a query's verification into its own query output — one report per query, in the calling skill's own folder). Then do the mechanical bookkeeping: the new page's `sources:`/`source_count`/`Sources`, the supporting source pages' `Concepts and Entities` callouts, every touched page's `updated:`, and `index.md` — and, when the approved page is a synthesis, the synthesis-only frontmatter the ingest-family `verification.md` does not cover: `origin:` (a pipe-rendered wikilink to this saved query output), `single_source_stub: true` only if a single-source stub was explicitly approved (Step 7), and the two-source minimum (CLAUDE.md → Synthesis Pages; lint flags a synthesis missing the required `origin:`). (A pure-output query with no durable page — the common case — skips these Step 8 ingest packets; the Step 6 verification still ran.)

9. **Update `hot.md` and `log.md`.** Prepend a one-line entry to `hot.md` Recent activity, then a full entry to `log.md`, both stamped `[YYYY-MM-DD HH:MM]` in 24-hour UTC — reuse the `HHMM` already captured for the Step 5 stem (do not re-run `date`), since CLAUDE.md → Hot, Index, And Log requires the time and lint's `chronology_missing_time` flags an untimed entry. Touch only Recent activity (and Open threads or Watchlist when the query opens a durable thread or a question worth tracking); never touch Active focus — it is user-owned.

   `hot.md` Recent activity (one line):

   ```markdown
   - [YYYY-MM-DD HH:MM] query | {topic} ([[2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md|query]]) — one-line outcome: what the wiki could or couldn't answer, plus any integration/promotion.
   ```

   `log.md` entry:

   ```markdown
   ## [YYYY-MM-DD HH:MM] query | {topic}
   - Used: [[1-wiki/concepts/page-1.md|page-1]], [[1-wiki/sources/page-2.md|page-2]]
   - Saved: [[2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md|query-YYYY-MM-DD-HHMM-{topic}]]
   - Integrated: [[1-wiki/concepts/self-attention.md|self-attention]] (or "none")
   - Promoted: [[1-wiki/syntheses/synthesis-title.md|synthesis title]] (or "none")
   ```

## Edge Cases

- **Partially answerable.** Answer the supported part and name the missing note/source.
- **Contradictory notes.** Present both sides and propose an audit or synthesis, not a forced resolution. When the contradiction is between two pages both marked `status: verified`, also flag them as needs-update candidates in the Step 7 proposal — a verified-vs-verified disagreement means at least one verification is now stale — and let the user decide; query never edits page status itself (no silent edits), it surfaces the flag.
- **Reusable answer but one source only.** Still surface it as a concept/entity candidate per Step 7 (flag the single-source support); do not create a synthesis page from one source unless the user explicitly asks for a single-source stub.
- **Answer reveals a page is wrong.** When the query finds an existing page is factually wrong against its own raw source (not merely disagreeing with a sibling), surface that in the Step 7 proposal as a removal-or-replacement candidate for the user to route; query never edits or removes the page itself (no silent edits).

## Limits

- Never modify `0-raw/`.
- Every query saves an output file (Step 5) — non-negotiable even when the user asks to skip it, because the audit trail and hot/log bookkeeping depend on the saved file; explain that briefly rather than skipping.
- No silent wiki edits (Step 7); no model-memory answers when the wiki is silent (Step 2 zero-coverage exit — say the wiki is silent and suggest sources to ingest, so unsupported claims do not enter the audit trail).
- The `Recommended ingests` section never fabricates a source — the academic-integrity rule applies (Step 5 authors it, Step 6 gates it; on the zero-coverage exit, which skips Step 6, the inline honesty guard is its gate).
