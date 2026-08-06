---
type: skill-llm-council
date: 2026-08-06
mode: solve
result: solved-applied
target: "consistency"
target_path: "./.claude/skills/consistency/"
snapshot_id: "a1eef03"
baseline_commit: "a1eef03"
dirty_paths: 0
drift: none
advisors: 6
evaluators: 6
chairs: 2
refuters: 2
applied: 1
needs_review: 0
cross_file_proposals: 3
---

# Skill LLM council: consistency (round 3)

Path: `./.claude/skills/consistency/`
Run: 2026-08-06 16:57
Mode/result: solve / `solved-applied`
Outcome: one candidate cleared every gate — 6/6 HOLD across both panels, both chairs, and both refuter lenses — and was applied verbatim. `pagination_map_integrity` now fires 43 findings on a gutted pagination map that the battery previously reported as byte-identical to an intact one.
Value over the skill-linter baseline: the five deterministic scanners find two pre-existing style findings on this skill and nothing about the named problem. The councils found a defect neither the audit nor two prior rounds had identified — that a map section keeping its heading while losing its entry lines is invisible to *both* consistency and lint, because the same empty dict silences lint's membership-test nudge and makes every page read `unregistered`.
Churn vs prior run: round 2 applied nothing (`solved-demoted`). Round 3's slate is entirely new; one candidate applied, five refuted.

## What was applied

**`pagination_map_integrity`**, packet `styles-files`, five limbs, all in-folder:

- `scripts/check_consistency.py` — `CHECK_MANIFEST` entry (after line 349), constants + `_scan_pagination_map_sections` + `check_pagination_map_integrity` (after line 2378), `CHECK_FUNCTIONS` entry (after line 2408).
- `references/checks.md` — line 5 now reads 28 checks / styles-files (13); new catalogue bullet after line 33.
- `scripts/tests/test_check_consistency.py` — module-level `_write_pagination_map` fixture plus six test methods.

Applied verbatim from the frozen candidate. No wording was changed, and the two defects the councils recorded (below) were shipped as-is rather than repaired, per the no-repair rule.

## The defect it closes

`check_wiki.py`'s `_load_pagination_map` registers a raw from its heading alone (`out.setdefault(raw, {})` at line 822). So a `## 0-raw/…` section whose `- ` entry lines are deleted enters `PAGINATION_MAP` with an empty page map, and two independent safety nets both fall through it:

- `pagination_map_unregistered` is guarded by `if raw_path in PAGINATION_MAP` (line 4159). An empty dict **is** a member, so the nudge never fires.
- `printed_page` returns `('unregistered', None)` when `phys not in pages` (lines 858-862), so `locator_page_mismatch` skips every page.

Measured on the populated vault: this state produces **0** findings from lint and **0** from consistency. Whole-section deletion, by contrast, produces 40 lint findings at `info`. The mode the check now covers is the one nothing anywhere reported.

## Problem manifest and rosters

**P1** — no check reads the curated `pagination-map.md` as pagination data. Verified: the full battery on a faithful copy of the populated vault returns **27 findings intact and 27 gutted, byte-identical**.

**Council 1 (cognitive lenses):** Contrarian, First-Principles, Outsider.
**Council 2 (skill specialists):** Adversarial Failure-Mode, Script & Python-Quality, Best-Practices-Compliance.

Evaluator panels ran at the documented health floor of three per panel (reduced from five at the user's direction to halve the remaining spend). At three evaluators, eligibility requires unanimity in both panels — a stricter bar, not a looser one.

## Frozen slate and evaluator verdicts

| C_ID | Generator | P1 | P2 | Eligible |
| --- | --- | --- | --- | --- |
| D-21 | Script & Python-Quality | 3 HOLD / 0 REFUTE | 3 HOLD / 0 REFUTE | **yes** |
| D-12 | Contrarian | 1 / 2 | 2 / 1 | no |
| D-03 | Adversarial | 0 / 3 | 0 / 3 | no |
| D-05 | First-Principles | 0 / 3 | 0 / 3 | no |
| D-08 | Best-Practices | 0 / 3 | 0 / 3 | no |
| D-17 | Outsider | 0 / 3 | 0 / 3 | no |

Measured behaviour, reproduced independently by multiple evaluators. Mode A = headings kept, entry lines stripped. Mode B = sections deleted outright.

| C_ID | intact tpl/mas | mode A | mode B | missing / undecodable / blank |
| --- | --- | --- | --- | --- |
| D-03 | 0 / 0 | 43 | 40 | 1 / 1 / 1 |
| D-05 | 0 / 0 | 43 | 40 | 1 / 1 / 0 on template |
| D-08 | 0 / 0 | **0** | 40 | 1 / 1 / 1 |
| D-12 | 0 / 0 | 43 | 1 | 1 / 1 / **0 on template** |
| D-17 | 0 / 0 | 43 | **0** | 1 / 1 / **0 on both** |
| D-21 | 0 / 0 | 43 | 0 | 1 / 1 / 1 |

**Why the others fell.** D-03, D-05 and D-17 each shipped a fixed "Seven checks in this battery read this file" claim — false of the populated vault, where eight do. D-05, D-12 and D-17 each return silently on a zero-byte or whitespace-only map. D-08 is silent on mode A, covering only the mode lint already reports. D-12 additionally fails a prose-masking probe: an evaluator rebuilt mode A with one line reading `Body offset = -29.` under each heading and D-12 fell from 43 findings to 0, because its entry test is `str.count('=')`.

## Adversarial verification

| Edit | Locator | Entailment | Disposition |
| --- | --- | --- | --- |
| D-21 — new check `pagination_map_integrity` | **holds** | **holds** | applied |

**Locator: holds.** All seven cited grounds verified verbatim at the named file and line, and it independently tallied the live manifest to confirm the 27→28 / 12→13 arithmetic. All five anchors exact.

**Entailment: holds.** It verified every assertion in the shipped artifacts — manifest `scope`, block comment, docstring, catalogue bullet — against both vaults, confirmed no round-1 repeat (nothing reads right of the `- ` prefix; the only integer emitted is a heading count) and no round-2 repeat (the vault-dependent reader count is deliberately written "several", true at 7 and 8). It measured the silence claim itself: 43 sections on the populated vault, zero duplicates, zero without an entry line.

## Post-apply validation

| Gate | Result |
| --- | --- |
| `--list-checks` | 28 checks; styles-files 13, schema-language 7, wiki-pages 5, ai-writing-tells 1, naming 2 |
| `_assert_manifest_consistency()` | `[]` — no wiring problems |
| Unit suite | **52 tests, OK** (46 pre-existing + 6 new) |
| `catalogue_matches_manifest` | `[]` |
| Battery, template | 2 findings — identical to baseline; new check 0 |
| Battery, research vault (its own script) | 27 findings — identical to baseline; new check 0 |
| New check vs gutted map | **43 findings**, all filed under `.claude/skills/`, no folio token in any message or hint |
| `check_h2_case` / `check_kwargs` | 5 / 1 — exact pre-existing baselines |
| `check_musts` / `check_structure` / `check_synonyms` | 0 / 0 / 0 |

Drift check immediately before application: target path clean, HEAD `a1eef03`, all five anchors exact.

## Recorded defects, shipped as-is

Both were ruled non-blocking by the chairs and confirmed by the entailment refuter. Neither could be repaired without invalidating survivor status.

1. A clause in the candidate's TRADEOFF prose argues that catching mode B would force findings onto wiki pages. That is **false** — D-12 filed such findings against the map itself, three times over. The clause sits in rationale prose, not in any applied artifact, and it under-claims rather than over-claims.
2. The check is silent on mode B (whole-section deletion). Disclosed in the shipped wording itself, and covered by lint at `info`.

## Cross-file proposals

Not applied — these touch files outside the target skill.

- **[cross-file]** `.claude/skills/multi-skill/scripts/check_wiki.py:813` — `_load_pagination_map` catches only `OSError`, and line 846 runs it at import. A non-UTF-8 pagination map therefore raises `UnicodeDecodeError` and **crashes lint before any check runs**, while the function's own docstring at line 808 reads "Never crashes lint." Reproduced directly: a valid map imports fine, an undecodable one aborts at import. Found by a council reviewing a different skill.
- **[cross-file]** `.claude/skills/audit/SKILL.md:84` — still claims consistency runs "capacity, integrity, and stale-entry checks" on the four curated data files. This round adds an integrity check for one of them; the sentence remains broader than what exists. Carried from rounds 1 and 2, still unresolved.
- **[cross-file]** `check_consistency.py:1250-1254` — `AGENT_DATA_FILES` names three of the four curated data files declared in `CLAUDE.md` → Stay In Your Lane; `synonym-ignore.md` is absent, against the constant's own instruction to keep in step. Round 2 established that adding it would be wrong (that constant is a content-based leakage exemption, not a permission roster), so the correct fix is to the comment or the schema wording, not the set.

## Preserved dissent

**D-21 leaves mode B to lint at `info`, "a severity nobody reads."** Council 1's chair recorded this as legitimate and unresolved, but a lint-severity question rather than a reason to reject.

**D-03 had the strongest code on the slate and did not ship.** Two evaluators and one chair said so independently: it covers both destruction modes, passes a fifteen-fixture false-positive gauntlet at zero, and fails loud on every absence shape. It was refuted for documentation — partly for a figure this orchestrator supplied wrong. It carried a second, independent falsehood (asserting the loader degrades silently on an unreadable file, when it crashes), so it would have failed constraint 7 regardless; but the slate was measurably distorted by orchestrator error, and Council 1's chair judged that a clean re-run of D-03 minus its two false assertions could plausibly have won.

## Self-report

- **The brief carried two false figures into six generators, and three candidates died holding one of them.** I wrote "Seven checks read the map" (true of the template, false of the populated vault, where eight do) and "167 findings" (not reproducible; the real figure is 27, confirmed by three evaluators independently). Both came from round 1's report, which nothing fact-checks before it becomes the next round's ground truth. → upgrade: every factual claim in a Step-1 brief must be measured at the current snapshot and stated per-vault or omitted, and a figure inherited from a prior report must be re-measured before it is reused, not copied.
- **The council caught my errors better than my process did.** Three generators measured 27 and flagged the discrepancy rather than adopting my number; two refused to ship a reader count at all and said why. The mechanism that saved this round was six agents independently distrusting the brief — which is luck, not design, since three others trusted it and were refuted for it. → upgrade: the brief should mark each factual claim as measured-this-run or inherited-unverified, so a generator knows which numbers to re-derive.
- **My extraction corrupted two candidates and nearly shipped a broken file.** Decoding subagent output with `unicode_escape` double-encoded 75 em dashes into mojibake, and a fence-splitting regex truncated the test block mid-string at 2721 of 4814 characters — which I applied, hit a `SyntaxError`, and had to revert. The entailment refuter caught the mojibake; only the parser caught the truncation. → upgrade: candidate text must be extracted by parsing the transcript as JSON, never by unescaping, and code blocks must be split on column-anchored fences, since a candidate's own test fixtures legitimately contain nested fences.
- **The reduced roster made eligibility stricter, not cheaper in risk.** Cutting to three evaluators per panel means unanimity is required, so one dissenter vetoes. It happened to cost nothing here (6/6), but the run was one contrary verdict away from a third consecutive no-survivor outcome on a candidate that then passed both refuters and full validation. → upgrade: the skill should state that panel size and eligibility interact — a smaller panel raises the bar — so a roster cut is a deliberate trade rather than a silent one.
