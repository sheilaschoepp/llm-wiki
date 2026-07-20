# query — dependencies

Reference map of every file `query` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/query/`)

- `SKILL.md` — the skill procedure (query is a single-file skill; its one linear pipeline has no separable-job seam that would warrant its own `references/`).
- `query-memory.md` — per-skill corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/verification.md` — the two ingest verification packets run in Step 8 when a query is promoted to a durable page (the page-authoring path).
- `references/self-report.md` — the Self-report format the Step 5 query output closes with.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~8 citations: Page Status, Source Support And Verification, Known Limitations, Synthesis Pages, Hot/Index/Log.
- `a-archive/` project reference and style material (read-only project resources, not another skill's logic):
  - `a-archive/style/ai-writing-tells.md` — the tells scanned over every query output in the Step 6 coverage-and-integration packet.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the pages read to answer the question (and authored, on the Step 8 promotion path).
- `0-raw/**` — read (never modified) on the Step 4 raw-source fallback and the Step 8 re-read.
- `2-outputs/query/**` — the query outputs it writes, and prior outputs it scans for follow-up threads.

## Self-containment status

Clean — no cross-skill logic dependency. query reaches no other skill's folder: its own Step 6 output-verification is inline, and its Step 8 page-authoring runs the shared `multi-skill/references/verification.md`. Every dependency is own-folder, multi-skill, `CLAUDE.md`, or `a-archive/` project reference material.
