# reflect — dependencies

Reference map of every file `reflect` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/reflect/`)

- `SKILL.md` — the skill procedure (reflect is a single-file skill; well under budget with no separable-job seam).
- `reflect-memory.md` — per-skill corrections (sample size, framing), read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/self-report.md` — the Self-report format the Step 3 note closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). Page Status (claim-level verification), Synthesis distinct-works counting.
- `a-archive/` project reference and style material (read-only project resources, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the tells scanned over the note in Step 4.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the pages it samples across support tiers (frontmatter scans of sources/concepts/entities/syntheses), plus `hot.md`, `index.md`, and recent `log.md` for orientation. It reads wiki pages only, never `0-raw/`.
- `2-outputs/reflect/**` — the compass notes it writes, and the prior note it compares against.

## Self-containment status

Clean — no cross-skill logic dependency. reflect is a pure-output skill: every dependency is own-folder, multi-skill, `CLAUDE.md`, or `a-archive/` project reference material, and the wiki pages it samples are operands, not procedure. (It names a candidate cluster and defers the actual scan to `/synthesis` by naming that skill, not by reading its folder.)
