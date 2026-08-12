---
name: cleanup
description: Two-part housekeeping for the wiki's working files. (1) Memory graduation check — classify each memory-tier entry (MEMORY.md, multi-skill, per-skill) against its permanent home and clear the absorbed, spent, and dropped ones; it never writes a rule into a home, so an un-graduated entry is reported with its home and the text to add, and left resident. (2) Outputs cleanup — prune 2-outputs files (OS junk, superseded check reports, reports orphaned from a deleted source or skill, aged artifacts), gating each deletion and recording every removal in the run's log entry with its last-holding commit. Use when the user wants to clean up, prune, consolidate, or clear memory files or old outputs, asks what is safe to remove, whether a rule has landed in its permanent home, or to clear out old, superseded, orphaned, or junk reports. Different from consistency (which only counts memory entries) and forget (which quarantines wiki pages); cleanup removes only memory-journal entries and 2-outputs artifacts.
---

# cleanup

Two-part housekeeping for the wiki's own working files: check-and-clear the memory journals, and prune unneeded artifacts from `2-outputs/`. Both jobs only ever remove with the user's explicit, per-item approval.

A run does both jobs by default. The user may scope it to one ("just clean memory", "just clean old outputs").

## Purpose

Memory files (`MEMORY.md`, the multi-skill file, the per-skill files) are working journals. CLAUDE.md's graduation path says a stable rule eventually graduates into its permanent home — `MEMORY.md` for stable behavioural rules, `CLAUDE.md` for wiki-structure and schema rules, a `SKILL.md` for skill-specific procedure — after which the memory entry can be removed. A journal entry (per-skill or multi-skill) most often graduates up into `MEMORY.md`; a `MEMORY.md` entry graduates further only when it is a misfiled schema rule (onward to `CLAUDE.md`) or skill-procedure rule (onward to a `SKILL.md`) — a stable behavioural rule is already in its terminal home in `MEMORY.md` and graduates no further. The memory job finds out which entries have actually made that trip, so the journals can be pruned without quietly dropping a rule that was never captured anywhere else. An entry whose rule is already present in its permanent home is "absorbed" — the `graduated` category in Step 3, and the word the description and When To Invoke use.

The hazard the memory job exists to prevent: clearing a memory file on the assumption that "it is all in CLAUDE.md by now" when some entries are not, and one or two may even contradict the current schema. Clearing then loses live guidance. This skill replaces that assumption with a per-entry check.

**cleanup detects graduation; it never performs it.** The permanent homes are maintained deliberately elsewhere — `MEMORY.md` by the user or by ordinary session work, and `CLAUDE.md` and the `.claude/skills/` folders as shared files that exist as hand-propagated copies across this wiki and its sibling repos. A rule cleanup wrote into one of those copies would either be overwritten the next time they are brought back into step or simply never reach the others, while the journal entry that carried it had already been cleared — leaving the rule nowhere it can be relied on. That is the same "quietly dropping a rule" failure the memory job exists to prevent, so the job is detection-only by construction: the journal drains on evidence that a rule has landed, never on an edit cleanup made itself. An entry that has not graduated is reported with its home and the exact text to add, and left resident for the user to promote where that home is maintained.

`2-outputs/` is uncapped: every skill appends dated reports and artifacts there and nothing is auto-pruned, so check folders fill with superseded reports, reports outlive the source or skill they were about, and old working artifacts accumulate. The outputs job surfaces these as deletion candidates — never deleting on its own, always gating each file on the user's approval (CLAUDE.md → Safety rules: deletions are confirmed file by file, never in bulk). That per-file approval is the "deliberate user action" by which `2-outputs/` is allowed to shrink; nothing here is auto-pruned.

The memory job is the deep, on-demand counterpart to the cheap mechanical entry-counter (the `memory_file_graduation_prompt` check). That counter flags a memory file that has grown past its soft cap; this skill reads each entry and decides whether its content is already somewhere permanent.

## Scope

### Memory graduation

Read and classify:

- `MEMORY.md` — stable transferable memory (each H2 section is one entry).
- `.claude/skills/multi-skill/multi-skill-memory.md` — cross-skill corrections (each H2 is one entry).
- `.claude/skills/<skill>/<skill>-memory.md` — per-skill corrections (each H2 is one entry).

Check each entry against its permanent home — each opened read-only, to see whether the rule has landed there:

- `MEMORY.md` — stable transferable behavioural rules; the home most per-skill and multi-skill journal entries graduate into.
- `CLAUDE.md` — schema and behavioural defaults (wiki-structure and schema rules).
- `.claude/skills/<skill>/SKILL.md` — skill-specific procedure.

A `MEMORY.md` entry is itself a tier being classified, but `MEMORY.md` is the terminal home for a stable behavioural rule — such a rule graduates no further and is settled where it sits. Only a rule that actually belongs elsewhere graduates onward: a wiki-structure or schema rule misfiled in `MEMORY.md` (home `CLAUDE.md`), or a skill-procedure rule (home a `SKILL.md`). A durable behavioural rule correctly in `MEMORY.md` is classified `keep-in-memory` (terminal), never `not-graduated`, and is never reported as needing a move into `CLAUDE.md`.

### Outputs cleanup

Scan `2-outputs/` and sort files into four candidate categories — junk, superseded-check, orphaned-subject, and aged — plus a fifth reported-only category, unrecognized (classified in Step 4; definitions in `references/outputs-cleanup.md`).

The **protected set** is never a candidate, in any category:

- every `.gitkeep`;
- the most-recent report of each repeatable check kind (`lint`, `consistency`, `audit`, `cleanup`) — all whole-wiki kinds, so one kept report each, globally;
- the most-recent `lint` and `consistency` report whose `result:` is `clean`;
- everything under `forget/quarantine/` and `supersede/preserve/`.

The clean-report carve-out exists because `audit`'s precondition is a recent clean lint and consistency, which the kept-latest alone does not guarantee — the newest lint may be `blocking`. `audit` writes no `result:` of its own, so its latest report is kept simply as the most-recent of its kind. A kept-latest must also be a real report: a zero-byte or unparseable file never counts as the most recent of its kind, or a crashed write would protect itself and expose the last good report to the superseded-check sweep.

The three subject-bearing kinds — `ingest`, `skill-linter`, `skill-llm-council` — have no kept-latest and are pruned by the ordinary rules: orphaned-subject when their source or skill is gone, aged out on the threshold otherwise. An ingest report is the only home of a deep ingest's non-frame `purpose:` field, so pruning it reduces that record to a log line. That cost is accepted deliberately; the fix belongs in the source-page frontmatter spec, not in a carve-out here.

The two preservation folders hold the only findable copy of removed or replaced wiki content — git history holds the bytes, but recovering from it means knowing what to look for. They are never part of any sweep, including the "everything not protected" threshold. The user may still ask to prune them by naming them exactly, which runs the preservation sub-mode in Step 4.

Do not read or modify `0-raw/`. `MEMORY.md`, `CLAUDE.md`, and the `SKILL.md` files are read-only here — an entry that has not landed in its home is reported, never written there (Step 7). The write boundary is stated once in Limits.

## When To Invoke

- The user wants to clear, prune, consolidate, or clean up memory files, old outputs, or both.
- The user asks whether memory has been absorbed into MEMORY.md, CLAUDE.md, or the skills.
- The user asks what is safe to remove from the memory files or from `2-outputs/`.
- The user asks where an un-absorbed entry should go and what text would graduate it — cleanup reports the target and the text; writing it there is the user's act.
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
- [ ] Step 4: [Outputs] Resolve the age threshold, scan and classify 2-outputs candidates (+ preservation sub-mode, if invoked)
- [ ] Step 5: Save the combined report
- [ ] Step 6: Prepend log entry
- [ ] Step 7: Present the memory findings and cleanup decisions
- [ ] Step 8: On approval, clear approved entries; delete approved output files; record every removal in the log; reconcile
```

1. **Load this skill's memory and the permanent-home targets.** Read `.claude/skills/cleanup/cleanup-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` for prior corrections to this skill. Read `MEMORY.md` and `CLAUDE.md` in full — `MEMORY.md` is the home most behavioural journal entries graduate into, and `CLAUDE.md` is where wiki-structure and schema rules land. Have the skill files ready to open as needed; a skill-specific entry graduates into its own `SKILL.md`. All three are opened only to see whether a rule is already present. If the user scoped the run to one job, skip the steps for the other (memory job = Steps 2–3; outputs job = Step 4), but always do Steps 5–8 for whichever job ran.

2. **[Memory] Enumerate every memory entry across the tiers.** List the memory files:

   ```bash
   ls .claude/skills/*/*-memory.md MEMORY.md
   ```

   The `*/*-memory.md` glob already matches `multi-skill/multi-skill-memory.md` — do not also list it explicitly, or that file is enumerated twice and its cross-skill entries are double-counted.

   Also run `git status --short .claude/skills MEMORY.md` here: removed memory has no quarantine fallback, so an uncommitted entry deleted later in Step 8 is unrecoverable. Note any uncommitted memory files in the report's Bottom line and carry the warning into Step 7 before deletions are approved.

   For each file, split on H2 headings (`## ...`). Each H2 section is one entry. The intro boilerplate above the first H2 is not an entry. In `MEMORY.md`, the `## Index` heading is a table of contents, not an entry — skip it (the consistency counter does the same). A file that has body content below the intro but no `## ` heading at all is malformed (entries appended without a heading), not empty — flag it `malformed (entries without H2)` for the user; never collapse it into the empties count.

   A struck-through heading (`## ~~...~~`) is a breadcrumb left by a prior Step 8 claiming the rule graduated. Do not blindly trust the claim — it is a self-claim like any other, and the home may have moved on since. Do a lightweight presence check against the named home (the same direction-aware check as Step 3 — graduated only if the home states the entry's do/never, not merely that the subject exists): if the rule is still present, record it `already-cleared (pointer)` and do not re-report it for promotion or deletion; if the rule is absent from the named home, widen the grep across `MEMORY.md` and `CLAUDE.md` before concluding it is lost, since the schema may have relocated it. If it is genuinely gone, flag it `regressed/lost` — the home dropped a rule that had graduated — and report the rule and its home so the user can restore it there; do not clear it. This is distinct from `contradicted` (active disagreement, whose remedy may be to drop the entry). If the pointer's own text carries an explicit drop-when-consolidating signal ("safe to drop", "remove in a later consolidation pass"), surface it in Step 7 as a low-priority "pointer the entry marks droppable" note rather than suppressing it.

   A file with no H2 sections is an empty template, not a cleanup target: every skill folder is required to carry its per-skill memory file (CLAUDE.md → Memory tiers), so an empty file is intact scaffolding. Record it as `empty (nothing to clear — template intact)` and collapse all empties to a single count in the report; never list them as deletion candidates. Separately, cross-check the matched per-skill files against the actual skill folders (`ls -d .claude/skills/*/`, excluding `multi-skill/` — it is not a skill folder, carries no `SKILL.md`, and holds the cross-skill journal `multi-skill-memory.md` rather than a `<skill>-memory.md`, so it is never a "missing per-skill memory file"): a skill folder with no `<skill>-memory.md` is a structural gap — note it in the report as `missing per-skill memory file` so the user can recreate the template (it is not a graduation finding, and is kept distinct from the empty-but-present case).

   Heading formats differ by tier: the journals (per-skill and multi-skill files) use dated headings, `## YYYY-MM-DD — title`; `MEMORY.md` uses topic headings with no date, `## Topic — description`. This matters for age (Step 3).

3. **[Memory] Classify each entry against its permanent home.** For each entry, first name where its content would live if graduated: `MEMORY.md` (a stable behavioural rule from a journal tier), a specific `CLAUDE.md` section (a wiki-structure or schema rule), or a specific `SKILL.md` (skill procedure). An entry in the multi-skill file is a special case: a single `SKILL.md` is never a valid home for it — CLAUDE.md forbids duplicating a cross-skill rule across per-skill files, so it graduates only into `MEMORY.md` (behavioural) or `CLAUDE.md` (schema). If the rule turns out to apply to one skill only, that is a misfiling to flag, not a `SKILL.md` graduation.

   Then open the home file and verify whether the substance is actually present. Verify against the current file text — never trust the memory entry's own claim that it "was added to CLAUDE.md", since the schema may have moved on since. Grep the target for the entry's load-bearing terms, then read the surrounding lines to confirm the rule matches, not just a keyword. **Match the entry's direction, not just its subject.** A prohibition ("never do X") or prescription ("always do Y") is graduated only if the home states that same do/never — not merely that X's mechanism exists. Many entries are about a mechanism CLAUDE.md already documents (`verified_hash`, frames, callouts); the documented mechanism does not graduate a behavioural rule about that mechanism. If the home describes the subject but not the rule's do/never, classify it not-graduated (or partial), never graduated. If the named home file or section no longer exists (a retired or renamed skill, a removed CLAUDE.md section), do not treat the rule as graduated — classify by current content: if it still applies, not-graduated against the current home; if its target is gone and the rule no longer applies, contradicted or spent. Flag the dangling reference explicitly.

   Assign each entry exactly one category — **graduated**, **partial**, **not-graduated**, **contradicted**, **keep-in-memory**, or **spent**. The full category definitions, the tie-break order when two seem to fit, the sensitive-content screen (run before reporting any entry's text for promotion into `MEMORY.md`/`CLAUDE.md`), and the keep-vs-graduate-vs-delete judgement (a common-sense content call, not a frequency count — age is a hint, never a trigger) are in `references/memory-graduation.md`.

   The classification produces a report line, never an edit. Naming an entry's home and the exact text that would graduate it *is* the deliverable for a `partial` or `not-graduated` entry — writing that text into the home is the user's act, wherever that home is maintained. An un-absorbed entry (`partial` or `not-graduated`) never becomes a removal candidate, so there is no in-run path by which it turns clearable.

4. **[Outputs] Resolve the age threshold, then scan and classify `2-outputs/` candidates.** If the user scoped this run to a preservation folder alone, skip straight to the preservation sub-mode below — the threshold and the `2-outputs/` walk do not apply, so asking the threshold question would be noise.

   Otherwise fix the **age threshold** for the aged category: take it from the invocation if the user named one ("clean up outputs older than 30 days", "prune everything"); otherwise ask once with `AskUserQuestion`, offering 30 days marked `(Recommended)` and ordered first, then 90 days / "everything not protected" / "no age cutoff this run"; default to 30 days if the user does not pick. A file is aged when `today − file_date ≥ threshold` in whole days, reading `file_date` from the `YYYY-MM-DD` in its filename and discarding the `HHMM`; so at 30 a file dated exactly 30 days ago is aged, and "everything not protected" sets the threshold to zero and sweeps every non-protected report including one written today. Say `≥`, not "older than", when presenting the threshold — "older than 0 days" excludes today's files and would silently spare exactly what the option promises to sweep. The protected set still holds at zero, and the preservation folders are still untouched. The threshold governs only the aged category; junk, superseded-check, and orphaned-subject ignore age entirely, so a stale check report or an orphaned review is proposed however recent it is.

   Then establish **recoverability** for every candidate: run the ignored-path pre-check and the pointer resolution script in `references/removal-safety.md` per candidate now, and record what each returns — a verified commit SHA (git-recoverable) or `uncommitted — not recoverable`. This is the run's single recoverability determination: Step 7 gates on it and Step 8 writes it, so resolve it once here and carry it forward. Do not improvise a shorter test — an empty `SHA` silently resolves to the git index, and an ignored path is indistinguishable from a committed one in `git status`.

   Then walk `2-outputs/` and sort each file into the first category it matches: **junk**, **superseded-check**, **orphaned-subject**, or **aged**; a file matching none is **unrecognized** and is reported, never proposed. The category definitions, the repeatable-check-vs-working-artifact split the superseded/aged boundary turns on, the inbound-reference check to run before proposing any working artifact for deletion, and how the protected set is applied (never surfacing a `.gitkeep`, a kept-latest check report, or anything under `forget/quarantine/` or `supersede/preserve/`, and recording what was skipped) are in `references/outputs-cleanup.md`.

   **Preservation sub-mode (opt-in only).** `2-outputs/forget/quarantine/` and `2-outputs/supersede/preserve/` are never swept. Run the sub-mode only when the user names one of those two folders exactly, and cover only the folder they named — naming a parent is not naming it, and when the phrasing is ambiguous confirm before listing anything, because the sub-mode's downside is irreversible and the ordinary sweep's is not. No plain invocation and no threshold, including "everything not protected", reaches it. The scope test, the subject-resolution rules, the two folders' differing stakes, and its gating and report slot are in `references/preservation.md`.

5. **Save the combined report** to `2-outputs/cleanup/cleanup-YYYY-MM-DD-HHMM.md`, creating the folder if needed, following the report shape in `references/report-and-log.md`. Obtain the timestamp at write time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context gives the date but not the current minute. If a report already exists for this minute, append a disambiguating suffix (`-2`, `-3`, …) rather than overwriting it; the report it would clobber is the one recording the previous run's deletions. Include only the sections for the job(s) that ran, and record the superseded predecessor in the protected list as the reference describes.

6. **Prepend log entry** to `1-wiki/log.md`, using the log entry shape in `references/report-and-log.md`. The `Applied (after approval):` and `Removed:` lines are written as "awaiting user" at this step and filled in at Step 8; the `Removed:` list is this run's permanent deletion record, whose line format Step 8.3 owns. Name only the job(s) that ran in the subject, and drop the preservation slot when the sub-mode did not run.

7. **Present the memory findings and cleanup decisions.** Lead with the bottom line — the action lists the user acts on first.

   For the memory job, present: the "safe to clear now" (graduated) list and the "left resident — not absorbed" list (not-graduated / partial). Then:
   - the not-graduated and partial entries, each naming the home it belongs in and the exact text that would graduate it, so the user can promote it where that home is maintained — a behavioural rule in this wiki's own `MEMORY.md`, a `CLAUDE.md` or `SKILL.md` rule wherever those shared files are authored before being propagated across the sibling repos. These are reported, not offered for removal: an un-absorbed entry stays resident, and no approval available in this run can clear it;
   - the contradicted entries, each with the disagreement stated plainly, for the user to decide whether to drop the stale entry or keep it resident;
   - the spent entries, each with its age and a one-line reason it has done its job and will not recur, proposed for deletion;
   - the graduated entries **carrying no flag**, listed as safe to clear, naming both removal styles up front so the user picks one as part of approval — clear the H2 section outright (git preserves it) or leave a one-line struck-through pointer to the new home;
   - the graduated entries **flagged `mis-homed` or `over-graduated`**, presented separately and *not* offered for clearing. The rule is present but in the wrong tier, or duplicated across two homes, so clearing the journal copy would leave the mis-tiered copy as the only record and destroy the evidence that a consolidation is owed. Name both locations and which one to keep (behavioural rule keep `MEMORY.md`; wiki-structure or schema rule keep `CLAUDE.md`); the entry stays resident until the user consolidates, after which a later run reclassifies it unflagged and it becomes clearable then;
   - the `regressed/lost` entries — a permanent home has **dropped** a rule that previously graduated. This is the most serious finding the memory job produces, so state it first among the memory findings and never leave it to the per-entry section alone: name the rule, the home it vanished from, and the text that would restore it. The entry stays resident; it is never a removal candidate;
   - the `hygiene`-flagged entries, each as its own gated decision (below);
   - empty templates as a single count (required scaffolding, no action), any `malformed` files (entries appended without an H2 heading) for the user to repair, and any missing per-skill files to recreate.

   **Hygiene-flagged entries are acted on, not merely reported.** An entry the Step 3 sensitive-content screen flags carries content CLAUDE.md → Memory hygiene forbids the repo to hold, so leaving it resident is not a neutral outcome — the violation persists in a file every run of that skill reads. Its text is never reported for promotion. Instead put it to the user as its own `AskUserQuestion` with three options and no recommendation (the right call depends on content only the user can weigh): **redact in place** (rewrite the entry to keep its rule while removing the sensitive specifics — the one case where this skill edits a journal entry's text rather than removing it), **remove the entry outright**, or **leave it and decide later**. Whichever is chosen, do not report the entry's text anywhere in the saved report; refer to it by heading alone.

   A `keep-in-memory` entry whose own body already states a current keep rationale is listed in the saved report but omitted from this spoken presentation marked `keep (already justified in-entry)`, so settled keeps are not re-litigated each run.

   For the outputs job, present the candidates grouped by category with the per-file rationale, and the protected-and-skipped summary so the user sees what was deliberately held back. List any `unrecognized` files separately as a reported-only group, with no gate and no proposal. Say that every approved deletion is recorded in this run's log entry with the commit that last held it, so the sweep stays reversible by lookup.

   **Gating — recoverability decides the shape of the call.** CLAUDE.md → Safety rules requires deletions confirmed file by file, with one carve-out it applies to `forget`, `supersede`, and `cleanup` alike: git-recoverable copies may be confirmed as a single `AskUserQuestion` multiSelect batch, because git preserves each and any one can be restored. Apply that split by the Step-4 recoverability finding, not by category:
   - **An output file the Step 4 determination marked git-recoverable** — batch these in one multiSelect per category, each row naming the file and its rationale.
   - **Any other output file** — not git-recoverable by that determination, or a preservation-sub-mode file of either folder. One item per `AskUserQuestion` call, never batched. Preservation files are held to per-file confirmation whatever their git state, because each is the only findable copy of a page's content or prior view.
   - **Every memory entry** — one per call, whatever its git state. The clear-vs-keep-vs-delete decision differs per entry rather than sharing one rationale, so a batch would collapse distinct judgements into a single tick.

   These three are exhaustive and ordered: an output file takes the first bullet only on a positive git-recoverable determination, so anything unresolved or ambiguous falls to the second and is gated individually. When in doubt, do not batch.
   - Mark each gated choice per CLAUDE.md → Communication style: order the recommended option first and mark it `(Recommended)` — `delete` for a spent entry, `clear` for a graduated one, the proposed action for an output candidate. Two calls are genuine no-lean decisions where you state "no recommendation" rather than fake a pick: the `contradicted` drop-vs-keep call, and every preservation-sub-mode file.
   - A declined or unticked candidate — memory entry or output file — is simply not removed: it stays resident, is recorded in the report as `kept (user declined)`, and cascades to nothing else. Declining one item never blocks approving another.

   Do not remove any memory entry or output file without the user's explicit say-so. No approval offered here unlocks a graduation — an un-absorbed entry has no approve-and-promote option to present (see Limits).

8. **On approval, apply — resolve each recovery pointer, then remove, then reconcile.**

   Only **unflagged** `graduated` entries, `spent` entries, a `contradicted` entry the user chose to drop, and a `hygiene`-flagged entry the user chose to redact or remove reach this step. Everything else stays resident whatever the user approves:
   - `not-graduated` and `partial` — not fully absorbed, so there is no home to clear against.
   - `graduated` flagged `mis-homed` or `over-graduated` — the rule sits in the wrong tier or in two homes at once. Clearing the journal copy here would leave the mis-tiered copy unchallenged and erase the record that a consolidation is owed, so a flagged entry is not clearable however it was ticked. If one reaches this step, treat it as a mis-gate: leave it resident and say so.
   - `regressed/lost` — the home dropped the rule, so the journal copy is now the only surviving statement of it. Removing it would complete the loss.

   **8.0 — Resolve every recovery pointer first, while the content still exists.** This precedes all removals in this step: once a file is deleted or an entry excised there is nothing left to verify a pointer against, and every removal line would degrade to `uncommitted — not recoverable`. Step 4 already resolved a pointer per approved removal — carry those forward rather than recomputing, since nothing between Step 4 and here changes a committed blob. Where a pointer reads `uncommitted — not recoverable`, say so at the moment of removal and, per CLAUDE.md → Safety rules, offer to commit first. The script, the four guards that make it correct, and the containment variant that replaces byte-equality for a memory file are in `references/removal-safety.md`.

   **8.1 — For each memory entry the user approved for clearing**, in these three moves:
   1. Re-read the home file and confirm the rule is actually present before removing anything. cleanup applied no edit anywhere this run, so the entry's safety rests entirely on this removal-time re-check: re-run the Step-3 direction-aware presence check against the named home right now, because a user edit during the Step-7 approval gate, or a propagation of the shared files landing mid-run, may have moved or clobbered the section since Step 3 read it. The confirmation is at the specific named target section, not anywhere in the file: a grep that finds the rule's terms in some *other* section (or a near-duplicate elsewhere) does not confirm it. Confirm the rule's full do/never is present, and that no clause the entry carried was dropped where the home paraphrases or relocates it. If that confirmation fails — the full do/never is not present at the named target section — do not remove the entry: reclassify it (`not-graduated`, `partial`, or `regressed/lost`), report it as still-resident, and never silently skip or proceed. Two categories have no home to confirm against: a `spent` entry never had one, and a dropped `contradicted` entry is being removed precisely because the home disagrees with it. For both, the user's approval to remove is the whole gate.
   2. Preserve before removing. git history preserves the prior text — but only if that prior state is committed, and the deletion has no quarantine fallback (unlike `forget`). The 8.0 pointer for this entry is that determination. If it reads `uncommitted — not recoverable`, surface the caveat with the actual state and, per CLAUDE.md Safety rules, offer to commit or stash first and get the user's explicit go-ahead before removing.
   3. Remove or redact the memory entry. For an unflagged `graduated` entry, either style the user chose in Step 7 applies — delete the H2 section outright, or replace it with a one-line struck-through pointer to where the rule now lives. A `spent` or dropped `contradicted` entry has no home to point at, so it is deleted outright. For a `hygiene`-flagged entry the user chose to **redact**, rewrite that entry in place so its rule survives and the sensitive specifics do not, changing nothing else in the file; this is the sole case where cleanup edits an entry's text rather than removing it, and the rewritten entry keeps its original category for a later run to act on.

   A declined entry simply stays resident. For a `graduated` entry the rule already lives in its home before this step begins, so clearing the journal copy never leaves a rule un-homed — under detection-only that ordering is structural, not something each run has to arrange. The other two are removals of content that was never homed (`spent`) or that the home actively disagrees with (dropped `contradicted`); for those git history is the only preservation, which is what makes 8.2's committed-state check their gate.

   **8.2 — For each output file the user approved for deletion:** read its 8.0 pointer; if it is `uncommitted — not recoverable`, restate the caveat and, per CLAUDE.md Safety rules, offer to commit first. Then remove the file (`rm`). Deleting reports never touches the wiki pages or raw sources they describe — only the `2-outputs/` artifact. A `.gitkeep` keeps each emptied folder present in git, so pruning a folder's last report does not drop the folder from `output_kinds_match_disk`.

   **8.3 — Record every removal in this run's `log.md` entry.** git history preserves what this skill deletes, but only if a reader knows what to look for — a path and a commit. `1-wiki/log.md` is already the permanent, complete record of every operation, so the removal record goes there rather than into a separate file: fill in the `Removed:` sub-list of the Step 6 entry, one line per removal, from both jobs, output files and cleared memory entries alike. No kind is exempt — whether an artifact will be wanted again is not knowable at deletion time, and a line costs nothing against a lost report. The line format, and what keeps a removal findable once the report itself is gone, are in `references/removal-safety.md`.

   **8.4 — Reconcile the record (done-state).** After all approved clears and deletions are applied, update the durable record to match disk: rewrite the log entry's `Applied (after approval):` and `Removed:` lines from "awaiting user" to what actually happened (entries cleared, files deleted, removal lines written, and anything the user declined or that was left resident as un-absorbed), and update the report's Bottom line, summary counts, and any per-entry finding reclassified at 8.1 the same way. The run is complete only when the log and the report both reflect the applied state — if the user approved nothing, the Applied line reads "none approved — all resident" and the `Removed:` list stays empty.

## Limits

- Do not read or edit raw sources; do not rewrite historical files under `2-outputs/` (the outputs job deletes whole superseded / orphaned / aged files on approval — it does not edit a kept file's contents).
- cleanup never writes a rule into a permanent home (the reason is in Purpose). `MEMORY.md`, `CLAUDE.md`, and every `SKILL.md` are read-only to this skill — it opens them only to check whether an entry's rule has already landed. An entry that has not landed is reported with its home and the text that would graduate it, and left resident; promoting it is the user's act. This skill's only writes are the report and the log entry (which carries the removal record), and — on approval — the removal or redaction of a memory entry, or the removal of an output file. The report and log are written without asking.
- Removing a memory entry or an output file is a deletion, gated on user approval. Verified git-recoverable output files may be confirmed as one multiSelect batch per category, per CLAUDE.md → Safety rules; everything not git-recoverable, every preservation-sub-mode file, and every memory entry is one item per `AskUserQuestion` call.
- Every removal, of every kind and from both jobs, is recorded in this run's `1-wiki/log.md` entry with the commit that last held it. That record is what makes git history a usable archive rather than a theoretical one, so it is written on the same pass as the removal, never deferred and never selective by kind.
- The protected set is never deleted: every `.gitkeep`, the most-recent report of each whole-wiki check kind (`lint`, `consistency`, `audit`, `cleanup`) plus the most-recent clean `lint` and `consistency` report, and everything under `forget/quarantine/` and `supersede/preserve/`. No protection is subject-scoped: `ingest`, `skill-linter`, and `skill-llm-council` have no kept-latest, and every report of all three is pruned by the ordinary orphaned-subject and aged rules.
- The preservation folders are pruned only through the opt-in sub-mode the user invokes by naming them; they are never swept, including under "everything not protected".
- An `unrecognized` file is reported, never proposed for deletion. cleanup resolves a file's kind from its folder and its date from its filename; where either fails, it cannot judge the file and does not gate it.
- Classification verifies against the current file text and the entry's direction, not the entry's own claim about where it was added.
