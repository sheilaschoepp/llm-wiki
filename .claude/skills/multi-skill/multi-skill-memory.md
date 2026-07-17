---
type: memory
scope: multi-skill
updated: 2026-07-17
---

# Multi-skill memory

Cross-skill corrections, rewrites, and scope adjustments. Read by every write skill at the start of its operation. Use this file for rules that apply across more than one skill — e.g., framing or source-support rules that should govern both ingest and synthesis.

Skill-specific corrections live in each skill's own memory file at `.claude/skills/<skill>/<skill>-memory.md`.

Newest entry on top, one entry per heading.

## Report-naming convention (all skills, one format)

Every report-writing skill writes a dated operation report to its own `2-outputs/<kind>/`, named `<kind>-YYYY-MM-DD-HHMM(-<seg>)?.md`. `<seg>` is the skill's per-run label (topic, slug, stem, target, or skill-name); `audit`, `lint`, `consistency`, and `cleanup` use no seg, and `audit` may add a `-full` mode marker. Get the stamp once per run with `TZ='UTC' date '+%Y-%m-%d-%H%M'`, never a bare `date`. The format is uniform across every skill and is enforced by `file_naming_consistency` and `output_kinds_match_disk`. One deliberate exception: `checkup` is a pure orchestrator that writes no report of its own, since its consistency, lint, and audit sub-runs each write theirs. The convention lives here, in each skill's own body, and in those two checks, so it need not be duplicated into every skill's `description:` frontmatter.
