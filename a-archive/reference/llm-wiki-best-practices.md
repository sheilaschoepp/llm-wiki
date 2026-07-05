# Building an LLM knowledge base: best practices

> Combined synthesis of the public record around Karpathy's "LLM Wiki" / "LLM Knowledge Bases" pattern. Citations point to original primary sources only — Karpathy's gist and X post, GitHub repos, Reddit threads, Hacker News comments, blog posts.
>
> **Terminology note.** Karpathy's own labels are "LLM Wiki" (gist) and "LLM Knowledge Bases" (X post). "Second brain" is community language, not Karpathy's. Distinguishing pattern (Karpathy's) from prompt (community-derived) matters for citation hygiene — many of the most-shared "Karpathy prompts" are community starter prompts and schema files, not Karpathy's own words.
>
> **Verification status.** Sources verified against their primary URLs; re-check before relying on any link. Repos that did not verify are flagged inline as `[unverified]` and listed in Appendix A; Reddit / X / gist-comment claims that could not be fetched are flagged inline and listed in Appendix B.

## 1. The thesis

Karpathy's pattern asks an LLM to compile each new source once into a persistent, interlinked Markdown wiki, and then to maintain that wiki — adding entity and concept pages, fixing backlinks, flagging contradictions, updating an index. The pattern fails when treated as "ask the model to do all of that"; it works when the human still does the cognitive work (deciding what matters, paraphrasing, promoting drafts) and the LLM is restricted to the bookkeeping (linking, indexing, formatting, lint). Ahrens called this "external scaffolding to think in" — the slip-box mechanism that makes a Zettelkasten compound. The LLM-wiki pattern automates exactly the bookkeeping operations Ahrens names while the human keeps the cognitive operations. The whole rest of this document is consequences of that one separation.

Karpathy's framing: "the wiki is a persistent, compounding artifact"; "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase"; the gist itself is "designed to be copy pasted" into your own LLM agent — the file is a pattern to instantiate, not a finished product to clone ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f); [Karpathy on X](https://x.com/karpathy/status/2039805659525644595); the [X trending page](https://x.com/i/trending/2042013766036926944) where the term "LLM Knowledge Bases" went viral is a separate primary citation worth keeping for terminology hygiene — the X-side label differs from the gist-side label). The originating X post (2026-04-03, with the gist following ~two days later) framed it as a personal shift in usage: a large share of his recent token throughput had moved away from manipulating code and toward manipulating knowledge — i.e. using LLMs to build personal knowledge bases for research topics. That framing matters for a survey because it locates the pattern as a *use-mode* observation, not a product launch ([Karpathy on X](https://x.com/karpathy/status/2039805659525644595); exact wording cross-checked against secondary write-ups, not re-fetched from X directly).

## 2. The architecture

Three explicit layers, plus one implicit:

```text
raw/         immutable source documents
wiki/        LLM-maintained Markdown — sources, concepts, entities, syntheses, index, log
schema       CLAUDE.md / AGENTS.md / SCHEMA.md — operating contract
[scripts]    deterministic helpers — lint, search, link audit, line-anchored read
```

The first three are Karpathy's. The fourth is what every working community implementation adds. Across the verified GitHub repos, the projects that ship a `doctor` / `lint` / `health` / `verify` / `rebuild-backlinks` command are the ones whose READMEs read like real systems rather than concept demos ([gowtham0992/link](https://github.com/gowtham0992/link); [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki); [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent); [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault); [simonsysun/seeklink](https://github.com/simonsysun/seeklink)). Markdown plus a clever prompt is not enough past a small corpus.

## 3. Why this is not RAG

Vanilla RAG re-derives each answer from chunks at query time. Karpathy's pattern compiles knowledge once into a structured artefact that compounds across sessions. Two consequences worth taking seriously.

**Token economics flip.** A precompiled wiki plus a small index is cheaper to read each session than re-embedding and re-retrieving over the source corpus. Community reports give two distinct point estimates rather than a smooth range: roughly **65%** non-ingest token reduction in one Reddit thread (heavy workflows moved out of the always-loaded root prompt) and roughly **90%** in another, both unverified ([unverified] r/ClaudeAI and r/ObsidianMD threads, see Appendix B). The most cited single example is a *code-wiki* variant that cut session start from ~47,450 tokens to ~360 by reading a precompiled wiki instead of exploring code from scratch. Treat magnitudes as plausible direction, not exact figure.

**The model maintains the files, not just answers from them.** This is the part naive implementations skip, and where most of them fail ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). If the LLM only answers from the wiki without updating it, the wiki rots; if it updates the wiki without human review, the wiki accumulates plausible-but-wrong "facts." The pattern lives on the seam between those two failure modes.

**The provider-level grounding: context rot and structured note-taking.** The pattern's mechanism is named directly in Anthropic's own context-engineering guidance, which is worth citing for a survey because it grounds the wiki in model architecture rather than in community lore. Two claims do the work. First, **context rot**: because the transformer lets every token attend to every other (n² pairwise relationships), a model has a finite "attention budget," and recall accuracy *degrades* as the context window fills — so stuffing raw sources into context every session is not just expensive, it actively reduces answer quality past some point. Second, **structured note-taking (a.k.a. agentic memory)**: the named technique of having the agent "regularly write notes persisted to memory outside of the context window" that "get pulled back into the context window at later times" — which is precisely what an LLM-maintained wiki *is*. Anthropic pairs this with **just-in-time retrieval** — keeping lightweight identifiers (file paths, stored queries) and loading data on demand rather than pre-loading it — which is the same index→page navigation discipline §10 advocates, and explicitly the model Claude Code uses (`CLAUDE.md` dropped in up front, `glob`/`grep` for the rest). The same source's closing heuristic, "do the simplest thing that works," is the provider-level version of §10's markdown-first escalation order ([Anthropic, *Effective context engineering for AI agents*](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). The companion piece on long-running agents frames the problem the wiki solves with a useful analogy — sessions are like engineers working in shifts where each new shift arrives with no memory of the last — and notes that compaction alone is insufficient, which is the argument for an external persisted artefact rather than just summarizing the conversation ([Anthropic, *Effective harnesses for long-running agents*](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)). One honest boundary: Anthropic's framing is about a *single agent's* working memory across its own sessions, whereas the LLM-wiki pattern is also a *human's* durable knowledge store — the techniques overlap on persistence but diverge on who the artefact is ultimately for (the §19 tension).

**The strongest case against the pattern** (worth stating in full, because §3 otherwise reads as advocacy). The sharpest published critique argues this is *not* a "bye-bye RAG" moment and that the wiki can be strictly worse than RAG for serious use. The mechanism: in vanilla RAG the model re-reads the immutable source each query, so a one-off misread is just one wrong answer and the *next* query has a fresh chance to get it right; the wiki instead bakes a misread into a page that is then read back, re-cited, and cross-linked — converting *random, self-correcting* errors into *organized, persistent* ones. Worse, those errors are camouflaged: a clean Wikipedia-style page *reads* as trustworthy regardless of whether its claims are grounded. And because building a wiki requires summarizing and compressing, the lossy step strips exactly what serious work depends on — edge cases, exact wording, subtle distinctions — which the raw documents in a RAG corpus still preserve for traceback ([Gupta, "Andrej Karpathy's LLM Wiki is a Bad Idea"](https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-wiki-is-a-bad-idea-8c7e8953c618)). This is not a fringe objection; it is the same compounding-error mechanism the SSGM survey formalizes (§13) and the reason every safeguard in this document — immutable `raw/` for traceback, claim-level provenance, the human promote gate, contradiction sections, lint — exists. The honest reading: the critique is correct about the failure mode and correct that naive implementations realize it; the pattern's defenders are betting that the bookkeeping safeguards plus a disciplined human keep the compounding under the line where the compounding benefit (pre-linked synthesis) outweighs it. Where you can't fund that discipline, or where exact wording is load-bearing (legal, medical, regulatory), RAG-with-traceback is the safer default — which is also the §13 "boundary conditions" conclusion.

## 4. The Ahrens grounding (one paragraph)

Sönke Ahrens's *How to Take Smart Notes* (2017) describes the same architecture with different vocabulary: a reference system (= `raw/`), a slip-box of atomic permanent notes (= `wiki/concepts/` plus `wiki/syntheses/`), an index of entry-points (= `wiki/index.md`), separated from project notes (= `projects/<name>/` outside the wiki) and fleeting notes (= an `inbox/` triaged within 24 hours). Ahrens's key argument: writing is the medium of thinking, not its output; the slip-box externalizes the bookkeeping the brain is bad at so the brain is freed for what only it can do. The LLM-wiki pattern automates exactly the bookkeeping operations Ahrens names — wikilinks, index maintenance, contradiction scanning — while the human keeps the cognitive operations (paraphrasing, promotion, atomic-note discipline). Treating this as the foundation rather than as a complementary framework explains every other decision in this document. The full integration design is in `a-archive/reference/smart-notes-llm-wiki-integration.md`; the upstream Ahrens summary is in `a-archive/reference/smart-notes-summary.md`.

## 4.1 The public lineage: v1 → v2 → v3

The pattern now has a small canonical lineage worth tracking, because later iterations name the failure modes the originals only gestured at, and because the community increasingly cites them by version number. All three are URL-verified primary sources.

**v1 — Karpathy's gist** (`karpathy/442a6bf555914893e9891c11519de94f`, created 2026-04-04). Append-only ingest, manual lint, human-readable notes. The canonical pattern; everything in this document grounds on it.

**v2 — rohitg00's fork** (`rohitg00/2067ab416f7bbe447c1977edaaa681e2`, "LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory", last active 2026-05-25). This is the source the earlier drafts of this document referenced only as an anonymous "LLM Wiki v2 gist comment" — it is in fact a named, dated fork drawn from the author's work on [agentmemory](https://github.com/rohitg00/agentmemory), a persistent-memory engine. v2's substantive additions over v1: a **memory lifecycle** (confidence scoring, supersession, an Ebbinghaus-style retention/forgetting curve, and four consolidation tiers — working → episodic → semantic → procedural); a **typed knowledge graph** layered over the pages (entity extraction, typed edges like `uses`/`depends on`/`contradicts`/`caused`/`supersedes`, graph traversal for queries); **hybrid search** (BM25 + vector + graph fused with reciprocal-rank fusion); **event-driven automation** (hooks on new-source / session-start / session-end / query / memory-write / schedule); quality scoring and self-healing lint; multi-agent mesh sync with shared/private scoping; ingest-time PII filtering and an audit trail; and "crystallization" (distilling a completed work-thread into a first-class wiki page). v2's own framing — *"the schema document is the real product"* — is the sharpest one-line statement of §6's thesis. Note that v2's design is candidly tuned for short agent-observation chunks; the author states book-length ingestion is not yet stress-tested, which is consistent with §11's "long PDFs and books" caveat ([rohitg00 v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)).

**v3 — Ghelbur's rebuild** (`eugeniughelbur/obsidian-second-brain`, MIT, in production since 2026-03, shipped as a cross-CLI Claude Code / Codex / Gemini / OpenCode skill). v3 adds three things v2 still lacks: **scheduled agents** (nightly close-out, weekly reconciliation + synthesis, periodic health check — the answer to "maintenance only happens when you remember it, so it never happens"); **unsolicited synthesis** (the wiki proactively surfaces unnamed recurring themes and connections you did not ask about); and the **AI-First Vault Principle** (notes written for LLM retrieval rather than human reading). Its two most transferable lessons, independent of the repo: ingest should **rewrite the live page, not only append a backlink** (so the top of every page carries the current best answer, with superseded versions preserved dated below), and automation should be **"everything reversibly, not everything always"** — every scheduled write lands in a daily diff note and waits 24 hours before becoming permanent. The AI-First Vault Principle is in direct tension with this document's promote gate (§7.3); that tension is treated as an open question in §19, not silently resolved ([Ghelbur writeup](https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres); [repo](https://github.com/eugeniughelbur/obsidian-second-brain)).

One dating caveat: the v3 writeup repeatedly dates Karpathy's gist to "2026-02," but the gist page itself, and multiple independent walkthroughs, give **2026-04-04**. This document uses the April date; do not let the v3 source's February claim propagate backward into the lineage.

## 5. Folder layout

The most-used variant after community modifications, with the additions Ahrens's discipline implies:

```text
knowledge-base/
  CLAUDE.md          # short operating rules + pointers to skills
  SCHEMA.md          # page types, frontmatter, citation rules
  inbox/             # Ahrens fleeting notes — triaged daily, never auto-ingested
  raw/               # immutable source-of-truth docs
    articles/
    pdfs/
    transcripts/
    notes/
  wiki/              # LLM-maintained Markdown
    index.md         # navigational index — entry points, not a topic ontology
    log.md           # append-only change log
    overview.md      # optional top-level summary
    hot.md           # carry-over context for sporadic sessions
    sources/         # one literature note (paraphrased summary) per raw source
    concepts/        # atomic permanent notes — one idea per file
    entities/        # people, projects, tools, datasets
    syntheses/       # cross-source permanent notes
    questions/       # saved investigations
    decisions/       # reusable decisions / rationale
    contradictions.md
    gaps.md
  projects/          # project-specific notes — outside the slip-box
  scripts/           # deterministic helpers
    lint_links.py
    lint_frontmatter.py
    find_orphans.py
    find_drafts.py             # status: draft pages overdue for promotion
    find_stale_inbox.py        # 24-hour Ahrens rule
    search_bm25.py
  reports/           # lint / doctor / ingest outputs
  skills/            # operational skills, split from CLAUDE.md
    wiki-triage.md
    wiki-ingest.md
    wiki-promote.md
    wiki-query.md
    wiki-lint.md
    wiki-update.md
```

The separation of `wiki/sources/` from `wiki/concepts/` and `wiki/entities/` is load-bearing. Without it, the LLM's synthesis pages cite each other and gradually amplify earlier mistakes ([NicholasSpisak/second-brain wiki-schema.md](https://github.com/NicholasSpisak/second-brain/blob/main/skills/second-brain/references/wiki-schema.md)).

## 6. Schema and operating contract

Two things go in the schema. First, the **page-type contract** as YAML frontmatter on every page:

```yaml
---
type: source | concept | entity | synthesis | question | decision
title:
aliases: []
tags: []
sources:
  - path:
    locator:               # page, section, paragraph, timestamp, or URL fragment
    date_accessed:
status: draft | active | superseded
confidence: low | medium | high
last_updated:
---
```

Second, the **operating rules** themselves: where files live, never edit `raw/`, every claim cites a source, prefer updating an existing page over creating a near-duplicate, contradictions go in a `Contradictions` section until resolved, every write updates `index.md` and `log.md`. Reference implementations that encode this concretely: [NicholasSpisak/second-brain wiki-schema.md](https://github.com/NicholasSpisak/second-brain/blob/main/skills/second-brain/references/wiki-schema.md); [Pratiyush/llm-wiki AGENTS.md](https://github.com/Pratiyush/llm-wiki/blob/master/AGENTS.md); [SamurAIGPT/llm-wiki-agent AGENTS.md](https://github.com/SamurAIGPT/llm-wiki-agent/blob/main/AGENTS.md).

**Split the schema from operations.** Keep `CLAUDE.md` short — global rules and pointers to skills only. Move ingest, query, lint logic into separate skill files. The community converged on this after monolithic `CLAUDE.md` files reached 300+ lines and started consuming significant context every session. One reported refactor shrank the file from ~300 lines to 104, saving roughly 1,960 tokens per session ([unverified] r/ObsidianMD thread). The counter-warning, also from that thread: too many overlapping micro-skills create router errors ("the agent picks the wrong skill on ambiguous requests"). Sweet spot: short global rules plus a few clearly named skills with explicit "when not to use this skill" guidance.

## 7. The four-stage cycle

The whole system is one loop: capture → ingest → maintain → query → save back. Each stage has a hard rule about what the LLM may and may not do.

For a survey framing, this loop maps onto the **write–manage–read** formalism that the 2026 agent-memory literature uses to decompose any external-memory system: *write* (capture + ingest, here gated by human triage), *manage* (maintain — lint, contradiction handling, supersession, the part most blog implementations underbuild), and *read* (query). Recent surveys formalize agent memory precisely as a write–manage–read loop coupled to perception and action, and treat the *manage* stage as the under-explored one — which matches this document's emphasis on lint and the promote gate as the load-bearing, most-skipped operations ([Du, *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers*, arXiv 2603.07670](https://arxiv.org/abs/2603.07670); see also [Luo et al., *From Storage to Experience*, arXiv 2605.06716](https://arxiv.org/abs/2605.06716), which frames the same evolution as storage → reflection → experience). The Karpathy pattern is a *human-curated, markdown-substrate* instance of this general loop; the academic systems differ mainly in automating the *manage* stage and in substrate (databases, vector stores, learned controllers) rather than in the loop's shape.

### 7.1 Capture and triage

Fleeting notes go to `inbox/`, not `raw/` or `wiki/`. Within ~24 hours the human triages each item: trash, promote to a literature note (if it cites a source), or convert to a concept-page draft. The LLM may *propose* triage but never commits it; this is the cognitive operation Ahrens insists on. If the LLM is allowed to auto-promote, the wiki accumulates LLM voice and the slip-box's compounding stops working — exactly the failure mode warned about in the Hacker News critique that "auto-generated notes can look good until someone actually reads them."

### 7.2 Ingest

The ingest is staged, with the agent talking to the user **before** writing anything:

```text
1. Read CLAUDE.md / SCHEMA.md, wiki/index.md, wiki/log.md, wiki/hot.md (if present).
2. Read the full raw source.
3. Produce a "candidate takeaways" summary (3–8 bullets — sources disagree: kfchou wiki-ingest specifies 3–5, Karpathy-help diagnosis specifies 5–8; pick a number for your skill file rather than leaving it to the model) and pause.
4. Discuss with the user: which to keep, what to emphasize, what is in/out of scope.
5. Write or update the source page (wiki/sources/) — paraphrased, in the user's voice.
6. Draft concept / entity / synthesis pages with status: draft.
7. Add citations back to raw locators (file path + page/section).
8. Scan existing pages for backlinks and contradictions.
9. Update wiki/index.md and wiki/log.md.
10. Run health checks; report what changed.
```

The "discuss takeaways before writing" step is what protects the wiki from compounding errors. Without it, the wiki becomes a "plausible but mis-prioritized summary of what the user actually cares about" ([unverified] r/ClaudeAI). The kfchou skill pack encodes this protocol explicitly in [`wiki-ingest/SKILL.md`](https://github.com/kfchou/wiki-skills); Astro-Han packages the same idea in a single SKILL.md ([Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)).

Three ingest invariants are non-negotiable across working implementations:

- **Stop dumping too many sources at once.** Curated batches of 10–20 sources from one domain. The clearest "worked for a real corpus" example is a TrainingSites tutorial that ingested 180+ videos for a video-library knowledge base; the author's recommendation is to start with ten videos before scaling, on the grounds that bulk-loading large corpora before the discipline is in place produces low-signal noise ([unverified] TrainingSites tutorial; original URL not located during verification).
- **Serialize ingest with retries and content caching.** SHA-256 caching, a serial queue, up to three retries, a guaranteed source-summary step ([nashsu/llm_wiki](https://github.com/nashsu/llm_wiki)).
- **Save useful answers back into the wiki.** Substantial investigations become `wiki/questions/<topic>.md` or `wiki/syntheses/<topic>.md` pages that future queries reuse ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). One implementer described their six-month variant: it reads session transcripts after coding sessions, extracts decisions and rejected approaches, then requires human review before anything is promoted into persistent context — the human directs exploration while the LLM does the bookkeeping ([unverified] HN comment on Karpathy gist).

### 7.3 Promote (the review gate)

LLM-drafted concept pages stay at `status: draft` until the human re-voices them and promotes to `status: active`. Draft pages are excluded from query results unless explicitly requested. This is the second human-in-the-loop commit point (after triage). It is the place where Ahrens's paraphrasing discipline enters the LLM workflow; without it, the wiki accumulates LLM-voice text that fails the AI-writing-tells filter and accumulates the "ingest errors compound" failure mode named below.

### 7.4 Query

The best query prompts are aggressively grounded:

```text
query: <question>
- read hot.md, index.md, and any folder _context.md files first
- answer from wiki/ first
- only open raw/ if the wiki is insufficient
- cite the exact wiki pages or source pages used
- do not answer from model memory
- exclude status: draft pages by default
- if the answer creates a reusable synthesis, ask whether to save it
```

The contrast with vanilla "ask my notes" prompting: this forbids model-memory answers, requires citing wiki pages, and offers to save high-value answers back. That round-trip is the compounding mechanism. The kfchou query skill enforces a similar ordering — read the index first, then the relevant pages, synthesize with wiki citations, offer to save the result ([kfchou/wiki-skills](https://github.com/kfchou/wiki-skills)).

One underused refinement: **named query templates** — pre-built, reusable prompts that extract a specific *kind* of insight rather than answering a one-off question (e.g. "summarize everything that contradicts hypothesis X," "trace the causation chain from decision D," "list every source that superseded an earlier claim this month"). Templates pay off most once the typed-link layer (§8) exists, because the useful ones query relationship types directly; without typed edges they collapse back into generic keyword search ([Level Up Coding walkthrough](https://levelup.gitconnected.com/beyond-rag-how-andrej-karpathys-llm-wiki-pattern-builds-knowledge-that-actually-compounds-31a08528665e)).

### 7.5 Maintain (cheap health + heavier lint)

Two passes, separated for cost reasons. The clearest cadence guidance comes from `SamurAIGPT/llm-wiki-agent`: **health every session, lint every 10–15 ingests** ([AGENTS.md](https://github.com/SamurAIGPT/llm-wiki-agent/blob/main/AGENTS.md)). Tying lint to ingest volume rather than a calendar interval matches the real failure rate — drift accumulates per ingest, not per day.

**Health** (cheap, deterministic, run every session): empty files, index drift, log coverage, broken wikilinks, frontmatter validity.

**Lint** (semantic, costs tokens, run every 10–15 ingests or weekly, whichever comes first):

- orphan pages
- claims with no source
- source files not represented in wiki
- wiki pages with no raw-source references
- duplicate pages
- stale pages past last-updated threshold
- contradictions
- pages exceeding size limits
- concept pages that cite only other concept pages (recursion smell)
- draft-status pages overdue for promotion

Treat contradictions as first-class objects: keep both claims under a `Contradictions` section until the human resolves them. This is one of the most-cited lessons in the community discussion. As one Reddit implementer put it: "the lint step is non-negotiable" ([unverified] r/AI_Agents). One contradiction-detection layer worth knowing about: [Jasonleonardvolk/sigma-guard](https://github.com/Jasonleonardvolk/sigma-guard), which does deterministic contradiction detection over memory graphs with reproducible proofs.

## 8. Page typology and atomicity

Five frontmatter `type` values, each with a clear role:

- *source* — paraphrased summary of one raw document. One file per source. Confidence high (sources are immutable). Tied to a `raw/` locator.
- *concept* — one atomic idea, self-explanatory, reusable across topics. **One idea per file** — non-negotiable.
- *entity* — a person, project, tool, dataset, organization.
- *synthesis* — cross-source claim that doesn't reduce to a single concept or entity.
- *question* — a saved investigation: answer plus the wiki pages cited.
- *decision* — a reusable choice and its rationale.

The atomicity rule is the part the LLM will resist on its own. Left alone, an LLM drifts toward writing topic pages that try to be comprehensive. Atomicity has to be enforced in the schema: one idea per file, one main claim per file, every page must answer "from what other contexts would I want to stumble upon this?" That second question generates the wikilinks. The first question — "where does this go?" — generates the failure mode Ahrens spent ch. 6 of *How to Take Smart Notes* warning against (Ahrens 2017, ch. 6).

**Page size limits** make atomicity enforceable: roughly **400-line soft cap, 800-line hard cap** ([unverified] r/AI_Agents). Beyond that, edits become whole-file rewrites and the model loses the thread. Once the wiki gets large, sharded indexes plus line-anchored retrieval are needed. The `PATH:LINE` retrieval pattern (with a context window, e.g. `-C 20`) is documented in [simonsysun/seeklink](https://github.com/simonsysun/seeklink). The "LLM Wiki v2" fork recommends BM25 + vector search + graph traversal + reciprocal-rank fusion for larger systems, but only after the basics are working ([rohitg00 v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2); see §4.1).

**Typed links: the most-named missing piece in the base pattern.** A plain `[[wikilink]]` records *that* two pages connect but not *how* — the relationship's meaning lives in the surrounding prose, invisible to any tool. Penfield Labs makes the sharpest version of this critique: Karpathy describes the LLM "noting where new data contradicts old claims" and "flagging contradictions," but the link format itself cannot express `supports` versus `contradicts` versus `supersedes`, so the most valuable structural information stays trapped in unstructured text — defeating the point of compiling a wiki in the first place ([Penfield "what's missing" article](https://dev.to/penfieldlabs/what-karpathys-llm-wiki-is-missing-and-how-to-fix-it-1988)). The concrete fix is a typed-relationship vocabulary. Their [PENgram](https://github.com/penfieldlabs/pengram) pipeline classifies every edge into one of **24 semantic types**, grouped: knowledge-evolution (`supersedes`, `updates`, `evolution_of`), evidence (`supports`, `contradicts`, `disputes`), hierarchy (`parent_of`, `child_of`, `sibling_of`, `composed_of`, `part_of`), causation (`causes`, `influenced_by`, `prerequisite_for`), implementation (`implements`, `documents`, `tests`, `example_of`), conversation (`responds_to`, `references`, `inspired_by`), sequence (`follows`, `precedes`), and dependencies (`depends_on`) — plus **8 code-structure types** for codebase corpora (`calls`, `imports`, `uses`, `extends`, `implements_interface`, `instantiates`, `overrides`, `decorates`). Two design choices are worth lifting independent of the tooling. First, **every edge carries a confidence label** — `EXTRACTED` (stated in the source), `INFERRED` (deduced from context), or `AMBIGUOUS` — on the principle that a graph where every edge claims equal confidence is lying to you; this is the edge-level analogue of the claim-level provenance in §9. Second, the Obsidian implementation ([penfieldlabs/obsidian-wikilink-types](https://github.com/penfieldlabs/obsidian-wikilink-types)) keeps the types human-writable as inline `@supersedes` / `@contradicts` syntax that auto-syncs to YAML frontmatter, so the same edge is both Dataview-queryable ("show everything that contradicts my current hypothesis") and LLM-readable. The honest caveat, also from Penfield: typing every link by hand is tedious and misses non-obvious connections, so the relationship discovery is itself delegated to the LLM (their "Vault Linker" skill) — which re-imports the §13 trust problem one level up, since an LLM-inferred `contradicts` edge can be as wrong as any other LLM claim. Treat AI-discovered edges as `INFERRED` and gate them the same way as draft pages. This typed-link layer is the concrete schema behind the vaguer "typed knowledge graph" the v2 fork gestures at (§4.1).

## 9. Provenance and citations

Working implementations require **claim-level provenance**, not just a bibliography at the bottom of each page. A working rule:

```text
Every non-obvious factual claim in a wiki page must include:
- source file path
- page, paragraph, timestamp, section, or URL locator
- confidence level (low | medium | high)
- date last checked
```

Two reasons: it stops the model from inventing references, and it gives a deterministic validator (a script) something to check. The community pattern of `compile --review` flags or claim-bearing JSON runners that reject confabulated source links recurs across multiple implementations. The validator approach is cheaper than human review and catches the most common failure: the LLM invents a plausible-looking but non-existent source URL. Pair claim-level provenance with a script that opens each cited path and confirms it exists.

## 10. Retrieval discipline and scale

Markdown plus a flat `index.md` is enough for a Karpathy-scale corpus — Karpathy's own example anchor is roughly **100 articles / 400K words** ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)) — provided lint runs consistently. It breaks past that. The escalation order, in increasing cost:

1. **Lexical search (BM25, `ripgrep`, or `qmd`)** — cheap, deterministic, no infrastructure. The `qmd` referenced in Karpathy's gist as a local Markdown search engine is [`tobi/qmd`](https://github.com/tobi/qmd) (consistently the one community skill files link); other unrelated projects share the name, so confirm before installing. `ripgrep` and BM25 work equivalently for most personal-vault scales.
2. **Sharded indexes** — once flat `index.md` becomes navigable in name only.
3. **Line-anchored retrieval (`PATH:LINE` plus context window)** — once pages exceed ~1,000 lines and edits start touching whole files.
4. **Embeddings / vector search** — when lexical search misses on paraphrase queries.
5. **Graph traversal and reciprocal-rank fusion** — for entity-resolution at scale.
6. **Entity-resolution layer** — when duplicate entities outpace manual cleanup.

The general rule: markdown-first until the pain is specific and obvious, then add a narrow capability for that specific pain. Adding embeddings, OCR, a graph database, and routing on day one is the most-cited failure pattern in the community discussion.

## 11. Document handling

Karpathy's gist names the raw types explicitly as **"articles, papers, images, data files"** — the pattern is built for a heterogeneous corpus, not just text. The PDF stays untouched in `raw/papers/` as the source of truth, but the agent works from a Markdown extraction beside it:

```text
raw/papers/
  transformer-paper.pdf      # immutable original
  transformer-paper.md       # extracted/converted text
wiki/sources/
  transformer-paper.md       # paraphrased literature note
wiki/concepts/
  attention-mechanism.md
  transformer-architecture.md
```

Long books are still cumbersome. Karpathy's own advice in the gist comments: **if a book is plain text, EPUB is probably the best source**; otherwise process chapter by chapter; keep images local and describe them textually ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). The "plain text" precondition matters — image-heavy or highly typeset books need a different ingest path regardless of format.

OCR is **optional, on-demand**. Successful projects make it a module rather than a default. [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) makes Mistral OCR optional in hosted mode; [domleca/llm-wiki](https://github.com/domleca/llm-wiki) (Obsidian plugin) assumes clean text by default and only invokes OCR when the source needs it.

For web sources, the practical failure mode is paywalls, JavaScript-heavy pages, and walled domains — prompt instructions alone don't solve source acquisition. Implementations that handle web well add a dedicated fetcher, a browser fallback, or a Web Clipper integration ([maeste/my-2nd-brain CLAUDE.md](https://github.com/maeste/my-2nd-brain/blob/main/CLAUDE.md)).

**Three branches of "what counts as truth."** When the corpus is something other than a research-style document set, the pattern forks. Karpathy's own pattern is **research-first** — raw documents are truth, the wiki summarizes and links them. Codebase-rationale variants like `tuandm/code-wiki` are **rationale-first** — the *code* is truth and the wiki captures *why* (decisions, gotchas, confidence bands such as 0.8+ for verified versus 0.3–0.5 for draft) rather than what the code does. The same fork pairs that with a human-audit prompt of the form "I assumed X because I saw Y. Correct?" — yes/no rather than open-ended elicitation, which forces the agent to expose its reasoning before drift accumulates ([unverified] gist comment thread; the `tuandm/code-wiki` repo URL did not surface during verification — see Appendix A. The *patterns* — confidence bands, audit-by-yes/no — recur across multiple verified repos and are worth lifting independently of the unverified citation). Pure code-structure variants like `Houseofmvps/codesight` are **structure-first** — they avoid prompt engineering during compilation by using ASTs and regexes, producing a deterministic wiki with no LLM in the compile path ([unverified] gist comment thread). The three branches imply different prompt shapes, different validation needs, and different failure modes; do not assume a research-wiki prompt will work on a codebase corpus or vice versa.

## 12. What works (positive evidence)

Patterns that recur across the verified primary sources and community discussion:

**Linking and maintenance burden goes down**, especially for users who previously bounced off "networked thought" tools because the link-keeping was too much manual work. The most concrete public anecdote is from "Be Datable," a long-time personal-knowledge-graph user who described their newer setup: voice notes → local transcription → LLM extracts signal → wikilinks created automatically — a workflow that only became viable once the LLM took over the link-keeping ([unverified] Be Datable post, original URL not located during verification).

**Cross-document synthesis improves** because relationships are pre-linked and pre-summarized; the model isn't rediscovering them at query time.

**Token savings** when expensive context (codebase, large prompt schema) is precompiled into a wiki — direction confirmed by multiple reports, exact magnitudes unverified. One code-wiki variant reported cutting session start from ~47,450 tokens to ~360 by reading a precompiled wiki instead of exploring code from scratch ([unverified] r/ClaudeAI).

**Continuity across sporadic sessions.** `hot.md` plus a small index carries enough state that users come back after gaps without re-explaining everything.

**Concrete walkthrough evidence.** A "Build Karpathy's Second Brain With Obsidian + Claude Code" podcast / video walks the full setup with timestamps: setup wizard at 05:53, graph view at 12:21, ingest at 15:38, automated ingestion at 16:29, lint and pruning at 20:19. Useful as evidence that the workflow is demonstrable end-to-end, not just describable; weaker as evidence of long-horizon reliability ([unverified] podcast/video listing; original URL not located during verification).

**Decision logs, project memory, research corpora, repeated work** are the strongest fits — better than generic note-taking. The pattern is most powerful when there's something durable to compound: investigations across many sources, decisions worth referring back to, project state that survives context resets.

**Independent confirmation from an existing PKM practitioner.** A Zettelkasten/Obsidian user (six months on Nick Milo's LYT framework with Claude Code) compared the pattern against his own mature system and named three operations his hand-built setup lacked: contradiction detection during ingest (his atomic cards don't cross-compare), cross-page chain updates (one new source updating 10–15 pages at once, where he only adds links manually), and — the one he singled out as most powerful — **concept-gap detection**, the LLM proactively noticing "you've referenced this idea in several places but have no dedicated page for it" and offering to create one. Useful as evidence that the pattern adds something even to a disciplined pre-existing PKM practice, not just to greenfield vaults ([WenHao Yu review](https://yu-wenhao.com/en/blog/karpathy-zettelkasten-comparison/)).

**At Karpathy-scale (hundreds of pages, hundreds of thousands of words), index summaries plus wiki links can be enough** — Karpathy's own framing is that an agent-maintained wiki with indexes and summaries can work without **"fancy RAG"** at his scale ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). The "fancy RAG" phrasing matters because it draws the line where the basic pattern stops being enough; once the corpus or churn outgrows that line, embeddings and graph layers come back into scope (see §10 escalation order).

**Markdown / Obsidian / Git baseline is praised because it's inspectable.** Users can read the wiki, see links, view the graph, diff changes, and avoid opaque memory layers ([Obsidian](https://obsidian.md); [Marp](https://marp.app); [Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview)). Several repos position this as a plain-text, agent-agnostic, privacy-aware alternative to closed "AI memory" products. Karpathy's gist also references [Tolkien Gateway](https://tolkiengateway.net) as a mental model for richly interlinked pages — a useful target image for what a mature wiki feels like (entity pages dense with backlinks, not isolated topic essays).

**Lightweight starts work surprisingly well.** A MindStudio blog post describes the setup as "a Markdown content folder plus Claude Code rather than a dedicated product," and reframes the wiki as optimised for *model* reading more than human browsing — useful intuition, because it explains why dense wikilinks beat prose summaries even when the prose looks nicer to a human reader ([unverified] MindStudio blog). Mark Chen's Medium post claims he created two structured wikis in about an hour, one for Medium writing and one for BI reporting, using Claude Code — direction-only evidence that the pattern is easy to start, not proof it stays reliable at scale ([unverified] Medium post).

Several short community quotes capture the trade-off neatly:

- **"Just fed Karpathy's recipe to Claude…"** — common framing for the "paste the gist and pray" failure mode ([unverified] community thread).
- **"Claude picking the wrong one on ambiguous requests."** — the over-splitting failure mode behind the schema/skill sweet spot ([unverified] r/ObsidianMD).
- **"The lint step is non-negotiable."** — why §7.5 exists ([unverified] r/AI_Agents).
- **"The Wiki significantly outperformed RAG on 'deleted' or archived logic."** — the differential value vs RAG; the mechanism (RAG re-derives from chunks, the wiki preserves the curated reasoning) is sound, magnitude unverified ([unverified] r/ClaudeAI).

## 13. What fails (the risk register)

The academic framing worth adopting before the list: in an *evolving* memory system, errors are not isolated the way a single bad RAG retrieval is — they are **cumulative and persistent**, because a wrong write is read back, re-summarized, and re-cited until it gains the authority of consensus. The SSGM work formalizes this as a **compounding failure loop** across three interfaces: input ingestion (**poisoning** — a bad or adversarial source enters), memory consolidation (**semantic drift** from repeated summarization, and **procedural drift** where a suboptimal workflow gets reinforced), and memory retrieval (**hallucination** surfaced as fact). This is the peer-reviewed version of the document's recurring "ingest errors compound" warning, and it is the single best argument for why the *manage* stage (§7) and the human gates (§7.1, §7.3) are not optional polish ([SSGM, arXiv 2603.11768](https://arxiv.org/html/2603.11768v1)). A related security survey adds a temporal wrinkle worth noting for any shared or multi-agent vault: a poisoned entry can be written in the *write* phase but lie dormant until *retrieve/execute* days later in an unrelated task, which is what distinguishes a memory attack from a single-session prompt injection ([arXiv 2604.16548](https://arxiv.org/html/2604.16548v1)). The entries below are the concrete, community-observed instances of this loop, grouped by which system component breaks.

**Trust / audit.** Fully LLM-generated wikis have hallucination risk, weak provenance, broken links, no audit trail, no editorial oversight unless those are explicitly engineered. *Fix:* human-in-the-loop ingest, claim-level provenance, lint, mandatory human promotion gate.

**Ingest errors compound.** A slightly wrong source summary becomes a "fact" cited across linked pages, gaining authority over time. *Fix:* paragraph-level attribution, contradiction sections, easy rollback, the "discuss takeaways before writing" step.

**Semantic gravity.** Wiki pages alone do not reliably override misleading schemas, names, APIs, or column labels. The community example: one user built a 200+ page wiki for a supply-chain AI use case and the agent kept ignoring a page that explicitly warned against using a misleading `FINAL_REASON` field — it kept grouping by it anyway. *Fix:* structural, not editorial. Rename the field (`LEGACY_FINAL_REASON_DO_NOT_USE`), add a validated query template, add a lint rule that rejects answers using the field, add a tool wrapper that prevents selecting it ([unverified] r/AI_Agents).

**Noise accumulation.** LLMs write too much. Auto-generated notes look fine until someone actually reads them. Scraping transcripts without intentional human capture is garbage in, garbage out ([unverified] HN comments).

**Prompt and skill sprawl.** Monolithic `CLAUDE.md` (300+ lines) wastes tokens every session; over-splitting (10+ skills) creates router errors. *Sweet spot:* short global rules plus a few unambiguous skills with explicit "when not to use this skill" guidance.

**Whole-file edit bottleneck.** Once pages exceed ~1,000 lines, the agent re-reads the whole file to update one paragraph. Symptoms: token burn, drift, unrelated sections breaking. *Fix:* "surgical edits rather than broad rewrites" (the framing the praneybehl Claude Code plugin author uses) plus line-anchored retrieval before edits ([simonsysun/seeklink](https://github.com/simonsysun/seeklink)).

**Maintenance ratchet.** A failure mode named in the praneybehl Reddit post: as the wiki grows, the system spends more and more time maintaining itself — silent corruption accumulates, the wiki drifts by reading its own outputs as if they were sources, and human attention gets eaten by upkeep rather than work. Distinct from noise accumulation (which is about LLM verbosity) and whole-file edits (which is about retrieval). *Fix:* validators, claim-level provenance, scope limits on what the maintenance loop is allowed to touch — better prompts alone won't catch it ([unverified] r/AI_Agents).

**Long PDFs and books.** Hard to summarize accurately in one pass. Karpathy's own advice: prefer EPUB; otherwise ingest chapter by chapter; keep images local and describe them textually ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)).

**Memory lifecycle missing.** Not all knowledge stays equally valid forever. Without confidence scoring, supersession, retention curves, and forgetting, old or weak claims rot into permanent context. *Fix:* explicit `status: superseded` field, periodic `last_updated` checks, retention rules. This is the central argument of the v2 fork, which proposes the full lifecycle apparatus — confidence decay, Ebbinghaus retention curves, four consolidation tiers ([rohitg00 v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2); see §4.1) — but note the two pointed counter-arguments to that apparatus in the next two entries.

**Decay repeats mistakes; confidence floats are false precision.** The most substantive critique of the lifecycle apparatus, from the v2 comment thread (Mattia83it, 2026-05-04): forgetting curves are a *biological* model tied to capacity constraints a wiki does not have, and applying decay to errors and superseded decisions is exactly how you repeat them — an old bug report is often *more* valuable than a recent one, and a superseded decision record still explains why the current one exists. The proposed primitive is **explicit supersession, not decay**: the old page stays, headed by a pointer to whatever replaced it, with Git as the audit trail. Separately, a numeric confidence score (`0.85`) dresses a claim in authority its evidence did not earn; the real, verifiable signal is the *chain of links* a claim carries (which sources, which related decisions, which commits). *Fix:* prefer supersession headers and link-chain provenance over retention curves and confidence floats; filter at ingest rather than in retention. (This view is in direct tension with the v2 fork it is replying to — the document does not adjudicate; both are live positions.)

**No-provenance / no-rollback in event-driven automation.** A blunter critique from the same thread (gnusupport, 2026-04-14) against treating v2 as a build plan rather than a vocabulary: event-driven auto-ingest assumes reliable LLMs, which silently corrupt the store on hook-triggered writes; "confidence scoring" and "auto-crystallize" are underspecified (who computes the score, what triggers crystallization, how dedup works); and the design omits versioning, rollback, per-fact provenance ("which agent wrote this, from what source?"), human-readable addresses for citing a fact, and back-links. *Fix:* human-in-the-loop as a write gate is quality control, not backwardness, when the writer is a stochastic process; pair any automation with reversibility (cf. v3's "everything reversibly" — daily diff notes, a 24-hour hold before changes become permanent) ([rohitg00 v2 gist comment thread](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)).

**Raw-source safety.** "raw is immutable" is often only prose, not enforcement. Sync tools can overwrite history or silently ingest the wrong corpus. *Fix:* runtime immutability guardrails (e.g., `chmod -w`), quarantine overwrites, make non-AI sync adapters opt-in.

**Anti-RAG framing oversold.** Good search still matters at larger vault sizes; one shouldn't delegate understanding entirely; document parsing and clean Markdown ingest are the actually-hard parts. For some corpora, simplified summaries introduce a lossy extra layer rather than helping ([unverified] r/learnmachinelearning).

**Privacy and cost at organizational scale.** Cloud LLMs raise data-handling concerns; ingest workflows have non-trivial cost at corpus sizes beyond personal vaults. One implementer who processed ~2,000 Brave bookmarks reported the workflow cost ~$15 with retries; enterprise use needs permissions, source tracking, update logic, and cost control ([unverified] gist comment thread).

**Boundary conditions.** The pattern works best for "small-to-medium, slow-moving, human-curated research folders." It is much weaker for "large, fast-changing, high-stakes, multi-user, or enterprise knowledge bases" ([unverified] gist permalink comment). Use it for personal vaults, book / fan wikis, evolving research topics, internal team KBs. Stay with classic RAG for high-churn material, regulatory-critical content (legal, medical), and very large corpora. A prior question, raised in the more measured community commentary: *do you need one at all?* The pattern earns its maintenance cost only when there's a durable, synthesis-heavy corpus to compound — "most 15-person accounting firms aren't sitting on hundreds of research papers they need cross-referenced." The failure mode of adopting it without that corpus is "an AI talking to itself," which is the §3 critique realized by over-application rather than by bad implementation ([Lobster Pack](https://www.lobsterpack.com/blog/karpathy-llm-wiki-idea-files/)).

**Public partial-failure cases worth reading.** The [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki/issues) issue tracker exposes real onboarding and ingest problems — partial failures with poor messaging, local-only / read-only complaints. Specific issues to browse: [#60](https://github.com/Pratiyush/llm-wiki/issues/60) and [#326](https://github.com/Pratiyush/llm-wiki/issues/326) — both URLs were not refetched (egress-limited); browse the tracker for current state.

## 14. Skills, plugins, and reusable repos (verified URLs only)

**Five forks of the pattern.** Across the verified primary sources the public ecosystem splits roughly five ways. Knowing which fork a repo belongs to is the fastest way to decide whether it suits your corpus.

1. *Schema-heavy vaults* — hard rules for immutability, frontmatter, index/log maintenance, lint cadence. Examples: `NicholasSpisak/second-brain`, `Pratiyush/llm-wiki`.
2. *Command-oriented variants* — tiny user surface (`ingest`, `query`, `health`, `lint`, `build graph`, `reflect`) backed by skill files on disk. Examples: `kfchou/wiki-skills`, `SamurAIGPT/llm-wiki-agent`.
3. *Codebase-oriented forks* — move from "documents as truth" to "code as truth" and use the wiki to capture rationale and gotchas. See the three-way contrast in §11.
4. *Scale-oriented forks* — add search, graph generation, embeddings, or entity resolution where the minimal markdown pattern starts to break. Examples: `lucasastorian/llmwiki`, `swarmclawai/swarmvault`, `Tencent/WeKnora`.
5. *Convenience-oriented packages* — wrap the whole thing in onboarding skills for non-technical users, often with paused workflows for exports / permissions / logins. Example: `charlie947/ai-second-brain`.

Almost all five forks preserve the same base loop — immutable sources, compiled wiki, navigational index and log, human-curated sources, LLM-maintained summaries and cross-links. They differ in *where* they add operational structure and how much they trust deterministic tooling versus prompts.

The two compact starters singled out across multiple verified primary sources, both URL-verified. Strong starting recommendation: pick one of these before reaching for any of the larger stacks.

- **kfchou/wiki-skills** — clean six-skill decomposition (`wiki-init`, `wiki-ingest`, `wiki-query`, `wiki-lint`, `wiki-update`, `wiki-audit`). Singled out as one of the cleanest publicly available prompt decompositions. [Repo](https://github.com/kfchou/wiki-skills).
- **Astro-Han/karpathy-llm-wiki** — single-skill SKILL.md, Agent Skills compatible. Includes `raw/` / `wiki/`, index/log maintenance, compile rules, cascade updates, linting. [Repo](https://github.com/Astro-Han/karpathy-llm-wiki).

**Larger schema / skill repos** worth reading before installing:

- [NicholasSpisak/second-brain](https://github.com/NicholasSpisak/second-brain) — strict schema, frontmatter rules, lint schedule. Multi-agent support via templates for Claude / Codex / Cursor / Gemini. [wiki-schema.md](https://github.com/NicholasSpisak/second-brain/blob/main/skills/second-brain/references/wiki-schema.md).
- [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki) — schema-heavy fork built around a **single-source-of-truth schema**: every page derives from one canonical source page, never from another wiki page. Adds **per-project `hot.md` "hot caches"** (one per project rather than a single global file), `MEMORY.md`, `CRITICAL_FACTS.md`, cross-session memory, sync/build/serve workflows. Documented operational defaults: 50 KB log auto-archive, 200-line memory cap, folder-context threshold for `_context.md` (threshold value itself unspecified in the public files), other parameters (temperature, `top_p`) unspecified. Turns AI session transcripts into sources, entities, concepts, syntheses, comparisons, and questions; produces both human-facing pages and AI-consumable exports (`llms.txt`, JSON-LD, per-page text/JSON). Design principles: works offline, redaction defaults, idempotency, agent-agnostic, privacy-by-default. [AGENTS.md](https://github.com/Pratiyush/llm-wiki/blob/master/AGENTS.md); [CLAUDE.md](https://github.com/Pratiyush/llm-wiki/blob/master/CLAUDE.md).
- [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent) — Python helpers for `health`, `lint`, `build_graph`. Deterministic checks every session. [AGENTS.md](https://github.com/SamurAIGPT/llm-wiki-agent/blob/main/AGENTS.md).
- [maeste/my-2nd-brain](https://github.com/maeste/my-2nd-brain) — opinionated, productized; `CLAUDE.md` contract, URL-to-Markdown inbox fetching, deterministic lint, view builders for timelines / comparisons / reports / slides / posts; commands `save`, `view`, `reflect`, `forget`. Operational guardrail worth lifting: a **touch budget of ≤15 files per operation** with unattended-mode restrictions — limits cascade damage when the agent goes wrong. The `reflect` command writes a `compass.md` with current direction, blind spots, and one question worth sitting with — a useful pattern even if you don't adopt the rest of the stack. Practical failure mode flagged: URL fetching breaks on paywalled or JavaScript-heavy domains, requiring browser or Web Clipper fallbacks. [CLAUDE.md](https://github.com/maeste/my-2nd-brain/blob/main/CLAUDE.md).
- [rvk7895/llm-knowledge-bases](https://github.com/rvk7895/llm-knowledge-bases) — research plugin with quick / standard / deep query modes; explicit model routing — Opus orchestrates, Haiku does mechanical scanning, Sonnet writes. Worth singling out because, in the verified primary sources, this is the only repo with an explicit per-role model policy in its prompt files; the rest leave temperature, `top_p`, and model choice unspecified. If you care about model routing, this is the reference to copy. [CLAUDE.md](https://github.com/rvk7895/llm-knowledge-bases/blob/master/CLAUDE.md).
- [charlie947/ai-second-brain](https://github.com/charlie947/ai-second-brain) — guided onboarding; integrates ChatGPT / Claude histories, Gmail, NotebookLM, Granola, iMessage; pauses for user action when exports / permissions / logins are needed.
- [rohitg00/llm-wiki (v2)](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) + [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) — the "v2" architecture doc (see §4.1) plus the persistent-memory engine its lessons came from. agentmemory reports a 95.2% LongMemEval-S score from running BM25 + vector + knowledge-graph retrieval fused with RRF — one of the few quantified retrieval benchmarks in this ecosystem, though it measures the engine, not a markdown-wiki-and-lint baseline, and the *-S* split is weak enough that the number should be read with the caveats in §19 (it likely fits in a frontier context window, and self-reported memory scores rarely share a methodology). Read v2 for the lifecycle/graph/automation vocabulary; read §13's two counter-critiques before adopting the apparatus wholesale.
- [eugeniughelbur/obsidian-second-brain (v3)](https://github.com/eugeniughelbur/obsidian-second-brain) — the "v3" rebuild (see §4.1). Cross-CLI Claude Code / Codex / Gemini / OpenCode skill, MIT, in production since 2026-03 and actively churning (the command count has moved 31 → 43 across releases, so cite the *capabilities* — scheduled agents, write-back-not-append ingest, unsolicited synthesis, a write-time AI-first validator, role presets — rather than a fixed number). The non-negotiable house rule worth lifting even if you adopt nothing else: scheduled writes land in a daily diff note and wait 24 hours before becoming permanent. Its AI-First Vault spec (`references/ai-first-rules.md`) is the reference artifact for §19's open tension.
- [SHzzzAyys/scholarbrain](https://github.com/SHzzzAyys/scholarbrain) — academic-research fork of obsidian-second-brain, cited upstream as the first domain-specialized proof case. Worth a look specifically for a research-survey workflow, though browse the repo to confirm current state before relying on it (newer and thinner than the forks above).
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — engineering / llm-wiki skill inside a larger claude-skills monorepo. Skill landing page: https://alirezarezvani.github.io/claude-skills/skills/engineering/llm-wiki/.
- [nvk/llm-wiki](https://github.com/nvk/llm-wiki) — single `wiki-manager` skill shared across Claude / Codex / OpenCode / Pi via symlinks.
- [praneybehl/llm-wiki-plugin](https://github.com/praneybehl/llm-wiki-plugin) — Karpathy pattern packaged as a Claude Code plugin. Documented design: a natural-language-triggered skill, **five slash commands**, **four Python scripts**, soft and hard page-length caps, sharded indexes after the wiki grows, YAML frontmatter, and "surgical edits rather than broad rewrites." Author reports using the pattern for "a couple of months" on a research project before packaging — useful as a stress-tested reference design rather than a fresh experiment.
- [hsuanguo/llm-wiki](https://github.com/hsuanguo/llm-wiki) — "LLM wiki that evolves with you."
- [mduongvandinh/llm-wiki](https://github.com/mduongvandinh/llm-wiki) — Vietnamese-language Karpathy-pattern KB.
- [skyllwt/OmegaWiki](https://github.com/skyllwt/OmegaWiki) — large research-oriented implementation; ~23 skills covering full research lifecycle.
- [6eanut/llm-wiki](https://github.com/6eanut/llm-wiki) — Claude Code skill, persistent interlinked KB.
- [NousResearch/hermes-agent (llm-wiki skill)](https://github.com/NousResearch/hermes-agent/tree/main/skills/research/llm-wiki) — built-in skill in NousResearch's hermes-agent.

**Application-style stacks:**

- [gowtham0992/link](https://github.com/gowtham0992/link) — ships `doctor`, `verify-mcp`, `rebuild-backlinks`, demo mode, golden-snapshot tests. The "sanity loop" template (demo → ingest → inspect → lint/doctor → repair → query).
- [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) — `context build`, `graph validate --strict`, shrink guards, export/serve, watch mode, local Whisper / ffmpeg / document ingest.
- [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) — strict filesystem source of truth, rebuildable SQLite graph/search, optional Mistral OCR, MCP config, full converter stack.
- [aws-samples/sample-kiro-llm-wiki](https://github.com/aws-samples/sample-kiro-llm-wiki) — wiki-first mode in Kiro, protected `raw/`, bootstrap / auto-ingest, MCP fetch integration.
- [nashsu/llm_wiki](https://github.com/nashsu/llm_wiki) — two-step ingest, SHA-256 cache, serial queue, retries, guaranteed source-summary step, optional vector search.
- [domleca/llm-wiki](https://github.com/domleca/llm-wiki) — Obsidian plugin; local-first hybrid search, background re-extraction, source-linked answers; defaults to local models (`qwen2.5:7b`, `nomic-embed-text`).
- [Tencent/WeKnora](https://github.com/Tencent/WeKnora) — Tencent's open-source LLM knowledge-base platform with Wiki Mode.
- [Beever-AI/beever-atlas](https://github.com/Beever-AI/beever-atlas) — chat-platform ingest variant; Apache 2.0.
- [doum1004/llmwiki-cli](https://github.com/doum1004/llmwiki-cli) — CLI for LLM agents to build / maintain personal KBs (`init`, `write`, `search`, `lint`, `status`, `orphans`).

**Code-truth variants** (different fork — see §11 three-way contrast). Both are referenced in the gist comment thread but did not URL-verify; treat as patterns worth knowing rather than safe-to-cite repos. Search GitHub before installing; both are also listed in Appendix A.

- `Houseofmvps/codesight` — zero-LLM code-wiki compiler that uses ASTs and regexes to compile a persistent wiki from source code, read at agent session start. No LLM or API calls during compilation, so temperature is irrelevant and the output is deterministic.
- `tuandm/code-wiki` — rationale-first codebase wiki with confidence bands (0.8+ verified vs 0.3–0.5 draft), `docs-check` re-verification on relevant code changes, and the human-audit yes/no prompt pattern.

**Adjacent fix layers** (not full implementations, useful as components):

- [simonsysun/seeklink](https://github.com/simonsysun/seeklink) — line-anchored retrieval (`PATH:LINE`), hybrid search, optional MCP, blind tests. Solves the whole-file-edit bottleneck.
- [Jasonleonardvolk/sigma-guard](https://github.com/Jasonleonardvolk/sigma-guard) — deterministic contradiction detection over memory graphs, reproducible proofs, sample datasets.
- [penfieldlabs/pengram](https://github.com/penfieldlabs/pengram) — a *pipeline*, explicitly not a KB system: takes raw content (code via tree-sitter AST across 25 languages, plus markdown / PDF / EPUB / YouTube captions), extracts entities, classifies edges into the 24 + 8 typed vocabulary (see §8), and emits `graph.json` + an interactive `graph.html` + a `GRAPH_REPORT.md` (with "god nodes," surprising connections, suggested questions), optionally also writing an Obsidian or Penfield vault. The architecture is a clean **three-pass separation worth copying regardless of the tool**: (1) deterministic AST extraction (no LLM, no hallucination risk), (2) local transcription (Whisper, on-device), (3) LLM semantic extraction (local or remote) — only the last pass can hallucinate, which localizes the trust problem. SHA-256 incremental caching, crash-safe per-file checkpointing, `--watch` for living corpora, and provider-flexible (claude-cli default, OpenAI, OpenRouter, Ollama; cheap models for extraction, heavier for synthesis). MIT, v0.1.0 — early, so treat as a reference design more than a dependency. The architectural patterns are credited to [safishamsi/graphify](https://github.com/safishamsi/graphify), a codebase-to-graph tool whose three-pass design PENgram generalizes from untyped to typed edges.
- [penfieldlabs/obsidian-wikilink-types](https://github.com/penfieldlabs/obsidian-wikilink-types) — the Obsidian plugin for the typed-link layer in §8: inline `@type` wikilink syntax auto-synced to frontmatter, AGPL-3.0, plus the bundled "Vault Linker" skill spec for AI-discovered relationships.

**Gist-comment ecosystem projects** (descriptions from gist comment thread; specific permalink fetches blocked, see Appendix B):

- *TheKnowledge* — the canonical example of claim-level source links, span anchors, validators that reject confabulated source URLs, NotebookLM-style artefacts, MCP, and Obsidian integration. The provenance pattern recommended in §9 traces directly to this project's gist comment ([unverified] gist comment). Search the comment thread on Karpathy's gist before installing.
- *Beever Atlas* — team-native variant with Neo4j + Weaviate + multi-stage ingestion pipeline. Repo: [Beever-AI/beever-atlas](https://github.com/Beever-AI/beever-atlas).
- *NEXUS* — 6-agent **VPS** (cloud server) stack: **Weaviate** (vector store), **Ollama** (local LLM runner), **Wiki.js** (rendering layer), and multiple MCP servers in front. The cloud-server framing is the load-bearing contrast: Karpathy's baseline runs locally on a markdown vault; NEXUS runs on a remote multi-service stack. Worth knowing as a worked example of "the maximalist build" and as the foil to the markdown-first defaults. Multiple sources cite it as evidence that heavier graph/vector stacks help only after the markdown-and-lint baseline is working, not on day one ([unverified] gist comment thread).

## 15. Reproducible diagnostic experiments

Run these against your current implementation to localize the problem before adding more layers.

**Duplicate detection.** Create two `raw/` files with near-identical content. Expected: one canonical concept page plus a duplicate-candidate report or merge path. Symptom of weak handling: two independent concept pages.

**Staleness propagation.** Add a `raw/` file that contradicts an earlier source ("we standardized on SQLite" → "we replaced SQLite with Postgres"). Expected: existing derived pages marked stale or `needs review` before the system answers confidently. Symptom: both claims kept silently, no surfaced conflict.

**Whole-file edit bottleneck.** Create one ~1,500-line Markdown file. Ask the system to update one paragraph near line 1,200. Compare token usage and correctness against a line-anchored retrieval call. Symptom: agent re-reads the whole file or breaks unrelated sections.

**OCR necessity.** Run one clean digital PDF and one scanned PDF through the same pipeline. If the scanned one produces unreliable pages, route only scanned sources through OCR. Don't fix this with prompt tweaks first.

## 16. Eight rules

If acting on a few things, these are what the verified primary sources converge on.

1. Keep `raw/` immutable, and enforce it at runtime, not just in prose.
2. Start with markdown, index, log, and wikilinks before adding embeddings or graph layers.
3. Use a tiny user command surface; put long instructions in skill files on disk, not in chat.
4. Separate cheap structural checks (`health`) from expensive semantic lint.
5. Keep a `hot.md` or equivalent carry-over note.
6. Require citations or source references on every wiki claim.
7. Use human audit on ingest and whenever the agent starts inferring rationale.
8. Only add graph / entity-resolution / vector infrastructure once the real failure is duplication or navigation at scale, not before.

## 17. Likely reasons your implementation isn't working

Synthesised across the verified primary sources, ranked by frequency:

1. Using the gist as a broad instruction instead of a strict skill / schema.
2. Wiki pages don't require source-level citations.
3. Model is not forced to read `index.md`, `log.md`, and relevant pages before answering.
4. No separate source-summary layer — the wiki recursively cites itself as truth.
5. Ingesting too much at once.
6. Missing lint / backlink / contradiction passes.
7. Pages too large or too loosely typed.
8. Relying on prose warnings where structural constraints or validation are needed.

The fastest fix the source recommends: adopt one of the verified starter skills above (kfchou or Astro-Han), ingest a small curated source set, and make linting + citations mandatory from the start.

## 18. Templates (copy-paste-ready)

### 18.1 System-prompt skeleton

```text
You maintain a compiled knowledge wiki for the user.

Truth model
- raw/ is immutable source material and the source of truth.
- wiki/ is your workspace. You may create, update, and cross-link pages there.
- output/ holds reports, views, and other generated artefacts.

Non-negotiable rules
- Never modify raw/ except explicit user-directed deletion workflows.
- Every writing operation updates wiki/index.md and wiki/log.md.
- Every claim in wiki/ must point to one or more source pages or raw source files.
- When new information conflicts with existing content, preserve both claims under a Contradictions section until resolved.
- Prefer updating an existing page over creating a near-duplicate.
- LLM-drafted concept pages stay at status: draft until the user promotes them.

Required orientation before work
- At session start, read wiki/hot.md if it exists.
- Then read wiki/index.md and any relevant folder _context.md files.
- Only descend into raw/ when wiki/ is insufficient.

Core operations
- triage: walk inbox/, propose for each item: trash | promote-to-source | promote-to-concept-draft. Never auto-commit.
- ingest <path>: read source, discuss key takeaways with user, update source/entity/concept pages, then update index and log.
- promote <page>: human-driven; user re-voices the draft, status flips to active.
- query: answer from the wiki first, then read raw sources only if needed.
- health: run cheap structural checks first.
- lint: run semantic checks for contradictions, stale claims, missing pages, duplicates.
- reflect: optional; write a short compass note about where the knowledge base is heading.

Default folders
- wiki/sources/
- wiki/entities/
- wiki/concepts/
- wiki/syntheses/
- wiki/views/   # optional
```

### 18.2 First-time bootstrap

```text
I want you to implement a Karpathy-style wiki in this folder.

Context
- Viewer/editor: Obsidian
- Corpus type: [research papers / articles / meetings / code rationale / mixed]
- Expected scale in the next 3 months: [small curated / medium / large]
- Output needs: [plain markdown only / reports / slides / charts / graph]

Please do the following:
1. Create raw/, wiki/, output/, inbox/, projects/.
2. Draft a CLAUDE.md or AGENTS.md that defines triage, ingest, promote, query, health, lint.
3. Add wiki/index.md and wiki/log.md starter files.
4. If helpful, add wiki/hot.md and folder _context.md stubs.
5. Keep the initial command surface minimal and unambiguous.
6. Before creating any optional extras, explain the trade-offs.
7. Then guide me through ingesting one source end-to-end.
```

### 18.3 Ingest

```text
ingest raw/<file-or-folder>

Before you write anything:
- tell me the key takeaways in 5-8 bullets
- list the pages you expect to create or update
- flag any ambiguity, contradiction, or missing metadata

Then:
- write or update the source page (paraphrased, in my voice)
- draft the most relevant entity / concept / synthesis pages with status: draft
- add wikilinks under Connections
- update index and log
- if you inferred anything weakly, mark it as tentative rather than factual
```

### 18.4 Query / health / lint bundle

```text
query: <question>
- read hot.md, index.md, and any folder _context.md files first
- answer from wiki/ first
- only open raw/ if the wiki is insufficient
- cite the exact wiki pages or source pages used
- exclude status: draft pages by default
- if the answer creates a reusable synthesis, ask whether to save it

health
- check empty files, index drift, log coverage, broken links
- do not spend tokens on semantic analysis yet

lint
- after health passes, check contradictions, stale claims, duplicates, orphan pages, missing high-value pages, draft-status pages overdue for promotion
- give me a short report first, then ask before fixing anything substantial
```

## 19. Open questions in the public record

Four limitations worth naming, in case any of them is worth chasing later.

**Independent benchmarks are thin.** Many strong claims are maintainer-authored; few controlled, third-party evaluations of full LLM-Wiki systems exist. Adjacent retrieval benchmarks exist — Daniel Yarmoluk's CKG (curated knowledge graph) benchmark is one — but they don't directly evaluate Karpathy-style markdown wikis ([unverified] CKG benchmark; original URL not located during verification). Treat any headline accuracy number with the same skepticism the document applies elsewhere. The cleanest worked example of why: the v2 fork (§4.1) reports 95.2% on LongMemEval-S, a real and widely-cited long-term-memory benchmark (Wu et al., [arXiv 2410.10813](https://arxiv.org/abs/2410.10813), ICLR 2025; 500 questions across five abilities — information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention). But Penfield Labs argues the *-S* split is too easy to mean much: at ~115K tokens per question it fits inside a frontier model's context window, so it functions more as a context-length test than a memory test, and because each system uses its own ingestion, answer-generation prompt, and sometimes its own judge, scores published in a shared table rarely share a methodology. Their exhibit is the documented Mem0/Zep dispute, where two parties evaluating the same systems arrived at wildly divergent numbers ([Penfield benchmark proposal](https://dev.to/penfieldlabs/proposal-a-real-benchmark-for-long-term-ai-memory-systems-57p5)). The harder regime (LongMemEval-M, ~500 sessions per history, where context-stuffing breaks down) is the one that would actually discriminate a compiled wiki from a long-context baseline, and almost nobody reports it. Net: a single benchmark number from a system's own author is weak evidence; ask which split, whose judge, and whether the corpus exceeds the model's context window before believing it.

**The ecosystem is young.** Most relevant *implementation* repos and posts are from April–May 2026; long-horizon reliability data isn't there yet. Expect continued churn and watch for shake-out around which patterns survive 6+ months of real use. The *academic* literature on the underlying problem (agent memory / external memory) is more developed and moving fast — a cluster of 2026 surveys (write–manage–read, storage→experience, externalization, memory security; see §7 and §13) now formalizes much of what the implementation community discovered empirically. For a survey, cite the academic framing for the mechanisms and risks, and the gist/repo ecosystem for the specific markdown-wiki instantiation; they are describing the same loop at different altitudes.

**The Karpathy / community split.** "LLM Wiki" is Karpathy's own term; "second brain" is community language. Many of the most-shared "Karpathy prompts" are not Karpathy's own words — they're community starter prompts and schema files derived from his pattern. Distinguishing pattern (Karpathy's) from prompt (community-derived) matters for citation hygiene.

**Human-voiced notes vs. the AI-First Vault — an unresolved fork in the pattern's purpose.** This document's promote gate (§7.3) rests on Ahrens's claim that paraphrasing in your own voice *is* the thinking, so an LLM-drafted page stays `status: draft` until a human re-voices it. The v3 rebuild attacks exactly this premise: it argues that in a vault where the LLM does almost all the reading, optimizing notes for human reading is optimizing for a reader who never shows up. Its AI-First Vault Principle writes every page for retrieval instead — a `## For future Claude` preamble, machine-readable frontmatter, mandatory wikilinks, per-claim recency markers, verbatim source URLs, self-contained context — and its house style rule is explicit: *do not rewrite vault output to be "more human-friendly."* The two positions are not reconcilable by compromise; they disagree about who the wiki is *for*. The Ahrens view predicts the AI-first vault accumulates ungrounded LLM-voice text that no human ever pressure-tests (the §13 "ingest errors compound" and "noise accumulation" failure modes); the AI-first view predicts the human-voicing gate is a bottleneck that guarantees the wiki stays small and is, in practice, the step people skip until the vault rots. A defensible synthesis nobody in the public record has validated yet: keep the human gate for *concept* and *synthesis* pages (where voice encodes judgement) and let *source* and *entity* pages be AI-first (where the value is retrievability, not insight). Treat that as a hypothesis, not a recommendation. The relevant reference artifacts are §7.3 here and `references/ai-first-rules.md` in the v3 repo ([Ghelbur writeup](https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres)).

## 20. Bibliography (verified URLs only)

**Karpathy primary:**
- *LLM Wiki* gist (v1, created 2026-04-04): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- X post: https://x.com/karpathy/status/2039805659525644595

**Lineage forks (v2 / v3) (see §4.1):**
- rohitg00 *LLM Wiki v2* gist: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
- rohitg00 *agentmemory* engine: https://github.com/rohitg00/agentmemory
- Ghelbur *obsidian-second-brain* (v3) repo: https://github.com/eugeniughelbur/obsidian-second-brain
- Ghelbur writeup: https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres
- SHzzzAyys/scholarbrain (academic fork): https://github.com/SHzzzAyys/scholarbrain

**Typed-link / pipeline layer and benchmarks (see §8, §19):**
- Penfield "What Karpathy's LLM Wiki Is Missing": https://dev.to/penfieldlabs/what-karpathys-llm-wiki-is-missing-and-how-to-fix-it-1988
- Penfield "We Fixed Karpathy's LLM Wiki — PENgram": https://dev.to/penfieldlabs/we-fixed-karpathys-llm-wiki-pengram-is-the-typed-knowledge-graph-pipeline-everyone-asked-for-j3j
- Penfield "Proposal: A Real Benchmark for Long-Term AI Memory Systems": https://dev.to/penfieldlabs/proposal-a-real-benchmark-for-long-term-ai-memory-systems-57p5
- penfieldlabs/pengram: https://github.com/penfieldlabs/pengram
- penfieldlabs/obsidian-wikilink-types: https://github.com/penfieldlabs/obsidian-wikilink-types
- safishamsi/graphify (architecture credited by PENgram): https://github.com/safishamsi/graphify
- LongMemEval (Wu et al., ICLR 2025): https://arxiv.org/abs/2410.10813

**Provider-level grounding (Anthropic engineering; see §3):**
- *Effective context engineering for AI agents* (context rot, structured note-taking, just-in-time retrieval): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- *Effective harnesses for long-running agents* (sessions-as-shifts, compaction insufficiency): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- *Equipping agents for the real world with Agent Skills* (the Skills standard the §14 skill-based repos build on): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

**Academic / survey grounding (see §7, §13):**
- Du, *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers* (write–manage–read loop): https://arxiv.org/abs/2603.07670
- Luo et al., *From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms*: https://arxiv.org/abs/2605.06716
- *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering*: https://arxiv.org/html/2604.08224v1
- SSGM, *Governing Evolving Memory in LLM Agents* (compounding failure loop; semantic/procedural drift): https://arxiv.org/html/2603.11768v1
- *A Survey on the Security of Long-Term Memory in LLM Agents* (memory poisoning, write→activation decoupling): https://arxiv.org/html/2604.16548v1

**Critiques and practitioner comparisons (see §3, §12, §13):**
- Gupta, "Andrej Karpathy's LLM Wiki is a Bad Idea" (strongest anti-pattern case): https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-wiki-is-a-bad-idea-8c7e8953c618
- WenHao Yu, "A Zettelkasten User's Honest Review": https://yu-wenhao.com/en/blog/karpathy-zettelkasten-comparison/
- Lobster Pack, "Karpathy's LLM Wiki and the rise of 'idea files'" (Memex lineage, "do you need one"): https://www.lobsterpack.com/blog/karpathy-llm-wiki-idea-files/

**Verified GitHub repos:** all repos listed in §14 above.

**Tooling:**
- Obsidian: https://obsidian.md
- Marp: https://marp.app
- Obsidian Dataview: https://github.com/blacksmithgu/obsidian-dataview
- Tolkien Gateway (mental model for densely interlinked wikis, referenced in Karpathy's gist): https://tolkiengateway.net
- `qmd` (local Markdown search engine, referenced in Karpathy's gist): https://github.com/tobi/qmd — confirm this is the intended one, as other projects share the name.

**Ahrens grounding:**
- Ahrens, *How to Take Smart Notes* (2017)
- `a-archive/reference/smart-notes-summary.md` (single-page distillation)
- `a-archive/reference/smart-notes-llm-wiki-integration.md` (integration design)

## Appendix A: Likely-fictional repos (do not cite without manual confirmation)

Upstream synthesis material references these repos with specific descriptive claims, but their URLs did not surface during verification. Likely fictional or under different paths. Listed here so future synthesis runs don't re-introduce them as verified citations. The body still references some of them (e.g., `tuandm/code-wiki` and `Houseofmvps/codesight`) where the *patterns* are worth surfacing even when the repo URLs don't verify — every such reference is flagged inline as `[unverified]`.

- `tuandm/code-wiki` — `tuandm` exists on GitHub but no `code-wiki` repo found. The "code as truth" / `docs-check` / confidence-bands / "I assumed X because I saw Y. Correct?" pattern is real; something matching may exist under a different username.
- `Houseofmvps/codesight` — no `codesight` repo found at this path. The zero-LLM AST/regex code-wiki compiler pattern is real and worth knowing; the citation is not.
- `QipengGuo/llm-wikidata` — did not surface. Pattern claimed: ChromaDB-backed entity recall to prevent duplicate entities at larger scale.
- `atomicstrata/llm-wiki-compiler` — no search hits. A similarly named `ussumant/llm-wiki-compiler` may exist; not confirmed. Pattern claimed: `compile --review` flags, claim-level provenance, typed page kinds, contradiction metadata, BM25 rerank.
- `yazanabuashour/openclerk` — `yazanabuashour` exists but `openclerk` repo did not surface; most public `openclerk` results are an unrelated PHP/crypto project. Pattern claimed: provenance-bearing JSON runner, stale-projection detection, duplicate-candidate report, optional semantic/OCR modules.

The descriptive features attached to these repos (`compile --review` flags, claim-bearing JSON runners, stale-projection detection, duplicate-candidate reports, line-anchored retrieval, confidence bands, audit-by-yes/no, AST-based deterministic compilation) are real patterns that recur across multiple verified repos — the patterns survive even when individual repo citations don't.

## Appendix B: Unverified Reddit / X / specific gist comments

Egress restrictions blocked direct fetch of Reddit, X, and specific gist permalink comments during the verification pass. The thread IDs did not surface in WebSearch fallback. Specific descriptive claims drawn from these threads — token figures, line counts, the `FINAL_REASON` / "semantic gravity" example, the 65–90% token-savings numbers, the 400 / 800-line caps, the `compile --review` provenance pattern, the $15 / 2,000-bookmark cost figure — are consistent across multiple verified secondary sources but were not independently confirmed at the primary source. Treat as "believe but verify."

- r/AI_Agents: https://www.reddit.com/r/AI_Agents/comments/1sqg5ew/spent_a_weekend_actually_understanding_and/
- r/ClaudeAI (token reductions): https://www.reddit.com/r/ClaudeAI/comments/1sfdztg/90_fewer_tokens_per_session_by_reading_a/
- r/ClaudeAI (second brain as wiki): https://www.reddit.com/r/ClaudeAI/comments/1sc7i84/vibe_code_inventors_second_brain_as_a_wiki/
- r/ObsidianMD (refactor): https://www.reddit.com/r/ObsidianMD/comments/1sqfe7m/i_have_refactored_the_karpathy_llmwiki_and_it_is/
- r/learnmachinelearning (hardest part): https://www.reddit.com/r/learnmachinelearning/comments/1sq5bxl/the_hardest_part_in_building_karpathys_llm_wiki/
- Karpathy gist comment permalink: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6090303
- X trending: https://x.com/i/trending/2042013766036926944
- Pratiyush/llm-wiki issues #60 and #326: https://github.com/Pratiyush/llm-wiki/issues/60 and https://github.com/Pratiyush/llm-wiki/issues/326 (both URLs not refetched due to egress; tracker root browseable for current open issues)

*Resolved:* the "LLM Wiki v2 gist comment" previously cited as unverified in §8 and §13 is identified as `rohitg00/2067ab416f7bbe447c1977edaaa681e2` — see §4.1 and §20. The "memory lifecycle missing" claim it backed, and the two counter-critiques now in §13, are drawn directly from that gist and its comment thread.
