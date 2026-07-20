# skill-llm-council — dependencies

Reference map of every file `skill-llm-council` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/skill-llm-council/`)

- `SKILL.md` — the skill procedure (the 8-step council overview).
- `references/protocol.md` — step mechanics, peer-review / chair / meta-chair / refuter prompts, quorum floor.
- `references/roles.md` — the two rosters, the specialist bank, the selection rule, the role prompts.
- `references/report-template.md` — the Step 7 audit-trail report structure.
- `skill-llm-council-memory.md` — per-skill corrections and revisit signals, read/appended at Steps 1 and 8.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.
- `references/self-report.md` — the Self-report format the report closes with.
- `references/skill-authoring-checklist.md`, `references/skill-authoring-checks.md` — the Anthropic best-practices rubric, reused instead of restated (Step 1 brief).
- `scripts/check_structure.py`, `scripts/check_synonyms.py`, `scripts/check_musts.py`, `scripts/check_h2_case.py`, `scripts/check_kwargs.py` — the five deterministic scanners run in the Step 6 structural sanity check.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~12 citations: the schema and workflow rules the reviewed skill must obey.
- `a-archive/` project reference and style material (read-only project resources the councils review against, not another skill's logic): `reference/llm-council-best-practices.md` (this skill's own lineage), `reference/skill-authoring-best-practices.md`, `reference/claude-code-prompting-best-practices.md`, `reference/claude-code-context-management-best-practices.md` (the three always-loaded), plus the conditionally-loaded `reference/ai-assisted-reading-best-practices.md`, `reference/llm-wiki-best-practices.md`, `reference/smart-notes-llm-wiki-integration.md`, `reference/smart-notes-summary.md`; and `style/ai-writing-tells.md`, `style/coding-best-practices.md`.

## Operands (subject matter, not logic dependencies)

The council operates *on* these — reads them as the thing under review, and auto-applies in-folder edits to the target — but does not read them to learn how to run:

- The target skill's folder (any skill under `.claude/skills/`) — read in full and edited in-folder in Step 6. This is the subject under review, chosen per run.
- Related skills' `SKILL.md` / references — pulled in as review context (Step 1), read-only.
- `2-outputs/skill-llm-council/**` — the audit-trail reports it writes; and the latest `2-outputs/skill-linter/` report, folded in as context when present.

## Self-containment status

Clean — no cross-skill dependency. The best-practices rubric and the five scanners it reuses now live in `multi-skill/` (shared skill-authoring infrastructure, used by both skill-llm-council and skill-linter), so the council runs from its own folder plus `multi-skill/`. The target-skill folder it reviews and edits is its operand, not a logic dependency.
