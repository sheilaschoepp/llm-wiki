# Design decisions for an Ahrens × Karpathy knowledge base

> Catalogue of every design decision involved in building a knowledge base that combines Ahrens's Zettelkasten discipline with the Karpathy-style LLM-maintained wiki pattern. Each entry lists the choice, the viable options, the trade-offs, what the source material suggests, and which failure modes each option re-opens or closes.
>
> Two source files ground this document: `a-archive/reference/llm-wiki-best-practices.md` (cited as **BP §N**) and `a-archive/reference/smart-notes-summary.md` (cited as **Ahrens ch. N**). Karpathy's primary URLs (gist and X post) are cited where relevant. Specific repos referenced are the ones BP §14 verified.
>
> This file is the design *space*. The companion `smart-notes-llm-wiki-integration.md` picks one position in that space and argues for it. The live wiki in this repo picks another. Other variations — published and unbuilt — also live in this space.

## How to use this file

Each decision has an identifier of the form **D N.K** where N is the part and K is the decision within the part. Read the parts in order on first pass; on later passes, jump directly to the decision identifier referenced from another doc.

When the literature says nothing, that is stated. When the literature is split, both positions are named with their citations.

The decisions are not all independent. Where one decision constrains another, that is flagged inline (e.g., "blocked by D 5.2"). The dependency graph is loose enough that decisions can be made in roughly the order presented.

---

## Part 1. Foundations

The meta-decisions. Every other decision is downstream of these.

### D 1.1 Which framework grounds the design

The substrate the system rests on.

**Options.** Pure Karpathy (LLM-maintained Markdown wiki, no formal Zettelkasten discipline). Pure Ahrens (paper or digital Zettelkasten, no LLM bookkeeping). Hybrid (Ahrens disciplines + Karpathy bookkeeping). Pure RAG (no compiled artefact). Hybrid wiki + RAG (curated wiki layer over a RAG retrieval base).

**Trade-offs.** Pure Karpathy fails when the human stops curating: ingest errors compound, hallucinations bake into "facts", noise accumulates, the wiki recursively cites itself as truth (BP §13). Pure Ahrens fails because the bookkeeping is exhausting; most note-takers drop off at the literature-note → permanent-note → wikilink discipline (Ahrens ch. 1, ch. 14). Hybrid plugs each one's main hole. Pure RAG re-derives every answer from chunks at query time and does not preserve curated reasoning (BP §3). Hybrid wiki + RAG is the right pattern for very large or fast-changing corpora where the wiki alone cannot keep up (BP §13).

**What the literature suggests.** Ahrens (ch. 3) names "any program that allows setting links and tagging (like Evernote or a Wiki)" as acceptable for the slip-box. Karpathy's gist describes the LLM-maintained wiki version of that same idea. The hybrid is what Ahrens looks like once an LLM does the linking, and is the position BP §4 ("the Ahrens grounding") takes.

**Failure modes.** Pure Karpathy re-opens hallucination compounding and recursive self-citation (BP §13). Pure Ahrens re-opens the bookkeeping-fatigue failure that ends most paper Zettelkästen (Ahrens ch. 1). Hybrid closes both, at the cost of two human commit points (D 7.1).

### D 1.2 Whether the human-in-the-loop is load-bearing

Whether the human's cognitive operations are essential to the system or convenience-only.

**Options.** Load-bearing (human writes literature notes, promotes drafts, decides titles and contradictions). Convenience-only (LLM does everything; human reviews when interested). No human (full automation).

**Trade-offs.** Load-bearing preserves Ahrens's elaboration discipline (ch. 5: writing is the medium of thinking; ch. 10: read with a pen) and prevents the wiki accumulating LLM voice. Convenience-only and full automation hit the failure modes BP §13 names (hallucinations, ingest errors compound, noise accumulation, semantic gravity). Load-bearing requires roughly six notes a day of cognitive work plus weekly maintenance review.

**What the literature suggests.** Ahrens ch. 5 is unambiguous: writing is *the* operation that compounds. BP §1 frames the entire pattern as "the human still does the cognitive work, the LLM is restricted to the bookkeeping." BP §13 lists trust / audit failure as the first risk if this is wrong.

**Failure modes.** Convenience-only and full automation re-open all four major failure classes (BP §13). Load-bearing closes them, at the cost of friction.

### D 1.3 What the system is optimized for

The corpus type the wiki is for.

**Options.** Research-first (raw documents are truth, the wiki summarizes and links them). Rationale-first (code is truth, the wiki captures *why* — decisions, gotchas, confidence bands). Structure-first (deterministic ASTs / regexes, no LLM at compile time). Mixed (research plus rationale plus other).

**Trade-offs.** Research-first is Karpathy's baseline; the prompts, validation, and failure modes assume documents as truth. Rationale-first variants pair confidence bands (e.g., 0.8+ for verified versus 0.3–0.5 for draft) with audit-by-yes/no prompts ("I assumed X because I saw Y. Correct?"). Structure-first avoids prompt engineering during compilation entirely and produces deterministic output. Mixed corpora need branch-aware prompts: a research-wiki prompt does not work on a codebase corpus.

**What the literature suggests.** BP §11 names the three branches explicitly and warns against using one branch's prompt shape on another's corpus. Ahrens does not address this — his slip-box is research-first by default.

**Failure modes.** Mismatched branch (e.g., research-first prompts on a code corpus) re-opens the noise-accumulation and semantic-gravity failures (BP §13).

### D 1.4 User scale

The human side of the system.

**Options.** Single-user personal vault. Small team. Enterprise (many users, permissions, audit trail).

**Trade-offs.** Single-user matches Ahrens's original setup and Karpathy's framing (BP §13: "small-to-medium, slow-moving, human-curated research folders"). Multi-user introduces permissions, source-tracking, and cost control problems the published pattern does not solve. Enterprise needs explicit ownership, redaction defaults, and update logic that personal vaults skip.

**What the literature suggests.** BP §13 ("Boundary conditions") flags the pattern as much weaker for multi-user / enterprise. One implementer reported ~$15 to process ~2000 bookmarks for a single user; enterprise costs scale further.

**Failure modes.** Multi-user re-opens version-conflict and overwrite failures unless a sync model is added. Enterprise re-opens privacy / cost concerns.

### D 1.5 Privacy and locality

Where computation and storage live.

**Options.** Local-only (Markdown + Git, local LLM). Cloud LLM (Markdown local, inference remote). Hybrid (local-first with cloud LLM for heavy work). Fully cloud (notes and inference both remote).

**Trade-offs.** Local-only is private and inspectable but capability-limited (small local models, no embedding services). Cloud LLM raises data-handling concerns when notes contain sensitive material. Hybrid is the most common compromise.

**What the literature suggests.** BP §12 cites Markdown / Obsidian / Git praised explicitly because it is inspectable, diffable, and avoids opaque memory layers. Several repos in BP §14 default to local models (`domleca/llm-wiki` ships with `qwen2.5:7b` and `nomic-embed-text`).

**Failure modes.** Cloud-default re-opens privacy failures for sensitive corpora. Local-only re-opens capability ceilings (no embeddings, weaker reasoning) at scale.

### D 1.6 Funding and cost model

How ingest and maintenance get paid for.

**Options.** Free local (no marginal cost per ingest). Personal cloud cap (e.g., monthly LLM budget). Pay-per-ingest. Enterprise plan with usage governance.

**Trade-offs.** Cost scales with corpus size and ingest cadence. The reported $15-for-2000-bookmarks figure (BP §13, unverified) is a useful order-of-magnitude. Cost discipline maps to ingest discipline (D 7.5): bulk-loading is expensive *and* low-quality, so cost is partly self-correcting.

**What the literature suggests.** Not addressed by Ahrens. BP §13 and §17 imply pain-driven escalation: do not optimize cost until the corpus or cadence makes it the bottleneck.

**Failure modes.** No cost model re-opens runaway-ingest failures at corpus scale.

### D 1.7 Standardize-the-environment scope

How aggressively to standardize organizational decisions across the workflow.

**Options.** Minimal (only standardize what causes friction). Moderate (one capture method, one slip-box format, one note-extraction routine). Aggressive (standardize every recurring decision — formats, locations, naming, prompts, cadence). Per-skill standardization only.

**Trade-offs.** Aggressive standardization preserves willpower for content decisions (Ahrens ch. 9 cites Baumeister et al. 1998 on ego depletion). Minimal leaves more flexibility but spends decision capacity on routine. The line: standardize organizational decisions; spend the budget on substance.

**What the literature suggests.** Ahrens ch. 9 ("Reduce decision count... Standardizing the workflow (one notebook, one capture method, one slip-box format, one note-extraction routine) frees decision capacity for the decisions that matter — the content").

**Failure modes.** Minimal re-opens willpower-depletion. Aggressive re-opens the standardize-the-wrong-thing failure where workflow standards calcify around outdated practice.

### D 1.8 Redaction-before-ingest policy

Whether the system pre-redacts sensitive identifiers before persisting raw or wiki content.

**Options.** No redaction (raw and wiki contain whatever the source contained). Default redaction (PII, identifiers, secrets stripped before write). Opt-in redaction per source. Manual review only.

**Trade-offs.** Default redaction matches privacy-by-default principles and is essential at organizational scale. None is fastest but exposes private data in the inspectable Markdown and Git history. Opt-in is a working middle but relies on the user remembering to opt in.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "Design principles: works offline, redaction defaults, idempotency, agent-agnostic, privacy-by-default"). BP §13 (privacy at organizational scale).

**Failure modes.** None re-opens sensitive-data leakage in a Git-tracked repo.

---

## Part 2. Layout

Where things live on disk.

### D 2.1 Folder ordering convention

How top-level folders are named.

**Options.** Prefix-numbered (`0-raw/`, `1-wiki/`, `2-outputs/`, `a-archive/`). Plain names (`raw/`, `wiki/`, `outputs/`). Dot-prefixed (`.raw/`, `.wiki/`). Hidden + Git-tracked (`_raw/`, `_wiki/`).

**Trade-offs.** Prefix-numbered forces a workflow-order sort in Obsidian and most file browsers — the agent and human both see the lifecycle (raw → wiki → outputs → archive) at a glance. Plain names look cleaner but rely on alphabetical sort. Dot-prefixed hides folders by default in some tools.

**What the literature suggests.** Neither source prescribes this. BP §5 uses plain names in the canonical example; the live schema uses prefixes; both work.

**Failure modes.** Plain names re-open the orientation problem when the user opens the vault after a gap and has to remember which folder is the source-of-truth.

### D 2.2 Where raw source material lives

The folder for immutable source-of-truth documents.

**Options.** Top-level `raw/` or `0-raw/`. Embedded inside `wiki/`. Outside the repo (e.g., a Zotero library). Multiple raw folders per source type.

**Trade-offs.** Top-level matches Karpathy's gist and BP §5. Embedded inside `wiki/` collapses the reference-system / slip-box separation Ahrens (ch. 6) treats as load-bearing. Outside the repo means git history does not track sources, and the agent needs cross-volume access. Multiple raw folders (papers / articles / media / other) help when the agent uses different parsers per type.

**What the literature suggests.** BP §11 names the raw types explicitly: "articles, papers, images, data files." Both sources treat raw as the truth layer, untouched by the agent.

**Failure modes.** Embedded raw re-opens the recursive-self-citation failure (BP §13). Outside-repo raw re-opens reproducibility failures across machines.

### D 2.3 Where the wiki lives

The folder for LLM-maintained Markdown.

**Options.** Top-level `wiki/` or `1-wiki/`. Single-folder (no `wiki/` prefix; pages at root). Multi-wiki (per-project or per-domain wikis).

**Trade-offs.** Top-level `wiki/` is the consensus. Single-folder collapses navigation. Multi-wiki recreates Ahrens's mistake #2 (project-only notes) at the wiki level — the slip-box is meant to be cross-project (Ahrens ch. 6).

**What the literature suggests.** BP §5 uses `wiki/`. Ahrens (ch. 6) treats the slip-box as a single durable artefact; one slip-box, many projects.

**Failure modes.** Multi-wiki re-opens Ahrens mistake #2.

### D 2.4 Whether to have an `inbox/` for fleeting notes

The capture surface for pre-decision thoughts.

**Options.** Inbox folder inside the repo, triaged daily. Inbox outside the repo (phone, voice memo, paper). No inbox (capture directly into a draft page). Skip fleeting notes entirely.

**Trade-offs.** In-repo inbox is the BP §5 default and gives the agent a place to *propose* triage. Outside-repo inbox aligns with Ahrens's "anywhere frictionless" guidance (ch. 6) but the agent cannot help triage. No-inbox forces every capture to be a permanent or literature note immediately, which contradicts Ahrens's three-category split.

**What the literature suggests.** Ahrens ch. 6 treats fleeting notes as essential and ch. 14 makes the capture habit the first one to install. BP §5 and §7.1 add the in-repo `inbox/` folder. Both warn against auto-ingesting from the inbox.

**Failure modes.** No inbox re-opens Ahrens mistake #3 (treating all notes as fleeting; piles accumulate). Auto-ingesting from inbox re-opens noise accumulation (BP §13).

### D 2.5 Where project notes live

The folder for project-specific scaffolding.

**Options.** Top-level `projects/` inside the wiki repo. Separate repo. Outside the repo entirely. Embedded inside `wiki/` (rejected by Ahrens; included for completeness).

**Trade-offs.** Top-level inside the repo aids cross-reference but risks ingest contamination if pipeline filters are wrong. Separate repo enforces clean separation but adds friction. Embedded inside `wiki/` violates Ahrens's "different storage for different ideas" rule (ch. 6).

**What the literature suggests.** Ahrens ch. 6 lists project notes as a distinct category, archived or discarded after the project ends. BP §5 puts `projects/` outside `wiki/`.

**Failure modes.** Embedded `projects/` re-opens Ahrens mistake #2 and the project-specific-vocabulary contamination of the slip-box.

### D 2.6 Where archive material lives

Behavioural rules, style guides, lessons, identity facts.

**Options.** Top-level `a-archive/` (or similar). Inside `wiki/` as concept pages. Outside the repo (e.g., `~/.claude/`). Mixed — some inside, some outside.

**Trade-offs.** In-repo means the agent reads it at session start; out-of-repo means rules are shared across projects but updates fragment. Concept pages inside `wiki/` blur archive material with knowledge.

**What the literature suggests.** Neither source addresses this directly. The pattern is downstream of D 5.1 (where the schema lives).

**Failure modes.** Out-of-repo archive re-opens onboarding problems for new agents or new machines.

### D 2.7 Where derived artefacts live

Lint reports, ingest reports, query saves not yet promoted, briefs.

**Options.** Top-level `2-outputs/` or `reports/`. Per-skill subfolders (`outputs/lint/`, `outputs/ingest/`). Per-date subfolders. Inside `wiki/`. No dedicated folder (derived artefacts become wiki pages directly).

**Trade-offs.** Dedicated folder keeps the wiki uncluttered. Per-skill subfolders aid retrieval. Per-date subfolders aid history. Mixing into `wiki/` re-opens noise accumulation.

**What the literature suggests.** BP §5 has `reports/`. Per-skill subfolders are common in the schema-heavy variants (BP §14: NicholasSpisak, Pratiyush).

**Failure modes.** No dedicated folder re-opens noise accumulation.

### D 2.8 Where attachments live

Figures, tables, diagrams, screenshots.

**Options.** Per-source folder (`wiki/attachments/<source-stem>/`). Global `wiki/attachments/`. Co-located with raw (`raw/papers/<source>/figures/`). Inline base64 in the Markdown. External (cloud storage with URL).

**Trade-offs.** Per-source folder is clean and avoids global-namespace collisions but requires unique cross-vault filenames for Obsidian's basename wikilink resolution. Global folder is simpler but collision-prone. Co-located with raw blurs the immutable-raw boundary if attachments are extracted post-hoc. Inline base64 bloats Markdown. External adds a dependency.

**What the literature suggests.** Neither source addresses this in detail. Karpathy's gist suggests "keep images local and describe them textually" (BP §11).

**Failure modes.** Global folder re-opens basename-collision failures in Obsidian. Inline base64 re-opens diff and edit problems.

### D 2.9 Single repo vs multi-repo

Whether everything sits in one git repository.

**Options.** Single repo (raw + wiki + outputs + archive). Multi-repo (raw separate from wiki; or wiki separate from outputs). Per-project repos with a shared submodule.

**Trade-offs.** Single repo is simpler and matches both sources' canonical examples. Multi-repo allows different access controls (e.g., raw private, wiki public) and finer history but adds setup cost.

**What the literature suggests.** BP §5 uses single repo. Multi-repo is implied by the privacy variants in BP §13.

**Failure modes.** Multi-repo re-opens cross-repo synchronization failures.

### D 2.10 Two-slipbox topology

Whether literature notes form a separate indexed system from permanent notes.

**Options.** One-slipbox (literature notes inside `wiki/sources/` as a folder of the main wiki). Two-slipbox (separate bibliographical slip-box paired with the reference manager; permanent notes in the main slip-box). Hybrid (sources folder inside the wiki but with its own index and lifecycle).

**Trade-offs.** One-slipbox is simpler and matches the Karpathy folder layout. Two-slipbox matches Luhmann's actual practice and keeps bibliographic bookkeeping cleanly separated from idea bookkeeping. Hybrid is the working compromise: one repo, two clear lifecycles.

**What the literature suggests.** Ahrens ch. 1.3 ("Luhmann ran two slip-boxes: a bibliographical one (literature notes paired with references) and a main one (permanent notes — his ideas)"). BP §5 folds them into one wiki by default.

**Failure modes.** One-slipbox without clear lifecycle separation re-opens the "literature notes drift into permanent voice" failure that the promotion gate (D 7.7) is meant to catch.

### D 2.11 Project workspace (the "desktop")

Whether the system has a project-specific scratch space for sorting, ordering, and drafting.

**Options.** Dedicated `desktop/` or `drafts/` folder per project. External editor (Obsidian canvas, OneNote, paper). Ad-hoc working files at project root. None — write directly into the manuscript.

**Trade-offs.** Dedicated scratch space lets the user copy notes out of the slip-box, rearrange for one project, and not disturb the slip-box itself. None re-opens the temptation to edit slip-box notes for a project's prose, which contaminates them.

**What the literature suggests.** Ahrens ch. 6 ("The Zettelkasten has built-in project-specific desktops where you can rearrange ideas and conceptualize chapters without touching the slip-box itself"); ch. 13 ("The Zettelkasten's desktop function lets you sort notes for a specific project without disturbing the slip-box").

**Failure modes.** None re-opens slip-box contamination during drafting.

### D 2.12 Cut-prose graveyard

Whether to keep a holding file for prose cut from drafts.

**Options.** Per-project `xy-rest.doc`-style graveyard. Single shared graveyard. Git history alone. None (cut prose is deleted).

**Trade-offs.** A graveyard makes deletion painless ("kill your darlings") because the cut text remains nominally recoverable, even though it almost never gets reused. None re-opens the tendency to leave unnecessary passages in drafts because cutting feels like loss.

**What the literature suggests.** Ahrens ch. 13 ("Ahrens uses the trick of moving cut passages to a separate `xy-rest.doc` — they're never used again, but the pretext that they might be makes deletion painless").

**Failure modes.** None re-opens draft bloat.

---

## Part 3. Page typology

Which kinds of pages exist.

### D 3.1 Which page types to support

The set of permitted `type:` frontmatter values.

**Options.** Source only (literature notes; everything else inline). Source + concept (the floor). Source + concept + entity. Source + concept + synthesis. Full BP set: source, concept, entity, synthesis, question, decision. Custom additions (method, hypothesis, experiment, paper-snippet).

**Trade-offs.** Fewer types means fewer taxonomic decisions per ingest but blurs distinctions; more types means more navigation handles but more rules to remember and more router errors when ingesting.

**What the literature suggests.** Ahrens ch. 6 distinguishes only literature / permanent / project (with main slip-box notes as the permanent sub-type) but emphasizes splitting when categories blur. BP §8 names five (source, concept, entity, synthesis, question, decision) and treats atomicity as non-negotiable. BP §14 shows custom additions in some variants.

**Failure modes.** Source-only re-opens topic-page drift (BP §13). Too many types re-opens taxonomic decision fatigue.

### D 3.2 Concept versus entity split

Whether to keep a separate page type for proper-noun things.

**Options.** Keep separate (concept = abstractions, entity = proper nouns). Merge into one type with a `kind` tag. Merge entirely (everything is concept).

**Trade-offs.** Split aids navigation when entities (people, models, datasets, organisations) recur across many concepts. Merge simplifies the schema. The split fails on cases where a named method is both an idea and an artefact (e.g., "BERT"); a written rule is needed for which folder it lives in.

**What the literature suggests.** BP §8 separates them. Ahrens does not address this — Luhmann's slip-box is uniform.

**Failure modes.** Merge re-opens duplication when the same person has both a "this is who they are" page and a "this is what they did" page.

### D 3.3 Synthesis as a separate type

Whether cross-source claims get their own page type.

**Options.** Separate `synthesis` type (durable cross-source argument pages). Absorb into `concept`. Allow ad-hoc `wiki/syntheses/` only when the user explicitly creates one. None — cross-source claims live inline on concept pages.

**Trade-offs.** Separate type makes cross-source claims discoverable and protects them from being mistaken for single-source concepts. Absorbing into concept loses the distinction. None re-opens recursive-self-citation when a concept page silently aggregates multiple sources without flagging.

**What the literature suggests.** BP §8 names synthesis as one of the five. Ahrens ch. 12 describes "overview-of-a-topic" notes (Schmidt 2013, type 1) that serve the same role.

**Failure modes.** None re-opens recursive-self-citation (BP §13).

### D 3.4 Question and decision types

Whether to formalize saved investigations and reusable choices.

**Options.** Include both. Question only. Decision only. Neither (use ad-hoc concept pages).

**Trade-offs.** Both formalize the "save useful answers back" mechanism that compounds the wiki (BP §7.2). Excluding them forces every reusable answer into concept, which blurs the page type.

**What the literature suggests.** BP §7.4 names the round-trip ("if the answer creates a reusable synthesis, ask whether to save it") as the compounding mechanism. Karpathy's gist mentions saving substantial investigations back. Ahrens does not address this directly; the closest analogue is Luhmann's hub notes (ch. 12).

**Failure modes.** Neither re-opens the lost-investigation failure (the same question gets asked next month and re-derived from scratch).

### D 3.5 Where contradictions live

How disagreements between sources are captured.

**Options.** Per-page `Contradictions` section (callout or H2). Global `contradictions.md`. Both (per-page + global index). Neither (resolve immediately, never preserve).

**Trade-offs.** Per-page is local and contextual. Global is centralized and helps orientation. Both gives discoverability + context. Neither re-opens the smooth-prose-hides-disagreement failure Ahrens spent ch. 12 warning against (paradoxes and oppositions are productive).

**What the literature suggests.** Ahrens ch. 12 (Rothenberg 1971; 1996; 2015) treats contradictions as gold. BP §6 ("preserve both claims under a Contradictions section until resolved"); BP §7.5 ("treat contradictions as first-class objects").

**Failure modes.** Neither re-opens the silent-resolution failure where the LLM picks one side.

### D 3.6 Where gaps and open questions live

Unanswered or unresolved threads.

**Options.** Per-page `Open Questions` section. Global `gaps.md`. Both. Promote to `wiki/questions/<topic>.md` when substantial.

**Trade-offs.** Same shape as D 3.5. Per-page contextual; global aids weekly review.

**What the literature suggests.** BP §5 has `gaps.md`. Ahrens does not name a folder; ch. 11 describes asking "what is *not* mentioned" as the discriminating skill of experienced readers (Lonka 2003).

**Failure modes.** Neither re-opens the lost-thread failure: an open question surfaces, gets ignored at ingest, never returns.

### D 3.7 Atomicity enforcement

How strictly the one-idea-per-page rule is held.

**Options.** Strict (every page must answer "what is the single idea?" at lint time; multi-idea pages get split). Soft guidance (prose rule, no enforcement). None (topic pages allowed).

**Trade-offs.** Strict aids reuse and prevents topic-page drift but increases page count and forces decisions about where an idea breaks. Soft lets pages slowly drift toward topic-pages. None re-creates the failure mode Ahrens spent ch. 6 warning against.

**What the literature suggests.** Ahrens ch. 6 ("one note one idea, one side of paper"). BP §8 ("non-negotiable"). The atomicity rule is the one place both sources are most aligned.

**Failure modes.** Soft and none re-open topic-page drift, navigation collapse, and the failure mode where notes get longer over time without compounding.

### D 3.8 Hub / overview notes

Whether the wiki has dedicated orientation pages that aggregate links to a topic.

**Options.** Hub notes as a distinct page type (e.g., `wiki/hubs/<topic>.md`). Hub notes folded into `wiki/syntheses/`. Hub notes as concept pages with a `kind: hub` tag. None — `index.md` alone serves as orientation.

**Trade-offs.** A distinct hub-note type aids orientation when entering a topic from the index. Folding into syntheses blurs argument pages with orientation pages — Schmidt's type 1 hub notes are orientation, not argument. None re-opens the "index entry-point only points to one note, then the user has to scan" failure.

**What the literature suggests.** Ahrens ch. 12 ("Overview-of-a-topic links. Notes referenced from the index, collecting up to ~25 links to other relevant notes on a topic. Function as entry points and orient you within the slip-box. The topic structure is itself a hypothesis on a note — it can be revised by writing a better overview note and updating the index"). Ahrens ch. 1.3 (Schmidt's type 1).

**Failure modes.** None re-opens orientation collapse for topics with many concept pages.

### D 3.9 Single-source-of-truth derivation rule

Whether wiki pages must derive from one canonical source page rather than from other wiki pages.

**Options.** Strict (every concept / synthesis / question / decision page lists one canonical source page and may not cite other wiki pages as primary support). Soft (wiki pages may cite other wiki pages, but lint flags pages whose only citations are other wiki pages). None (pages cite freely).

**Trade-offs.** Strict prevents recursive self-citation (BP §13: wiki recursively cites itself as truth) and forces every claim back to raw. Soft is the working compromise. None re-opens recursive self-citation.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "schema-heavy fork built around a single-source-of-truth schema: every page derives from one canonical source page, never from another wiki page").

**Failure modes.** Soft and none re-open recursive self-citation (BP §13).

### D 3.10 Disconfirming-evidence capture

Whether the schema includes a mechanism for flagging evidence that cuts against the user's own current hypotheses, distinct from cross-source contradictions.

**Options.** Per-page `Disconfirming` section or callout (Darwin's golden rule, encoded structurally). Frontmatter field (e.g., `disconfirms: [<page>]`). Ingest prompt that asks "what evidence cuts against this?". None — rely on D 3.5 (cross-source contradictions) alone.

**Trade-offs.** A dedicated mechanism institutionalizes Darwin's discipline by giving the user a place to write disconfirming evidence the moment they encounter it (since confirming evidence sticks and disconfirming escapes). None re-opens confirmation bias in the user's own thinking: the user's hypotheses are reinforced silently because counter-evidence is never written down. Distinct from D 3.5: that handles disagreements *between sources*; this handles disagreements *with the user's working hypothesis*.

**What the literature suggests.** Ahrens ch. 10 ("Charles Darwin's golden rule was to write down every fact or argument *opposed* to his theories the moment he encountered them, because confirming evidence sticks and disconfirming evidence escapes... The slip-box institutionalizes Darwin's rule by separating tasks (focus on understanding the text first, evaluate later) and by changing incentives — any *relevant* note enriches the slip-box, regardless of which side of an argument it supports").

**Failure modes.** None re-opens confirmation-bias accumulation in the user's own thinking.

### D 3.11 Self-explanatory permanent-note rule

Whether concept and synthesis pages must read independently of their source pages.

**Options.** Required (the page must read as a standalone idea; lint checks for source-context dependence such as phrases like "as the paper notes" or "in this work"). Recommended but not enforced. None.

**Trade-offs.** Self-explanatory permanent notes survive without their source context, which is what makes them reusable across topics. Pages that depend on the source context become source-summaries in disguise and lose the slip-box's compounding property. Lint can detect dependence with simple regexes.

**What the literature suggests.** Ahrens ch. 6 ("Main slip-box notes. Full sentences. Self-explanatory, so the idea survives without its source context. One idea per note, one side of paper. Written 'as if for print'"); ch. 11 ("Translate them into the context of your own thinking").

**Failure modes.** Recommended-only re-opens the "concept page reads as a paper summary" failure (a sub-class of noise accumulation, BP §13).

---

## Part 4. Page format

What an individual page looks like.

### D 4.1 Body section style

How section structure is rendered.

**Options.** Markdown H2 headings (`## Idea`, `## Why It Matters`). Obsidian callouts (`> [!idea] Idea`). Definition lists. Mixed.

**Trade-offs.** H2 is portable across editors and renderers. Callouts render distinctively in Obsidian (collapsible, styled) but are non-standard Markdown — they degrade in other tools. Definition lists are concise but visually flat.

**What the literature suggests.** Neither source prescribes. The live schema uses Obsidian callouts; the BP reference implementations use H2.

**Failure modes.** Callouts re-open portability failures when content is exported. H2 re-opens visual flatness in Obsidian (no distinct rendering for different section types).

### D 4.2 Required sections per page type

The schema for each page type's body.

**Options.** Minimal (e.g., just summary + sources). Medium (3–5 sections). Maximal (per-type schema with 7–9 required sections, e.g., source pages: tldr / contribution / key-claims / evidence / figures / concepts-entities / contradictions / open-questions / connections). None (freeform).

**Trade-offs.** Maximal aids consistency and lint-ability but creates many empty placeholders. Minimal stays clean but lets pages drift in shape. None makes lint impossible.

**What the literature suggests.** BP §6 implies medium structure but does not enumerate. Ahrens describes the principle (one idea per note, full sentences, explicit references) without prescribing sections.

**Failure modes.** None re-opens shape drift across pages. Maximal re-opens placeholder-padding failures (where empty sections get filled with invented content).

### D 4.3 Filename convention

How page files are named.

**Options.** Kebab-case lowercase (`scaled-dot-product-attention.md`). Snake_case (`scaled_dot_product_attention.md`). Title Case (`Scaled Dot-Product Attention.md`). Freeform. Numeric ID (`21-3d7a7.md`). ID + slug (`21-3d7a7-attention.md`).

**Trade-offs.** Kebab is web-friendly and the modern default. Snake_case is shell-friendly. Title Case looks like prose but breaks on case-insensitive filesystems. Freeform fragments wikilinks. Numeric ID matches Luhmann (ch. 1.3) and survives renames but is cryptic. ID + slug is a common compromise.

**What the literature suggests.** Ahrens ch. 1.3 describes Luhmann's numeric ID scheme (e.g., 21/3d7a7) as a permanent address. BP does not prescribe. The ecosystem (BP §14) leans kebab.

**Failure modes.** Freeform re-opens wikilink fragility. Numeric-only re-opens readability failures (the human cannot guess what the file is).

### D 4.4 Wikilink syntax

How links between pages are written.

**Options.** Basename-only (`[[scaled-dot-product-attention]]`). Path-based (`[[wiki/concepts/scaled-dot-product-attention]]`). Markdown links (`[label](path/to/page.md)`). Mixed.

**Trade-offs.** Basename = simple but requires unique filenames across the entire vault. Path-based = explicit but verbose and breaks if folders move. Markdown links = portable to non-Obsidian tools but lose Obsidian's resolution.

**What the literature suggests.** Neither source prescribes. Obsidian default is basename-only.

**Failure modes.** Basename re-opens collision failures (same filename in two folders). Markdown links re-open broken-link failures on rename.

### D 4.5 Frontmatter shape

Which YAML fields are required, optional, or absent.

**Options.** Minimal (`type`, `title`). Medium (add `sources`, `status`, `last_updated`). Maximal (add `confidence`, `locator`, `aliases`, `tags`, `created`, `frame`, `attachments`, `source_count`, `origin`). Custom additions per page type.

**Trade-offs.** More fields = more structure for lint to check but more maintenance. Some fields (e.g., `frame`) only make sense on certain page types; conditional schemas aid clarity but complicate validation.

**What the literature suggests.** BP §6 sketches a medium-to-maximal frontmatter. Ahrens ch. 6 only requires explicit references.

**Failure modes.** Minimal re-opens lint blindness (the lint script has nothing to check). Maximal re-opens placeholder-padding (empty fields get filled with junk).

### D 4.6 Provenance granularity

How source citations are attached to claims.

**Options.** Page-level only (one `Sources` section at bottom). Per-section (claim groups cite their sources). Per-claim with locator + confidence + date_accessed.

**Trade-offs.** Per-claim catches hallucinations and lets a deterministic validator open each cited path; it adds friction at write time. Page-level is the lightest. Per-section is a middle ground.

**What the literature suggests.** Ahrens ch. 6 requires "explicit references" on each literature note. BP §9 names per-claim as the standard for working implementations. Validator scripts (D 9.4) only work on per-claim.

**Failure modes.** Page-level re-opens the invented-citation failure (the LLM puts a real-looking source URL on a fabricated claim and the page-level bibliography hides it).

### D 4.7 Page size limits

Whether pages have a size cap.

**Options.** None. Soft cap only (e.g., 400 lines). Hard cap only. Both (soft 400, hard 800). Custom values per page type.

**Trade-offs.** Limits enforce atomicity (D 3.7) by forcing splits. No limits let pages bloat into topic-pages and re-open the whole-file edit bottleneck (BP §13). Different page types may justify different limits — source pages can be longer (evidence pointers); concept pages should be shortest.

**What the literature suggests.** BP §8 cites 400 / 800. Ahrens (ch. 1.3) describes Luhmann's "one side of A6 paper" — roughly 100–150 words, far stricter than BP. The literature does not converge.

**Failure modes.** No limits re-open whole-file edit bottleneck and topic-page drift. Too-tight limits re-open over-fragmentation.

### D 4.8 Word and bullet limits

Whether page-level word counts or per-bullet limits apply.

**Options.** Word cap per page type (e.g., concept ≤ 400 words, synthesis ≤ 600). Per-bullet review threshold (e.g., flag bullets over 35 words). None.

**Trade-offs.** Word cap is a softer atomicity signal than line cap. Bullet thresholds catch sentences that should be paragraphs.

**What the literature suggests.** Neither source prescribes word caps. The live schema does.

**Failure modes.** No caps re-opens prose drift.

### D 4.9 Tentative-claim markers

How weak inferences and disputed bullets are flagged.

**Options.** Inline markers (`*[tentative]*`, `*[disputed - see Contradictions]*`). Per-page `confidence` field. Comment annotations. None.

**Trade-offs.** Inline markers are visible at point-of-read but clutter prose. Per-page confidence is structural but loses bullet-level granularity. None re-opens the "claim is presented as fact when it is a guess" failure.

**What the literature suggests.** Neither source prescribes. The pattern is implicit in Ahrens's "explicit references" rule (ch. 6) and BP §9's confidence field.

**Failure modes.** None re-opens overconfident claims.

### D 4.10 Page identifier scheme

The permanent address for a page.

**Options.** Filename only (rename = new identifier). Luhmann-style numeric ID (e.g., 21/3d7a7). Both (ID + slug). Hash. UUID. Sequential integer.

**Trade-offs.** Filename-only is readable but rename-fragile. Numeric ID is permanent but cryptic. ID + slug is the compromise. Hash and UUID are permanent but lose all human readability.

**What the literature suggests.** Ahrens ch. 1.3 documents Luhmann's numeric scheme as a fixed address — branching unbounded (22 → 22a → 22a1 → 22b). BP does not prescribe.

**Failure modes.** Filename-only re-opens wikilink-rot on rename. Numeric-only re-opens search and recall failures.

### D 4.11 Branching scheme

How filing order is encoded.

**Options.** Luhmann-style branching (22 / 22a / 22a1 / 22b — extends the "behind" relationship). Flat with manual links (no positional encoding). Tagged hierarchy (folder = topic). None.

**Trade-offs.** Luhmann-style preserves the "filed behind" semantic that Ahrens names as the load-bearing structural relationship (ch. 6). Flat relies entirely on links. Tagged hierarchy re-creates topic-tree filing — exactly the failure mode Ahrens spent ch. 6 warning against.

**What the literature suggests.** Ahrens ch. 1.3 describes Luhmann's branching. BP does not prescribe; the ecosystem (BP §14) is mostly flat.

**Failure modes.** Tagged hierarchy re-opens topic-tree filing failure. Flat-only re-opens the "lose the filing thread" failure where new pages have no obvious neighbour.

### D 4.12 Cross-reference link types

Whether the wiki distinguishes link kinds.

**Options.** One link kind (plain note-to-note; semantic encoded by where the link appears). Two kinds (overview-of-topic plus plain). Schmidt's four (overview-of-topic, physical-cluster, sequence, plain). Custom (e.g., supports / contradicts / extends).

**Trade-offs.** One kind is simple. Two kinds make hub-note links visible. Schmidt's full four matters in the paper version (types 2 and 3 compensate for paper limits) but only types 1 and 4 survive into the digital version. Custom relation types require lint discipline and are harder to maintain.

**What the literature suggests.** Ahrens ch. 1.3 ("Four cross-reference types... Only types 1 and 4 matter in the digital version; 2 and 3 compensate for paper limits"). Ahrens ch. 12 (type 4 — plain note-to-note — yields the surprising patterns Luhmann was famous for).

**Failure modes.** Custom relation types re-open the "lint must enforce relation semantics" maintenance burden.

### D 4.13 Keyword and tag strategy

How tags are chosen and what they connect to.

**Options.** Content-derived (tags reflect what the note is about). Question-derived (tags reflect the lines of thought the note connects to — "in which circumstances will I want to stumble upon this again?"). Auto-suggested by tooling. None.

**Trade-offs.** Content-derived is automatable but produces obvious-in-context tags that aid little. Question-derived requires thinking time but generates the keywords most likely to surface the note when needed. Auto-suggested usually defaults to content-derived.

**What the literature suggests.** Ahrens ch. 12 ("Index like a writer, not an archivist. An archivist asks 'where do I store this?'; a writer asks 'in which circumstances will I want to stumble upon this again?' Keywords should connect to the questions and lines of thought you're already working on, not the content of the note in isolation. The Zettelkasten suggests keywords automatically from a note's text, but Ahrens warns these are usually the worst options (already obvious in context); good keywords are usually *not* present in the note itself").

**Failure modes.** Content-derived re-opens the "tags are noise" failure where the index fills with keywords that don't surface notes when needed.

### D 4.14 Optimization target: human vs LLM readability

Whether wiki prose is shaped for a human reader (flowing prose) or an LLM reader (dense wikilinks, telegraphic bullets).

**Options.** Human-first (paragraphs, prose, fewer wikilinks per sentence). LLM-first (dense wikilinks, telegraphic bullets, frontmatter-heavy). Hybrid (concept and synthesis pages human-readable; index, log, and folder context files LLM-optimized).

**Trade-offs.** LLM-first packs more relationships into the same token budget, which matters when the agent reads the wiki at session start (D 5.9). Human-first reads better when browsing in Obsidian. Hybrid is the working compromise: optimize the high-frequency-read files (index, hot.md, _context.md) for the agent; optimize the durable-thinking files (concepts, syntheses) for the human.

**What the literature suggests.** BP §12 ("a MindStudio blog post... reframes the wiki as optimised for *model* reading more than human browsing — useful intuition, because it explains why dense wikilinks beat prose summaries even when the prose looks nicer to a human reader").

**Failure modes.** Human-first across the board re-opens the "session start reads too much prose" failure for the agent. LLM-first across the board re-opens the "I can't read my own wiki" failure for the human.

### D 4.15 Hub-note link-density cap

Whether hub and overview notes (D 3.8) have a soft cap on the number of links they hold before the topic should be split.

**Options.** Soft cap at ~25 links (Luhmann's actual practice; lint warns but does not block). Hard cap. No cap. Cap by sub-cluster density (split when one sub-cluster exceeds half of the parent's links).

**Trade-offs.** A cap forces topic splits and prevents hub notes from drifting into topic-pages — the failure mode Ahrens spent ch. 6 warning against. No cap re-opens hub-as-directory drift. Hard caps can be surprising; soft caps with lint warnings are the standard pattern.

**What the literature suggests.** Ahrens ch. 12 ("Overview-of-a-topic links... collecting up to ~25 links to other relevant notes on a topic. Function as entry points and orient you within the slip-box. The topic structure is itself a hypothesis on a note — it can be revised by writing a better overview note and updating the index").

**Failure modes.** No cap re-opens hub-as-directory failure even when hub notes are properly typed (D 3.8).

---

## Part 5. Schema and operating contract

The agent's instructions.

### D 5.1 Where the schema lives

The file the agent reads to learn the rules.

**Options.** Single `CLAUDE.md`. Single `AGENTS.md`. Single `SCHEMA.md`. Split (CLAUDE.md = behavioural rules; SCHEMA.md = page schemas; per-skill files = operations). Hierarchical (per-folder `_context.md`).

**Trade-offs.** Single file is simple but balloons over time, costing context every session. Split saves context but creates router errors when the agent picks the wrong skill on ambiguous requests. Hierarchical aids navigation in large vaults but multiplies files.

**What the literature suggests.** BP §6 is explicit: split. The community converged on this after monolithic files reached 300+ lines. The sweet spot is "short global rules plus a few clearly named skills with explicit *when not to use this skill* guidance."

**Failure modes.** Single file re-opens context-bloat and slow session start. Over-split re-opens router errors (BP §13).

### D 5.2 Skill files: inline vs separate

Where the agent's operations are defined.

**Options.** Inline in the schema file. Separate skill files in `.claude/skills/<name>/SKILL.md`. Separate plus shared scripts. Mixed.

**Trade-offs.** Inline keeps everything visible in one place but bloats the schema. Separate skill files match the Anthropic skill convention and let each skill be loaded only when invoked. Shared scripts (Python helpers) make deterministic checks cheap and reusable.

**What the literature suggests.** BP §14 lists multiple skill-pack repos (kfchou/wiki-skills with six skills; Astro-Han/karpathy-llm-wiki single-skill; SamurAIGPT helpers). The live wiki uses separate skill files with shared scripts.

**Failure modes.** Inline re-opens context-bloat. Separate-only re-opens duplication if shared logic is not extracted.

### D 5.3 Number of skills

How many distinct skills the agent has.

**Options.** One monolithic skill. Few (5–7, kfchou-style). Medium (10–15). Many (16–25, OmegaWiki-style). Very many (with sub-skills).

**Trade-offs.** Few = simple but each skill does a lot. Many = each skill is focused but the router has to disambiguate. The sweet spot from BP §6 is "a few clearly named skills with explicit when-not-to-use guidance."

**What the literature suggests.** BP §14 spans the range (kfchou 6, this wiki ~16, skyllwt ~23). BP §6 warns against over-splitting.

**Failure modes.** Monolithic re-opens context-bloat. Very many re-opens router-error failures.

### D 5.4 Severity vocabulary

How report findings are graded.

**Options.** One set across all reports (e.g., `error / warning / info`). Split by audience (`critical / warning / info` for wiki-facing reports; `error / warning / suggestion` for skill-facing reports, matching Anthropic's skill-authoring convention). Custom per skill.

**Trade-offs.** One set is simpler but reads oddly when "error" is used for "this skill is broken" alongside "error" for "this wiki page is wrong." Split matches different audiences but means readers learn two vocabularies.

**What the literature suggests.** Neither source prescribes. The split is downstream of D 1.3 (what the system is for) — codebases tend to use error/warning/suggestion; research wikis lean toward critical/warning/info.

**Failure modes.** One set re-opens semantic-collision (the same word means different things in different reports).

### D 5.5 Status field values

The states a page can be in.

**Options.** Minimal: active / draft. Standard: draft / active / superseded. Extended: draft / needs_update / verified / superseded / archived. Custom per page type.

**Trade-offs.** More states = finer signal but more transitions to manage. `verified` is useful when an audit is meaningful; without an audit pass it is empty signal. `needs_update` is useful when contradictions are surfaced; without a workflow to clear it, pages get stuck.

**What the literature suggests.** BP §6 names draft / active / superseded. BP §13 (memory lifecycle) requires `superseded`. Ahrens does not address.

**Failure modes.** Minimal (no superseded) re-opens the memory-lifecycle failure (BP §13: old claims rot into permanent context). Too many states re-open transition-management failures.

### D 5.6 Confidence field

How uncertainty is encoded.

**Options.** Numeric (0.0–1.0). Categorical (low / medium / high). Bands (e.g., 0.8+ = verified, 0.3–0.5 = draft). None.

**Trade-offs.** Numeric is precise but spurious — there is no calibration mechanism for "0.74". Categorical maps to human judgement. Bands pair with status (D 5.5). None re-opens overconfidence.

**What the literature suggests.** BP §6 names categorical (low / medium / high). BP §11 cites rationale-first variants using bands. Ahrens does not address.

**Failure modes.** None re-opens overconfidence.

### D 5.7 Operating-rule enforcement style

How non-negotiables are kept.

**Options.** Prose-only (rules in CLAUDE.md, agent obeys). Prose plus lint scripts (deterministic checks catch violations). Prose plus runtime guardrails (e.g., `chmod -w` on raw to prevent writes). Structural (rename misleading fields, rejecting invalid frontmatter at write time, validators).

**Trade-offs.** Prose is cheap but easy for the agent to ignore on edge cases ("semantic gravity," BP §13). Lint catches violations after the fact. Runtime guardrails prevent the violation. Structural prevents the failure mode that would have caused the violation.

**What the literature suggests.** BP §13 explicitly: "raw is immutable" is often only prose, not enforcement; fix is runtime guardrails. BP §16 rule 1: "enforce at runtime, not just in prose."

**Failure modes.** Prose-only re-opens raw-source-safety failures and semantic-gravity failures.

### D 5.8 Mechanical-edit policy

What the agent may change without approval.

**Options.** All edits require approval. Mechanical edits unsupervised (`updated:` fields, index entries, log entries, source_count rolls). Substantive content unsupervised. Everything unsupervised.

**Trade-offs.** All-approval slows everything. Mechanical-only is the standard middle (BP §7.5: lint reports only, fixes nothing without approval). Substantive unsupervised re-opens noise and hallucination compounding.

**What the literature suggests.** BP §7.5 names the cadence (report-only for lint). Ahrens's discipline is upstream: substantive content is the human's job.

**Failure modes.** Substantive unsupervised re-opens all four major failure classes (BP §13).

### D 5.9 Read-orientation requirement

Which files the agent must read at the start of a session or operation.

**Options.** Schema only. Schema + index. Schema + index + log. Schema + index + log + hot.md + folder _context.md (most aggressive). Custom per skill.

**Trade-offs.** Aggressive read-orientation costs context every session but prevents the "agent answers from model memory" failure. Schema-only is light but loses orientation across sessions.

**What the literature suggests.** BP §7.4 names the most aggressive: "read hot.md, index.md, and any folder _context.md files first." BP §17 ranks "model is not forced to read index.md, log.md, and relevant pages before answering" as one of the top reasons implementations fail.

**Failure modes.** Schema-only re-opens model-memory answers and continuity loss across sessions.

### D 5.10 Touch budget per operation

Whether the agent has an upper bound on files modified per operation.

**Options.** No budget. Soft budget (warn beyond N files). Hard budget (refuse beyond N files; e.g., ≤15). Per-skill budgets. Stricter caps in unattended mode.

**Trade-offs.** A hard budget limits cascade damage when the agent goes wrong (e.g., a botched supersede that rewrites half the wiki). No budget re-opens runaway-agent failures, especially in unattended runs.

**What the literature suggests.** BP §14 (`maeste/my-2nd-brain`: "a touch budget of ≤15 files per operation with unattended-mode restrictions — limits cascade damage when the agent goes wrong").

**Failure modes.** No budget re-opens cascade-damage failures.

### D 5.11 Rollback and quarantine policy

How removed and overwritten content is preserved.

**Options.** System-wide quarantine on every removal or overwrite (move to `quarantined/` or `superseded/`). Quarantine only on `forget` and `supersede` operations. Rely on git history alone. None.

**Trade-offs.** System-wide quarantine makes recovery cheap and gives the agent a place to write rejected drafts without polluting the wiki. Git-only re-opens the "no in-vault marker that the page once existed" failure (the user has to know to look at git). None re-opens audit-trail loss.

**What the literature suggests.** BP §13 ("Raw-source safety... quarantine overwrites, make non-AI sync adapters opt-in"; "easy rollback" as a fix for ingest-error compounding).

**Failure modes.** None re-opens audit-trail loss. Git-only re-opens silent-removal failures.

### D 5.12 Sync-adapter and external-write policy on raw

Whether non-LLM tools (Dropbox, iCloud, rsync, file-sync apps) are allowed to write to raw or wiki, and how silent ingest of an unintended corpus is prevented. Distinct from D 5.7, which covers agent writes.

**Options.** No external writes (only the agent and the human via filesystem can change files; sync tools blocked). Opt-in adapters (named tools allowed; everything else rejected at runtime). All sync allowed (default — files move silently into raw whenever the sync runs). Quarantine on unexpected writes (allow but flag for review).

**Trade-offs.** No-external-writes is the most defensive but blocks legitimate workflows like syncing PDFs from a tablet. Opt-in adapters are the working middle. All-allowed re-opens the "sync tool dumped 200 unintended files into raw and the agent ingested them" failure.

**What the literature suggests.** BP §13 (Raw-source safety): "'raw is immutable' is often only prose, not enforcement. Sync tools can overwrite history or silently ingest the wrong corpus. Fix: runtime immutability guardrails (e.g., chmod -w), quarantine overwrites, make non-AI sync adapters opt-in."

**Failure modes.** All-allowed re-opens silent-corpus-corruption failures.

### D 5.13 Index and log update policy

When `wiki/index.md` and `wiki/log.md` get updated.

**Options.** Required on every write (every page change touches index and log). Batched (updates accumulate and flush periodically). Deferred (a separate skill rebuilds index and log from page metadata). Optional (the agent updates them when convenient).

**Trade-offs.** Required-on-every-write is the BP-canonical operating rule and keeps the orientation files always-current, at the cost of two extra file edits per operation. Batched / deferred update reduces write cost but re-opens the "agent reads stale index at session start" failure (D 5.9). Optional re-opens drift entirely.

**What the literature suggests.** BP §6 ("every write updates `index.md` and `log.md`" — listed as a non-negotiable operating rule). BP §7.2 step 9. BP §16 rule 6 (log coverage as a health check). BP §18.1 system-prompt skeleton ("Every writing operation updates wiki/index.md and wiki/log.md").

**Failure modes.** Optional re-opens orientation drift; agent answers from a stale picture of the wiki.

---

## Part 6. Memory tiers

How persistent context is layered.

### D 6.1 Number of tiers

How many distinct memory files the agent reads.

**Options.** One (CLAUDE.md only). Two (CLAUDE.md + MEMORY.md). Three (CLAUDE.md + MEMORY.md + lessons.md). More (per-project hot caches, per-domain context files, etc.).

**Trade-offs.** More tiers = better separation of stable vs volatile vs corrective context, but more places to update and more session-start cost. One tier collapses everything into the schema and re-opens the monolithic-CLAUDE.md failure (BP §6).

**What the literature suggests.** BP §6 implies two (rules + skills). BP §14 (`Pratiyush/llm-wiki`) adds per-project `hot.md` plus `MEMORY.md` plus `CRITICAL_FACTS.md`. Ahrens does not address.

**Failure modes.** One tier re-opens monolithic-schema failures. Many tiers re-open update-fragmentation failures.

### D 6.2 What each tier holds

The contract for each memory file.

**Options.** Schema-only in CLAUDE.md, identity in MEMORY.md, corrections in lessons.md. Or any other split.

**Trade-offs.** This is the entire design point of D 6.1; getting it wrong leads to the same fact appearing in multiple tiers.

**What the literature suggests.** BP does not prescribe a tier-content split. Ahrens does not address.

**Failure modes.** Wrong split re-opens duplication and contradiction across memory files.

### D 6.3 Who can write each tier

Edit permissions per tier.

**Options.** Agent writes all. User writes all. Mixed (agent writes some, user writes others). Soft read-only (agent edits only on explicit instruction).

**Trade-offs.** Agent-only is fast but loses oversight. User-only is principled but slow. Mixed lets the agent maintain volatile state while the human owns the durable rules. Soft read-only is the convention for files that need to remain stable.

**What the literature suggests.** Neither source prescribes. The pattern is downstream of D 1.2 (human-in-the-loop).

**Failure modes.** Agent-only re-opens the silent-rule-rewriting failure where the agent edits its own rules. User-only re-opens stale-state failures.

### D 6.4 Graduation path

How a correction in one tier becomes a stable rule in another.

**Options.** Explicit (lessons → memory → schema, with criteria). Implicit (review periodically, manually move). None (each tier is independent and grows).

**Trade-offs.** Explicit prevents `lessons.md` from growing forever. Implicit is simpler but lets the lessons file accumulate. None re-opens the "everything is a lesson" failure.

**What the literature suggests.** Neither source addresses. The graduation pattern is an extrapolation of Ahrens's "permanent notes are kept; fleeting notes are trashed" rule (ch. 6).

**Failure modes.** None re-opens lesson accumulation. Explicit re-opens the cost of running graduation reviews.

### D 6.5 Hot caches

Short orientation files that survive across sessions.

**Options.** Single global `hot.md`. Per-project `hot.md` (one per project rather than a single global file). Per-domain. None.

**Trade-offs.** Global aids continuity across sessions but conflates projects. Per-project aids project-switching but multiplies files. None re-opens cold-start cost every session.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`) uses per-project. BP §7.4 names a single `hot.md` as the default in the canonical example.

**Failure modes.** None re-opens cold-start cost.

### D 6.6 Folder context files

Per-folder agent guidance.

**Options.** `_context.md` in every folder. Only where needed. None.

**Trade-offs.** Per-folder context aids agent orientation when navigating a large vault. Maintaining many context files is expensive and they become stale.

**What the literature suggests.** BP §7.4 names the read-orientation pattern (read folder `_context.md` files first if present).

**Failure modes.** None re-opens the agent-getting-lost failure in deep folder trees. Many re-open staleness.

### D 6.7 Operational size caps for memory and log files

Whether memory tiers and the log have runtime size caps with archive policies.

**Options.** No caps (files grow indefinitely). Soft caps (warn at threshold). Hard caps with auto-archive (e.g., 50 KB log auto-archive, 200-line memory cap, folder-context threshold). Per-tier caps.

**Trade-offs.** Caps prevent context-bloat when the agent reads memory at session start. Archive policy preserves history for audit. No caps re-open slow session start as files grow over months of use.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "Documented operational defaults: 50 KB log auto-archive, 200-line memory cap, folder-context threshold for `_context.md`").

**Failure modes.** No caps re-open session-start cost.

### D 6.8 Pinned critical-context tier

Whether to add a separate always-read file for facts that must never be overlooked, distinct from stable identity memory and session-orientation hot caches.

**Options.** Add `CRITICAL_FACTS.md` (always read at session start, separate from `MEMORY.md` and `hot.md`). Fold critical facts into `MEMORY.md`. Fold into the schema (`CLAUDE.md`). None.

**Trade-offs.** A pinned tier ensures critical facts get attention at session start, separate from the high-volume orientation context (`hot.md`) that may scroll past. Folding into `MEMORY.md` works but critical facts compete with stable identity for attention. Folding into the schema bloats the schema with project-specific data.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "per-project `hot.md` hot caches, `MEMORY.md`, `CRITICAL_FACTS.md`, cross-session memory") — one of the most-developed published memory-tier patterns.

**Failure modes.** None re-opens the "agent overlooks a critical fact buried in `MEMORY.md` or `hot.md`" failure.

---

## Part 7. Workflow and commit points

The cycle and where the human enters it.

### D 7.1 Number of human commit points

How many places the human must approve before the wiki state changes.

**Options.** Zero (full automation). One (e.g., approve each ingest as a unit). Two (triage + promotion). Three or more (triage + promotion + synthesis approval + supersession + forget).

**Trade-offs.** More commit points = more discipline preserved, more friction. Fewer = faster but more drift. Zero re-opens all four major failure classes (BP §13).

**What the literature suggests.** BP §7 names the four-stage cycle (capture → ingest → maintain → query → save back) with explicit hard rules about what the LLM may and may not do at each stage. BP §7.3 makes promotion *the* second commit point. Ahrens ch. 5 grounds the principle: writing is the cognitive operation that compounds, so the operations that *would* be writing must be human.

**Failure modes.** Zero re-opens trust / audit, ingest-error compounding, noise accumulation, semantic gravity. More than three re-opens approval fatigue.

### D 7.2 Where commit points sit

Which operations require approval.

**Options.** Triage (daily inbox sweep). Promotion (draft → active). Synthesis approval (cross-source page committed). Supersession (one source replaces another). Forget (page or trail removed). Title and tag commits.

**Trade-offs.** Each commit point closes a specific failure class. Triage closes Ahrens mistake #3 (treating all notes as fleeting). Promotion closes ingest-error compounding. Synthesis approval closes hallucination on cross-source claims. Supersession closes the silent-stale failure. Forget protects the audit trail.

**What the literature suggests.** BP §7 implies all five. Ahrens names triage and promotion explicitly (ch. 6).

**Failure modes.** Each missing commit point re-opens its corresponding failure.

### D 7.3 Ingest staging

How an ingest run is structured.

**Options.** Single-pass (LLM reads source, writes pages, done). Staged with takeaway approval (read → propose 5–8 takeaways → pause for human → write). Multi-pass (takeaways → outline → pages → verification packets). Deep ingest with multiple verification packets.

**Trade-offs.** Single-pass is fast but compounds errors and hides them. Staged catches mistakes at the cheapest stage. Multi-pass thorough but slower. Deep ingest with verification is the most defensive — useful for load-bearing sources.

**What the literature suggests.** BP §7.2 names staged with takeaway approval as the default ("the discuss takeaways before writing step is what protects the wiki"). The deep variant is implicit in the "ingest-deep" / "reingest" pattern.

**Failure modes.** Single-pass re-opens ingest-error compounding (BP §13).

### D 7.4 Takeaway count

How many candidate takeaways the LLM proposes during ingest.

**Options.** 3–5 (kfchou). 5–8 (Karpathy-help diagnosis). Freely chosen by the model. Variable per source length.

**Trade-offs.** Too few drops material; too many dilutes; freely chosen drifts and produces inconsistent ingests across sources.

**What the literature suggests.** BP §7.2 names the disagreement explicitly (kfchou 3–5; Karpathy-help 5–8) and recommends picking a number for your skill file rather than leaving it to the model.

**Failure modes.** Freely chosen re-opens the inconsistency failure across ingests.

### D 7.5 Ingest batch size

How many sources go through the pipeline together.

**Options.** One source at a time. Small batches (5–10). Larger batches (10–20). Bulk (50+).

**Trade-offs.** Bulk produces low-signal noise and overwhelms the human commit points. Small batches enforce discipline but slow down corpus migration. One-at-a-time is the safest and Ahrens's default (he treats each note as one unit, ch. 11).

**What the literature suggests.** BP §7.2 (first invariant): "Stop dumping too many sources at once. Curated batches of 10–20 sources from one domain." Ahrens ch. 11.4 describes filing one note at a time.

**Failure modes.** Bulk re-opens noise accumulation and overwhelms triage.

### D 7.6 Verification packets

How an ingest is checked before being declared complete.

**Options.** Zero (just write the pages and stop). One (any kind of post-write check). Two-packet (source-faithfulness + note-quality, run independently). Multi-packet. Subagent-isolated (each packet by a separate agent).

**Trade-offs.** More packets = more reliability but more cost. Subagent isolation prevents one packet's drift from contaminating another's. The cost is ingest latency.

**What the literature suggests.** BP does not prescribe verification packets explicitly. The two-packet pattern is in the live schema; the principle (independent checks) appears in BP §9 (validator scripts) and §17 (claim-bearing JSON runners).

**Failure modes.** Zero re-opens ingest-error compounding. Many re-opens cost.

### D 7.7 Promotion gating

How the draft → active transition happens.

**Options.** Full manual (human re-voices each draft, flips status). Auto-promote after delay (e.g., 14 days idle). Auto-promote with manual override. Auto-promote with confidence threshold (e.g., confidence high → auto-promote).

**Trade-offs.** Manual preserves Ahrens's elaboration discipline (ch. 5) — the human paraphrases, which forces understanding. Any form of auto-promotion bypasses that operation and the wiki accumulates LLM voice. The friction is intentional.

**What the literature suggests.** BP §7.3 is explicit: "LLM-drafted concept pages stay at status: draft until the human re-voices them and promotes to status: active." Ahrens ch. 5 grounds the principle.

**Failure modes.** Auto-promote re-opens noise accumulation, AI-writing-tells contamination, and the failure mode where the slip-box stops being a thinking tool.

### D 7.8 Frame for ingest

Whether ingest is run with a stated angle or scope.

**Options.** No frame (ingest is comprehensive within the source). Explicit frame text saved in frontmatter. Multiple frames per source (separate ingest runs with different frames).

**Trade-offs.** No frame is comprehensive but unfocused. Explicit frame is scoped and lets the source page omit out-of-frame material faithfully — but only if the frame is recorded so a future reingest can reuse it. Multiple frames create duplication.

**What the literature suggests.** Neither source addresses framing directly. Ahrens ch. 6 ("be extremely selective") implies framing in spirit.

**Failure modes.** No frame re-opens ingest bloat for long sources. Frame without recording re-opens reingest contradiction.

### D 7.9 Save-answers-back

What happens to substantial query answers.

**Options.** Always offer to save (human accepts or discards). Offer when threshold met (length, multi-source, reuse-likely). Never offer. Auto-save every answer.

**Trade-offs.** Always offer is the BP §7.2 third invariant. Auto-save re-opens noise accumulation. Never offer re-opens the lost-investigation failure.

**What the literature suggests.** BP §7.2: "Save useful answers back into the wiki" — substantial investigations become `wiki/questions/<topic>.md` or `wiki/syntheses/<topic>.md`. The round-trip is the compounding mechanism.

**Failure modes.** Never offer re-opens the lost-investigation failure. Auto-save re-opens noise.

### D 7.10 Query grounding rules

What the agent is allowed to do when answering.

**Options.** Read wiki only. Read wiki first, then raw if needed. Read raw freely. Require citations on every claim. Exclude drafts by default. Forbid model-memory answers.

**Trade-offs.** Aggressive grounding (read wiki first, cite, exclude drafts, forbid memory) prevents hallucinations but requires the wiki to actually have the answer. Loose grounding is faster but re-opens hallucination.

**What the literature suggests.** BP §7.4 names the most aggressive set: read hot.md → index.md → folder _context.md first; answer from wiki first; cite exact pages; do not answer from model memory; exclude status: draft pages by default.

**Failure modes.** Loose grounding re-opens hallucinations and recursive self-citation.

### D 7.11 Translation rule for source pages

Whether the source-page draft must be paraphrased in the user's voice or may include extracted text.

**Options.** Strict translation (paraphrase only; direct quotes only with quotation marks plus locator). Mixed (extraction allowed verbatim where wording matters; paraphrase otherwise). Extraction-friendly (the LLM may copy text verbatim into the source page).

**Trade-offs.** Strict translation forces the cognitive operation Ahrens names as the difference between "having read" and "having understood" (ch. 10). Extraction-friendly is fast but the source page does not pass the test for understanding. The promotion gate (D 7.7) catches this for concept pages but not for source pages, which is why the rule belongs at ingest time.

**What the literature suggests.** Ahrens ch. 1.3 ("Translation, not copying... Copy-paste keeps the idea trapped in its original context. Translation preserves meaning while changing form, and the change of form is what makes the idea reusable elsewhere"). Ahrens ch. 10 ("Read with a pen. Don't copy ideas; translate them into the context of your own thinking"). BP §7.2 step 5 ("paraphrased, in the user's voice").

**Failure modes.** Extraction-friendly re-opens the "read but not understood" failure on source pages, which propagates downstream into every concept page derived from them.

### D 7.12 Ingest queueing and retry policy

How the ingest pipeline handles partial failures and re-runs.

**Options.** Synchronous (one source at a time, no caching, no retries). Serial queue with content caching (e.g., SHA-256 of source body) and bounded retries (e.g., up to three). Parallel queue. Manual retry only.

**Trade-offs.** Serial queue with caching and bounded retries handles partial failures cleanly: if the LLM fails partway through an ingest, the cached content lets the next attempt resume rather than re-pay the read cost. Parallel re-opens race conditions on `index.md` and `log.md`. Synchronous re-opens partial-state corruption when an ingest fails mid-write.

**What the literature suggests.** BP §7.2 second invariant ("Serialize ingest with retries and content caching. SHA-256 caching, a serial queue, up to three retries, a guaranteed source-summary step").

**Failure modes.** Synchronous re-opens partial-state corruption. Parallel re-opens race conditions.

### D 7.13 Audit prompt style

Whether the agent uses constrained or open-ended prompts when reviewing its own work.

**Options.** Open-ended elicitation ("explain your reasoning"). Yes/no audit prompts ("I assumed X because I saw Y. Correct?"). Mixed.

**Trade-offs.** Yes/no forces the agent to expose its reasoning before drift accumulates and lets the human reject quickly. Open-ended is conversational but lets the agent rationalize. The yes/no pattern is most useful in rationale-first variants where the wiki captures *why* rather than *what*, but generalizes.

**What the literature suggests.** BP §11 ("the human-audit prompt of the form 'I assumed X because I saw Y. Correct?' — yes/no rather than open-ended elicitation, which forces the agent to expose its reasoning before drift accumulates").

**Failure modes.** Open-ended re-opens rationalization failures (the agent justifies its drift instead of exposing it).

### D 7.14 Re-verification trigger on source change

When wiki pages get re-checked after their source changes.

**Options.** On-demand only (user runs `reingest`). Scheduled re-verification (every N days). Change-triggered (`docs-check` re-runs when relevant code or source changes). Continuous.

**Trade-offs.** Change-triggered is the most defensive: when the source changes, derived pages get re-checked automatically. On-demand re-opens the silent-stale failure. Scheduled wastes effort on unchanged sources. Continuous is most expensive.

**What the literature suggests.** BP §11 (`tuandm/code-wiki`: "`docs-check` re-verification on relevant code changes"). The pattern is most useful in rationale-first variants but generalizes.

**Failure modes.** On-demand re-opens silent-stale failures.

### D 7.15 Idempotency of ingest

Whether re-running ingest on the same source produces identical output.

**Options.** Idempotent (deterministic — same input, same output, every time). Non-idempotent (LLM choices vary across runs; default for any LLM-driven pipeline). Mixed (frontmatter and structural fields are deterministic; prose may vary).

**Trade-offs.** Idempotent ingest plays well with content caching (D 7.12) and lets the user trust that re-running ingest after a crash produces the same wiki. Non-idempotent is the LLM default and produces drift across re-ingests, which undermines retry policies. Mixed is the working compromise.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "Design principles: works offline, redaction defaults, idempotency, agent-agnostic, privacy-by-default"). BP §7.2 second invariant ("SHA-256 caching") implies content-keyed reproducibility.

**Failure modes.** Non-idempotent re-opens "re-ingest produces a different wiki page than the first ingest" failures, which break the content-cache assumption.

### D 7.16 Watch / continuous-ingest mode

Whether the agent runs a daemon that detects new raw files and auto-triggers ingest.

**Options.** Manual only (user invokes `ingest <path>`). Watch mode (daemon polls or uses filesystem events; auto-triggers on new files). Scheduled (every N minutes / hours). Hybrid (watch with manual confirmation step).

**Trade-offs.** Watch mode reduces friction at scale. Manual preserves the human commit point at the start of every ingest, which the discipline depends on (D 7.1). Watch mode breaks the discipline if it bypasses takeaway approval (D 7.3); hybrid keeps the commit point but eliminates the "remember to run ingest" step.

**What the literature suggests.** BP §14 (`swarmclawai/swarmvault`: "context build, graph validate --strict, shrink guards, export/serve, watch mode").

**Failure modes.** Watch mode without a takeaway-approval gate re-opens silent-ingest failures.

### D 7.17 Duplicate-handling policy at write time

What the agent does when ingest or page creation could produce a near-duplicate of an existing page.

**Options.** Prefer-update (the agent updates the existing page rather than creating a new one). Always-create (allow duplicates; lint catches them later). Surface for human decision (the agent flags and pauses). Auto-merge (the agent merges silently).

**Trade-offs.** Prefer-update keeps the wiki clean and prevents the duplicate-concept-pages failure mode (BP §13 names duplicates as a normal failure). Always-create is fast but accumulates duplicates that need lint to clean up. Auto-merge re-opens the silent-content-loss failure when the agent merges incorrectly.

**What the literature suggests.** BP §6 (operating rule, listed among non-negotiables): "Prefer updating an existing page over creating a near-duplicate." BP §13 ("Memory lifecycle... Duplicate concepts and entities are a normal failure mode. Prefer merging or updating once noticed").

**Failure modes.** Always-create re-opens duplicate accumulation. Auto-merge re-opens silent-content-loss.

### D 7.18 Link placement: human vs LLM vs hybrid

Who writes the wikilinks between pages, and at what stage of the workflow.

**Options.** LLM-only (the agent proposes and writes all links during ingest and maintenance). Human-only (every wikilink is written by the human). Hybrid (LLM proposes during ingest; human accepts or revises at promotion). Stage-split (LLM writes structural backlinks; human writes substantive cross-references).

**Trade-offs.** LLM-only is the load-bearing separation BP §1 names ("the LLM is restricted to the bookkeeping (linking, indexing, formatting, lint)") — but the LLM tends toward obvious links. Human-only matches Luhmann's actual practice (Ahrens ch. 1.3 — Luhmann placed every link by hand) and catches the non-obvious connections that yield surprising patterns, but defeats the LLM's main contribution. Hybrid is the working compromise, separating mechanical links (LLM) from substantive cross-references (human).

**What the literature suggests.** BP §1 frames linking as bookkeeping the LLM should handle. Ahrens ch. 1.3 describes Luhmann placing every link by hand. Ahrens ch. 12 ("Good cross-referencing is itself a thinking task") — which puts the human back in the loop for the most consequential links.

**Failure modes.** LLM-only re-opens the "important non-obvious connections never get made" failure (the LLM tends toward obvious links). Human-only re-opens the bookkeeping-fatigue failure that the LLM is meant to absorb.

### D 7.19 Bottom-up vs top-down topic-selection policy

Whether the workflow allows user-declared topics or enforces that synthesis pages derive from clusters already in the slip-box.

**Options.** Bottom-up only (synthesis topics must derive from clusters that meet a critical-mass threshold; user-declared topics rejected until supporting notes exist). Top-down allowed (the user can declare a topic and back-fill notes). Hybrid (bottom-up by default, top-down allowed with a flag and lower confidence). Free.

**Trade-offs.** Bottom-up only matches Ahrens's central principle but blocks legitimate cases where the user wants to write about something they care about even before the cluster is mature. Top-down is the academic-norm default and fits aspirational topics. The hybrid is the working compromise.

**What the literature suggests.** Ahrens ch. 2.1 step 6 ("Choose a topic from what you have, not from an external prompt"). Ahrens ch. 7 ("the problem of 'finding a topic' is replaced by the problem of 'having too many topics to write about'"). Ahrens ch. 13 ("From top-down to bottom-up... the belief in one's ingenuity decreases with expertise even as the actual ability to make a new contribution increases").

**Failure modes.** Top-down allowed re-opens the "writing about what you don't yet know" failure that Ahrens names as the main failure mode the slip-box is designed to prevent.

### D 7.20 Project-note to slip-box routing

Whether the system supports an explicit path for promoting a project-note insight into the slip-box as a permanent concept, distinct from the daily inbox triage path.

**Options.** Dedicated `route-to-slipbox` operation (the user marks a project note as containing a reusable idea; the operation copies the idea into the inbox or creates a draft concept page). Manual path (the user copies the idea into the inbox themselves; standard inbox triage takes over). No explicit support (project notes never feed the slip-box directly; reusable ideas must be re-encountered when reading). Auto-detection (the agent scans project notes for reusable insights).

**Trade-offs.** A dedicated operation captures Verbund by-products (the by-products of one project's drafting that are useful for other projects). Manual path works but relies on the user remembering to copy. No support re-opens lost-insight failures when project notes are archived. Auto-detection re-opens silent-promotion failures.

**What the literature suggests.** Ahrens ch. 13 ("Reading produces ideas relevant to projects you're not currently focused on; the slip-box catches those by-products and routes them"). The Verbund decision (D 11.9) names the multi-project workflow but does not address the routing mechanism between project notes and the slip-box.

**Failure modes.** No-support re-opens lost-insight failures when projects archive.

---

## Part 8. Skills

The agent's command surface.

### D 8.1 Core skill set

Which skills the agent has.

**Options.** Minimal (ingest only). Small (ingest + query). Standard (ingest + query + lint). Karpathy-canonical (capture + ingest + maintain + query). Extended (add audit, promote, triage, forget, supersede, reflect, compare, brief, synthesis, reingest / ingest-deep, consistency, skill-linter).

**Trade-offs.** Minimal is fast to set up but every operation becomes a one-off. Karpathy-canonical covers the four-stage cycle. Extended supports the full Ahrens × Karpathy hybrid but means more skills to maintain. The sweet spot from BP §6 is "a few clearly named skills with explicit when-not-to-use guidance."

**What the literature suggests.** BP §14 spans the range. The two starter recommendations are kfchou/wiki-skills (six skills) and Astro-Han/karpathy-llm-wiki (single SKILL.md).

**Failure modes.** Minimal re-opens manual work for routine operations. Extended re-opens router errors.

### D 8.2 Triage skill

Whether daily inbox triage is a dedicated skill.

**Options.** Dedicated `triage` skill. Embedded in `ingest`. Manual (no skill). Skip the inbox entirely (D 2.4).

**Trade-offs.** Dedicated skill enforces the 24h rule (Ahrens ch. 6). Embedded loses the daily cadence. Manual relies on habit alone.

**What the literature suggests.** BP §7.1 makes triage a stage of the cycle. Ahrens ch. 6 makes it a daily habit.

**Failure modes.** No triage skill re-opens Ahrens mistake #3.

### D 8.3 Promote skill

Whether the draft → active transition is a dedicated skill.

**Options.** Dedicated `promote` skill (forces re-voicing, then status flip). Manual edit (status flip in frontmatter). Automated after review.

**Trade-offs.** Dedicated skill enforces re-voicing as part of the operation. Manual is more flexible but easier to skip the re-voicing step. Automation re-opens promotion without paraphrase.

**What the literature suggests.** BP §7.3 names promotion as a discrete step. The live schema has not yet implemented a `promote` skill.

**Failure modes.** No promote skill re-opens the silent-promotion failure (status flipped without re-voicing).

### D 8.4 Lint / audit / consistency split

Whether maintenance is one skill or several.

**Options.** One combined skill. Two (lint = structural; audit = semantic). Three (lint = page-level structural; audit = page-level semantic; consistency = project-level schema and skill drift). Custom.

**Trade-offs.** One skill mixes structural and semantic checks; structural is cheap and deterministic, semantic is expensive — running them together wastes tokens. Three-way split lets cheap checks run every session and expensive checks run on cadence. Audit-precondition chains (D 8.6) only make sense with the split.

**What the literature suggests.** BP §7.5 names two (cheap health vs heavier lint). The live schema adds a third (consistency) for project-level drift.

**Failure modes.** One skill re-opens token waste. Many skills re-open router errors if not clearly named.

### D 8.5 Lint cadence

How often lint runs.

**Options.** Every session. Every 10–15 ingests. Weekly. On-demand only.

**Trade-offs.** Frequent lint catches drift early but costs tokens. On-demand lets drift accumulate and the human forgets to run it. Tying cadence to ingest volume (rather than time) matches the real failure rate — drift accumulates per ingest, not per day.

**What the literature suggests.** BP §7.5 names the cadence: "health every session, lint every 10–15 ingests." `SamurAIGPT/llm-wiki-agent` documents this explicitly.

**Failure modes.** On-demand re-opens drift accumulation.

### D 8.6 Audit precondition chain

Whether audit can run independently of other maintenance skills.

**Options.** Independent (audit can run anytime). Lint-first (audit requires recent clean lint). Lint + consistency clean (audit requires both). Sequenced (full chain).

**Trade-offs.** Gating prevents auditing pages against a drifted schema (since the audit's findings would be against rules the project no longer agrees on). Independence is faster but lower-quality. The chain — lint clears page-level drift, consistency clears schema-level drift, audit then runs on a clean substrate — is the strongest pattern.

**What the literature suggests.** Neither source addresses this directly. The pattern is downstream of D 8.4 (the three-way split). The live schema documents the chain.

**Failure modes.** Independent audit re-opens drift-blind audits.

### D 8.7 Forget vs supersede skills

How removal and replacement are handled.

**Options.** Have both as separate skills. Have one (e.g., supersede only). Combine into one. Rely on git history alone.

**Trade-offs.** `forget` removes a page or trail (with quarantine for recovery); `supersede` replaces while preserving the prior view. They are different operations: forget = "this is wrong"; supersede = "this is replaced." Combining loses the distinction. Git-only re-opens the visibility-of-superseded-claims failure (the user cannot tell from the wiki that the claim was once different).

**What the literature suggests.** BP §13 names memory lifecycle as a failure class fixed by `status: superseded`. Ahrens ch. 6 says permanent notes are never thrown away — which creates tension: in the LLM-wiki version, "thrown away" becomes "forgotten with quarantine."

**Failure modes.** Git-only re-opens silent-stale-claim failures.

### D 8.8 Reflect / compass skill

Whether the agent has a periodic self-review skill.

**Options.** Dedicated `reflect` skill (writes a `compass.md` with current direction, blind spots, and one question worth sitting with). Embedded in weekly habit. Skip.

**Trade-offs.** Dedicated skill surfaces direction explicitly. Skip leaves it implicit and the user may never notice drift.

**What the literature suggests.** BP §14 (`maeste/my-2nd-brain`) ships `reflect`. The live schema has it. Ahrens does not address.

**Failure modes.** Skip re-opens silent-direction-drift.

### D 8.9 Skill model routing

Which model runs each skill.

**Options.** Same model for all skills. Per-role policy (e.g., Opus orchestrates, Haiku scans, Sonnet writes). Per-skill choice. Cost-tier routing.

**Trade-offs.** Per-role reduces cost (cheap models for mechanical work) but adds complexity. Same-model is simple but wastes tokens on operations that do not need a flagship model.

**What the literature suggests.** BP §14 names `rvk7895/llm-knowledge-bases` as the only verified repo with explicit per-role model policy. The rest leave model choice unspecified.

**Failure modes.** Same-model re-opens cost waste at scale. Per-role re-opens fragility when one model rolls out and breaks the routing.

### D 8.10 Mechanical-edit policy per skill

What the skill is allowed to change without approval.

**Options.** All edits require approval. Mechanical-only (e.g., `updated:` field, index entries, `source_count`). Substantive-also (the skill can edit content). Everything (autonomous).

**Trade-offs.** Mechanical-only is the standard. Substantive re-opens the failure modes from D 5.8.

**What the literature suggests.** BP §7.5: lint reports only, fixes nothing without approval.

**Failure modes.** Substantive re-opens hallucination compounding.

### D 8.11 Skill discoverability

How skills surface to the user.

**Options.** Slash commands (`/ingest`). Natural-language triggers. Skill-search (deferred tools). Combination.

**Trade-offs.** Slash commands are predictable but require memorization. Natural-language triggers re-open router errors. Combination is the modern default.

**What the literature suggests.** BP does not prescribe. The ecosystem (BP §14) leans toward natural-language triggers in skill descriptions plus slash-command shortcuts.

**Failure modes.** Natural-language only re-opens router errors.

### D 8.12 Demo and golden-snapshot test mode

Whether the system ships a self-test pipeline.

**Options.** Demo mode plus golden-snapshot tests (sanity loop: demo → ingest → inspect → lint / doctor → repair → query). Demo mode only. Tests but no demo. None.

**Trade-offs.** Demo plus snapshots lets the user verify the pipeline end-to-end after schema changes without ingesting real sources. None re-opens silent-pipeline-rot detection failures.

**What the literature suggests.** BP §14 (`gowtham0992/link`: "ships `doctor`, `verify-mcp`, `rebuild-backlinks`, demo mode, golden-snapshot tests. The 'sanity loop' template").

**Failure modes.** None re-opens pipeline-rot detection failures.

### D 8.13 View-builder skill

Whether the agent supports building derived views from wiki content.

**Options.** Dedicated `view` skill with templates (timelines, comparisons, reports, slides, posts). Per-view-type skills. Ad-hoc query saves with templates. None.

**Trade-offs.** A dedicated view skill makes derived artefacts a first-class operation; the wiki becomes a reading layer for many output formats. Per-view-type skills re-open router errors. None re-opens publication friction (the wiki content is hard to share outside Markdown).

**What the literature suggests.** BP §14 (`maeste/my-2nd-brain`: "view builders for timelines / comparisons / reports / slides / posts; commands `save`, `view`, `reflect`, `forget`").

**Failure modes.** None re-opens publication-friction failures.

### D 8.14 Bootstrap and first-run auto-ingest

Whether the system has a setup mode that scaffolds the wiki from an initial corpus.

**Options.** Bootstrap skill (first run scaffolds the folder layout and ingests an initial seed corpus). Setup-only (skeleton without auto-ingest). Manual (user runs every step from scratch).

**Trade-offs.** Bootstrap reduces onboarding friction but ingests at scale before the human has internalized the pipeline — re-opening the curated-batches discipline (D 7.5). Setup-only is the standard middle: scaffold the structure, but leave ingest to the user.

**What the literature suggests.** BP §14 (`aws-samples/sample-kiro-llm-wiki`: "wiki-first mode in Kiro, protected raw/, bootstrap / auto-ingest, MCP fetch integration").

**Failure modes.** Bootstrap with auto-ingest re-opens bulk-load noise.

### D 8.15 Onboarding-wizard and guided setup

Whether the system includes a guided onboarding for new users.

**Options.** Guided wizard (pauses for user action at each external integration — exports, permissions, logins). Documentation only. None.

**Trade-offs.** Guided wizard is essential for non-technical users and integration-heavy systems. Documentation-only suits technical users who prefer reading. None re-opens the "user gets stuck at the first integration step" failure for non-technical adopters.

**What the literature suggests.** BP §14 (`charlie947/ai-second-brain`: "guided onboarding; integrates ChatGPT / Claude histories, Gmail, NotebookLM, Granola, iMessage; pauses for user action when exports / permissions / logins are needed"). BP §12 ("Concrete walkthrough evidence... setup wizard at 05:53").

**Failure modes.** None re-opens non-technical-adoption failures.

### D 8.16 Backlink-rebuild operation

Whether the system has a dedicated backlink-rebuild skill, distinct from per-ingest backlink scanning and lint reporting.

**Options.** Per-ingest only (every ingest scans and updates backlinks for touched pages). Dedicated `rebuild-backlinks` skill (run periodically or on-demand to re-derive all backlinks from scratch). Lint-only (lint detects missing or broken backlinks but does not fix them). Hybrid (per-ingest plus an occasional rebuild).

**Trade-offs.** Per-ingest is cheap and incremental but drifts over time when pages are renamed or removed. A dedicated rebuild operation is the canonical fix once drift accumulates. Lint-only re-opens the "lint reports orphans the user never fixes" failure.

**What the literature suggests.** BP §2 ("the projects that ship a `doctor` / `lint` / `health` / `verify` / `rebuild-backlinks` command are the ones whose READMEs read like real systems"). BP §7.2 step 8 ("Scan existing pages for backlinks and contradictions").

**Failure modes.** Per-ingest only re-opens backlink drift over time as pages move and rename.

### D 8.17 Lint check set

Which targets the lint / audit pass actually checks for.

**Options.** Minimal (broken links, frontmatter validity). Standard (BP §7.5 list: orphan pages, claims with no source, source files not represented in wiki, wiki pages without raw references, duplicate pages, stale pages, contradictions, oversize pages, recursion-smell pages where a concept page cites only other concept pages, draft-overdue pages). Custom subset. Custom additions (project-specific checks, e.g., placeholder padding detection).

**Trade-offs.** A minimal set runs cheaply but misses real failures. The standard set covers every documented failure mode but produces noisy reports if too many checks fire at once. Custom subsets work when standard checks don't apply (a code-rationale variant has no raw papers to check; a single-author wiki has no need for some signature checks).

**What the literature suggests.** BP §7.5 enumerates the 10 standard targets. BP §13 names the failure modes each check catches.

**Failure modes.** Minimal re-opens the lint-blindness failure for the targets it skips. Custom subsets re-open whichever failure modes they omit.

### D 8.18 Cluster-discovery / synthesis-scan skill

Whether the system includes an active operation that scans the wiki for emerging clusters and proposes candidate synthesis topics, distinct from a synthesis-creation skill the user invokes when they have already noticed a cluster.

**Options.** Active synthesis-scan (a skill periodically scans `index.md`, `hot.md`, and connected wiki pages for clusters meeting a critical-mass threshold and proposes candidate synthesis topics for human approval). Passive (synthesis pages only get written when the user notices a cluster and asks). User-only discovery (the user manually scans the wiki). Hybrid (the agent surfaces candidates only when the user explicitly asks for them).

**Trade-offs.** Active scanning makes the bottom-up topic-emergence mechanism that Ahrens names as central into a system property rather than relying on the user noticing. Passive defaults to user attention. Active without a human commit point re-opens the auto-promotion failure (D 7.7) — proposals are fine; auto-creation is not.

**What the literature suggests.** Ahrens ch. 2.1 step 5 ("Develop bottom-up. Don't pre-plan a topic. Look into the slip-box and notice where chains of notes have grown into clusters. Follow whichever cluster has the most momentum"). Ahrens ch. 13 ("Once a cluster has critical mass, the perspective shifts: instead of widening to find every connection, you narrow to develop one argument").

**Failure modes.** Passive re-opens the "user never notices the cluster" failure that defeats the slip-box's bottom-up emergence property.

---

## Part 9. Provenance and retrieval

How sources are tracked and how the agent finds things.

### D 9.1 Citation style

How wiki claims are tied back to sources.

**Options.** Per-page bibliography. Per-section. Per-claim with locator. Mixed (per-claim for claims tagged as load-bearing; per-page for the rest).

**Trade-offs.** Per-claim catches the invented-citation failure (BP §13) and is what working implementations require. Per-page is the lightest. Per-section is a middle ground.

**What the literature suggests.** Ahrens ch. 6 requires "explicit references" on every literature note. BP §9: "Working implementations require claim-level provenance, not just a bibliography at the bottom of each page."

**Failure modes.** Per-page re-opens invented-citation failures.

### D 9.2 Locator granularity

How precise the source pointer is.

**Options.** Page only. Page + section. Page + section + paragraph. Figure / timestamp / line number. Stable fragment ID.

**Trade-offs.** Finer locator catches more verification failures and lets a script open the cited fragment, but adds work at write time.

**What the literature suggests.** BP §9 names: source file path, page / paragraph / timestamp / section / URL locator, confidence, date last checked.

**Failure modes.** Page-only re-opens vague-citation failures (the page exists but the claim is not on it).

### D 9.3 Confidence on every claim

Whether confidence is required.

**Options.** Required on every claim. Required only when below high. Optional. Absent.

**Trade-offs.** Required = explicit doubt at every load-bearing point. Required-when-low = lighter but loses the calibration cue. Absent re-opens overconfidence.

**What the literature suggests.** BP §9 names required confidence per claim. Ahrens does not address directly.

**Failure modes.** Absent re-opens overconfidence.

### D 9.4 Validator scripts

Whether deterministic scripts check provenance.

**Options.** Deterministic script that opens each cited path and confirms it exists. URL checker (live HTTP HEAD). LLM-based verifier. None.

**Trade-offs.** Deterministic script catches the easy invented-source failure (the LLM puts a real-looking URL on a fabricated claim) at near-zero cost. URL checker catches link rot but adds external requests. LLM verifier catches semantic drift but is expensive.

**What the literature suggests.** BP §9: "Pair claim-level provenance with a script that opens each cited path and confirms it exists." BP §17 names the absence of a validator as one of the top reasons implementations fail.

**Failure modes.** None re-opens invented-citation failures.

### D 9.5 Search escalation rungs

How the wiki is searched at increasing scale.

**Options.** Lexical (`ripgrep`, BM25, `qmd`). Sharded indexes. Line-anchored retrieval (`PATH:LINE` plus context window). Embeddings / vector search. Graph traversal and reciprocal-rank fusion. Entity-resolution layer.

**Trade-offs.** Each rung adds capability and cost. Skipping rungs is the most-cited failure pattern: adding embeddings, OCR, a graph database, and routing on day one breaks before the basics are working.

**What the literature suggests.** BP §10 names the escalation order explicitly. The general rule: Markdown-first until the pain is specific and obvious, then add a narrow capability for that specific pain.

**Failure modes.** Skipping rungs re-opens premature-optimization failures.

### D 9.6 When to climb each rung

The trigger for each escalation.

**Options.** Pain-driven (a specific failure justifies the next rung). Pre-emptive (build it now while there is time). Schedule-driven (every six months, evaluate). Never (Markdown forever).

**Trade-offs.** Pain-driven is the literature consensus. Pre-emptive bloats and wastes effort. Never breaks at scale. Schedule-driven adds overhead.

**What the literature suggests.** BP §10 (general rule): Markdown-first until the pain is specific. BP §16 rule 8: "Only add graph / entity-resolution / vector infrastructure once the real failure is duplication or navigation at scale, not before."

**Failure modes.** Pre-emptive re-opens premature-optimization failures.

### D 9.7 Search tooling choice

The actual tool stack at each rung.

**Options.** `ripgrep` for lexical. `qmd` (Karpathy gist mention; multiple unrelated projects share the name). BM25 implementation (e.g., bm25s). Vector DB (Chroma, Weaviate, FAISS). Graph DB (Neo4j). Hybrid (Postgres + pgvector). Local vs cloud at every rung.

**Trade-offs.** Local = private but capability-limited. Cloud = capable but cost and privacy concerns.

**What the literature suggests.** BP §10 names ripgrep / BM25 / qmd as cheap defaults. BP §14 mentions Chroma (`QipengGuo/llm-wikidata`, unverified), Weaviate (NEXUS, Beever-AI), Neo4j (Beever-AI).

**Failure modes.** Cloud-default re-opens privacy failures.

### D 9.8 Index granularity

What `wiki/index.md` actually lists.

**Options.** Exhaustive (every wiki page listed). Entry-points only (one or two starter notes per line of thought, ~25 links per topic at most). Hybrid (exhaustive in some sections, entry-points in others). Auto-generated from page metadata.

**Trade-offs.** Entry-points only matches Luhmann's actual practice and makes the index a navigation aid rather than a catalogue. Exhaustive grows linearly with page count and becomes a directory. Auto-generated is cheap but produces exhaustive output by default. Entry-points only requires hub notes (D 3.8) to compensate — the index points at hubs, hubs point at concepts.

**What the literature suggests.** Ahrens ch. 1.3 ("The index is small. The index didn't list every note. It listed entry-points — one or two starter notes per line of thought"). Ahrens ch. 12 ("Luhmann typically attached only one or two notes to a keyword in the index — entry points, not exhaustive listings"). BP §5 (`index.md` is "navigational index — entry points, not a topic ontology").

**Failure modes.** Exhaustive re-opens index-as-directory navigation collapse. Entry-points-only without hub notes re-opens orientation collapse.

### D 9.9 Log entry shape

How `log.md` entries are structured.

**Options.** Free prose. Structured (dated header plus `verb | subject` plus body). Append-only. Reverse-chronological. Per-skill subfile (`log/ingest.md`, `log/lint.md`).

**Trade-offs.** Structured aids automated scanning — a weekly digest can summarize the week's verbs without reading prose. Free prose is faster to write but harder to parse. Reverse-chronological matches the most-recent-first reading pattern.

**What the literature suggests.** BP §5 has `log.md` as an append-only change log; BP §7.2 step 9 ("Update wiki/index.md and wiki/log.md"); BP §16 rule 6 (log coverage as a health check). The structured `## [YYYY-MM-DD] verb | subject` form is one common shape; BP does not mandate.

**Failure modes.** Free prose re-opens log-scan failures (the weekly review can't summarize unstructured prose).

### D 9.10 Paragraph-level attribution at write time

Whether ingest produces per-paragraph source pointers.

**Options.** Per-paragraph attribution (every paragraph in a draft cites the raw passage it came from). Per-claim only (D 9.1). Per-page only.

**Trade-offs.** Per-paragraph is the most defensive at ingest time and makes "ingest errors compound" easy to catch — when a paragraph's cited passage doesn't support its prose, the failure is visible at the paragraph level. The cost is friction at write time.

**What the literature suggests.** BP §13 ("Ingest errors compound... Fix: paragraph-level attribution, contradiction sections, easy rollback, the 'discuss takeaways before writing' step").

**Failure modes.** Page-only re-opens the failure where a wrong paragraph hides inside an otherwise-cited page.

### D 9.11 Index keyword density

How many notes the index lists per keyword or topic. Finer-grained than D 9.8.

**Options.** One or two notes per keyword (Luhmann's actual practice — entry points only). Up to ~5. Up to ~25 (matching the hub-note size limit). Exhaustive. Auto-determined by tooling.

**Trade-offs.** Two notes per keyword forces the user to pick the most useful entry points and keeps the index navigable. More permits a richer surface but re-opens the "index becomes a directory" failure even when the index is nominally entry-points-only (D 9.8). Auto-determined re-opens the tags-as-noise failure (D 4.13).

**What the literature suggests.** Ahrens ch. 12 ("Luhmann typically attached only one or two notes to a keyword in the index — entry points, not exhaustive listings"). Ahrens ch. 1.3 ("one or two starter notes per line of thought").

**Failure modes.** Many-notes-per-keyword re-opens the index-as-directory failure even when D 9.8 is set to entry-points-only.

### D 9.12 Orphan-page policy and reachability invariant

Whether every wiki page must be reachable from the index, and what happens to orphans when found.

**Options.** Strict reachability (every page must be reachable from `index.md`, directly or via a hub note already in the index; orphans get flagged or blocked). Soft (lint reports orphans but does not enforce). Auto-link orphans to the nearest hub note. Demote orphans to draft. Allow orphans freely.

**Trade-offs.** Strict reachability matches Ahrens's canonical rule (ch. 11.4) and prevents the "page exists but is invisible" failure. Soft re-opens "lint reports orphans the user never fixes." Auto-linking re-opens incorrect-classification failures (the agent picks the wrong hub). Demote-to-draft is a useful middle: orphans drop out of query results until reattached.

**What the literature suggests.** Ahrens ch. 11.4 ("make sure it's reachable from the index, either directly or via an entry-point note already linked from the index"). BP §7.5 (orphan pages as a standard lint target).

**Failure modes.** Allow re-opens the page-exists-but-invisible failure.

---

## Part 10. Document handling

How raw sources are processed.

### D 10.1 PDF strategy

How PDFs become readable to the agent.

**Options.** Untouched in raw + extracted Markdown alongside (`raw/papers/x.pdf` + `raw/papers/x.md`). Extract-only. Re-extract on each ingest. Agent reads PDF directly (multimodal model).

**Trade-offs.** Untouched + extracted preserves the source-of-truth and gives the agent something easy to read. Extract-only loses the source. Re-extract is wasteful. Direct multimodal is expensive.

**What the literature suggests.** BP §11: untouched + extracted is the canonical pattern.

**Failure modes.** Extract-only re-opens reproducibility failures.

### D 10.2 EPUB vs PDF for books

Source format preference.

**Options.** Prefer EPUB. PDF acceptable. Both. Always convert to text before ingest.

**Trade-offs.** EPUB has clean text and chapter markers. PDF has layout but extraction is lossy. Always-convert-to-text loses figures and structure.

**What the literature suggests.** Karpathy's gist comments name EPUB as the preferred book format. BP §11.

**Failure modes.** PDF-only re-opens lossy-extraction failures for books.

### D 10.3 OCR

How scanned sources are handled.

**Options.** Default off, on-demand. Default on for all. Never (skip scanned sources).

**Trade-offs.** Default-on is wasteful. On-demand matches need. Never excludes a class of sources.

**What the literature suggests.** BP §11: "Make it a module, not a default." `lucasastorian/llmwiki` makes Mistral OCR optional in hosted mode.

**Failure modes.** Default-on re-opens cost waste. Never excludes valid sources.

### D 10.4 Long sources

How books and other long sources are ingested.

**Options.** Split by chapter at ingest (one source page per chapter, e.g., `bookkey-ch01.md`, `bookkey-ch02.md`). Single source page for the whole book. Chapter-by-chapter as separate ingest runs.

**Trade-offs.** Splitting preserves atomicity (D 3.7) and respects page-size limits. Single page hits the size cap and re-opens whole-file edit bottleneck.

**What the literature suggests.** Karpathy's gist: process chapter by chapter. BP §11.

**Failure modes.** Single page re-opens whole-file edit and atomicity failures.

### D 10.5 Web sources

How web pages enter raw.

**Options.** Manual save (copy-paste into `raw/articles/`). Programmatic fetcher (curl, wget). Browser automation (Playwright). Web Clipper integration. Claude / agent-based fetch.

**Trade-offs.** Manual is simple but tedious. Browser handles JavaScript-heavy and paywalled pages but is heavy. Web Clipper is a dedicated tool.

**What the literature suggests.** BP §11: "the practical failure mode is paywalls, JavaScript-heavy pages, and walled domains — prompt instructions alone don't solve source acquisition." Implementations that handle web well add a dedicated fetcher (`maeste/my-2nd-brain`).

**Failure modes.** Manual-only re-opens scaling failures for high-volume web ingest.

### D 10.6 Image handling in sources

What happens to figures and diagrams in source documents.

**Options.** Keep images local + describe textually. Ignore images. OCR images for embedded text. Multimodal LLM ingestion (LLM reads the image directly).

**Trade-offs.** Local + description is portable and matches Karpathy's recommendation. Multimodal is expensive but captures more.

**What the literature suggests.** Karpathy's gist (BP §11): "keep images local and describe them textually."

**Failure modes.** Ignoring images re-opens information loss for figure-heavy sources.

### D 10.7 Attachment naming and uniqueness

How extracted images are named.

**Options.** Descriptive (`fig3-layouts.png`). Stem-prefixed (`vaswani2017-fig-1.png`). Slugified. Numeric-only.

**Trade-offs.** Descriptive is readable but collides on the second source. Stem-prefixed is collision-free but verbose. Slugified is a compromise.

**What the literature suggests.** Neither source addresses in detail. The collision concern is real for Obsidian's basename wikilink resolution.

**Failure modes.** Descriptive re-opens cross-source filename collisions.

### D 10.8 Where attachments embed

Which page types may include images.

**Options.** Source pages only. Source + concept (one defining image per concept). Source + concept + synthesis (when comparing approaches visually). Anywhere.

**Trade-offs.** Restricting embeds enforces single-canonical placement. Anywhere allows duplication.

**What the literature suggests.** Neither source prescribes. The pattern is downstream of D 3.7 (atomicity).

**Failure modes.** Anywhere re-opens duplication.

### D 10.9 External-app capture integrations

Which third-party apps the capture pipeline pulls from beyond direct file drops.

**Options.** None (manual file drops only). Single integration (e.g., Gmail). Multiple (Gmail, Claude / ChatGPT history, NotebookLM, voice apps like Granola, iMessage). Custom adapters.

**Trade-offs.** Multiple integrations widen the capture surface but each integration has its own auth, format, and rate-limit failure modes. None forces every capture through manual drops, which preserves the inbox triage discipline (D 2.4) but loses ambient capture.

**What the literature suggests.** BP §14 (`charlie947/ai-second-brain`: "integrates ChatGPT / Claude histories, Gmail, NotebookLM, Granola, iMessage"). BP §12 ("voice notes → local transcription → LLM extracts signal").

**Failure modes.** Multiple-without-discipline re-opens noise accumulation as integrations dump material into raw or inbox without filtering.

### D 10.10 AI-session-transcript ingest

Whether session transcripts (Claude / ChatGPT / Cursor logs) are accepted as raw sources, and how they are triaged given their noise profile.

**Options.** Accept and ingest with a dedicated transcript page schema. Reject (transcripts stay outside raw). Accept selectively (only after human review and excerpt extraction). Accept with a higher promotion bar (extra verification packet, higher confidence threshold).

**Trade-offs.** Transcripts capture decisions and rejected approaches that would otherwise vanish, but their noise profile is different from research papers — much more thinking-aloud per useful claim. Accepting requires either a stricter triage or a session-summary skill. Rejecting loses valuable working state, especially for code-rationale variants (D 1.3).

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki`: "Turns AI session transcripts into sources, entities, concepts, syntheses, comparisons, and questions"). BP §7.2 third invariant (one implementer's six-month variant: "reads session transcripts after coding sessions, extracts decisions and rejected approaches, then requires human review before anything is promoted into persistent context").

**Failure modes.** Accept-without-discipline re-opens noise accumulation. Reject re-opens lost-decision failures.

---

## Part 11. Habits

The cycle that sustains the system.

### D 11.1 Daily habit cadence

When the daily cycle runs.

**Options.** End of work day. Morning review. On-capture (every time something enters inbox). None.

**Trade-offs.** Scheduled cadence builds habit (Ahrens ch. 14). On-capture is always fresh but interrupts. None re-opens triage debt.

**What the literature suggests.** Ahrens ch. 6 ("review within a day or so") and ch. 14 (habits replace habits, not willpower). BP §7.5 implies end-of-day for the inbox sweep.

**Failure modes.** None re-opens fleeting-note rot.

### D 11.2 Daily habit content

What the daily cycle covers.

**Options.** Triage inbox. Triage + review draft promotions. Triage + draft review + log read. Full daily reflect.

**Trade-offs.** Triage is the floor. Adding more increases discipline but may push the cycle past sustainable length.

**What the literature suggests.** BP §7.1 (triage) + §7.3 (promotion) + §7.5 (lint reports). Ahrens ch. 11 (the per-note habit).

**Failure modes.** Triage-only re-opens promotion latency.

### D 11.3 Weekly habit cadence

When the weekly cycle runs.

**Options.** Fixed day (e.g., Friday). Flexible. Aligned to lint cadence (every 10–15 ingests).

**Trade-offs.** Fixed day is predictable. Flexible adapts but may slip.

**What the literature suggests.** BP §7.5 leaves cadence between weekly and per-15-ingests. Ahrens does not prescribe.

**Failure modes.** Flexible re-opens slip.

### D 11.4 Weekly habit content

What the weekly cycle covers.

**Options.** Lint review + report-reading. + log review. + draft review. + full audit. + reflect.

**Trade-offs.** More = thorough but slow. Less = sustainable but misses signals.

**What the literature suggests.** BP §7.5 (lint and reports). Ahrens ch. 14 (review log to notice clusters forming for bottom-up topic emergence).

**Failure modes.** Lint-only re-opens cluster blindness (the user does not notice a topic is forming).

### D 11.5 Fleeting-note staleness threshold

How old a fleeting note can be before it is trash.

**Options.** 24 hours (Ahrens). 48 hours. 1 week. No threshold.

**Trade-offs.** Shorter enforces freshness; longer is forgiving but lets meaning rot.

**What the literature suggests.** Ahrens ch. 6: "fleeting notes are only useful if you review them within a day or so."

**Failure modes.** Long thresholds re-open meaning rot.

### D 11.6 Promotion-latency threshold

How long a draft can sit before it is flagged.

**Options.** 7 days. 14 days. 30 days. No threshold.

**Trade-offs.** Shorter forces decisions; longer lets drafts mature; none re-opens silent draft accumulation.

**What the literature suggests.** Neither source prescribes. The pattern is implicit in the lint cadence (D 8.5).

**Failure modes.** None re-opens draft pile-up.

### D 11.7 Note quota

Whether the user has a daily writing target.

**Options.** Daily count (3 notes / 6 / Trollope's 250 words / 10 pages). Weekly count. No quota.

**Trade-offs.** Quota sets pace; no quota adapts. Luhmann's effective rate was about six notes per day across the slip-box's working life; Ahrens names "three notes a day is a reasonable goal" (ch. 11).

**What the literature suggests.** Ahrens ch. 11 (Luhmann ~6 per day; Trollope 10 pages per day at 250 words per 15 minutes). BP does not prescribe.

**Failure modes.** No quota re-opens drift toward zero output.

### D 11.8 Habit installation order

Which habit to build first.

**Options.** Capture-first (Benjamin Franklin, Ahrens ch. 14: "fetch a pen whenever you read"). Triage-first. Lint-first. Promotion-first. All at once.

**Trade-offs.** All-at-once usually fails. Sequential builds sustainability. Capture-first matches Ahrens's recommendation because once capture is automatic, the rest follows.

**What the literature suggests.** Ahrens ch. 14 names capture as the first habit and frames the rest as developing on its own once capture is automatic.

**Failure modes.** All-at-once re-opens habit collapse.

### D 11.9 Verbund / parallel projects

Whether the workflow supports running multiple manuscripts concurrently.

**Options.** Single-project focus (one manuscript at a time). Verbund (multiple parallel manuscripts; by-product ideas from one project route to others via the slip-box). Sequential with warm hand-offs.

**Trade-offs.** Verbund matches Luhmann's practice and lets reading produce ideas relevant to projects you're not currently focused on; the slip-box catches those by-products and routes them. Single-focus is simpler but loses the cross-project routing the slip-box enables, and re-opens the block-when-stuck failure.

**What the literature suggests.** Ahrens ch. 13 ("Try working on multiple manuscripts at once — the chemical industry's *Verbund* model, where the by-product of one production line becomes the input to another. Reading produces ideas relevant to projects you're not currently focused on; the slip-box catches those by-products and routes them"). Luhmann's answer when stuck on one manuscript: work on a different one ("I never encounter any mental blockages").

**Failure modes.** Single-project focus re-opens block-when-stuck failures.

### D 11.10 Spaced retrieval of old notes

Whether the system periodically re-surfaces old notes for review.

**Options.** Random walk (the agent surfaces a random concept page during the weekly habit). Scheduled re-read (notes surface at increasing intervals after creation, like Anki). Query-time exposure (when the user queries a topic, related old notes surface even when not directly cited). None.

**Trade-offs.** Spaced retrieval converts storage strength into retrieval strength — Ahrens ch. 11 cites Bjork on retrieval at irregular intervals as the mechanism that builds durable learning. None means the user only sees notes when they explicitly look; most never get re-read, and the slip-box's "presents you with ideas you have already forgotten" property never activates.

**What the literature suggests.** Ahrens ch. 11 (storage vs retrieval strength; "retrieval at irregular intervals in different contexts builds durable learning where massed practice does not"). Ahrens ch. 12 ("The slip-box is designed to present you with ideas you have already forgotten, allowing your brain to focus on thinking instead of remembering").

**Failure modes.** None re-opens the "wrote it once and never saw it again" failure that defeats the slip-box's central property.

### D 11.11 Reflect-skill cadence

How often the reflect / compass skill (D 8.8) runs.

**Options.** Weekly. Per-N-ingests. On-demand only. Scheduled (e.g., end of month). Triggered by lint findings.

**Trade-offs.** Scheduled cadence builds the habit (Ahrens ch. 14). On-demand re-opens the "user never reflects" failure. Triggered cadence ties reflection to detected drift but may run too often during active periods and not enough during quiet ones.

**What the literature suggests.** BP §14 (`maeste/my-2nd-brain`: "the `reflect` command writes a `compass.md` with current direction, blind spots, and one question worth sitting with — a useful pattern even if you don't adopt the rest of the stack"). Ahrens ch. 14 (habits replace habits, not willpower).

**Failure modes.** On-demand re-opens silent-direction-drift.

---

## Part 12. Boundaries

When this pattern fits and when it does not.

### D 12.1 Corpus type

What the system is for.

**Options.** Research papers. Articles. Meeting notes / transcripts. Code rationale. Mixed.

**Trade-offs.** Each fork (D 1.3) has different prompts and validation needs. Mixed corpora need branch-aware ingest.

**What the literature suggests.** BP §11, §12, §13. Karpathy's gist: "articles, papers, images, data files."

**Failure modes.** Mismatched-fork prompts re-open noise and semantic-gravity failures.

### D 12.2 Personal vs enterprise scale

The corpus and user count.

**Options.** Personal (~100 articles / 400K words — Karpathy's anchor). Medium (~1000 sources). Large (10K+).

**Trade-offs.** Karpathy-scale works on flat Markdown plus an index, provided lint runs. Medium forces sharded indexes and line-anchored retrieval. Large forces embeddings, graph traversal, entity resolution.

**What the literature suggests.** BP §10 (Karpathy-scale anchor: 100 articles / 400K words; "fancy RAG" not needed at his scale). BP §13 (boundary conditions: weaker for large, fast-changing, high-stakes, multi-user, enterprise).

**Failure modes.** Large-scale on flat Markdown re-opens navigation collapse.

### D 12.3 Editor / interface

What the human reads and edits in.

**Options.** Obsidian. VSCode. Plain Markdown viewer. Web app. Hybrid.

**Trade-offs.** Obsidian provides wikilinks, graph view, plugins (Dataview), and is praised for inspectability. VSCode is code-friendly and integrates with development workflows. Web apps allow collaboration but reduce locality.

**What the literature suggests.** BP §12 names Obsidian as the consensus editor; the praise is specifically that it is inspectable (read the wiki, see links, view the graph, diff changes, avoid opaque memory layers).

**Failure modes.** Web app re-opens locality and offline failures.

### D 12.4 Agent runner

Which agent platform runs the skills.

**Options.** Claude Code. Cursor. Codex. OpenCode. Pi. Multiple via symlinks.

**Trade-offs.** Single runner is simple. Multiple runners require schema portability (e.g., `nvk/llm-wiki` shares one wiki-manager skill across Claude / Codex / OpenCode / Pi via symlinks). Some runners (Claude Code, Cursor) support skills natively; others need a wrapper.

**What the literature suggests.** BP §14 lists multi-runner approaches. The live wiki is Claude Code-first.

**Failure modes.** Lock-in to one runner re-opens portability failures.

### D 12.5 AI-consumable exports

Whether the wiki publishes machine-readable views.

**Options.** Human-only pages (no exports). `llms.txt` and JSON-LD exports. Per-page text and JSON. AI-consumable views for agents.

**Trade-offs.** Exports widen the consumer base (other agents can read the wiki) but double-publishing has maintenance cost.

**What the literature suggests.** BP §14 (`Pratiyush/llm-wiki` produces both human-facing pages and AI-consumable exports).

**Failure modes.** Exports without sync re-open contradiction between human and AI views.

### D 12.6 Privacy and locality

(Covered in D 1.5; surfaced here for boundary completeness.)

### D 12.7 Funding and cost model

(Covered in D 1.6; surfaced here for boundary completeness.)

### D 12.8 What the pattern is *not* for

Where to use something else entirely.

**Options.** High-churn material (use classic RAG). Regulatory-critical content (legal, medical — use audited systems). Very large corpora (10K+ documents — use vector search with curated wiki layer on top). Multi-user enterprise knowledge bases (use a CMS with permissions). Real-time streams (use stream processing).

**Trade-offs.** Forcing the wiki pattern onto an unsuitable corpus re-opens the failure modes BP §13 names plus domain-specific risks (e.g., medical hallucinations).

**What the literature suggests.** BP §13: "Stay with classic RAG for high-churn material, regulatory-critical content (legal, medical), and very large corpora."

**Failure modes.** Forcing the pattern re-opens hallucination, scale, and compliance failures.

### D 12.9 Reference-manager integration

Whether the system connects to a separate bibliographic tool.

**Options.** Standalone (no reference manager; bibliographic data lives in source-page frontmatter only). Connected (Zotero, Paperpile, Mendeley as the reference manager; `wiki/sources/` references it). Built-in (the wiki itself is the reference manager).

**Trade-offs.** Connected matches Ahrens (ch. 3 names Zotero) and lets the user reuse standard BibTeX / citation formats in external writing without retyping. Standalone is simpler but re-opens duplicate citation maintenance across the wiki and external writing. Built-in conflates two distinct lifecycles (sources versus ideas).

**What the literature suggests.** Ahrens ch. 3 ("Reference manager. Free programs preferred. Ahrens recommends Zotero (zotero.org). Stores bibliographic entries plus literature notes; integrates with major editors so you don't retype references"). Ahrens ch. 1.3 (Luhmann's two-slipbox: bibliographical plus main).

**Failure modes.** Standalone re-opens duplicate citation maintenance.

### D 12.10 Rendering and publishing layer

Whether the wiki is read only as Markdown or also through a published view.

**Options.** Markdown-only (in editor). Markdown plus a separate viewer (Wiki.js, MkDocs, custom static site, GitHub Pages). Markdown plus AI-consumable exports (D 12.5). Both.

**Trade-offs.** Markdown-only is simple and matches the inspectability argument (BP §12). A rendered viewer aids sharing and discoverability — Tolkien Gateway-style densely interlinked pages are the mental model Karpathy's gist references. The cost is a build pipeline and the risk that the rendered view drifts from the source.

**What the literature suggests.** BP §14 (NEXUS uses Wiki.js as the rendering layer; `Pratiyush/llm-wiki` produces both human-facing pages and AI-consumable exports). BP §12 (Tolkien Gateway as a target image for what a mature wiki feels like).

**Failure modes.** Rendered-only re-opens source-of-truth confusion (users edit the rendered view).

### D 12.11 MCP / external-tool integration surface

Whether the wiki is callable by other agents or systems.

**Options.** No external surface (read-only via filesystem). MCP server exposing read tools. MCP server exposing read and write tools. Custom REST API. Multiple surfaces.

**Trade-offs.** An external tool surface lets other agents query the wiki without filesystem access; useful when the wiki sits behind a remote service or in a multi-agent stack. Adds attack surface and operational complexity.

**What the literature suggests.** BP §14 (`lucasastorian/llmwiki`: "MCP config"; `simonsysun/seeklink`: "optional MCP"; NEXUS: "multiple MCP servers in front"; `aws-samples/sample-kiro-llm-wiki`: "MCP fetch integration").

**Failure modes.** No surface re-opens the "other agents can't read the wiki" failure for multi-agent setups.

---

## Cross-cutting decisions

Decisions that touch multiple parts.

### D X.1 What "atomic" means in practice

Atomicity is named in D 3.7, D 4.7, D 4.8, D 7.3, and D 8.4. The actual *definition* of atomic varies across sources.

**Options.** Strict atomic (one main claim per page, no sub-claims). Idea-atomic (one *idea*, possibly with supporting bullets). Topic-atomic (loosely atomic but in practice a small topic).

**Trade-offs.** Strict atomic forces many small pages; navigation suffers. Topic-atomic re-creates topic-page drift. Idea-atomic is the working compromise and is what Ahrens (ch. 6) describes.

**What the literature suggests.** Ahrens ch. 6 ("one note one idea, full sentences, one side of paper"); BP §8 ("one idea per file, one main claim per file, every page must answer 'from what other contexts would I want to stumble upon this?'").

**Failure modes.** Topic-atomic re-opens topic-page drift.

### D X.2 What "draft" means in practice

The `status: draft` field appears in D 5.5, D 7.7, D 8.3. Its contract varies.

**Options.** Draft = LLM-written, awaiting human re-voicing. Draft = incomplete content. Draft = under review. Draft = anything not yet promoted.

**Trade-offs.** A clear contract makes the promotion gate enforceable. Mixed contracts make `status: draft` semantically empty.

**What the literature suggests.** BP §7.3: draft = LLM-written, awaiting human re-voicing. The promotion gate is the operation that flips it to active.

**Failure modes.** Mixed contracts re-open silent-promotion failures.

### D X.3 What "source-grounded" means in practice

Source-grounding appears in D 4.6, D 7.10, D 9.1, D 9.4. The standard varies.

**Options.** Page-level (the page cites at least one source somewhere). Section-level. Claim-level (every non-obvious claim points to a locator). Validator-enforced (a script confirms the cited path exists).

**Trade-offs.** Each level closes more failure modes at higher write-time cost.

**What the literature suggests.** BP §9 (claim-level required for working implementations); BP §17 (lack of source-level citations is the second-most-cited reason implementations fail).

**Failure modes.** Page-level re-opens hallucination compounding.

### D X.4 Whether to enforce a "no-stub" rule

Whether empty placeholders are acceptable.

**Options.** Allow empty placeholders (`> - None noted`, `> - None yet`). Require minimal content per section. Disallow the page until every section has substance.

**Trade-offs.** Empty placeholders are honest about what the source supported and prevent invented content padding. Required-minimum forces writing where there is nothing to write. Disallow blocks otherwise-useful pages.

**What the literature suggests.** Neither source prescribes explicitly. Ahrens ch. 6 is implicit: do not invent content to fill quotas.

**Failure modes.** Required-minimum re-opens placeholder-padding failures (sections get padded with invented or paraphrased content).

---

## Failure-mode index

For quick lookup. Each failure mode names the decisions that close it.

- **Hallucinations baked into the wiki.** Closed by D 1.2 (load-bearing human), D 4.6 (claim-level provenance), D 7.7 (manual promotion), D 9.4 (validator scripts), D 9.10 (paragraph-level attribution).
- **Wiki recursively cites itself as truth.** Closed by D 2.2 (raw separate from wiki), D 3.5 (contradictions kept), D 3.9 (single-source-of-truth derivation), D X.3 (claim-level source-grounding).
- **Ingest errors compound.** Closed by D 7.3 (staged ingest), D 7.6 (verification packets), D 7.7 (manual promotion), D 9.10 (paragraph-level attribution), D X.2 (draft contract).
- **Topic-based drift.** Closed by D 3.7 (atomicity strict), D 4.7 (page size limits), D 4.11 (no tagged hierarchy), D X.1 (atomic = idea-atomic).
- **Semantic gravity.** Closed by D 5.7 (structural enforcement, not prose).
- **Noise accumulation.** Closed by D 1.2 (human writes), D 7.7 (manual promotion), D 7.9 (save-back is offered, not auto).
- **Whole-file edit bottleneck.** Closed by D 4.7 (page size limits) plus D 9.5–9.6 (line-anchored retrieval at the right rung).
- **Maintenance ratchet.** Closed by D 4.6 (claim-level provenance), D 8.10 (mechanical-edits-only), D 9.4 (validators).
- **Memory lifecycle missing.** Closed by D 5.5 (status includes superseded), D 8.7 (forget vs supersede skills), D 11.5 (staleness threshold).
- **Raw-source safety.** Closed by D 5.7 (runtime guardrails on raw).
- **Anti-RAG framing oversold.** Closed by D 9.5–9.6 (treat retrieval escalation as a ladder, not a refusal).
- **Cascade damage from agent runaway.** Closed by D 5.10 (touch budget per operation).
- **Audit-trail loss when content is removed or overwritten.** Closed by D 5.11 (rollback / quarantine policy), D 8.7 (forget vs supersede skills).
- **Partial-state corruption from mid-ingest failure.** Closed by D 7.12 (serial queue with caching and bounded retries).
- **Read-but-not-understood at the source page.** Closed by D 7.11 (translation rule for source pages).
- **Silent-stale failures (source changes, derived pages don't).** Closed by D 7.14 (re-verification trigger), D 11.5 (staleness threshold), D 8.5 (lint cadence).
- **Slip-box contamination during drafting.** Closed by D 2.11 (project workspace / desktop separate from slip-box).
- **Index-as-directory navigation collapse.** Closed by D 9.8 (entry-points-only index) plus D 3.8 (hub notes as orientation pages).
- **Pipeline-rot detection failure (silent breakage of the agent pipeline).** Closed by D 8.12 (demo and golden-snapshot tests).
- **Tags-as-noise (index fills with content-derived keywords that don't surface notes).** Closed by D 4.13 (question-derived tag strategy).
- **Rendered-view drift from source.** Closed by D 12.10 (Markdown as source of truth even with a published view).
- **Standardize-the-wrong-thing (workflow standards calcify around outdated practice).** Closed by D 1.7 (standardize organizational decisions only; spend the budget on substance).
- **Willpower depletion across the workflow.** Closed by D 1.7 (standardize the environment).
- **Block-when-stuck on a single manuscript.** Closed by D 11.9 (Verbund / parallel projects).
- **Draft bloat (cutting feels like loss, so cuts don't happen).** Closed by D 2.12 (cut-prose graveyard).
- **Duplicate citation maintenance across wiki and external writing.** Closed by D 12.9 (reference-manager integration).
- **Other agents can't read the wiki (multi-agent setups).** Closed by D 12.11 (MCP / external-tool surface).
- **Publication-friction failures (wiki content hard to share outside Markdown).** Closed by D 8.13 (view-builder skill), D 12.10 (rendering layer).
- **Session-start cost from unbounded memory growth.** Closed by D 6.7 (operational size caps for memory and log files).
- **Log-scan failures (weekly review can't summarize unstructured prose).** Closed by D 9.9 (structured log entry shape).
- **Rationalization failures during audit (agent justifies drift instead of exposing it).** Closed by D 7.13 (yes/no audit prompt style).
- **Custom-relation maintenance burden (lint must enforce relation semantics).** Closed by D 4.12 (one or two link kinds, not custom relation types).
- **Ahrens mistake #1 (every note permanent).** Closed by D 7.1 (commit points limit promotion), D 7.9 (save-back is opt-in).
- **Ahrens mistake #2 (project-only notes).** Closed by D 2.5 (projects outside the wiki), D 2.3 (single wiki).
- **Ahrens mistake #3 (all notes fleeting).** Closed by D 2.4 (inbox + triage), D 8.2 (triage skill), D 11.1 (daily cadence), D 11.5 (24h threshold).
- **Bookkeeping fatigue (Ahrens-pure failure).** Closed by D 1.1 (LLM does bookkeeping).
- **Cognitive bypass (Karpathy-pure failure).** Closed by D 1.2 (human is load-bearing), D 7.1 (commit points), D 7.7 (manual promotion).
- **Sensitive-data leakage in inspectable Markdown / Git history.** Closed by D 1.8 (redaction-before-ingest policy).
- **Confirmation-bias accumulation in the user's own thinking.** Closed by D 3.10 (disconfirming-evidence capture mechanism, distinct from cross-source contradictions).
- **Concept page reads as a paper summary instead of a reusable idea.** Closed by D 3.11 (self-explanatory permanent-note rule), D 7.11 (translation rule for source pages).
- **Silent-corpus-corruption from non-LLM sync tools.** Closed by D 5.12 (sync-adapter and external-write policy).
- **Re-ingest drift (running ingest again produces a different page).** Closed by D 7.15 (idempotency policy), D 7.12 (content caching).
- **Watch-mode bypass of takeaway approval.** Closed by D 7.16 (hybrid watch mode that keeps the commit point).
- **Non-technical-adoption failures (user gets stuck at first integration).** Closed by D 8.15 (onboarding wizard).
- **Index-as-directory even with entry-points-only.** Closed by D 9.11 (one or two notes per index keyword).
- **"Wrote it once and never saw it again" failure that defeats the slip-box's compounding property.** Closed by D 11.10 (spaced retrieval of old notes).
- **Lost-decision failures from rejecting AI session transcripts.** Closed by D 10.10 (selective transcript ingest with higher promotion bar).
- **Bulk-load noise on first run.** Closed by D 8.14 (setup-only without auto-ingest), or mitigated by D 7.5 (curated batches).
- **"I can't read my own wiki" failure when prose is fully LLM-optimized.** Closed by D 4.14 (hybrid optimization target — concepts human-readable, indices LLM-optimized).
- **Orientation drift (agent reads stale index at session start).** Closed by D 5.13 (required index/log update on every write).
- **Critical-fact oversight (agent misses a load-bearing fact buried in MEMORY.md or hot.md).** Closed by D 6.8 (pinned `CRITICAL_FACTS.md` tier).
- **Duplicate-page accumulation at write time.** Closed by D 7.17 (prefer-update policy).
- **Important non-obvious connections never made.** Closed by D 7.18 (human writes substantive cross-references; LLM writes mechanical backlinks).
- **Backlink drift over time as pages rename and move.** Closed by D 8.16 (dedicated rebuild-backlinks skill).
- **Lint-blindness for targets the check set omits.** Closed by D 8.17 (standard or full BP §7.5 lint check set).
- **Page exists but is invisible (orphan).** Closed by D 9.12 (strict reachability invariant or demote-to-draft on orphan detection).
- **Hub-as-directory drift (hub note holds too many links and stops being a navigation aid).** Closed by D 4.15 (hub-note link-density cap).
- **"Writing about what you don't yet know" (Ahrens ch. 13 failure).** Closed by D 7.19 (bottom-up topic-selection policy enforces clusters before drafts).
- **Lost-insight failures when project notes archive.** Closed by D 7.20 (project-to-slip-box routing operation).
- **"User never notices the cluster" failure that defeats bottom-up emergence.** Closed by D 8.18 (active synthesis-scan skill).

---

## What this catalogue does not cover

Three classes of decision deliberately left out, with reasons.

**Implementation-language choices.** Whether scripts are Python, Node, or Rust; whether the editor is Obsidian or something else at the syntax level; specific library choices for BM25, embeddings, OCR. These are downstream of D 12.3, D 12.4, D 9.7 and depend on local environment.

**Collaboration mechanics.** Specifically: branch / merge / review patterns when multiple humans write to the same wiki. The pattern's boundary conditions (D 1.4, D 12.2) imply this is out of scope. If multi-user is needed, the relevant decisions live in source control / CMS literature, not here.

**Aesthetics and editor styling.** Theme files, custom CSS, visual rendering. These do not affect the integration's discipline.

---

## Source files

Citations in this document refer to:

- **BP §N** = `a-archive/reference/llm-wiki-best-practices.md`, section N. The exhaustive synthesis of the public Karpathy-pattern record.
- **Ahrens ch. N** = `a-archive/reference/smart-notes-summary.md`, chapter N. The faithful distillation of Sönke Ahrens, *How to Take Smart Notes* (2017).
- **Karpathy gist** = https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- **Karpathy on X** = https://x.com/karpathy/status/2039805659525644595

Specific repos cited in BP §14 (kfchou/wiki-skills, Astro-Han/karpathy-llm-wiki, NicholasSpisak/second-brain, Pratiyush/llm-wiki, SamurAIGPT/llm-wiki-agent, maeste/my-2nd-brain, rvk7895/llm-knowledge-bases, lucasastorian/llmwiki, simonsysun/seeklink, nvk/llm-wiki, etc.) have URLs in the source file.

The **opinionated integration design** that picks one position in this decision space lives at `a-archive/reference/smart-notes-llm-wiki-integration.md`. **The live wiki schema** picks another position and lives at this repo's `CLAUDE.md`. Both are worth consulting as worked examples once the design space here is internalized.
