# ingest — dependencies

Reference map of every file `ingest` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact — it makes the skill's reach visible at a glance.

## Own folder (`.claude/skills/ingest/`)

- `SKILL.md` — the skill procedure.
- `references/existing-mode.md` — existing-source (reingest) always-on checks: reason, needs-update / tentative resolution, schema-migration, frames decision, deep-purpose recovery.
- `references/planning-questions.md` — Step 3 context-post catalogue and the per-decision question types.
- `references/source-page-writing.md` — per-callout source-page writing guidance, inline-embed format, citation rules.
- `references/attachments.md` — figure extraction and crop mechanics (point-space clip, render→inspect→crop loop).
- `ingest-memory.md` — per-skill corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/verification.md` — Step 8 two-packet verification spec (shared with `query`'s page-authoring path).
- `references/dependent-cascade.md` — Step 7 `needs-update` cascade mechanics.
- `references/inbound-reference-discovery.md` — inbound-reference rewrite on a legacy-page rename.
- `references/quarantine-path-convention.md` — attachment quarantine path rules.
- `references/relationship-sweep.md` — relationship-sweep catalogue (reached via `references/planning-questions.md`).
- `scripts/pagination_map.py` — proposes a pagination map from a PDF's footers and renders footer crops to verify; ingest runs it at Step 2.
- `pagination-map.md` — per-raw record of what each physical page prints (curated data). ingest registers a source's entry here at Step 2; `lint` reads it (`locator_page_mismatch`, the anchor-only locator exemption).
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~23 citations for required sections, frontmatter blocks, block-ID placement, and locator/citation rules.

## Self-containment status

Clean — every dependency is own-folder, multi-skill, or `CLAUDE.md`. The pagination tooling ingest runs and writes at Step 2 (`pagination_map.py`, `pagination-map.md`) now lives in `multi-skill/` — shared with `lint`, which reads the map — so ingest reaches no other skill's folder.
