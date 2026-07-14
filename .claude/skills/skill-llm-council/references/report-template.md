# Report template

Write to `2-outputs/skill-llm-council/skill-llm-council-YYYY-MM-DD-HHMM-{skill-name}.md`, following the timestamp and same-minute-suffix rule in SKILL.md Step 7 (not restated here); `{skill-name}` is the target skill's folder name.

The report is the audit trail: it must let someone reconstruct the whole deliberation and check every applied edit. Paths in the report are repo-relative (start with `./`). Keep the agent responses verbatim enough to be inspectable — summarize only the parts that were redundant.

```markdown
---
type: skill-llm-council
date: {YYYY-MM-DD}
target: "{skill-name}"
target_path: "./.claude/skills/{skill-name}/"
applied: {N}
cross_file_proposals: {N}
---

# Skill LLM council: {skill-name}

Path: `./.claude/skills/{skill-name}/`
Run: {YYYY-MM-DD HH:MM}
Outcome: {N edits applied}, {N cross-file proposals}, {one-line headline}
Value over the skill-linter baseline: {what this council caught that the deterministic scripts + best-practices checklist pass would have missed — the reason the ~22-call spend was worth it this run; if little beyond the cheap pass, say so plainly}
Churn vs prior run: {if a prior report for this skill exists, how this run's applied set differs from it — repeated churn on the same lines is a signal the councils are oscillating rather than converging; "no prior run" otherwise}

## Task brief

{What the skill does, what a good version needs, which rules bind it, what was already known wrong (from any prior skill-linter report), what disagreement is useful here.}

Related context: {which related skills and repo files the councils were given, and whether by inlined excerpts or a bounded read-access grant — naming the files, so a reader can see what context shaped each review.}

## Council 1 — cognitive lenses

### Step 2 responses
Independence: confirm the five Step-2 calls were issued in parallel in a single message (the launch that keeps the reads independent); note any that were not.
{Each role's FINDINGS / PROPOSED EDITS / CONFIDENCE / DO-NOT-IGNORE, one block per role.}

### Anonymization
{A–E → role mapping for this council.}

### Step 3 peer reviews
{Each reviewer's four answers.}

### Step 4 chair synthesis
{The consolidated change-set, agreements, clashes (tension vs error catch), strongest dissent, what peer review surfaced, uncertainty, confidence.}

## Council 2 — skill specialists

{Composed roster: the three core specialists plus the two selectable specialists chosen for this skill, with a one-line reason for each selection (e.g. "Script & Python-Quality — skill bundles `scripts/`"). Then the same four subsections as Council 1.}

## Step 5 — meta-chair reconciliation

{The final change-set as an ordered list: file, anchor, change, scope, rationale. Note where the two councils agreed, where one council carried a change alone, and how each conflict was resolved. Preserve dissent.}

## Completed changes

Adversarial verification (load-bearing edits): {each refuter verdict — holds / refuted — with a one-line ground-truth reason; refuted edits were demoted to `[needs-review]` proposals, listed under Cross-file proposals.}

Applied in-folder, smallest reasonable edit each:

- Judgement edits (list each): `file:line — old → new`
- Mechanical edits (counts): {e.g. "3 broken links fixed, 2 H2 headings re-cased"}

Skipped / reverted: {edits dropped at Step 5, demoted by the health gate or a refuter, or reverted on the semantic re-read — each with the one-line reason.}

Post-apply sanity check: {result of running skill-linter's deterministic scripts on the edited skill, naming which scanners ran and which were not applicable.}

## Cross-file proposals

Not applied — these touch shared files. Act on them by hand if you agree.

- [cross-file] `{target path}` — {exact edit and why}

## Preserved dissent

{Minority views the councils wanted kept on record, even where the change was applied or dropped.}
```

## Notes

- If a council ran with fewer than five advisors (a failed subagent that could not be re-run), say so in that council's section and note how it affected confidence.
- The report does not carry a machine-readable `result:` gate field — nothing downstream consumes it.
- This is a skill-facing operation: no `1-wiki/log.md` entry.

## Self-report

- A specific limitation that bit the council process *this run* — the two councils converged so the split under-earned its cost, the refuters over- or under-fired, an applied edit needed rework a later pass caught, a role that added no signal — paired with how the `skill-llm-council` skill should be upgraded. `none noted this run` when the process ran cleanly. (Per `.claude/skills/multi-skill/references/self-report.md`; this is the council's report on *itself*, distinct from its findings about the target skill and from the revisit-trigger memory note.)
