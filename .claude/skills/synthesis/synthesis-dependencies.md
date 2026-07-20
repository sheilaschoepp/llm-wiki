# synthesis — dependencies

Reference map of every file `synthesis` relies on to run, grouped by where the file lives. Self-containment bar: the skill must run from its own folder plus `.claude/skills/multi-skill/`; anything else is a dependency to justify. This map is a reference, not an enforced artifact.

## Own folder (`.claude/skills/synthesis/`)

- `SKILL.md` — the skill procedure (synthesis is a single-file skill; its linear authoring pipeline has no separable-job seam that would warrant its own `references/`).
- `synthesis-memory.md` — per-skill corrections, read at Step 1.

## Multi-skill folder (`.claude/skills/multi-skill/`, shared)

- `references/verification.md` — the two ingest-family verification packets run in Step 8 over the drafted synthesis page.
- `references/self-report.md` — the Self-report format the Step 10 report closes with.
- `scripts/check_wiki.py` — the Step 8 structural check over the touched synthesis page, the same shared checker audit/ingest/forget/supersede all use.
- `multi-skill-memory.md` — cross-skill corrections, read at Step 1.

## Elsewhere

- `CLAUDE.md` — the shared schema (the one always-allowed non-multi-skill reference). ~15 citations: Synthesis Pages, Source Support And Verification, Callout Block IDs, Page Status, Length, Known Limitations.

## Skill-invocation (delegation) dependencies

synthesis delegates two operations to sibling skills rather than duplicating their mechanics — the method's "don't duplicate shared logic" spirit. These invoke the skill (loaded by the harness), not a read into its folder:

- `supersede` — invoked on a merge (Step 5 item 2a) to run its full Merge procedure (survivor kept, absorbed content preserved, inbound links re-pointed). synthesis resumes afterward for the synthesis-specific post-merge bookkeeping.
- `forget` — routed to when the user wants an overlapping page removed outright with no preserved view.

## Operands (subject matter, not logic dependencies)

- `1-wiki/**` — the concept/entity/synthesis pages it reads, clusters, and authors.
- `0-raw/**` — read (never modified) on the Step 8 raw-source verification.
- `2-outputs/**` — the synthesis reports it writes, and the query/brief/reflect/compare artifacts it may promote from.

## Self-containment status

Clean — every file dependency is own-folder, multi-skill, or `CLAUDE.md`. The shared structural checker `check_wiki.py` synthesis runs in Step 8 now lives in `multi-skill/` (used by audit/ingest/forget/supersede too), so synthesis reaches no other skill's folder for logic. Beyond files, synthesis delegates merges to `supersede` and removals to `forget` by invoking those skills — a delegation that avoids duplicating their mechanics, not a read into their folders.
