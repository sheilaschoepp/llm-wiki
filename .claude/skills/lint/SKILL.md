---
name: lint
description: "Cheap structural integrity check for the LLM knowledge base. Checks frontmatter, required callout sections, source_count, index drift, broken links, missing source support, stale hot/log structure, and note length. Applies only safe mechanical fixes. Use after ingest (any mode) or on demand. Also use when the user asks to lint, structurally check, or sanity-check the wiki, the vault, or wiki pages/notes, or whether an ingest, forget, or supersede broke anything structurally, or whether their notes are well-formed or something looks broken or wrongly formatted in the wiki — even when they don't say 'lint'. Lints WIKI PAGES under 1-wiki/, not skills: for a skill, SKILL.md, or skill folder, use skill-linter. Lint clears one of audit's two preconditions (page-level structural drift); the other (project-level schema and skill drift) is cleared by consistency. Different from audit, which judges note quality and source support."
---

# lint

Run the cheap mechanical checks. Save a report to `2-outputs/lint/`.

## Purpose

Lint keeps the vault structurally healthy without spending tokens on deep semantic judgement.

The governing boundary: lint *detects* anything decidable by regex or structure without reading the raw source (a few prose-content checks included), but *auto-fixes* only what is uniquely determined and touches frontmatter or block-ID / section-callout structure — never callout body prose. Everything else is detected and handed to `audit`. The Step 3 fix test ((a) + (b)) is this principle applied; the prose-content checks that live in lint are detect-only for the same reason.

## When To Invoke

Use after ingest (any mode), forget, supersede, or any schema-touching page edit. Also use before `audit`: lint clears one of audit's two preconditions; pair with `consistency` (which clears the project-level half) before audit can run.

## When Not To Invoke

- The user wants a semantic editorial pass. Use `audit`.
- Nothing has changed since the last clean lint.
- The wiki is empty and there are no raw sources.

## Procedure

```text
Lint Progress:
- [ ] Step 1: Load memory; run scripts/check_wiki.py
- [ ] Step 2: Walk remaining structural checks
- [ ] Step 3: Apply determinate fixes; re-run the script until clean (baseline regression guard, max 3 iterations)
- [ ] Step 3b: Verified-hash sweep — run body_hash.py on every verified page lint mutated; confirm each was re-stamped (allowlisted fix) or reset to draft
- [ ] Step 4: Save lint report
- [ ] Step 5: Log the run
```

Three terms recur below and carry the verification logic — fix them before running:

- Hash baseline — each `verified` page's `body_hash.py` output captured in Step 2 (page as-is, before any Step 3 fix), compared to its `verified_hash:`. Retain, per page, the match/mismatch result AND the set of pages that were `verified` at the start and whose body you mutate this run: the Step 3 re-stamp branch reads the former, the Step 3b sweep iterates the latter. `check_wiki.py` now emits `verified_hash_mismatch`, so it recomputes each page's *current* hash every pass — but it does not preserve the Step-2 baseline match state or the mutated-page set, which is the run-state the re-stamp-vs-demote decision needs and the script's single-pass finding cannot carry.
- Regression baseline — the full set of `(check_id, file)` pairs from the Step 1 script run, recorded before the first fix; the Step 3 loop diffs against it to catch a fix that introduces a new finding. Distinct from the hash baseline — "baseline" unqualified is ambiguous.
- Re-stamp vs demote — an allowlisted verification-neutral format fix (`callout_block_id`, `wikilink_pipe_spacing`, `citation_bracket_style`, `embed_not_isolated`) recomputes and rewrites `verified_hash:` in the same edit, keeping `status: verified`; any other unmarked body change resets the page to `draft`. (The allowlist membership, the lint/audit partition, the text-content exclusion, and the re-stamp/demote rule are the shared operational spec `.claude/skills/multi-skill/references/verification-neutral-fixes.md`.) An "owned-drift" `check_id` is one whose fix the Step 3 auto-fix list owns. The script also emits `verified_anchor_unaudited` (Critical) when a `verified` page's locator anchor changed vs git HEAD — not auto-fixed; report it (remedy: demote, mark `*[unverified]*`, or re-verify via `audit`).

1. **Load memory, then run the deterministic script.** First read `.claude/skills/lint/lint-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` to apply prior corrections about which findings the user has tuned, what counts as auto-fixable here, and any project-specific rules layered onto the script's defaults. Then run the script:

```bash
python3 .claude/skills/lint/scripts/check_wiki.py "1-wiki"
```

Parse the JSON findings.

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
   - Length caps (the script does not count words): concept/entity pages over 400 words (atomicity drift signal; pages this long usually contain more than one idea), syntheses over 600 words (entry-point pages should stay scannable), bullets over about 35 words (compression drift; a long bullet usually wants to be a sub-bullet list or its own page).
   - Schema-staleness warning: check `git log -1 --format=%ad -- CLAUDE.md README.md .claude/skills` against the newest `2-outputs/consistency/consistency-*.md`. If the project layer has changed since the last consistency run, surface a single Info-level finding telling the user to re-run consistency. Do not block, since lint runs too often to require a hard precondition.
   - AI-writing tells (mechanical): read `a-archive/style/ai-writing-tells.md` and scan wiki page bodies for the regex-friendly tells only — banned vocabulary words from the high-density list (delve, robust, intricate, pivotal, tapestry, showcase, etc.), em-dash density above ~3 per page, curly-quote leakage when straight quotes were intended, `:contentReference[oaicite:`, `oai_citation`, `turn0search`, `↩` footnote arrows, `Subject:` headers in page bodies, UTM parameters in URLs, and bracketed placeholder leakage (`[Your Name]`, `[Insert Date]`). Semantic tells (puffing tone, conclusion templates, broader-context reflex) belong in `audit`, not here.
   - Verified-hash drift (`verified_hash_mismatch`): now detected deterministically by the Step 1 script — `check_wiki.py` emits `verified_hash_mismatch` for each `status: verified` page whose body hash does not match `verified_hash:`, or that has none. The Step 2 action here is not detection but capturing the **hash baseline** the Step 3 re-stamp-vs-demote decision needs: for each `verified` page, record whether `body_hash.py` matched `verified_hash:` *before* any Step 3 fix. A mismatch, or a `verified` page with no `verified_hash:`, means the page's *checked content* changed since `audit` verified it. `body_hash.py` masks `*[unverified]*` claim lines before hashing (CLAUDE.md → Page Status: verification is claim-level), so adding or editing an `*[unverified]*`-marked claim does **not** trip the hash — the page stays `verified` with that claim as the pending delta; only a change to *unmarked* (checked) content trips it and demotes the page. The mask is line-scoped: only the line carrying the marker is dropped, so a marked claim that wraps onto a continuation `>` line still counts that continuation toward the hash — keep a marked claim on its single bullet line. The marker may be added only to a genuinely new or changed claim: appending `*[unverified]*` to a pre-existing *unmarked* verified claim to keep the hash from tripping is hash-evasion and is not permitted — the marker is a process state for unchecked claims, not an opt-out of verification. lint cannot detect this (it reads neither the raw nor the page's prior state); it is a prose contract the editor must honour. A page with no markers hashes exactly as before, so existing stamps stay valid. This Step 2 check is the **hash baseline**: the page as-is, before any Step 3 fix. A baseline mismatch is an unmarked change made *outside* this lint run; lint cannot tell a claim edit from an allowlisted edit a hand-editor forgot to re-stamp, so it conservatively demotes (CLAUDE.md → Page Status: an allowlisted verification-neutral edit made outside a re-stamping skill is demoted, the safe fallback). Lint's *own* allowlisted format fixes do the opposite — they re-stamp rather than demote; see the `verified_hash_mismatch` fix in Step 3. Separately, a non-`verified` page (`draft`/`needs-update`) that still carries a `verified_hash:` has a stale hash from an earlier demotion — strip it (a non-`verified` page carries none).

3. **Apply every determinate fix.** Apply every fix that is mechanically determined (one correct fix, no content authorship) at every severity level, not only the cases listed here; the list is the common set, not the limit. A fix beyond the listed set is permitted only when both hold: (a) the corrective edit is uniquely determined with no wording choice, and (b) it touches frontmatter, a block-ID / section-callout *structure*, or the determinate catalogue/orientation list bookkeeping in `index.md` and `hot.md` (a list entry fixed by disk state), never callout body prose. A finding whose fix would split, merge, reword, compose, or otherwise restructure page content (or hot.md/log.md body text) is not lint's to make: lint records it (it appears in the report) and `audit` carries it out. Determinate fixes include:
   - Correct `source_count` to match `sources:`.
   - Touch `updated:` when a page was mechanically changed.
   - Fix `1-wiki/index.md` drift: add an `index_missing_entry` page to its section (`## Sources` / `## Entities` / `## Concepts` / `## Syntheses`, chosen by the page's folder) as a path-qualified wikilink whose display is the page's H1 title; delete an `index_stale_entry` line whose target file no longer exists. Both are determinate from disk (this is the catalogue-bookkeeping half of the (b) clause above; line 102's confirmation step assumes it ran). Rule: CLAUDE.md → Hot, Index, And Log; Workflow Rules.
   - Insert missing required callouts with the page-type's empty placeholder (`> - None noted` for source pages, `> - None yet` for concept/entity and synthesis pages). Trigger: any `section_order` finding whose message begins with `Missing required sections`. Insertion point — deterministic anchor walk. Let `SCHEMA` be the ordered `REQUIRED_SECTIONS` list for the page type in `.claude/skills/lint/scripts/check_wiki.py` (the canonical order). Process missing sections in `SCHEMA` order, one at a time, re-reading the body after each insert so anchors reflect prior inserts in the same run:
       1. Find the nearest callout that is *present* (or was inserted earlier this run) and precedes the missing one in `SCHEMA`. Insert the new callout immediately after that callout's closing `> ^{slug}` block-ID line, separated by exactly one blank line.
       2. If no `SCHEMA`-earlier callout is present (the missing section is, or would be, the first body section), insert it at the top of the body: after the closing frontmatter `---`, the single H1 (`# Title`) line, and the one blank line after the H1 — never above the H1. The H1 always stays the first body line; callouts never precede it.
       3. Consecutive missing sections are inserted in `SCHEMA` order; because each just-inserted callout is now "present", the next one anchors after it, so a run of missing sections lands in correct relative order instead of stacking at one anchor.
       Guard: if the body has no H1, or more than one H1, do not insert — record the `section_order` finding for `audit` instead (the anchor walk assumes exactly one H1; inserting into a malformed page risks structural corruption).
       Format each inserted callout as `> [!{slug}] {Title}`, one blank quoted line (`>`), the placeholder bullet, then the block ID `> ^{block-id}` as the last quoted line — no blank `>` between the placeholder and the block ID (see `CLAUDE.md` → Callout Block IDs). The `{block-id}` is the kebab-case of the callout title, which equals `{slug}` for most callouts but expands an abbreviated type (`[!why]` → `^why-it-matters`, `[!disconfirming]` → `^disconfirming-evidence`, `[!what-would-change-this]` → `^what-would-change-this-answer`). Do not auto-fix `section_order` findings about unknown extras or wrong-order; those need manual reorder or removal.
   - Fix `callout_block_id` findings: every callout carries its block ID `> ^<block-id>` as the last line inside the `>` block, where `<block-id>` is the kebab-case of the callout title (`{slug}` for most callouts; the expanded form for the three abbreviated types above, e.g. `^why-it-matters` on a `[!why]` callout). Missing → insert `> ^{block-id}` as the callout's last quoted line. Wrong value (`^{other}` on a callout) → rewrite it to the expected `^{block-id}`. Not last → move it to the last quoted line. Duplicated → keep one `> ^{block-id}` as the last line and delete the rest. The expected ID is determined by the callout type, so each fix is determinate. (See `CLAUDE.md` → Callout Block IDs.) A *value rewrite* (wrong → expected) changes the anchor an inbound `[[page#^{old-id}|…]]` section link resolved to; `check_wiki.py` does not traverse `#^` anchors, so such a link is not flagged as dangling. The exposure is narrow — a correctly-targeted inbound link already used the expected ID and is repaired, not broken, by this fix — but when correcting a block-ID value, a quick grep for `#^{old-id}` across `1-wiki/` catches any inbound link that targeted the wrong anchor.
   - Prune `hot.md` Open threads — do not author them. Auto-remove only an Open-threads entry that meets the determinate close condition (a): its wikilink target no longer exists. Condition (b) — target page has `source_count >= 2`, `status` is not `needs-update`, and its `Contradictions` callout (or, for syntheses, `Tensions`) is the empty placeholder — is a *heuristic* proxy for "thread closed", not a determinate signal: a 2-source non-`needs-update` page can carry a genuinely open thread whose follow-up was never written as a contradiction. So do **not** silently delete on (b); surface it as a `hot_log_stale` finding ("candidate-closed thread — confirm before pruning") for the user or `audit`, the same way thread *creation* is surfaced rather than auto-done. Deleting orientation prose on an editorial proxy would violate lint's own safe-fix boundary (frontmatter/structure only, never body prose). Leave every surviving entry's wording untouched. Never add a new Open-threads entry and never rephrase an existing one: deciding a thread is *open* (and how to state it) is editorial judgement, not a mechanical fix — in particular, do not auto-prune or auto-create on a coverage/quality call like "low-coverage", which has no mechanical definition. When a current `needs-update` / contradiction-bearing page has no Open-threads entry, surface that as a `hot_log_stale` finding for the user or `audit` rather than auto-writing the thread.
   - Trim `hot.md` Recent activity to five entries (keeps the orientation cache short enough to read at a glance).
   - Remove hot entries pointing to missing pages. Exception: a Recent-activity link pointing into `2-outputs/` at a check report that no longer exists on disk (deleted under the former retention cap, now lifted, or otherwise removed by hand) is an expected dangler, not a missing-page entry — leave it.
   - Recover determinate missing times and re-sort `log.md` and `hot.md` Recent activity newest-first (`chronology_missing_time` recoverable case + `chronology_out_of_order`): run `python3 .claude/skills/lint/scripts/sort_chronology.py`. Determinate — a stable sort on each entry's `[YYYY-MM-DD HH:MM]` header; entry bodies move with their header, no prose changes, equal timestamps keep their order, idempotent. Before sorting it fills a missing `HH:MM` from the entry's own linked report filename (`2-outputs/…-YYYY-MM-DD-HHMM-…`) when exactly one such link matches the entry's date — transcribed, never invented, never from git. The script skips a file (untouched) only if an untimed entry has no recoverable link; that residual `chronology_missing_time` is the part still not auto-fixable (recover the time from the report or git by hand, then re-run). The fixer lives at `.claude/skills/lint/scripts/sort_chronology.py`. Rule: CLAUDE.md → Hot, Index, And Log.
   - Do not auto-rotate `log.md`. When it exceeds 1000 lines, surface a `hot_log_stale` Info finding recommending the user rotate it (move the oldest entries into an archive of their choosing) — moving content and inventing a durable file is content authorship and would create a file the schema does not document, so it is the user's call, not a lint auto-fix. (If automated rotation is wanted later, `CLAUDE.md` → Hot, Index, And Log should first document the archive file.)
   - Collapse whitespace around a wikilink pipe (`wikilink_pipe_spacing`): rewrite `[[path | display]]` / `[[path| display]]` / `[[path |display]]` to `[[path|display]]`. Determinate — within each `PIPE_SPACING_RE` match (the script locates the spans), replace the pipe-and-padding `\s*\|\s*` with a bare `|`; only the padding adjacent to the `|` is removed, inside the matched wikilink span; never touch a `|` outside `[[...]]` (table cells) or inside inline code. Idempotent: an already-bare `|` does not change.
   - Convert a superseded square-bracket Form 2 citation to round brackets (`citation_bracket_style`): rewrite `[[[1-wiki/sources/X.md|X]]; [[0-raw/papers/X.pdf#page=N|sec. Y, p. M]]]` to `([[1-wiki/sources/X.md|X]]; [[0-raw/papers/X.pdf#page=N|sec. Y, p. M]])`. Determinate — swap only the outer literal `[` `]` (the wrap) for `(` `)`; the inner source-page and raw deep-link wikilinks are untouched. Apply the swap only where the detector flagged it — within the code-masked, `Sources`-callout-blanked scan the check uses (`_blank_sources_callout(_mask_code_spans(body))`), never inside an inline-code span or a verbatim quote, where a `[[[…]]]`-shaped example is a literal, not a citation, and must stay byte-identical (`CLAUDE.md` → Page Status text-content exclusion); a swap reaching a masked span would ride through this verification-neutral re-stamp fix as a silent false green. `SQUARE_CITATION_RE` is the exact pattern (it also handles the multi-locator form). Idempotent: it never matches the round form. Rule: CLAUDE.md → Source Support And Verification (Form 2 is round-bracketed).
   - Isolate an image embed (`embed_not_isolated`): a standalone embed line (`> ![[…]]`, its only content one embed) must sit in its own block — a blank quoted line (`>`) directly above AND below it, or Obsidian lazy-continues the embed into the adjacent bullet/line and mis-renders. Insert a blank `>` line on whichever side the finding names (`above`, `below`, or `above and below`). Determinate — only blank `>` lines are inserted, no prose touched; idempotent (an already-isolated embed is left alone). Rule: CLAUDE.md → Attachments / Source Pages.
   - Handle a `status: verified` page whose body hash does not match `verified_hash:` (`verified_hash_mismatch`), and a `verified` page with no `verified_hash:` at all. There are two cases, and they differ by whether the change is a verification-neutral allowlisted one (CLAUDE.md → Page Status):
       - **Verification-neutral fix lint applied this run → re-stamp, do not demote.** When *every* body change to the page this run is an allowlisted verification-neutral fix of lint's own — `callout_block_id`, `wikilink_pipe_spacing`, `citation_bracket_style`, `embed_not_isolated` (one such fix, or several across loop iterations, but nothing else) — and the page's Step 2 baseline hash *matched* `verified_hash:` before this run (so it was verification-stable when lint started), the fixes change no claim. Apply the fix, touch `updated:`, and **re-stamp** `verified_hash:` to the fresh `body_hash.py` output in the *same* edit, keeping `status: verified`. This is the verification-neutral re-stamp the schema authorizes — a block-ID or pipe-spacing correction must not un-verify a page.
       - **Any other mismatch → reset to `draft`.** When the Step 2 baseline hash did *not* match (an unmarked change was made outside this lint run — possibly a claim edit lint cannot see, or an allowlisted edit a hand-editor did not re-stamp), or lint made a *non-allowlisted* body change this run (inserting a missing required callout): reset `status: verified → draft`, touch `updated:`, and remove the now-stale `verified_hash:` in that same edit (a non-`verified` page carries none; `audit` re-adds it on the next verify) — never recompute it to preserve verified status on a non-neutral change. Also strip a `verified_hash:` found on a page that is already `draft` or `needs-update` (a stale hash left by an earlier demotion): a non-`verified` page never carries one.
       Editing a verified page is allowed: an incremental claim edit keeps it verified via the `*[unverified]*` marker (CLAUDE.md → Page Status), an allowlisted format fix keeps it verified via the re-stamp above, and any *other* unmarked body change demotes — the correct outcome, not a barrier.
   - Do not edit `hot.md` Active focus.

   After applying auto-fixes, iterate the deterministic layer until it is clean. This is a loop, not a single closing re-run. Before the first iteration, record the regression baseline: the full set of `(check_id, file)` pairs from the Step 1 script run. The Step 2 LLM walk and `.claude/skills/lint/scripts/body_hash.py` are *not* part of this loop — they run once in Step 2 (see the verified-hash bullet there); the loop re-runs only `check_wiki.py`.

   1. Re-run `python3 .claude/skills/lint/scripts/check_wiki.py "1-wiki"` as one fresh, complete pass. A mechanical fix can break a check it did not touch, so re-run the whole script, not a spot-check of the lines just edited.
   2. **Regression guard.** Diff this pass's `(check_id, file)` set against the recorded baseline. A pair at `error`/Critical or `warning`/Warning severity that was *not* in the baseline is a fix-introduced regression: stop the loop, leave the page as-is, and surface it under Auto-Fixed as "fix-introduced finding — needs review", naming the fix that preceded it. (Exclude `verified_hash_mismatch` from this regression diff even though `check_wiki.py` now emits it: a mismatch on a `verified` page lint just mutated is expected — lint re-stamps or demotes it in the same edit, Step 3 — not a fix-introduced structural regression, so it must not stop the loop. The re-stamp/demote branch and the Step 3b sweep own it.) A fix that creates a new structural problem is not determinate and must not cascade.
   3. If the pass surfaces new auto-fixable drift that is *not* a regression, apply it (per the auto-fix list above) and return to step 1. When a fix edits a `verified` page body, handle that page in the same edit per the `verified_hash_mismatch` bullet — re-stamp `verified_hash:` for an allowlisted format fix on a baseline-matched page, or reset `verified → draft` otherwise — so it is not deferred to a later pass.
   4. A pass is **clean** when it introduces no regression (step 2) and reports no *auto-fixable* drift — where "auto-fixable drift" is the closed set of `check_id`s the auto-fix list above owns. Every other finding is expected output, not drift, and never keeps the loop spinning: all Warning and Info findings the auto-fixer does not own, plus the standing repo-state Criticals (`STANDING_NONBLOCKING` in `check_wiki.py`: `raw_without_source_page`, `uningested_raw_source`, `status_needs_update`) and the non-auto-fixable Criticals (`file_field_unresolved`, `embed_unresolved`, `missing_index`, `frontmatter_missing`, synthesis `zero_source_page`).
   5. **Non-convergence guard.** The owned auto-fix set is constrained and idempotent (a `source_count` correction, a callout insert, a block-ID or pipe-spacing fix does not undo itself), so a true fix/undo oscillation should not arise; the failure mode to catch is a fix that does not stick. If the same owned-drift `check_id` is still reported for the same page after two fix attempts, stop: leave the page as-is and surface that `check_id` under Auto-Fixed as "fix did not converge — needs manual resolution". Hard bound: stop after 3 iterations regardless, and surface any unresolved owned-drift findings under Auto-Fixed rather than spinning.

   The Step 2 walk is not part of this loop: it runs once, and its findings are reported, not auto-fixed. After the loop, confirm the targeted findings (`source_count_mismatch`, `index_missing_entry`/`index_stale_entry`, hot entries pointing to missing pages, `section_order` "Missing required sections") cleared. If any persist, the auto-fix was incorrect; surface the specific finding in the report under Auto-Fixed instead of silently leaving drift.

   **Step 3b — verified-hash sweep.** Re-run `python3 .claude/skills/lint/scripts/body_hash.py {page}` on every page whose body lint mutated this run that was `verified` at the start, and confirm each was handled per the `verified_hash_mismatch` bullet — its fresh hash either matches a re-stamped `verified_hash:` (allowlisted format fix on a baseline-matched page, still `verified`) or the page was reset to `draft` with the hash stripped (otherwise). `check_wiki.py` now emits `verified_hash_mismatch`, so a mishandled mutated page would also surface on the final loop pass; this sweep stays as the explicit confirmation (and the exhaustive-superset fallback below), since the loop's regression diff deliberately excludes that finding. A mutated page left `verified` with a stale hash (neither re-stamped nor reset) is a missed handling: fix it before writing the report. If you are not certain the mutated-page set is complete (a long multi-iteration run, or a crashed-and-resumed run), fall back to re-hashing every `status: verified` page rather than trusting the agent-held set — a safe superset whose extra pages hash as clean no-ops, since neither the loop nor the script persists which pages were touched. (`body_hash.py` errors rather than hashing the whole file when frontmatter is malformed; an error here flags a page whose `---` delimiters need repair, not a content change.)

4. **Compile the report** at `2-outputs/lint/lint-YYYY-MM-DD-HHMM.md`. Obtain the timestamp at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context provides the date but not the current minute). If a lint report already exists for the same minute, do not overwrite it; append one of these suffixes: `-rerun` (re-run with no changes since the prior report), `-after-fixes` (after applying fixes from the prior report), or an ordinal `-2`/`-3`/... for further runs. Cite the `check_id` and short name from `references/checks.md` in each finding row so the user can refer to checks by their canonical ID (`source_count_mismatch`, `verified_hash_mismatch`, etc.).

   **Emit the audit-blocking gate field.** Write report frontmatter with a deterministic `result:` field so `audit` can gate on it without re-parsing prose (matching the `result:` field consistency reports already carry). The script emits `severity: error | warning | info`; in the report these render as **Critical / Warning / Info** respectively (CLAUDE.md → Severity vocabulary — wiki-facing reports use critical/warning/info). A finding is **audit-blocking** when it is a Critical whose `check_id` is *not* one of the standing repo-state items audit cannot act on — the `STANDING_NONBLOCKING` set in `check_wiki.py` (`raw_without_source_page`, `uningested_raw_source`, and `status_needs_update`) — note `uningested_raw_source` is CLAUDE.md's name for the condition the script actually emits as `raw_without_source_page`, so the JSON you filter only ever carries `raw_without_source_page`; both sit in the set for CLAUDE.md-verbatim parity. The same set drives the script's exit code, so exit code, `result:`, and the audit gate stay consistent. Warnings and Info never block: the non-auto-fixable Warnings are audit's authored-tier worklist (Step 3), not structural drift audit would audit against. Compute `audit_blocking` mechanically from the final post-loop `check_wiki.py` JSON — the count of findings with `severity == "error"` whose `check_id` is not in `STANDING_NONBLOCKING` — rather than hand-tallying the rendered report, and take it from the final pass after the non-convergence guard has fired, never an intermediate pass (a fix may not converge, leaving a blocking Critical the gate must reflect). The script computes the identical predicate for its exit code, so the two stay consistent by construction. Set `result: blocking` when that count is > 0 and `result: clean` otherwise, and list each blocking finding in the `## Audit-Blocking` section so a reader sees what must clear.

Report structure:

```markdown
---
type: lint
date: YYYY-MM-DD
result: <clean|blocking>   # compute per Step 4 from the final post-loop pass — do not leave the literal `clean`
audit_blocking: <N>        # count of unresolved audit-blocking findings
critical: N            # all Criticals, incl. standing (matches the script's error count)
critical_blocking: N   # critical minus the STANDING_NONBLOCKING set — the count that matters
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
```

5. **Prepend log entry.**

```markdown
## [YYYY-MM-DD HH:MM] lint | {N} findings ({C} critical, {W} warning, {I} info)
- Saved: [[2-outputs/lint/lint-YYYY-MM-DD-HHMM.md|lint-YYYY-MM-DD-HHMM]]
- Auto-fixed: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]] (or "none")
```

## Checks

The full check catalogue — every `check_id`, its severity, and what it means — is in `references/checks.md`, split into **Script-emitted** (the canonical ids `check_wiki.py` prints; cite them verbatim in report rows) and **LLM-walk** (the Step 2 checks with no `check_id`, cited by short name).

`python3 .claude/skills/lint/scripts/check_wiki.py --list-checks` prints the script's `CHECKS` registry as JSON and is the source of truth for ids and severity; the Script-emitted half of `references/checks.md` must stay diffable against it (every id appears in both).


## Tests

The scripts require Python 3.10+ (they use `X | None` unions and built-in generics); the test suite uses Python's stdlib `unittest` (no extra dependency).

Regression tests for `check_wiki.py` live in `scripts/tests/test_check_wiki.py` — they pin the `CHECKS` registry, the auto-fix transforms (callout block IDs, citation bracket style, embed isolation, pipe spacing), and the specific bug classes each check guards. Regression tests for `body_hash.py` live in `scripts/tests/test_body_hash.py` — they pin the `*[unverified]*` line-masking and the malformed-frontmatter error behaviour the verified-hash sweep depends on. After changing `check_wiki.py` or `body_hash.py`, run:

```bash
python3 -m unittest discover -s .claude/skills/lint/scripts/tests
```

`unittest` ships with Python, so the suite needs no install. Running it is not a lint gate: if it cannot be run, note in the report that the script regression tests were not run rather than treating that as a lint failure.

## Limits

- Lint does not decide whether a note is intellectually good. Use `audit`.
- Lint does not read raw source content (out of scope and token-expensive; that is `audit`'s job).
- Never modify `0-raw/`: raw sources are immutable evidence; mutations break the audit trail back to the original PDF/article.
- Only mechanical fixes are automatic; anything requiring semantic judgement belongs in `audit`, where the user has opted into the deeper pass.
