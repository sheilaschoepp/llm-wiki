# Wiki-authoring verification

The single canonical copy of the wiki-authoring verification spec, in the shared `multi-skill/references/` location because more than one skill runs it. Every operation that authors or changes durable `1-wiki/` content runs these two packets before finalizing: `ingest` Step 8 (every mode — new or existing source, normal or deep), `query`'s page-authoring path (when an approved query promotes a durable page), `synthesis` Step 8 (over a new or updated synthesis page), and `supersede` Step 7 (over the content it newly authored or changed). Running the packets does not require `CLAUDE.md` open; this file is complete on its own. There is no `CLAUDE.md` mirror of this spec — `CLAUDE.md` carries only the cross-skill lifecycle invariant in Page Status (a newly authored or changed page stays `status: draft`, or its changed claims are marked `*[unverified]*`, until `audit` promotes it), not the packet procedure. (The skills that run these packets still cite `CLAUDE.md` for page templates, section lists, and structural rules, per the single-source-of-truth design.)

**Page-type scope.** The packet bullets are written for a source page and the concept/entity pages it feeds (`ingest`'s outputs); read them by page type for the other callers. On a **synthesis** page the source-page-specific bullets map to the synthesis analogue — the `Answer`, `Scope`, and `Tensions` claims stand in for a source page's TL;DR and Key Claims, and the caller adds its own composition check (the aggregating `Answer` must not exceed the union of its cited sources; see `synthesis` Step 8). On a **supersede** operation the packets run over the claims that operation newly authored or changed — a replacement bullet, a merged-in claim, a re-extracted figure's caption — not over unchanged content moved intact from an already-verified page. The concept/entity and source-page bullets apply as written to `ingest` and `query`.

## Contents

- Tiered Independent-Refuter Verification
- Source-Faithfulness Packet
- Note-Quality and Coverage Packet
- Both Packets Also Check
- Fix, Rerun, Report

Run at least two independent verification packets over the raw source and every page created or touched by the operation. Packets may be run by separate assistants or by one assistant in separate passes, but each packet returns its own result. One assistant in separate passes buys independence from self-circularity — the second pass re-checks the page against the raw, not against the first pass's conclusions — but not from a shared blind spot, since the same model can repeat one misreading twice. Genuinely separate assistants are therefore not optional but required, at the tier the claim's impact sets: the independence of every packet is supplied by independent refuter subagents per the tiered model below (Tiered Independent-Refuter Verification), and `verified` is earned only at the top tier. Each packet re-derives its load-bearing checks from the raw source, not from the drafted page — matching the page against itself is not verification. When one assistant runs both passes, the second re-opens the raw and re-locates the load-bearing numbers, quotes, and locators there, including at least one detail from a late section (final section, last figure, or appendix) as proof the raw was re-read this pass. A packet that re-read no raw content cannot return pass. If either packet reports a fix, apply it and re-run both packets. The operation is complete only after at least two independent packets are clean in the same round — both pass with no fix applied. If fixes cannot bring both packets clean within three fix-and-rerun rounds, or a fix for one packet re-introduces a finding the other just cleared (an oscillation), stop, leave the page as last written, and report the unresolved findings rather than looping.

## Tiered Independent-Refuter Verification

The independence every packet needs is supplied by **independent refuter subagents**, and how many is set by the claim's **impact** — how much a wrong certification costs, and how likely one agent is to miss the error. This is the mandatory form of the "genuinely separate assistants" the intro calls for; the same-agent second pass is a fallback only where the tier is 0.

Tiers, set per non-obvious claim (a whole-page check takes the highest tier any of its claims reaches):

- **Tier 0 — no refuter.** Obvious or definitional bullets, the author's own marked judgement (`Appraisal`, `Open Questions`, `Assumptions`, `Disconfirming Evidence`, synthesis `Tensions`), and mechanical or verification-neutral edits. These carry no inline citation and assert nothing a refuter could ground-check, so the orchestrator's own pass suffices.
- **Tier 1 — one refuter.** A low-stakes non-obvious claim with a single, clearly-locatable citation (a specific fact at a specific page). One independent refuter opens the raw at the cited page and tries to refute it.
- **Tier 3 — three refuters, must agree.** Every other non-obvious wiki claim — the broad default, so in practice most claims: a summary / aggregate / generalization claim, a cross-source or contrast citation, a number / metric / result, or any claim that will be trusted downstream once stamped. Three independent refuters each attempt to refute the claim against the raw; it is certified only when all three fail to refute it. For a summary or generalization claim each refuter **recomputes the whole set cold** — every row, task, or condition the claim ranges over — not the single cell the claim cites (the cited cell is the evidence the author selected because it fits, so confirming it certifies the distortion).

Refuter mechanics — the cross-skill subagent rule:

- Refuters **read and reason only.** Spawn each with read-only tools (Read, Glob, Grep; no Edit / Write / shell-write), from the **top-level orchestrating agent**, never nested inside another subagent. Every status change and fix is applied by the orchestrator, so all writes pass through one place and one set of safety rules, and concurrent writes never collide.
- Give each refuter the claim and the raw, **not the page's framing**, and prompt it to refute — default to "refuted" unless the raw plainly supports the claim. A refuter that cannot reach the cited raw region (missing, unreadable, image-only, OCR-garbled, truncated) returns "cannot confirm", which counts as a non-pass, not a pass.
- **Agreement certifies; a split does not.** When a tier's refuters do not all hold — any refuter refutes or cannot confirm — the claim is not certified: mark it `*[unverified]*` (or `*[tentative]*` where support is thin) and, for a page being promoted, set the page `needs-update` with the disagreement recorded, never certify on a split.

Where the tiers run:

- **`verified` is earned only at Tier 3.** The schema invariant (`CLAUDE.md` → Page Status): a wiki claim reaches `status: verified` only after passing the Tier-3 gate — three independent refuters agreeing — on every non-obvious claim on the page. This is the layer-2 gate `audit` runs, and the only place `verified` is stamped.
- **Authoring runs the tier its draft warrants and finishes at `draft`.** The layer-1 authoring skills (`ingest`, `synthesis`, `query`'s promotion path, `supersede`) run these packets with independent refuters at the tier the authored claim's impact sets, but their output stays `status: draft` — a draft is explicitly untrusted, so a wrong draft claim is lower-impact than a wrong `verified` one. They do not run the full Tier-3 quorum on every authored claim; `audit` runs that when it later earns `verified`, and running the full quorum at both authoring and audit would double the cost for no gain.
- **Cost is paid once per claim.** The Tier-3 quorum runs when a claim earns `verified`; `audit` skips already-`verified` claims on later runs (`partial` mode, keyed on `verified_hash:`). Steady state is bounded — the heavy spend is the first full verification of the existing corpus.

## Source-Faithfulness Packet

- Metadata matches the raw source; the source-page TL;DR, Contribution, Key Claims, and Evidence pointers are faithful to the raw; no load-bearing part of the raw source is dropped in a way that makes the source page misleading.
- Sections without genuine source support are left as `> - None noted` placeholders, not padded with invented or paraphrased content.
- For each embedded image, the surrounding text or paired locator identifies what the image is (figure, table, equation, slide, frame, or other artifact), and that identification is correct. On source pages this is the locator paired with the embed; on concept/entity pages it's the prose around the embed plus the source-page locator the image inherits from.
- **Faithfulness is judged within the stated scope.** If frames or a deep-mode purpose were used, the page is faithful if everything it claims about the source, scoped to those frames (their union) or that purpose, is correct. Items dropped because they fall outside every listed frame or the purpose do not count as faithfulness gaps. A page may carry more than one frame; judge it against the union of all listed frames. (Depth purpose generalizes the narrower frame — the same within-scope rule applies whether the scope was supplied as frame texts or as a stated non-frame purpose.)
- **Scope-widening reingests are judged against the new wider scope.** When this operation widened scope — the new `frames:` union (including `frames: []`) admits source material the old union did not — judge the body against that wider scope: content the widened scope now admits but the body did not grow to cover is a faithfulness gap, not a legitimate omission. A `frames:` value that claims more scope than the body covers fails the packet. (A reword or a redundant lens that admits nothing new is not a widening; judge it against the unchanged scope.)
- **Full-text coverage.** Every ingest fully re-reads the raw source, so confirm the operation had full-text coverage — the raw was fully readable, not truncated, an image-only scan, OCR-garbled, paywalled to an abstract, or partially extracted. Probe concretely: the final page/section is present and intelligible (catches truncation) and body text, not only figure captions, is extractable (catches image-only scans). For a genuinely image- or media-based source (a slide deck, an infographic, a video still), body-text extraction is not the probe — confirm instead that the visual content the page draws on (every slide, frame, or figure) is present and legible; the absence of body text is expected there, not a coverage failure. Partial coverage is surfaced, not summarized as if whole.
- **Subtle-hallucination check** — run each by name, since these errors are plausible and well-formatted, not obvious nonsense:
  - Outbound citations: any other work named on the page (related work or prior papers in Contribution or Connections) actually appears in the raw source and is attributed as the raw source attributes it — no invented or misattributed references.
  - Cite versus contribute: claims the source quotes or borrows from other work are not presented as this source's own contribution.
  - Restated numbers and math: every statistic, metric, or equation result restated in TL;DR, Key Claims, or Evidence matches the raw source exactly, with extra care where notation is overloaded across sections.
  - Claim faithfulness (claim by claim): walk each non-obvious claim and check it individually against the source it draws from — not only that numbers match, but that the claim's meaning, scope, and strength match the source. A plausibly-worded claim that overstates, narrows, over-generalizes, or otherwise misinterprets the source fails here, even when the number is right.
  - Under-specified detail: where the source omits its own data, hyperparameters, sample size, or settings, those gaps stay as `> - None noted`, never filled with confident specifics the source never stated. Each non-empty `Limitations` bullet ties to a locator, since `Limitations` records the source's own acknowledged weaknesses — a bullet with no locator is an agent-invented limitation, not the source's.
  - Load-bearing anchor: each load-bearing Key Claim is anchored to a short verbatim quote (in quote marks) plus a locator in Evidence so it can be re-checked against the raw cheaply; paraphrase elsewhere and reserve verbatim for the anchor.
  - Paraphrase versus extraction: bullets outside the quote-marked anchors are re-voiced in the user's words, not lifted near-verbatim from the raw. An accurate copy-paste still fails — verbatim text belongs only inside quote marks paired with a locator. This is the verify-side defence of the translation discipline; the page is LLM-drafted and not human-re-voiced, so nothing else catches a lifted-but-accurate bullet.
  - Cross-source merge: no detail (a number, method, hyperparameter, result, or attribution) from a different source has been imported into this one and presented as this source's own — multi-source context and the sibling sweep make silent merging a live risk, distinct from cross-source contradiction.
  - Cross-source mis-location: on a bullet naming two or more sources, each clause is cited to the source that states it — the claim's origin — not to the source the bullet is framed about. The failure is a true, well-formed claim from source A pinned to a locator in source B where it does not appear; it passes every structural check and reads correctly, so only opening the cited page catches it. Concentrated in the cross-source callouts (`Contradictions`, `Tensions`, `Not This`, `Disconfirming Evidence`), where a contrast sentence has two origins and needs two locators (cite each clause to its own source). Two variants: the whole claim landing on the wrong page, and the softer case where the criticism is genuinely at the cited page but a specific named detail within it (a model name, a figure, a method) is the wiki's own inference attributed to the source. This is the opposite direction from Cross-source merge above — mis-location keeps the claim's true origin but points the citation at the wrong source (CLAUDE.md → Source Support And Verification, the multi-source-bullet rule).
  - Niche-subfield fabrication: where the source sits in a narrow or data-poor area, background and terminology the raw does not state are left as `> - None noted` rather than filled with a confident guess.
  - Located deep-links (PDF raws): open the raw at physical page N, confirm the cited content is there, and record the printed page number visible at N (proof the page was opened, not just offset-computed). Sampling differs by bullet type. For ordinary within-source locators, spot-check at least one `#page=N` link per distinct raw a touched page cites. But **for every locator on a cross-source bullet — one naming two or more sources (`Contradictions`, `Tensions`, `Not This`, `Disconfirming Evidence`) — open all of them, no sampling.** These are the small, high-risk population where a mis-located citation (Cross-source mis-location above) hides behind a good sibling when only one link per raw is sampled, so verify each clause at the exact page it is cited to, never the document at large — a distinctive figure or name often appears elsewhere in the same document, so a document-wide search would falsely confirm a bad citation. Verify the structural anchor too, not only the page: a `sec.` or `fig.` locator that names a section or figure the content does not sit in is a fabricated locator, as wrong as a bad offset. A guessed zero offset on a non-1-paginated source (proceedings, article pagination), or an invented anchor, is a silent-wrong link — not a pass. A locator that cannot be confirmed in the raw is dropped, corrected, or its claim marked `*[unverified]*`, never written as if confirmed.

## Note-Quality and Coverage Packet

- Each concept/entity idea is supported by the source page touched in this operation; one idea per page; simple language; no source-shaped "what source X says" sections.
- **Supporting-source attachment (reverse direction).** This catches the under-link the forward checks miss: a source that genuinely supports an *existing* concept/entity page but was never attached to it. For each existing concept/entity page on the source's topic, confirm the support relationship was resolved either way — the source was attached (it appears in that page's `sources:` + `Sources` callout, carrying the claim bullets it contributes) or it was consciously declined (recorded as "no attach" in the Step 3 plan because the overlap is purely topical, with no real support). A page this source genuinely supports — backs a claim it makes, or contributes a non-obvious point it should make — that does not list this source is a finding: attach it (and write the contributed claims) or, if the support is not genuine on a second look, record why. The bidirectional `Concepts and Entities` ↔ `sources:` agreement check below only covers pages already in the source page's callout, so it passes vacuously on a page that was never touched; this is the check that flags the page that *should* have been touched. Judge "genuinely supports" conservatively — purely topical overlap is not support, so this does not license attaching the source to every neighbouring page (that would be the citation-wallpaper failure the conservative-growth rule guards against).
- Link every reference (claim by claim): every genuine reference to a wiki page that exists (concept/entity/synthesis/source) is wikilinked, on every occurrence in every callout, not only first use — an existing page is never left as a plain-text mention. A page never links to itself; generic wording that is not actually referencing the page, and text in quotes/verbatim/code, are exempt. `lint`'s `unlinked_page_mention` is the deterministic backstop on concept/entity/synthesis pages. See `CLAUDE.md` → Wikilink Format.
- Claims carry their reason (claim by claim): a causal, comparative, or evaluative claim ("X enables Z", "X is harder than Y", "X is brittle") gives its reason or mechanism, not just the conclusion, so the bullet is understandable on its own. The reason is the source's (faithful to it) for a source claim, or the user's own for an own-voice judgement (`Appraisal`/`Disconfirming Evidence`/`Open Questions`). A mechanism the source does not state is never fabricated and attributed to the source — flag the bare assertion (`*[tentative]*`) or recast it as own-voice reasoning instead. See `CLAUDE.md` → Plain-Language Style.
- Claim support (claim by claim): walk each bullet. A non-obvious factual claim on a concept/entity (or synthesis) page carries an inline citation in one of the two canonical forms — both pair the source-page wikilink (which source) with a located raw deep-link (where in it): Form 1 attributive `[[1-wiki/sources/<stem>.md|<stem>]] ([[0-raw/papers/<stem>.pdf#page=N|sec. 3.2, p. 5]]) shows …`, or Form 2 parenthetical `… claim ([[1-wiki/sources/<stem>.md|<stem>]]; [[0-raw/papers/<stem>.pdf#page=N|sec. 3.2, p. 5]]).` (round brackets `(` `)` wrap the citation, semicolon between key and locator). For a PDF the deep-link display always carries both a structural anchor (`sec.`/`app.`/`ch.`/`fig.`/`tab.`/`eq.`) and the printed page `p. M`; for a non-PDF, a backticked per-type locator replaces the deep-link. Form 2 is wrapped in round brackets `( )` — a citation in the superseded square-bracket form (`[[[<key>]]; [[<loc>]]]`, the triple-bracket `[[[` opener) FAILS this packet and must be rewritten to round brackets (lint's `citation_bracket_style` catches it mechanically, but ingest writes it correctly the first time). A non-obvious claim with no inline source, or cited to a source that does not back it, is a finding — and a source-link-only citation (a bare source link with no located deep-link, or a PDF deep-link missing its anchor or its `p. M`) on a non-obvious claim is an incomplete citation and FAILS this packet. Obvious or definitional bullets, and the author's own marked judgement (`Appraisal`, `Open Questions`, `Disconfirming Evidence`, `Assumptions`, synthesis `Tensions`), need none. This is not citation wallpaper: obvious bullets stay uncited. Non-obvious = a specific finding, a number, a particular mechanism or design choice attributed to a source, a contestable generalization, or a claim about what other work did. See `CLAUDE.md` → Source Support And Verification.
- Standalone-read: each concept/entity page reads with its source page closed — no implicit referents ("the proposed method", "their setup"), no dependence on source context the reader does not have, and every leaned-on technical term glossed on first use. The visible symptoms (source-shaped sections, per-line citations) are checked above; this catches the clean-prose page that still only parses if you have read the raw — a source-summary in disguise. Re-voice it into a reusable idea.
- Named source attribution: on concept/entity (and synthesis) pages, any bullet that attributes a claim or caveat to the source names it in the standard form `[[1-wiki/sources/<stem>.md|<stem>]]` (or the named system) — never a vague referent for the source ("the paper", "the survey", "the study", "the article", "the authors", "the source", or their possessives "the paper's"/"the survey's"). Where the reference is just narration in `Idea`/`Why It Matters` ("the survey breaks it into X"), re-voice the bullet to state the idea standalone rather than bolting on a citation. See `CLAUDE.md` → Plain-Language Style; `lint`'s `vague_source_referent` and `source_context_leak` checks are the deterministic backstop.
- No load-bearing idea from the source page is dropped in a way that makes a touched note misleading.
- No intra-page redundancy: no point is paraphrased across two callouts (or repeated within one) on a touched concept/entity/synthesis page — `CLAUDE.md` → Body Sections As Callouts forbids restating the same point across sections. Each section says its own thing; an empty `> - None yet` placeholder is correct when a section has nothing genuine to add, and is never padded by re-stating a point already made elsewhere. This is the semantic half — a point reworded into different words across sections — that `lint`'s `intra_page_redundancy` (lexical token-overlap) cannot see; the two together cover both. Source pages are exempt (a Key Claim is intentionally re-anchored as a verbatim Evidence quote). When two bullets do say the same thing, keep it in the one section where it belongs and drop or merge the other.
- Concept/entity pages have at most one defining image, and that image illustrates the idea rather than summarizing the source.
- No bold or italic in any wiki body (the `*[unverified]*` / `*[tentative]*` / `*[disputed]*` bullet markers are allowed). All wikilinks include `.md` and use the pipe-rendered display form with no whitespace around the pipe (`[[path|display]]`, never `[[path | display]]`) per the schema.
- **No LLM-voice / AI-writing tells in any produced body** (source, concept/entity, synthesis). Scan against `a-archive/style/ai-writing-tells.md` for its full pattern set — significance-puffing openers, hedging filler, elegant variation, fabricated typologies, the broader-context reflex, and the high-density vocabulary list. Re-voice any hit into the user's plain register. The page stays LLM-drafted (the audit promotion gate verifies correctness, not voice), so this packet is the safeguard that keeps generic LLM prose out of the durable record.
- Deep mode: detailed evidence (equations, metric tables, long method detail) stays in the source page, not pushed into concept/entity pages.

## Both Packets Also Check

Cross-page support and honesty: the source page's `Concepts and Entities` callout and the supported pages' `sources:`, `source_count`, `Sources`, and `attachments:` agree; embedded image paths resolve to files that exist; weak claims are tentative; contradictions are visible; open questions are not disguised as claims. In existing-source mode, also confirm quarantined files no longer appear as live embeds.

## Fix, Rerun, Report

Fix clear mistakes in the just-created or touched pages before finalizing. If a fix requires judgement beyond this operation's scope, report it instead of silently changing the wiki. Rerun affected packets after fixes.

**Repeated-literal sweep after any citation fix.** When a citation is corrected mid-run — a mis-located claim moved to its true source, a wrong locator or restated number fixed — the same distinctive claim is usually restated on several other pages, so a fix at one site leaves the siblings standing. Before finalizing, grep the distinctive literal across the wiki (`grep -rn "{literal}" 1-wiki/` for a figure or percentage; the distinctive phrase for a qualitative claim) and re-check every occurrence, applying the same fix wherever the claim recurs. Record the sweep — the literal searched and the sites checked and fixed — in the report. A single-site correction that leaves an identical error a few bullets or a few pages away is the half-repair this sweep exists to close.

One report per operation, in the calling skill's own output folder — never a second file, and never another skill's folder.

- `ingest` (Step 8) writes a dedicated report to `2-outputs/ingest/ingest-YYYY-MM-DD-HHMM-{stem}.md` (`HHMM` is the 24-hour UTC from `TZ='UTC' date '+%Y-%m-%d-%H%M'` at write time). The body differs by mode — new-source vs reingest, the two shapes below — but the folder and filename pattern are the same. This report is ingest's single operation output.
- `query`'s page-authoring path writes no separate report. It records the two packets' results — the per-packet late-section detail and `#page=N` spot-check, plus any fixes — as a short `Promotion verification` section inside the query output it already saved at `2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md`. One file per query, even when the query promotes a page; nothing is written under `2-outputs/ingest/`.
- `synthesis` (Step 8) writes no separate report; it records the two packet results (late-section detail, `#page=N` spot-check, fixes) in its `1-wiki/log.md` entry (Step 10). Nothing is written under `2-outputs/ingest/`.
- `supersede` (Step 7) records the two packet results in its own log entry (Step 8) alongside the supersession's landed-cleanly checks; no separate ingest report.

Record both packet results. If frames or a non-frame depth purpose were used, include them in the report — not on the source page — so the framing/scope decision is recoverable later.

**Recommended next ingests.** Every report closes with a `Recommended next ingests` section: the papers that would fill a gap *this ingest surfaced* — a single-source page this ingest created or left wanting its primary, a watch item it added, a dangling concept that now warrants its own source, or uningested prior work this source cites and leans on. One entry per paper: author and year, the title, and one line on the gap it fills. This is ingest-derived, not a generic literature dump: list only what this source's gaps actually point to. **Honesty guard (the academic-integrity rule applies):** list only papers you are confident genuinely exist — never fabricate a title, author, or venue, and mark any whose existence you are unsure of `(verify exists)` rather than asserting it. The section is `none` when the ingest surfaced no specific next-source — it is not a quota, so do not pad it.

New-source report shape:

```markdown
---
type: ingest-report
date: YYYY-MM-DD
stem: "{stem}"
frames: []  # one or more frame texts, or empty if unscoped
purpose: "{non-frame depth purpose, or empty}"
---

# Ingest report: {stem}

Touched:

- [[1-wiki/sources/{stem}.md|{stem}]]
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]

## Source-faithfulness packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on metadata, TL;DR, contribution, key claims, evidence pointers, image fidelity.

## Note-quality and coverage packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on one-idea clarity, simple language, source support, image discipline, coverage gaps, intra-page redundancy.

## Fixes applied
- Short bullet per fix made before finalizing (or "none").
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

## Recommended next ingests
- {author year — "Title" — the gap this ingest surfaced that it fills; "(verify exists)" if unsure}, grouped if several. Only papers you are confident exist. "none" when the ingest surfaced no specific next-source.

## Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Existing-source (reingest) report shape:

```markdown
### Source-faithfulness packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/sources/{stem}.md|{stem}]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}

### Note-quality and coverage packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/concepts/self-attention.md|self-attention]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

### Recommended next ingests
- {author year — "Title" — the gap this reingest surfaced that it fills; "(verify exists)" if unsure; "none" when none}. Only papers you are confident exist.

### Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Do not set any touched page to `status: verified`. These packets are the layer-1 authoring safety pass; new and still-draft pages remain `status: draft` until a later `audit` earns `verified` through the Tier-3 independent-refuter gate (Tiered Independent-Refuter Verification above). Pages with a pre-existing status (existing-source mode) keep it unless the approved operation explicitly changes it.
