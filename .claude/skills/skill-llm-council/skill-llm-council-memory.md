---
type: memory
skill: skill-llm-council
updated: 2026-08-16
---

# Skill-llm-council memory

Corrections, rewrites, and scope adjustments specific to the `skill-llm-council` skill. Read at the start of every skill-llm-council operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

## 2026-08-16 — A measurable claim is applied by a script that asserts it, never by an agent that states it

Five character-count errors across three councils today, and the last one was made by a *refuter* — the mechanism that had just caught the previous four.

- Two `lint` advisors and two peer reviewers reported "11 lines exceed the 79-char limit"; `pyproject.toml` sets 88 and the longest line was 87.
- A `consistency` advisor proposed a description rewrite "at 1015 chars"; a peer reconstructed it at 1054, over the hard 1024 cap.
- The refuter that caught that then certified its own replacement at 1018. Measured: 1029. It would have breached the cap had it been applied on the refuter's word.
- Three separate agents reported three different word counts for the same `checks.md` (1343 / 1469 / 1503).

The pattern is not carelessness in one agent; it is that a number stated in prose carries no more evidence than a guess, however many agents restate it. So: when an edit's correctness IS a measurable quantity, apply it with a script that asserts the quantity and fails loudly, and never accept a count — from an advisor, a peer, or a refuter — as grounds to apply.

## 2026-08-16 — Put every measurement in a task brief in the unit the finding will be argued in

I told the `consistency` structure reviewer that `references/checks.md` was "49 lines vs lint's 111 lines / ~6900 words", which reads as a 4x density gap. Both files are one-line-per-bullet, so lines measure nothing; per-check the real ratio is ~56 vs ~110 words. The advisor caught it and corrected the brief rather than inheriting it — but a brief carrying a wrong premise can manufacture a finding that then survives peer review because everyone downstream shares the premise.

Compute every number that goes into a brief, and state it in the unit the resulting finding will actually be argued in.

## 2026-08-16 — The refutation rate is a tuning signal, not a cost of doing business

Three full councils today: `ingest` (9 of 15 held), `lint` (8 of 13, twelve distinct claims refuted), `consistency` (3 of 9 held). Roughly half to two-thirds of load-bearing proposals do not survive an adversarial read, and several fell to facts a single grep would have surfaced *before* the proposal was written.

Two things follow. First, treat chair change-sets as candidate lists and never apply a load-bearing edit that skipped the gate. Second — the actual fix — require each advisor to name, for its strongest finding, the one check that would falsify it, and to report the result of running that check. The gate is currently doing work the advisors should have done.


## 2026-08-16 — Shared-premise convergence is not evidence; verify the one fact a cluster rests on

The `lint` council produced two false findings that multiple independent agents agreed on, and each fell to a single dissenter who opened a config file.

- Four agents (two advisors, two peer reviewers) reported "11 lines exceed the 79-char limit". `pyproject.toml` sets `line-length = 88`; the longest line is 87. The peer reviewers "verified" it by re-counting the same eleven line numbers — nobody checked the limit. The premise came from `coding-best-practices.md` *recommending* 79.
- Three of five C1 peers agreed a `checks.md` severity misfiling "drops findings off audit's worklist". Report tiers render from the script's JSON severity, not from where `checks.md` files the bullet, so nothing was dropped. Only the fifth reviewer traced the rendering path.

Both clusters shared one unchecked premise. Agreement across agents that inherited the same premise carries no independent information. When a convergent cluster forms, identify the single checkable fact underneath it and check that, rather than counting agreement.

## 2026-08-16 — Anything injected into a chair prompt as SETTLED needs a verified evidence line

In the `lint` run the orchestrator rated a peer reviewer's finding highly and passed it into Council 2's chair prompt as settled context: that the `checks.md` "Warning is audit's authored-tier worklist" sentence was false and must be narrowed. The refuter later showed the sentence restates the project's own cross-file definition (`audit/SKILL.md:29`), and deleting it would have desynced two files.

A SETTLED item shapes every downstream agent's reasoning and is by construction not re-litigated, so it needs the same evidence bar as a refuter verdict — an orchestrator-checked file and line — or it must be labelled provisional. The refuter gate caught this one, but only because the edit happened to be load-bearing.

## 2026-08-16 — The councils over-propose; budget for a high refutation rate

Thirteen load-bearing edits reached the refuter gate on `lint`; twelve distinct claims were refuted in whole or part, eight edits held (several multi-part). This matches the `ingest` run earlier the same day and the three prior consecutive majority refutations already recorded below.

The pattern is consistent enough to plan around: treat the chair change-sets as candidate lists, not conclusions, and never apply a load-bearing edit that skipped the gate. Consider asking each advisor for a disconfirming check they ran on their own strongest finding before it reaches peer review.

## 2026-08-16 — refuters refuted 6 of 15, and the mode inverted again: false claims about neighbours, not over-deletion

Run: `skill-llm-council-2026-08-16-2023-ingest`. Third consecutive run where the refuters killed a large share of the load-bearing edits, so the documented trigger has now fired three times running. But the shape inverted from the 2026-08-15 entry a second time, and the fix that entry implies did not apply here.

That run's councils over-**deleted**. This run's deletions were the safest edits in the set: the refuter given the "is this the only statement of this rule anywhere?" hunt cleared **all four**, each with a quoted alternate location. The kills were concentrated in **additions**, and three of the six shared one shape — the edit asserted something factually false about a *neighbouring file*: that quarantining preserves nothing (the convention verifies a byte-identical copy before unlinking), that `audit` re-verifies without rewriting (its own description says it applies splits, merges, and rewrites), and that the shared spec defines no terminal state for a stalled run (it does, twice). Each read plausibly, survived both chairs, and survived two rounds of peer review; only opening the neighbour caught it.

Three things to carry:

- **Additions need a symmetric hunt to the deletion one.** The deletion prompt asks "is this the only copy?" and it works. Nothing asks an addition "does the file this edit describes actually say what the edit claims about it?" — which is the exact question that killed three of six here. Add it to the refuter prompt for any edit that characterizes another file.
- **A same-day edit is a live conflict surface.** Two kills were collisions with rules landed earlier the same session, not with old text. When a run briefs its councils on "current state", the refuter should be pointed at that state as the *first* thing to check the edit against, since the councils were told it is settled and will not re-examine it.
- **Refuter coverage is not enforced.** Two load-bearing edits were bundled into a prompt scoped to two others and briefly had no verdict; the omission was caught by hand, not by the skill. Step 6 has no count-reconciliation, so coverage rests on the orchestrator remembering.

## 2026-08-15 — refuters refuted 5 of 10, and the mode inverted: over-deletion, not over-duplication

Run: `skill-llm-council-2026-08-15-1617-audit`. Second consecutive run where the refuters killed half or more of the load-bearing edits. The rate is now a pattern rather than an incident, but the *shape* inverted, so the fix is not the one the 2026-08-13 entry implies.

That run's councils over-**duplicated**: they proposed local copies of rules whose canonical home is the shared spec. This run's councils over-**deleted**: having correctly identified one class of rules as non-transferable tuning ported from another repo, they extended that verdict to rules that were sound. Four of the five refutations were of proposed *deletions*, and in each the refuter found the rule was the only statement of something real — the sole "do not state an unconfirmable value" rule for frontmatter, the sole guidance for a repeatedly-failing count, the sole ordering rule for a worklist class an earlier step explicitly excludes, and a crop-reading rule whose proposed safety caveat would have re-broken the exact defect it was ported to fix.

Three things to carry:

- **A correct framing generalizes past its evidence.** Peer review supplied this run's most valuable insight (these rules were tuned for a different corpus), and both chairs then applied it to rules the insight did not cover. When a reframing arrives late and lands hard, the meta-chair should re-test each rule against it individually rather than accepting the frame's own scope — that is precisely what the refuters ended up doing.
- **Deletion needs a stronger prior than the gate currently gives it.** A proposed deletion is load-bearing in a way an addition is not: an over-broad addition is visible and reversible, a deletion removes the only copy and leaves nothing marking the spot. Consider prompting the refuter for a deletion specifically to hunt "is this the only statement of this rule anywhere", which is what caught four of five here.
- The 2026-08-13 note that chair rankings correlate poorly with refuter survival **held again**, in both directions: chair-confident deletions died, and one chair's self-flagged lowest-confidence item was the one a refuter partly upheld.

## 2026-08-13 — refuters refuted 5 of 6 load-bearing edits (councils over-reaching)

Run: `skill-llm-council-2026-08-13-2146-ingest-audit`. The documented revisit trigger fired — the refuters killed a majority of the load-bearing edits, and four of the five were chair-ranked Tier 1 or "highest-value".

The failure had one shape, in every case: the councils proposed adding a **local copy of a rule whose canonical home is the shared spec**, and each copy was either lossier than the original (dropping the Tier-3 cold-recompute discipline), over-fired in a context the original was scoped to avoid (a `draft`-page marker rule lifted out of the Setting Status frame), unexecutable as written (hashing "the page as it entered this run" at a step where the run has already rewritten it), or contradicted a standing safety rule (importing another run's findings against "Never inherit a finding from a prior report").

Two consequences worth carrying into the next run:

- Peer review warned against collapsing duplicated rules before reconciling them. Nobody warned against the inverse — duplicating to close a gap the canonical rule already covers — which is what actually bit. Both directions need a prior.
- Chair rankings correlated poorly with refuter survival. A chair's "highest-value" is an argued severity, not a ground-truth verdict, and should be reported as such until the gate has run.
