---
name: lint
description: "Cheap structural integrity check for the LLM knowledge base. Checks frontmatter, required callout sections, source_count, index drift, broken links, missing source support, stale hot/log structure, and note length. Applies only safe mechanical fixes. Use after ingest (any mode) or on demand. Also use when the user asks to lint, structurally check, or sanity-check the wiki, the vault, or wiki pages/notes, or whether an ingest, forget, or supersede broke anything structurally, or whether their notes are well-formed or something looks broken or wrongly formatted in the wiki — even when they don't say 'lint'. Lints WIKI PAGES under 1-wiki/, not skills: for a skill, SKILL.md, or skill folder, use skill-linter. Lint clears one of audit's two preconditions (page-level structural drift); the other (project-level schema and skill drift) is cleared by consistency. Different from audit, which judges note quality and source support."
---

# lint

Run the cheap mechanical checks. Save a report to `2-outputs/lint/`.

## Purpose

Lint keeps the vault structurally healthy without spending tokens on deep semantic judgement.

The governing boundary: lint *detects* anything decidable by regex or structure without reading the raw source (a few prose-content checks included), but *auto-fixes* only what is uniquely determined and touches frontmatter or block-ID / section-callout structure — never callout body prose. Everything else is detected and handed to `audit`. The Step 3 fix test — auto-fix only when the correction is uniquely determined *and* touches frontmatter / block-ID / section-callout structure or determinate index/hot bookkeeping, never callout body prose — is this principle applied; the prose-content checks that live in lint are detect-only for the same reason.

## When To Invoke

Use after ingest (any mode), forget, supersede, or any schema-touching page edit. Also use before `audit`: lint clears one of audit's two preconditions; pair with `consistency` (which clears the project-level half) before audit can run.

## When Not To Invoke

- The user wants a semantic editorial pass. Use `audit`.
- Nothing has changed since the last clean lint.
- The wiki is empty and there are no raw sources.

## Procedure

```text
Lint Progress:
- [ ] Step 1: Load memory; run .claude/skills/multi-skill/scripts/check_wiki.py — pin this pre-fix pass as BOTH baselines (regression + hash) before any Step 3 fix; confirm the run completed (see Step 1)
- [ ] Step 2: Walk remaining structural checks
- [ ] Step 3: Apply determinate fixes; re-run the script until clean (baseline regression guard, max 3 iterations)
- [ ] Step 3b: Verified-hash sweep (runs at the tail of Step 3, before Step 4) — run body_hash.py on every verified page lint mutated; confirm each was re-stamped (allowlisted fix) or reset to draft
- [ ] Step 4: Save lint report
- [ ] Step 5: Log the run
```

Two base terms are used as givens throughout, defined once here: `verified_hash:` is the SHA-256 of a page's body with `*[unverified]*`-marked claim lines excluded (computed by `.claude/skills/multi-skill/scripts/body_hash.py`), which `audit` writes when it fact-checks a page `verified` (CLAUDE.md → Page Status). An `*[unverified]*` marker tags a non-obvious claim added since the last fact-check (a changed claim demotes the page instead); `body_hash.py` masks those lines, so a marked claim rides a `verified` page without tripping the hash (CLAUDE.md → Bullet Markers).

Four run-state terms recur below and carry the verification logic. They cross-define and are *applied* in Step 3 — read them now for orientation, each used at the step noted:

- Hash baseline — which `verified` pages were already drifted *before* this run, i.e. the pages carrying a `verified_hash_mismatch` finding in the Step 1 `check_wiki.py` pass. That pass runs before any fix and hashes with the same `body_hash.py` the re-stamp decision uses, so its finding set *is* the pre-fix baseline: a `verified` page absent from it was baseline-matched (re-stamp-eligible), one present (or with no `verified_hash:`) was baseline-mismatched (demote-only). Pin that finding set before the first Step 3 fix — do not re-derive it by running `body_hash.py` after a fix (a fix may have made the hash match) or read it off a later loop pass (which overwrites the pre-fix state). Separately retain the set of pages that were `verified` at the start and whose body you mutate this run — the Step 3b sweep iterates that mutated-page set.
- Regression baseline — the full set of `(check_id, file)` pairs from the Step 1 script run, recorded before the first fix; the Step 3 loop diffs against it to catch a fix that introduces a new finding. Distinct from the hash baseline — "baseline" unqualified is ambiguous. Both baselines come from the same Step 1 pass, so pin that pass once, before any mutation.
- Re-stamp vs demote — on a `verified` page lint mutated, the choice between rewriting `verified_hash:` in the same edit (an allowlisted format fix — `callout_block_id`, `wikilink_pipe_spacing`, `citation_bracket_style`, `embed_not_isolated` — on a baseline-matched page, keeping `status: verified`) and resetting to `draft` (any other unmarked body change). The full rule is applied at Step 3's `verified_hash_mismatch` fix; membership, the lint/audit partition, the text-content exclusion, and the re-stamp/demote rule are the shared operational spec `.claude/skills/multi-skill/references/verification-neutral-fixes.md`.
- Owned-drift — a `check_id` whose fix the Step 3 auto-fix list owns; the loop's clean-test keys on this set.

The script also emits `verified_anchor_unaudited` (Critical) when a `verified` page's locator anchor (the `sec.`/`fig.`/`tab.`/`app.` structural label inside a citation's `#page=N` deep-link) changed vs git HEAD — not auto-fixed; report it (remedy: demote, mark `*[unverified]*`, or re-verify via `audit`). It likewise emits `locator_page_mismatch` (Critical) when a `p. M` locator contradicts what the pagination map says its physical page prints, and `pagination_map_unregistered` (Info) for a raw cited but unregistered — both report-only (the fix edits citation body prose, or registers the raw, neither a mechanical lint fix): `audit` or the user resolves them.

1. **Load memory, then run the deterministic script.** First read `.claude/skills/lint/lint-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` to apply prior corrections about which findings the user has tuned, what counts as auto-fixable here, and any project-specific rules layered onto the script's defaults. Then run the script:

```bash
python3 .claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"
```

Parse the JSON findings. Guard the parse: `check_wiki.py` prints its findings JSON only on a run that ran to completion, so **empty or unparseable stdout is not "zero findings" — it is a run that could not complete.** A wrong or missing wiki path exits 2, and a crashed check aborts the battery with a traceback on stderr; both print nothing to stdout, whereas a genuinely clean wiki prints `[]` (non-empty and parseable). The exit code alone does not distinguish these — a crashed check exits 1, the same as a normal blocking run — so key on the stdout: if it is empty or does not parse as a JSON array, stop and write the report with `result: blocking` naming the failure, rather than letting it fall through to Step 4's `audit_blocking` count (which would read zero findings and certify an un-run or crashed wiki to `audit` as clean). This mirrors the empty-stdout guard `consistency` already applies to its own gate. Retain this completed pre-fix pass as the pinned snapshot both baselines are read from — its `verified_hash_mismatch` finding set (the hash baseline, used in Step 2) and its full `(check_id, file)` set (the regression baseline, diffed in the Step 3 loop) — before applying any Step 3 fix, because a fix mutates both sets and neither can be re-derived afterward.

2. **Walk only the checks the script can't do.** The script's coverage is exactly the set of `check_id`s it emits. The **Script-emitted** subsection of `references/checks.md` is the authoritative enumeration; the script's module docstring lists only a representative subset, not all of them, and the runtime source of truth is the set of `check_id`s actually present in the JSON output. Do not re-run any check whose `check_id` appears in that output. Walk only the **LLM-walk** checks below (the ones the script never emits), grouped by whether the bullet layers on top of a script finding or is a check the script does not touch at all:

   *Extensions to script findings* (the script catches a related case; layer this on top):
   - Source pages whose `Concepts and Entities` callout points to missing concept/entity pages (the script's `concept_source_asymmetry` enforces forward/reverse agreement but not link resolution to a file that exists). (The reverse direction — `sources:` entries pointing at deleted source pages — is now deterministic via `source_link_unresolved`.)
   - Concept/entity pages with more than one image embed (the script catches the structural case via `concept_multi_image`; double-check after auto-fixes have moved embeds around).
   - Connection-graph reciprocity (`missing_reciprocal_connection`): if page A's `Connections` makes an explicit relationship to `[[B]]`, B's `Connections` should reciprocate. This is the LLM-walk analogue of the script's deterministic `missing_reciprocal_contradiction` (which already covers the Contradictions/Tensions graph — do not redo it here).

   *Independent checks the script doesn't touch* (run these as fresh checks):
   - Broken wikilinks and missing raw-file targets (the script does not traverse links to confirm the target file exists). Exception: `log.md` / `hot.md` links pointing into `2-outputs/` at check reports that no longer exist on disk (deleted under the former retention cap, now lifted, or otherwise removed by hand) are expected danglers, not findings. (Link *path-qualification* — bare-basename targets — is now script-checked via `bare_basename_link`; this walk is only about whether the target resolves.)
   - Concept/entity pages that still use old line-by-line citation clutter.
   - Source pages missing useful `Evidence` when they make detailed claims.
   - Hot file drift: Recent activity entries that don't appear in `log.md`; Open threads pointing at pages that no longer have low coverage / `needs-update` / contradictions; Watchlist entries pointing at missing pages.
   - Log coverage for pages updated today.
   - Length caps (the script does not count words): concept/entity pages over 400 words of prose (atomicity drift signal; pages this long usually contain more than one idea), syntheses over 600 words of prose (entry-point pages should stay scannable), bullets over about 35 words (compression drift; a long bullet usually wants to be a sub-bullet list or its own page). Count rendered prose only — the display text and body words — not the inline-citation machinery (source-page wikilink targets and raw deep-link paths), which inflates the raw count without signalling the multi-idea drift the cap proxies; a single-idea page long only from many inline citations is not over the cap (`CLAUDE.md` → Length). Length alone never forces a split: it is a review signal `audit` owns, carried out only when the page genuinely holds more than one idea.
   - Schema-staleness warning: check `git log -1 --format=%ad -- CLAUDE.md README.md .claude/skills` against the newest `2-outputs/consistency/consistency-*.md`, **and also `git status --porcelain -- CLAUDE.md README.md .claude/skills`** for uncommitted edits the git-log date misses (a git-log date does not move on an uncommitted working-tree change — the same hole `audit` Step 2 closes). If the project layer has changed since the last consistency run — a committed change postdating the report, or any uncommitted change to those paths — surface a single Info-level finding telling the user to re-run consistency. Do not block, since lint runs too often to require a hard precondition.
   - AI-writing tells (mechanical): read `a-archive/style/ai-writing-tells.md` and scan wiki page bodies for the regex-friendly tells only — banned vocabulary words from the high-density list (delve, robust, intricate, pivotal, tapestry, showcase, etc.), em-dash density above ~3 per page, curly-quote leakage when straight quotes were intended, `:contentReference[oaicite:`, `oai_citation`, `turn0search`, `↩` footnote arrows, `Subject:` headers in page bodies, UTM parameters in URLs, and bracketed placeholder leakage (`[Your Name]`, `[Insert Date]`). Semantic tells (puffing tone, conclusion templates, broader-context reflex) belong in `audit`, not here.
   - Verified-hash drift (`verified_hash_mismatch`) is detected by the Step 1 script — `check_wiki.py` emits it for each `status: verified` page whose body hash does not match `verified_hash:`, or that has none. The Step 2 action is not detection but capturing the **hash baseline** the Step 3 re-stamp-vs-demote decision needs — pinned from the completed Step 1 pass (Step 1 prose; *hash baseline* term above), which carries the baseline-matched/mismatched semantics and the do-not-re-derive-after-a-fix caveats. A baseline mismatch means the page's checked (unmarked) content changed *outside* this run: lint cannot tell a claim edit from an allowlisted edit a hand-editor forgot to re-stamp, so it conservatively demotes (the safe fallback) — whereas lint's *own* allowlisted format fixes re-stamp rather than demote (Step 3's `verified_hash_mismatch` fix). `body_hash.py` masks `*[unverified]*` claim lines before hashing, so an incrementally-added marked claim does not trip the hash and the page stays `verified` with that claim pending (a *changed* claim was already in the hash, so marking it moves the hash and demotes the page); the line-scoped mask semantics and the no-hash-evasion contract are CLAUDE.md → Page Status / Bullet Markers, not restated here. Separately, a non-`verified` page (`draft`/`needs-update`) that still carries a `verified_hash:` has a stale hash from an earlier demotion — strip it (a non-`verified` page carries none).

3. **Apply every determinate fix, then loop until clean.** Apply every fix that is mechanically determined (one correct fix, no content authorship) at every severity level. A fix is lint's to make only when both hold: (a) the corrective edit is uniquely determined with no wording choice, and (b) it touches frontmatter, block-ID / section-callout *structure*, or determinate `index.md` / `hot.md` bookkeeping — never callout body prose. A finding whose fix would split, merge, reword, compose, or restructure page content (or `hot.md`/`log.md` body text) is not lint's: lint records it and `audit` carries it out.

   The common determinate fixes — `source_count`, `updated:`, `index.md` drift (`index_missing_entry` / `index_stale_entry`), missing-callout insertion (the deterministic anchor walk), `callout_block_id`, `hot.md` Open-threads pruning / Recent-activity five-entry trim / missing-page removal, chronology re-sort (`.claude/skills/lint/scripts/sort_chronology.py`), `wikilink_pipe_spacing`, `citation_bracket_style`, `embed_not_isolated`, and the `verified_hash_mismatch` re-stamp-vs-demote branch — with their exact transforms, the convergence loop (re-run `check_wiki.py`; the regression guard diffing against the pinned Step 1 `(check_id, file)` baseline; the clean test over the owned-drift set; the non-convergence guard, max 3 iterations), and **Step 3b — the verified-hash sweep** (re-hash with `body_hash.py` every verified page lint mutated and confirm each was re-stamped or reset), are in `references/fixes.md`. Two load-bearing anchors: the verified-hash re-stamp requires a *baseline-matched* page and an allowlisted format fix, else demote to `draft` (the safe fallback, CLAUDE.md → Page Status); and both the regression baseline and the hash baseline are pinned from the pre-fix Step 1 pass and never re-derived after a fix.

4. **Compile the report** at `2-outputs/lint/lint-YYYY-MM-DD-HHMM.md`. Obtain the timestamp at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context provides the date but not the current minute). If a lint report already exists for the same minute, do not overwrite it; append one of these suffixes: `-rerun` (re-run with no changes since the prior report), `-after-fixes` (after applying fixes from the prior report), or an ordinal `-2`/`-3`/... for further runs. Cite the `check_id` and short name from `references/checks.md` in each finding row so the user can refer to checks by their canonical ID (`source_count_mismatch`, `verified_hash_mismatch`, etc.).

   **Emit the audit-blocking gate field.** Write report frontmatter with a deterministic `result:` field so `audit` can gate on it without re-parsing prose (matching the `result:` field consistency reports already carry). The script emits `severity: error | warning | info`; in the report these render as **Critical / Warning / Info** respectively (CLAUDE.md → Severity vocabulary — wiki-facing reports use critical/warning/info). A finding is **audit-blocking** when it is a Critical whose `check_id` is *not* one of the standing repo-state items audit cannot act on — the `STANDING_NONBLOCKING` set in `check_wiki.py` (`raw_without_source_page`, `uningested_raw_source`, and `status_needs_update`) — note `uningested_raw_source` is CLAUDE.md's name for the condition the script actually emits as `raw_without_source_page`, so the JSON you filter only ever carries `raw_without_source_page`; both sit in the set for CLAUDE.md-verbatim parity. The same set drives the script's exit code, so exit code, `result:`, and the audit gate stay consistent. Warnings and Info never block: the non-auto-fixable Warnings are audit's authored-tier worklist (Step 3), not structural drift audit would audit against. Compute `audit_blocking` mechanically from the final post-loop `check_wiki.py` JSON of a run that **completed** — the count of findings with `severity == "error"` whose `check_id` is not in `STANDING_NONBLOCKING` — rather than hand-tallying the rendered report, and take it from the final pass after the non-convergence guard has fired, never an intermediate pass (a fix may not converge, leaving a blocking Critical the gate must reflect). A run whose stdout was empty or unparseable never reaches this computation: Step 1 already stopped it as `result: blocking` (empty stdout is a could-not-complete run, not zero findings), so this count is only ever taken from a genuine JSON-array result. The script computes the identical predicate for its exit code, so the two stay consistent by construction. Set `result: blocking` when that count is > 0 and `result: clean` otherwise, and list each blocking finding in the `## Audit-Blocking` section so a reader sees what must clear.

Report structure:

```markdown
---
type: lint
date: YYYY-MM-DD
result: <clean|blocking>   # compute per Step 4 from the final post-loop pass — do not leave the literal `clean`
audit_blocking: <N>        # count of unresolved audit-blocking findings
critical: N            # all Criticals, incl. standing (matches the script's error count)
critical_blocking: N   # critical minus the STANDING_NONBLOCKING set — equals audit_blocking by construction (every standing item is error-severity); keep the two in sync
warning: N
info: N
---

# Lint - YYYY-MM-DD-HHMM

> Severity: the script emits `error|warning|info`; rendered here as Critical/Warning/Info.

## Summary
- Critical: N total — {critical_blocking} blocking, {N − critical_blocking} standing (expected)
- Warning: N
- Info: N
- Auto-fixed this run: N

## Audit-Blocking
- Criticals that block `audit` — every Critical whose `check_id` is not in the `STANDING_NONBLOCKING` set (`check_wiki.py`: `raw_without_source_page`, `uningested_raw_source`, `status_needs_update`). (or "none")

## Standing (expected, non-blocking)
- The `STANDING_NONBLOCKING` Criticals — `status_needs_update` pages and uningested raws. Ongoing repo states, not drift; listed here so the Critical count above does not read as "something is broken". (or "none")

## Auto-Fixed
- ...

## Critical
- Page - `check_id` (short-name) - description - proposed fix
- (Standing Criticals appear in the Standing section above, not here.)

## Warning
- ...

## Info
- ... (includes user-owned findings lint and audit do not auto-fix: `filename_not_kebab`, `source_stem_mismatch`, `bare_basename_link`)

## Self-report
- {a specific limitation that bit lint this run — a check it lacked, a false positive/negative it produced, a fix it couldn't safely apply} → upgrade: {how the lint skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

5. **Prepend log entry.**

```markdown
## [YYYY-MM-DD HH:MM] lint | {N} findings ({C} critical, {W} warning, {I} info)
- Saved: [[2-outputs/lint/lint-YYYY-MM-DD-HHMM.md|lint-YYYY-MM-DD-HHMM]]
- Auto-fixed: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]] (or "none")
```

## Checks

The full check catalogue — every `check_id`, its severity, and what it means — is in `references/checks.md`, split into **Script-emitted** (the canonical ids `check_wiki.py` prints; cite them verbatim in report rows) and **LLM-walk** (the Step 2 checks with no `check_id`, cited by short name).

`python3 .claude/skills/multi-skill/scripts/check_wiki.py --list-checks` prints the script's `CHECKS` registry as JSON and is the source of truth for ids and severity; the Script-emitted half of `references/checks.md` must stay diffable against it (every id appears in both).

## Optional: Cited-Figure Backstop (Opt-In, Reads Raws)

`.claude/skills/multi-skill/scripts/cited_figure_check.py` is a standalone, detect-only backstop for the cross-source mis-location defect (`CLAUDE.md` → Source Support And Verification, the multi-source-bullet rule): a true, well-formed claim carrying a distinctive figure cited to a raw `#page=N` deep-link whose page does not carry that figure — it passes every structural check, so only opening the cited page catches it. It is deliberately OUTSIDE `check_wiki.py`'s battery: `check_wiki.py` never opens a raw source (Limits), whereas this script opens the cited PDF at physical page N and confirms the figure is there. So it is a separate, opt-in tool — never part of the Step 1–3 structural pass, the Step 3 loop, or the audit-blocking gate.

Run it deliberately (after a large ingest, or when checking cross-source citations), with the `llm-wiki` conda env active (it needs PyMuPDF):

```bash
python3 .claude/skills/multi-skill/scripts/cited_figure_check.py "1-wiki"
```

It prints its own JSON findings (`check_id: cited_figure_off_page`, severity `warning`) to stdout, the same shape as `check_wiki.py` but a separate invocation. Policy: detect-only, never auto-fixed (like a mislabelled locator, it cannot tell which half is wrong — the figure, the page, or the source); decimals and percentages only (bare integers are skipped, where false positives would come from); a figure flags only when it is on none of a bullet's cited pages and every cited page was readable. It cannot catch a mislocated qualitative claim (no figure to match) — that stays ingest's and audit's job (the page-scoped citation check), so it is a backstop for the numeric subset, not a substitute. Exit code 3 means PyMuPDF is missing and the check could not run (not "zero findings"); surface that rather than reading empty output as clean. Findings are advisory: note them in the lint report or hand them to `audit` to open the cited page and settle which half is wrong.


## Tests

The scripts require Python 3.10+ (they use `X | None` unions and built-in generics); the test suite uses Python's stdlib `unittest` (no extra dependency).

Regression tests for `check_wiki.py` live in `.claude/skills/multi-skill/scripts/tests/test_check_wiki.py` — they pin the `CHECKS` registry, the auto-fix transforms (callout block IDs, citation bracket style, embed isolation, pipe spacing), and the specific bug classes each check guards. Regression tests for `body_hash.py` live in `.claude/skills/multi-skill/scripts/tests/test_body_hash.py` — they pin the `*[unverified]*` line-masking and the malformed-frontmatter error behaviour the verified-hash sweep depends on. Tests for the opt-in `cited_figure_check.py` backstop live in `.claude/skills/multi-skill/scripts/tests/test_cited_figure_check.py` — they pin its figure/deep-link parsing, the version-string and bare-integer exclusions, and `check_page` over a fake page-text cache (no PDF opened). After changing `check_wiki.py`, `body_hash.py`, or `cited_figure_check.py`, run:

```bash
python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests
```

`unittest` ships with Python, so the suite needs no install. Running it is not a lint gate: if it cannot be run, note in the report that the script regression tests were not run rather than treating that as a lint failure.

## Limits

- Lint does not decide whether a note is intellectually good. Use `audit`.
- Lint's core pass does not read raw source content (out of scope and token-expensive; that is `audit`'s job). The one exception is the opt-in `cited_figure_check.py` backstop (above), a separate script the user runs deliberately — never part of the structural pass, the Step 3 loop, or the audit-blocking gate.
- Never modify `0-raw/`: raw sources are immutable evidence; mutations break the audit trail back to the original PDF/article.
- Only mechanical fixes are automatic; anything requiring semantic judgement belongs in `audit`, where the user has opted into the deeper pass.
