# Resuming a prior session — pick up the open weak spots, retarget them

A real committee that reconvenes does not re-litigate what you nailed last time; it checks whether you closed what you didn't. This file is how the drill does the same: read the earlier session reports for this event, work out what was left open, and lead the next drill straight at those seams to see whether they have been fixed. Load it at Step 3 (build the carry-forward set), Step 5 (offer resume vs fresh), Step 6 (retarget during the drill), and Step 7 (record continuity).

## Step 3 — Scan Prior Reports and Build the Carry-Forward Set

1. **Find the prior reports.** Look for earlier report files whose event matches the current event (Step 2) in `.claude/skills/mock-defence/outputs/`. Match on the `event:` frontmatter exactly, falling back to the filename slug only when frontmatter is absent — a focus-suffixed filename (an event slug with extra words after it) is not a distinct event unless its `event:` field says so; skip the verbatim transcripts (`*-transcript.md`) — the report carries the verdicts. If the folder has no report for this event, there is nothing to resume: skip to the fresh-run path and run the drill cold, exactly as a first session does.
2. **Order newest first.** The most recent report is the current state of play; older ones add context for how a seam has behaved over time. The standing ledger (`mode: synthesis`) — every session folded into one current view, written and refreshed by the consolidation mode below — is the single best summary of where things stand; when one exists, prefer it as the spine and use the individual session reports to fill in detail. But re-confirm its seams as in step 5: the ledger can lag the latest session, so it is a starting point to re-check, not settled truth.
3. **Extract what was left open.** From each report pull the carry-forward material:
   - the `## Weak spots` section (the open seams as of that session);
   - any answer logged `untested`, `skipped`, `does not satisfy the room`, or `wobbles` in `## Questions and how they held`;
   - the conditions named in `## Room verdict` (what stood between the candidate and a clean pass);
   - the `## To read / tighten before the real thing` to-dos.
4. **Net it out.** If a later report marked a seam closed or `holds`, drop it from the open set — but a seam whose only later pass is a *coached re-attempt* (logged `Coached re-attempt` in the report, not a cold hold) is not closed: the candidate answered with the coach's pointer in view, which is recognition, not the cold recall the real room tests, so carry it forward for a cold re-test as a lower-confidence seam rather than dropping it. What remains — the still-open seams plus the unfinished to-dos — is the carry-forward set. De-duplicate seams that recur across sessions into one entry, but keep a note of how many sessions each has survived: a seam still open after two or more drills is a standing liability, and the retarget should treat it as one.
5. **Treat it as "what to re-check," not "what is still wrong."** The prior reports record the document path and date they were written against. You read the *current* document at Step 2, and the candidate may have edited it since — so a carried-forward seam may already be closed on the page. Re-confirm each against the current text before pressing it; never assert a seam is still open on the strength of an old report alone.

State the carry-forward set plainly before committee selection: how many open seams carry forward, from which prior reports, and which one cuts deepest. A matched report from which nothing could be extracted (its headings may predate the current skeleton) is reported as matched-but-unparsed, never silently counted as zero seams.

## Step 5 — Offer Resume vs Fresh

When a carry-forward set exists, fold one choice into the scope confirmation (its own `AskUserQuestion`):

- **Resume and retarget** (recommended default) — lead the drill with the open seams and re-test each, then move to fresh ground. This is the value of having a session history.
- **Fresh full drill** — ignore the history and run cold from the opening fundamentals. The right pick when the proposal was substantially rewritten since the last session (most seams may be stale) or when the user wants breadth over a focused re-test.

Recommend resume and order it first. When there is no carry-forward set, do not ask — run fresh, the same as today.

## Step 6 — Retarget During the Drill

- **Open by retargeting, not the fresh drill's cold fundamentals opening.** Open on the question that re-probes the deepest open seam — name the topic, not the prior verdict ("Take me back to X — how does the current design handle it?"), so the candidate has to re-surface the seam rather than being told where the room faulted them last time. Never recite the prior room's conclusion or its recommended fix as the opening.
- **The carry-forward set is privileged, like the prep file.** The prior report's `How to strengthen` notes and `Room verdict` conditions are stored model answers — use them only to choose which seam to press, never to voice, hint at, or grade the candidate against during questioning. The candidate must re-produce the stronger answer themselves; any comparison to the prior fix happens only out of role (the closed / improved / still open call below, the coaching addendum, or the closing verdict).
- **Re-test each carried-forward seam against the current document and the candidate's current answer**, and judge it one of three ways: **closed** (the document now addresses it, or the answer now holds and survives the counter), **improved** (better, but not yet airtight), or **still open** (unchanged). Hold the document in context so the judgement is against the text, not the old report. Deliver this closed / improved / still open call as an out-of-role verdict (the resume counterpart of the closing room verdict), not as an in-role grade voiced mid-question.
- **Raise the bar on a seam that survived a prior session.** The candidate has had time to fix it, so a verbal patch that would have passed cold is not enough now — press for the design change or the written commitment that actually closes it. Say plainly when a seam is still open after more than one drill.
- **Route each retargeted seam to the seat whose lens owns it** (the evaluation seam to the evaluation examiner, the framing seam to the chair's framing question), the same as any question — seams are document-level, so they carry even when a different committee convenes than last time.
- **Then move to fresh ground.** Once the carry-forward set is worked through, run the pressure points not yet tested in prior sessions, then end as a normal drill does — the synthesis question, the logistics close, the closing verdict. Resuming narrows the opening, it does not cap the session.

## Step 7 — Record Continuity So the Next Session Can Resume

- List the prior reports this session built on in the report's `resumes:` frontmatter, and name them in Scope.
- Record each carried-forward seam's outcome (closed / improved / still open) in the `## Carried-forward weak spots (retargeted)` section (see `references/report-format.md`).
- The session's still-open set — carried seams that did not close, plus any newly surfaced — is the `## Weak spots` section. That section is exactly what the *next* session's Step 3 scan reads, so keep it clean and current: it is the hand-off.

## Consolidation Mode — Building and Refreshing the Standing Ledger

This is a separate mode from the drill: it does not convene a committee or ask the candidate anything. Run it when the user asks to consolidate the sessions for an event into one view, or asks where they stand across all their defence runs. It reuses the scan above (Steps 1–3), then folds the reports into the standing ledger and stops — no committee selection, no drill, no transcript.

- **Fold, recomputing status — do not just union the old open-lists.** Read every session report for the event, newest first, plus the current ledger if one already exists. For each distinct seam, compute its *current* state from the latest evidence: a seam a later session or the current document has closed moves to Resolved (but a seam whose latest pass is only a coached re-attempt is not Resolved — it stays Open, flagged for a cold re-test, since that answer was produced with the fix in view); a seam still open stays in Open with its survival count (how many sessions it has now survived); a seam that first appears in the newest session is added to Open. De-duplicate seams that recur across sessions into one entry, and rank Open deepest-first.
- **Write or refresh in place.** Write the ledger to `.claude/skills/mock-defence/outputs/mock-defence-{event}-ledger.md` — a stable per-event name, `mode: synthesis`, per the skeleton in `references/report-format.md`. If the file already exists, refresh it in place: this is the one artefact the skill updates rather than versions, because it is a living view, and git preserves the prior version once the outputs are committed (between commits a refresh overwrites the only copy — commit first if the prior view matters). A refresh is never silent: state its delta to the user — which seams moved to Resolved, which newly surfaced into Open, which survival counts incremented. If the folded session reports have since been pruned, say so and do not re-emit the stale ledger as freshly recomputed. Set `updated:` to today and list every folded report in `sources:`. (This is the deliberate exception to the new-file-per-run rule, which governs immutable session reports, not the ledger.)
- **It goes stale between refreshes.** A weakness does not stay a weakness and new ones arise, so refresh the ledger after each later drill to keep it current. Until it is refreshed it can lag the latest session — which is why the Step 3 scan re-confirms each carried seam against the current document rather than trusting the ledger's open-list as settled.

## Edge Cases

- **No prior reports for the event.** Nothing to resume; run a fresh drill and write a normal report (no `resumes:` field, no carried-forward section). This is the first-session case and the unchanged default.
- **The prior report defended a different document path** (the `document:` frontmatter differs from the current one). The seams may not map onto the current text. Surface it, treat the carry-forward as advisory only, and confirm each seam against the current document before raising it.
- **Everything from last time is closed.** Say so — it is a genuine win, not an empty session — and spend the drill finding new seams rather than forcing stale ones back open. Record the closed seams in the carried-forward section and an honest, possibly stronger, room verdict.
- **A different committee convenes than last time.** Carry the seams anyway (they are document-level), routing each to the seat whose lens owns it; note in Scope that the retarget crosses committees.
