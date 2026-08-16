# Log

Reverse-chronological event log. Newest entry on top.

## [2026-08-16 21:29] skill-llm-council | consistency

- Saved: [[2-outputs/skill-llm-council/skill-llm-council-2026-08-16-2129-consistency.md|skill-llm-council-2026-08-16-2129-consistency]]
- Full protocol: 10 advisors across two councils, 10 anonymized peer reviews, 2 chair syntheses, meta-chair reconciliation, 8 adversarial refuters. Three of nine load-bearing proposals held; six were refuted, including both chair disagreements.
- Applied 10 edits to `.claude/skills/consistency/`. The run's motivating finding: `result:` — the field gating whether `audit` may run — was underivable three ways. A `2-outputs/` rename the skill may not perform fell outside every non-blocking class and bounded the loop out to `blocked`; one line made `clean` conditional on the judgment-drift attestation while another said "Exit 0 ⇒ clean" flatly; and the report demanded three severity counts that no finding carries and no skill reads.
- Fixes: a sixth non-blocking class keyed on fix-permission with a mandatory named-rule citation; the exit code made necessary-but-not-sufficient on both branches; the three fabricated counts deleted and the dangling severity pointer repaired from `AI_TELL_PATTERNS`; a freeze on schema-derived fixes while the roster is in dispute; a restated Limits rule removed; Scope widened to the trees the battery actually reads; the description given the action posture every sibling states (947 -> 984 chars); and `placeholder_consistency` fixed to use the page kind it had been discarding.
- Five cross-file proposals raised, not applied — chief among them hoisting one canonical section roster shared by `check_consistency.py` and `check_wiki.py`.
- Verification: battery clean but for the standing handoff-doc finding, 33 consistency tests (up from 30), 296 multi-skill tests, ruff clean, scanner sweep clean across all 14 skills.

## [2026-08-16 21:04] skill-llm-council | ingest cross-file proposals

- Put the ingest council's cross-file proposals through the refuter gate before applying, per the user's decision to apply only the verified ones.
- Applied 2 of 6 to `.claude/skills/multi-skill/references/verification.md`: the proof-of-read claim is now named by the orchestrator when it issues the batch (a different claim per refuter where the batch allows), and Setting Status condition 2 gained an all-marked-page guard — a page entering non-`verified` with every non-obvious claim marked is not stamped, because `body_hash.py` masks every marked line and the checked body reduces to callout scaffolding.
- Refuted 4: the claim-check scope patch (condition 2 already states it and naming it twice would over-obligate `synthesis`/`supersede`/`query`); the `Recommended next ingests` deletion (`synthesis` and `supersede` have no local statement of the rule); the dependent-cascade `needs-update` rule (Setting Status condition 4 already blocks the overwrite, and the wording strands a page whose cause the same run resolved); and the `CLAUDE.md` list fix (the enumeration is illustrative, and the proposal's premise that `self-report.md` was already named is false). `CLAUDE.md` left unedited.
- Verification: scanner sweep clean across all 15 skills, 296 tests pass.

## [2026-08-16 20:52] skill-llm-council | lint

- Saved: [[2-outputs/skill-llm-council/skill-llm-council-2026-08-16-2052-lint.md|skill-llm-council-2026-08-16-2052-lint]]
- Full protocol: 10 advisors across two councils, 10 anonymized peer reviews, 2 chair syntheses, meta-chair reconciliation, 13 adversarial refuters.
- Applied 14 edits to `.claude/skills/lint/` (SKILL.md, references/checks.md, references/fixes.md, scripts/sort_chronology.py). Eight load-bearing edits held at the refuter gate; twelve distinct claims were refuted.
- Substantive: Open-threads prune now requires every wiki-page link in an entry to be dead before auto-removal (it could previously delete live orientation on one dangling link); `recover_time` scoped to the entry's own `Saved:`/`Report:` bullet, fixing a false whole-file skip; the verified-hash re-stamp re-confirms its baseline immediately before the edit; two Warning-tier checks moved out of the Info catalogue; `verified_hash` ownership corrected at three sites to match the current schema.
- Four cross-file proposals raised, not applied: a `locator_page_mismatch` severity question, a unit test for the chronology sorter, a registry-versus-catalogue assertion, and single-sourcing two duplicated regexes.
- Verification: 5 scanners clean on `lint`, 296 tests pass, `checks.md` now diffs clean against the registry apart from the deliberate `caller-determined` split.

