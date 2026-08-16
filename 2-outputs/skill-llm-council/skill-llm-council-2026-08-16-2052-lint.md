---
skill: lint
date: 2026-08-16
time: "20:52"
councils: 2
advisors: 10
peer_reviews: 10
chairs: 2
refuters: 13
load_bearing_proposed: 13
load_bearing_held: 8
load_bearing_refuted: 12
edits_applied: 14
proposals_raised: 4
---

# skill-llm-council — lint (2026-08-16 20:52)

Full protocol: ten advisors across two independent councils, anonymized peer review by all ten, one chair per council, meta-chair reconciliation, and one adversarial refuter per load-bearing edit.

## Outcome

Fourteen edits applied across `SKILL.md`, `references/checks.md`, `references/fixes.md`, and `scripts/sort_chronology.py`. All five scanners return zero findings on `lint`; 296 tests pass; the `checks.md`-versus-registry diff now shows only the deliberate `caller-determined` `zero_source_page` split.

The headline number is the refutation rate. Thirteen load-bearing edits reached the refuter gate; **eight held and twelve distinct claims were refuted** (several edits were multi-part, held in one part and refuted in another). The councils were productive but over-proposed, and roughly half of what survived peer review did not survive an adversarial read.

## Applied

### Irreversible-action fixes

1. **`scripts/sort_chronology.py` — `recover_time` scoped to the entry's own report bullet.** New `OWN_REPORT_LINE_RE` matching `^\s*- (?:Saved|Report):`; recovery scans only those lines, falling back to the whole entry when no labelled bullet exists. Fixes a real false abort: an entry carrying both its own `Saved:` link and any other same-date `2-outputs` link previously yielded two distinct times, returned `None`, raised `ValueError`, and skipped the whole file despite having a perfectly determinate self-link.
2. **`references/fixes.md` — Open-threads prune now requires every wiki-page wikilink in the entry to resolve to no file.** The condition was written singular ("its wikilink target no longer exists") while the fix removes the whole entry, so one deleted page in a three-page entry could delete live orientation prose that is not duplicated in `log.md`. A partially-dangling entry is now surfaced as `hot_log_stale` for the user or `audit`. The neighbouring "Remove hot entries pointing to missing pages" bullet was narrowed in the same edit so it cannot re-license the removal, and the test is stated over wiki-page links only so a `2-outputs/` expected dangler never counts as resolving.
3. **`SKILL.md` — the Step 3 fix list now carries the same qualifier**, since that is the line a runner actually reads; only `fixes.md` had the restriction.
4. **`references/fixes.md` — the verified-hash re-stamp re-confirms the baseline immediately before the edit**, hashing the pre-fix body and demoting on any difference. `fixes.md` itself concedes that a page wrongly re-stamped over an unmatched baseline "passes this sweep as a clean no-op", so nothing downstream catches an external edit landing between the Step 1 pin and the fix. Worded as narrowing, not closing, the window.

### Correctness of the catalogue

5. **`references/checks.md` — `verified_anchor_unaudited` and `verified_hash_mismatch` moved from `#### Info` to `#### Warning`.** Both are `warning` in the registry, and both bullets said so in their own text. The now-redundant "(Warning)" label was dropped from the second, and the "These three are real schema violations" lead-in became accurate automatically once the fourth bullet left the group.

### Stale schema attribution

6-8. **`SKILL.md`, `references/checks.md`, `references/fixes.md` — `verified_hash:` is no longer attributed solely to `audit`.** The schema now says the stamp is written by whichever run certifies the page's claims, with `ingest` normally stamping itself and `lint` re-stamping allowlisted fixes. Three sites corrected; the wording is careful not to imply lint ever stamps on a fact-check, which lint does not perform.

9. **`SKILL.md:47` — `pagination_map_unregistered` split from `locator_page_mismatch`.** The map is registered on ingest with a human confirming each line and is never grown by `audit`, so handing both to "audit or the user" was wrong for one of them.

### Contract and disclosure

10. **`SKILL.md` report template — a named status-change line** inside `## Auto-Fixed`, listing pages demoted `verified` → `draft` with the triggering `check_id` and, symmetrically, pages re-stamped. Step 3b already tracks both sets. A demotion costs a later run a full re-verification to undo and was previously invisible.
11. **`SKILL.md` log template — the same demotion set** appended to the existing `Auto-fixed:` line.
12. **`SKILL.md` — `critical_blocking:` deleted** from report frontmatter (self-described as "equals audit_blocking by construction"), and the Summary line rewritten to use `audit_blocking`. Verified no consumer outside lint's own SKILL.md.
13. **`SKILL.md` — the self-report chat mirror** the shared self-report reference requires.
14. **`references/fixes.md` — "Step 2 baseline" renamed "pinned Step 1 baseline"** at both sites; one object had two names on the guard that decides re-stamp versus demote.

## Refuted — and why this section matters

Every item here passed at least one advisor and usually peer review. None survived an adversarial read.

- **Scoping `recover_time` to `- Saved:` alone.** Only seven skills use that label; `ingest`, `forget`, `supersede`, and `synthesis` use `- Report:`. The edit as proposed would have disabled recovery for the highest-frequency write operations and made the function dead code for `hot.md`. Applied only in widened form.
- **Reassigning `locator_page_mismatch` to the user.** `audit/SKILL.md:39` names it among the locators audit settles with the raw open. The project already met this exact deadlock shape for `verified_anchor_unaudited` and concluded the code was wrong, not the prose — the severity was changed in `check_wiki.py`. Raised as a proposal instead.
- **Deleting "Warning is audit's authored-tier worklist" from the `checks.md` lead-in.** Not this file's error: `audit/SKILL.md:29` states the same definition, and the auto-fixed Warnings do not contradict the tier's routing semantics because lint clears them before audit reads the report. Deleting it would have desynced two files.
- **Gating the Recent-activity trim on the sorter's exit code, and on entry body lines.** The exit code is one flag shared across both files, so the gate would block on an unrelated file's defect; and the trim is not in the script at all — it is an agent action, so the cited body-attachment code proves nothing about it.
- **Guarding the demote against malformed frontmatter.** Dead code: `check_page` returns early on `frontmatter_missing`, well before `check_verified_hash` runs, so the demote path is never entered for such a page. The guard would also invert the safety direction, leaving `status: verified` beside an uncomputable hash.
- **Enumerating the owned-drift set literally, and dropping chronology ids on exit 1.** The clean test parses script JSON, so id-less fix bullets can never enter the set or spin the loop; and dropping `chronology_out_of_order` on a process-wide exit 1 would suppress a genuinely unsorted `hot.md`.
- **Specifying a Warning row shape, and the Step 5 UTC stamp.** Three report sections are bare, not one, and the row shape is already specified once globally at Step 4 — duplicating it per tier is the restatement the schema forbids. The bare `HH:MM` is a placeholder every sibling skill uses, not an instruction to read a local clock.
- **Deleting the false "Idempotent" claim.** The script *is* idempotent in the strict sense — it canonicalizes on one pass then stabilizes, verified across three runs — and the word is load-bearing for the non-convergence guard. Only the "rewritten byte-identically" clause was false; only that clause was changed.
- **Eleven lines exceeding the 79-character limit.** `pyproject.toml` sets `line-length = 88`; the longest line is 87. Zero violations. Two advisors reported it independently and two peer reviewers "verified" it by re-counting the same line numbers — none checked the configured limit.

## Proposals (cross-file, not applied)

1. **`check_wiki.py` — reconsider `locator_page_mismatch`'s `error` severity.** Six checks force `result: blocking`; this one names `audit` as its resolver while `audit` gates on `result: clean`. The precedent set for `verified_anchor_unaudited` was to change the severity in code.
2. **`multi-skill/scripts/tests/test_sort_chronology.py` (new).** Lint's only owned and only mutating script has no test; `recover_time` now has branch behaviour worth pinning (own `Saved`, own `Report`, indented, own-plus-foreign, foreign-only, date-mismatched).
3. **A registry-versus-catalogue assertion.** Nothing enforces the diffability rule `checks.md` asserts, which is why two misfilings survived. One test would prevent recurrence.
4. **Single-source `LOG_HEADER_RE` / `HOT_ENTRY_RE`.** Byte-identical to `check_wiki.py:4643-4644`; drift would make checker and fixer disagree silently.

## Residual, not fixed

- **`recover_time`'s foreign-only case still returns the foreign minute.** With no labelled bullet anywhere in the entry, the fallback preserves today's whole-entry scan. This is the refuter-mandated shape (removing the fallback would turn working recovery into mandatory hand-fixes), so the hazard is narrowed, not closed. Reported rather than claimed fixed.
- **The `main()` success message still says `re-sorted newest-first` for a whitespace-only pass.** The proposed two-way fix was refuted as incomplete — there are three actions, and a pure time recovery would still be mislabelled. Left for a correct three-way fix.
- **`concept_multi_idea` is catalogued but no Step 2 bullet instructs it.** An LLM-walk id absent from the registry, so deleting it breaks no diff — but it is a content deletion that reached no refuter, and one-idea judgement is `audit`'s remit anyway. Reported, not acted on.

## Self-report

- **The orchestrator propagated an unverified finding into a chair prompt.** Peer reviewer T's claim that the `checks.md:85` rationale sentence was false was rated highly and passed to Council 2's chair as settled context; the refuter later showed it restates the project's own cross-file definition. Marking something "settled" for a downstream agent is an assertion that needs the same evidence bar as a finding. → upgrade: the skill should require that anything injected into a chair prompt as SETTLED carry the same orchestrator-verified evidence line a refuter verdict does, or be labelled provisional.
- **Convergence was treated as evidence twice, and was wrong both times.** Three of five C1 peers repeated the severity worklist-loss claim; four agents across both councils reported the 79-character violations. Both fell to a single dissenter who checked a config file. → upgrade: the protocol should name shared-premise agreement as a known failure mode and require the chair to identify the *one* checkable fact a convergent cluster rests on.
- **The refutation rate suggests the advisor prompts reward proposing over verifying.** Twelve of thirteen load-bearing edits were wrong in whole or part. → upgrade: ask advisors for a disconfirming check they ran on their own strongest finding, before it reaches peer review.
