---
type: memory
skill: skill-llm-council
updated: 2026-08-15
---

# Skill-llm-council memory

Corrections, rewrites, and scope adjustments specific to the `skill-llm-council` skill. Read at the start of every skill-llm-council operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

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
