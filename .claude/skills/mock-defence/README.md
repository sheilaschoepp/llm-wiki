# mock-defence

A guide to running a mock candidacy or thesis defence with this skill. `mock-defence` reads the document you are defending, role-plays a committee of examiners, and grills you on it one question at a time so the real exam holds no surprises. It is prep-only: it writes session reports to `.claude/skills/mock-defence/outputs/` and never touches the wiki.

This file is the how-to-use guide. The full operational spec the agent follows lives in `SKILL.md`.

**New here, or just copied this folder?** The skill ships with no committee data. Do the one-time setup first — see **Adopting this skill** at the bottom (point it at your document, add your examiners) — then the how-to below works.

## What you get

- A live, adversarial oral-exam rehearsal, grounded in the actual document and — for your real committee — your actual examiners.
- After each session: a **report** (the questions asked, where answers held or wobbled, the weak spots, a room-level verdict, and what to tighten) and, for a live drill, a verbatim **transcript**. Both land in `.claude/skills/mock-defence/outputs/`.

## Starting a session

Just ask, in plain language — for example:

- "Run a mock defence of my proposal."
- "Grill me on my candidacy like my real committee would."
- "Give me a written question bank for my defence."

By default it defends the document named in `references/defaults.md` — a small user-owned file that is yours to edit whenever the defended document changes. To defend something else (a thesis, a paper talk), just name the file.

It then walks you through a few choices, one at a time:

1. **Which committee** convenes (see below).
2. **Which mode** — live drill or written question bank.
3. **Who is at the table** — all members, or a subset.
4. **Detail level** — how picky the questions get.
5. If you have run a session on this document before, **resume or start fresh**.

## Choosing a committee

A committee is a folder of examiner profiles. Pick the one that fits what you want to rehearse.

**Real people**

- **real-committee** — your actual examiners. Best for genuine exam prep; the recommended default. Ships with no members (only a `_TEMPLATE`) — add your examiners under `profiles/` first (see "Creating a real committee profile" below).
- Any panel you assemble yourself — for example, field luminaries whose work your proposal builds on. Add a folder under `references/committees/` and it appears in the menu.

**Fictional roles**

- **proxy-panel** — generic exam seats (chair, near-field expert, broader-field examiner, recent passer). Exam-format realism without modelling your specific examiners.
- **cognitive-council** — five reasoning lenses (contrarian, first-principles, and so on) that stress-test your logic rather than your field.
- **specialist-council** — a peer-review panel (methods, statistics, reproducibility, novelty, and more) that reviews the proposal the way a program committee reviews a paper.

On your real committee, supervisors are played as backstops — they defend the framing rather than attack it — while arms-length examiners press hardest. Fictional panels share the model's blind spots, so they are weaker than a real near-field expert on field-specific critique: use them to harden your reasoning and contribution statement, not as a substitute for technical depth.

## Modes

- **Interactive drill (default)** — a live, multi-turn oral exam. One question at a time; you answer; the examiner pushes back with follow-ups before giving a one-line verdict. By default it runs as a pure-realism mock. Turn on coaching with `coach on` for a workshop-style run: then, when an answer does not hold, a short out-of-role `Coach:` note says how to rebuild it and the examiner immediately re-asks that seam so you deploy the fix under pressure, not just recognize it later (`coach off` returns to pure realism).
- **Question bank** — no live drill; a written set of likely questions per member, each with the strongest answer, the seam a committee would probe, and a locator into your proposal. Good for solo review between drills.
- **Cross-session consolidation** — no drill; folds all your past sessions for one event into a single standing "where I stand" ledger. Ask to consolidate or summarize where you stand across sessions.

## Detail level

Set at the start, switchable mid-drill:

- **high-level** — substantive design, contribution, framing, evaluation soundness.
- **nit-pick** — the granular pass: exact wording, notation, citation and figure/table details, small inconsistencies.
- **mixed** (default) — both, and the closest match to a real exam.

## Control words (during a live drill)

```text
pause                          step out of role to debrief (model answers shared here)
skip                           move on; the skipped question is logged as untested
switch to NAME                 hand the questioning to another member
harder / easier                adjust difficulty within the current register
big picture / nitpick / mixed  set the detail level on the fly
coach off / coach on           turn coaching (Coach: note + immediate re-ask) off or on; off by default
stop / done                    end the session and write the report + transcript
```

## Resuming across sessions

When you have defended the same document before, the skill reads your earlier reports, works out which weak spots and untested seams were left open, and offers to **resume and retarget** them — re-testing each against your current document — rather than start cold. A **fresh full drill** is always available; pick it after a big rewrite or when you want breadth over a focused re-test. Reports are matched by event.

## What you get out, and where

Everything lands in `.claude/skills/mock-defence/outputs/`:

- `mock-defence-YYYY-MM-DD-HHMM-{event}.md` — the session report (or the question bank).
- `mock-defence-YYYY-MM-DD-HHMM-{event}-transcript.md` — the verbatim drill transcript.
- `mock-defence-{event}-ledger.md` — the standing cross-session ledger, refreshed in place.

A new report and transcript are written every run; nothing is overwritten. (`{event}` is a short slug for the occasion — `candidacy`, a thesis slug, and so on — which also names the report file.)

## Maintaining committees

Each committee is a folder under `references/committees/`, with a short `committee.md` manifest (one line per field) and one profile per member under `profiles/`. To add a committee, add a folder — the selection menu is built by scanning. Rules worth knowing:

- **Real-people profiles** hold neutral public facts only (role, research focus, representative work); the examiner's lens and questioning style live in an event prep file (for example `candidacy-prep.md`). A profile's usual shape: identity, research focus, key themes, selected works, sources. These profiles are yours to maintain — the skill will not rewrite them unasked.
- **Publication records.** Beside any real-person profile you can drop a same-stem BibTeX file — for example `jane-khan.bib` next to `jane-khan.md` — holding that member's publications (say, everything since 2020, exported from a reference manager or Google Scholar). The drill loads it with the profile and grounds questions that invoke the member's own work in it, instead of trusting model memory. A stem that differs slightly from the profile's (a middle initial, say) still pairs to the nearest-named member.
- **Questions actually asked.** After a real encounter with your committee, record what each member actually asked in an `asked-questions.md` inside the committee folder — one dated section per encounter, from your own notes. When present, it outranks every prediction for calibrating future drills.
- **Fictional-role profiles** define the role itself — its job, what it probes, its reasoning method — since nothing is being inferred about a real person.

## Creating a real committee profile

A real-people profile holds **neutral public facts only** — role, research focus, key themes, representative work, and sources. It is *not* your read of how the examiner will grill you; that inference belongs in the event prep file (`<event>-prep.md`), never in the profile. The drill combines the two: the profile fixes each member's lens, the prep file supplies their questioning style.

Build one in three steps.

**1. Gather the public record.** For each member, collect:

- Their **faculty / lab page** and **personal website** — title, affiliations, research statement.
- Their **Google Scholar** (or **Semantic Scholar**) profile — recent and most-cited papers.
- A **BibTeX export** of their recent publications (say, everything since 2020), from Google Scholar, Semantic Scholar, or a reference manager (Zotero, Mendeley). Save it beside the profile as a **same-stem `.bib`** — `jane-khan.bib` next to `jane-khan.md` — and the drill loads it to ground any question about their own work in a real citation instead of model memory. Copy `profiles/_TEMPLATE.bib` for the expected shape.
- Optionally **DBLP** for a clean venue/year list.

**2. Write the summary.** Distil the material into the profile shape (Identity, Research focus, Key themes, Selected recent works, Sources — see the worked example below, or copy `profiles/_TEMPLATE.md`). Keep it factual: what they work on, not how they examine. Never invent a paper, venue, or affiliation — if a field is unknown, leave it blank.

**3. (Optional) Let the model draft it, then verify.** Paste the gathered material into the prompt below for a first draft, then check every line against the sources. The profile is ground truth for the drill, so a wrong venue or mis-attributed paper matters.

### A prompt to draft a profile

```text
You are helping me build a neutral committee-member profile for a mock-defence
skill. I will give you public material about one academic. Produce a Markdown
profile using EXACTLY these sections, in this order:

# <Full Name>
> Profile — <role>, <institution>. Neutral ground-truth facts only. Sources at bottom.
## Identity            (Title, Affiliations, Office, Email, Education, public handles)
## Research focus      (1–2 short paragraphs: what they actually work on; their central question)
## Key themes          (bulleted: recurring topics, methods, named systems, benchmarks)
## Selected recent works (2020–)
                       (bulleted: Author(s) (year). Title. Venue. — one line on what it did)
## Sources             (the links I give you)

Rules:
- Neutral facts ONLY. Do not infer how they will examine, what they will probe,
  or their questioning style — that goes in a separate prep file, not here.
- Use ONLY the material I provide. If a field is unknown, leave it blank rather
  than guessing. Never invent a paper, title, venue, affiliation, or date.
- Obfuscate the email (e.g. "first.last at institution dot edu").
- Canadian spelling.

Material:
<paste the faculty page, Scholar list, .bib entries, personal site, etc.>
```

### Worked example (fictional)

```markdown
# Jane A. Khan

> Profile — Associate Professor, School of Computing, Example University. Sources at bottom.

## Identity

- **Title**: Associate Professor, School of Computing, Example University
- **Affiliations**: Director, Data Systems Lab; Example Institute Data Fellow
- **Office**: Turing Hall 4-12, Example University
- **Email**: jane.khan at example dot edu
- **Education**: PhD (Computer Science) Example Tech, 2011; BSc (Computer Science) Example State, 2005

## Research focus

Khan studies how database systems execute queries efficiently and stay correct under concurrency — how a query optimizer chooses an execution plan, and how a storage engine keeps transactions consistent as data and load scale up. Her recent line asks whether an optimizer can adapt its plans to shifting workloads without hand-tuning.

## Key themes

- Cost-based query optimization and adaptive plan selection.
- Concurrency control and transaction isolation under high contention.
- Storage engines, indexing, and their effect on read/write trade-offs.
- Benchmarks: TPC-C, TPC-H, and workload-replay suites.

## Selected recent works (2020–)

- **Khan & Osei (2024). Adaptive Plan Selection for Shifting Workloads.** SIGMOD 2024. Re-optimizes query plans online as the workload distribution drifts.
- **Khan, Adeyemi, & Roy (2022). Low-Contention Transaction Scheduling.** VLDB 2022. Reduces abort rates under high contention with a conflict-aware scheduler.
- **Khan (2021). Query Optimization in Modern Database Systems: A Survey.** ACM Computing Surveys 2021. Taxonomy of cost-based and adaptive optimization methods.

## Sources

- Personal website: <https://example.edu/~jkhan>
- Google Scholar: <https://scholar.google.com/citations?user=EXAMPLE>
- Lab page: <https://datasystems.example.edu>
```

Everything in the example is invented for illustration — swap in your examiner's real, verified facts.

And its paired publication record, saved as `jane-khan.bib` beside `jane-khan.md` (copy `profiles/_TEMPLATE.bib` to start):

```bibtex
@inproceedings{khan2024adaptive,
  author    = {Khan, Jane A. and Osei, Kwame},
  title     = {Adaptive Plan Selection for Shifting Workloads},
  booktitle = {ACM SIGMOD International Conference on Management of Data (SIGMOD)},
  year      = {2024},
  abstract  = {Cost-based query optimizers pick a plan once, from statistics
               that go stale as the workload drifts, so a plan that was optimal
               at deploy time can degrade badly. We re-optimize online: a
               lightweight monitor watches operator-level costs and triggers
               targeted re-planning only for the subplans whose estimates have
               drifted. On workload-replay benchmarks the approach recovers
               most of the lost performance while keeping re-optimization
               overhead small.},
}

@article{khan2021survey,
  author   = {Khan, Jane A.},
  title    = {Query Optimization in Modern Database Systems: A Survey},
  journal  = {ACM Computing Surveys (CSUR)},
  year     = {2021},
  abstract = {We survey query optimization in modern database systems and
              organize the field along three axes: the cost model (heuristic
              versus statistics-driven), the search strategy over the plan
              space, and whether the optimizer adapts to runtime feedback. We
              map methods onto this taxonomy, compare their evaluation
              protocols, and identify open problems in adaptivity and in
              estimating costs under skewed data.},
}
```

Only `title` / `booktitle` / `journal` / `year` are load-bearing for the drill; a fuller export (authors, pages, volume, `abstract`) is fine — an `abstract`, where the export has one, gives the drill more to ground a member's own-work questions in. See `profiles/_TEMPLATE.bib` for the full three-entry template.

## Adopting this skill

The machinery is generic; the committee data is not. If you are setting this skill up for yourself (or received the folder from someone else), the quickest path is the guided wizard:

```text
python .claude/skills/mock-defence/scripts/setup.py   # from the repository root
```

**Have to hand before you run it** (or skip any and fill it in later): your document's path; your committee roster — supervisor(s), co-supervisor, and arm's-length examiners; each member's public info (faculty page, Google Scholar, research focus, a few key papers); and, optionally, a BibTeX export per member. The wizard writes `references/defaults.md`, scaffolds your committee profiles under `references/committees/real-committee/profiles/`, and can stub an event prep file — asking before it overwrites anything, and re-runnable to add members later. It only needs Python 3 (standard library, no dependencies). To set things up by hand instead, create or replace these user-owned files:

- `references/defaults.md` — point the skill at the document you're defending. Set `document:` to your candidacy proposal (or thesis) path, `event:` to a short slug that also names the report files (e.g. `candidacy`), and the optional `timezone:` to pin report timestamps across machines. This becomes the default document every run; name any other file at the start to override it for that session.
- `references/committees/real-committee/` — your own examiners: one profile per member under `profiles/` (see "Creating a real committee profile" above), plus optionally a same-stem `.bib` per member, an `<event>-prep.md`, and an `asked-questions.md` once you have a real encounter to record.
- Any extra panels you want (for example, your field's luminaries) — one folder each.
- `mock-defence-memory.md` — the correction journal; it ships header-only and accumulates user-confirmed corrections as you use the skill.

Everything else — the fictional panels (`proxy-panel`, `cognitive-council`, `specialist-council`) and the reference files (`mock-committee-best-practices.md`, `llm-council-panel.md`, `real-exam-calibration.md`, `resume.md`, `report-format.md`) — is generic and works as shipped, with one caveat: `real-exam-calibration.md`'s question archetypes were distilled from an empirical-science exam — the four-register structure transfers, but adapt the archetypes to your field (its intro says how).

**Passing the folder on?** The generic machinery is safe to share, but your *data* is not — before handing the folder to someone else, clear the files that hold personal content: `references/committees/real-committee/` (and any luminaries panels you added), `references/defaults.md`, everything under `outputs/`, and `mock-defence-memory.md`. The skill ships with those empty or placeholder for exactly this reason.

## References

- The cognitive and specialist councils adapt Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council) — several models answer the same question, review one another's answers anonymously, and a chairman synthesizes — into role-played seats within one model. Role sets and failure-mode guardrails are in `references/llm-council-panel.md`.
- The proxy panel and session protocol follow `references/mock-committee-best-practices.md`, a digest of university mock-exam guidance, a peer-reviewed review article, and first-hand graduate-student accounts; its full source list (16 references) is inside the file.
- `references/real-exam-calibration.md` distils the question registers of one real candidacy exam (names abstracted; the empirical-science exam shape remains — adapt the archetypes to your field).
