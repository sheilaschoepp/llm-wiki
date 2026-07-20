# supersede — dependencies

Reference map of every file `supersede` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/supersede/`)

- `SKILL.md` — the skill procedure.
- `references/preservation-mechanics.md` — the Step 5 command mechanics (preserve-and-verify guard, two-tool-call overwrite rule, name-clash suffix, Restore Active Page rollback).
- `supersede-memory.md` — per-skill corrections, read at Step 2.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/dependent-cascade.md` — Step 6 cascade, `sources:` / `source_count` / `Sources` bookkeeping, verified_hash / status reset, under-supported-page rules.
- `references/quarantine-path-convention.md` — preserved-copy verification and the name-clash suffix rule.
- `references/verification.md` — Step 7 two-packet verification of newly-authored content.
- `references/verification-neutral-fixes.md` — the re-stamp allowlist for a same-page stale-path repair.
- `references/inbound-reference-discovery.md` — Step 2 inbound-link and source-support discovery.
- `references/self-report.md` — the Self-report format the Step 8 report closes with.
- `scripts/check_wiki.py` — the structural landed-cleanly re-check in Step 7 (run whenever attachments were involved or a page was deleted/renamed), the same shared checker audit/ingest/forget/synthesis all use.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 2.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~13 citations: Page Filenames, Page Status, Bullet Markers, Source Support And Verification, Safety rules.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the pages, claims, and attachments it supersedes and the inbound references it rewrites.
- `2-outputs/supersede/preserve/**` — the prior-view artifacts it writes.
- `0-raw/**` — read (never modified) for the Step 7 fact-check of newly-authored claims.

## Self-containment status

Clean — every dependency is own-folder, multi-skill, or `CLAUDE.md`. The shared structural checker `check_wiki.py` supersede runs in Step 7 now lives in `multi-skill/` (used by audit/ingest/forget/synthesis too), so supersede reaches no other skill's folder for logic.
