# lint — dependencies

Reference map of every file `lint` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/lint/`)

- `SKILL.md` — the skill procedure.
- `references/checks.md` — the full check catalogue (Script-emitted + LLM-walk).
- `references/fixes.md` — the Step 3 determinate-fix mechanics, convergence loop, and Step 3b verified-hash sweep.
- `scripts/sort_chronology.py` — the log / hot Recent-activity chronology re-sort (lint-only; not shared, so it stays here).
- `lint-memory.md` — per-skill corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

The wiki-checking scripts and curated data live here because audit/ingest/forget/supersede/synthesis use them directly too — genuinely shared infrastructure. lint runs them from here.

- `scripts/check_wiki.py` — the main deterministic structural checker (imports `body_hash.py` as a sibling).
- `scripts/body_hash.py` — the `verified_hash:` computation (masks `*[unverified]*` lines).
- `scripts/cited_figure_check.py` — the opt-in cited-figure backstop (reads raws; PyMuPDF).
- `scripts/pagination_map.py` — proposes and verifies the per-raw pagination map.
- `scripts/tests/` — the regression suites for `check_wiki.py`, `body_hash.py`, `cited_figure_check.py` (and the shared scanner suites).
- `pagination-map.md` — per-raw record of what each physical page prints (curated data).
- `hyphenation-lists.md` — the four lists behind `hyphenated_open_compound_noun` (curated data).
- `unlinked-mention-ignore.md` — the verified-ignore list behind `unlinked_page_mention` (curated data).
- `references/verification-neutral-fixes.md` — the re-stamp-vs-demote allowlist (shared with `audit`; lint owns the four format fixes).
- `references/self-report.md` — the Self-report format the Step 4 report closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~68 citations: lint enforces the page-level half of the schema (frontmatter, callouts, Page Status, Bullet Markers, Source Support And Verification, Hot/Index/Log).
- `a-archive/` project reference and style material (read-only project resources, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the mechanical tells scanned over wiki-page bodies (Step 2).
  - `a-archive/reference/llm-wiki-design-decisions.md` — referenced as design provenance.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the wiki pages it structurally checks and mechanically fixes.
- `0-raw/**` — read (never modified) by `pagination_map.py` and the opt-in `cited_figure_check.py`.
- `2-outputs/lint/**` — the reports it writes; and it reads the newest `2-outputs/consistency/` report for the schema-staleness warning.

## Self-containment status

Clean — lint runs from its own folder plus `multi-skill/`. Its wiki-checking scripts (`check_wiki.py`, `body_hash.py`, `cited_figure_check.py`, `pagination_map.py`) and curated data (`pagination-map.md`, `hyphenation-lists.md`, `unlinked-mention-ignore.md`) live in `multi-skill/` because five sibling skills use them directly; lint reaches them there, not in another skill's folder. Only `sort_chronology.py` (lint-only) stays in lint. No cross-skill dependency.
