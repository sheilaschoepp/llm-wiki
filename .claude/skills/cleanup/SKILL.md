---
name: cleanup
description: Three-part housekeeping for the knowledge base's working files. (1) Memory graduation — check whether each memory-tier entry (MEMORY.md, multi-skill, per-skill) is already absorbed into its permanent home, then graduate and clear it. (2) Outputs cleanup — prune 2-outputs junk, superseded reports, reports orphaned by a deleted source or skill, and aged artifacts. (3) Wiki bookkeeping — move log.md entries older than a cutoff into 1-wiki/archive/, and retire hot.md Open threads and Watchlist bullets that are finished. Use when the user wants to clean up, prune, or clear memory files, old outputs, or log.md and hot.md, asks what is safe to remove, whether memory is absorbed, or whether an open thread or watchlist item is still live, to clear out old, superseded, orphaned, or junk reports, or to shrink, archive, trim, or rotate an overgrown log — or as a periodic pass. Different from lint (index drift, hot Recent-activity trim, chronology sorting) and forget (removes wiki pages).
---

# cleanup

Three-part housekeeping for the knowledge base's own working files: graduate-and-clear the memory journals, prune unneeded artifacts from `2-outputs/`, and archive the wiki bookkeeping files that grow without bound. Every job removes or moves content only with the user's explicit approval under the recoverability-aware gate in Step 8 and Limits.

A run does all three jobs by default. The user may scope it to one or two ("just clean memory", "just clean old outputs", "just archive the log").

## Purpose

Memory files (`MEMORY.md`, the multi-skill file, the per-skill files) are working journals. CLAUDE.md's graduation path says a stable rule eventually graduates into its permanent home — `MEMORY.md` for stable behavioural rules, `CLAUDE.md` for wiki-structure and schema rules, a `SKILL.md` for skill-specific procedure — after which the memory entry can be removed. A journal entry (per-skill or multi-skill) most often graduates up into `MEMORY.md`; a `MEMORY.md` entry graduates further only when it is a misfiled schema rule (onward to `CLAUDE.md`) or skill-procedure rule (onward to a `SKILL.md`) — a stable behavioural rule is already in its terminal home in `MEMORY.md` and graduates no further. The memory job finds out which entries have actually made that trip, so the journals can be pruned without quietly dropping a rule that was never captured anywhere else. An entry whose rule is already present in its permanent home is "absorbed" — the `graduated` category in Step 3, and the word the description and When To Invoke use.

The hazard the memory job exists to prevent: clearing a memory file on the assumption that "it is all in CLAUDE.md by now" when some entries are not, and one or two may even contradict the current schema. Clearing then loses live guidance. This skill replaces that assumption with a per-entry check.

`2-outputs/` is uncapped: every skill appends dated reports and artifacts there and nothing is auto-pruned, so check folders fill with superseded reports, reports outlive the source or skill they were about, and old working artifacts accumulate. The outputs job surfaces these as deletion candidates — never deleting on its own, always applying the user's explicit approval. Memory removals and non-git-recoverable output deletions are approved individually; committed-clean, git-recoverable output candidates may share one path-explicit `multiSelect` (Step 8). That approval is the "deliberate user action" by which `2-outputs/` is allowed to shrink; nothing here is auto-pruned.

The memory job is the deep, on-demand counterpart to the cheap mechanical entry-counter (the `memory_file_graduation_prompt` check). That counter flags a memory file that has grown past its soft cap; this skill reads each entry and decides whether its content is already somewhere permanent.

`1-wiki/log.md` is the permanent, complete record of every operation, so nothing may delete from it — and no skill trims it, so it grows without bound. The bookkeeping job resolves both at once by *moving* aged entries into `1-wiki/archive/log-YYYY-MM.md`: the record stays complete as the union of the live log and its archives, while the file the user opens keeps a recent working window. `hot.md` gets the judgement half — lint already prunes an Open-threads or Watchlist bullet whose target page is gone, but cannot judge one whose page still exists and whose thread is simply finished. `index.md` gets no archival job at all: it is a live catalog that lint keeps synchronized both ways, and its length tracks the wiki rather than accumulating cruft.

## Scope

### Memory graduation

Read and classify:

- `MEMORY.md` — stable transferable memory (each H2 section is one entry).
- `.claude/skills/multi-skill/multi-skill-memory.md` — cross-skill corrections (each H2 is one entry).
- `.claude/skills/<skill>/<skill>-memory.md` — per-skill corrections (each H2 is one entry).

Check each entry against its permanent home:

- `MEMORY.md` — stable transferable behavioural rules; the home most per-skill and multi-skill journal entries graduate into.
- `CLAUDE.md` — schema and behavioural defaults (wiki-structure and schema rules).
- `.claude/skills/<skill>/SKILL.md` — skill-specific procedure.

A `MEMORY.md` entry is itself a tier being classified, but `MEMORY.md` is the terminal home for a stable behavioural rule — such a rule graduates no further and is settled where it sits. Only a rule that actually belongs elsewhere graduates onward: a wiki-structure or schema rule misfiled in `MEMORY.md` (home `CLAUDE.md`), or a skill-procedure rule (home a `SKILL.md`). A durable behavioural rule correctly in `MEMORY.md` is classified `keep-in-memory` (terminal), never `not-graduated`, and is never proposed for a move into `CLAUDE.md`.

### Outputs cleanup

Scan `2-outputs/` and sort files into four candidate categories — junk, superseded-check, orphaned-subject, and aged (classified in Step 4; definitions in `references/outputs-cleanup.md`).

The **protected set** is never a candidate, in any category: every `.gitkeep`; every output file containing a complete `%%LOCKED%%` ... `%%/LOCKED%%` span or either unmatched marker; the most-recent report of each repeatable check kind — for the per-subject kind `skill-linter`, the most-recent report per skill, not one globally; the most-recent clean `lint` and `consistency` report (audit's actual precondition — a recent clean lint and consistency — so it survives the prune; the latest `audit` report is already kept as the most-recent of its kind, and audit writes no `result:` field of its own to test for "clean"); the latest `ingest-*-{stem}.md` report for every `{stem}` still present in `1-wiki/sources/` (it is the sole home of the deep-ingest `purpose:` recovery record); and everything under `forget/quarantine/` and `supersede/preserve/`. The `forget/quarantine/` and `supersede/preserve/` folders hold the only preserved copy of removed wiki content; deleting from either is a separate, deliberate act the user must request explicitly, not part of a sweep.

### Wiki bookkeeping

Three files, three different jobs — and each stops where `lint` already acts, so the two skills never propose competing fixes (full split in `references/bookkeeping-cleanup.md`):

- `1-wiki/log.md` — archive entries older than the resolved cutoff into `1-wiki/archive/log-YYYY-MM.md`, grouped by the entry's own year-month. A move, never a deletion: archives write and verify first, a conservation check proves no entry was lost or duplicated, and only then is `log.md` rewritten.
- `1-wiki/hot.md` — review `Open threads` and `Watchlist` bullets that are stale while their target page still exists, archiving each removed bullet to `1-wiki/archive/hot-YYYY-MM.md` first. `Recent activity` is lint's five-entry trim and `Active focus` is user-owned; neither is touched.
- `1-wiki/index.md` — never edited and never archived from. Report only: a duplicate listing of the same page — the one class lint's drift checks cannot see, since it dedupes listings into a set — is recorded `unclassified-blocked` for manual review.

Do not read or modify `0-raw/`. `CLAUDE.md` and the `SKILL.md` files are read-only here — graduations into them are surfaced as proposals (Step 9). The write boundary is stated once in Limits.

## When To Invoke

- The user wants to clear, prune, consolidate, or clean up memory files, old outputs, or both.
- The user asks whether memory has been absorbed into MEMORY.md, CLAUDE.md, or the skills.
- The user asks what is safe to remove from the memory files or from `2-outputs/`.
- The user asks to graduate, promote, or move a memory entry into its permanent home.
- The user asks to clear out old, superseded, orphaned, or junk reports under `2-outputs/`.
- The user asks to clean up, shrink, trim, or archive `log.md`, `hot.md`, or `index.md`, or says the log has grown too long.
- The user asks whether a `hot.md` open thread or watchlist item is still live.
- As a periodic consolidation pass when memory files, `2-outputs/`, or the bookkeeping files have grown.

## When Not To Invoke

- The user wants the memory entry count against the soft cap only — that is the mechanical `memory_file_graduation_prompt` check.
- The user wants to add a new memory entry. Append it directly per CLAUDE.md → Memory tiers.
- Schema or skill drift unrelated to memory. Use `consistency`.
- `index.md` drift, the `hot.md` Recent-activity trim, pruning a `hot.md` bullet whose target page is gone, or log chronology sorting. All four are `lint`'s mechanical fixes; this skill deliberately leaves them alone.
- Removing a wiki page, source-support link, or attachment. Use `forget` — it quarantines wiki content to `2-outputs/forget/quarantine/`. This skill removes only memory-journal entries and `2-outputs/` artifacts, which git history alone preserves, and moves `log.md` / `hot.md` content into `1-wiki/archive/` without deleting it.

## Procedure

```text
Cleanup Progress:
- [ ] Step 1: Load this skill's memory and the permanent-home targets
- [ ] Step 2: [Memory] Enumerate every memory entry across the tiers
- [ ] Step 3: [Memory] Classify each entry against its permanent home (verify against current files)
- [ ] Step 4: [Outputs] Resolve the age threshold, scan and classify 2-outputs candidates
- [ ] Step 5: [Bookkeeping] Resolve the archive cutoff, scan log.md, hot.md, and index.md
- [ ] Step 6: Save the combined report
- [ ] Step 7: Prepend log entry
- [ ] Step 8: Present graduation proposals and cleanup decisions
- [ ] Step 9: On approval, graduate then remove; delete approved output files; archive log/hot; reconcile the record
```

1. **Load this skill's memory and the job-specific references and operands.** Always read `.claude/skills/cleanup/cleanup-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` for prior corrections to this skill; this operation-level loading does not replace the repository's session-start bootstrap. For the memory job, read `references/memory-graduation.md`, `MEMORY.md`, and `CLAUDE.md` in full, then open target skill files as needed — `MEMORY.md` and `CLAUDE.md` are permanent-home operands, and a skill-specific entry may graduate into its own `SKILL.md`. For the outputs job, read `references/outputs-cleanup.md`; an outputs-only run does not re-read the memory-job operands. For the bookkeeping job, read `references/bookkeeping-cleanup.md`, then `1-wiki/log.md`, `1-wiki/hot.md`, and `1-wiki/index.md`. If the user scoped the run to a subset of jobs, skip the steps and job-specific reads for the others (memory job = Steps 2–3; outputs job = Step 4; bookkeeping job = Step 5), but always do Steps 6–9 for whichever jobs ran.

2. **[Memory] Enumerate every memory entry across the tiers.** List the memory files:

   ```bash
   ls .claude/skills/*/*-memory.md MEMORY.md
   ```

   The `*/*-memory.md` glob already matches `multi-skill/multi-skill-memory.md` — do not also list it explicitly, or that file is enumerated twice and its cross-skill entries are double-counted.

   Also run `git status --short .claude/skills MEMORY.md` here: removed memory has no quarantine fallback, so an uncommitted entry deleted later in Step 9 is unrecoverable. Note any uncommitted memory files in the report's Bottom line and carry the warning into Step 8 before deletions are approved.

   For each file, split on H2 headings (`## ...`). Each H2 section is one entry. The intro boilerplate above the first H2 is not an entry. In `MEMORY.md`, the `## Index` heading is a table of contents, not an entry — skip it (the consistency counter does the same). A file that has body content below the intro but no `## ` heading at all is malformed (entries appended without a heading), not empty — flag it `malformed (entries without H2)` for the user; never collapse it into the empties count.

   A struck-through heading (`## ~~...~~`) is a breadcrumb left by a prior Step 9 claiming the rule graduated. Do not blindly trust the claim — it is a self-claim like any other, and the home may have moved on since. Do a lightweight presence check against the named home (the same direction-aware check as Step 3 — graduated only if the home states the entry's do/never, not merely that the subject exists): if the rule is still present, record it `already-cleared (pointer)` and do not re-propose graduation or deletion; if the rule is absent from the named home, widen the grep across `MEMORY.md` and `CLAUDE.md` before concluding it is lost, since the schema may have relocated it. If it is genuinely gone, flag it `regressed/lost` — the home dropped a rule that had graduated — and re-propose graduation to restore it; do not clear it. This is distinct from `contradicted` (active disagreement, whose remedy may be to drop the entry). If the pointer's own text carries an explicit drop-when-consolidating signal ("safe to drop", "remove in a later consolidation pass"), surface it in Step 8 as a low-priority "pointer the entry marks droppable" note rather than suppressing it.

   A file with no H2 sections is an empty template, not a cleanup target: every skill folder is required to carry its per-skill memory file (CLAUDE.md → Memory tiers), so an empty file is intact scaffolding. Record it as `empty (nothing to clear — template intact)` and collapse all empties to a single count in the report; never list them as deletion candidates. Separately, cross-check the matched per-skill files against the actual skill folders (`ls -d .claude/skills/*/`, excluding `multi-skill/` — it is not a skill folder, carries no `SKILL.md`, and holds the cross-skill journal `multi-skill-memory.md` rather than a `<skill>-memory.md`, so it is never a "missing per-skill memory file"): a skill folder with no `<skill>-memory.md` is a structural gap — note it in the report as `missing per-skill memory file` so the user can recreate the template (it is not a graduation finding, and is kept distinct from the empty-but-present case).

   Heading formats differ by tier: the journals (per-skill and multi-skill files) use dated headings, `## YYYY-MM-DD — title`; `MEMORY.md` uses topic headings with no date, `## Topic — description`. This matters for age (Step 3).

3. **[Memory] Classify each entry against its permanent home.** For each entry, first name where its content would live if graduated: `MEMORY.md` (a stable behavioural rule from a journal tier), a specific `CLAUDE.md` section (a wiki-structure or schema rule), or a specific `SKILL.md` (skill procedure). An entry in the multi-skill file is a special case: genuinely cross-skill content never graduates into one `SKILL.md`, because that would install a shared rule in only one caller. If inspection shows that the entry actually applies to one skill only, flag it `mis-homed`: while it is still provisional, propose moving the full entry to that skill's existing `<skill>-memory.md`; when it is durable skill procedure, propose its named `SKILL.md` as the permanent home. In either case, clear the multi-skill source only after the user approves the move and the full rule is verified at the named destination.

   Then open the home file and verify whether the substance is actually present. Verify against the current file text — never trust the memory entry's own claim that it "was added to CLAUDE.md", since the schema may have moved on since. Grep the target for the entry's load-bearing terms, then read the surrounding lines to confirm the rule matches, not just a keyword. **Match the entry's direction, not just its subject.** A prohibition ("never do X") or prescription ("always do Y") is graduated only if the home states that same do/never — not merely that X's mechanism exists. Many entries are about a mechanism CLAUDE.md already documents (`verified_hash`, frames, callouts); the documented mechanism does not graduate a behavioural rule about that mechanism. If the home describes the subject but not the rule's do/never, classify it not-graduated (or partial), never graduated. If the named home file or section no longer exists (a retired or renamed skill, a removed CLAUDE.md section), do not treat the rule as graduated — classify by current content: if it still applies, not-graduated against the current home; if its target is gone and the rule no longer applies, contradicted or spent. Flag the dangling reference explicitly.

   Assign each entry exactly one category — **graduated**, **partial**, **not-graduated**, **contradicted**, **keep-in-memory**, or **spent**. The full category definitions, the tie-break order when two seem to fit, the sensitive-content screen (run before proposing any graduation into `MEMORY.md`/`CLAUDE.md`), and the keep-vs-graduate-vs-delete judgement (a common-sense content call, not a frequency count — age is a hint, never a trigger) are in `references/memory-graduation.md`.

4. **[Outputs] Resolve the age threshold, then scan and classify `2-outputs/` candidates.** First fix the **age threshold** for the aged category: take it from the invocation if the user named one ("clean up outputs older than 30 days"); otherwise ask once with `AskUserQuestion`, offering 90 days marked `(Recommended)` and ordered first, then 30 / 180 days / "no age cutoff this run"; default to 90 days if the user does not pick. The threshold governs only the aged category; the other three ignore age. Run `git status --short 2-outputs/` so you know which candidates are uncommitted (git cannot recover those — they are gated individually in Step 8, like a true deletion).

   Enumerate `2-outputs/` without following symlinks, using `lstat`-equivalent type checks. Traversal directories are not inventory items. Count every regular file exactly once as **candidate**, **protected**, **retained-current**, or **unclassified-blocked**, and list symlinks or other non-regular entries separately as blocked; never delete a non-regular entry in this skill. Require `regular files scanned = candidates + protected + retained-current + unclassified-blocked` before saving the report. For every candidate, record a SHA-256 of the exact bytes approved. The candidate definitions (**junk**, **superseded-check**, **orphaned-subject**, **aged**), their precedence, the inbound-reference check, the protected set, and the retained/unclassified distinction are in `references/outputs-cleanup.md`.

5. **[Bookkeeping] Resolve the archive cutoff, then scan `log.md`, `hot.md`, and `index.md`.** First fix the **archive cutoff** for `log.md`: take it from the invocation if the user named one ("archive log entries older than 30 days"); otherwise ask once with `AskUserQuestion`, offering 90 days marked `(Recommended)` and ordered first, then 30 / 180 days / "no archival this run"; default to 90 days if the user does not pick. Run `git status --short 1-wiki/log.md 1-wiki/hot.md` so you know whether either file is uncommitted before proposing a rewrite.

   Then parse `log.md` into entries on its `## [YYYY-MM-DD HH:MM] verb | subject` headings and partition them into **archivable** (heading date strictly older than the cutoff), **retained**, and **unclassified-blocked** (no parseable date — never archived, never guessed). Group the archivable set by each entry's own year-month into its `1-wiki/archive/log-YYYY-MM.md` destination, and record the counts per destination. Enumerate `1-wiki/archive/` as part of this scan: a destination that already exists is a merge rather than a new file, and an archivable entry already present there is a leftover from an interrupted run — carry it as already-archived rather than archiving it twice. Part 4 still takes its own snapshot immediately before writing, not here. Run the four-part conservation check before proposing anything; a failure aborts the log archival for the run and is reported rather than worked around.

   For `hot.md`, read only `Open threads` and `Watchlist`, and propose a bullet only when its target page still exists (a missing target is lint's prune) **and** the run can state the evidence that its thread is finished. For `index.md`, report unparseable or duplicate lines only — never edit it. The cutoff's meaning, entry boundaries, grouping and ordering rules, the conservation check, the write order, the staleness signals, and the archive-file format are in `references/bookkeeping-cleanup.md`.

6. **Save the combined report** to `2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md`, creating the folder if needed. Obtain the timestamp at write time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context gives the date but not the current minute. Include only the sections for the job(s) that ran. Report shape:

   ```markdown
   ---
   type: cleanup-report
   date: YYYY-MM-DD
   ---

   # Cleanup report: YYYY-MM-DD

   ## Bottom line
   - Memory — safe to clear now: <count> graduated; needs a decision: <count> (not-graduated / partial / contradicted); decisions to confirm: <count> (spent → delete; contradicted → drop / re-graduate / keep)
   - Outputs — deletion candidates: <count> (junk J / superseded-check S / orphaned-subject O / aged A); protected: <count>; retained-current: <count>; unclassified-blocked: <count>; non-regular blocked: <count>
   - Bookkeeping — log: <count> entries archivable of <total> (cutoff <N days | none>) into <count> archive files; hot: <count> stale bullets proposed; index: <count> unparseable lines (report-only)
   - Uncommitted and unrecoverable if removed: <count> (memory entries + output files; each gated individually)

   ## Memory: summary
   - Entries: N across M files
   - Graduated (safe to clear): A
   - Partial: B
   - Not graduated: C
   - Contradicted: D
   - Keep in memory: E
   - Spent (propose deletion): F
   - Mis-homed / over-graduated (move before clearing): G
   - Empty templates: H (no action — required scaffolding, left as-is)
   - Missing per-skill memory files (recreate template): list of folders

   ## Memory: per-entry findings

   ### `path/to/memory-file.md` — "<entry heading>"
   - Category: graduated | partial | not-graduated | contradicted | keep-in-memory | spent | already-cleared (pointer) | regressed/lost | malformed
   - Flag: none | mis-homed | over-graduated (a `graduated` entry counted under summary line G, not A)
   - Age: <entry date from heading> (<N days/weeks old>), or `n/a` for MEMORY.md entries (topic heading, no date)
   - Home: `MEMORY.md` (or `CLAUDE.md` → <section>, `.claude/skills/<skill>/SKILL.md` → <step>, or `.claude/skills/<skill>/<skill>-memory.md` for a provisional mis-homed move)
   - Evidence: `file:line` showing the rule is present / absent / contradicted
   - Direction check: what the home actually states (mechanism only, or the matching do/never) vs what the entry prescribes — the basis for graduated-vs-not
   - Proposal: exact edit to graduate it (for partial / not-graduated), the contradiction to resolve, the deletion rationale (for spent), or "none — safe to clear"

   ## Outputs: cleanup candidates
   - Age threshold this run: <N days | none>
   - Regular files scanned: N
   - Reconciliation: candidates C + protected P + retained-current R + unclassified-blocked U = N
   - Non-regular blocked (not in regular-file total): Q

   ### junk
   - `2-outputs/<path>` — <why: OS cruft / zero-byte stray>; sha256: `<digest>`; recoverability: <committed-clean | uncommitted>

   ### superseded-check
   - `2-outputs/<kind>/<file>` — superseded by newer `<kept file>` (kept); sha256: `<digest>`; recoverability: <committed-clean | uncommitted>

   ### orphaned-subject
   - `2-outputs/<kind>/<file>` — subject `<stem/skill>` no longer on disk; sha256: `<digest>`; recoverability: <committed-clean | uncommitted>

   ### aged
   - `2-outputs/<kind>/<file>` — older than <N> days; sha256: `<digest>`; recoverability: <committed-clean | uncommitted>

   ### protected (skipped, no action)
   - kept-latest: lint `<file>`, consistency `<file>` (clean), audit `<file>`, ...
   - preservation: `forget/quarantine/`, `supersede/preserve/`

   ### retained-current (not a candidate)
   - `2-outputs/<path>` — <recognized artifact that matches no deletion-candidate category>

   ### unclassified-blocked (manual review)
   - `2-outputs/<path>` — <malformed or ambiguous regular file; never delete in this run>

   ### non-regular blocked (manual review)
   - `2-outputs/<path>` — <symlink or other non-regular entry; never follow or delete in this run>

   ## Bookkeeping: log.md archival
   - Cutoff this run: <N days | none> (entries dated before YYYY-MM-DD)
   - Entries: <total> total = <archivable> archivable + <retained> retained + <blocked> unclassified-blocked
   - Conservation check: pass | FAILED (<which of the four parts, and what the archival did instead>)
   - Destinations: `1-wiki/archive/log-YYYY-MM.md` — <count> entries (new | merge into existing); ...
   - Recoverability: <committed-clean | uncommitted> at scan time

   ### quoted headings (not split)
   - `## <line>` — inside a fenced or indented code block in the entry above; counted as body text, not a heading

   ### unclassified-blocked (left in the live log)
   - `## <heading>` — <no parseable date; never archived on file position>

   ## Bookkeeping: hot.md stale bullets
   ### Open threads
   - `<bullet text>` — target `<page>` exists; evidence it is finished: <the synthesis that answers it (name it) / all named pages verified / no log activity since YYYY-MM-DD — corroborating only, never deciding>, plus one line stating why the thread is closed; archives to `1-wiki/archive/hot-YYYY-MM.md`

   ### Watchlist
   - `<bullet text>` — <same evidence form>

   ### not proposed (still live)
   - <count> bullets with no staleness evidence, left untouched

   ## Bookkeeping: index.md
   - Never edited. Unparseable or duplicate lines for manual review: <count>
   - `1-wiki/index.md:<line>` — <what could not be parsed>

   ## Self-report
   - {a specific limitation that bit cleanup this run — a graduation call it couldn't make, a candidate it couldn't classify, a safety gate that slowed it} → upgrade: {how the cleanup skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
   ```

7. **Prepend log entry** to `1-wiki/log.md`. Use the schema's dated-and-timed heading (`## [YYYY-MM-DD HH:MM] verb | subject`, 24-hour UTC from the same `TZ='UTC' date` call as Step 6):

   ```markdown
   ## [YYYY-MM-DD HH:MM] cleanup | memory graduation + outputs sweep + bookkeeping archival
   - Saved: [[2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md|cleanup-YYYY-MM-DD-HHMM]]
   - Memory: graduated/safe-to-clear K; not-graduated C; contradicted D
   - Outputs: candidates — junk J, superseded-check S, orphaned-subject O, aged A; protected P
   - Bookkeeping: log — L of T entries archivable (cutoff N days); hot — H stale bullets; index — report-only
   - Applied (after approval): <memory clears / output deletions / archival>, or "awaiting user"
   ```

   Name only the job(s) that ran in the subject and drop the line for any job that did not. This entry is written **before** any log archival is applied, and it is always newer than the cutoff, so it is never itself archivable in the same run.

8. **Present graduation proposals and cleanup decisions.** Lead with the bottom line — the action lists the user acts on first.

   For the memory job, present: the "safe to clear now" (graduated) list and the "needs a decision before clearing" list (not-graduated / partial / contradicted). Then:
   - the not-graduated and partial entries, each with the concrete edit that would graduate it (exact text + target file and section);
   - the mis-homed single-skill entries, each with the exact proposed destination: its per-skill memory journal while provisional, or its named `SKILL.md` when durable procedure;
   - the contradicted entries, each with the disagreement stated plainly, for the user to decide whether to drop the stale entry or re-graduate the rule;
   - the spent entries, each with its age and a one-line reason it has done its job and will not recur, proposed for deletion;
   - the graduated entries, listed as safe to clear, naming both removal styles up front so the user picks one as part of approval — clear the H2 section outright (git preserves it) or leave a one-line struck-through pointer to the new home;
   - empty templates as a single count (required scaffolding, no action), and any missing per-skill files to recreate.

   A `keep-in-memory` entry whose own body already states a current keep rationale is listed in the saved report but omitted from this spoken presentation marked `keep (already justified in-entry)`, so settled keeps are not re-litigated each run.

   For the outputs job, present the candidates grouped by category with the per-file rationale, and the protected-and-skipped summary so the user sees what was deliberately held back.

   For the bookkeeping job, present the log archival as **one** proposal — the cutoff, the entry counts (total = archivable + retained + blocked), every destination path, and the conservation-check result — then the `hot.md` stale bullets individually with their evidence, then the `index.md` report-only lines. State plainly that the log archival moves entries rather than deleting them and that the record stays complete as live plus archives; a user who cannot see that will read the log shrinking as data loss.

   **Gating — approve the edit separately from the removal, then apply the recoverability rule to deletions.** First ask separately about every proposed graduation, re-graduation, consolidation, or provisional-journal move, including every `partial`, `not-graduated`, mis-homed, over-graduated, and regressed entry; never combine that edit approval with a later clear-or-pointer decision. Every memory-entry removal and every non-git-recoverable output deletion stays one item per `AskUserQuestion` call. After verifying each path is a committed-clean, git-recoverable `2-outputs/` candidate, those output paths may share one `multiSelect` that names every path and rationale separately; an unticked path stays resident. Batch eligibility is per item: if a path becomes modified, untracked, protected, locked, non-regular, or otherwise changes classification before deletion, only that item's approval expires, and it must be reclassified and freshly gated under its current state.
   The log archival is the one exception to per-item gating, and it is an exception on the merits rather than for convenience: nothing leaves the repo, the conservation check proves entry-for-entry that nothing was lost or duplicated, and a per-entry gate over hundreds of date-mechanical moves would be approval theatre. It takes one confirmation for the whole operation. A `hot.md` bullet stays per item — which thread is finished is an editorial judgement the check cannot make.
   - Mark each gated choice per CLAUDE.md → Communication style: order the recommended option first and mark it `(Recommended)` — `delete` for a spent entry, `clear` for a graduated one, the proposed action for an output candidate, `archive` for the log operation. The `contradicted` drop-vs-re-graduate call is a genuine no-lean decision, so state "no recommendation" rather than fake a pick.
   - A declined or unticked candidate — memory entry or output file — is simply not removed: it stays resident, is recorded in the report as `kept (user declined)`, and cascades to nothing else. Declining one item never blocks approving another.

   Do not apply any `CLAUDE.md` or `SKILL.md` edit, and do not remove any memory entry or output file, without the user's explicit say-so.

9. **On approval, apply — graduate before removing for memory, then delete approved output files, then archive.**

   For each memory entry the user approved for cleanup:
   1. Apply the separately approved destination edit first. A durable rule may graduate into `MEMORY.md`, `CLAUDE.md`, or its named `SKILL.md`; a provisional single-skill entry misfiled in the multi-skill journal moves by appending the full entry to the existing named `<skill>-memory.md`. `CLAUDE.md` and `SKILL.md` edits proceed only on the user's explicit say-so (see Limits). For a `partial` entry, the graduation edit is the missing delta only (the clause absent from the home); once it lands the entry is fully graduated. A `spent` entry usually has nothing to graduate; if its one-time kernel check found a general rule, graduate that first.
   2. Re-read the named destination and confirm the rule is actually present before removing anything — for **every** entry being cleared, not only the ones that got an edit this run. A plain `graduated` entry applies no edit in 9.1, so its safety rests entirely on this removal-time re-check: re-run the Step-3 direction-aware presence check against the named home right now, because an earlier destination edit in this same Step-9 loop, or a user edit during the Step-8 approval gate, may have moved or clobbered the section since Step 3 read it. For an entry that did get a destination edit, also confirm that edit landed — never remove on the assumption the just-applied edit matched, since a near-miss or wrong-section edit can succeed yet leave the rule un-homed. Either way the confirmation is at the specific named target section, not anywhere in the file: a grep that finds the rule's terms in some *other* section (or a near-duplicate elsewhere) does not confirm it. Confirm the rule's full do/never is present — and for a moved or paraphrased rule, that no clause the entry carried was dropped in the move (a `partial` graduation re-checks the full do/never, not only the just-added delta, in case the home's pre-existing core was weakened since). If that confirmation fails, do not remove the entry: surface the failure to the user (retry the destination edit, keep the entry as-is, or abandon the upgrade), never silently skip or proceed.
   3. **Preserve and revalidate before removing.** Re-enumerate the exact current H2 and confirm its heading, section boundaries, and direction-bearing text still identify the entry the user approved. If the H2 intersects a complete `%%LOCKED%%` ... `%%/LOCKED%%` span, or its file contains an unmatched lock marker that makes the boundary ambiguous, removal is absolutely blocked. Re-check `git status --short` (or `git diff --quiet -- <file>`) for every affected file now rather than trusting the Step 2 snapshot. git history preserves prior text only when that prior state is committed, and the deletion has no quarantine fallback (unlike `forget`). If the source journal is dirty, git cannot recover the deleted text; surface the actual state and, per CLAUDE.md Safety rules, offer to commit or stash first and get explicit go-ahead before removal. If the destination edit from 9.1 is uncommitted, offer to commit it (and, if approved, the removal with it) before the only other copy disappears; do not leave the rule resident only in an uncommitted destination after deleting its source. Any change in H2 identity, lock state, or recoverability invalidates the existing removal approval and requires reclassification and fresh approval.
   4. Only after 9.2 and 9.3 pass, apply the separately approved removal style: delete the H2 section outright or replace it with the approved one-line struck-through pointer.

   Graduation and removal are gated separately. If the user approves the graduation edit but declines removal, apply the edit and leave the entry (optionally as a struck-through pointer). If the user declines the graduation edit, do not remove the entry — without a permanent home the rule would be lost; report it as still-resident. Never reverse the order: removal is contingent on the graduation having been applied first (or, for a spent entry with no kernel, on the deletion itself being approved).

   For each output file the user approved for deletion, revalidate the approved snapshot immediately before mutation. Use an `lstat`-equivalent check without following symlinks; require that the canonical path is still inside `2-outputs/`, is still the same regular file, and has the same SHA-256 recorded in Step 4. Recompute its candidate category, protected-set membership, lock-marker status, inbound-reference disclosure, and `git status --short` recoverability. A missing path, type/path/hash change, or changed classification blocks that item and requires reclassification plus fresh approval; a currently protected or locked file is an absolute block, not approval-overridable. If a batched path is no longer committed-clean, only that path's batch approval expires and the current non-git-recoverable deletion must be gated individually. After every check holds, remove that exact file. Deleting reports never touches the wiki pages or raw sources they describe — only the `2-outputs/` artifact. A `.gitkeep` keeps each emptied folder present in git, so pruning a folder's last report does not drop the folder from `output_kinds_match_disk`.

   If the log archival was approved, apply it after the memory and output work, in this order and no other:
   1. Re-parse `log.md` from disk and re-run the four-part conservation check against the approved partition. The file has changed since Step 5 — Step 7 prepended this run's own entry — so the totals must be recomputed, not reused. The new entry is newer than the cutoff and therefore lands in the retained set; if it does not, abort rather than archive the record of the run doing the archiving.
   2. Re-check `git status --short 1-wiki/log.md`. If the file is dirty with changes this run did not make, stop and surface it — a rewrite would absorb an edit nobody has reviewed.
   3. Write every destination archive file and read each back, confirming its entry count and that its headings match the approved set. For a month file that already existed, merge and re-sort newest-first, then verify the pre-existing entries survived.
   4. Only after every archive is verified on disk, edit `log.md` in place: delete each archived entry's byte span, leave every byte outside those spans untouched, then upsert the pointer line — replace the single existing line beginning `Older entries:`, or insert one if none exists; block if two exist. Never regenerate the file. Deleting spans preserves the H1, the description line, and any locked span without enumerating them, and the upsert cannot accrue a duplicate pointer. Run this whenever the removal set is non-empty, where that set is this run's archivable entries plus any entry present in both `log.md` and an archive with a matching digest — the second term is cutoff-independent, so a resumed run still repairs even when it archives nothing. When the removal set is empty, still upsert the pointer if the archive directory holds a file the pointer omits. A crash before this point leaves the record duplicated, which is recoverable; a crash after a premature write would lose entries outright.
   5. Re-run the conservation check across the final on-disk state (live plus archives) and report the result.

   For each approved `hot.md` bullet, append it verbatim to `1-wiki/archive/hot-YYYY-MM.md` under a dated heading naming its source section, confirm it landed, then remove it from `hot.md` and touch that file's `updated:` frontmatter to the run date (CLAUDE.md → Workflow Rules: touch `updated:` on every modified wiki page). Never remove before the archive copy is verified. `index.md` is never written.

   **Reconcile the record (done-state).** After all approved graduations, clears, deletions, and archival are applied, update the durable record to match disk: rewrite the log entry's `Applied (after approval):` line from "awaiting user" to what actually happened (entries cleared, files deleted, entries archived and where, and anything the user declined and left resident), and update the report's Bottom line the same way. The run is complete only when the log and report reflect the applied state, not the pre-approval proposal — if the user approved nothing, the Applied line reads "none approved — all resident". When the archival ran, this reconciliation edits the freshly rewritten `log.md`, so make it the last write of the run.

## Limits

- Do not read or edit raw sources; do not rewrite historical files under `2-outputs/` (the outputs job deletes whole superseded / orphaned / aged files on approval — it does not edit a kept file's contents).
- `CLAUDE.md` and every `SKILL.md` are never auto-edited — graduations into them are proposals applied only on the user's explicit say-so (Step 9). Graduations into `MEMORY.md` are ordinary agent-writable content edits, still gated on the Step 8 approval; the report and log are written without asking.
- Removing a memory entry or a non-git-recoverable output file is a deletion gated individually on user approval. Committed-clean, git-recoverable `2-outputs/` candidates may share one path-explicit `multiSelect`; every path is revalidated immediately before deletion, and drift invalidates only that item's approval.
- The bookkeeping job never deletes: it moves. A log archival is one approval for the whole operation (nothing leaves the repo, and the conservation check proves it entry for entry); a `hot.md` bullet removal is per item, and archives before it removes. `index.md` is report-only and is never written by this skill.
- Never rewrite `log.md` before every destination archive is written and verified on disk, and never archive an entry whose heading carries no parseable date. A conservation-check failure aborts the archival for the run — it is reported, never worked around.
- Do not duplicate `lint`'s mechanical fixes: `index.md` drift, the `hot.md` Recent-activity five-entry trim, pruning a `hot.md` bullet whose target page is gone, and chronology sorting all belong to `lint`. `hot.md`'s `Active focus` is user-owned and untouched.
- The protected set is never deleted: every `.gitkeep`; every output file containing a complete locked span or an unmatched lock marker; the most-recent report of each check kind (per-subject kinds like `skill-linter` per subject) plus the most-recent clean `lint` and `consistency` report; the latest `ingest` report for every source still in `1-wiki/sources/`; and everything under `forget/quarantine/` and `supersede/preserve/`. Deleting from those two preservation folders is a separate act the user must request explicitly.
- Classification verifies against the current file text and the entry's direction, not the entry's own claim about where it was added.
