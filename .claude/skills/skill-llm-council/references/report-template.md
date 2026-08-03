# Report template

Write to `2-outputs/skill-llm-council/skill-llm-council-YYYY-MM-DD-HHMM-{skill-name}.md`, following the timestamp and same-minute-suffix rule in SKILL.md Step 7 (not restated here); `{skill-name}` is the target skill's folder name.

The report is the audit trail. Render the shared body and exactly one mode ending; never emit solve-only candidate, edit, or proposal headings in evaluate. Paths are repo-relative. Keep responses inspectable and bind every item to the recorded snapshot.

```markdown
---
type: skill-llm-council
date: {YYYY-MM-DD}
mode: {evaluate | solve}
result: {evaluated-clean | evaluated-findings | solved-applied | solved-proposals | solved-demoted | solved-no-survivor | blocked | incomplete}
target: "{skill-name}"
target_path: "./.claude/skills/{skill-name}/"
snapshot_id: "{manifest hash}"
baseline_commit: "{commit}"
dirty_paths: {N}
drift: {none | detected}
{solve only: applied: N}
{solve only: cross_file_proposals: N}
---

# Skill LLM council: {skill-name}

Path: `./.claude/skills/{skill-name}/`
Run: {YYYY-MM-DD HH:MM}
Mode/result: {mode} / {result}
Outcome: {one-line headline; include edit/proposal tallies only in solve}
Value over the skill-linter baseline: {what this council caught that the deterministic scripts + best-practices checklist pass would have missed — the reason the ~22-call spend was worth it this run; if little beyond the cheap pass, say so plainly}
Churn vs prior run: {evaluate: how the finding set changed; solve: how the applied candidate set changed; "no prior run" otherwise}

## Task brief

{What the skill does, what a good version needs, which rules bind it, what was already known wrong (from any prior skill-linter report), what disagreement is useful here.}

Related context: {which related skills and repo files the councils were given, and whether by inlined excerpts or a bounded read-access grant — naming the files, so a reader can see what context shaped each review.}

## Council 1 — cognitive lenses

### Step 2 responses
Independence: confirm the five Step-2 calls were issued in parallel in a single message (the launch that keeps the reads independent); note any that were not.
Ground check: {every finding or candidate dropped for failed/missing ground, with its original claim and ground; "None dropped" when clean.}
Ungroundable: {each flagged finding or candidate and its reason; never sole support for a load-bearing candidate. "None" when absent.}
{Each role's mode-specific response, one block per role, with ground-dropped items marked rather than cut. Evaluate contains FINDINGS only; solve contains implementation-complete IDEAS.}

### Anonymization
{A–E → role mapping for this council.}

### Step 3 fresh reviews
{Evaluate: each findings peer review. Solve: frozen candidate ledger plus each evaluator's per-C_ID verdicts and panel/candidate coverage.}

### Step 4 chair synthesis
{Evaluate: consolidated assessment only. Solve: exact selected/rejected C_IDs. Then agreements, clashes, dissent, peer/evaluator-only signal, uncertainty, confidence.}

## Council 2 — skill specialists

{Composed roster: the three core specialists plus the two selectable specialists chosen for this skill, with a one-line reason for each selection (e.g. "Script & Python-Quality — skill bundles `scripts/`"). Then the same four subsections as Council 1.}

## Step 5 — meta-chair reconciliation

{Evaluate: final findings, grounds, severity, confidence, and dissent only. Solve: selected exact C_IDs with P_ID, snapshot, implementation, scope, chair trace, evaluator coverage, and conflicts.}

## Evaluate ending — render only when `mode: evaluate`

### Consolidated assessment

{Grounded findings by severity; ground-check dispositions; uncertainty; preserved dissent. No target-improvement ideas, replacement wording, candidates, proposed edits, change-set, needs-review proposals, cross-file proposals, or memory recommendations.}

Zero-write attestation: target unchanged; memory unchanged; no proposal/change-set artifacts emitted. Report drift against the captured snapshot, if any.

## Solve ending — render only when `mode: solve`

### Problem manifest and frozen candidates

{Every P_ID; every frozen C_ID and snapshot; material-difference check; evaluator panel quorum; per-candidate HOLD/REFUTE/ABSTAIN coverage; chair/meta-chair disposition; no-survivor reason when applicable.}

## Completed changes

Adversarial verification (load-bearing edits): {per exact C_ID edit, BOTH verdicts — locator and entailment — with verified evidence. Name the refuting lens. Refuted candidates are terminal for this run and appear under Needs-review; no repair path.}

Applied in-folder, smallest reasonable edit each:

- Judgement edits (list each): `file:line — old → new`
- Mechanical edits (counts): {e.g. "3 broken links fixed, 2 H2 headings re-cased"}

Skipped / reverted: {edits dropped at Step 5, demoted by the health gate or a refuter, or reverted on the semantic re-read — each with the one-line reason.}

Post-apply sanity check: {result of running skill-linter's deterministic scripts on the edited skill, naming which scanners ran and which were not applicable.}

## Needs-review proposals

Not applied — these in-folder edits were demoted by the health, coherence, refuter, or semantic gate.

- [needs-review] `{target path}` — {exact edit, the gate that demoted it, and why}

## Cross-file proposals

Not applied — these touch shared files. Act on them by hand if you agree.

- [cross-file] `{target path}` — {exact edit and why}

## Preserved dissent

{Minority views the councils wanted kept on record, even where the change was applied or dropped.}
```

## Notes

- If a council ran with fewer than five advisors (a failed subagent that could not be re-run), say so in that council's section and note how it affected confidence.
- The report always carries `mode:` and `result:`. Use `solved-proposals` when only cross-file candidates survive, `solved-demoted` when candidates reached verification but none held, and `solved-no-survivor` when none survived generation, eligibility, or coherence. In evaluate, omit every solve-only heading and frontmatter field; do not render empty placeholders.
- This is a skill-facing operation: no `1-wiki/log.md` entry.

## Self-report

- Follow `.claude/skills/multi-skill/references/self-report.md` in both modes. This process-governance section is distinct from evaluate's target assessment and does not license target-improvement ideas or writes. Use `none noted this run` only when the process genuinely ran cleanly.
