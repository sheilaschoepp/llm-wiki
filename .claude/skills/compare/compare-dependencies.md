# compare — dependencies

Reference map of every file `compare` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/compare/`)

- `SKILL.md` — the skill procedure (compare is a single-file skill; well under budget with no separable-job seam).
- `compare-memory.md` — per-skill corrections, read at Step 2.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/self-report.md` — the Self-report format the Step 5 comparison closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 2.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). Page Status, Bullet Markers, Known Limitations, Communication style.
- `a-archive/` project reference and style material (read-only project resources, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the tells scanned over the comparison in Step 6.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the 2-4 target pages it compares and the source pages behind them (read for support judgement; it does not reopen `0-raw/`).
- `2-outputs/compare/**` — the comparison files it writes.

## Self-containment status

Clean — no cross-skill logic dependency. compare is a pure-output skill: every dependency is own-folder, multi-skill, `CLAUDE.md`, or `a-archive/` project reference material, and the wiki pages it reads are operands, not procedure.
