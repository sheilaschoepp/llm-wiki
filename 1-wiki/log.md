# Log

Reverse-chronological event log. Newest entry on top.

## [2026-08-16 20:52] skill-llm-council | lint

- Saved: [[2-outputs/skill-llm-council/skill-llm-council-2026-08-16-2052-lint.md|skill-llm-council-2026-08-16-2052-lint]]
- Full protocol: 10 advisors across two councils, 10 anonymized peer reviews, 2 chair syntheses, meta-chair reconciliation, 13 adversarial refuters.
- Applied 14 edits to `.claude/skills/lint/` (SKILL.md, references/checks.md, references/fixes.md, scripts/sort_chronology.py). Eight load-bearing edits held at the refuter gate; twelve distinct claims were refuted.
- Substantive: Open-threads prune now requires every wiki-page link in an entry to be dead before auto-removal (it could previously delete live orientation on one dangling link); `recover_time` scoped to the entry's own `Saved:`/`Report:` bullet, fixing a false whole-file skip; the verified-hash re-stamp re-confirms its baseline immediately before the edit; two Warning-tier checks moved out of the Info catalogue; `verified_hash` ownership corrected at three sites to match the current schema.
- Four cross-file proposals raised, not applied: a `locator_page_mismatch` severity question, a `test_sort_chronology.py`, a registry-versus-catalogue assertion, and single-sourcing two duplicated regexes.
- Verification: 5 scanners clean on `lint`, 296 tests pass, `checks.md` now diffs clean against the registry apart from the deliberate `caller-determined` split.

