---
name: cleanup
description: Two-part housekeeping for the knowledge base's working files. (1) Memory graduation — check whether each memory-tier entry (MEMORY.md, multi-skill, or per-skill) has already graduated into its permanent home, classify it, then graduate and clear the absorbed entries. (2) Outputs cleanup — prune 2-outputs files (OS junk, superseded check reports, reports orphaned from a deleted source or skill, and aged artifacts), confirming each deletion file by file. Use when the user wants to clean up, prune, consolidate, or clear memory files or old outputs, asks what is safe to remove, whether memory has been absorbed, to graduate or move an entry, or to clear out old, superseded, orphaned, or junk reports — or as a periodic consolidation pass. Different from consistency (which counts memory entries against a soft cap and checks schema/skill drift) and forget (which removes and quarantines wiki pages); cleanup removes only memory-journal entries and 2-outputs artifacts, which git history alone preserves.
---

# cleanup

Two-part housekeeping for the knowledge base's own working files: graduate-and-clear the memory journals, and prune unneeded artifacts from `2-outputs/`. Both jobs only ever remove with the user's explicit, per-item approval.

A run does both jobs by default. The user may scope it to one ("just clean memory", "just clean old outputs").

## Purpose

Memory files (`MEMORY.md`, the multi-skill file, the per-skill files) are working journals. CLAUDE.md's graduation path says a stable rule eventually graduates into its permanent home — `MEMORY.md` for stable behavioural rules, `CLAUDE.md` for wiki-structure and schema rules, a `SKILL.md` for skill-specific procedure — after which the memory entry can be removed. A journal entry (per-skill or multi-skill) most often graduates up into `MEMORY.md`; a `MEMORY.md` entry graduates further only when it is a misfiled schema rule (onward to `CLAUDE.md`) or skill-procedure rule (onward to a `SKILL.md`) — a stable behavioural rule is already in its terminal home in `MEMORY.md` and graduates no further. The memory job finds out which entries have actually made that trip, so the journals can be pruned without quietly dropping a rule that was never captured anywhere else. An entry whose rule is already present in its permanent home is "absorbed" — the `graduated` category in Step 3, and the word the description and When To Invoke use.

The hazard the memory job exists to prevent: clearing a memory file on the assumption that "it is all in CLAUDE.md by now" when some entries are not, and one or two may even contradict the current schema. Clearing then loses live guidance. This skill replaces that assumption with a per-entry check.

`2-outputs/` is uncapped: every skill appends dated reports and artifacts there and nothing is auto-pruned, so check folders fill with superseded reports, reports outlive the source or skill they were about, and old working artifacts accumulate. The outputs job surfaces these as deletion candidates — never deleting on its own, always gating each file on the user's approval (CLAUDE.md → Safety rules: deletions are confirmed file by file, never in bulk). That per-file approval is the "deliberate user action" by which `2-outputs/` is allowed to shrink; nothing here is auto-pruned.

The memory job is the deep, on-demand counterpart to the cheap mechanical entry-counter (the `memory_file_graduation_prompt` check). That counter flags a memory file that has grown past its soft cap; this skill reads each entry and decides whether its content is already somewhere permanent.

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

The **protected set** is never a candidate, in any category: every `.gitkeep`; the most-recent report of each repeatable check kind — for the per-subject kind `skill-linter`, the most-recent report per skill, not one globally; the most-recent clean `lint` and `consistency` report (audit's actual precondition — a recent clean lint and consistency — so it survives the prune; the latest `audit` report is already kept as the most-recent of its kind, and audit writes no `result:` field of its own to test for "clean"); the latest `ingest-*-{stem}.md` report for every `{stem}` still present in `1-wiki/sources/` (it is the sole home of the deep-ingest `purpose:` recovery record); and everything under `forget/quarantine/` and `supersede/preserve/`. The `forget/quarantine/` and `supersede/preserve/` folders hold the only preserved copy of removed wiki content; deleting from either is a separate, deliberate act the user must request explicitly, not part of a sweep.

Do not read or modify `0-raw/`. `CLAUDE.md` and the `SKILL.md` files are read-only here — graduations into them are surfaced as proposals (Step 8). The write boundary is stated once in Limits.

## When To Invoke

- The user wants to clear, prune, consolidate, or clean up memory files, old outputs, or both.
- The user asks whether memory has been absorbed into MEMORY.md, CLAUDE.md, or the skills.
- The user asks what is safe to remove from the memory files or from `2-outputs/`.
- The user asks to graduate, promote, or move a memory entry into its permanent home.
- The user asks to clear out old, superseded, orphaned, or junk reports under `2-outputs/`.
- As a periodic consolidation pass when memory files or `2-outputs/` have grown.

## When Not To Invoke

- The user wants the memory entry count against the soft cap only — that is the mechanical `memory_file_graduation_prompt` check.
- The user wants to add a new memory entry. Append it directly per CLAUDE.md → Memory tiers.
- Schema or skill drift unrelated to memory. Use `consistency`.
- Removing a wiki page, source-support link, or attachment. Use `forget` — it quarantines wiki content to `2-outputs/forget/quarantine/`. This skill removes only memory-journal entries and `2-outputs/` artifacts, which git history alone preserves.

## Procedure

```text
Cleanup Progress:
- [ ] Step 1: Load this skill's memory and the permanent-home targets
- [ ] Step 2: [Memory] Enumerate every memory entry across the tiers
- [ ] Step 3: [Memory] Classify each entry against its permanent home (verify against current files)
- [ ] Step 4: [Outputs] Resolve the age threshold, scan and classify 2-outputs candidates
- [ ] Step 5: Save the combined report
- [ ] Step 6: Prepend log entry
- [ ] Step 7: Present graduation proposals and cleanup decisions
- [ ] Step 8: On approval, graduate then remove; delete approved output files; reconcile the record
```

1. **Load this skill's memory and the permanent-home targets.** Read `.claude/skills/cleanup/cleanup-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` for prior corrections to this skill. Read `MEMORY.md` and `CLAUDE.md` in full — `MEMORY.md` is the home most behavioural journal entries graduate into, and `CLAUDE.md` is where wiki-structure and schema rules land. Have the skill files ready to open as needed; a skill-specific entry graduates into its own `SKILL.md`. If the user scoped the run to one job, skip the steps for the other (memory job = Steps 2–3; outputs job = Step 4), but always do Steps 5–8 for whichever job ran.

2. **[Memory] Enumerate every memory entry across the tiers.** List the memory files:

   ```bash
   ls .claude/skills/*/*-memory.md MEMORY.md
   ```

   The `*/*-memory.md` glob already matches `multi-skill/multi-skill-memory.md` — do not also list it explicitly, or that file is enumerated twice and its cross-skill entries are double-counted.

   Also run `git status --short .claude/skills MEMORY.md` here: removed memory has no quarantine fallback, so an uncommitted entry deleted later in Step 8 is unrecoverable. Note any uncommitted memory files in the report's Bottom line and carry the warning into Step 7 before deletions are approved.

   For each file, split on H2 headings (`## ...`). Each H2 section is one entry. The intro boilerplate above the first H2 is not an entry. In `MEMORY.md`, the `## Index` heading is a table of contents, not an entry — skip it (the consistency counter does the same). A file that has body content below the intro but no `## ` heading at all is malformed (entries appended without a heading), not empty — flag it `malformed (entries without H2)` for the user; never collapse it into the empties count.

   A struck-through heading (`## ~~...~~`) is a breadcrumb left by a prior Step 8 claiming the rule graduated. Do not blindly trust the claim — it is a self-claim like any other, and the home may have moved on since. Do a lightweight presence check against the named home (the same direction-aware check as Step 3 — graduated only if the home states the entry's do/never, not merely that the subject exists): if the rule is still present, record it `already-cleared (pointer)` and do not re-propose graduation or deletion; if the rule is absent from the named home, widen the grep across `MEMORY.md` and `CLAUDE.md` before concluding it is lost, since the schema may have relocated it. If it is genuinely gone, flag it `regressed/lost` — the home dropped a rule that had graduated — and re-propose graduation to restore it; do not clear it. This is distinct from `contradicted` (active disagreement, whose remedy may be to drop the entry). If the pointer's own text carries an explicit drop-when-consolidating signal ("safe to drop", "remove in a later consolidation pass"), surface it in Step 7 as a low-priority "pointer the entry marks droppable" note rather than suppressing it.

   A file with no H2 sections is an empty template, not a cleanup target: every skill folder is required to carry its per-skill memory file (CLAUDE.md → Memory tiers), so an empty file is intact scaffolding. Record it as `empty (nothing to clear — template intact)` and collapse all empties to a single count in the report; never list them as deletion candidates. Separately, cross-check the matched per-skill files against the actual skill folders (`ls -d .claude/skills/*/`, excluding `multi-skill/` — it is not a skill folder, carries no `SKILL.md`, and holds the cross-skill journal `multi-skill-memory.md` rather than a `<skill>-memory.md`, so it is never a "missing per-skill memory file"): a skill folder with no `<skill>-memory.md` is a structural gap — note it in the report as `missing per-skill memory file` so the user can recreate the template (it is not a graduation finding, and is kept distinct from the empty-but-present case).

   Heading formats differ by tier: the journals (per-skill and multi-skill files) use dated headings, `## YYYY-MM-DD — title`; `MEMORY.md` uses topic headings with no date, `## Topic — description`. This matters for age (Step 3).

3. **[Memory] Classify each entry against its permanent home.** For each entry, first name where its content would live if graduated: `MEMORY.md` (a stable behavioural rule from a journal tier), a specific `CLAUDE.md` section (a wiki-structure or schema rule), or a specific `SKILL.md` (skill procedure). An entry in the multi-skill file is a special case: a single `SKILL.md` is never a valid home for it — CLAUDE.md forbids duplicating a cross-skill rule across per-skill files, so it graduates only into `MEMORY.md` (behavioural) or `CLAUDE.md` (schema). If the rule turns out to apply to one skill only, that is a misfiling to flag, not a `SKILL.md` graduation.

   Then open the home file and verify whether the substance is actually present. Verify against the current file text — never trust the memory entry's own claim that it "was added to CLAUDE.md", since the schema may have moved on since. Grep the target for the entry's load-bearing terms, then read the surrounding lines to confirm the rule matches, not just a keyword. **Match the entry's direction, not just its subject.** A prohibition ("never do X") or prescription ("always do Y") is graduated only if the home states that same do/never — not merely that X's mechanism exists. Many entries are about a mechanism CLAUDE.md already documents (`verified_hash`, frames, callouts); the documented mechanism does not graduate a behavioural rule about that mechanism. If the home describes the subject but not the rule's do/never, classify it not-graduated (or partial), never graduated. If the named home file or section no longer exists (a retired or renamed skill, a removed CLAUDE.md section), do not treat the rule as graduated — classify by current content: if it still applies, not-graduated against the current home; if its target is gone and the rule no longer applies, contradicted or spent. Flag the dangling reference explicitly.

   Assign each entry exactly one category — **graduated**, **partial**, **not-graduated**, **contradicted**, **keep-in-memory**, or **spent**. The full category definitions, the tie-break order when two seem to fit, the sensitive-content screen (run before proposing any graduation into `MEMORY.md`/`CLAUDE.md`), and the keep-vs-graduate-vs-delete judgement (a common-sense content call, not a frequency count — age is a hint, never a trigger) are in `references/memory-graduation.md`.

4. **[Outputs] Resolve the age threshold, then scan and classify `2-outputs/` candidates.** First fix the **age threshold** for the aged category: take it from the invocation if the user named one ("clean up outputs older than 30 days"); otherwise ask once with `AskUserQuestion`, offering 90 days marked `(Recommended)` and ordered first, then 30 / 180 days / "no age cutoff this run"; default to 90 days if the user does not pick. The threshold governs only the aged category; the other three ignore age. Run `git status --short 2-outputs/` so you know which candidates are uncommitted (git cannot recover those — they are gated individually in Step 7, like a true deletion).

   Then walk `2-outputs/` and sort each file into the first category it matches: **junk**, **superseded-check**, **orphaned-subject**, or **aged**. The category definitions, the repeatable-check-vs-working-artifact split the superseded/aged boundary turns on, the inbound-reference check to run before proposing any working artifact for deletion, and how the protected set is applied (never surfacing a `.gitkeep`, a kept-latest report, or anything under `forget/quarantine/` or `supersede/preserve/`, and recording what was skipped) are in `references/outputs-cleanup.md`.

5. **Save the combined report** to `2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md`, creating the folder if needed. Obtain the timestamp at write time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context gives the date but not the current minute. Include only the sections for the job(s) that ran. Report shape:

   ```markdown
   ---
   type: cleanup-report
   date: YYYY-MM-DD
   ---

   # Cleanup report: YYYY-MM-DD

   ## Bottom line
   - Memory — safe to clear now: <count> graduated; needs a decision: <count> (not-graduated / partial / contradicted); decisions to confirm: <count> (spent → delete; contradicted → drop / re-graduate / keep)
   - Outputs — deletion candidates: <count> (junk J / superseded-check S / orphaned-subject O / aged A); protected and skipped: <count>
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
   - Home: `MEMORY.md` (or `CLAUDE.md` → <section>, or `.claude/skills/<skill>/SKILL.md` → <step>)
   - Evidence: `file:line` showing the rule is present / absent / contradicted
   - Direction check: what the home actually states (mechanism only, or the matching do/never) vs what the entry prescribes — the basis for graduated-vs-not
   - Proposal: exact edit to graduate it (for partial / not-graduated), the contradiction to resolve, the deletion rationale (for spent), or "none — safe to clear"

   ## Outputs: cleanup candidates
   - Age threshold this run: <N days | none>

   ### junk
   - `2-outputs/<path>` — <why: OS cruft / zero-byte stray>

   ### superseded-check
   - `2-outputs/<kind>/<file>` — superseded by newer `<kept file>` (kept)

   ### orphaned-subject
   - `2-outputs/<kind>/<file>` — subject `<stem/skill>` no longer on disk

   ### aged
   - `2-outputs/<kind>/<file>` — older than <N> days

   ### protected (skipped, no action)
   - kept-latest: lint `<file>`, consistency `<file>` (clean), audit `<file>`, ...
   - preservation: `forget/quarantine/`, `supersede/preserve/`

   ## Self-report
   - {a specific limitation that bit cleanup this run — a graduation call it couldn't make, a candidate it couldn't classify, a safety gate that slowed it} → upgrade: {how the cleanup skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
   ```

6. **Prepend log entry** to `1-wiki/log.md`. Use the schema's dated-and-timed heading (`## [YYYY-MM-DD HH:MM] verb | subject`, 24-hour UTC from the same `TZ='UTC' date` call as Step 5):

   ```markdown
   ## [YYYY-MM-DD HH:MM] cleanup | memory graduation + outputs sweep
   - Saved: [[2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md|cleanup-YYYY-MM-DD-HHMM]]
   - Memory: graduated/safe-to-clear K; not-graduated C; contradicted D
   - Outputs: candidates — junk J, superseded-check S, orphaned-subject O, aged A; protected P
   - Applied (after approval): <memory clears / output deletions>, or "awaiting user"
   ```

   Name only the job(s) that ran in the subject and drop the line for the job that did not.

7. **Present graduation proposals and cleanup decisions.** Lead with the bottom line — the action lists the user acts on first.

   For the memory job, present: the "safe to clear now" (graduated) list and the "needs a decision before clearing" list (not-graduated / partial / contradicted). Then:
   - the not-graduated and partial entries, each with the concrete edit that would graduate it (exact text + target file and section);
   - the contradicted entries, each with the disagreement stated plainly, for the user to decide whether to drop the stale entry or re-graduate the rule;
   - the spent entries, each with its age and a one-line reason it has done its job and will not recur, proposed for deletion;
   - the graduated entries, listed as safe to clear, naming both removal styles up front so the user picks one as part of approval — clear the H2 section outright (git preserves it) or leave a one-line struck-through pointer to the new home;
   - empty templates as a single count (required scaffolding, no action), and any missing per-skill files to recreate.

   A `keep-in-memory` entry whose own body already states a current keep rationale is listed in the saved report but omitted from this spoken presentation marked `keep (already justified in-entry)`, so settled keeps are not re-litigated each run.

   For the outputs job, present the candidates grouped by category with the per-file rationale, and the protected-and-skipped summary so the user sees what was deliberately held back.

   **Gating — one decision per `AskUserQuestion` call, for every removal in both jobs.** Surface each removal as its own question — every graduated / spent / contradicted memory entry (clear / keep / graduate-then-delete) and every output file (junk, superseded-check, orphaned-subject, aged) — one item per call, never batched into a `multiSelect`. This keeps cleanup's gate identical to its sibling deletion skills `forget` and `supersede`, which gate one decision per call and treat recoverability (their quarantine, cleanup's git history) as lowering the stakes of a wrong call, not as licence to batch the approval; CLAUDE.md → Safety rules asks for deletions confirmed file by file, individually, not in bulk. Recoverability lowers the cost of a mistake; it does not license batching the approval. (Whether to relax this to a recoverability-gated `multiSelect` for committed, git-recoverable reports is a CLAUDE.md-level question, not one this skill settles on its own.)
   - Mark each gated choice per CLAUDE.md → Communication style: order the recommended option first and mark it `(Recommended)` — `delete` for a spent entry, `clear` for a graduated one, the proposed action for an output candidate. The `contradicted` drop-vs-re-graduate call is a genuine no-lean decision, so state "no recommendation" rather than fake a pick.
   - A declined or unticked candidate — memory entry or output file — is simply not removed: it stays resident, is recorded in the report as `kept (user declined)`, and cascades to nothing else. Declining one item never blocks approving another.

   Do not apply any `CLAUDE.md` or `SKILL.md` edit, and do not remove any memory entry or output file, without the user's explicit say-so.

8. **On approval, apply — graduate before removing for memory, then delete approved output files.**

   For each memory entry the user approved for cleanup:
   1. Apply the approved graduation edit first (to `MEMORY.md`, `CLAUDE.md`, or the `SKILL.md`), so the rule has a permanent home before the journal copy disappears; `CLAUDE.md` and `SKILL.md` edits proceed only on the user's explicit say-so (see Limits). For a `partial` entry, the graduation edit is the missing delta only (the clause absent from the home); once it lands the entry is fully graduated. A `spent` entry usually has nothing to graduate; if its one-time kernel check found a general rule, graduate that first.
   2. Re-read the home file and confirm the rule is actually present before removing anything — for **every** entry being cleared, not only the ones that got an edit this run. A plain `graduated` entry applies no edit in 8.1, so its safety rests entirely on this removal-time re-check: re-run the Step-3 direction-aware presence check against the named home right now, because an earlier graduation edit in this same Step-8 loop, or a user edit during the Step-7 approval gate, may have moved or clobbered the section since Step 3 read it. For an entry that did get a graduation edit, also confirm that edit landed — never remove on the assumption the just-applied edit matched, since a near-miss or wrong-section edit can succeed yet leave the rule un-homed. Either way the confirmation is at the specific named target section, not anywhere in the file: a grep that finds the rule's terms in some *other* section (or a near-duplicate elsewhere) does not confirm it. Confirm the rule's full do/never is present — and for a moved or paraphrased rule, that no clause the entry carried was dropped in the move (a `partial` graduation re-checks the full do/never, not only the just-added delta, in case the home's pre-existing core was weakened since). If that confirmation fails — the rule's full do/never is not present at the named target section — do not remove the entry: surface the failure to the user (retry the graduation, keep the entry as-is, or abandon the upgrade), never silently skip or proceed. Once confirmed, remove the memory entry — delete the H2 section outright, or replace it with a one-line struck-through pointer to where the rule now lives, per the style the user chose in Step 7.
   3. Preserve before removing. git history preserves the prior text — but only if that prior state is committed, and the deletion has no quarantine fallback (unlike `forget`). Two uncommitted states put the rule at risk at removal time, so re-check `git status --short` (or `git diff --quiet -- <file>`) for each affected file immediately before the removal rather than trusting the Step 2 snapshot — a file committed-clean at Step 2 can have been dirtied since (by the Step 8.1 graduation edit itself, a parallel append, or a new entry added this session). (a) The journal entry being removed: if its file is dirty at removal time, git cannot recover the deleted text — surface the caveat with the actual state and, per CLAUDE.md Safety rules, offer to commit or stash first and get the user's explicit go-ahead before removing. (b) The graduation edit just applied in 8.1: it is itself uncommitted, so if the user later discards the working tree (`git restore`/`reset`), the rule vanishes from both its new home and the deleted journal source at once. Offer to commit the graduation (and, if approved, the removal with it) so the rule is durably homed before its only other copy disappears; do not leave a graduated-then-removed rule resident only in an uncommitted working tree.

   Graduation and removal are gated separately. If the user approves the graduation edit but declines removal, apply the edit and leave the entry (optionally as a struck-through pointer). If the user declines the graduation edit, do not remove the entry — without a permanent home the rule would be lost; report it as still-resident. Never reverse the order: removal is contingent on the graduation having been applied first (or, for a spent entry with no kernel, on the deletion itself being approved).

   For each output file the user approved for deletion: re-check `git status --short` for that file immediately before deleting (a file committed-clean at Step 4 can have been dirtied or newly created since); for an uncommitted file git cannot recover, restate the caveat and, per CLAUDE.md Safety rules, offer to commit first before deleting. Then remove the file (`rm`). Deleting reports never touches the wiki pages or raw sources they describe — only the `2-outputs/` artifact. A `.gitkeep` keeps each emptied folder present in git, so pruning a folder's last report does not drop the folder from `output_kinds_match_disk`.

   **Reconcile the record (done-state).** After all approved graduations, clears, and deletions are applied, update the durable record to match disk: rewrite the log entry's `Applied (after approval):` line from "awaiting user" to what actually happened (entries cleared, files deleted, and anything the user declined and left resident), and update the report's Bottom line the same way. The run is complete only when the log and report reflect the applied state, not the pre-approval proposal — if the user approved nothing, the Applied line reads "none approved — all resident".

## Limits

- Do not read or edit raw sources; do not rewrite historical files under `2-outputs/` (the outputs job deletes whole superseded / orphaned / aged files on approval — it does not edit a kept file's contents).
- `CLAUDE.md` and every `SKILL.md` are never auto-edited — graduations into them are proposals applied only on the user's explicit say-so (Step 8). Graduations into `MEMORY.md` are ordinary agent-writable content edits, still gated on the Step 7 approval; the report and log are written without asking.
- Removing a memory entry or an output file is a deletion: gated on user approval, surfaced one item per `AskUserQuestion` call, never batched — the same one-decision-per-call model as sibling `forget` and `supersede`. Recoverability (git history, a committed prior state) lowers the cost of a wrong call but is not treated as licence to batch the approval.
- The protected set is never deleted: every `.gitkeep`, the most-recent report of each check kind (per-subject kinds like `skill-linter` per subject) plus the most-recent clean `lint` and `consistency` report, the latest `ingest` report for every source still in `1-wiki/sources/`, and everything under `forget/quarantine/` and `supersede/preserve/`. Deleting from those two preservation folders is a separate act the user must request explicitly.
- Classification verifies against the current file text and the entry's direction, not the entry's own claim about where it was added.
