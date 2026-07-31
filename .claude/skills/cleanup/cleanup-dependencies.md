# cleanup — dependencies

Reference map of every file `cleanup` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/cleanup/`)

- `SKILL.md` — the skill procedure.
- `references/memory-graduation.md` — Step 3 classification: the six categories, tie-break order, sensitive-content screen, and the keep/graduate/delete judgement.
- `references/outputs-cleanup.md` — Step 4 classification: the four candidate categories, the repeatable-check-vs-working-artifact split, the inbound-reference check, and the protected-set application.
- `cleanup-memory.md` — per-skill corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.
- `references/self-report.md` — the Self-report format the Step 5 report closes with.

## Operands (subject matter, not logic dependencies)

cleanup operates *on* these files — it reads them to classify, and graduates into or prunes them — but it does not read them to learn *how* to run. They are enumerated at runtime, not fixed logic dependencies, so they are not a self-containment concern:

- `MEMORY.md` — a memory tier read and graduated-into.
- `CLAUDE.md` — the project schema and a memory-job classification/graduation target. cleanup's runtime mechanics, including the recoverability-aware deletion boundary, stay mirrored in its own folder or `multi-skill/`; an outputs-only run does not load this file as a procedural dependency.
- `.claude/skills/*/*-memory.md` (every per-skill journal and the multi-skill journal) — the memory entries it classifies.
- `.claude/skills/*/SKILL.md` — graduation targets for skill-procedure rules (read, and proposed-for-edit only on user approval).
- `2-outputs/**` — the artifacts the outputs job scans and prunes.

## Self-containment status

Clean — no unresolved violations. Every procedural dependency is in cleanup's own folder or `multi-skill/`. cleanup reaches no other skill's folder for logic; the cross-folder files it touches are schema or content operands it classifies, graduates into, or cleans.
