# cleanup — Outputs Candidate Classification (Step 4)

How the outputs job sorts each `2-outputs/` file into a deletion-candidate category. SKILL.md Step 4 resolves the age threshold and runs the git-status check; this file holds the four categories, the repeatable-check-vs-working-artifact split they turn on, the inbound-reference check, and how the protected set is applied. The memory job never loads this.

## Contents

- Repeatable Check Vs Working Artifact
- The Four Categories
- Inbound-Reference Check
- Apply The Protected Set

## Repeatable Check Vs Working Artifact

Walk `2-outputs/` and sort each file into the first category it matches, in the order below. The superseded-check-vs-aged split turns on kind: a repeatable check kind (`lint`, `consistency`, `audit`, `skill-linter`, `cleanup`) emits a fresh report each run that the next run supersedes, so only the latest is kept; a working artifact (`query`, `brief`, `compare`, `reflect`, `ingest`, `forget`, `supersede`, `synthesis`) is a unique deliverable, kept until it ages out.

## The Four Categories

- **junk** — OS cruft and orphaned writes: `.DS_Store`, `Thumbs.db`, and any zero-byte file that is not a `.gitkeep`. Trivially safe; always proposed.
- **superseded-check** — for the repeatable check kinds, every report except the most recent of that kind, grouped before comparing. Whole-wiki kinds (`lint`, `consistency`, `audit`, and this skill's own `cleanup` reports) supersede globally — keep the single most-recent. Per-subject kinds supersede within each subject: `skill-linter` reports are named per skill (`skill-linter-…-{skill}.md`), so keep the most-recent per `{skill}` — re-linting one skill never supersedes another skill's latest review. (`skill-llm-council` reports are a deep per-skill audit trail, not a disposable-on-rerun check, so they are not a superseded-check kind — they age out instead.) Resolve the date from the `{kind}-YYYY-MM-DD-HHMM` filename, not mtime; when two reports of the same kind and subject share the exact `YYYY-MM-DD-HHMM`, keep both (the tie leaves "most recent" undetermined). Additionally keep the most-recent `lint` and `consistency` report whose frontmatter `result:` is `clean` (read the frontmatter to find it), so `audit`'s precondition — a recent clean lint and consistency — survives the prune; `audit` writes no `result:` of its own, so its latest report is kept simply as the most-recent of its kind. A `superseded-check` candidate is a stale check report proposed for deletion — unrelated to the protected `2-outputs/supersede/preserve/` preservation folder, which is never touched. Those kept reports are protected, not candidates.
- **orphaned-subject** — a report whose subject no longer exists: an `ingest/` report `ingest-YYYY-MM-DD-HHMM-{stem}.md` whose `{stem}` is gone from `1-wiki/sources/`; a `skill-linter/` or `skill-llm-council/` report for a `{skill}` no longer in `.claude/skills/`. Resolve the subject by stripping the fixed `{kind}-YYYY-MM-DD-HHMM-` prefix — everything after it is the subject, internal hyphens included (`illustrated-transformer`, `Vaswani2017AttentionIA-ch01`), never a last-hyphen split. Confirm against disk before proposing: count the subject present if `1-wiki/sources/{stem}.md` OR any chapter split `1-wiki/sources/{stem}-ch*.md` exists (a split source is not orphaned), and a merely renamed skill still on disk under its new name is not orphaned. A report whose subject still exists is not orphaned. The `forget`, `supersede`, and `synthesis` operation reports are never orphaned-subject candidates: a `forget` report documents removing its subject page (the subject is gone by design), and `supersede`/`synthesis` reports name a page that may have been renamed or later removed — these three age out by threshold only, never pruned for a missing subject.
- **aged** — any remaining report older than the resolved threshold (by the `YYYY-MM-DD` in its filename), across every non-protected kind, including the working artifacts (`query`, `brief`, `compare`, `reflect`, `ingest`, `forget`, `supersede`, `synthesis`). Skip this category entirely when the user chose "no age cutoff this run".

## Inbound-Reference Check

Run this before proposing any working artifact (`query`, `brief`, `compare`, `reflect`, `ingest`, `forget`, `supersede`, `synthesis`) for aged or orphaned deletion. A promoted synthesis page records where it came from in `origin:` frontmatter pointing at the report it grew from (CLAUDE.md → Synthesis frontmatter: `origin: "[[2-outputs/query/…]]"`), and a live page may wikilink a report in its body. Before proposing such a report for deletion, grep `1-wiki/` for its path — synthesis `origin:` fields first, then body wikilinks. If a live page references it, note that inbound link on the file's Step 7 per-file gate so the user removes it knowing a live page's `origin:` pointer will be left dangling. The dangler is tolerated — `forget` and `supersede` likewise leave a live-page-to-output `origin:` link frozen rather than repairing it, and CLAUDE.md already expects `log.md`/`hot.md` danglers into `2-outputs/` — so this is pre-deletion transparency, not a blocked deletion. It mirrors the inbound-reference sweep `forget` and `supersede` run before removing a wiki page.

## Apply The Protected Set

Apply the protected set (Scope → Outputs cleanup) before proposing anything: never surface a `.gitkeep`, a kept-latest check report, or any file under `forget/quarantine/` or `supersede/preserve/`. Record in the report what was protected and skipped, so a sweep that holds content back reads as deliberate, not missed.
