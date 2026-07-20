# brief — dependencies

Reference map of every file `brief` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/brief/`)

- `SKILL.md` — the skill procedure (brief is a single-file skill; well under budget with no separable-job seam).
- `brief-memory.md` — per-skill corrections (page types to include, draft aggressiveness, word target), read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/self-report.md` — the Self-report format the Step 3 brief closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). Page Status, Source Support And Verification, Hot/Index/Log, the academic-integrity rule.
- `a-archive/` project reference and style material (read-only project resources, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the tells scanned over the brief in Step 4.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the concept/entity/synthesis and source pages it reads for the topic, plus `hot.md` and `index.md`.
- `0-raw/**` — read (never modified) only in the rare edge case where a support-level claim the brief must state has no locator on the source page.
- `2-outputs/brief/**` — the briefs it writes.

## Self-containment status

Clean — no cross-skill logic dependency. brief is a pure-output skill: every dependency is own-folder, multi-skill, `CLAUDE.md`, or `a-archive/` project reference material, and the wiki pages (and rare raw read) are operands, not procedure.
