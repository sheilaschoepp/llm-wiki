# skill-linter — dependencies

Reference map of every file `skill-linter` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/skill-linter/`)

- `SKILL.md` — the skill procedure.
- `skill-linter-memory.md` — per-skill corrections, read at Step 1.

(skill-linter's scanners, rubric, and terminology data moved to `multi-skill/` because its deep-review companion `skill-llm-council` also uses them — they are shared skill-authoring infrastructure now, listed below.)

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `scripts/check_structure.py` — frontmatter / length / paths / reference-depth / inline-ref checks.
- `scripts/check_synonyms.py` — synonym-candidate scanner (reads `synonym-ignore.md`).
- `scripts/check_musts.py` — heavy-handed-imperative scanner.
- `scripts/check_h2_case.py` — H2 title-case scanner.
- `scripts/check_kwargs.py` — keyword-argument scanner over a target's `scripts/*.py`.
- `scripts/tests/` — the regression suite pinning the scanners' behaviour.
- `references/skill-authoring-checklist.md` — the Step 3 judgement-check rubric (shared with `skill-llm-council`).
- `references/skill-authoring-checks.md` — the deterministic-check catalogue (shared with `skill-llm-council`).
- `synonym-ignore.md` — the per-skill confirmed-distinct terminology allow-list; skill-linter alone grows it (the one shared-folder file it writes).
- `references/self-report.md` — the Self-report format the Step 4 report closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~9 citations: Stay In Your Lane, the `2-outputs/` naming convention, severity vocabularies.
- `a-archive/` project reference and style material (read-only project resources skill-linter applies to the linted skill, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the tells flagged in linted-skill prose (Step 3).
  - `a-archive/style/coding-best-practices.md` — the Python rules checked against linted-skill `scripts/*.py` (Step 3).

## Operands (subject matter, not logic dependencies)

- The target skill's folder (any skill under `.claude/skills/`, an external directory, or an unzipped `.skill` bundle) — read and auto-edited in-folder. The subject under lint, chosen per run.
- `2-outputs/skill-linter/**` — the reports it writes.

## Self-containment status

Clean — skill-linter runs from its own folder plus `multi-skill/`. Its five scanners, its rubric (`skill-authoring-checklist.md` / `skill-authoring-checks.md`), and its terminology data (`synonym-ignore.md`) live in `multi-skill/` because `skill-llm-council` uses the same tooling — genuinely shared skill-authoring infrastructure, in the shared folder where both reach it. No cross-skill logic dependency remains.
