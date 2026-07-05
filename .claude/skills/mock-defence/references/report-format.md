# Report and question-bank format

The `mock-defence` skill writes one file per run to `.claude/skills/mock-defence/outputs/mock-defence-YYYY-MM-DD-HHMM-{event}.md`. This is the skeleton for both modes. Load it at Step 7. An interactive drill additionally writes a companion verbatim transcript — see *Transcript* below.

## Contents

- Interactive-Drill Report
- Question-Bank Report
- Consolidation Report (the Standing Ledger)
- Transcript

**Privacy rule (all artefacts).** The report and the transcript attribute questions by member name, but do not transcribe profile content — a member's probing habits, stylistic tics, or personal characterizations — into the file. The same exclusion covers the prep file's inferred stances and a captured record's per-member exam behaviour: a question drawn from those is voiced as a neutral probe on its topic — never as "last time you asked X" or as the member's asserted position — so the verbatim record stays clean by construction. They record the questions asked and the candidate's answers, not the real examiners' personalities. The transcript is the verbatim record of what was actually said in the session (the questions as voiced, the candidate's answers, the counters, the in-role verdicts, and any out-of-role `Coach:`/`pause` turns); it is not a place to paste profile descriptions or invent member characterizations beyond what the drill produced. (The committee profiles are the user's private prep material; the report and transcript are more durable artefacts.) If the user wants fuller per-member notes, they keep a private copy outside the repo.

**Detail-level field (both modes).** The session runs at a chosen detail level — `high-level` (substantive design, contribution, framing, and evaluation soundness; skip wording, notation, and citation-format quibbles), `nit-pick` (the granular pass: exact wording, notation, citation and figure/table details, small inconsistencies), or `mixed` (both, the closest match to a real exam and the default). Record it in the frontmatter `detail_level:` field and name it in Scope so a reader knows which register the questions were pitched at.

**Resume fields (both modes).** When the session resumed from earlier reports on the same event (see `references/resume.md`), the report records the continuity so the chain stays traceable: a `resumes:` frontmatter list of the prior report paths it retargeted, a Scope mention of how many open seams carried forward, and — drill mode — a `## Carried-forward weak spots (retargeted)` section recording each prior seam's outcome (closed / improved / still open). The `## Weak spots` section then holds this session's still-open set (carried seams that did not close, plus newly surfaced ones) — which is exactly what the next session's scan reads. On a fresh first session with nothing to resume, omit the `resumes:` field and the carried-forward section entirely.

A third frontmatter value, `mode: synthesis`, marks the cross-session consolidation — the standing weak-spot ledger that folds every session for an event into one current view. The consolidation mode writes and refreshes it (the fold-and-recompute logic lives in `references/resume.md`; the skeleton is below), and the resume scan prefers it as its spine when one exists. The per-session drill and question-bank reports are immutable — a new file per run, never overwritten — but the ledger is the one living artefact: it is refreshed in place after each later run, because a seam that was a weakness may since have been fixed and new weaknesses surface each session, so its open set is recomputed rather than frozen.

## Interactive-Drill Report

```markdown
---
type: mock-defence
event: {event}
date: {YYYY-MM-DD}
document: "{path to the document defended}"
mode: drill
detail_level: {high-level | nit-pick | mixed}
resumes: {list of prior report paths this session retargeted; omit on a fresh first session}
transcript: mock-defence-YYYY-MM-DD-HHMM-{event}-transcript.md
---

# Mock defence — {event} — {YYYY-MM-DD}

Scope: {members at the table, focus area, detail level (high-level / nit-pick / mixed), document pages actually read, prior sessions resumed and how many open seams were retargeted (if any), how far the drill got}

## Questions and how they held

- {member}: {question}
  - Answer: {one-line summary of what the candidate said}
  - Verdict: holds / wobbles / does not satisfy the room — {why, in one line}
  - How to strengthen: {the Coach: note for this answer — the answer-scaffold stage it skipped (pause / clarify / answer / support / qualify / close) and one concrete way to rebuild it, naming the stage rather than reciting the content; omit this line when the answer held or coaching was off}
  - Coached re-attempt: {how the candidate's immediate rebuild landed — stronger, or still shaky with the fix in hand; a deliberate-practice signal, not the seam closed; omit when the answer held or coaching was off}

## Carried-forward weak spots (retargeted)

- {prior seam}: closed / improved / still open — {one line on what changed since last session, naming the prior report it came from}

{Omit this whole section on a fresh run with nothing to resume. List one bullet per carried-forward seam; a seam still open after more than one session is flagged as a standing liability.}

## Weak spots

- {the answers that wobbled or were skipped, and the seam each leaves open}

## Coverage

- Document sections / design pressure points pressed: {list}; not tested this session: {list}.
- Registers exercised: {which of fundamentals / uncited-literature / breadth / logistics fired}; skipped: {list}.
- Members drilled: {list}; at the table but not reached, or dropped from a subset: {list — untested real-exam surface, not a clean bill}.

{This section exists so a partial or early-stopped drill cannot read as complete. The Room verdict below is scoped to what is listed here as tested.}

## Room verdict

{not-yet / pass-with-conditions / pass, derived from the logged weak spots — an open load-bearing seam caps the verdict below pass, and one decisive unresolved objection outweighs several holds (do not average to a comfortable middle). Before landing, state the case for the next-harsher verdict — what would have to be true for this to be not-yet (or, at pass-with-conditions, a fail) — so the call is argued, not defaulted to the lenient end. Calibrate to the event (a candidacy probes whether the plan is sound; a thesis whether the work is done) and to the real room's intensity, flagging when the mock likely ran easier or harsher than the real committee will. Where a weakness cut across many answers rather than one, name it as a capacity (command of field, research judgement, answer structure, intellectual resilience, narrative and significance; presentation and logistics is not assessed in a typed drill). Close with a confidence flag on the prediction — highest for a real committee grounded in `asked-questions.md`, lowest for a fictional panel — and the one or two things that decide it. Scope the verdict to what was actually tested (see Coverage): a partial or subset drill is a pass on the tested ground, never a whole-room pass.}

## To read / tighten before the real thing

- {concrete next actions}
```

## Question-Bank Report

```markdown
---
type: mock-defence
event: {event}
date: {YYYY-MM-DD}
document: "{path to the document defended}"
mode: question-bank
detail_level: {high-level | nit-pick | mixed}
resumes: {list of prior report paths whose open seams this bank leads with; omit on a fresh first session}
---

# Likely defence questions — {event} — {YYYY-MM-DD}

{When resuming, lead the bank with the open seams carried forward from the prior reports (see `references/resume.md`) before the fresh questions.}

## {member}

- Question: {the question, in this member's lens}
  - Strongest answer: {the answer that would satisfy the room}
  - Seam: {where a committee would press further}
  - Anchor: {proposal locator — section/page — and, where the question invokes the member's own work, the profile line it rests on}
```

## Consolidation Report (the Standing Ledger)

One living file per event at `.claude/skills/mock-defence/outputs/mock-defence-{event}-ledger.md` — a stable name, no timestamp. The consolidation mode folds every session report for the event into one current view of where the candidate stands, then refreshes it in place after each later run (git preserves the prior version once committed). It is not a session record, so the new-file-per-run rule does not apply: there is one ledger per event, kept current. Each refresh recomputes seam status from the latest evidence — a seam that has since been fixed moves to Resolved, surviving seams keep an incremented survival count, and seams new to the latest session surface into Open — because a weakness does not stay a weakness and new ones arise. Same privacy rule as every artefact: seams are named by their content, not by which examiner raised them.

```markdown
---
type: mock-defence
event: {event}
date: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
document: "{path to the document defended}"
mode: synthesis
sources:
  - ".claude/skills/mock-defence/outputs/mock-defence-YYYY-MM-DD-HHMM-{event}.md"
---

# Defence standing ledger — {event} — updated {YYYY-MM-DD}

{One line: what this consolidates, how many sessions fold in, the bar (a candidacy probes whether the plan is sound; a thesis whether the work is done), and that statuses are recomputed each refresh, not frozen.}

## Open weak spots (current)

Deepest first; each recomputed against the latest session and, where it matters, the current document.

- {seam, one line}: surviving {N} sessions ({which reports}); {still open | improved}; closes when {the fix or to-do that would resolve it}.

## Resolved since (for the record)

- {seam}: closed in {session / report} — {what closed it: a document edit, or an answer that finally held}.

## Throughline

{The one or two things that most decide the outcome — what to fix first; the headline a reader should leave with.}
```

## Transcript

An interactive drill also writes a verbatim companion to `.claude/skills/mock-defence/outputs/mock-defence-YYYY-MM-DD-HHMM-{event}-transcript.md` (same timestamp and event as the report). The question-bank mode has no dialogue and writes no transcript. The transcript is the full turn-by-turn record of the session, in order — questions as voiced, the candidate's answers verbatim, every counter and follow-up, the in-role verdicts, and any out-of-role `Coach:` or `pause` turns where they occurred. It follows the privacy rule above. Write it from the actual conversation; never reconstruct or embellish turns that did not happen.

```markdown
---
type: mock-defence-transcript
event: {event}
date: {YYYY-MM-DD}
document: "{path to the document defended}"
mode: drill
detail_level: {high-level | nit-pick | mixed}
report: mock-defence-YYYY-MM-DD-HHMM-{event}.md
---

# Mock defence transcript — {event} — {YYYY-MM-DD}

Verbatim record of the drill, in turn order. Questions attributed by seat; candidate answers as given. Detail level: {high-level / nit-pick / mixed}.

{member}: {question, as voiced}

Candidate: {the candidate's answer, verbatim}

{member}: {counter or follow-up, as voiced}

Candidate: {the candidate's reply, verbatim}

Verdict: {the one-line in-role verdict}

Coach: {the out-of-role coaching addendum, where one fired}

---

{continue in turn order to the end of the drill, including any control-word turns — pause / skip / switch / harder / easier / nitpick / big picture — where they occurred}
```
