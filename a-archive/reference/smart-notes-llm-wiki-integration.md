# Integrating *How to Take Smart Notes* with the Karpathy LLM knowledge base

> Foundation document combining **Ahrens's Zettelkasten discipline** (Sönke Ahrens, *How to Take Smart Notes*, 2017) with the **LLM-maintained wiki pattern** (Andrej Karpathy, [LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f); [Karpathy on X](https://x.com/karpathy/status/2039805659525644595)).
>
> Ahrens describes the human's note-making discipline and the underlying epistemology. Karpathy describes the LLM's bookkeeping role. They map onto the same architecture, and the failure modes one warns about are mostly fixed by the discipline the other supplies.
>
> Companion files: `llm-wiki-best-practices.md` (the public-record synthesis of Karpathy's pattern, cited as **BP §N**) and `smart-notes-summary.md` (the faithful single-page distillation of Ahrens, cited as **Ahrens ch. N**). This document supersedes both for the question "how do I actually combine these into a working system?"

## 0. How to read this document

This is a guide to building the system, not a description of one particular vault. Each section states a practice, the reason behind it, and the failure mode that returns if you drop it. Where a choice genuinely comes down to your own tools or threat model, the guide says so rather than pretending there is one answer; §22 collects those open choices in one place.

The spine of the argument: let the LLM do the bookkeeping Ahrens describes, and protect the cognitive operations Ahrens insists on. Everything else follows from that separation — the project desktop, the cut-prose graveyard, disconfirming-evidence capture, spaced retrieval of old notes, Verbund parallel projects, the two-slipbox topology, hub-note caps, memory tiers, and the operational hardening (touch budgets, idempotency, audit-prompt style) that ties each discipline to the specific risk it closes.

## 1. The argument in one paragraph

Let the LLM do the bookkeeping Ahrens describes — wikilinks, indexing, contradiction scans, format checks — and protect the cognitive operations Ahrens insists on: paraphrasing, atomicity, promotion, and the choice of what an idea "is about". Ahrens already named "a Wiki" as one acceptable slip-box medium (Ahrens ch. 3). The integration is not a mash-up. It is what Ahrens's framework looks like once an LLM does the linking and indexing for you, with the human still doing the thinking. This is the **hybrid** position on the foundational decision, and every other decision in this document is a consequence of that one separation.

The lineage is older than either source. Vannevar Bush's 1945 "As We May Think" described the *memex* — a personal store of books, records, and communications, linked by associative trails the user builds and can recall later (Bush 1945). Bush could specify the trails but could not solve *who maintains them*; the trails had to be hand-built and degraded as the researcher's interests moved on. Ahrens's answer was human discipline; Karpathy's is the LLM. The integration's claim is that you need both: the LLM to absorb the maintenance Bush could not automate, and Ahrens's discipline to keep what the LLM maintains worth maintaining.

## 2. Why integrate: each system is incomplete on its own

Pure Karpathy fails when the human stops curating. Ingest errors compound, hallucinations bake into "facts", noise accumulates, the wiki recursively cites itself as truth. These are the failures Ahrens's discipline prevents — by insisting the human writes literature notes in their own words and elaborates each idea before it enters the slip-box.

Pure Ahrens / Zettelkasten fails because the bookkeeping is exhausting. Footnote-level discipline (literature note → permanent note → atomic note in your own words → wikilinks added by hand → review and reorganize) is where most note-takers drop off. The LLM is good at exactly that bookkeeping — proposing wikilinks, flagging contradictions, regenerating an index, scanning backlinks.

The combination plugs each one's main hole. Ahrens supplies the discipline that stops the wiki rotting; the LLM supplies the bookkeeping that stops the human burning out. This is corroborated by independent practitioners: the most-developed public extension of Karpathy's pattern (rohitg00's "LLM Wiki v2", built from lessons maintaining an agent-memory engine) arrives at the same hard rule from the engineering side — "human-in-the-loop as a write gate is not backwardness, it is quality control when the writer is a stochastic process," with the schema doing roughly 90% of the work and automation added only after dozens of manual cycles prove stable (rohitg00 2026). That is the load-bearing human and the ban on first-run auto-ingest, reached by a different route.

The boundary on this claim is set out in §17: the hybrid is for small-to-medium, slow-moving, human-curated research folders, not high-churn, regulatory-critical, or very large multi-user corpora.

## 3. The Ahrens grounding

Four underlying principles (Ahrens ch. 5–8) that constrain every design choice below.

**Writing is the only thing that matters** (ch. 5). Writing is not the activity that follows research. It *is* the medium of research, learning, and thinking. You read with a pen because you cannot rephrase what you don't understand. You listen with a notebook because the test of attention is whether you can rebuild the argument later. The manuscript is residue; the writing is the work. Translating from a source into your own context is the cognitive operation that distinguishes "having read" from "having understood." This rules out letting the LLM write literature notes or promote drafts — both bypass the operation that would otherwise force understanding.

**Simplicity is paramount** (ch. 6). Power comes from a standardized format that lets ideas be combined cheaply, not from a clever ontology. Topic-based filing systems get worse as they grow because they push complexity into the structure itself; the slip-box pushes complexity into the connections between simple, uniform notes. Storage cost is constant per note while combinatorial value grows roughly with the square of the number of notes. The right question is not "Under which topic do I store this?" but "In which context will I want to stumble upon this again?" This dictates flat folder layout, atomic page typology, uniform frontmatter, and bottom-up topic emergence rather than a pre-designed ontology.

**Nobody ever starts from scratch** (ch. 7). The blank-page model is a misunderstanding. Every project is downstream of prior reading and prior commitments. The slip-box makes that prior work tangible. The reliable sign that a workflow has converted to circular: the problem of "finding a topic" is replaced by the problem of "having too many topics to write about." The wiki is the externalization of that prior work; the LLM accelerates retrieving it.

**Let the work carry you forward** (ch. 8). Bad workflows are *exergonic* — willpower-fed, exhausting. The slip-box is *endergonic* — once triggered, each step generates the next: a fleeting note generates a literature note, a literature note generates a permanent note, a chain of permanent notes generates a topic, a topic generates a draft. Motivation comes from visible progress, not from discipline. Slip-box value grows roughly exponentially with size, not linearly, because each new note can connect to every existing note. The LLM removes the friction Ahrens's pen-and-paper version still required — but only if the LLM's role is friction-removal, not work-replacement.

A fifth principle from ch. 9 sits underneath the workflow design and is treated in §14: **standardize the environment, spend the decision budget on substance**. Willpower depletes (Baumeister et al. 1998); standardizing organizational decisions — one capture method, one slip-box format, one note-extraction routine — frees decision capacity for content. The danger to avoid is standardizing the *wrong* thing, where workflow conventions calcify around outdated practice; the rule is to standardize only the organizational layer.

The credibility argument is Luhmann's output: roughly 90,000 notes, 58 books, hundreds of articles in 30 years, with about half a dozen more posthumous books from near-finished manuscripts. His own explanation: "I, of course, do not think everything by myself. It happens mainly within the slip-box" (Luhmann, Baecker, and Stanitzek 1987). He described his working rule as only ever doing the easy thing — writing only when he already knew how, and setting anything that made him falter aside to work on something else (1987). The slip-box is the reason both claims are true. The LLM-augmented version aims for the same property at less expense.

## 4. The architectural alignment

Same building blocks, different vocabulary.

| Ahrens | Karpathy / LLM Wiki | What it is |
|---|---|---|
| Reference system (Zotero) | `raw/` | Immutable source-of-truth documents. Never edited. |
| Literature notes | `wiki/sources/<source>.md` | Brief, paraphrased summary of a source — what struck you, in your own words. Tied to the source. |
| Permanent / main notes (slip-box) | `wiki/concepts/`, `wiki/syntheses/`, `wiki/entities/`, `wiki/decisions/`, `wiki/questions/` | Atomic, self-explanatory, reusable. Written so the idea survives without its original context. |
| Project notes | `projects/<name>/` (outside the main wiki) | Project-specific scaffolding, drafts, to-dos. Discardable when the project ends. |
| Project desktop / scratch space | `projects/<name>/desktop/` (or external canvas) | Where notes are copied out and rearranged for one manuscript without touching the slip-box. |
| Cut-prose graveyard | `projects/<name>/xy-rest.md` | Holding file for prose cut from drafts, so cutting feels painless. |
| Fleeting notes | `inbox/` (outside `raw/` and `wiki/`) | Reminders to be triaged within a day or so, then trashed or elevated. |
| Index / register / "tag-trees" | `wiki/index.md` + wikilinks | Navigational layer. Entry-points only, bottom-up rather than topic-down. |
| Manual cross-references between notes | Wikilinks under `Connections` on each page | Explicit links anywhere in the system. The "weak ties" (Granovetter 1973) — Bush's associative trails — that yield surprising new perspectives. |
| Hub / overview-of-a-topic notes (Schmidt type 1) | `wiki/syntheses/<topic>.md` | Notes that collect up to ~25 links to other notes on a topic. Function as entry points. |
| Slip-box numbering (e.g., 22, 22a, 22a1) | Filename + frontmatter `aliases` | A permanent address, not a category. Branching is unbounded. |
| The slip-box itself (the durable artefact) | `wiki/` (the compiled, interlinked Markdown) | What compounds over time. |
| Two slip-boxes (bibliographical + main) | `wiki/sources/` lifecycle vs. the rest of `wiki/` | One repo, two clear lifecycles: sources are immutable-confidence literature notes; the rest are ideas. |
| The human (curator, thinker, writer) | The human (still) | Decides what to elevate, what to call things, which connections matter. |
| Pen and paper / Lüdecke's Zettelkasten / "any wiki" | LLM agent + Markdown editor (Obsidian) | The interface. |
| — | Schema file (`CLAUDE.md` / `SCHEMA.md` + skills) | New layer the LLM pattern adds: explicit rules so the agent behaves like a disciplined wiki maintainer. |

Three things to notice. First, the human row is unchanged — the LLM doesn't replace any of Ahrens's intellectual work. Second, the schema file is the only genuinely new layer; almost everything else is a rename. Third, three rows are easy to miss — the project desktop, the cut-prose graveyard, and the two-slipbox lifecycle split — but they are core Ahrens, not embellishments, and are treated in §6 and §8.

## 5. Page typology and atomicity

Six frontmatter `type` values, each with a defined role (full set: source, concept, entity, synthesis, question, decision). The first four are required; the last two are conveniences worth using once the basics are stable. The workable floor is `source + concept`; take the full set because the question/decision types are what make the save-answers-back round-trip work and the synthesis type protects cross-source claims from being mistaken for single-source concepts.

- **source** — paraphrased summary of one raw document. One file per source. Confidence high (sources are immutable). Tied to a `raw/` locator. Maps to Ahrens's literature notes.
- **concept** — one atomic idea, self-explanatory, reusable across topics. **One idea per file** — non-negotiable. Maps to Ahrens's main slip-box notes.
- **entity** — a person, project, tool, dataset, organization. Useful because entities recur across many concepts and benefit from a canonical page. Edge case to settle in the schema: a named method that is both an idea and an artefact (e.g., "BERT") needs a written rule for which folder it lives in.
- **synthesis** — a cross-source claim that doesn't reduce to a single concept or entity. Maps to Ahrens's "overview-of-a-topic" notes (Schmidt 2013, type 1). Doubles as the hub-note type.
- **question** — a saved investigation: the question, the answer, and the wiki pages cited.
- **decision** — a reusable choice and its rationale.

**Atomicity** is the one place both sources are most aligned (*idea*-atomic, the working definition). The LLM will resist it on its own. Left alone, an LLM drifts toward writing topic pages that try to be comprehensive — exactly the structure Ahrens spent ch. 6 warning against. His objection (ch. 6) is that topic-based filing offers only two bad options as it grows: pile more notes under one topic until they become impossible to find, or keep splitting into sub-topics until the mess simply relocates one level down. Atomicity has to be enforced in the schema: one idea per file, one main claim per file, every page must answer "from what other contexts would I want to stumble upon this?" "Idea-atomic" rather than "strict-atomic" is the chosen reading — one idea, possibly with supporting bullets — because strict one-claim-per-page fragments navigation while topic-atomic re-creates the drift.

**The self-explanatory rule**. Concept and synthesis pages must read independently of their source pages. A page that leans on phrases like "as the paper notes" or "in this work" has become a source-summary in disguise and has lost the slip-box's compounding property. This is lint-detectable with simple regexes and is the structural form of Ahrens ch. 6 ("self-explanatory, so the idea survives without its source context") and ch. 11 ("translate them into the context of your own thinking").

**The single-source-of-truth derivation rule**. Every concept / synthesis / question / decision page should trace to at least one `source` page or `raw/` locator, and lint flags any page whose only citations are other wiki pages. Strict (forbidding wiki-to-wiki primary citation entirely) is the most defensive against recursive self-citation; the soft form is the working compromise, since some syntheses legitimately build on concepts. The recursion smell — a concept page citing only other concept pages — is a standard lint target (§12).

**Page size limits** make atomicity enforceable (soft 400 / hard 800). Beyond the soft cap, edits become whole-file rewrites and the model loses the thread; this is the "whole-file edit bottleneck" failure mode (§15). If a page hits the soft cap, that is a signal it has stopped being atomic and should be split. Note the literature does not converge here: Ahrens's "one side of A6 paper" (ch. 1.3) is roughly 100–150 words, far stricter than BP's 400/800 lines. Source pages may run longer than concept pages because they hold evidence pointers; per-type caps are allowed but not required. Word and per-bullet thresholds are a softer atomicity signal and are optional.

**Tentative-claim markers** carry uncertainty at finer grain than the page-level `confidence` field. The page-level field says how sure the page is on average; it can't distinguish a load-bearing inference from a settled fact sitting in the same page. Mark weak inferences inline (`*[tentative]*`) and disputed bullets inline (`*[disputed — see Contradictions]*`) so a guess is never silently read as a fact at the point of reading. This is the in-wiki form of the same confidence discipline that governs how the system reports to the human (Verified / Confident / Unsure / Guess): the marker travels with the claim rather than living only in metadata. Inline markers do clutter prose, so reserve them for claims that are actually load-bearing and uncertain; everything else relies on the frontmatter `confidence` value and the per-claim provenance of §13.

## 6. The four note types, mapped

Ahrens (ch. 6) is explicit that distinguishing categories is "crucial to building critical mass": fleeting, permanent, and project. Permanent has two sub-forms — literature notes (in the reference system, brief, context = the source) and main notes (in the slip-box, self-explanatory, atomic). Each maps to a folder, with the LLM's role in each case.

### 6.1 Fleeting notes → `inbox/`

**Ahrens.** "Reminders of information ... will end up in the trash within a day or two." Pen, paper, voice memo, anything frictionless. The point is to capture before the thought escapes; not the thought itself.

**Integration**. Keep an `inbox/` folder *outside* `raw/` and `wiki/`. Don't let the LLM ingest from `inbox/` automatically — fleeting notes are pre-decision. The LLM's role is to triage daily: each fleeting note is either trashed, promoted into a literature note (if it cites a source), or promoted into a draft permanent note (if it's an original idea).

**Why outside the wiki.** If the LLM treats fleeting notes as ingest material, the wiki accumulates noise. Ahrens's third typical mistake (ch. 6) is treating all notes as fleeting; the LLM-wiki version of that mistake is auto-ingesting the inbox.

### 6.2 Literature notes → `wiki/sources/<source>.md`

**Ahrens.** Brief, in your own words, about what caught your attention in the text (ch. 6). Luhmann never underlined or wrote in margins — he made one short note per text on a separate piece of paper, then later wrote a permanent note from it. The key word is **paraphrase**. Underlining is a fleeting note. A literature note has been thought through.

**Integration**. The Karpathy ingest protocol's "discuss takeaways before writing" step is exactly this. The LLM proposes a fixed number of candidate takeaways from the source (pick one — 5–8 is the common choice; kfchou uses 3–5 and Karpathy-help uses 5–8, but do not let the model choose the number freely); the human decides which to keep, edits the wording, then the source page is written. The source page is **paraphrased, not extracted**. Direct quotes get quotation marks and a page locator; everything else is in the human's own voice. The translation rule belongs at *ingest* time, not just at promotion, because the promotion gate (§11) catches unparaphrased concept pages but not unparaphrased source pages — and an extracted source page propagates its "read but not understood" defect into every concept derived from it.

**Frontmatter.**

```yaml
---
type: source
title: <author> <year> — <short title>
authors: [<author>]
year:
locator:               # path to raw file, e.g. raw/papers/transformer-paper.pdf
frame:                 # optional: the angle this ingest was run with
status: active
confidence: high       # because it cites a real, immutable source
last_updated:
---
```

The optional `frame` field records the angle an ingest was run with, so a future reingest can reuse it rather than contradict it. Without recording the frame, a scoped ingest and a later comprehensive reingest produce conflicting source pages.

**Why this matters.** The literature note is what protects the wiki from compounding errors. If the source page is in your own words and ties back to a specific page or section of the raw source, every concept page that derives from it has a real, checkable provenance. If the source page is a copy-paste or LLM-summary you didn't read, the rest of the wiki inherits that fragility.

### 6.3 Permanent / main notes → `wiki/concepts/`, `wiki/syntheses/`, `wiki/entities/`, `wiki/decisions/`, `wiki/questions/`

**Ahrens.** "Written in a way that can still be understood even when you have forgotten the context they are taken from." Self-explanatory. Atomic — one idea per note. Written as if for print. Every permanent note should "have the potential to become part of or inspire a final written piece." Once filed, it is never thrown away (ch. 6).

**Integration.** This is the heart of the slip-box / wiki. Each `wiki/concepts/<idea>.md` is one atomic idea. `wiki/syntheses/<topic>.md` is for cross-source ideas that don't reduce to one entity or concept. `wiki/entities/` holds canonical pages for recurring people, projects, tools, datasets. `wiki/decisions/` and `wiki/questions/` are conveniences that capture the save-answers-back round-trip.

**Frontmatter.**

```yaml
---
type: concept             # or: synthesis, entity, decision, question
title:
aliases: []
tags: []                  # question-derived, not content-derived
sources:
  - path: wiki/sources/<source>.md
    locator:               # e.g. ch. 6, p. 38; or section heading
    confidence: high | medium | low   # categorical, not numeric
    date_accessed:
status: draft | active | superseded   #
last_updated:
---
```

Frontmatter shape is medium-to-maximal. Go fully maximal and you re-open placeholder-padding (empty fields filled with junk), so fields a page can't honestly fill are left absent rather than invented — the no-stub principle.

The `status: draft` flag is what makes the integration possible. **The LLM may draft a concept page during ingest, but it does not get to promote it to `active`.** Draft pages are excluded from query results unless explicitly requested. Promotion is a human decision, made after the human has read and rewritten the page in their own voice. This preserves Ahrens's discipline while letting the LLM do the boring scaffolding.

The `status: superseded` flag handles the memory-lifecycle problem (BP §13): not all knowledge stays equally valid forever. A superseded page links forward to the page that replaced it; both stay in the wiki but only the active one shows up in queries by default. This is the resolution to a real tension with Ahrens — ch. 6 says permanent notes are *never thrown away*, so in the LLM-wiki version "thrown away" becomes "superseded (kept, demoted)" or "forgotten with quarantine".

Tags are **question-derived, not content-derived**. Ahrens (ch. 12) warns that the keywords a tool auto-suggests from a note's text are usually the worst options — already obvious in context. Good keywords connect to the lines of thought you're working on ("in which circumstances will I want to stumble upon this again?"), and are usually *not* present in the note itself. Assigning a keyword is a thinking task; it is therefore a human commit, not an LLM auto-fill (§14).

### 6.4 Project notes → `projects/<name>/`, with a desktop and a graveyard

**Ahrens.** Kept in a project-specific folder, discarded or archived after the project ends. They include comments in the manuscript, project-specific literature collections, outlines, draft snippets, reminders, to-dos, and the draft itself (ch. 6). The format doesn't matter, because they will end up in the bin (or the archive — "the bin for the indecisive") once the project is finished anyway. Crucially, Ahrens also describes two structures that are easy to overlook: the **desktop** ("built-in project-specific desktops where you can rearrange ideas and conceptualize chapters without touching the slip-box itself," ch. 6, 13) and the **cut-prose graveyard** (the `xy-rest.doc` trick, ch. 13 — cut passages are moved to a holding file so that deletion feels painless, even though they are almost never reused).

**Integration**. Keep `projects/<name>/` separate from the main wiki. Add a `projects/<name>/desktop/` scratch space (or an external Obsidian canvas) where the human copies notes out of the slip-box, rearranges them for one manuscript, and drafts — *without editing the slip-box notes themselves*. Add a `projects/<name>/xy-rest.md` graveyard for cut prose. Both are cheap and both close real failure modes: no desktop re-opens the temptation to edit slip-box notes for one project's prose (which contaminates them); no graveyard re-opens draft bloat (cutting feels like loss, so cuts don't happen).

**Why separate.** Ahrens's second typical mistake (ch. 6) is collecting only project-specific notes — "you have to start all over after each project and cut off all other promising lines of thought." The slip-box is the cross-project reservoir. The LLM-wiki version of the mistake is wiring `projects/<name>/` into the same ingest pipeline as the main wiki. Don't (§15 mistake #2).

**The reverse path matters too**. Project notes legitimately *produce* reusable ideas — the Verbund by-products of §18. The system needs an explicit path for promoting a project-note insight into the slip-box (the human marks the note; the operation copies the idea into `inbox/` or drafts a concept page for normal triage), distinct from auto-detection (which re-opens silent promotion) and from doing nothing (which loses the insight when the project archives).

## 7. Folder layout

```text
knowledge-base/
  CLAUDE.md                          # short global rules + pointers to skills
  SCHEMA.md                          # page types, frontmatter, citation rules
  MEMORY.md                          # stable identity / conventions
  CRITICAL_FACTS.md                  # pinned, always-read, load-bearing facts
  inbox/                             # Ahrens fleeting notes — triaged daily, never auto-ingested
  raw/                               # Ahrens reference system; immutable, chmod -w enforced
    papers/                          # x.pdf + x.md extraction alongside
    articles/
    transcripts/                     # AI-session transcripts, higher promotion bar
    notes/
  wiki/                              # Ahrens slip-box, LLM-maintained
    index.md                         # entry-points only, ~1–2 notes per keyword
    log.md                           # structured, append-only
    hot.md                           # carry-over context for sporadic sessions
    sources/                         # one literature note per source (bibliographical slip-box)
    concepts/                        # atomic permanent notes
    entities/                        # people, projects, tools, datasets
    syntheses/                       # cross-source notes + hub notes
    decisions/                       # reusable choices and rationale
    questions/                       # saved investigations
    attachments/<source-stem>/       # extracted figures, stem-prefixed names
    contradictions.md                # global index of cross-source disagreements
    disconfirming.md                 # global index of evidence against the user's own hypotheses
    gaps.md                          # open questions
  projects/                          # Ahrens project notes — outside the slip-box
    <project>/
      desktop/                       # project scratch space
      xy-rest.md                     # cut-prose graveyard
  quarantined/                       # rollback target for forgotten/overwritten pages
  reports/                           # lint / health / ingest reports
  scripts/
    lint_links.py
    lint_frontmatter.py
    find_orphans.py
    find_drafts.py                   # status: draft pages overdue for promotion
    find_stale_inbox.py              # inbox items older than 24 h
    check_citations.py               # opens each cited path, confirms it exists
    search_bm25.py
  skills/
    wiki-triage.md                   # daily inbox triage
    wiki-ingest.md                   # staged, idempotent, content-cached
    wiki-promote.md                  # human-driven draft → active
    wiki-query.md
    wiki-lint.md                     # structural + semantic split
    wiki-supersede.md                # replace, keep prior view
    wiki-forget.md                   # remove with quarantine
    wiki-synthesis-scan.md           # active cluster discovery
    wiki-reflect.md                  # periodic direction review → compass.md
    rebuild-backlinks.md             # periodic backlink re-derivation
```

The additions over the pure Karpathy layout each support an Ahrens discipline that pure Karpathy leaves implicit: `inbox/` + `wiki-triage` (the 24-hour rule), `wiki-promote` + `find_drafts.py` (the elaboration gate), the project `desktop/` and `xy-rest.md` (Ahrens's drafting structures), `disconfirming.md` (Darwin's golden rule), `wiki-synthesis-scan` (bottom-up emergence as a system property), and the memory tiers (`MEMORY.md`, `CRITICAL_FACTS.md`, `hot.md`) that keep session-start orientation cheap (§8). The `quarantined/` folder and `check_citations.py` are the operational hardening of §13.

Folder ordering (plain `raw/`/`wiki/` vs. prefix-numbered `0-raw/`/`1-wiki/`) is **deferred**: neither source prescribes it, both work, and the choice is down to whether you want a workflow-order sort in your file browser. The live wiki uses prefixes; this document uses plain names; that is the one place the two diverge harmlessly.

## 8. Schema and operating contract

The schema is **split**, not monolithic. The community converged on this after monolithic `CLAUDE.md` files reached 300+ lines and started consuming significant context every session. Counter-warning: too many overlapping micro-skills create router errors. The sweet spot is short global rules plus a few clearly named skills with explicit "when not to use this skill" guidance.

Three things go in the schema layer:

1. The **page-type contract** as YAML frontmatter on every page (§6).
2. The **operating rules** that govern the agent's behaviour (below).
3. The **memory tiers**: `CLAUDE.md`/`SCHEMA.md` hold the durable rules (human-owned), `MEMORY.md` holds stable identity and conventions, `CRITICAL_FACTS.md` is the always-read pinned tier for facts that must never scroll past, and `hot.md` is the per-session orientation cache. The split exists so volatile state, stable rules, and load-bearing facts don't compete for attention; operational size caps keep them cheap to read at session start.

Operating rules (the non-negotiables):

- `raw/` is immutable — enforce at runtime (`chmod -w`), not just in prose. Non-LLM sync tools (Dropbox, iCloud) are opt-in adapters, not default-allowed, so a sync run can't silently dump an unintended corpus into `raw/`.
- Every claim in `wiki/` cites a source page or `raw/` locator, at the **claim level**, not just a page-bottom bibliography.
- When new information conflicts with existing content, preserve both claims under a `Contradictions` section until resolved by the human.
- Prefer updating an existing page over creating a near-duplicate.
- Every write updates `wiki/index.md` and `wiki/log.md`.
- The agent's mechanical edits (`last_updated`, index entries, log entries, backlinks) are unsupervised; substantive content is not.
- A **touch budget** caps files modified per operation (e.g., ≤15), stricter in unattended mode, to limit cascade damage when the agent goes wrong.
- LLM-drafted concept pages stay at `status: draft` until the human promotes them.
- Read `CRITICAL_FACTS.md`, `hot.md`, `index.md`, and any folder `_context.md` before answering or editing.
- Only descend into `raw/` when the wiki is insufficient.


## 9. The unified workflow

One cycle, with Ahrens's intellectual operations on the left and the LLM's bookkeeping operations on the right. The cycle has **two human commit points**, with three further commit points available as the system matures (synthesis approval, supersession, forget).

```
1. Capture
   Human  → fleeting note in inbox/
   LLM    → (idle)

2. Triage (daily, ~10 min)         [HUMAN COMMIT POINT 1]
   Human  → decide for each fleeting note: trash, literature note, or concept draft
   LLM    → propose triage for unclear cases; never auto-promote

3. Ingest a source
   Human  → drop source into raw/, ask LLM to ingest
   LLM    → read source, propose N candidate takeaways (fixed N), propose pages to create or update
   Human  → edit takeaways in own words, accept / reject proposed pages, name them
   LLM    → write source page (paraphrased), draft concept pages (status: draft),
            scan + write mechanical backlinks, update index.md and log.md
            (serial queue, content-cached, idempotent)

4. Promote (review gate)            [HUMAN COMMIT POINT 2]
   Human  → read each draft concept page, rewrite in own voice, set status: active,
            write the substantive cross-references the LLM wouldn't make
   LLM    → (idle until promotion is committed; then re-scan backlinks)

5. Develop ideas (bottom-up, not on schedule)
   LLM    → synthesis-scan surfaces clusters meeting a critical-mass threshold
   Human  → confirm a cluster is real, ask LLM to propose a synthesis page
   LLM    → draft wiki/syntheses/<topic>.md citing the relevant concepts
   Human  → rewrite, accept or discard                        [optional COMMIT POINT 3]

6. Query
   Human  → ask a question
   LLM    → read CRITICAL_FACTS.md + hot.md + index.md + relevant pages first,
            answer from wiki, cite pages, exclude drafts + superseded by default,
            offer to save the answer back as wiki/questions/<topic>.md
   Human  → accept or discard the save

7. Maintain (health every session; lint every 10–15 ingests)
   LLM    → health: broken links, orphans, index drift, frontmatter validity
            lint: claims with no source, contradictions, stale pages, duplicates,
            recursion smell, oversize pages, overdue drafts; report only — fix nothing
   Human  → review the report; approve structural fixes; defer semantic fixes

8. Write
   Human  → copy notes onto the project desktop, bring into draft order,
            translate into prose, move cuts to xy-rest.md
   LLM    → propose related concepts, scan for missing citations
```

Everything between the commit points can be delegated to the LLM. Everything at a commit point cannot. The commit points are not safety theatre; they are the load-bearing cognitive operations (§14).

## 10. Ingest invariants

Six rules that hold across every ingest. Violating any of them lets the failure modes named in §15 back in.

**Discuss takeaways before writing**. The LLM produces a fixed number of candidate takeaways and pauses. The human edits, picks, and reframes before any page is created. This is what protects the wiki from compounding errors. Without it, the wiki becomes a "plausible but mis-prioritized summary of what the user actually cares about." Pick the number in the skill file rather than leaving it to the model.

**Curated batches, not bulk loads**. Ingest 10–20 sources from one domain, then run health and lint, then add the next batch. Bulk-loading large corpora before the discipline is in place produces low-signal noise *and* is expensive — cost is partly self-correcting because bulk-loading is both wasteful and low-quality. The clearest "worked for a real corpus" story scaled to 180+ sources only after starting with ten.

**Serialize ingest with content caching, retries, and idempotency**. SHA-256 caching, a serial queue, bounded retries (up to three), a guaranteed source-summary step. The model occasionally fails part-way through an ingest; without serialization and idempotency, partial state corrupts the wiki and a retry produces a *different* page than the first attempt, which breaks the content-cache assumption. Frontmatter and structural fields should be deterministic; prose may vary.

**Check the ingest with two independent verification packets before declaring it complete**. After the pages are written, run two checks that do not see each other's output: a *source-faithfulness* packet (does every claim on the new pages actually hold in the raw source at the cited locator?) and a *note-quality* packet (is each page atomic, self-explanatory, paraphrased, and reachable?). Keeping them independent — ideally as separate subagent runs — stops one packet's drift from rationalizing the other's. Zero verification re-opens ingest-error compounding; many packets only buy latency. Two is the load-bearing minimum, and it pairs with the yes/no audit-prompt style (§14): each packet reports "I assumed X because I saw Y — correct?" rather than open-ended self-justification.

**Save useful answers back into the wiki**. Substantial investigations become `wiki/questions/<topic>.md` or `wiki/syntheses/<topic>.md` pages that future queries reuse. The round-trip is the compounding mechanism. Without it, the wiki only ingests; it never harvests. Auto-saving every answer re-opens noise accumulation, so the rule is *offer*, not *commit*.

**Paraphrase always; never copy-paste**. Translation is the cognitive operation Ahrens (ch. 10) names as the difference between "having read" and "having understood." Direct quotes get quotation marks and a page locator; everything else is in the human's voice on the source page, and in re-voiced form on the concept page.

A note on the four cross-reference types Schmidt (2013, 173f; 2015) identifies in Luhmann's slip-box. Only types 1 (overview-of-a-topic) and 4 (plain note-to-note) survive into the digital version; 2 (physical-cluster overviews) and 3 (sequence links) compensate for paper limits and become automatic in Markdown. The digital wiki should make plain note-to-note links the dominant form (under each page's `Connections` heading) and use `wiki/syntheses/` for type 1 hub notes. Custom relation types (supports/contradicts/extends) are rejected: they re-open a lint-maintenance burden.

## 11. The promotion gate

The second human commit point. LLM-drafted concept pages stay at `status: draft` until the human re-voices them and flips the status to `active`. Draft pages are excluded from query results unless explicitly requested.

This is the place Ahrens's paraphrasing discipline enters the LLM workflow. Without a promotion gate, the wiki accumulates LLM-voice text — generic, "evolving landscape", "underscores the importance" prose that fails the AI-writing-tells filter (`ai-writing-tells.md`). With it, every claim that becomes part of the durable record has been read, rewritten, and judged by a human.

The promotion gate is also where the writing-as-thinking principle (Ahrens ch. 5) reappears. If the LLM is allowed to auto-promote — whether after a delay or on a confidence threshold — the human never elaborates, the slip-box becomes an LLM-content repository, and its compounding stops working (§16). The friction is intentional.

The dedicated `promote` skill makes re-voicing *part of the operation* rather than an easily-skipped manual step: the skill refuses to flip status without an edit. A practical detail: keep promotion small. Two or three drafts per session, not a queue of forty. This matches Ahrens's own pacing — Luhmann produced about six notes a day across the slip-box's working life, and three a day is Ahrens's stated reasonable goal (ch. 11). Track promotion latency: if drafts older than 14 days accumulate session-over-session, the discipline isn't working (§18 diagnostics).

## 12. Query and maintenance discipline

**Query**:

```text
query: <question>
- read CRITICAL_FACTS.md, hot.md, index.md, and any folder _context.md files first
- answer from wiki/ first
- only open raw/ if the wiki is insufficient
- cite the exact wiki pages or source pages used
- do not answer from model memory
- exclude status: draft and status: superseded pages by default
- if the answer creates a reusable synthesis, ask whether to save it
```

The contrast with vanilla "ask my notes" prompting: this forbids model-memory answers, requires citing wiki pages, and offers to save high-value answers back. That round-trip is the compounding mechanism (cf. §10). Aggressive read-orientation costs context every session but prevents the "agent answers from model memory" failure, which is among the top reasons implementations fail.

**Maintenance: cheap health vs. heavier lint vs. semantic audit**. Three passes, separated for cost reasons. Structural health is cheap and deterministic; semantic lint costs tokens; a project-level consistency/audit pass should run *after* lint clears page-level drift, so it isn't auditing pages against a schema that has itself drifted. Tying lint to ingest volume rather than a calendar interval matches the real failure rate — drift accumulates per ingest, not per day.

*Health* (cheap, deterministic, every session): empty files, index drift, log coverage, broken wikilinks, frontmatter validity.

*Lint* (semantic, every 10–15 ingests — the standard check set):

- orphan pages (and the reachability invariant, — demote orphans to draft until reattached)
- claims with no source
- source files not represented in wiki
- wiki pages with no raw-source references
- duplicate pages (prefer merge/update)
- stale pages past last-updated threshold (staleness; re-verification when a source changes)
- contradictions (first-class objects, below)
- pages exceeding size limits (400 / 800)
- concept pages that cite only other concept pages (recursion smell)
- draft-status pages overdue for promotion
- inbox items older than 24 h

**Contradictions are first-class objects**: keep both claims under a `Contradictions` section, indexed in `wiki/contradictions.md`, until the human resolves them. This is where paradoxes and oppositions get caught — and Ahrens (ch. 12; cf. Rothenberg 1971; 1996) treats those as the most productive observations the slip-box can surface. Auto-resolving contradictions silently removes the friction that makes thinking happen.

**Disconfirming evidence is a separate, second mechanism** (Ahrens ch. 10). Cross-source contradictions handle disagreements *between sources*. They do nothing for disagreements between a source and *the user's own working hypothesis* — and that is exactly where confirmation bias accumulates silently, because confirming evidence sticks and disconfirming evidence escapes (Darwin's golden rule, Ahrens ch. 10). The schema therefore includes a `disconfirming.md` index and a per-page `Disconfirming` section, plus an ingest prompt that asks "what evidence here cuts against what you currently believe?" The slip-box institutionalizes Darwin's rule by changing the incentive: any *relevant* note enriches the wiki regardless of which side it supports, so disconfirming evidence becomes attractive to capture rather than something to avoid. Omitting this mechanism re-opens confirmation-bias accumulation in the user's own thinking — a failure distinct from anything cross-source contradictions catch.

## 13. Provenance, retrieval, and document handling

Three operational concerns where the integration relies on best-practices rules but adds Ahrens-derived constraints.

**Claim-level provenance**. Every non-obvious factual claim in a wiki page must include: source file path, page/paragraph/timestamp/section/URL locator, confidence level (categorical low/medium/high, not a spurious numeric), date last checked. Three reasons: it stops the model inventing references, it gives a deterministic validator something to check, and at ingest time paragraph-level attribution makes "ingest errors compound" visible at the paragraph rather than only the page level. Pair claim-level provenance with `check_citations.py`, a script that opens each cited path and confirms it exists; the absence of such a validator is one of the most-cited reasons implementations fail. This is the structural enforcement of Ahrens's "literature note has explicit references" rule (ch. 6).

**Retrieval at scale**. Karpathy-scale (~100 articles / 400K words) works on Markdown plus a flat `index.md` provided lint runs consistently. Past that, the escalation order in increasing cost is: lexical search (BM25, `ripgrep`, `qmd`); sharded indexes; line-anchored retrieval (`PATH:LINE` plus context window); embeddings / vector search; graph traversal and reciprocal-rank fusion; entity resolution. The general rule: Markdown-first until the pain is specific and obvious, then add a narrow capability for that specific pain. Adding embeddings, OCR, a graph database, and routing on day one is the most-cited failure pattern. But the ladder is an option set you climb, not a refusal to ever climb — don't skip rungs, and don't refuse the next rung once duplication or navigation at scale is the genuine, demonstrated failure.

This rule is downstream of Ahrens's *simplicity is paramount* principle (ch. 6, §3 above). Complexity belongs at the content level, not in the retrieval layer.

**Index granularity**. `index.md` lists entry points, not every page — one or two starter notes per line of thought, matching Luhmann's actual practice (Ahrens ch. 1.3, 12). An exhaustive index grows linearly with page count and collapses into a directory. Entry-points-only requires hub notes to compensate: the index points at hubs (`wiki/syntheses/`), hubs point at concepts. Hub notes carry a soft cap of ~25 links (Luhmann's number, Ahrens ch. 12); lint warns past it, because a hub that exceeds it has drifted into a topic-page — the exact failure Ahrens spent ch. 6 warning against. The topic structure on a hub is "a hypothesis on a note," revisable by writing a better hub and updating the index.

**Document handling**. The PDF stays untouched in `raw/papers/` as the source of truth, but the agent works from a Markdown extraction beside it (`x.pdf` + `x.md`). Long books are split by chapter at ingest (one source page per chapter) to respect atomicity and size caps; prefer EPUB for clean text and chapter markers. OCR is optional, on-demand — a module, not a default. Keep figures local and describe them textually; extracted attachments are stem-prefixed to avoid Obsidian basename collisions. For web sources, paywalls and JavaScript-heavy pages don't yield to prompt instructions; add a dedicated fetcher or browser fallback when web ingest matters.

**AI-session transcripts**. Transcripts of research/coding sessions capture decisions and rejected approaches that would otherwise vanish, which is directly valuable for a research workflow. But their noise profile is different from papers — far more thinking-aloud per useful claim. Accept them into `raw/transcripts/` with a stricter triage: extract decisions and rejected approaches, then route through the *normal* promotion gate with an extra verification step. Rejecting transcripts outright loses working state; accepting them without discipline re-opens noise accumulation.


## 14. Where the human stays in the loop, and why

Ahrens's argument (ch. 5, 10, 11) is that *writing is the medium of thinking*, not its output. The act of paraphrasing forces elaboration; elaboration forces understanding; understanding is what compounds. If the LLM does the paraphrasing, the human does not elaborate, and the slip-box accumulates "plausible but mis-prioritized" summaries. The human-in-the-loop rule is therefore the load-bearing cognitive operation, not safety theatre.

What the LLM **cannot** do unsupervised (each maps to a commit point):

- **Write literature notes.** The LLM may *propose* candidate takeaways; the human writes the note in their own words.
- **Promote `draft` → `active`.** The LLM drafts; the human re-voices, then promotes.
- **Commit synthesis pages.** Cross-source claims are exactly where hallucinations sneak in.
- **Decide what an idea "is about" — titles, tags, and the substantive cross-references.** The wiki's wikilinks are how ideas connect; the title is the API. If the LLM names pages freely, related concepts fragment across "attention-mechanism.md", "self-attention.md", "attention-head.md". Tags are question-derived thinking tasks. And the most consequential links — the non-obvious "weak ties" that yield surprising patterns — are a thinking task the human does; the LLM writes only the mechanical, obvious backlinks. This is the one place to push *back* against pure "LLM does all linking": Luhmann placed every link by hand (Ahrens ch. 1.3), and "good cross-referencing is itself a thinking task" (ch. 12).
- **Decide that one source supersedes another, or what to throw away**.
- **Auto-resolve contradictions**.

What the LLM **can** do unsupervised (mechanical only):

- Maintain `index.md` and `log.md`.
- Scan and propose backlinks; write the mechanical ones.
- Run cheap structural health checks.
- Propose triage, pages to create, connections, synthesis topics, candidate clusters — *propose*, never commit.
- Format and lint (report only).
- Generate the weekly progress one-pager and other derived views from `log.md` (a derivative artefact, not a permanent note).

**Audit-prompt style**. When the agent reviews its own work, constrain it to yes/no audit prompts of the form "I assumed X because I saw Y. Correct?" rather than open-ended "explain your reasoning." Open-ended elicitation lets the agent rationalize its drift; the yes/no form forces it to expose the assumption before drift accumulates and lets the human reject quickly.

**Attention discipline** (Ahrens ch. 9). The slip-box only pays off when paired with attention discipline. Different tasks need different attention modes: drafting (floating, generative), editing (focused, critical), slip-box work (associative, playful), reading (whatever the text demands). Multitasking is rapid context-switching; switching itself drains the resource you'd need to handle two tasks. The LLM-augmented workflow respects this by separating operations cleanly — triage is its own block, ingest is its own block, query is its own block, promotion is its own block. Don't fold them together. Standardizing these organizational decisions is what frees decision capacity for the content.

The **Zeigarnik effect** (ch. 9) is the deeper reason the workflow works at all. Open tasks occupy short-term memory until they're either finished or written down — the brain doesn't distinguish between "done" and "credibly noted for later" (Zeigarnik 1927). Capturing fleeting notes into `inbox/`, drafting concept pages, and saving questions back as `wiki/questions/` all close the loop the brain would otherwise keep nagging about. The wiki is not just a record; it's also a way of paying attention.

## 15. Common mistakes (the union set)

Ahrens's three (ch. 6), with the LLM-wiki failure mode each maps onto and the decision that closes it.

**1. Treating every note as permanent.** *Ahrens version:* notebooks full of unprocessed thoughts; nothing builds critical mass. *LLM-wiki version:* every chat reply auto-saved as `wiki/questions/`; the slip-box is buried in low-value pages. *Fix:* explicit promotion gate (§11) and save-back-is-opt-in. The LLM offers to save; the human decides.

**2. Collecting only project-specific notes.** *Ahrens version:* must restart each project; insights that don't fit the current project are discarded. *LLM-wiki version:* `projects/<name>/` content gets ingested into `wiki/`; the slip-box is dominated by one project's vocabulary. *Fix:* keep `projects/` outside `wiki/` and exclude it from ingest paths; one slip-box, not one per project.

**3. Treating all notes as fleeting.** *Ahrens version:* slowly growing piles followed by clean-up cycles; even small amounts of unprocessed fleeting notes "induce the wish of starting from scratch." *LLM-wiki version:* `inbox/` never gets triaged; the LLM auto-summarizes everything into the wiki at session-start. *Fix:* 24-hour triage habit and a dedicated triage skill; the LLM *proposes* triage, never commits it.

LLM-specific failure modes the integration also fixes, each paired with the discipline that prevents it:

- **Hallucinations baked into the wiki.** Blocked by the literature-note discipline (paraphrase forces verification) and the promotion gate.
- **Wiki recursively cites itself as truth.** Blocked by the `sources/` vs. `concepts/` separation and the single-source-of-truth rule.
- **Ingest errors compound.** Blocked by "discuss takeaways before writing" plus `status: draft` plus paragraph-level attribution.
- **Topic-based drift.** Blocked by atomicity and bottom-up wikilink discipline.
- **Semantic gravity** — the page that warns against a misleading field, ignored by the agent. Not fixed by a better warning. Fix structurally: rename the field, add a validated query template, add a lint rule that rejects answers using it. Prose alone doesn't override schema.
- **Noise accumulation.** LLMs write too much; auto-generated notes look fine until someone reads them. Blocked by human-written literature notes and the promotion gate keeping LLM voice out of the active set.
- **Whole-file edit bottleneck.** Pages over ~1,000 lines force whole-file rewrites. Blocked by the 400/800-line caps and line-anchored retrieval before edits.
- **Maintenance ratchet.** As the wiki grows, the system spends more time maintaining itself, accumulating silent corruption. Blocked by validators, claim-level provenance, scope limits, and the touch budget.
- **Memory lifecycle missing.** Old or weak claims rot into permanent context. Blocked by `status: superseded`, periodic `last_updated` checks, and re-verification on source change.
- **Cascade damage from agent runaway.** Blocked by the per-operation touch budget.
- **Audit-trail loss on removal/overwrite.** Blocked by the quarantine/rollback policy and the forget-vs-supersede split.
- **Backlink drift as pages rename and move.** Blocked by a dedicated rebuild-backlinks operation, not per-ingest scanning alone.

## 16. What does *not* work in the integration

Combinations that look appealing but break one or both disciplines.

- **Letting the LLM auto-promote drafts** (after a delay, or on a confidence threshold). Breaks Ahrens's elaboration step — the human never paraphrases, so the wiki accumulates LLM-voice text. The promotion gate is *the* place the human's judgement enters the wiki; automating it removes the cognitive work that makes the slip-box compound.
- **Auto-archiving project notes into the slip-box at project-end.** Breaks Ahrens's project/permanent separation. Only the *promoted* concept pages produced during the project belong in the slip-box; the project folder stays archived separately. The legitimate path is the explicit route-to-slipbox operation, not bulk archival.
- **Using the LLM to "expand" a fleeting note into a permanent note.** Breaks the 24-hour rule and the elaboration discipline. An expanded fleeting note is just a longer fleeting note in LLM voice. Expansion is the human's job.
- **Letting the LLM choose page titles, tags, or substantive cross-references freely.** The title is the API; tags are question-derived thinking tasks; the non-obvious links are where the value is. The LLM may *propose* all three; the human commits.
- **Watch / continuous-ingest mode that bypasses takeaway approval.** Tempting at scale. A watch daemon is fine *only* in hybrid form — it eliminates the "remember to run ingest" step but keeps the takeaway-approval commit point. Without that gate it re-opens silent-ingest failures.
- **Adding embeddings or graph layers before the discipline is in place.** Premature optimization. Without the literature-note + promotion-gate discipline, more retrieval power just makes bad notes easier to surface.
- **A monolithic `CLAUDE.md` describing the entire integration.** Wastes context every session and accumulates internal contradictions. Split into skills with `CLAUDE.md` holding only global rules and pointers.
- **One slip-box per project.** Re-introduces Ahrens's mistake #2 in a new wrapper. One slip-box; `projects/` holds per-project material.
- **Top-down topic ontology.** Pre-decided categories collapse the slip-box back into a topic-tree filing system. Topics emerge from clusters; they're not designed up-front. Top-down topic declaration is allowed only as a flagged, lower-confidence exception, because forcing it re-opens the "writing about what you don't yet know" failure.
- **Custom relation types on links** (supports/contradicts/extends as first-class link kinds). Re-opens a lint-maintenance burden the slip-box doesn't need; one or two link kinds suffice.

## 17. Boundary conditions

The pattern is not universal. Best for: small-to-medium, slow-moving, human-curated research folders — personal vaults, book/fan wikis, evolving research topics, internal team KBs where curation is part of the job. Weaker for: large, fast-changing, high-stakes, multi-user, or enterprise knowledge bases. For high-churn material, regulatory-critical content (legal, medical), and very large corpora (10K+ documents), use classic RAG — or RAG plus a curated wiki layer on top of it.

The deeper way to read this: the integration depends on the human doing roughly six notes a day of cognitive work and ~40 minutes a week of triage + lint review. If the use case can't sustain that human workload — because the human isn't there, or there are too many humans, or the corpus is too large for the human to keep up — the discipline collapses and the §15 failure modes reassert themselves. Multi-user and enterprise scale additionally need permissions, redaction defaults, and source-tracking the published pattern does not solve; at organizational scale, default redaction-before-ingest becomes essential rather than optional, because the inspectable Markdown and Git history would otherwise expose private data.

Privacy/locality and the cost model are **deferred to the local environment**: local-only (private, capability-limited), cloud LLM (capable, raises data-handling concerns), or hybrid (the common compromise). The order-of-magnitude cost anchor in the record is ~$15 to process ~2000 bookmarks for a single user; cost discipline tracks ingest discipline, so the curated-batches rule is partly self-correcting on cost.

## 18. Habits and diagnostics

**Daily (~10 minutes, end of work day).** Triage `inbox/`. Each item: trash, promote to literature note, or convert to a concept draft. The 24-hour rule (Ahrens ch. 6): "fleeting notes are only useful if you review them within a day or so." Stale fleeting notes lose their meaning.

**Weekly (~30 minutes).** Review draft concept pages; promote what's ready, rewrite or discard the rest. Run lint; scan the report; approve structural fixes, defer semantic ones. Read `wiki/log.md` for the week. Notice patterns: which concepts recurred? Are clusters forming? This is how bottom-up topic emergence happens (Ahrens ch. 13) — and the `wiki-synthesis-scan` skill makes it a system property rather than relying on the human noticing: it surfaces candidate clusters meeting a critical-mass threshold and proposes synthesis topics for approval. The structured log shape (— dated `verb | subject` entries) is what lets the weekly digest summarize the week without re-reading prose.

**Spaced retrieval of old notes** (Ahrens ch. 11–12). This is the slip-box's central payoff and the easiest part of the method to leave unimplemented. The slip-box "is designed to present you with ideas you have already forgotten, allowing your brain to focus on thinking instead of remembering" (Ahrens ch. 12). That property only activates if old notes resurface. Two cheap mechanisms: at query time, the agent surfaces related old notes even when not directly cited; during the weekly habit, the agent surfaces one or two random concept pages for re-reading. Spaced retrieval at irregular intervals is what converts storage strength into retrieval strength (Bjork, in Ahrens ch. 11). Without it, the "wrote it once, never saw it again" failure defeats the compounding the whole system is for.

**Verbund / parallel projects** (Ahrens ch. 13). Run more than one manuscript at a time. Reading for one project produces by-product ideas relevant to others; the slip-box catches and routes them (via the route-to-slipbox operation). Luhmann's answer when stuck on one manuscript was to work on another — "I never encounter any mental blockages." Single-project focus re-opens the block-when-stuck failure.

**Reference-manager integration** (Ahrens ch. 3). Connect a reference manager (Zotero is Ahrens's named recommendation) rather than keeping bibliographic data only in source-page frontmatter. This is the digital form of Luhmann's *bibliographical* slip-box and it lets BibTeX/citation formats be reused in external writing without retyping — closing the duplicate-citation-maintenance failure.

**Reflect on direction, periodically.** The weekly review notices clusters forming (bottom-up emergence); a separate, slower-cadence `reflect` skill notices where the whole vault is *heading*. It writes a `compass.md` capturing the current direction, the blind spots, and one question worth sitting with — the system-level analogue of Ahrens's "let the slip-box show you what you have too many topics about" (ch. 7, 13). Run it on a schedule (monthly, or triggered by lint findings) rather than on-demand, because on-demand means it never runs and direction drifts silently. This is a derived artefact, not a permanent note, so the agent may draft it unsupervised; the human reads it and decides what, if anything, to act on.

**Make it a habit** (Ahrens ch. 14). Good intentions don't predict long-term behaviour; existing habits do. Install the smallest habit first: open the inbox at the start of every reading session and don't read without it. Once capture is automatic, the rest develops on its own. Habits replace habits — don't try to install the whole workflow at once.

**Diagnostic experiments** to localize problems before adding more layers. Run these against your current implementation when something feels off.

- *Duplicate detection.* Two `raw/` files with near-identical content. Expected: one canonical concept page plus a duplicate-candidate report. Symptom: two independent concept pages (prefer-update not enforced).
- *Staleness propagation.* A `raw/` file contradicting an earlier source ("standardized on SQLite" → "replaced SQLite with Postgres"). Expected: derived pages marked stale or `needs review`. Symptom: both claims kept silently (re-verification on source change not wired).
- *Whole-file edit bottleneck.* One ~1,500-line file; ask to update one paragraph near line 1,200. Compare tokens/correctness against a line-anchored retrieval call. Symptom: agent re-reads the whole file or breaks unrelated sections.
- *OCR necessity.* One clean digital PDF and one scanned PDF through the same pipeline. If the scanned one is unreliable, route only scanned sources through OCR — don't fix with prompt tweaks first.
- *Promotion latency.* Count draft pages older than 14 days. If the count grows session-over-session, the discipline isn't working — fix that before adding tools.
- *Pipeline rot.* Run the demo / golden-snapshot test after any schema change. If it breaks silently, the agent pipeline has rotted and ingests are corrupting the wiki without anyone noticing.


## 19. Quick-start checklist

If implementing from scratch.

1. Create the folder layout in §7.
2. Write a short `CLAUDE.md` (under 100 lines) naming the four note types, the immutability of `raw/`, the `inbox/` 24-hour rule, the page-size caps, the promotion gate, and the touch budget. Point it at the skill files; keep the page schemas in `SCHEMA.md`.
3. Set up the memory tiers: `MEMORY.md` (conventions), `CRITICAL_FACTS.md` (pinned facts), `hot.md` (per-session cache).
4. Pick one verified starter skill pack ([kfchou/wiki-skills](https://github.com/kfchou/wiki-skills) or [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)) and adapt: add `wiki-triage` and `wiki-promote`; modify `wiki-ingest` to require human-edited takeaways and to be serial/content-cached/idempotent; modify `wiki-query` to exclude `draft` and `superseded` by default.
5. Enforce `raw/` immutability at runtime (`chmod -w`) and add `check_citations.py` before trusting any provenance.
6. Migrate 10–20 sources from one domain into `raw/`. Don't bulk-load; don't enable first-run auto-ingest.
7. Run the daily and weekly habits for two weeks before adding any optional layer (embeddings, graph DB, OCR).
8. After two weeks, audit using the §18 diagnostics. If drafts aren't promoted or the inbox isn't triaged, the discipline isn't working — fix that before adding tools.
9. Once the discipline is sustained, climb the retrieval ladder (§13) only when a specific failure justifies it.

## 20. System-prompt skeleton

A short LLM-facing operating contract. Adapt and place at the wiki root as `CLAUDE.md`.

```text
You maintain a compiled knowledge wiki for the user.

Truth model
- raw/ is immutable source material and the source of truth.
- wiki/ is your workspace. You may create, update, and cross-link pages there.
- inbox/ is fleeting notes pre-decision; never auto-ingest.
- projects/ is project-specific scaffolding; never ingest into wiki/.

Non-negotiable rules
- Never modify raw/ except explicit user-directed deletion workflows.
- Every writing operation updates wiki/index.md and wiki/log.md.
- Every claim in wiki/ must point to one or more source pages or raw source files,
  at the claim level — not just a page-bottom bibliography.
- When new information conflicts with existing content, preserve both claims under
  a Contradictions section until resolved by the user.
- Capture evidence that cuts against the user's own hypotheses in the page's
  Disconfirming section and disconfirming.md.
- Prefer updating an existing page over creating a near-duplicate.
- LLM-drafted concept pages stay at status: draft until the user promotes them.
- Page size: aim for under 400 lines, never over 800. Split atomically when needed.
- Touch at most ~15 files per operation; stricter when running unattended.
- Tags and substantive cross-references are the user's calls; you may propose, not commit.

Required orientation before any work
- Read CRITICAL_FACTS.md and hot.md if they exist.
- Read wiki/index.md and any folder _context.md files.
- Only descend into raw/ when wiki/ is insufficient.

Core operations (each lives in its own skill file)
- triage: walk inbox/, propose per item: trash | promote-to-source | promote-to-concept-draft.
  Never auto-commit.
- ingest <path>: read source, propose a fixed number of candidate takeaways, pause for user,
  then write the source page (paraphrased), draft concept pages (status: draft), scan and write
  mechanical backlinks, update index and log. Serial queue, content-cached, idempotent. Finish
  with two independent verification packets (source-faithfulness + note-quality).
- promote <page>: human-driven; user re-voices the draft; status flips to active. Refuse to flip
  without an edit.
- query: answer from the wiki first, then raw only if needed; cite exact pages; exclude draft and
  superseded by default; offer to save reusable answers back.
- synthesis-scan: surface clusters meeting a critical-mass threshold; propose synthesis topics.
  Propose only.
- reflect: periodically write compass.md (direction, blind spots, one open question). A derived
  artefact; draft freely, the user acts on it.
- health: cheap structural checks every session.
- lint: semantic checks every 10–15 ingests; report only, fix nothing without approval.
- supersede / forget: replace-with-prior-view / remove-with-quarantine. User-directed only.

What you cannot do unsupervised
- Promote a draft to active.
- Write a literature note, or add a substantive citation or non-obvious cross-reference.
- Decide that one source supersedes another, or what to throw away.
- Decide what an idea "is about" (title, tags, weak-tie links).
- Auto-resolve contradictions.
- Audit yourself with open-ended prompts; use yes/no ("I assumed X because I saw Y. Correct?").
```

## 21. Why this works (the Ahrens argument re-applied)

Ahrens's central claim (ch. 1, 3, 5) is that the slip-box works because it externalizes the bookkeeping — "the slip-box provides an external scaffold to think in and helps with those tasks our brains are not very good at, most of all objective storage of information" (Ahrens ch. 3). The brain is freed to do what only the brain can do: judge relevance, see connections, articulate ideas. Luhmann's epigraph: "One cannot think without writing" (Luhmann 1992). The lineage runs back to Bush's memex (1945): the associative trails were always the point; the unsolved problem was who maintains them.

The LLM doesn't change that argument. It makes a stronger version possible. The LLM is even better than a paper Zettelkasten at the bookkeeping Ahrens names — proposing backlinks, scanning for contradictions, regenerating an index, finding orphans, surfacing stale claims, and now resurfacing forgotten notes on a schedule. The human is freed even further to do the cognitive work. But only if the human keeps doing it; the moment the LLM is allowed to write the permanent note, the slip-box stops being a thinking tool and becomes an LLM-content repository. That is the consensus the independent practitioners reach too (rohitg00 2026): the write gate is quality control, not backwardness.

The integration in one line: **let the LLM do the bookkeeping Ahrens describes, and protect the cognitive operations Ahrens insists on**.

## 22. What this guide leaves to you

Everything above is prescriptive because it affects the discipline: drop it and a named failure mode returns. The choices below are genuinely open — they change how the system feels to use, not whether it works — so pick them to suit your tools and threat model rather than looking for a right answer.

**Presentation and naming.** Folder ordering (plain `raw/` and `wiki/` versus prefix-numbered `0-raw/` and `1-wiki/`), whether page sections are callouts or plain headings, and your filename and wikilink conventions. All are cosmetic with respect to the discipline; settle each once and apply it uniformly, because inconsistency here is what makes an agent's mechanical edits unreliable.

**Tooling.** Your editor, your agent runner, which model handles which operation, any MCP surface you expose, and whether the wiki renders or publishes anywhere. The one constraint the discipline imposes: whatever you choose has to let a human read and edit the notes directly. A pipeline that only an agent can write to loses the promotion gate.

**Privacy, locality, and cost.** Local-only (private, capability-limited), a cloud model (capable, raises data-handling questions), or the hybrid most people land on. The order-of-magnitude anchor in the public record is roughly $15 to process ~2,000 bookmarks for a single user. Cost tracks ingest discipline, so the curated-batches rule is partly self-correcting: bulk-loading is both the expensive path and the low-quality one.

**Things that scale in.** A single-user personal vault is the default assumption throughout. Redaction-before-ingest, permissions, and multi-user source-tracking become necessary at organizational scale and are not solved by the published pattern — see §17 before taking this past one person.

Two further choices are deliberately left open because they depend on your repository setup rather than the method: where archived material lives, and whether the vault is one repository or several.

## 23. References

**Ahrens** (page references are to the e-book edition of Ahrens 2017; faithful comprehensive summary at `smart-notes-summary.md`):

- Ahrens, S. (2017). *How to Take Smart Notes: One Simple Technique to Boost Writing, Learning and Thinking — for Students, Academics and Nonfiction Book Writers.* takesmartnotes.com.
  - Ch. 1, *Everything You Need to Know* — workflow > willpower; Luhmann's two slip-boxes; the small entry-point index; numeric addressing; the four cross-reference types.
  - Ch. 3, *Everything You Need to Have* — the four-tool toolbox; Zotero as reference manager; "any program that allows setting links and tagging (like Evernote or a Wiki)."
  - Ch. 5, *Writing Is the Only Thing That Matters* — writing is the medium of research, not its output.
  - Ch. 6, *Simplicity Is Paramount* — the three note-type distinction; the slip-box as "shipping container"; bottom-up topic emergence; the three typical mistakes; the project desktop.
  - Ch. 7, *Nobody Ever Starts From Scratch* — the hermeneutic circle; "find a topic" → "too many topics."
  - Ch. 8, *Let the Work Carry You Forward* — exergonic vs. endergonic workflows; intrinsic motivation.
  - Ch. 9, *Separate and Interlocking Tasks* — attention as a limited resource; multitasking; Zeigarnik effect; reduce decision count / standardize the environment (Baumeister et al. 1998).
  - Ch. 10, *Read for Understanding* — read with a pen; Darwin's golden rule (disconfirming evidence); the Feynman test.
  - Ch. 11, *Take Smart Notes* — make a career one note at a time; think outside the brain; storage vs. retrieval strength (Bjork); reachability from the index.
  - Ch. 12, *Develop Ideas* — the four cross-reference types; index like a writer; the ~25-link overview note; the slip-box as a creativity machine; "presents you with ideas you have already forgotten."
  - Ch. 13, *Share Your Insight* — slip-box-storming; bottom-up; the desktop function; the cut-prose graveyard; Verbund / parallel projects.
  - Ch. 14, *Make It a Habit* — habits replace habits; capture-first; Whitehead's epigraph.
  - Epigraph: Luhmann (1992): "One cannot think without writing"; Levy (2011, p. 270): "the mind is reliant upon external scaffolding."

**Karpathy** (verified primary URLs):

- Karpathy, A. *LLM Wiki* gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f.
- Karpathy, A. on X: https://x.com/karpathy/status/2039805659525644595.

**External sources consulted for this revision:**

- Bush, V. (1945). "As We May Think." *The Atlantic Monthly*, 176(1), 641–649. The memex — a personal store of books and records, linked by user-built associative trails that can be recalled and shared. The intellectual-history anchor for §1 and §21: the associative trail was always the goal; the unsolved problem was who maintains it. (Corroborated via Wikipedia "Memex" and multiple secondary sources; AI Builder Club's LLM-Wiki write-up makes the same memex-to-Karpathy connection.)
- rohitg00 (2026). "LLM Wiki v2 — extending Karpathy's LLM Wiki pattern with lessons from building agentmemory." GitHub gist: https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2. Independent practitioner corroboration of the human-as-write-gate rule, supersession over decay, manual-before-automated, and the memory-lifecycle framing. Cited in §2 and §21.
- Secondary explainers of the Karpathy pattern (consulted to confirm the public record, not cited for specific claims): MindStudio (the "optimized for model reading, not human browsing" framing); Data Science Dojo, Level Up Coding, Starmorph, AI Builder Club tutorials. These corroborate but do not extend the synthesis already in `llm-wiki-best-practices.md` §14.

**Companion files:**

- `llm-wiki-best-practices.md` (**BP §N**) — public-record synthesis of the Karpathy pattern (verified repos, community failure modes, retrieval escalation, templates). Source for the ingest invariants (§10), provenance/retrieval/documents (§13), failure modes (§15), boundaries (§17), and the system prompt (§20).
- `smart-notes-summary.md` (**Ahrens ch. N**) — comprehensive single-page distillation of Ahrens 2017. Source for the four principles (§3), note-type definitions and cross-reference types (§6, §10), translation discipline (§10), disconfirming evidence and attention/Zeigarnik (§12, §14), the three typical mistakes (§15), and the habit/Verbund/spaced-retrieval material (§18).
- `CLAUDE.md` — encodes the live wiki's existing conventions (atomic permanent notes, paraphrased literature notes, anthropic-skills toolchain). This document is the explicit walkthrough of why those conventions are the right ones and how the LLM fits into them.
