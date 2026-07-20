# audit — dependencies

Reference map of every file `audit` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/audit/`)

- `SKILL.md` — the skill procedure.
- `references/semantic-checks.md` — Step 4 Critical/Warning/Info semantic-check catalogue.
- `references/apply-fixes.md` — Step 7 fix mechanics (per-check dispositions, distortion-disposition rule, guards).
- `references/verification-spec.md` — Step 5 verification: coverage gate, tiered refuter gate, per-page-type checklist, citation check.
- `references/verify-and-set-status.md` — Step 8 pre-stamp checks and status-setting.
- `audit-memory.md` — per-skill corrections, read at Step 3.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/verification.md` — the shared tiered independent-refuter spec (also run by `ingest`/`query`).
- `references/verification-neutral-fixes.md` — the re-stamp allowlist for verification-neutral edits.
- `references/dependent-cascade.md` — Step 9 `sources:` / `source_count:` bookkeeping.
- `references/inbound-reference-discovery.md` — inbound-reference rewrite on a split/merge rename.
- `references/quarantine-path-convention.md` — prior-version preservation on an authored fix.
- `references/relationship-sweep.md` — cross-page relationship sweep.
- `references/self-report.md` — the Self-report format the Step 6 report closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 3.
- `scripts/body_hash.py` — computes/masks `verified_hash:` (Steps 5, 7, 8).
- `scripts/check_wiki.py` — structural re-validation of touched pages (Step 8) and the Step 1 gate report.
- `scripts/cited_figure_check.py` — figure-citation check (verification-spec).
- `pagination-map.md` — read to check a `p. M` locator; audit does not maintain it (registered on ingest).
- `unlinked-mention-ignore.md` — ignore list audit grows autonomously (Step 7, sub-agent-verified).
- `hyphenation-lists.md` — hyphenation data audit grows autonomously (Step 7, sub-agent-verified).

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~39 citations: Page Status, Bullet Markers, Source Support And Verification, Stay In Your Lane.
- `a-archive/` project reference and style material (read-only project resources audit consults, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the AI-writing tells applied in the Step 4 semantic-tell check.
  - `a-archive/reference/smart-notes-llm-wiki-integration.md`, `a-archive/reference/llm-wiki-design-decisions.md` — the foundation-design docs audit cites for the `verified`-stamp lineage (Purpose).

## Notes

- audit names `ingest`'s existing-source-mode and `supersede`'s procedures when describing authored fixes (Step 7), but does not read their folders — the actual mechanics it loads are the `multi-skill/` shared references above. Those are allowed comparative asides, not dependency-creating cross-references.

## Self-containment status

Clean — every dependency is own-folder, multi-skill, or `CLAUDE.md`. The wiki-checking scripts audit runs (`check_wiki.py`, `body_hash.py`, `cited_figure_check.py`) and the curated data it reads and grows (`pagination-map.md`, `unlinked-mention-ignore.md`, `hyphenation-lists.md`) now live in `multi-skill/` (shared with lint/ingest/forget/supersede/synthesis), so audit reaches no other skill's folder for logic.
