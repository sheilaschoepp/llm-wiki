# Building an LLM knowledge base: best practices

> Consolidated, de-duplicated synthesis of Karpathy's "LLM Wiki" / "LLM Knowledge Bases" pattern, implementation reports, agent-context guidance, evaluation and governance practices, and the literature on multi-refuter factuality verification. Primary sources are preferred; implementation claims whose verification differs across the supplied reports are labelled conservatively.
>
> **Terminology note.** Karpathy's own labels are "LLM Wiki" (gist) and "LLM Knowledge Bases" (X post). "Second brain" is community language, not Karpathy's. Distinguishing pattern (Karpathy's) from prompt (community-derived) matters for citation hygiene — many of the most-shared "Karpathy prompts" are community starter prompts and schema files, not Karpathy's own words.
>
> **Verification status.** v1 URL checks completed 2026-05-09 via WebFetch / WebSearch; v2 comprehensiveness pass completed 2026-05-10; v3 update pass completed 2026-06-02 (added the v1→v2→v3 lineage in §4.1, resolved the previously-anonymous "LLM Wiki v2 gist comment" to its named primary source `rohitg00/2067ab416f7bbe447c1977edaaa681e2`, fetched and verified, and integrated two substantive critiques from its comment thread into §17; added the v3 "append-vs-rewrite" / AI-First Vault material and the §23 tension it creates with the promote gate; verified `rohitg00/agentmemory`, `eugeniughelbur/obsidian-second-brain`, and the `SHzzzAyys/scholarbrain` fork into §18). A second 2026-06-02 pass added the Penfield Labs typed-link layer (24+8 relationship vocabulary, EXTRACTED/INFERRED/AMBIGUOUS edge confidence) to §8 with `penfieldlabs/pengram` + `obsidian-wikilink-types` + `safishamsi/graphify` in §18, named query templates in §7.4, and a substantially expanded §23 benchmarks caveat grounded in LongMemEval (arXiv 2410.10813) and Penfield's methodology critique. A third 2026-06-02 pass added provider-level grounding from Anthropic's engineering blog (context rot / attention budget, structured note-taking, just-in-time retrieval, sessions-as-shifts) to §3. A fourth 2026-06-02 pass added academic grounding: the write–manage–read formalism (arXiv 2603.07670) to §7, the SSGM compounding-failure-loop with semantic/procedural drift (arXiv 2603.11768) and the memory-poisoning temporal-decoupling point (arXiv 2604.16548) to §17, plus related 2026 surveys (arXiv 2605.06716, 2604.08224) and an updated §23 "ecosystem is young" note distinguishing the mature academic literature from the young implementation ecosystem. A fifth 2026-06-02 pass added Karpathy's originating X-post framing (2026-04-03) to §1, the strongest steelmanned critique of the pattern (Gupta) to §3, a "do you need one at all" caution (Lobster Pack) to §17 boundary conditions, and an existing-PKM-practitioner confirmation (WenHao Yu Zettelkasten review) to §16. By this pass, new searches were returning predominantly confirmatory restatements of already-integrated material — the signal that the public record has been substantially covered. Karpathy's gist and X post verified; ~17 GitHub repos verified. Likely-fictional repos (`tuandm/code-wiki`, `QipengGuo/llm-wikidata`, `atomicstrata/llm-wiki-compiler`, `yazanabuashour/openclerk`, `Houseofmvps/codesight`) referenced in body but flagged inline and in Appendix A; their *patterns* are worth knowing even when the repo URLs do not URL-verify. Reddit threads and specific gist comment permalinks could not be fetched (egress restrictions); claims drawn from them are flagged inline as `[unverified]` and listed in Appendix B. v2 added: three-way (research-/rationale-/structure-first) and five-fork typologies; `TheKnowledge` / `TrainingSites` / MindStudio / Mark Chen / NEXUS / "Build Karpathy's Second Brain" walkthrough attributions; `qmd`, Tolkien Gateway, the "100 articles / 400K words" anchor, the "designed to be copy pasted" quote, additional `Pratiyush/llm-wiki` and `maeste/my-2nd-brain` and `rvk7895/llm-knowledge-bases` specifics, the Daniel Yarmoluk CKG benchmark name, and missing direct quotes; corrected `kfchou/wiki-skills` to six skills. All 102 unique URLs were re-checked 2026-07-27. 98 return HTTP 200; Medium, Tolkien Gateway, and two GitHub file URLs answer 403/429 to a plain client but are reachable in a browser. The five Reddit URLs return 200 only as a bot-verification interstitial, so they stay `[unverified]` in Appendix B. Every §12 / §24 multi-refuter citation was confirmed against its arXiv or ACL Anthology title (arXiv 2502.08788 is cited at `v1` deliberately — the paper was retitled in a later version).

> **Consolidation note (2026-07-27).** This edition merges the earlier best-practices file with the supplied *Andrej LLM KB* PDF, two deep-research reports, and the multi-refuter factuality review. Repeated material has been consolidated rather than appended. New material includes purpose and governance files, two-pass ingest and review queues, systematic evaluation, privacy/licensing, portability, token-efficient agent operation, and an evidence-based architecture for using multiple independent refuters. Where the supplied reports disagree about whether a repository was publicly verifiable, this document preserves the more conservative status and separates the reusable pattern from the uncertain attribution; see Appendix C.

## Executive summary

An LLM knowledge base is most reliable when it is treated as a **small information system**, not as a prompt and not as an opaque memory product. The stable centre of the design is:

```text
immutable sources
    -> staged analysis and human scope decisions
    -> cited, typed Markdown pages
    -> review / verification gates
    -> index-first retrieval
    -> selective save-back
    -> deterministic health checks and semantic lint
    -> periodic evaluation and rollback
```

The combined evidence supports the following operating principles:

1. **Preserve a source-of-truth layer.** Originals remain immutable and independently inspectable. Extracted text, embeddings, graphs, and compiled pages are derived artefacts that can be rebuilt.
2. **Write down the purpose before the schema.** A short `PURPOSE.md` defines audience, core questions, exclusions, and what must never be silently promoted. Without it, a technically tidy wiki can still drift away from the user's actual research goals.
3. **Separate source pages from derived knowledge.** One page summarizes each source; concept, entity, decision, and synthesis pages combine evidence across sources. Derived pages must not recursively cite one another as if they were primary evidence.
4. **Use staged ingest.** Parse and analyse first; discuss takeaways, scope, ambiguity, and contradictions; then write. High-impact claims enter a review queue rather than becoming active memory immediately.
5. **Require claim-level provenance.** Every non-obvious claim needs a source path or URL, an exact locator, freshness information, and a review state. Confidence labels are useful only when accompanied by an evidence trail.
6. **Use multiple refuters for accuracy only when they are genuinely independent and complementary.** A strong default is two blind, parallel refuters—one checking evidence/source quality and one checking entailment/scope—followed by a separate evidence-based adjudicator. A third refuter is invoked selectively for disagreement, weak evidence, low confidence, or high-risk claims. Raw agent count is not a reliability guarantee.
7. **Keep retrieval progressive.** Start with `index.md`, typed links, and lexical search. Add line-anchored reads, embeddings, graph traversal, or hybrid retrieval only when a measured failure—paraphrase miss, duplication, or navigation at scale—justifies the added stack.
8. **Measure the system.** Track retrieval quality, claim factuality, citation coverage, stale and orphan pages, refutation precision/recall, false corrections, cost, latency, and regression against a fixed question set.
9. **Automate reversibly.** Hash sources, skip unchanged work, serialize ingest, log every write, limit the number of files touched, and route uncertain or external updates through review. Scheduled writes should be inspectable and easy to roll back.
10. **Keep agent context small.** Persistent instruction files contain only universal rules; procedures live in on-demand skills; indexes are read before pages; pages before raw sources; tools return compact evidence packs rather than entire corpora.

The most defensible default architecture is therefore **Git-backed Markdown plus strong schema and provenance first; human or refuter-assisted review second; evaluation third; retrieval acceleration and interoperability layers only after the basic loop is demonstrably healthy**.

## Contents

- §1–4: thesis, architecture, RAG boundary, Ahrens grounding, and public lineage
- §5–11: folder design, schema, operating cycle, atomic pages, provenance, retrieval, and document handling
- §12: multi-refuter accuracy and factuality architecture
- §13: evaluation and regression testing
- §14: governance, privacy, licensing, security, and portability
- §15: token-efficient operation in coding agents
- §16–18: positive evidence, risk register, and implementation ecosystem
- §19–22: diagnostics, rules, troubleshooting, and copy-paste templates
- §23–24: open questions and bibliography
- Appendices: uncertain repositories, unverified community claims, and source reconciliation


## 1. The thesis

Karpathy's pattern asks an LLM to compile each new source once into a persistent, interlinked Markdown wiki, and then to maintain that wiki — adding entity and concept pages, fixing backlinks, flagging contradictions, updating an index. The pattern fails when treated as "ask the model to do all of that"; it works when the human still does the cognitive work (deciding what matters, paraphrasing, promoting drafts) and the LLM is restricted to the bookkeeping (linking, indexing, formatting, lint). Ahrens called this "external scaffolding to think in" — the slip-box mechanism that makes a Zettelkasten compound. The LLM-wiki pattern automates exactly the bookkeeping operations Ahrens names while the human keeps the cognitive operations. The whole rest of this document is consequences of that one separation.

Karpathy's framing: "the wiki is a persistent, compounding artifact"; "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase"; the gist itself is "designed to be copy pasted" into your own LLM agent — the file is a pattern to instantiate, not a finished product to clone ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f); [Karpathy on X](https://x.com/karpathy/status/2039805659525644595); the [X trending page](https://x.com/i/trending/2042013766036926944) where the term "LLM Knowledge Bases" went viral is a separate primary citation worth keeping for terminology hygiene — the X-side label differs from the gist-side label). The originating X post (2026-04-02, with the gist following two days later on 2026-04-04) framed it as a personal shift in usage: "a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge (stored as markdown and images)" — i.e. using LLMs to build personal knowledge bases for research topics. That framing matters for a survey because it locates the pattern as a *use-mode* observation, not a product launch ([Karpathy on X](https://x.com/karpathy/status/2039805659525644595); post text and timestamp fetched and verified directly 2026-07-27).


## 2. The architecture

Karpathy's original pattern has three explicit layers. Working systems add three control layers around them:

```text
raw/                    immutable original sources and source metadata
wiki/                   compiled Markdown: sources, concepts, entities, syntheses, index, log
schema/contract         CLAUDE.md / AGENTS.md / SCHEMA.md: page and workflow rules
purpose/governance      PURPOSE.md / GOVERNANCE.md: scope, exclusions, roles, review policy
scripts/retrieval       deterministic lint, hashing, search, link audit, exact-context reads
review/evaluation       held changes, refutation records, gold questions, regression reports
```

The first three are Karpathy's. The other three are the operational layer that the more mature implementations and research reports repeatedly add. Projects that ship a `doctor`, `lint`, `health`, `verify`, `status`, `eval`, or `rebuild-backlinks` command read like systems rather than concept demonstrations ([gowtham0992/link](https://github.com/gowtham0992/link); [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki); [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent); [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault); [simonsysun/seeklink](https://github.com/simonsysun/seeklink)). Markdown plus a clever prompt is not enough past a small corpus.

### 2.1 Truth model

The architecture is easier to reason about when every layer has an explicit epistemic status:

| Layer | Status | May be edited by the LLM? | What happens when it is wrong? |
|---|---|---:|---|
| Original source | Source of record | No | Correct, replace, or withdraw the source through an explicit human workflow. |
| Extraction / conversion | Rebuildable representation | Only through a deterministic conversion pipeline | Re-run the parser or OCR and preserve the original. |
| Source page | Cited paraphrase of one source | Draft/update, subject to review | Recompile from the source and inspect the changed claims. |
| Concept/entity/synthesis page | Derived, cross-source knowledge | Draft/update, subject to promotion and verification | Mark stale, supersede, or roll back; never overwrite conflicting evidence silently. |
| Index/graph/search cache | Navigation aid | Yes, preferably deterministically | Rebuild from canonical Markdown. |
| Answer or report | Query-time output | Yes | Verify against cited pages and raw evidence; save back only if reusable and approved. |

The wiki is therefore **authoritative as a maintained synthesis**, but it is not the terminal authority for exact wording or high-stakes facts. The immutable source remains available for traceback.

### 2.2 Purpose and scope are part of the architecture

A schema tells the agent *how* to write. It does not tell the agent *why the knowledge base exists*. Add a short `PURPOSE.md` (or `wiki-purpose.md`) containing:

- intended audience and decisions the wiki should support;
- core questions and research themes;
- included and excluded source types;
- the level of detail expected from source and concept pages;
- what counts as a durable insight worth saving;
- domains that require raw-source verification or human approval;
- acceptable automation and privacy boundaries;
- criteria for archiving, splitting, or retiring the wiki.

Read `PURPOSE.md` at ingest, query, and major maintenance boundaries. Scope drift is not merely an organizational problem: it creates noisy pages, weak retrieval, growing cost, and misleading confidence.

### 2.3 Review and evaluation are separate from generation

Do not ask the same agent call to generate, approve, and score its own write. Generation may propose changes; review decides whether they become active; evaluation measures the system over time. Keeping these roles separate makes the audit trail intelligible and reduces the risk that polished prose is mistaken for verified knowledge.

## 3. Why this is not RAG

Vanilla RAG re-derives each answer from chunks at query time. Karpathy's pattern compiles knowledge once into a structured artefact that compounds across sessions. Two consequences worth taking seriously.

**Token economics flip.** A precompiled wiki plus a small index is cheaper to read each session than re-embedding and re-retrieving over the source corpus. Community reports give two distinct point estimates rather than a smooth range: roughly **65%** non-ingest token reduction in one Reddit thread (heavy workflows moved out of the always-loaded root prompt) and roughly **90%** in another, both unverified ([unverified] r/ClaudeAI and r/ObsidianMD threads, see Appendix B). The most cited single example is a *code-wiki* variant that cut session start from ~47,450 tokens to ~360 by reading a precompiled wiki instead of exploring code from scratch. Treat magnitudes as plausible direction, not exact figure.

**The model maintains the files, not just answers from them.** This is the part naive implementations skip, and where most of them fail ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). If the LLM only answers from the wiki without updating it, the wiki rots; if it updates the wiki without human review, the wiki accumulates plausible-but-wrong "facts." The pattern lives on the seam between those two failure modes.

**The provider-level grounding: context rot and structured note-taking.** The pattern's mechanism is named directly in Anthropic's own context-engineering guidance, which is worth citing for a survey because it grounds the wiki in model architecture rather than in community lore. Two claims do the work. First, **context rot**: because the transformer lets every token attend to every other (n² pairwise relationships), a model has a finite "attention budget," and recall accuracy *degrades* as the context window fills — so stuffing raw sources into context every session is not just expensive, it actively reduces answer quality past some point. Second, **structured note-taking (a.k.a. agentic memory)**: the named technique of having the agent "regularly write notes persisted to memory outside of the context window" that "get pulled back into the context window at later times" — which is precisely what an LLM-maintained wiki *is*. Anthropic pairs this with **just-in-time retrieval** — keeping lightweight identifiers (file paths, stored queries) and loading data on demand rather than pre-loading it — which is the same index→page navigation discipline §10 advocates, and explicitly the model Claude Code uses (`CLAUDE.md` dropped in up front, `glob`/`grep` for the rest). The same source's closing heuristic, "do the simplest thing that works," is the provider-level version of §10's markdown-first escalation order ([Anthropic, *Effective context engineering for AI agents*](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)). The companion piece on long-running agents frames the problem the wiki solves with a useful analogy — sessions are like engineers working in shifts where each new shift arrives with no memory of the last — and notes that compaction alone is insufficient, which is the argument for an external persisted artefact rather than just summarizing the conversation ([Anthropic, *Effective harnesses for long-running agents*](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)). One honest boundary: Anthropic's framing is about a *single agent's* working memory across its own sessions, whereas the LLM-wiki pattern is also a *human's* durable knowledge store — the techniques overlap on persistence but diverge on who the artefact is ultimately for (the §23 tension).

**The strongest case against the pattern** (worth stating in full, because §3 otherwise reads as advocacy). The sharpest published critique argues this is *not* a "bye-bye RAG" moment and that the wiki can be strictly worse than RAG for serious use. The mechanism: in vanilla RAG the model re-reads the immutable source each query, so a one-off misread is just one wrong answer and the *next* query has a fresh chance to get it right; the wiki instead bakes a misread into a page that is then read back, re-cited, and cross-linked — converting *random, self-correcting* errors into *organized, persistent* ones. Worse, those errors are camouflaged: a clean Wikipedia-style page *reads* as trustworthy regardless of whether its claims are grounded. And because building a wiki requires summarizing and compressing, the lossy step strips exactly what serious work depends on — edge cases, exact wording, subtle distinctions — which the raw documents in a RAG corpus still preserve for traceback ([Gupta, "Andrej Karpathy's LLM Wiki is a Bad Idea"](https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-wiki-is-a-bad-idea-8c7e8953c618)). This is not a fringe objection; it is the same compounding-error mechanism the SSGM survey formalizes (§17) and the reason every safeguard in this document — immutable `raw/` for traceback, claim-level provenance, the human promote gate, contradiction sections, lint — exists. The honest reading: the critique is correct about the failure mode and correct that naive implementations realize it; the pattern's defenders are betting that the bookkeeping safeguards plus a disciplined human keep the compounding under the line where the compounding benefit (pre-linked synthesis) outweighs it. Where you can't fund that discipline, or where exact wording is load-bearing (legal, medical, regulatory), RAG-with-traceback is the safer default — which is also the §17 "boundary conditions" conclusion.

## 4. The Ahrens grounding (one paragraph)

Sönke Ahrens's *How to Take Smart Notes* (2017) describes the same architecture with different vocabulary: a reference system (= `raw/`), a slip-box of atomic permanent notes (= `wiki/concepts/` plus `wiki/syntheses/`), an index of entry-points (= `wiki/index.md`), separated from project notes (= `projects/<name>/` outside the wiki) and fleeting notes (= an `inbox/` triaged within 24 hours). Ahrens's key argument: writing is the medium of thinking, not its output; the slip-box externalizes the bookkeeping the brain is bad at so the brain is freed for what only it can do. The LLM-wiki pattern automates exactly the bookkeeping operations Ahrens names — wikilinks, index maintenance, contradiction scanning — while the human keeps the cognitive operations (paraphrasing, promotion, atomic-note discipline). Treating this as the foundation rather than as a complementary framework explains every other decision in this document. The full integration design is in `projects/llm-knowledge-base/outputs/smart-notes-llm-kb-integration.md`; the upstream Ahrens summary is in `references/smart-notes/outputs/smart-notes-summary.md`.

## 4.1 The public lineage: v1 → v2 → v3

The pattern now has a small canonical lineage worth tracking, because later iterations name the failure modes the originals only gestured at, and because the community increasingly cites them by version number. All three are URL-verified primary sources.

**v1 — Karpathy's gist** (`karpathy/442a6bf555914893e9891c11519de94f`, created 2026-04-04). Append-only ingest, manual lint, human-readable notes. The canonical pattern; everything in this document grounds on it.

**v2 — rohitg00's fork** (`rohitg00/2067ab416f7bbe447c1977edaaa681e2`, "LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory", last active 2026-05-25). This is the source the earlier drafts of this document referenced only as an anonymous "LLM Wiki v2 gist comment" — it is in fact a named, dated fork drawn from the author's work on [agentmemory](https://github.com/rohitg00/agentmemory), a persistent-memory engine. v2's substantive additions over v1: a **memory lifecycle** (confidence scoring, supersession, an Ebbinghaus-style retention/forgetting curve, and four consolidation tiers — working → episodic → semantic → procedural); a **typed knowledge graph** layered over the pages (entity extraction, typed edges like `uses`/`depends on`/`contradicts`/`caused`/`supersedes`, graph traversal for queries); **hybrid search** (BM25 + vector + graph fused with reciprocal-rank fusion); **event-driven automation** (hooks on new-source / session-start / session-end / query / memory-write / schedule); quality scoring and self-healing lint; multi-agent mesh sync with shared/private scoping; ingest-time PII filtering and an audit trail; and "crystallization" (distilling a completed work-thread into a first-class wiki page). v2's own framing — *"the schema document is the real product"* — is the sharpest one-line statement of §6's thesis. Note that v2's design is candidly tuned for short agent-observation chunks; the author states book-length ingestion is not yet stress-tested, which is consistent with §11's "long PDFs and books" caveat ([rohitg00 v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2)).

**v3 — Ghelbur's rebuild** (`eugeniughelbur/obsidian-second-brain`, MIT, in production since 2026-03, shipped as a cross-CLI Claude Code / Codex / Gemini / OpenCode skill). v3 adds three things v2 still lacks: **scheduled agents** (nightly close-out, weekly reconciliation + synthesis, periodic health check — the answer to "maintenance only happens when you remember it, so it never happens"); **unsolicited synthesis** (the wiki proactively surfaces unnamed recurring themes and connections you did not ask about); and the **AI-First Vault Principle** (notes written for LLM retrieval rather than human reading). Its two most transferable lessons, independent of the repo: ingest should **rewrite the live page, not only append a backlink** (so the top of every page carries the current best answer, with superseded versions preserved dated below), and automation should be **"everything reversibly, not everything always"** — every scheduled write lands in a daily diff note and waits 24 hours before becoming permanent. The AI-First Vault Principle is in direct tension with this document's promote gate (§7.3); that tension is treated as an open question in §23, not silently resolved ([Ghelbur writeup](https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres); [repo](https://github.com/eugeniughelbur/obsidian-second-brain)).

One dating caveat: the v3 writeup repeatedly dates Karpathy's gist to "2026-02," but the gist page itself, and multiple independent walkthroughs, give **2026-04-04**. This document uses the April date; do not let the v3 source's February claim propagate backward into the lineage.


## 5. Folder layout

A hardened but still Markdown-first layout is:

```text
knowledge-base/
  README.md                   # how to use and recover the system
  PURPOSE.md                  # audience, questions, exclusions, success criteria
  GOVERNANCE.md               # roles, review rules, privacy, deletion, external imports
  CLAUDE.md                   # short universal rules + pointers to skills
  SCHEMA.md                   # page types, frontmatter, citation and link rules

  inbox/                      # fleeting notes; triaged, never silently promoted

  raw/                        # immutable source-of-record files
    articles/
    papers/
    transcripts/
    meetings/
    notes/
    datasets/
    metadata/                 # licences, access conditions, hashes, sensitivity labels

  derived/                    # rebuildable machine representations
    extractions/              # PDF/HTML/audio -> Markdown or text
    thumbnails/
    manifests/

  wiki/                       # canonical compiled Markdown
    index.md                  # navigational entry points, not a giant ontology
    log.md                    # append-only human-readable change log
    overview.md               # optional top-level synthesis
    hot.md                    # concise carry-over context for sporadic sessions
    sources/                  # one paraphrased literature/source note per raw source
    concepts/                 # one reusable idea per page
    entities/                 # people, projects, tools, datasets, organizations
    syntheses/                # cross-source claims and models
    questions/                # saved investigations and their evidence
    decisions/                # reusable decisions and rationale
    methods/                  # optional procedures, protocols, and workflows
    contradictions.md         # unresolved conflicts or pointers to conflict records
    gaps.md                   # missing evidence, missing pages, open investigations

  review/                     # proposed changes that are not yet active knowledge
    ingest/
    refutations/
    contradictions/
    external-imports/
    scheduled-diffs/

  projects/                   # project-specific notes outside the durable slip-box

  eval/                       # reproducible quality measurement
    questions.yaml            # fixed query set and expected evidence
    claims/                   # claim-level gold labels where available
    snapshots/
    reports/

  scripts/                    # deterministic helpers
    hash_sources.py
    lint_links.py
    lint_frontmatter.py
    validate_citations.py
    find_orphans.py
    find_duplicates.py
    find_drafts.py
    find_stale_pages.py
    find_stale_inbox.py
    search_bm25.py
    read_context.py           # PATH:LINE / exact-context retrieval

  reports/                    # health, lint, ingest, refuter, and cost outputs
  skills/                     # on-demand operational procedures
    wiki-triage.md
    wiki-ingest.md
    wiki-promote.md
    wiki-query.md
    wiki-refute.md
    wiki-lint.md
    wiki-eval.md
    wiki-update.md
```

The separation of `wiki/sources/` from `wiki/concepts/`, `wiki/entities/`, and `wiki/syntheses/` is load-bearing. Without it, the model recursively cites earlier summaries and amplifies its own mistakes ([NicholasSpisak/second-brain wiki-schema.md](https://github.com/NicholasSpisak/second-brain/blob/main/skills/second-brain/references/wiki-schema.md)).

The `derived/` layer clarifies a common PDF ambiguity. The untouched PDF, EPUB, webpage capture, audio file, or dataset is the source of record. Extracted Markdown is a rebuildable working representation. The compiled source page is a human- and agent-readable paraphrase. Keeping those statuses distinct makes parser errors and summary errors diagnosable.

Enforce `raw/` immutability at runtime where practical—permissions, pre-commit checks, or a write-blocking tool wrapper—not merely as prose in `CLAUDE.md`.


## 6. Schema and operating contract

The schema has four jobs: define page types, define claim provenance, define lifecycle/review state, and define the agent's permitted operations.

### 6.1 Page frontmatter

A practical superset of the common schemas is:

```yaml
---
id:                         # stable identifier; do not derive identity only from filename
type: source | concept | entity | synthesis | question | decision | method
title:
aliases: []
tags: []

status: draft | active | superseded | archived
review_state: unreviewed | in_review | approved | rejected
confidence: low | medium | high       # categorical; evidence trail matters more than decimals

freshness:
  valid_as_of:
  last_checked:
  next_review:
  volatility: low | medium | high

sources:
  - path:                   # raw file path or stable URL
    locator:                # page, line, paragraph, timestamp, section, or fragment
    source_hash:
    date_accessed:
    licence:
    sensitivity: public | internal | confidential | restricted

provenance:
  created_by: human | llm | imported
  created_with:
  last_verified_by:
  verification_method: human | single_refuter | multi_refuter | deterministic

relations:
  supports: []
  contradicts: []
  supersedes: []
  depends_on: []

last_updated:
---
```

Not every personal wiki needs every field. The minimum reliable set is `type`, `status`, `sources` with exact locators, `last_updated`, and a review/freshness signal. Add privacy, licence, hash, and verification fields when the corpus or consequences justify them.

### 6.2 Claim-level provenance

Page frontmatter is not a substitute for citations inside the page. Every non-obvious factual claim should identify the source and locator that support it. A paragraph that synthesizes several sources should make the mapping visible rather than placing a bibliography at the bottom and leaving the reader to guess.

For claims likely to change, record both the source publication date and the date the claim was last verified. For inferred relationships, distinguish `EXTRACTED`, `INFERRED`, `AMBIGUOUS`, and `UNVERIFIED` rather than presenting all links as equally certain.

### 6.3 Operating rules

At minimum, the contract should state:

- never modify `raw/` through ordinary agent operations;
- read `PURPOSE.md`, the index, and relevant context before writing;
- prefer updating a canonical page over creating a near-duplicate;
- keep source pages separate from derived pages;
- cite every substantive claim to a raw source or source page with a raw locator;
- preserve contradictions until resolved; do not average them into false consensus;
- keep low-confidence, externally imported, high-risk, or refuter-disputed writes in `review/`;
- update `index.md`, `log.md`, and affected backlinks after every accepted write;
- use surgical edits and a file-touch budget rather than broad rewrites;
- run structural health checks after writes and semantic lint at a defined cadence;
- never treat an LLM critique, majority vote, or confidence score as evidence by itself.

Reference implementations that encode parts of this contract include [NicholasSpisak/second-brain](https://github.com/NicholasSpisak/second-brain/blob/main/skills/second-brain/references/wiki-schema.md), [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki/blob/master/AGENTS.md), and [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent/blob/main/AGENTS.md).

### 6.4 Split schema from operations

Keep `CLAUDE.md` or the equivalent root instruction file short—global truths, directory layout, safety rules, and pointers to skills. Move ingest, query, refutation, lint, and evaluation procedures into separate, clearly named skill files. A reported refactor reduced a root file from roughly 300 lines to 104 and saved about 1,960 tokens per session ([unverified] r/ObsidianMD; see Appendix B). The counter-risk is over-splitting: overlapping micro-skills cause routing errors. The useful middle is a small universal contract plus a few procedures whose trigger and non-trigger conditions are explicit.

## 7. The operating cycle

The whole system is one loop: capture → ingest → maintain → query → save back. Each stage has a hard rule about what the LLM may and may not do.

For a survey framing, this loop maps onto the **write–manage–read** formalism that the 2026 agent-memory literature uses to decompose any external-memory system: *write* (capture + ingest, here gated by human triage), *manage* (maintain — lint, contradiction handling, supersession, the part most blog implementations underbuild), and *read* (query). Recent surveys formalize agent memory precisely as a write–manage–read loop coupled to perception and action, and treat the *manage* stage as the under-explored one — which matches this document's emphasis on lint and the promote gate as the load-bearing, most-skipped operations ([Du, *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers*, arXiv 2603.07670](https://arxiv.org/abs/2603.07670); see also [Luo et al., *From Storage to Experience*, arXiv 2605.06716](https://arxiv.org/abs/2605.06716), which frames the same evolution as storage → reflection → experience). The Karpathy pattern is a *human-curated, markdown-substrate* instance of this general loop; the academic systems differ mainly in automating the *manage* stage and in substrate (databases, vector stores, learned controllers) rather than in the loop's shape.

### 7.1 Capture and triage

Fleeting notes go to `inbox/`, not `raw/` or `wiki/`. Within ~24 hours the human triages each item: trash, promote to a literature note (if it cites a source), or convert to a concept-page draft. The LLM may *propose* triage but never commits it; this is the cognitive operation Ahrens insists on. If the LLM is allowed to auto-promote, the wiki accumulates LLM voice and the slip-box's compounding stops working — exactly the failure mode warned about in the Hacker News critique that "auto-generated notes can look good until someone actually reads them."


### 7.2 Ingest

Use a two-pass ingest: **analysis first, generation second**. The agent must orient itself and surface uncertainty before it writes durable pages.

```text
0. Read PURPOSE.md, GOVERNANCE.md, CLAUDE.md / SCHEMA.md, index.md, log.md, and hot.md.
1. Register the source: preserve the original, calculate a hash, record licence/access/sensitivity, and check duplicates.
2. Parse or extract into a rebuildable working representation; flag OCR/layout loss rather than hiding it.
3. Analysis pass: read the full source and produce candidate takeaways (3–8 bullets — sources disagree: kfchou wiki-ingest specifies 3–5, Karpathy-help diagnosis specifies 5–8; pick a number for your skill file rather than leaving it to the model), atomic claims, entities, methods, contradictions, gaps, and uncertain interpretations.
4. Pause for scope decisions: ask what matters, what is out of scope, and which claims deserve durable pages.
5. Generation pass: write or update one source page — paraphrased, in the user's voice — then draft only the relevant concept/entity/synthesis/method pages.
6. Add exact citations to raw locators and label inference separately from extraction.
7. Run verification appropriate to risk: deterministic validators for paths/links/hashes; one or two independent refuters for high-impact or synthesized claims (§12).
8. Route disagreements, low-confidence claims, external imports, and material contradictions to review/ rather than activating them.
9. Scan for canonical pages, duplicates, backlinks, typed relationships, and downstream pages made stale.
10. Update index.md and log.md; run health checks; report files touched, claims added, claims disputed, and unresolved work.
```

The "candidate takeaways before writing" step protects the wiki from becoming a plausible but mis-prioritized summary of what the user actually cares about. The kfchou skill pack encodes a related protocol in [`wiki-ingest/SKILL.md`](https://github.com/kfchou/wiki-skills); Astro-Han packages the pattern in a single skill ([Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)).

Three ingest invariants recur across the stronger implementations:

- **Start with a controlled corpus.** A useful initial batch is roughly 10–20 related sources, with one-source-at-a-time review while the schema is still changing. A tutorial reporting 180+ video ingests nevertheless recommends beginning with ten ([unverified] TrainingSites tutorial).
- **Serialize, cache, and recover.** Hash sources, skip unchanged files, process a serial queue, retry transient failures, checkpoint after each file, and guarantee that a source page exists even when downstream synthesis fails ([nashsu/llm_wiki](https://github.com/nashsu/llm_wiki)).
- **Save useful answers selectively.** A substantial, well-supported investigation can become a `wiki/questions/<topic>.md`, `wiki/decisions/<topic>.md`, or `wiki/syntheses/<topic>.md` page that future queries reuse ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)). Routine answers and speculative brainstorming should not automatically expand the permanent store. One implementer described their six-month variant: it reads session transcripts after coding sessions, extracts decisions and rejected approaches, then requires human review before anything is promoted into persistent context — the human directs exploration while the LLM does the bookkeeping ([unverified] HN comment on Karpathy gist).

A source summary should normally be easier to regenerate than a concept page. Consequently, human or multi-refuter review effort should concentrate on cross-source synthesis, decisions, high-volatility facts, and claims whose wording is stronger than any single source.

### 7.3 Promote (the review gate)

LLM-drafted concept pages stay at `status: draft` until the human re-voices them and promotes to `status: active`. Pages whose promotion rule is evidence-based rather than voice-based may instead pass the structured review and refuter gate in §12, but high-impact synthesis should still receive human approval unless `GOVERNANCE.md` explicitly permits otherwise. Draft pages are excluded from query results unless explicitly requested. This is the second human-in-the-loop commit point (after triage). It is the place where Ahrens's paraphrasing discipline enters the LLM workflow; without it, the wiki accumulates LLM-voice text that fails the AI-writing-tells filter and accumulates the "ingest errors compound" failure mode named below.


### 7.4 Query

The best query prompts are aggressively grounded and progressively disclosed:

```text
query: <question>
- read PURPOSE.md, hot.md, index.md, and relevant folder _context.md files first
- identify the likely page types and retrieve a small candidate set
- answer from active wiki pages first
- inspect cited source passages when the claim is uncertain, volatile, high-stakes, or disputed
- do not answer from model memory when the knowledge base is intended to be authoritative
- cite the exact wiki pages and source locators used
- exclude draft, rejected, and unresolved-review pages by default
- state missing evidence, contradictions, and the date scope of the answer
- for high-impact answers, run the refutation/adjudication gate in §12
- save back only a reusable, adequately supported synthesis or decision
```

This differs from generic "ask my notes" prompting in four ways: it forbids uncited model-memory substitution, retrieves progressively rather than preloading the corpus, makes uncertainty and time scope explicit, and closes the loop by saving only high-value results.

Named query templates — pre-built, reusable prompts that extract a specific *kind* of insight rather than answering a one-off question — are useful once page and edge types are stable. Examples include "show every active claim that contradicts hypothesis X", "trace the evidence chain for decision D", "list claims whose supporting source has been superseded", and "find high-confidence pages that have not been verified within their freshness window". Templates should query structured relationships where possible rather than rely on prose reminders: they pay off most once the typed-link layer (§8) exists, because the useful ones query relationship types directly, and without typed edges they collapse back into generic keyword search ([Level Up Coding walkthrough](https://levelup.gitconnected.com/beyond-rag-how-andrej-karpathys-llm-wiki-pattern-builds-knowledge-that-actually-compounds-31a08528665e)).

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


Add governance and verification checks as the corpus matures:

- source hashes or extracted representations that no longer match the registered original;
- claims whose exact locator cannot be opened;
- volatile claims past `next_review`;
- pages with incompatible privacy or licence metadata;
- active pages that still have `review_state: unreviewed`;
- unresolved refuter disagreements or adjudications with missing evidence;
- corrections that changed a previously correct claim (false-correction candidates);
- scheduled or automated writes that have not passed their hold period;
- external bundles whose provenance, schema version, or signatures cannot be trusted;
- regression questions whose expected evidence or answer class changed.

A useful "sanity loop" is **demo/test → ingest → inspect → health → lint/refute → repair or review → query → evaluate**. The point is not the specific command names; it is that the system exposes intermediate state rather than hiding every failure inside one agent turn.

## 8. Page typology and atomicity

Six frontmatter `type` values, each with a clear role — plus the optional `method` type in §6.1:

- *source* — paraphrased summary of one raw document. One file per source. Confidence high (sources are immutable). Tied to a `raw/` locator.
- *concept* — one atomic idea, self-explanatory, reusable across topics. **One idea per file** — non-negotiable.
- *entity* — a person, project, tool, dataset, organization.
- *synthesis* — cross-source claim that doesn't reduce to a single concept or entity.
- *question* — a saved investigation: answer plus the wiki pages cited.
- *decision* — a reusable choice and its rationale.

The atomicity rule is the part the LLM will resist on its own. Left alone, an LLM drifts toward writing topic pages that try to be comprehensive. Atomicity has to be enforced in the schema: one idea per file, one main claim per file, every page must answer "from what other contexts would I want to stumble upon this?" That second question generates the wikilinks. The first question — "where does this go?" — generates the failure mode Ahrens spent ch. 6 of *How to Take Smart Notes* warning against (Ahrens 2017, ch. 6).

**Page size limits** make atomicity enforceable: roughly **400-line soft cap, 800-line hard cap** ([unverified] r/AI_Agents). Beyond that, edits become whole-file rewrites and the model loses the thread. Once the wiki gets large, sharded indexes plus line-anchored retrieval are needed. The `PATH:LINE` retrieval pattern (with a context window, e.g. `-C 20`) is documented in [simonsysun/seeklink](https://github.com/simonsysun/seeklink). The "LLM Wiki v2" fork recommends BM25 + vector search + graph traversal + reciprocal-rank fusion for larger systems, but only after the basics are working ([rohitg00 v2 gist](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2); see §4.1).

**Typed links: the most-named missing piece in the base pattern.** A plain `[[wikilink]]` records *that* two pages connect but not *how* — the relationship's meaning lives in the surrounding prose, invisible to any tool. Penfield Labs makes the sharpest version of this critique: Karpathy describes the LLM "noting where new data contradicts old claims" and "flagging contradictions," but the link format itself cannot express `supports` versus `contradicts` versus `supersedes`, so the most valuable structural information stays trapped in unstructured text — defeating the point of compiling a wiki in the first place ([Penfield "what's missing" article](https://dev.to/penfieldlabs/what-karpathys-llm-wiki-is-missing-and-how-to-fix-it-1988)). The concrete fix is a typed-relationship vocabulary. Their [PENgram](https://github.com/penfieldlabs/pengram) pipeline classifies every edge into one of **24 semantic types**, grouped: knowledge-evolution (`supersedes`, `updates`, `evolution_of`), evidence (`supports`, `contradicts`, `disputes`), hierarchy (`parent_of`, `child_of`, `sibling_of`, `composed_of`, `part_of`), causation (`causes`, `influenced_by`, `prerequisite_for`), implementation (`implements`, `documents`, `tests`, `example_of`), conversation (`responds_to`, `references`, `inspired_by`), sequence (`follows`, `precedes`), and dependencies (`depends_on`) — plus **8 code-structure types** for codebase corpora (`calls`, `imports`, `uses`, `extends`, `implements_interface`, `instantiates`, `overrides`, `decorates`). Two design choices are worth lifting independent of the tooling. First, **every edge carries a confidence label** — `EXTRACTED` (stated in the source), `INFERRED` (deduced from context), or `AMBIGUOUS` — on the principle that a graph where every edge claims equal confidence is lying to you; this is the edge-level analogue of the claim-level provenance in §9. Second, the Obsidian implementation ([penfieldlabs/obsidian-wikilink-types](https://github.com/penfieldlabs/obsidian-wikilink-types)) keeps the types human-writable as inline `@supersedes` / `@contradicts` syntax that auto-syncs to YAML frontmatter, so the same edge is both Dataview-queryable ("show everything that contradicts my current hypothesis") and LLM-readable. The honest caveat, also from Penfield: typing every link by hand is tedious and misses non-obvious connections, so the relationship discovery is itself delegated to the LLM (their "Vault Linker" skill) — which re-imports the §17 trust problem one level up, since an LLM-inferred `contradicts` edge can be as wrong as any other LLM claim. Treat AI-discovered edges as `INFERRED` and gate them the same way as draft pages. This typed-link layer is the concrete schema behind the vaguer "typed knowledge graph" the v2 fork gestures at (§4.1).

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

Markdown plus a flat `index.md` is enough for a Karpathy-scale corpus — Karpathy's own example anchor is roughly **100 articles / 400K words** ([Karpathy on X](https://x.com/karpathy/status/2039805659525644595); the anchor is in the X post, not the gist, which puts the same scale as "~100 sources, ~hundreds of pages") — provided lint runs consistently. It breaks past that. The escalation order, in increasing cost:

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


## 12. Accuracy and factuality: a multi-refuter verification layer

A compiled wiki can compound correct knowledge, but it can also compound a single bad interpretation. Multiple refuters are one way to improve the accuracy gate—provided they are designed to add **independent evidence and complementary checks**, not merely more voices.

### 12.1 Terminology and role

A **refuter** is an agent assigned to challenge a specific claim and determine whether a valid evidence-based objection exists. Related literature uses *critic*, *verifier*, *debater*, *judge*, *fact-checking agent*, *error detector*, and *self-refinement agent*. These are not interchangeable:

- a critic may provide open-ended feedback;
- a verifier may return a correctness label;
- a debater interacts with another agent;
- a fact checker retrieves external evidence;
- an adjudicator decides which objections justify a change.

For an LLM knowledge base, the refuter should have a narrow contract: **assess an atomic claim against identified evidence and return a structured verdict**. It should not silently rewrite the page, and it should be allowed to report `no valid refutation found`.

### 12.2 What the literature supports

The literature does not support the rule "more agents are always better". It supports a narrower proposition: multiple **diverse, independent, competent, evidence-grounded** verifiers can catch errors that one verifier misses.

#### Direct positive evidence

*N-Critics* directly evaluated multiple critics for factual hallucination correction. Its TriviaQA ablation reported:

| Critics | TriviaQA F1 |
|---:|---:|
| 0 | 79.4 |
| 1 | 81.5 |
| 2 | 84.7 |

The two-critic condition also improved the generator on TriviaQA, AmbigNQ, and HotpotQA. Important limits: the ablation stopped at two critics, used one main generator, evaluated 400 sampled questions per dataset, and found that weaker 13B critics sometimes failed to help. The result supports a second competent critic, not indefinite scaling ([N-Critics](https://arxiv.org/pdf/2310.18679)).

The original multi-agent debate study reported improvements from one to three agents on biography factuality (66.0% to 73.8%), MMLU (63.9% to 71.1%), and chess-move validity (29.3% to 45.2%). Its monotonic agent-count ablation was on arithmetic rather than factuality, so it does not establish that factuality keeps improving with every added refuter ([Multiagent Debate](https://arxiv.org/pdf/2305.14325)).

A systematic 2025 study found that **independent initial answers and diversity** contributed substantially, while additional discussion rounds could reduce performance. This supports parallel, blind first-pass verification rather than long conversational debate ([Findings of ACL 2025 study](https://aclanthology.org/2025.findings-acl.606.pdf)).

Selective-deliberation work such as SELENE suggests that extra agents should be triggered mainly by disagreement, miscalibration, or risk; the reported experiments reduced token use by roughly half while improving one or more of accuracy, calibration, or judgement stability on the evaluated tasks ([SELENE](https://aclanthology.org/2026.eacl-industry.7.pdf)).

#### Negative and mixed evidence

Several studies find that multi-agent discussion does not reliably outperform a well-prompted single agent or self-consistency:

| Evidence | Relevant finding | Design lesson |
|---|---|---|
| Wang et al., ACL 2024 | A strongly prompted single agent was close to the best multi-agent method on several reasoning tasks. | Compare against a strong single-agent baseline, not a weak prompt. |
| Smit et al., ICML 2024 | Debate did not reliably beat self-consistency or reasoning-path ensembles; results were protocol-sensitive. | Agent count cannot compensate for a poor interaction protocol. |
| Zhang et al., 2025 | Five debate methods across nine benchmarks and four foundation models did not reliably outperform single-agent CoT/self-consistency despite more compute. | Report total inference budget and simple baselines. |
| Chen et al., 2026 | Conventional competitive and consensus-seeking two-agent debate often underperformed individual agents on direct error detection/fact verification; a designed collaborative protocol reversed the result. | Complementary information and adjudication matter more than "debate". |
| Multi-Agent Verification | Diverse verifier ensembles sometimes helped, sometimes dipped, and showed diminishing returns; a repeated strong verifier was occasionally better. | Measure diversity and marginal value rather than assuming it. |

Relevant sources: [Wang et al.](https://arxiv.org/abs/2402.18272), [Smit et al.](https://proceedings.mlr.press/v235/smit24a.html), [Zhang et al.](https://arxiv.org/html/2502.08788v1), [Chen et al.](https://arxiv.org/html/2510.20963v2), and [Multi-Agent Verification](https://arxiv.org/html/2502.20379v1).

The defensible conclusion is:

> Multiple refuters can improve factuality when they contribute independent evidence or complementary error detection. Multiplying correlated instances, forcing objections, or using a weak judge can equal or underperform one strong verifier.

### 12.3 Why several refuters can help—and why they can hurt

If each refuter independently catches a real error with probability \(p\), the probability that at least one of \(n\) refuters catches it is:

\[
P(\text{caught}) = 1-(1-p)^n
\]

For \(p=0.60\), coverage rises from 60% with one refuter to 84% with two and 93.6% with three. This is the potential **recall advantage**.

The same calculation applies to invalid objections. If each refuter has a 10% chance of inventing a criticism, the chance of at least one false objection is 10% with one, 19% with two, and 27.1% with three. More refuters can therefore improve error-detection recall while reducing refutation precision. That is why objections require adjudication rather than automatic acceptance.

In practice, independence is rarely complete. Refuters may share the same model, prompt, retrieved evidence, training-data misconception, source-quality failure, or tendency to defer to confident language. Three correlated agents can be less useful than two genuinely different ones.

### 12.4 Failure modes to design against

**Correlated errors.** Repeated calls to the same model and retrieval path may reproduce the same blind spot. Vary role, evidence path, model family, or source subset when the benefit justifies the cost.

**Incorrect majorities.** When the wrong answer is already more probable, additional samples can strengthen the wrong majority. Majority vote is not a substitute for evidence.

**Social convergence.** Open debate lets one persuasive but unsupported objection contaminate the others. Preserve blind initial judgements and reveal peer outputs only after each refuter has committed its evidence.

**Forced contrarianism.** A prompt that says "find an error" creates fabricated criticism when the claim is correct. Permit `supported` and `no valid refutation found`.

**Shared evidence failure.** Two agents that both receive the same weak snippet are not independent. Log retrieval queries and the evidence each refuter actually inspected.

**Uncritical revision.** A valid critique may contain an invalid correction. The revision stage must assess the evidence and then run a post-revision check.

**Judge bias.** The adjudicator may favour verbosity, confidence, its own model family, or apparent consensus. Require claim/evidence alignment and concise structured inputs.

**Context overload.** Long debate transcripts bury the strongest evidence. Give the adjudicator normalized records, not an unbounded conversation.

### 12.5 Recommended reference architecture

A literature-aligned default uses **two blind, parallel, specialized refuters**, then a separate adjudicator, with selective escalation.

#### Stage 1: decompose into atomic claims

Refute the smallest independently checkable proposition. Each claim receives a stable `claim_id` and retains its dependencies. Atomic claims make it possible to identify the exact disputed wording, relevant evidence, error type, and downstream pages affected by a correction.

#### Stage 2: run two refuters independently

The first-pass refuters do not see each other's conclusions. They may share the claim, source registry, and resource budget, but their retrieval queries and analyses are logged separately.

#### Stage 3: assign complementary roles

A strong pair is:

1. **Evidence and source refuter**
   - finds supporting and contradicting evidence;
   - checks source identity, quality, recency, licence/access status, and whether the locator exists;
   - detects missing, conflicting, or circular evidence;
   - distinguishes direct evidence from secondary restatement.

2. **Entailment and scope refuter**
   - checks whether the cited evidence supports the *exact wording*;
   - identifies overstatement, scope shift, causal inflation, missing qualification, temporal mismatch, or uncertainty presented as fact;
   - tests whether a synthesis combines incompatible source claims.

Optional roles are invoked only when relevant:

- **temporal refuter** for current or version-sensitive facts;
- **numerical refuter** for calculations, units, denominators, and table consistency;
- **domain refuter** for technical standards, medicine, law, finance, or specialized science;
- **contradiction refuter** for conflicts across pages or source versions;
- **provenance refuter** for fabricated, inaccessible, or recursively derived citations;
- **privacy/licensing refuter** for restricted or rights-sensitive material.

#### Stage 4: require a structured refutation record

Every refuter returns:

```yaml
claim_id:
claim_text:
verdict: supported | contradicted | insufficient_evidence | unverifiable
error_types: []                 # factual, temporal, numerical, entailment, scope, source, contradiction
sources_checked:
  - source:
    locator:
    stance: supports | contradicts | contextualizes
reasoning_summary:              # concise explanation of claim-evidence relation
confidence: low | medium | high
proposed_correction: null
no_valid_refutation_found: false
retrieval_log:
  queries: []
  unavailable_sources: []
```

Confidence is not evidence. An objection without an inspectable source or a precise logical issue remains an unsupported objection.

#### Stage 5: use a neutral evidence-based adjudicator

The adjudicator receives the original claim, the relevant source passages, and normalized refuter records. It must not count objections as votes, favour the more verbose response, assume consensus is correct, or rewrite every challenged claim.

Its possible decisions are:

```text
ACCEPT_ORIGINAL       evidence supports the claim as written
REVISE                evidence supports a specific narrower/corrected claim
REMOVE                no defensible version is supported or the claim is irrelevant
HOLD_FOR_REVIEW       evidence conflicts, source is unavailable, or risk exceeds automation policy
ESCALATE               another specialist/refuter or human judgement is required
```

The default is to preserve the original claim unless evidence justifies a change. When revising, the adjudicator should identify dependent claims and pages that become stale.

#### Stage 6: escalate adaptively

Invoke a third refuter or human reviewer when:

- the first two verdicts disagree;
- supporting and contradicting evidence are both credible;
- confidence is low or calibration is poor;
- the claim is high-risk or highly volatile;
- a source is inaccessible, weak, or secondary-only;
- the proposed correction materially changes a conclusion or decision;
- the adjudicator cannot distinguish an evidence conflict from an entailment error.

This is usually more efficient than running three or more agents on every claim.

#### Stage 7: verify the revision

After a correction is drafted, re-run a concise check against the accepted evidence. This catches overcorrection, removed qualifications, merged incompatible suggestions, and new errors introduced during revision.

#### Stage 8: store the audit trail

Save the claim, evidence pack, refuter outputs, adjudication, revision diff, model/tool versions, cost, and final status under `review/refutations/` or as a structured report. The audit record is not ordinary wiki content; it is the evidence for why the active page changed.

### 12.6 Where the refuter layer belongs in the knowledge-base lifecycle

| Lifecycle point | What to verify | Default policy |
|---|---|---|
| Source ingest | source identity, extracted claims, exact locators, parser loss | Deterministic checks for every source; refuters for high-impact claims or ambiguous extraction. |
| Concept/synthesis draft | cross-source entailment, contradiction, scope, causal wording | Two-refuter gate before promotion when the page will become reusable active knowledge. |
| External import | provenance, schema compatibility, stale or malicious instructions | Treat as untrusted; hold in review and verify before merging. |
| Query answer | atomic factual claims, current facts, conclusions that affect decisions | Verify selectively based on risk, disagreement, novelty, and source freshness. |
| Maintenance | stale claims, contradictory pages, superseded evidence | Scheduled contradiction/temporal refuters plus deterministic freshness checks. |
| Major revision | whether the correction itself is supported and whether dependants changed | Post-revision refuter and downstream-staleness sweep. |

Do not run an expensive multi-refuter gate on formatting edits, generated indexes, or deterministic link repairs. Use it where semantic correctness, synthesis, or consequences justify the cost.

### 12.7 Acceptance policy

A simple policy is:

- **Auto-accept** a claim only when both refuters return `supported`, all cited locators resolve, the source is permitted, and no freshness rule is violated.
- **Auto-reject or revise** only when a contradiction is direct, the evidence is inspectable, and the correction is narrowly entailed.
- **Hold for review** when verdicts disagree, evidence conflicts, a source cannot be inspected, the claim is high-risk, or the revision changes the page's main conclusion.
- **Abstain** when evidence is insufficient. The system should record a gap rather than manufacture certainty.

Majority vote is intentionally absent. Evidence quality, entailment, and policy determine the outcome.

### 12.8 Cost and independence controls

Track the marginal value of each refuter. Useful controls include:

- equal token and retrieval budgets for comparative experiments;
- independent retrieval before agents see peer outputs;
- different role prompts before different model families;
- a cap on sources and passages returned to the adjudicator;
- selective escalation based on disagreement, risk, novelty, or uncertainty;
- caching the evidence pack so repeated agents do not re-download the corpus;
- a matched-budget single-refuter baseline that may use more search or reasoning;
- performance per token, retrieval call, dollar, and second—not accuracy alone.

The recommended operational starting point is **two specialized refuters plus a neutral adjudicator**, not a large debating swarm. Add a third only when the measured error classes and escalation triggers justify it.

## 13. Evaluation and regression testing

A wiki that "feels useful" can still be drifting. Evaluation should separate **structural integrity**, **retrieval**, **answer factuality**, **refutation quality**, **revision quality**, and **efficiency**.

### 13.1 Build a fixed evaluation set

Maintain a versioned set of questions and claim checks representing the work the knowledge base must support:

```yaml
- id: q-001
  question: What evidence supports the current study design decision?
  type: multi_source_synthesis
  expected_pages: [decision-study-design, source-a, source-b]
  required_source_locators: []
  answer_constraints:
    must_include: []
    must_not_claim: []
  volatility: low
  risk: medium

- id: q-002
  question: Which active claims are contradicted by the newest source?
  type: contradiction_detection
  expected_relationships: [contradicts, supersedes]
  risk: high
```

Include easy navigation questions, paraphrase retrieval, multi-hop synthesis, temporal updates, contradiction resolution, abstention, and adversarial cases where the correct answer is "the wiki does not contain enough evidence". Preserve frozen snapshots so a new schema or retrieval layer can be compared against the same corpus.

### 13.2 Structural and knowledge-health metrics

Track at least:

- broken links and missing cited paths;
- citation coverage and locator resolution rate;
- raw sources without source pages and source pages without raw references;
- orphan, duplicate, oversized, stale, and overdue-draft pages;
- active claims past their freshness window;
- contradiction backlog and mean time to resolution;
- percentage of writes that touched index/log/backlinks correctly;
- review queue age and approval/rejection rates;
- external imports lacking provenance or schema compatibility;
- rollback success and reproducibility of rebuildable caches.

These are inexpensive and often reveal more than an LLM judge.

### 13.3 Retrieval metrics

Evaluate retrieval separately from generation. Depending on the task, use:

- Recall@k and Precision@k for expected pages/passages;
- MRR, MAP, or NDCG for ranked results;
- source-locator recall;
- answerable-versus-unanswerable discrimination;
- duplicate entity retrieval and canonical-page selection;
- graph path accuracy for typed relationships;
- pages and raw-source passages opened per completed query.

Compare the simplest baseline—index plus lexical search—against line-anchored, vector, graph, and hybrid retrieval under the same corpus and query set. Azure AI Search and Qdrant describe hybrid lexical/vector fusion, often through Reciprocal Rank Fusion; `qmd` is a local Markdown-oriented example ([Azure hybrid search](https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview), [Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/), [tobi/qmd](https://github.com/tobi/qmd)).

### 13.4 Final-answer factuality

Score answers at the claim level:

- factual precision, recall, and F1;
- unsupported-claim rate;
- contradiction rate;
- correct abstention rate;
- citation precision and citation completeness;
- temporal accuracy and appropriate `valid_as_of` qualification;
- entailment: whether each citation supports the exact wording;
- preservation of source disagreement and uncertainty.

Human adjudication remains the strongest reference for a small, important set. LLM-as-judge can expand coverage, but should be calibrated against human labels and should never replace deterministic citation checks.

### 13.5 Refutation and revision metrics

For the §12 layer, record:

- refutation precision and recall;
- valid errors uniquely detected by each refuter;
- invalid objections and forced-refutation rate;
- inter-refuter agreement and error correlation;
- evidence quality and source diversity;
- confidence calibration;
- proportion of original errors corrected or missed;
- **false-correction rate**—correct claims changed into incorrect ones;
- new errors introduced by revision;
- valid corrections rejected by the adjudicator;
- escalations that changed the final decision;
- marginal gain from the second and third refuter.

A high error-detection recall with a high false-correction rate is not an accurate system.

### 13.6 Efficiency and operational metrics

Track:

- input/output tokens by stage;
- retrieval calls and sources fetched;
- latency and monetary cost;
- files and lines read or rewritten;
- cache hit rate and unchanged files skipped;
- performance per unit of compute and retrieval;
- human review minutes per accepted page;
- queue wait time and failure/retry rate;
- storage growth and maintenance-to-useful-work ratio.

The last measure detects the "maintenance ratchet": a system that increasingly maintains itself instead of supporting research.

### 13.7 Matched-budget experimental design for refuters

A defensible experiment compares:

1. no refuter;
2. one refuter;
3. two refuters;
4. three refuters;
5. one refuter with the same total token, retrieval, and revision budget as the multi-refuter condition.

Within the two-refuter condition, vary:

- identical model/prompt repeats versus specialized prompts;
- same versus different model families;
- shared versus independent retrieval;
- parallel blind critique versus interactive debate;
- majority vote versus evidence-based adjudication;
- fixed two-refuter use versus adaptive escalation.

Hold constant the generator, evidence corpus, context length, total retrieval calls, total token budget, allowed revisions, adjudication policy, benchmark difficulty, model versions, latency accounting, and price basis.

### 13.8 Statistical claims

Distinguish:

- **superiority:** multiple refuters perform better;
- **non-inferiority:** they are not meaningfully worse;
- **equivalence:** the difference falls inside a pre-specified practically negligible interval.

A non-significant superiority test does not demonstrate equivalence. Pre-register the practical margin, analyse paired claim/question outcomes, report confidence intervals and effect sizes, and test interactions with error type, claim difficulty, evidence diversity, model diversity, and retrieval success.

### 13.9 Regression cadence

A practical cadence is:

- structural health after every write or session;
- semantic lint after a defined ingest volume (for example, 10–15 sources) or weekly;
- a small smoke-test question set after schema, prompt, or model changes;
- a full retrieval/factuality suite before a release or major migration;
- periodic human re-annotation of a sample to detect judge drift;
- cost and latency trend review monthly;
- an explicit rollback trigger when citation coverage, false corrections, or core-question performance degrades beyond tolerance.

Store the evaluation configuration, corpus snapshot, model/tool versions, prompts, and raw outputs so results are reproducible rather than anecdotal.

## 14. Governance, privacy, licensing, security, and portability

The original pattern is mostly silent on governance. Once the wiki contains private documents, team knowledge, or material that affects decisions, governance becomes part of correctness.

### 14.1 Roles and approval boundaries

Define at least:

- **source curator:** decides what enters `raw/` and records access/licence metadata;
- **maintainer agent:** proposes structured updates and performs deterministic bookkeeping;
- **reviewer:** approves, rejects, or narrows semantic changes;
- **administrator:** controls providers, permissions, exports, deletion, and backups;
- **evaluator:** maintains gold questions and reviews regressions;
- **adjudicator:** resolves evidence-based disputes without being the original generator.

One person may fill several roles in a personal vault, but the operations should remain conceptually distinct. High-risk domains should require human approval for active claims and external outputs.

### 14.2 Review queues and reversibility

Route low-confidence writes, contradictions, external bundles, inferred rationale, privacy-sensitive transformations, and refuter disagreements into `review/`. Each record should show the proposed diff, source evidence, agent/model, timestamp, reason for hold, and available actions.

Prefer "everything reversibly" to "everything always". Scheduled automation can write daily diff notes that remain provisional for a hold period before promotion. Use Git or equivalent versioning so any page, index, or schema migration can be inspected and rolled back.

### 14.3 Privacy and data minimization

Record sensitivity at source and, where needed, claim level. Send only the minimum evidence required to an external provider. Local models or local retrieval may be preferable for confidential corpora, but local execution does not remove the need for access controls, logs, backups, and secure deletion.

Practical rules:

- separate public, internal, confidential, and restricted sources;
- exclude secrets, credentials, and unnecessary personal data at ingest;
- redact or pseudonymize before external model calls when appropriate;
- keep provider and retention choices explicit in `GOVERNANCE.md`;
- prevent generated public views from following links into restricted pages;
- test deletion through all derived pages, indexes, embeddings, caches, exports, and backups;
- treat session transcripts as sensitive sources, not harmless logs.

Adjacent guidance includes data-minimization principles from the [ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/) and [GDPR Article 5](https://www.legislation.gov.uk/eur/2016/679/article/5). Apply the law and policy relevant to the actual jurisdiction and data.

### 14.4 Copyright, licence, and attribution

The right to read a source does not necessarily imply the right to redistribute its full text. Preserve source title, author, URL/path, licence, access date, and usage restrictions. Paraphrase rather than reproduce long copyrighted passages unless permission or an applicable exception supports the use. For Creative Commons material, record the licence and follow attribution guidance such as title, author, source, and licence ([Creative Commons](https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution)). Canadian users should also consult the [Canadian Intellectual Property Office copyright overview](https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en/copyright).

Add a takedown/deletion workflow and avoid assuming that an exported wiki may include every underlying source. The compiled page can cite a restricted source without embedding the entire source text.

### 14.5 Memory poisoning and untrusted imports

A persistent knowledge base creates a temporal security risk: malicious or simply wrong content can be written now and activated in a later, unrelated query. Treat external compiled wikis, agent memories, session histories, web captures, and shared bundles as untrusted inputs.

Controls include:

- quarantine before merge;
- source allow/deny policies and content hashes;
- stripping embedded instructions from source content;
- schema validation and provenance requirements;
- least-privilege tools for ingest and query agents;
- review of high-impact relationships such as `supersedes`, `contradicts`, or `approved_policy`;
- audit logs that connect a future answer to the write that introduced the claim;
- tests for prompt injection hidden in retrieved pages.

The memory-security literature's central warning is temporal decoupling: a poisoned entry may appear harmless during write and only become harmful when retrieved days later ([survey, arXiv 2604.16548](https://arxiv.org/html/2604.16548v1)).

### 14.6 Multi-user contribution and change control

For a team wiki, distinguish source contribution, page editing, schema change, and automation change. Document branch/PR rules, required lint/evals, reviewer ownership, conflict resolution, and how concurrent edits are merged. A schema change should include migration and rollback plans because it can silently alter retrieval and agent behaviour across the whole corpus.

Useful repository files include `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and versioned release notes. Publish the knowledge process like software because the artefact is both content and executable context.

### 14.7 Portability and standards

Markdown and Git provide a durable minimum: the human-readable source can move even if a particular model, vector store, or application disappears. Keep caches rebuildable and avoid storing irreplaceable knowledge only in a proprietary embedding index.

One supplied June 2026 report identifies Google Cloud's **Open Knowledge Format (OKF)** as an emerging attempt to formalize LLM-wiki portability, provenance, trust, freshness, lifecycle, and attestation ([Google Cloud announcement](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing); [OKF specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)). Treat it as an evolving interoperability option, not a settled universal standard. A good local schema should be exportable to plain Markdown plus a documented metadata mapping even if OKF or another standard changes.

## 15. Token-efficient operation in coding agents

An LLM wiki saves tokens only when the agent uses **progressive disclosure**. A large wiki combined with a large always-loaded prompt can be more expensive than direct search.

### 15.1 Keep the root instruction file small

For Claude Code, project `CLAUDE.md` files are loaded persistently and parent-level files can be concatenated. Anthropic recommends keeping them concise (the supplied report cites a target under roughly 200 lines) and placing only rules needed in most sessions: architecture, essential commands, safety constraints, and the instruction to consult the wiki before raw sources ([Claude Code memory docs](https://code.claude.com/docs/en/memory)).

Move path-specific rules into `.claude/rules/` and operational procedures into `.claude/skills/`. Importing a long file with `@path` improves organization but does not reduce context if the import is expanded at session start.

When a repository uses `AGENTS.md`, keep one canonical contract where possible. For Claude Code, a short `CLAUDE.md` may import or point to `AGENTS.md`; for other agents, use their native instruction mechanism without maintaining divergent copies.

### 15.2 Use memory as an index, not a duplicate wiki

Agent auto-memory should contain compact operational facts—commands, recurring debugging lessons, user preferences, and pointers—not copied source summaries. The canonical research knowledge remains in the wiki. If the agent loads only the beginning of a memory file, use that space as a map to topic files rather than a long narrative.

### 15.3 Progressive query path

A token-efficient default is:

1. read the small project contract;
2. read `PURPOSE.md`, `hot.md`, and `index.md`;
3. search metadata and open a small set of candidate pages;
4. retrieve exact passages or lines rather than whole large files;
5. open raw-source snippets only for verification, ambiguity, volatility, or high stakes;
6. return a concise answer with citations;
7. save back only a durable supported insight.

Measure the number of pages, source passages, and tool-output tokens opened per query. "Context isolation" through a subagent may protect the main session, but it does not necessarily reduce total tokens because the subagent still performs work.

### 15.4 Put procedures in on-demand skills

Ingest, query, lint, refutation, review, and evaluation are multi-step procedures and belong in skills rather than the root prompt. Skill names and descriptions should make both invocation and non-invocation conditions clear. Too many overlapping skills create router failures; too few create a monolithic context tax.

A practical Claude-oriented layout is:

```text
CLAUDE.md
.claude/rules/wiki-pages.md
.claude/skills/wiki-ingest/SKILL.md
.claude/skills/wiki-query/SKILL.md
.claude/skills/wiki-refute/SKILL.md
.claude/skills/wiki-lint/SKILL.md
.claude/skills/wiki-eval/SKILL.md
raw/
wiki/
eval/
```

See Anthropic's [skills documentation](https://code.claude.com/docs/en/skills) and [features overview](https://code.claude.com/docs/en/features-overview).

### 15.5 Control sessions and compaction

Use context-inspection commands to identify what is consuming the window. Compact long sessions with a clear focus, and write durable decisions to the wiki or log before compaction. Start a fresh session when the task changes materially. Instructions that exist only in conversation are fragile; rules and accepted decisions belong in versioned files ([Claude Code context window](https://code.claude.com/docs/en/context-window); [how Claude Code works](https://code.claude.com/docs/en/how-claude-code-works)).

### 15.6 Keep tool and MCP output narrow

Tool schemas and tool results can dominate context. Let tool search defer unused schemas, disable irrelevant servers, and return ranked candidate pages or compact evidence packs instead of entire documents. Filter, aggregate, and rank locally before returning data to the model ([Claude Code MCP docs](https://code.claude.com/docs/en/mcp)).

A wiki tool should prefer interfaces such as:

```text
search(query, filters, k) -> page IDs + short snippets + scores
read(page_id, line_range) -> exact bounded context
sources(claim_id) -> locators + metadata
health() -> compact counts + paths requiring action
```

### 15.7 Skip unchanged work

Hash sources and derived artefacts, deduplicate before ingest, and recompile only changed or stale pages. Track cache hits, skipped files, and downstream pages invalidated by a source change. This reduces tokens more reliably than prompt compression alone. `nashsu/llm_wiki` and `graphify` describe hash-based caching; Graphify's published token figures are corpus-specific and should be treated as an example to reproduce locally, not a universal benchmark ([Graphify](https://github.com/safishamsi/graphify/blob/v8/docs/how-it-works.md)).

### 15.8 Model routing and randomness

Use the least expensive competent model for mechanical scanning, formatting, link repair, and deterministic orchestration; reserve stronger models for difficult synthesis, adjudication, and high-risk verification. One supplied implementation report singles out `rvk7895/llm-knowledge-bases` for explicit role-based model routing.

Keep maintenance operations low-randomness and schema-constrained. Higher creativity belongs in optional views, brainstorming, or reflection—not citation repair, source registration, or contradiction adjudication.

### 15.9 Token-efficiency checklist

| Priority | Action | Verification |
|---|---|---|
| Highest | Measure start-of-session instructions, memory, and tool definitions. | Record baseline context before changes. |
| Highest | Reduce the root contract to universal rules. | Check line count and instruction adherence. |
| Highest | Require index-first, bounded retrieval. | Track files/passages opened per query. |
| High | Move procedures to skills and path rules. | Compare context and routing errors before/after. |
| High | Hash, deduplicate, and skip unchanged ingest. | Track cache hits and regenerated pages. |
| High | Compact or restart when the task changes. | Verify accepted decisions remain recoverable. |
| Medium | Keep MCP schemas/results progressive and compact. | Track tool-output tokens and unused tools loaded. |
| Medium | Route models by task and use selective refuters. | Track quality and cost by stage. |

The goal is not the lowest token count in isolation. It is the lowest context and compute cost that preserves retrieval coverage, factuality, and maintainability.
## 16. What works (positive evidence)

Patterns that recur across the verified primary sources and community discussion:

**Linking and maintenance burden goes down**, especially for users who previously bounced off "networked thought" tools because the link-keeping was too much manual work. The most concrete public anecdote is from "Be Datable," a long-time personal-knowledge-graph user who described their newer setup: voice notes → local transcription → LLM extracts signal → wikilinks created automatically — a workflow that only became viable once the LLM took over the link-keeping ([unverified] Be Datable post, original URL not located during 2026-05-09 verification).

**Cross-document synthesis improves** because relationships are pre-linked and pre-summarized; the model isn't rediscovering them at query time.

**Token savings** when expensive context (codebase, large prompt schema) is precompiled into a wiki — direction confirmed by multiple reports, exact magnitudes unverified. One code-wiki variant reported cutting session start from ~47,450 tokens to ~360 by reading a precompiled wiki instead of exploring code from scratch ([unverified] r/ClaudeAI).

**Continuity across sporadic sessions.** `hot.md` plus a small index carries enough state that users come back after gaps without re-explaining everything.

**Concrete walkthrough evidence.** A "Build Karpathy's Second Brain With Obsidian + Claude Code" podcast / video walks the full setup with timestamps: setup wizard at 05:53, graph view at 12:21, ingest at 15:38, automated ingestion at 16:29, lint and pruning at 20:19. Useful as evidence that the workflow is demonstrable end-to-end, not just describable; weaker as evidence of long-horizon reliability ([unverified] podcast/video listing; original URL not located during 2026-05-09 verification).

**Decision logs, project memory, research corpora, repeated work** are the strongest fits — better than generic note-taking. The pattern is most powerful when there's something durable to compound: investigations across many sources, decisions worth referring back to, project state that survives context resets.

**Independent confirmation from an existing PKM practitioner.** A Zettelkasten/Obsidian user (six months on Nick Milo's LYT framework with Claude Code) compared the pattern against his own mature system and named three operations his hand-built setup lacked: contradiction detection during ingest (his atomic cards don't cross-compare), cross-page chain updates (one new source updating 10–15 pages at once, where he only adds links manually), and — the one he singled out as most powerful — **concept-gap detection**, the LLM proactively noticing "you've referenced this idea in several places but have no dedicated page for it" and offering to create one. Useful as evidence that the pattern adds something even to a disciplined pre-existing PKM practice, not just to greenfield vaults ([WenHao Yu review](https://yu-wenhao.com/en/blog/karpathy-zettelkasten-comparison/)).

**At Karpathy-scale (hundreds of pages, hundreds of thousands of words), index summaries plus wiki links can be enough** — Karpathy's own framing is that an agent-maintained wiki with indexes and summaries can work without **"fancy RAG"** at his scale — "I thought I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries" ([Karpathy on X](https://x.com/karpathy/status/2039805659525644595); the phrase is the X post's, not the gist's, which says the pattern "avoids the need for embedding-based RAG infrastructure"). The "fancy RAG" phrasing matters because it draws the line where the basic pattern stops being enough; once the corpus or churn outgrows that line, embeddings and graph layers come back into scope (see §10 escalation order).

**Markdown / Obsidian / Git baseline is praised because it's inspectable.** Users can read the wiki, see links, view the graph, diff changes, and avoid opaque memory layers ([Obsidian](https://obsidian.md); [Marp](https://marp.app); [Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview)). Several repos position this as a plain-text, agent-agnostic, privacy-aware alternative to closed "AI memory" products. Karpathy's gist also references [Tolkien Gateway](https://tolkiengateway.net) as a mental model for richly interlinked pages — a useful target image for what a mature wiki feels like (entity pages dense with backlinks, not isolated topic essays).

**Lightweight starts work surprisingly well.** A MindStudio blog post describes the setup as "a Markdown content folder plus Claude Code rather than a dedicated product," and reframes the wiki as optimised for *model* reading more than human browsing — useful intuition, because it explains why dense wikilinks beat prose summaries even when the prose looks nicer to a human reader ([unverified] MindStudio blog). Mark Chen's Medium post claims he created two structured wikis in about an hour, one for Medium writing and one for BI reporting, using Claude Code — direction-only evidence that the pattern is easy to start, not proof it stays reliable at scale ([unverified] Medium post).

Several short community quotes capture the trade-off neatly:

- **"Just fed Karpathy's recipe to Claude…"** — common framing for the "paste the gist and pray" failure mode ([unverified] community thread).
- **"Claude picking the wrong one on ambiguous requests."** — the over-splitting failure mode behind the schema/skill sweet spot ([unverified] r/ObsidianMD).
- **"The lint step is non-negotiable."** — why §7.5 exists ([unverified] r/AI_Agents).
- **"The Wiki significantly outperformed RAG on 'deleted' or archived logic."** — the differential value vs RAG; the mechanism (RAG re-derives from chunks, the wiki preserves the curated reasoning) is sound, magnitude unverified ([unverified] r/ClaudeAI).

## 17. What fails (the risk register)

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

**Public partial-failure cases worth reading.** The [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki/issues) issue tracker exposes real onboarding and ingest problems — partial failures with poor messaging, local-only / read-only complaints. Specific issues to browse: [#60](https://github.com/Pratiyush/llm-wiki/issues/60) and [#326](https://github.com/Pratiyush/llm-wiki/issues/326) — both URLs were not refetched on 2026-05-09 (egress-limited); browse the tracker for current state.

## 18. Skills, plugins, and reusable repos (verification-aware)


### 18.1 How to choose an implementation family

The merged reports describe two broad technical families layered over the five functional forks already listed below:

1. **Graph-first, Markdown-native systems** use page structure, wikilinks, local graph expansion, and often no mandatory vector database. They are attractive for local-first vaults with curated links, low latency, and strong inspectability.
2. **Compiler plus hybrid-search systems** keep Markdown as the canonical authority but add BM25, vectors, reranking, review queues, freshness repair, APIs, and evaluation harnesses as scale and interoperability demands grow.

A third, lighter-weight deployment form is the **agent skill**: no dedicated application, just a schema and on-demand ingest/query/lint procedures inside Claude Code, Codex, OpenCode, Gemini, or a similar coding agent.

Choose according to the actual bottleneck:

| Need | Start with | Add only when measured |
|---|---|---|
| Personal research, hundreds of pages | Markdown, index, log, typed pages, lexical search | Vectors when paraphrase recall is poor; graph tools when multi-hop navigation is poor. |
| Existing Obsidian vault | Vault-native plugin or skill, deterministic lint, Git | Background extraction, graph ranking, local models, review UI. |
| Team/CI/interoperability | Compiler/SDK, review queue, evals, export formats | Hybrid retrieval, API/MCP, permissions, attestations. |
| Codebase rationale | Code as truth, AST/static analysis plus rationale pages | LLM synthesis only where static extraction cannot capture "why". |
| Sensitive corpus | Local filesystem, local retrieval, least-privilege tools | Local models or approved hosted providers after privacy assessment. |
| Large heterogeneous corpus | Clean parsing, manifests, BM25 baseline | Dense retrieval, reranking, entity resolution, graph traversal. |

Dynamic popularity figures, download counts, release counts, and current repository activity from the supplied reports are intentionally not reproduced here as enduring facts. Recheck them at adoption time. Appendix C records cases where the supplied documents disagreed about repository verification.


#### Implementation snapshot from the merged reports

This table preserves the architectural comparison without treating time-sensitive popularity metrics as durable facts:

| Project or pattern | Form | Distinguishing design | Verification treatment in this edition |
|---|---|---|---|
| `green-dalii/obsidian-llm-wiki` | Obsidian plugin | Vault-native graph retrieval, local-first options, no mandatory external vector database | Described in the supplied Claude-Code report; recheck the live repository before adoption. |
| `nashsu/llm_wiki` | Desktop application / local service | `PURPOSE.md`, two-pass ingest, review queue, source watching, hashing, optional vectors, local API/MCP | URL appears in the verified ecosystem; features should still be rechecked by version. |
| `SamurAIGPT/llm-wiki-agent` | Cross-agent skill + Python helpers | Markdown-first wiki, deterministic health/lint, graph export, multi-format conversion | Included in the verified base list. |
| `sdyckjq-lab/llm-wiki-skill` | Multi-platform skill/workbench | Offline graph artefacts and explicit confidence labels such as `EXTRACTED`, `INFERRED`, `AMBIGUOUS`, `UNVERIFIED` | Described in the supplied report; not independently rechecked in the earlier base pass. |
| `atomicstrata/llm-wiki-compiler` | Compiler/SDK/MCP pattern | Review-first compilation, claim provenance, hybrid retrieval, freshness/eval/export concepts | Repository verification conflicts across supplied documents; retain the patterns, recheck the attribution. |
| `langchain-ai/openwiki` | CLI / CI-maintained wiki | Code or personal wiki modes, scheduled updates, agent entry points, emerging OKF compatibility | Described in the supplied report; treat current capabilities as version-sensitive. |
| `safishamsi/graphify` | Skill + deterministic parser/graph pipeline | Changed-file skipping, index navigation, SHA-256 caching, inspectable benchmark artefacts | Verified as an adjacent pipeline component in the base file. |

A project can move between categories over time. Evaluate the source-of-truth model, review path, rebuildability, and failure visibility—not only its feature count.

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
- [rohitg00/llm-wiki (v2)](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) + [rohitg00/agentmemory](https://github.com/rohitg00/agentmemory) — the "v2" architecture doc (see §4.1) plus the persistent-memory engine its lessons came from. agentmemory reports a 95.2% LongMemEval-S score from running BM25 + vector + knowledge-graph retrieval fused with RRF — one of the few quantified retrieval benchmarks in this ecosystem, though it measures the engine, not a markdown-wiki-and-lint baseline, and the *-S* split is weak enough that the number should be read with the caveats in §23 (it likely fits in a frontier context window, and self-reported memory scores rarely share a methodology). Read v2 for the lifecycle/graph/automation vocabulary; read §17's two counter-critiques before adopting the apparatus wholesale.
- [eugeniughelbur/obsidian-second-brain (v3)](https://github.com/eugeniughelbur/obsidian-second-brain) — the "v3" rebuild (see §4.1). Cross-CLI Claude Code / Codex / Gemini / OpenCode skill, MIT, in production since 2026-03 and actively churning (the command count has moved 31 → 43 across releases, so cite the *capabilities* — scheduled agents, write-back-not-append ingest, unsolicited synthesis, a write-time AI-first validator, role presets — rather than a fixed number). The non-negotiable house rule worth lifting even if you adopt nothing else: scheduled writes land in a daily diff note and wait 24 hours before becoming permanent. Its AI-First Vault spec (`references/ai-first-rules.md` inside that repo) is the reference artifact for §23's open tension.
- [SHzzzAyys/scholarbrain](https://github.com/SHzzzAyys/scholarbrain) — academic-research fork of obsidian-second-brain, cited upstream as the first domain-specialized proof case. Worth a look specifically for a research-survey workflow, though browse the repo to confirm current state before relying on it (newer and thinner than the forks above).
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — engineering / llm-wiki skill inside a larger claude-skills monorepo. [Skill landing page](https://alirezarezvani.github.io/claude-skills/skills/engineering/llm-wiki/).
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

**Code-truth variants** (different fork — see §11 three-way contrast). Both are referenced in the gist comment thread but did not URL-verify on 2026-05-09; treat as patterns worth knowing rather than safe-to-cite repos. Search GitHub before installing; both are also listed in Appendix A.

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


## 19. Reproducible diagnostic experiments

Run these against a small frozen corpus before adding more infrastructure. Save inputs, outputs, model/tool versions, token counts, and file diffs so the result is comparable after changes.

### 19.1 Duplicate detection

Create two raw files with nearly identical content and different titles. Expected: one canonical page plus a duplicate-candidate or merge path. Failure: two independent concept pages that later drift.

### 19.2 Staleness and supersession propagation

Add a source that reverses an earlier decision, such as "we standardized on SQLite" followed by "we replaced SQLite with Postgres". Expected: affected pages become stale, contradictory, or `needs_review` before the system answers confidently; the older decision remains traceable. Failure: both claims remain active without surfaced conflict.

### 19.3 Whole-file edit bottleneck

Create a Markdown page of roughly 1,500 lines and update one paragraph near line 1,200. Compare whole-file reading against `PATH:LINE` or another bounded-context read. Record token use, unrelated changes, and whether the intended paragraph was edited correctly.

### 19.4 PDF and OCR routing

Run one clean digital PDF and one scanned PDF through the same ingest path. Expected: the digital document uses direct extraction; the scanned document is routed through OCR and receives a lower-confidence or review flag when layout is uncertain. Failure: both produce polished pages even though the scan text is corrupted.

### 19.5 Fabricated citation and locator test

Insert a plausible-looking but nonexistent path, URL, page number, or timestamp into a draft. Expected: deterministic citation validation fails and the page cannot be promoted. Failure: the model "confirms" the reference without opening it.

### 19.6 Source-versus-summary conflict

Place an incorrect statement in an existing concept page while the raw source says the opposite. Query the claim. Expected: the system either opens the raw evidence or flags the conflict; the concept page does not override the source merely because it is easier to retrieve.

### 19.7 Refuter independence test

Give two refuters the same claim but require blind, independently logged retrieval. Compare their sources, verdicts, and unique errors caught. Then repeat with shared evidence or interactive debate. Expected: the independent condition preserves more diversity; failure is near-identical objections sourced from the same weak snippet.

### 19.8 Forced-contrarianism test

Give refuters a correctly supported claim. Expected: they can return `supported` or `no valid refutation found`. Failure: one invents a problem solely because the prompt demands criticism.

### 19.9 False-correction test

Provide an answer containing one wrong claim and several correct qualified claims. Expected: the wrong claim is corrected while the correct qualifications remain intact. Measure the false-correction rate, not only whether the target error was found.

### 19.10 Matched-budget verifier test

Compare one refuter with a larger token/retrieval budget against two refuters sharing the same total budget. Hold evidence access, revision count, generator, and adjudicator constant. This isolates whether gains come from multiple perspectives or simply more compute.

### 19.11 Privacy and deletion cascade

Register a sensitive source, derive several pages and an embedding/index entry, then execute the documented deletion workflow. Expected: the source and all prohibited derivatives, caches, exports, and search entries are removed or tombstoned as policy requires, while the audit record remains appropriate. Failure: the source disappears from `raw/` but survives in summaries or indexes.

### 19.12 Regression and rollback

Change one schema field, prompt, model, or retrieval component and run the fixed evaluation set. Expected: the system reports metric deltas and can restore the previous accepted state. Failure: quality changes are judged only from a few conversational impressions.

A diagnostic should localize a failure. Do not respond to an OCR problem by adding debate agents, or to a duplicate-page problem by increasing model size.


## 20. Twelve rules

If acting on only a small set of recommendations, use these:

1. Keep original sources immutable and enforce the rule at runtime, not only in prose.
2. Define the purpose, audience, exclusions, risk boundaries, and review policy before scaling the schema.
3. Separate source pages from concept, entity, decision, and synthesis pages.
4. Require exact claim-level provenance; confidence without an evidence chain is not enough.
5. Use staged ingest: analyse, discuss scope, write drafts, verify, then promote.
6. Start with Markdown, index, log, wikilinks, a carry-over note (`hot.md` or equivalent), and lexical search before embeddings or graph infrastructure.
7. Keep the root instruction file and user command surface small; put procedures in a few unambiguous skills.
8. Separate cheap deterministic health checks from expensive semantic lint and refutation.
9. For important factual claims, use two blind complementary refuters plus evidence-based adjudication; never treat majority vote as proof.
10. Evaluate retrieval, factuality, false corrections, cost, and regressions against a fixed test set.
11. Automate reversibly: hash, cache, log, limit file touches, hold uncertain writes, and preserve rollback.
12. Add vector, graph, entity-resolution, multi-agent, or interoperability layers only when a measured failure justifies their cost.


## 21. Likely reasons your implementation is not working

Synthesized across the supplied sources, roughly in the order to inspect them:

1. **The gist is being used as a broad persona prompt rather than a strict operating contract.** The model invents structure and workflow as it goes.
2. **The wiki has no concise purpose or exclusion boundary.** It captures too much and optimizes for the wrong questions.
3. **Original, extracted, source-summary, and synthesis layers are not distinguished.** Derived text recursively becomes "truth".
4. **Claims lack exact locators, freshness, or review state.** Polished pages cannot be audited or safely updated.
5. **Ingest writes before analysis and user scope decisions.** Early misunderstandings harden into many linked pages.
6. **Too much is ingested at once.** Duplicate entities, low-signal summaries, and review debt appear before the schema stabilizes.
7. **The model is not forced to orient through `PURPOSE.md`, `hot.md`, `index.md`, and relevant pages before answering.** It relies on model memory or opens the whole corpus.
8. **Pages are too large or edits are not line-anchored.** Small changes become costly whole-file rewrites and introduce unrelated drift.
9. **There is no deterministic health loop.** Broken links, missing citations, stale pages, and partial ingest failures remain invisible.
10. **Warnings are expressed only in prose.** Misleading fields, unsafe operations, or forbidden sources need renamed schemas, validators, wrappers, or permission boundaries.
11. **Verification is poorly designed.** Identical refuters share the same evidence, are forced to object, use majority vote, or revise without post-checking; added agents then increase noise rather than accuracy.
12. **There is no fixed evaluation set or rollback threshold.** Model, prompt, schema, and retrieval changes are accepted based on feel rather than regression evidence.
13. **Privacy, licence, or external-import rules are implicit.** The system cannot safely decide what may be sent, saved, shared, or deleted.
14. **The stack is too ambitious for the corpus.** OCR, vectors, graph databases, multi-agent routing, and many skills were added before a specific baseline failure was measured.

The fastest recovery path is usually: freeze the corpus; adopt a short purpose and schema, or one of the verified starter skills in §18 (kfchou or Astro-Han); ingest 10–20 curated sources through a two-pass workflow; make citation validation and health checks mandatory; build a small gold question set; then add refuters or retrieval layers only for errors the baseline actually exhibits.

## 22. Templates (copy-paste-ready)


### 22.1 System-prompt skeleton

```text
You maintain a compiled knowledge wiki for the user.

Purpose and truth model
- Read PURPOSE.md and GOVERNANCE.md before ingest, major updates, or high-impact queries.
- raw/ contains immutable original sources and source metadata.
- derived/ contains rebuildable extractions and indexes.
- wiki/ contains cited, typed, maintained Markdown.
- review/ contains proposed or disputed semantic changes that are not active knowledge.
- eval/ contains fixed questions, snapshots, and regression reports.

Non-negotiable rules
- Never modify raw/ through ordinary operations.
- Every non-obvious claim must cite an exact source locator.
- Source pages summarize one source; derived pages do not cite one another as primary evidence.
- Prefer updating a canonical page over creating a near-duplicate.
- Preserve contradictions and superseded claims with traceable history.
- Keep inferred relationships visibly distinct from extracted ones.
- Route low-confidence, external, high-risk, or refuter-disputed writes to review/.
- Every accepted write updates index.md, log.md, backlinks, and affected freshness state.
- Use surgical edits and respect the configured file-touch budget.
- Do not treat model confidence, consensus, or a critique as evidence.

Required orientation
1. Read the short project contract.
2. Read PURPOSE.md, hot.md, index.md, and relevant folder context.
3. Open only a small candidate set of active wiki pages.
4. Open exact raw-source passages when evidence is uncertain, volatile, high-risk, or disputed.

Core operations
- triage: propose trash | source | concept-draft | project-note; never silently commit.
- ingest <path>: register/hash source, analyse, discuss takeaways, write drafts, cite, verify, update index/log.
- promote <page>: approve a reviewed draft and record who/what verified it.
- query: answer from active pages, verify as risk requires, cite pages and raw locators, state gaps.
- refute <page-or-answer>: run blind complementary refuters and evidence-based adjudication.
- health: deterministic structure, link, hash, frontmatter, and citation checks.
- lint: semantic checks for contradictions, staleness, duplication, unsupported claims, and review debt.
- eval: run the fixed retrieval/factuality/cost suite and compare with the accepted baseline.
- reflect: optional; create a clearly labelled exploratory compass, not verified knowledge.

Default folders
- wiki/sources/
- wiki/entities/
- wiki/concepts/
- wiki/syntheses/
- wiki/questions/
- wiki/decisions/
- review/refutations/
- eval/reports/
```


### 22.2 First-time bootstrap

```text
I want you to implement a Karpathy-style compiled knowledge wiki in this folder.

Context
- Viewer/editor: [Obsidian / VS Code / other]
- Agent(s): [Claude Code / Codex / OpenCode / Gemini / other]
- Corpus type: [research papers / articles / meetings / code rationale / mixed]
- Expected scale in the next 3 months: [small curated / medium / large]
- Sensitivity: [public / internal / confidential / mixed]
- Accuracy risk: [low / medium / high]
- Output needs: [Markdown / reports / slides / charts / graph / API]

Please:
1. Draft PURPOSE.md and GOVERNANCE.md from this context and ask me to approve them.
2. Create raw/, derived/, wiki/, review/, eval/, reports/, inbox/, projects/, and scripts/.
3. Draft a short CLAUDE.md or AGENTS.md plus SCHEMA.md.
4. Define source, concept, entity, synthesis, question, decision, and method page types.
5. Add index.md, log.md, hot.md, and a minimal fixed evaluation set.
6. Define triage, two-pass ingest, promote, query, refute, health, lint, update, and eval skills.
7. Add deterministic checks for hashes, links, frontmatter, citations, duplicates, and staleness.
8. Keep the initial command surface small and explain every optional dependency before adding it.
9. Guide me through one source end-to-end, including review and rollback.
10. Do not add embeddings, graph databases, OCR, or multiple agents until the baseline test identifies a need.
```


### 22.3 Ingest

```text
ingest raw/<file-or-folder>

Before writing
- read PURPOSE.md, GOVERNANCE.md, SCHEMA.md, index.md, log.md, and hot.md
- register the source path, type, hash, access/licence, sensitivity, and date
- check for exact and near duplicates
- read or parse the full source; flag extraction/OCR uncertainty
- provide 5–8 candidate takeaways, atomic claims, entities, methods, contradictions, and gaps
- list pages expected to be created, updated, made stale, or held for review
- ask me what to emphasize, exclude, or treat as tentative

Then
- write or update one paraphrased source page
- draft only the relevant concept/entity/synthesis/method pages
- attach exact raw-source locators to every substantive claim
- mark inferred relationships and volatile claims explicitly
- run deterministic citation/link/hash checks
- run the configured refuter gate for high-impact cross-source claims
- place disagreements or low-confidence claims in review/
- update index, log, backlinks, and freshness/dependency state
- report files touched, claims added, claims disputed, checks run, and unresolved actions
```


### 22.4 Query / health / lint bundle

```text
query: <question>
- read PURPOSE.md, hot.md, index.md, and relevant folder context first
- retrieve a small set of active pages; exclude draft/rejected/unresolved review by default
- answer from wiki/ first and open exact raw passages when needed
- cite the pages and source locators used
- state contradictions, missing evidence, and the answer's valid-as-of date
- use the §12 refuter gate for high-impact, novel, volatile, or disputed claims
- save back only a reusable, adequately supported synthesis or decision

health
- check hashes, empty files, frontmatter, index/log coverage, links, citation paths, and queue state
- return compact counts and exact paths
- do not spend tokens on semantic analysis yet

lint
- after health passes, check unsupported claims, contradictions, staleness, duplicates, orphans,
  oversized pages, circular source chains, overdue drafts, refuter disagreements, privacy/licence conflicts,
  scheduled diffs past their hold period, and regression failures
- show the report and proposed file-touch set before substantial fixes
```

### 22.5 Multi-refuter verification bundle

```text
verify-claims <page-or-answer>

Goal
- improve factuality without forcing criticism or treating agent count as evidence

Preparation
1. Decompose the content into atomic claims with stable claim IDs.
2. Attach the cited source passages and freshness metadata.
3. Mark high-risk, volatile, numerical, causal, or cross-source claims.

Refuter A: evidence/source
- work independently
- find supporting and contradicting evidence
- verify source identity, locator, recency, quality, and circular citation
- return supported | contradicted | insufficient_evidence | unverifiable
- it is valid to return: no valid refutation found

Refuter B: entailment/scope
- work independently and do not read Refuter A first
- check whether the evidence supports the exact wording
- test scope, qualifiers, causality, time, units, and certainty
- return the same structured verdict and evidence mapping

Adjudicator
- examine the claim, source passages, and both structured records
- do not count votes or favour verbosity
- choose ACCEPT_ORIGINAL | REVISE | REMOVE | HOLD_FOR_REVIEW | ESCALATE
- preserve the original unless evidence justifies change
- identify dependent claims/pages affected by any revision

Escalation
- invoke a third specialist or human when the two refuters disagree, evidence conflicts,
  confidence is low, the claim is high-risk, or the correction changes the conclusion

After revision
- verify the corrected wording against the accepted evidence
- save the records, diff, models/tools, cost, and final decision under review/refutations/
```

### 22.6 Refuter output schema

```yaml
claim_id:
claim_text:
refuter_role: evidence | entailment | temporal | numerical | domain | contradiction
verdict: supported | contradicted | insufficient_evidence | unverifiable
error_types: []
sources_checked:
  - source:
    locator:
    stance: supports | contradicts | contextualizes
reasoning_summary:
confidence: low | medium | high
proposed_correction: null
no_valid_refutation_found: false
retrieval_log:
  queries: []
  unavailable_sources: []
```

### 22.7 Evaluation harness starter

```text
evaluate-wiki

1. Freeze the corpus commit, schema, prompts, model versions, and retrieval configuration.
2. Run structural health: links, frontmatter, citations, hashes, orphans, duplicates, staleness.
3. Run the fixed query set and save retrieved pages/passages before generation.
4. Score retrieval separately from final-answer quality.
5. Decompose final answers into claims and score factuality, support, contradiction, and abstention.
6. For refuter conditions, record refutation precision/recall and false-correction rate.
7. Record tokens, retrieval calls, latency, cost, files opened, and human review time.
8. Compare against the previous accepted release and a simple baseline.
9. Stop promotion when a core metric crosses its pre-defined regression threshold.
10. Save raw outputs and a compact report under eval/reports/<date-or-version>/.
```

### 22.8 Purpose and governance starter

```markdown
# Purpose

## Audience and decisions supported

## Core questions

## Included sources

## Explicit exclusions

## What becomes durable knowledge

## High-risk claims requiring raw-source verification or human approval

## Privacy and provider boundaries

## Success metrics

## Conditions for splitting, archiving, or retiring the wiki
```

```markdown
# Governance

## Roles and permissions

## Source contribution and rights metadata

## Review queue and approval rules

## Automated-write limits and hold period

## External import policy

## Privacy, retention, deletion, and export rules

## Schema change and migration process

## Evaluation and rollback thresholds

## Incident response and audit-log location
```

## 23. Open questions in the public record


**Do multiple refuters add information or merely compute?** The key unresolved comparison is a matched-budget test: one well-resourced refuter versus multiple independent refuters with the same total tokens, retrieval calls, evidence access, revision opportunities, latency, and monetary cost. The useful question is not only whether `N > 1`, but which mechanism—model diversity, evidence diversity, role specialization, independent reasoning, or adjudication—creates the gain. See §12–13.

**What is the optimal escalation policy?** A practical system needs calibrated triggers for a second or third refuter: disagreement, novelty, risk, volatility, source weakness, or low confidence. Too little escalation misses errors; too much creates false objections and a maintenance burden.

**How should false corrections be bounded?** Most systems focus on errors caught, not correct claims damaged by revision. The false-correction rate, downstream page invalidation, and correction rollback should be first-class evaluation targets.

**Which governance metadata will become portable?** Purpose, provenance, freshness, lifecycle, sensitivity, review, and attestation fields are converging in spirit but not yet in one settled schema. OKF is an emerging option; plain Markdown plus a documented export mapping remains the durable baseline.

**How should multi-user semantic conflicts be merged?** Git resolves text conflicts, not epistemic conflicts. Team systems still need policies for competing interpretations, permissioned sources, reviewer authority, and incompatible evidence.

**What is the right boundary between human voice and agent-oriented representation?** The existing Ahrens-versus-AI-first tension becomes sharper when refuters and automated reviewers are added. A human-facing concept page and an agent-facing evidence record may need different representations while sharing one source graph.

Four limitations worth naming, in case any of them is worth chasing later.

**Independent benchmarks are thin.** Many strong claims are maintainer-authored; few controlled, third-party evaluations of full LLM-Wiki systems exist. Adjacent retrieval benchmarks exist — Daniel Yarmoluk's CKG (curated knowledge graph) benchmark is one — but they don't directly evaluate Karpathy-style markdown wikis ([unverified] CKG benchmark; original URL not located during 2026-05-09 verification). Treat any headline accuracy number with the same skepticism the document applies elsewhere. The cleanest worked example of why: the v2 fork (§4.1) reports 95.2% on LongMemEval-S, a real and widely-cited long-term-memory benchmark (Wu et al., [arXiv 2410.10813](https://arxiv.org/abs/2410.10813), ICLR 2025; 500 questions across five abilities — information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention). But Penfield Labs argues the *-S* split is too easy to mean much: at ~115K tokens per question it fits inside a frontier model's context window, so it functions more as a context-length test than a memory test, and because each system uses its own ingestion, answer-generation prompt, and sometimes its own judge, scores published in a shared table rarely share a methodology. Their exhibit is the documented Mem0/Zep dispute, where two parties evaluating the same systems arrived at wildly divergent numbers ([Penfield benchmark proposal](https://dev.to/penfieldlabs/proposal-a-real-benchmark-for-long-term-ai-memory-systems-57p5)). The harder regime (LongMemEval-M, ~500 sessions per history, where context-stuffing breaks down) is the one that would actually discriminate a compiled wiki from a long-context baseline, and almost nobody reports it. Net: a single benchmark number from a system's own author is weak evidence; ask which split, whose judge, and whether the corpus exceeds the model's context window before believing it.

**The ecosystem is young.** Most relevant *implementation* repos and posts are from April–May 2026; long-horizon reliability data isn't there yet. Expect continued churn and watch for shake-out around which patterns survive 6+ months of real use. The *academic* literature on the underlying problem (agent memory / external memory) is more developed and moving fast — a cluster of 2026 surveys (write–manage–read, storage→experience, externalization, memory security; see §7 and §17) now formalizes much of what the implementation community discovered empirically. For a survey, cite the academic framing for the mechanisms and risks, and the gist/repo ecosystem for the specific markdown-wiki instantiation; they are describing the same loop at different altitudes.

**The Karpathy / community split.** "LLM Wiki" is Karpathy's own term; "second brain" is community language. Many of the most-shared "Karpathy prompts" are not Karpathy's own words — they're community starter prompts and schema files derived from his pattern. Distinguishing pattern (Karpathy's) from prompt (community-derived) matters for citation hygiene.

**Human-voiced notes vs. the AI-First Vault — an unresolved fork in the pattern's purpose.** This document's promote gate (§7.3) rests on Ahrens's claim that paraphrasing in your own voice *is* the thinking, so an LLM-drafted page stays `status: draft` until a human re-voices it. The v3 rebuild attacks exactly this premise: it argues that in a vault where the LLM does almost all the reading, optimizing notes for human reading is optimizing for a reader who never shows up. Its AI-First Vault Principle writes every page for retrieval instead — a `## For future Claude` preamble, machine-readable frontmatter, mandatory wikilinks, per-claim recency markers, verbatim source URLs, self-contained context — and its house style rule is explicit: *do not rewrite vault output to be "more human-friendly."* The two positions are not reconcilable by compromise; they disagree about who the wiki is *for*. The Ahrens view predicts the AI-first vault accumulates ungrounded LLM-voice text that no human ever pressure-tests (the §17 "ingest errors compound" and "noise accumulation" failure modes); the AI-first view predicts the human-voicing gate is a bottleneck that guarantees the wiki stays small and is, in practice, the step people skip until the vault rots. A defensible synthesis nobody in the public record has validated yet: keep the human gate for *concept* and *synthesis* pages (where voice encodes judgement) and let *source* and *entity* pages be AI-first (where the value is retrievability, not insight). Treat that as a hypothesis, not a recommendation. The relevant reference artifacts are §7.3 here and `references/ai-first-rules.md` in the v3 repo ([Ghelbur writeup](https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres)).

## 24. Bibliography and source status

**Karpathy primary:**
- *LLM Wiki* gist (v1, created 2026-04-04): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- X post: https://x.com/karpathy/status/2039805659525644595

**Lineage forks (v2 / v3), verified 2026-06-02 (see §4.1):**
- rohitg00 *LLM Wiki v2* gist: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
- rohitg00 *agentmemory* engine: https://github.com/rohitg00/agentmemory
- Ghelbur *obsidian-second-brain* (v3) repo: https://github.com/eugeniughelbur/obsidian-second-brain
- Ghelbur writeup: https://ghelburlabs.substack.com/p/i-rebuilt-karpathys-llm-wiki-heres
- SHzzzAyys/scholarbrain (academic fork): https://github.com/SHzzzAyys/scholarbrain

**Typed-link / pipeline layer and benchmarks, verified 2026-06-02 (see §8, §23):**
- Penfield "What Karpathy's LLM Wiki Is Missing": https://dev.to/penfieldlabs/what-karpathys-llm-wiki-is-missing-and-how-to-fix-it-1988
- Penfield "We Fixed Karpathy's LLM Wiki — PENgram": https://dev.to/penfieldlabs/we-fixed-karpathys-llm-wiki-pengram-is-the-typed-knowledge-graph-pipeline-everyone-asked-for-j3j
- Penfield "Proposal: A Real Benchmark for Long-Term AI Memory Systems": https://dev.to/penfieldlabs/proposal-a-real-benchmark-for-long-term-ai-memory-systems-57p5
- penfieldlabs/pengram: https://github.com/penfieldlabs/pengram
- penfieldlabs/obsidian-wikilink-types: https://github.com/penfieldlabs/obsidian-wikilink-types
- safishamsi/graphify (architecture credited by PENgram): https://github.com/safishamsi/graphify
- LongMemEval (Wu et al., ICLR 2025): https://arxiv.org/abs/2410.10813

**Provider-level grounding (Anthropic engineering), verified 2026-06-02 (see §3):**
- *Effective context engineering for AI agents* (context rot, structured note-taking, just-in-time retrieval): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- *Effective harnesses for long-running agents* (sessions-as-shifts, compaction insufficiency): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- *Equipping agents for the real world with Agent Skills* (the Skills standard the §18 skill-based repos build on): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills

**Academic / survey grounding, verified 2026-06-02 (see §7, §17):**
- Du, *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers* (write–manage–read loop): https://arxiv.org/abs/2603.07670
- Luo et al., *From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms*: https://arxiv.org/abs/2605.06716
- *Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering*: https://arxiv.org/html/2604.08224v1
- SSGM, *Governing Evolving Memory in LLM Agents* (compounding failure loop; semantic/procedural drift): https://arxiv.org/html/2603.11768v1
- *A Survey on the Security of Long-Term Memory in LLM Agents* (memory poisoning, write→activation decoupling): https://arxiv.org/html/2604.16548v1

**Critiques and practitioner comparisons, verified 2026-06-02 (see §3, §16, §17):**
- Gupta, "Andrej Karpathy's LLM Wiki is a Bad Idea" (strongest anti-pattern case): https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-wiki-is-a-bad-idea-8c7e8953c618
- WenHao Yu, "A Zettelkasten User's Honest Review": https://yu-wenhao.com/en/blog/karpathy-zettelkasten-comparison/
- Lobster Pack, "Karpathy's LLM Wiki and the rise of 'idea files'" (Memex lineage, "do you need one"): https://www.lobsterpack.com/blog/karpathy-llm-wiki-idea-files/

**Verified GitHub repos:** all repos listed in §18 above.

**Tooling:**
- Obsidian: https://obsidian.md
- Marp: https://marp.app
- Obsidian Dataview: https://github.com/blacksmithgu/obsidian-dataview
- Tolkien Gateway (mental model for densely interlinked wikis, referenced in Karpathy's gist): https://tolkiengateway.net
- `qmd` (local Markdown search engine, referenced in Karpathy's gist): https://github.com/tobi/qmd — confirm this is the intended one, as other projects share the name.

**Ahrens grounding (separate folder, this workspace):**
- `references/smart-notes/sources/Ahrens2017HowTT.pdf` (Ahrens 2017)
- `references/smart-notes/outputs/smart-notes-summary.md` (single-page distillation)
- `projects/llm-knowledge-base/outputs/smart-notes-llm-kb-integration.md` (integration design)


**Multi-refuter, verification, and debate literature (integrated in §12–13):**
- *N-Critics: ensemble critics for factuality refinement*: https://arxiv.org/pdf/2310.18679
- *Multiagent debate for improving factuality and reasoning*: https://arxiv.org/pdf/2305.14325
- Systematic study of agent count, diversity, and discussion rounds: https://aclanthology.org/2025.findings-acl.606.pdf
- SELENE selective multi-agent deliberation: https://aclanthology.org/2026.eacl-industry.7.pdf
- Repeated LLM calls, voting, and fact verification: https://arxiv.org/pdf/2403.02419
- Wang et al., *Rethinking the Bounds of LLM Reasoning*: https://arxiv.org/abs/2402.18272
- Smit et al., *Should We Be Going MAD?*: https://proceedings.mlr.press/v235/smit24a.html
- Zhang et al., *If Multi-Agent Debate Is the Answer, What Is the Question?*: https://arxiv.org/html/2502.08788v1
- Chen et al., *When and Why Does Multi-Agent Debate Fail and Does It Really Underperform?*: https://arxiv.org/html/2510.20963v2
- *Multi-Agent Verification: Scaling Test-Time Compute with Multiple Verifiers*: https://arxiv.org/html/2502.20379v1

**Retrieval, evaluation, governance, and portability sources from the merged reports:**
- Azure AI Search hybrid search overview: https://learn.microsoft.com/en-us/azure/search/hybrid-search-overview
- Qdrant hybrid queries: https://qdrant.tech/documentation/search/hybrid-queries/
- IBM RAG evaluation guidance: https://www.ibm.com/think/architectures/rag-cookbook/result-evaluation
- Creative Commons attribution guidance: https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution
- Canadian Intellectual Property Office copyright overview: https://ised-isde.canada.ca/site/canadian-intellectual-property-office/en/copyright
- ICO data minimization guidance: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/
- GDPR Article 5: https://www.legislation.gov.uk/eur/2016/679/article/5
- Google Cloud Open Knowledge Format announcement: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing
- Open Knowledge Format specification: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md

**Claude Code context and skill documentation (integrated in §15):**
- Project memory / `CLAUDE.md`: https://code.claude.com/docs/en/memory
- Skills: https://code.claude.com/docs/en/skills
- How Claude Code works: https://code.claude.com/docs/en/how-claude-code-works
- MCP: https://code.claude.com/docs/en/mcp
- Context window: https://code.claude.com/docs/en/context-window
- Features overview: https://code.claude.com/docs/en/features-overview
- Configuration debugging: https://code.claude.com/docs/en/debug-your-config

## Appendix A: Likely-fictional repos (do not cite without manual confirmation)

Upstream synthesis material references these repos with specific descriptive claims, but their URLs did not surface during verification on 2026-05-09. Likely fictional or under different paths. Listed here so future synthesis runs don't re-introduce them as verified citations. The body still references some of them (e.g., `tuandm/code-wiki` and `Houseofmvps/codesight`) where the *patterns* are worth surfacing even when the repo URLs don't verify — every such reference is flagged inline as `[unverified]`.

- `tuandm/code-wiki` — `tuandm` exists on GitHub but no `code-wiki` repo found. The "code as truth" / `docs-check` / confidence-bands / "I assumed X because I saw Y. Correct?" pattern is real; something matching may exist under a different username.
- `Houseofmvps/codesight` — no `codesight` repo found at this path on 2026-05-09. The zero-LLM AST/regex code-wiki compiler pattern is real and worth knowing; the citation is not.
- `QipengGuo/llm-wikidata` — did not surface. Pattern claimed: ChromaDB-backed entity recall to prevent duplicate entities at larger scale.
- `atomicstrata/llm-wiki-compiler` — no search hits. A similarly named `ussumant/llm-wiki-compiler` may exist; not confirmed. Pattern claimed: `compile --review` flags, claim-level provenance, typed page kinds, contradiction metadata, BM25 rerank.
- `yazanabuashour/openclerk` — `yazanabuashour` exists but `openclerk` repo did not surface; most public `openclerk` results are an unrelated PHP/crypto project. Pattern claimed: provenance-bearing JSON runner, stale-projection detection, duplicate-candidate report, optional semantic/OCR modules.

The descriptive features attached to these repos (`compile --review` flags, claim-bearing JSON runners, stale-projection detection, duplicate-candidate reports, line-anchored retrieval, confidence bands, audit-by-yes/no, AST-based deterministic compilation) are real patterns that recur across multiple verified repos — the patterns survive even when individual repo citations don't.

## Appendix B: Unverified Reddit / X / specific gist comments

Egress restrictions blocked direct fetch of Reddit, X, and specific gist permalink comments during the 2026-05-09 verification pass, and the thread IDs did not surface in WebSearch fallback. **This caveat now applies to the Reddit threads only.** As of 2026-07-27, X and the gist are directly fetchable: the originating post and the trending page both serve their real content, the gist body was read in full (which is how the "designed to be copy pasted", "persistent, compounding artifact", "Obsidian is the IDE" and "articles, papers, images, data files" quotes are now verbatim-verified, and how the "fancy RAG" and 100-articles/400K-words attributions in §10 and §16 were corrected from the gist to the X post), and the permalink resolves to the gist — though the visible comment thread is paginated to the most recent replies, so a specific older comment still cannot be pinned. Reddit answers with a bot-verification interstitial rather than the thread, so its `[unverified]` flags stand. Specific descriptive claims drawn from these threads — token figures, line counts, the `FINAL_REASON` / "semantic gravity" example, the 65–90% token-savings numbers, the 400 / 800-line caps, the `compile --review` provenance pattern, the $15 / 2,000-bookmark cost figure — are consistent across multiple verified secondary sources but were not independently confirmed at the primary source. Treat as "believe but verify."

- r/AI_Agents: https://www.reddit.com/r/AI_Agents/comments/1sqg5ew/spent_a_weekend_actually_understanding_and/
- r/ClaudeAI (token reductions): https://www.reddit.com/r/ClaudeAI/comments/1sfdztg/90_fewer_tokens_per_session_by_reading_a/
- r/ClaudeAI (second brain as wiki): https://www.reddit.com/r/ClaudeAI/comments/1sc7i84/vibe_code_inventors_second_brain_as_a_wiki/
- r/ObsidianMD (refactor): https://www.reddit.com/r/ObsidianMD/comments/1sqfe7m/i_have_refactored_the_karpathy_llmwiki_and_it_is/
- r/learnmachinelearning (hardest part): https://www.reddit.com/r/learnmachinelearning/comments/1sq5bxl/the_hardest_part_in_building_karpathys_llm_wiki/
- Karpathy gist comment permalink: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f?permalink_comment_id=6090303
- X trending: https://x.com/i/trending/2042013766036926944
- Pratiyush/llm-wiki issues #60 and #326: https://github.com/Pratiyush/llm-wiki/issues/60 and https://github.com/Pratiyush/llm-wiki/issues/326 (both URLs not refetched 2026-05-09 due to egress; tracker root browseable for current open issues)

*Resolved 2026-06-02:* the "LLM Wiki v2 gist comment" previously cited as unverified in §8 and §17 is now identified, fetched, and verified as `rohitg00/2067ab416f7bbe447c1977edaaa681e2` — see §4.1 and §24. The "memory lifecycle missing" claim it backed, and the two counter-critiques now in §17, are drawn directly from that gist and its comment thread.

## Appendix C: Reconciliation of the supplied source documents

This consolidated edition used five supplied artefacts: the prior best-practices file, the *Andrej LLM KB* PDF export, two deep-research Markdown reports, and the multi-refuter literature review.

### C.1 How overlap was handled

The PDF and the implementation-focused deep-research report substantially overlap with the prior best-practices file on the three-layer architecture, staged ingest, source/concept separation, citations, lint, small initial corpora, line-anchored retrieval, optional OCR, and failure modes. Those details were merged into the relevant operational sections rather than duplicated as separate reports.

The Claude-Code-focused report contributed material that was less developed in the prior file: `PURPOSE.md`, governance/review queues, systematic evaluation, privacy/licensing, portability, hybrid retrieval as an acceleration layer, and progressive context loading. These are integrated in §2, §5–7, and §13–15.

The multi-refuter report is integrated as a separate accuracy layer in §12 and as a matched-budget evaluation design in §13. It is not treated as evidence that a large agent swarm is automatically better.

### C.2 Conflicting repository verification

The supplied reports do not agree on every repository. In particular, one report presents `atomicstrata/llm-wiki-compiler`, `yazanabuashour/openclerk`, `QipengGuo/llm-wikidata`, `tuandm/code-wiki`, and `Houseofmvps/codesight` as concrete implementations, while the earlier URL-verification pass did not confirm some of those paths and listed them in Appendix A.

This file therefore follows three rules:

1. retain reusable design patterns when they are corroborated elsewhere;
2. preserve the conservative verification label for an uncertain repository attribution;
3. require a fresh manual or web check before installation, citation as a live project, or reliance on dynamic claims.

The same caution applies to star counts, download counts, release counts, "production-ready" labels, and benchmark numbers reported by maintainers. They are time-stamped evidence, not permanent properties.

### C.3 Evidence hierarchy used in this edition

From strongest to weakest for a factual claim about the system:

1. immutable source or official specification;
2. inspectable repository file, release, issue, or reproducible command;
3. peer-reviewed paper or official technical documentation;
4. maintainer-authored report with concrete artefacts;
5. practitioner anecdote with a described corpus and failure modes;
6. unattributed social-media claim or search snippet.

Lower-tier evidence can reveal a useful failure mode, but it should not silently become a high-confidence operational fact.
