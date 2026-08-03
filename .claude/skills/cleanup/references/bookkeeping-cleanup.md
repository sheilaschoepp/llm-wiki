# cleanup — Wiki Bookkeeping Classification (Step 5)

How the bookkeeping job handles the three wiki bookkeeping files. SKILL.md Step 5 resolves the archive cutoff and runs the scan; this file holds what each file's job actually is, the archival mechanics, and the conservation check that makes an archival move safe. The memory and outputs jobs never load this.

## Contents

- What Lint Already Owns
- `log.md` — Age-Based Archival
- `hot.md` — Stale Thread And Watchlist Review
- `index.md` — No Archival Job
- Archive File Format And Placement
- Why Archival Is Not A Deletion

## What Lint Already Owns

Do not duplicate these — lint fixes them mechanically every run, and a second skill proposing the same edit produces conflicting fixes:

- `index_missing_entry` / `index_stale_entry` — index drift in both directions, plus `missing_index`.
- `hot.md` Recent-activity five-entry trim (the retention policy CLAUDE.md owns) and Open-threads pruning when the target page **no longer exists**.
- `chronology_missing_time` / `chronology_out_of_order` and the `sort_chronology.py` re-sort, over `log.md` and `hot.md` Recent activity.

The bookkeeping job covers only what none of those reach: `log.md`'s unbounded growth, and a `hot.md` thread that is stale **while its target page still exists**.

## `log.md` — Age-Based Archival

`log.md` is the permanent, complete record of every operation, so nothing may delete from it. It also never shrinks — no skill trims it — so it grows without bound. Archival resolves both: entries move to a dated archive file and remain part of the record, and the live log keeps a recent working window.

**Cutoff.** Default 90 days before the run date; the user may name another. An entry is archivable when the date in its `## [YYYY-MM-DD HH:MM] verb | subject` heading is strictly older than the cutoff.

**Entry boundaries.** An entry runs from its `## [` heading through the line before the next `## [` heading, or to end of file. Blank lines and the trailing report link belong to the entry above them. Mask fenced (``` or ~~~) and indented code blocks before splitting: a `## [` line inside one is quoted text, not a heading. Splitting on it invents an entry from the tail of a live one, and every conservation part still passes because they measure the same mis-parse. Record each masked line in the report as `quoted-heading (not split)`.

**Undated and unparseable entries are never archived.** An entry whose heading carries no parseable `YYYY-MM-DD` is recorded `unclassified-blocked` and left in the live log — never guessed at, never archived on file position. An entry with a date but no `HH:MM` is archivable on its date alone (its missing time is `lint`'s `chronology_missing_time` to recover, not this job's to invent).

**Grouping.** Group archivable entries by the entry's own year and month into `1-wiki/archive/log-YYYY-MM.md`. An entry's destination is fixed by its own heading date, never by the run date, so re-running the job is idempotent in placement.

**Order.** Newest-first inside each archive file, matching `log.md`. When a run archives into a month file that already exists, merge and re-sort that file newest-first — the one and only time an archive file is re-sorted.

**Conservation check — run on the planned partition before anything is proposed, again against the approved partition before any write, and once more against the final on-disk state. A failure at either of the first two checkpoints aborts the archival before anything moves. The third runs after every write has landed, including the `log.md` rewrite, so nothing remains to abort and a failure there is not the recoverable duplication the resume path handles — that state exists only between the archive write and the log rewrite. A failure at the third checkpoint means an entry was lost or a pre-existing archive was clobbered. Report it as blocking, name the entries whose accounting does not balance, state that the loss is recoverable from git and not by re-running, and write nothing further:**

1. `archivable count + retained count + unclassified-blocked count == original entry count` — three terms, matching the three-way partition. Blocked entries stay in the live log and are counted in their own right, so a log carrying an undated entry is still archivable.
2. The multiset of `(heading, body digest)` pairs is preserved. Digest each entry's exact bytes, bounded as above, when the log is parsed; the multiset over the planned destination (retained entries staying in `log.md`, archivable entries placed in their archive files) must equal the original's, and the multiset recomputed from disk after the writes must equal it again. The planned half is computable with no disk read and no write, so the guarantee exists before the single approval in Step 8; the disk recomputation confirms it rather than standing in for it. A multiset, not a set: two entries logged in the same minute with the same verb and subject share a heading string, and a set comparison would pass while one of them was dropped. A heading match alone never proves the body survived.
3. No retained **dated** entry is older than the cutoff, and no archived entry is newer. Unclassified-blocked entries carry no date and are exempt from this part.
4. Every entry already in a destination archive file before this run is still in it afterwards — snapshot each touched archive's `(heading, body digest)` multiset before writing and re-check after. Parts 1-3 range only over `log.md`'s own entries, so a clobbered month file would otherwise pass them all.

**Write order.** Write and verify every archive file on disk **first**, then rewrite `log.md`. Never the reverse: a crash between the two must leave the record duplicated, never dropped.

**Resuming an interrupted run.** The duplicated state that write order deliberately leaves is recoverable, and this is how. An entry present in both `log.md` and its destination archive means a previous run wrote the archive and stopped before the log rewrite. Confirm the archived copy's digest matches the live one, treat that entry as already archived, and finish the interrupted log rewrite. Do not append it again, and do not read the duplication as a conservation failure — it is the expected intermediate state, not evidence of loss. Parts 1-3 range over `log.md`'s own entries, so once the duplicate is carried as already-archived the destination multiset holds exactly one copy and equality still holds.

**Pointer block.** `log.md` carries one pointer line listing each archive file as a path-qualified wikilink, so the full record stays navigable. It sits below the H1 and the description line beneath it, above the first `## [` entry — not between the H1 and its own description. A later run replaces that single line in place rather than adding a second:

```markdown
Older entries: [[1-wiki/archive/log-2026-06.md|log-2026-06]], [[1-wiki/archive/log-2026-07.md|log-2026-07]]
```

**Log archives are frozen.** Once written, a log archive file is never re-linted for chronology, never re-archived, and never edited except by the merge-and-re-sort above. A stale-path repair (CLAUDE.md → Stay In Your Lane) is still allowed, as in any file.

## `hot.md` — Stale Thread And Watchlist Review

Scope is `Open threads` and `Watchlist` only. `Recent activity` is lint's five-entry cache trim, and `Active focus` is user-owned — never touched.

Lint auto-removes an **Open-threads** bullet whose target page is **gone**; a Watchlist bullet with a missing target it only surfaces as a `hot_log_stale` Info finding, never prunes. What lint will not do at all is judge a bullet whose target page still exists but whose thread is finished. That judgement is this job's, and it is a judgement — so every removal is gated per item and none is ever automatic.

Signals that a thread may be stale. Each is a hint; none is a trigger on its own, and a bullet is proposed only when the run can state why:

- A synthesis page now answers the question the thread poses (search `1-wiki/syntheses/` for the thread's topic).
- Every page the thread names has reached `status: verified`, so the open work it tracked is closed.
- No `log.md` entry has touched the thread's subject since the cutoff. Corroborating only — never the deciding signal: a thread nobody has worked on is exactly what an open backlog item looks like.

**Removed bullets are archived, not deleted.** CLAUDE.md is explicit that Open threads and Watchlist "hold unique orientation that is not duplicated in `log.md`" — so unlike a Recent-activity line, removing one loses the only copy outside git history. Append each removed bullet verbatim to `1-wiki/archive/hot-YYYY-MM.md` (the run's year-month), under a dated heading naming the section it came from, before removing it from `hot.md`.

## `index.md` — No Archival Job

`index.md` is a live catalog: every entry maps to a page that exists, and lint keeps it synchronized in both directions. Its length is proportional to the wiki, not accumulated cruft, and archiving entries would break the catalog it exists to be. **The bookkeeping job never edits `index.md` and never archives from it.**

Its only role here is reporting the one class lint's drift checks cannot see: a **duplicate** listing of the same page. `check_index_drift` builds its listed set as a set comprehension, so a page listed twice collapses to one and never drifts; an unparseable line, by contrast, simply yields no link and falls through to `index_missing_entry`, which lint does flag. Record a duplicate listing `unclassified-blocked` for manual review. Report it; do not fix it.

## Archive File Format And Placement

All archives live in `1-wiki/archive/`. The folder exists and is already listed in CLAUDE.md's Directory Structure tree, so archives are tree-legal and `consistency`'s `dir_tree_drift` is clean on them. If that tree entry is ever removed, restoring it is a root-level proposal for the user, never an autonomous edit (CLAUDE.md is soft read-only).

Archive files are not wiki pages: they carry no frontmatter at all, no callouts, and no `status:` — the H1 and lead paragraph below are ordinary markdown, not frontmatter. Lint enumerates pages only from `sources/`, `concepts/`, `entities/`, and `syntheses/`, so an archive file is never linted as a page and never belongs in `index.md`.

Header for a log archive (`log-YYYY-MM.md`):

```markdown
# Log archive: YYYY-MM

Archived from [[1-wiki/log.md|the log]] on YYYY-MM-DD. Entries are newest-first, verbatim, and part of the permanent record — this file is frozen except for a later merge into the same month.
```

Header for a hot archive (`hot-YYYY-MM.md`) — a different file with a different grouping key, the run's month rather than the entry's, appended to by any run in that month:

```markdown
# Hot archive: YYYY-MM

Open-threads and Watchlist bullets retired from [[1-wiki/hot.md|the hot cache]] during YYYY-MM. Each is verbatim, under a dated heading naming the section it came from.
```

Naming: `log-YYYY-MM.md` and `hot-YYYY-MM.md`, kebab-case lowercase. Archive files are not pages, so CLAUDE.md → Page Filenames does not reach them; this job holds them to the same shape anyway.

## Why Archival Is Not A Deletion

A log archival moves entries between files inside the repo. Nothing leaves, the record stays complete as the union of live plus archives, and the conservation check proves it before `log.md` is rewritten. So it does **not** take the per-file deletion gate: it takes **one** confirmation for the whole operation, showing the cutoff, the entry counts, and every destination path.

A `hot.md` thread removal is also archived first, so it is likewise a move rather than a loss — but which thread is stale is a judgement the check cannot make, so it stays **per item**, like a memory-entry clear. The distinction is what is being approved: for the log it is a date-mechanical bulk move the user can verify by count, and for a thread it is a per-bullet editorial call.

Neither ever runs without approval, and `index.md` is never written at all.
