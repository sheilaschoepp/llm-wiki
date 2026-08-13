# cleanup — report and log templates (Steps 5–6)

The two durable artifacts every cleanup run writes: the combined report saved to `2-outputs/cleanup/`, and the dated entry prepended to `1-wiki/log.md`. SKILL.md Steps 5 and 6 hold the filename, the timestamp rule, and what each run must fill in; this file holds the shapes to copy. Load it at write time — the classification steps do not need it.

Include only the sections for the job(s) that ran, and drop the preservation slot when the sub-mode did not run. This is the run's own new log entry; no past entry is ever edited to match the current state.

## Contents

- The predecessor record
- Report shape
- Log entry shape

## The predecessor record

Writing this report supersedes the previous `cleanup` report, which Step 4 classified as protected (it was the most recent on disk at scan time). That is expected: a run never proposes its own immediate predecessor, and the predecessor becomes a superseded-check candidate on the next run. Record it in the report's protected list as `cleanup <file> (superseded by this report; candidate next run)` so the kept-latest line is not read as a claim that it survives.

## Report shape

```markdown
---
type: cleanup
date: YYYY-MM-DD
---

# Cleanup report: YYYY-MM-DD

## Bottom line
- Memory — safe to clear now: <count> graduated; left resident, awaiting promotion elsewhere: <count> (not-graduated / partial); decisions to confirm: <count> (spent → delete; contradicted → drop / keep)
- Outputs — deletion candidates: <count> (junk J / superseded-check S / orphaned-subject O / aged A / preservation P, sub-mode only); reported, no action: <count> unrecognized; protected and skipped: <count>
- Hot threads — spent entries: <count> (Open threads <n> / Watchlist <n>); of these, trim <count>, drop whole <count>
- Uncommitted and unrecoverable if removed: <count> (memory entries + output files; each gated individually)

## Memory: summary
- Entries: N across M files (A+B+C+D+E+F+G+I+J+K must equal N; every entry lands in exactly one line)
- Graduated, unflagged (safe to clear): A
- Partial: B
- Not graduated: C
- Contradicted: D
- Keep in memory: E
- Spent (propose deletion): F
- Mis-homed / over-graduated (consolidate at the home first — not clearable this run): G
- Regressed/lost (a home dropped a rule that had graduated — restore it): I
- Already-cleared pointers (breadcrumb verified, rule still present): J
- Malformed (entries without an H2 heading): K
- Hygiene-flagged (sensitive content — redact or remove): L, a cross-cutting flag counted on top of the entry's own category
- Empty templates: H (no action — required scaffolding, left as-is)
- Missing per-skill memory files (recreate template): list of folders

## Memory: per-entry findings

### `path/to/memory-file.md` — "<entry heading>"
- Category: graduated | partial | not-graduated | contradicted | keep-in-memory | spent | already-cleared (pointer) | regressed/lost | malformed
- Flag: none | mis-homed | over-graduated (a `graduated` entry counted under summary line G, not A — and never offered for clearing) | hygiene (counted under L, in addition to the category's own line)
- Outcome: proposed-for-clearing | proposed-for-deletion | proposed-for-redaction | reported only (left resident) | kept (user declined) | keep (already justified in-entry) — filled in at Step 8 with what actually happened
- Age: <entry date from heading> (<N days/weeks old>), or `n/a` for MEMORY.md entries (topic heading, no date)
- Home: `MEMORY.md` (or `CLAUDE.md` → <section>, or `.claude/skills/<skill>/SKILL.md` → <step>) — for a `CLAUDE.md` or `SKILL.md` home, name where the user authors that shared file, since this wiki's copy is one of several kept in step by hand
- Evidence: `file:line` showing the rule is present / absent / contradicted
- Direction check: what the home actually states (mechanism only, or the matching do/never) vs what the entry prescribes — the basis for graduated-vs-not
- Action: "none — safe to clear" | "left resident — not absorbed; add to <home>: <exact text that would graduate it>" (for `partial`, the missing clause only) | "left resident — restore at <home>: <the dropped rule>" (`regressed/lost`) | the contradiction to resolve (`contradicted`) | the deletion rationale (`spent`) | "none — stays" (`keep-in-memory`)

## Outputs: cleanup candidates
- Age threshold this run: <N days (aged = at least N days old) | 0 — everything not protected | no age cutoff>

### junk
- `2-outputs/<path>` — <why: OS cruft / zero-byte stray>

### superseded-check
- `2-outputs/<kind>/<file>` — superseded by `<kept file>` (kept), or `demoted: zero-byte/unparseable, so <kept file> is the kept-latest instead`

### orphaned-subject
- `2-outputs/<kind>/<file>` — subject `<stem/skill>` no longer on disk

### aged
- `2-outputs/<kind>/<file>` — <N> days old, at or past the <N>-day threshold (or `swept: everything not protected` when the threshold is zero)

### unrecognized (reported, not proposed)
- `2-outputs/<path>` — no `{kind}-YYYY-MM-DD-HHMM` filename to classify by; your call

### preservation (opt-in sub-mode)
- `2-outputs/forget/quarantine/<file>` — sole copy of `<page>` (page absent from `1-wiki/`) | `2-outputs/supersede/preserve/<file>` — prior version of `<page>` (page live)

### protected (skipped, no action)
- kept-latest: lint `<file>`, consistency `<file>`, audit `<file>`, cleanup `<file>` (superseded by this report; candidate next run)
- clean-report carve-out: lint `<file>`, consistency `<file>` — list a file here only when it differs from that kind's kept-latest, i.e. the newest report was not `clean`
- preservation: `forget/quarantine/`, `supersede/preserve/` — name each folder separately, since the sub-mode lifts protection for only the one folder the user named

## Hot threads: spent entries
- Flagged by `hot_thread_spent`: <N> (Open threads <n>, Watchlist <n>)

### `hot.md` line <N> — <trim | drop whole>
- Spent: "<quoted sub-item>" — <why: every page it names is now verified / no named page carries a marker / the sweep it defers reports zero>
- Live (kept): <the named remainder, or "nothing — entry dropped">
- Proposed text: "<the post-prune entry, omitted when dropped whole>"
- Outcome: proposed-for-trim | proposed-for-drop | kept (user declined) — filled in at Step 8 with what actually happened

## Self-report
- {a specific limitation that bit cleanup this run — a graduation call it couldn't make, a candidate it couldn't classify, a safety gate that slowed it} → upgrade: {how the cleanup skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

## Log entry shape

Use the schema's dated-and-timed heading (`## [YYYY-MM-DD HH:MM] verb | subject`, 24-hour UTC from the same `TZ='UTC' date` call as Step 5). Name only the job(s) that ran in the subject and drop the line for the job that did not.

```markdown
## [YYYY-MM-DD HH:MM] cleanup | memory graduation check + outputs sweep + hot-thread prune
- Saved: [[2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md|cleanup-YYYY-MM-DD-HHMM]]
- Memory: graduated/safe-to-clear K; left resident C (not-graduated / partial); contradicted D
- Outputs: candidates — junk J, superseded-check S, orphaned-subject O, aged A, preservation P (sub-mode); unrecognized U (reported); protected K
- Hot threads: spent T (Open threads t1, Watchlist t2) — trim X, drop whole Y
- Applied (after approval): <memory clears / output deletions / hot-thread prunes>, or "awaiting user"
- Removed: "awaiting user" — replaced in Step 8.3 by one line per removal (path | what it was | descriptor | verified SHA or `uncommitted — not recoverable`)
```

The `Applied` and `Removed` lines are written as "awaiting user" at Step 6 and filled in at Step 8. The `Removed:` list is the run's permanent deletion record; its line format is in `references/removal-safety.md`.
