# checkup — dependencies

Reference map of every file `checkup` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/checkup/`)

- `SKILL.md` — the orchestration procedure (the fixed order, the partial-mode choice, the audit precondition gate, proposal surfacing).
- `checkup-memory.md` — orchestration-level corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/self-report.md` — the Self-report format checkup collates and adds its own to (Step 5).
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~11 citations: the Audit-preconditions contract, Page Status, Severity vocabulary.
- Orchestration dependency (inherent and accepted — this *is* what checkup does):
  - `.claude/skills/consistency/SKILL.md` — read and run inline as Step 1.
  - `.claude/skills/lint/SKILL.md` — read and run inline as Steps 2 and 4.
  - `.claude/skills/audit/SKILL.md` — read and run inline as Step 3.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the wiki the sub-skills check and fix (checkup itself adds no checks).
- `2-outputs/consistency/**`, `2-outputs/lint/**`, `2-outputs/audit/**` — the sub-skill reports it reads for the precondition gate and the closing summary.

## Self-containment status

checkup is an orchestrator: its defining function is to read and run `consistency`, `lint`, and `audit` inline in one context (SKILL.md Procedure: "reading that skill's `SKILL.md` and performing its steps here"). Its dependency on those three skills' `SKILL.md` is therefore inherent and correct — the leaf-skill self-containment bar (own folder + multi-skill only) cannot and should not apply to an orchestrator, because relocating the three sub-skills into checkup's folder would defeat the point. This is the accepted orchestration category, documented here rather than "fixed." Every other dependency is own-folder, multi-skill, or `CLAUDE.md`.
