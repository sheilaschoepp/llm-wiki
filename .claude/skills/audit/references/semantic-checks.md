# audit — Semantic Check Catalogue (Step 4)

The full Critical / Warning / Info catalogue audit runs in Step 4, across all pages (these are cross-page and prose-quality checks needing no raw re-read). Critical = support/faithfulness failures; Warning = the authored-worklist items audit carries out in Step 7; Info = candidates and suggestions.

Critical:

- Concept/entity or synthesis page is unsupported or its listed sources do not actually support it.
- A non-obvious factual claim on a concept/entity/synthesis page (or output) carries no full inline citation in one of the two canonical forms, is cited to a source that does not actually back it, or carries a source-page link alone with no located locator — a bare source link with no locator is incomplete on a non-obvious claim, and so is a citation that names the source but drops where in it. The canonical citation is one of two forms, chosen by sentence grammar, each pairing a source-page wikilink (which source) with a located raw deep-link (where in it): Form 1 — attributive, `[[1-wiki/sources/<stem>.md|<key>]] ([[0-raw/papers/<stem>.pdf#page=N|sec. X, p. M]]) <verb> …`; Form 2 — parenthetical, `… claim ([[1-wiki/sources/<stem>.md|<key>]]; [[0-raw/papers/<stem>.pdf#page=N|sec. X, p. M]]).`. For a PDF the deep-link display always carries both a structural anchor (`sec.`/`app.`/`ch.`/`fig.`/`tab.`/`eq.`) and a printed page (`p. M`), with N the physical PDF page; for a non-PDF, a backticked per-type locator replaces the `#page=N` deep-link. Form 2 is round-bracketed — a citation in the superseded square-bracket form (`[[[<key>]]; [[<loc>]]]`, the triple-bracket `[[[` opener) is a finding; when audit is already authoring or correcting that citation on a page in its fact-check scope, write the round-bracketed form directly (swap the outer literal `[ ]` for `( )`, inner wikilinks unchanged). A standalone `citation_bracket_style` fix on a `verified` page audit is not otherwise touching is lint's to auto-fix and re-stamp, not audit's (SKILL.md Step 7; CLAUDE.md → Page Status lists it among lint's four format fixes). A callout link `[[…#^callout|…]]` is correct only when the claim cites the wiki's own processed judgement, not a place in the raw. On a source page a non-obvious claim follows the source-page rule instead (`CLAUDE.md` → Source page rules): no source-page self-link, but the located raw deep-link still carries the anchor and page in its display — so a correct `Evidence`/`Method` pointer (`p. N` token-as-link, anchor in prose) is not a "bare source link" to flag, and a source-page claim citation missing its anchor is incomplete just as on a concept page (lint cannot backstop this — source pages are exempt from its citation checks). Claim-by-claim support check. Obvious/definitional bullets and the author's own marked judgement (`Appraisal`, `Open Questions`, `Assumptions`) are exempt; a `Disconfirming Evidence` (concept/entity) or synthesis `Tensions` bullet is exempt only when it is a purely own observation with no source — sourced counterevidence in those callouts carries an inline citation like any non-obvious claim. See `CLAUDE.md` → Source Support And Verification.
- A claim misrepresents or misinterprets the source it draws from — overstated, narrowed, over-generalized, or otherwise distorted (claim-by-claim faithfulness check), even when a restated number is correct.
- `needs-update` page has no explanation.
- Source page materially misrepresents raw evidence.

Warning:

- Concept/entity page contains multiple ideas and should be split.
- Concept/entity page is too source-shaped, with source-by-source summary instead of one idea.
- Concept/entity page is too vague, jargon-heavy, or not written in simple language.
- Near-duplicate concept/entity pages should be merged or one redirected.
- A page repeats the same point across two callouts, or within one (intra-page redundancy) — `CLAUDE.md` → Body Sections As Callouts forbids paraphrasing one point across sections. This is the within-PAGE case (distinct from the cross-PAGE near-duplicate above): one section is the right home for the point; drop or merge the other. `lint`'s `intra_page_redundancy` catches the lexical case (high token-overlap) and is on audit's worklist; this semantic pass also catches the point reworded into different words, which the lexical check cannot see. Source pages are exempt (a Key Claim is intentionally re-anchored as a verbatim Evidence quote). When the two bullets are genuinely distinct, leave them.
- A concept/entity page is missing an obvious relationship to a related existing page — especially a cross-paradigm parallel or near-twin that should be a `Connections` or `Not This` link. Run the relationship taxonomy in `.claude/skills/multi-skill/references/relationship-sweep.md` against the inventory (group by functional role, walk same-role concepts across all frameworks/paradigms, not just the page's own). This is connection-graph completeness, not just per-page correctness, and is the half ingest most often misses; a page whose only links are to its own source's pages is the signature. Reciprocal on both pages.
- Cross-page contradiction is not surfaced in `Contradictions` or `Tensions`.
- An existing wiki page is genuinely referenced in prose but not wikilinked (lint's `unlinked_page_mention`, or noticed in the walk) — link every genuine reference, on every occurrence; a page never links to itself. Generic non-reference wording and quoted/verbatim text are exempt.
- A causal, comparative, or evaluative claim asserts a conclusion with no reason or mechanism — the reader cannot follow it. Add the source's stated reason (faithful), recast it as own-voice reasoning, or flag `*[tentative]*`. (A mechanism fabricated and attributed to the source is not this Warning but a Critical faithfulness violation — see the claim-faithfulness Critical above.)
- Source page lacks evidence pointers for details that will matter later.
- Tags drift across related pages.
- Draft page is old enough to review (concrete threshold: `status: draft` and `created:` is 60+ days old).
- Semantic AI-writing tells in a page body. Full source list: `a-archive/style/ai-writing-tells.md` — read at start of audit. Check for:
    - puffing-up tone;
    - "Despite challenges …" conclusion templates;
    - broader-context reflex (tangential generic statements about the field/region/ecosystem);
    - superficial-analysis participial tails ("…, highlighting the enduring legacy of …");
    - elegant variation;
    - fabricated typologies ("there are three main types of X");
    - promotional/travel-guide register.

  The mechanical tells (banned vocabulary, em-dashes, citation-markup leakage) belong in `lint`, not here.

Info:

- *Verified candidate* — looks ready for `status: verified` but audit did not fact-check it against its raw source this run; flag for the next audit.
- *Missing page* — high-value concept/entity page implied by multiple source pages but not yet written.
- *Next source* — suggested next source to close a gap in support; suggest only a source you are confident genuinely exists (never invent a title, author, or venue), and mark an uncertain one `(verify exists)` — CLAUDE.md's no-fabricated-citations rule, the same guard ingest's Recommended next ingests carries.
