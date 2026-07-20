# consistency — dependencies

Reference map of every file `consistency` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/consistency/`)

- `SKILL.md` — the skill procedure (the 10-step battery, six packets, and the `result:` gate contract).
- `references/checks.md` — the per-check catalogue (kept aligned with the script manifest by `catalogue_matches_manifest`).
- `scripts/check_consistency.py` — the deterministic battery (five script packets, ~27 checks).
- `scripts/tests/test_check_consistency.py` — the regression suite.
- `consistency-memory.md` — per-skill corrections and sanctioned-exception entries, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/self-report.md` — the Self-report format the Step 8 report closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~34 citations: consistency's whole purpose is checking the project against this schema (`EXPECTED_SECTIONS`, the Operations list, callout templates, the audit-precondition contract).
- `a-archive/` project reference and style material (read-only project resources the checks consult, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the source list for the `ai_writing_tells` check.
  - `a-archive/about-me/about-me.md` — the `## Identity` section the `identity_term_leakage` check auto-extracts its terms from.
  - `a-archive/reference/` — referenced as project reference material.

## Operands (subject matter, not logic dependencies)

consistency checks the whole project for drift — it reads these to verify them, not to learn how to run:

- `CLAUDE.md`, `README.md` — checked for stale schema prose and drift.
- `.claude/skills/**` (every skill's `SKILL.md`, `references/`, `scripts/`) — checked for skill/script drift, orphan scripts, leakage, and shared-reference integrity.
- `1-wiki/**` — wiki-page placeholders, section order, index-vs-files drift.
- `.obsidian/snippets/custom_callouts.css` — callout CSS coverage.
- `MEMORY.md`, `2-outputs/**` — memory graduation counter, output-kind coverage.

## Self-containment status

Clean — no cross-skill logic dependency. consistency's own logic is its script, references, `CLAUDE.md`, and the `a-archive/` resource files its checks read; every other skill's folder it opens is an operand it audits, not procedure it depends on. (Its test file carries a synthetic fixture skill and a nonexistent reference path to exercise orphan-script and path checks — fixtures, not real dependencies.)

## Known unfixable check finding

`check_h2_case` flags the five `## Packet: <name>` headings in `references/checks.md` (`schema-language`, `wiki-pages`, `styles-files`, `ai-writing-tells`, `naming`) as sentence-case. These packet names are code identifiers that consistency's own `catalogue_matches_manifest` check parses from the bare heading — backticking or title-casing them breaks that parser (it reads the packet name verbatim). Per skill-linter's rule a code-token-only `h2_heading_case` finding is dropped, not applied; these are that case, constrained here by consistency's own tooling.
