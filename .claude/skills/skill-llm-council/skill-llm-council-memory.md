---
type: memory
skill: skill-llm-council
updated: 2026-08-08
---

# Skill-llm-council memory

Corrections, rewrites, and scope adjustments specific to the `skill-llm-council` skill. Read at the start of every skill-llm-council operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

## The Step-1 census is a premise, not a hint — undercounting it fails the whole slate (2026-08-08)

Solve run on `audit`: ten candidates, zero applied. Eight of ten died on site completeness, and the
proximate cause was the orchestrator's own frozen census. The manifest named 3 sites for one problem
and the true count was 8; another problem's decisive site (`SKILL.md:128`) was never listed at all,
and it is what refuted the leading candidate in both panels. Because the Step-1 brief is appended to
all ten generator prompts, an incomplete census becomes the premise of ten candidates at once and is
then refuted ten times downstream instead of once at the source.

Two concrete fixes for the next run, both cheap:

- Derive each problem's census by grepping the rule's distinctive phrase **and its paraphrases**. Here
  a grep for `zero unresolved required target` missed the live clause `or any unresolved required
  target` on a line a candidate had already edited — the candidate's own success test greped the same
  narrow string and therefore passed while the contradiction stood.
- State the census as a floor ("at least N sites; enumerate more and report what you find"), never as
  a list. Generators treated the list as complete; the ones that went looking anyway found sites the
  brief lacked, and those were the only candidates that got close.

## Complementary failure needs its own disposition (2026-08-08)

Same run. Both candidates for one `P_ID` failed by missing *different* subsets of the same census:
one missed a single site, its sibling missed five others. Merging is forbidden and should stay
forbidden, but the outcome — `solved-no-survivor` — understates what was learned, because the union of
the two frozen candidates would have been complete. A future run regenerating from the same brief
repeats the work. Worth a distinct terminal ("re-freeze with expanded census") so the next round
starts from the union of the enumerated sites rather than from the original manifest.

## Cross-council convergence signal fired (2026-08-08)

The two councils produced the same disposition on 9 of 10 candidates — the signal `roles.md` says to
record rather than act on. Recorded, not acted on: the one divergence was decisive (Panel 1 refuted a
candidate Panel 2 held unanimously, on a real unedited site Panel 2's five evaluators all missed), so
the second council earned its cost on exactly the case where agreement would have been wrong. Do not
collapse the two-council structure on this evidence.

## Self-target scope: two tests, not one (2026-08-06)

On a self-run the meta-chair routed two auto-appliable `SKILL.md` edits to proposals by conflating two separate tests. `SKILL.md:157` ("When a candidate's scope is unclear, classify the whole candidate as cross-file") governs **which files** an edit touches — in-folder versus outside the folder. The self-target carve-out at `:159`/`:161` governs **which text within `SKILL.md`** is protected: only text that *states* a safety, independence, mode-boundary, or quorum mechanism. An in-folder `SKILL.md` edit to ordinary procedure content is auto-appliable, and chair disagreement about it is not by itself "unclear scope".

The task-brief specification is ordinary content: `SKILL.md:87` justifies it on framing quality, not as a stated independence mechanism. Do not reason from "the defect this fixes implicates independence" to "the text is a protected mechanism" — the rule keys on what the text states.

`references/` files stay proposal-only by explicit enumeration; that half was applied correctly.
