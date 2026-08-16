# Handoff prompt — paste into a fresh session

Everything below the line is the prompt. It is written to be self-sufficient: a new session needs no other context.

This supersedes `2-outputs/skill-llm-council/HANDOFF-next-session-prompt.md` (2026-08-15). Do not follow that file — several of its findings were refuted, and acting on two of them would break working rules. It also violates the output naming convention and should be deleted once you have read this one; ask the user before removing it.

---

Repo: `sheilaschoepp/llm-wiki`, branch `claude/new-session-il7quk` (HEAD `0218662`). Working tree clean. Do not touch `llm-wiki-mas` — it is read-only reference.

Note the branch name. An earlier handoff named `claude/llm-wiki-skill-upgrades-v4kwju`; the work continued on `claude/new-session-il7quk`, which carries the full history. Develop and push there unless the user says otherwise.

State: 296 tests pass. All six skill scanners (`check_structure`, `check_h2_case`, `check_internal_refs`, `check_musts`, `check_synonyms`, `check_kwargs`) return zero findings across all fourteen skills. `check_wiki.py 1-wiki` returns `[]`. `check_consistency.py .` returns exactly one finding — the stale handoff filename named above, which predates this work.

**Your job is one thing: run a full `skill-llm-council` on `ingest`.** Do not also attempt `lint` and `consistency`. Read "Why only one council" below before deciding otherwise.

## Background — what the last two sessions did

The session of 2026-08-15 ran a complete council on `audit` (`2-outputs/skill-llm-council/skill-llm-council-2026-08-15-1617-audit.md`), then started one on `ingest` and got through Step 2 only: ten advisors returned, but peer review, both chair syntheses, the meta-chair reconciliation, and the refuter gate never ran. It recorded eleven findings it had verified but deliberately not applied, because each changed a verification gate rather than fixing a contradiction.

The session of 2026-08-16 put those eleven through an adversarial refuter gate and applied what survived. Its report is `2-outputs/skill-llm-council/skill-llm-council-2026-08-16-1950-held-findings-refuter-gate.md` — read it before briefing the council, because it is the current state of the spec the council will review.

Six of the eleven were refuted. Two would have made things worse:

- The flagship finding proposed requiring a verbatim quote from every refuter returning `holds`. At the Tier-3 default the refuter is required to recompute a claim's whole set cold, explicitly *not* the cited cell — so demanding a quote demands the one artifact the spec names as distortion-certifying. It would have manufactured the failure it closed. What shipped instead is one proof-of-read per refuter per batch.
- Another alleged that `ingest` Step 4's replaced-attachment parenthetical inverts the added-versus-changed hash asymmetry. It does not. The parenthetical's consequents chain to the *unmarked* state — an image swap leaves the prose byte-identical, so the hash cannot detect it and lint cannot catch an omitted mark, which is why the mark is mandatory. Applying the proposed fix would have inverted a correct rule.

## Job — the `ingest` council

Run the full protocol, with `.claude/skills/multi-skill/references/verification.md` as the brief's central subject. That spec is run by `ingest`, `query`, `synthesis`, and `supersede`, and bound in part by `audit`, so every word added to it is paid five times — make the council reason about that cost explicitly.

**Targeting constraint:** `.claude/skills/multi-skill/` has no `SKILL.md`, so the council skill cannot resolve it as a target and its auto-apply is scoped to skill folders by construction. Target `ingest` and pass the shared spec as central context; findings against it come back as cross-file proposals.

**Brief the council on current state, so it does not re-litigate settled ground.** Five gate changes landed in `verification.md` on 2026-08-16:

1. A `holds` verdict now owes a proof-of-read once per batch — one verbatim quote plus physical page for any one held claim — which the orchestrator re-greps. Deliberately not per-claim.
2. Where Tier 1 and Tier 3 overlap, Tier 3 governs. Previously a cited number stopped at Tier 1 and bought one refuter instead of three, held there only by the self-graded word "low-stakes".
3. Setting Status condition 2 now states that on a page entering the run non-`verified`, the inherit route is unavailable, so a pre-existing unmarked claim cited to the raw this run read is the run's to certify or fix. This resolved a contradiction with `ingest/references/existing-mode.md`.
4. A refuter quote read off a figure crop is no longer discarded as unre-greppable; the orchestrator opens the crop, and an unconfirmable quote marks the claim rather than certifying it.
5. "No refuters, no stamp" — where refuters cannot be spawned at all, nothing above Tier 0 is certified and the page finishes at `draft`.

Also: the two ingest report templates moved out of the shared spec to `.claude/skills/ingest/references/report-shapes.md` (778 words four other callers loaded and never used).

## Known-open items the council should either resolve or leave alone

Each was measured, not guessed.

- **The pre-write gate is misplaced.** `ingest/SKILL.md`'s checklist lists it between Steps 3 and 4, but its text lives inside Step 5. Real, and deferred purely on budget: `ingest/SKILL.md` is at **6497 of 6500** body words and the fix needs about four. Any addition must be paid for with a measured cut. Step 4 does back-reference the gate ("only after the Step 5 clean-working-tree gate"), so it is discoverable today.
- **The audit batching paragraph.** An earlier handoff called `audit/references/verification-spec.md`'s batching paragraph a near-verbatim duplicate of the shared spec's, suggesting a pointer swap. It is not a clean duplicate — the audit copy carries an extra constraint (the explicit per-claim verdict rule) that the shared spec keeps in a *different* bullet, plus a cross-reference to `apply-fixes.md`. A pointer swap would drop material. This needs a real decision about where the per-claim verdict rule belongs, not a deduplication.
- **The `ingest` description.** Currently **1010 of 1024** characters. A rewrite adding a `read` trigger and the reingest boundary against `supersede` was once measured at 991 characters but never applied, and never re-measured. Re-measure before trusting that number.
- **Stale consistency finding.** `2-outputs/skill-llm-council/HANDOFF-next-session-prompt.md` breaks the output naming pattern. Introduced by commit `3d2c16f`. It is a user-authored document, so ask before renaming or deleting.

## Why only one council

The evidence in this repo is that a full council consumes about a session. The 2026-08-15 session completed one on `audit`, then started the `ingest` one and stopped a third of the way in. The 2026-08-16 session spent itself on the refuter gate over eleven findings and correctly declined to start a council on the remainder.

A council does not fail loudly when context runs short — it degrades at the meta-chair stage, which is exactly where its value is. Reconciliation is what catches three advisors converging on the same wrong edit. A thin reconciliation produces confident-looking output that nobody re-derives, which is worse than no council. So: `ingest` only. Leave `lint` and `consistency` — neither has ever had a council, both were changed on 2026-08-15, and both deserve a session each.

## Process notes — these were paid for twice, do not rediscover them

- **The refuter gate earns its cost, repeatedly.** Across three sessions it has killed 5 of 10 council proposals, 3 of 8 of one session's own applied changes, and 6 of 11 held findings. Never skip it. Never treat council consensus as corroboration: in one case three of ten advisors converged on the same wrong edit and only a peer reviewer caught it.
- **Vary the refuter's angle, not just the reader.** Three refuters given the same prompt buy less than three given different attack surfaces. The 2026-08-16 gate used redundancy ("is this already covered?"), harm and cost ("assume the defect is real, attack the fix"), and misreading ("does the defect exist as described?"). Each caught findings the others missed. The redundancy angle alone would have wrongly killed a real contradiction; the cost angle alone would have wrongly cleared the tier-overlap bug.
- **When refuters disagree on a textual question, settle it against the file, not by vote.** Two refuters reached opposite conclusions on whether Tier 3's "every other claim" resolves a tier overlap safely. Reading the text directly settled it — the tiers read in order, so a claim matching Tier 1 stops there. Counting verdicts would have got it backwards.
- **An advisor's measurement is a claim to check.** This has now bitten three times. Most recently a refuter quoted `ingest` at 6528 words and `audit` at 6501 — `wc -w` figures including frontmatter, where the checker counts *body* words only (6497 and 6458). State the measurement method in the prompt whenever you ask an agent to reason about a budget.
- **Simulate before enabling a dormant check.** `check_reference_depth_and_toc` was dead repo-wide (all fourteen skills cite references as backticked inline-code paths; none uses a Markdown link, which is all that check collected). The naive fix looked obviously correct and would have fired ~15 findings against architecture the schema explicitly prescribes. It needed two exemptions — shared `multi-skill/` targets, and siblings `SKILL.md` already cites directly. A dead check's true-positive yield is unknown until measured.
- **Never `str.replace` a Markdown line without its leading indent.** A past session cut a bullet with a pattern omitting the indent; the replace left orphaned spaces that merged with the next line and silently demoted a top-level rule to a sub-bullet. No scanner caught it.
- **Word budgets are tight.** `ingest/SKILL.md` 6497/6500, `audit/SKILL.md` 6458/6500. Measure with the checker's method (body words, frontmatter excluded), not `wc -w`. A pure move to a reference must land in a file that actually *owns* the material — a refuter once rejected a relocation because the destination list was scoped to a different case.
- **No available agent type has an exact Read/Glob/Grep toolset.** `Explore` is closest (no Edit/Write/NotebookEdit) but reads excerpts by default, so instruct full reads explicitly. Record the deviation in the report.
- **`git log` settles disputed rules.** One refuter resolved a severity question by finding a value flipped in a commit whose entire message was `u`, which deleted the rationale docstring — evidence no amount of reasoning from current files would have produced.

Commit and push to `claude/new-session-il7quk` as you go; do not open a PR unless asked.
