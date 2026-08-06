---
type: memory
skill: skill-llm-council
updated: 2026-08-03
---

# Skill-llm-council memory

Corrections, rewrites, and scope adjustments specific to the `skill-llm-council` skill. Read at the start of every skill-llm-council operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

## Self-target scope: two tests, not one (2026-08-06)

On a self-run the meta-chair routed two auto-appliable `SKILL.md` edits to proposals by conflating two separate tests. `SKILL.md:157` ("When a candidate's scope is unclear, classify the whole candidate as cross-file") governs **which files** an edit touches — in-folder versus outside the folder. The self-target carve-out at `:159`/`:161` governs **which text within `SKILL.md`** is protected: only text that *states* a safety, independence, mode-boundary, or quorum mechanism. An in-folder `SKILL.md` edit to ordinary procedure content is auto-appliable, and chair disagreement about it is not by itself "unclear scope".

The task-brief specification is ordinary content: `SKILL.md:87` justifies it on framing quality, not as a stated independence mechanism. Do not reason from "the defect this fixes implicates independence" to "the text is a protected mechanism" — the rule keys on what the text states.

`references/` files stay proposal-only by explicit enumeration; that half was applied correctly.
