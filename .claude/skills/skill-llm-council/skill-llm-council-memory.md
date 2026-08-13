---
type: memory
skill: skill-llm-council
updated: 2026-07-14
---

# Skill-llm-council memory

Corrections, rewrites, and scope adjustments specific to the `skill-llm-council` skill. Read at the start of every skill-llm-council operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

## 2026-08-13 — refuters refuted 5 of 6 load-bearing edits (councils over-reaching)

Run: `skill-llm-council-2026-08-13-2146-ingest-audit`. The documented revisit trigger fired — the refuters killed a majority of the load-bearing edits, and four of the five were chair-ranked Tier 1 or "highest-value".

The failure had one shape, in every case: the councils proposed adding a **local copy of a rule whose canonical home is the shared spec**, and each copy was either lossier than the original (dropping the Tier-3 cold-recompute discipline), over-fired in a context the original was scoped to avoid (a `draft`-page marker rule lifted out of the Setting Status frame), unexecutable as written (hashing "the page as it entered this run" at a step where the run has already rewritten it), or contradicted a standing safety rule (importing another run's findings against "Never inherit a finding from a prior report").

Two consequences worth carrying into the next run:

- Peer review warned against collapsing duplicated rules before reconciling them. Nobody warned against the inverse — duplicating to close a gap the canonical rule already covers — which is what actually bit. Both directions need a prior.
- Chair rankings correlated poorly with refuter survival. A chair's "highest-value" is an argued severity, not a ground-truth verdict, and should be reported as such until the gate has run.
