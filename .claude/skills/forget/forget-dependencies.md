# forget — dependencies

Reference map of every file `forget` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/forget/`)

- `SKILL.md` — the skill procedure.
- `references/removal-mechanics.md` — the Step 5 copy/verify/move command sequences and the Restore From Quarantine rollback.
- `forget-memory.md` — per-skill corrections, read at Step 2.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/dependent-cascade.md` — Step 6 `needs_update_reason:` hand-off, `verified_hash` / status reset, zero-source and single-source-synthesis decisions.
- `references/quarantine-path-convention.md` — the name-clash suffix rule and preserved-copy verification.
- `references/inbound-reference-discovery.md` — Step 2 inbound-reference discovery (anchored stem grep, alias sweep).
- `references/self-report.md` — the Self-report format the Step 8 report closes with.
- `scripts/check_wiki.py` — the Step 7 structural landed-cleanly re-check (run on every forget), the same shared checker audit/ingest/supersede/synthesis all use.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 2.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). Safety rules (file-by-file deletion), Wikilink Format, Page Status.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the pages, support links, and attachments it removes and the inbound references it repairs.
- `2-outputs/forget/quarantine/**` — where it quarantines removed whole pages and attachments.

## Self-containment status

Clean — every dependency is own-folder, multi-skill, or `CLAUDE.md`. The shared structural checker `check_wiki.py` forget runs in Step 7 now lives in `multi-skill/` (used by audit/ingest/supersede/synthesis too), so forget reaches no other skill's folder for logic. (forget routes a mis-scoped "this is wrong" removal to `supersede` by naming it, not by reading its folder.)
