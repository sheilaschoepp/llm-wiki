---
type: skill-llm-council
date: 2026-08-06
mode: solve
result: solved-demoted
target: "consistency"
target_path: "./.claude/skills/consistency/"
snapshot_id: "fcf89e6"
baseline_commit: "fcf89e6"
dirty_paths: 0
drift: none
advisors: 6
evaluators: 10
chairs: 2
refuters: 2
applied: 0
needs_review: 1
cross_file_proposals: 2
---

# Skill LLM council: consistency (round 2)

Path: `./.claude/skills/consistency/`
Run: 2026-08-06 15:42
Mode/result: solve / `solved-demoted`
Outcome: one candidate cleared every gate the first round skipped — 10/10 HOLD across two independent evaluator panels, both chairs, and the locator refuter — then was refuted by the entailment lens on three factually false sentences in its own documentation. Nothing was written to the target skill.
Value over the skill-linter baseline: the five deterministic scanners find two pre-existing style findings on this skill and nothing about either named problem. This round's gates killed a candidate whose behaviour I independently verified as correct, on the strength of prose that contradicts the repository — the exact defect class `consistency` exists to catch, found inside a candidate written for `consistency`.
Churn vs prior run: round 1 refuted three candidates at the adversarial gate without ever running the evaluator or chair gates. Round 2 ran every gate. The surviving candidate set changed completely: all three round-1 candidates are gone, five new ones were generated, and exactly one reached refutation.

## Correction to round 1's record

Round 1 was filed as `solved-no-survivor`. That was the wrong code: its three candidates reached Step-6 refutation and were demoted there, which the report template defines as `solved-demoted` (`solved-no-survivor` is for candidates that never survive generation, eligibility, or coherence). Round 2 is filed correctly. The substantive outcome of round 1 is unchanged.

## Task brief

`consistency` checks cross-file schema and skill drift and is one of two preconditions gating `audit`. A good version detects drift the other checks cannot, never auto-edits a soft-read-only file, and never emits a fix hint an agent could follow into damage. Binding rules: `CLAUDE.md` (Stay In Your Lane, Audit preconditions, Severity vocabulary), the Anthropic skill-authoring guidance, `ai-writing-tells.md`, and `coding-best-practices.md` for the 2560-line script. Useful disagreement here is about *what a check should quantify over* — the round-1 failure was a candidate that quantified over folio values instead of registration.

Known wrong going in, from round 1: non-digit printed folios are legitimate map data; no fix hint may instruct writing `none`; the permission roster and the leakage exemption are different sets; a schema-exhibit predicate must tolerate indentation and inline-code delimiters.

Related context: councils were given bounded read-only access to `.claude/skills/consistency/`, `CLAUDE.md`, `.claude/skills/multi-skill/` (`pagination-map.md`, `body_hash.py`, `check_wiki.py`), `.claude/skills/lint/` and `.claude/skills/audit/`, and — new this round — the populated sister vault `/home/user/llm-wiki-mas/`, which carries 43 registered raws and real papers. That grant is what made this round's decisive findings possible; round 1 validated against the empty template and missed both.

## Problem manifest (frozen before launch)

- **P1** — no integrity check for the curated data files `consistency` declares single sources of truth. Ground: emptying all 43 `## 0-raw/` sections of `pagination-map.md` in a scratch copy of the populated vault produced a byte-identical 167-finding set; `lint` raises `pagination_map_unregistered` only at `info`. Success test: fires on the gutted map, silent on both intact repos.
- **P2** — no check that a schema rule and the tooling enforcing it agree. Ground: 200 markers authored into the position `body_hash.py` ignores, 0 `unverified_claim` findings, 90 `verified_hash_mismatch`, `consistency` `clean` throughout.

The manifest was deliberately narrowed to these two and the rosters cut to three per council, applying round 1's self-report item 1 (compute the budget for the whole run up front, rather than shedding gates later).

## Rosters

**Council 1 — cognitive lenses (reduced to 3):** Contrarian, First-Principles, Outsider.
**Council 2 — skill specialists (reduced to 3):** Adversarial Failure-Mode, Script & Python-Quality, Best-Practices-Compliance.

Both above the documented floor of three usable advisors plus a chair. Dropped in the fixed priority order: Expansionist, Executor, Description & Trigger, Structure & Token-Economy — their round-1 contributions (the manifest `gate:` key, the atomicity and deadlock analysis) were passed forward as frozen constraints rather than re-derived.

Best-Practices-Compliance returned no candidate by design: tasked with the registration surface, it returned the four-limb atomicity requirements and a must-not-change list (no SKILL.md packet-blurb edit, no Step 7.3 / Step 8 edit, no description change — 992 of 1024 characters).

## Frozen candidates and de-anonymization

| C_ID | P_ID | Generator | Council | Outcome |
| --- | --- | --- | --- | --- |
| C-11 | P1 | First-Principles | 1 | eligible, selected, **refuted at Step 6** |
| C-04 | P1 | Adversarial Failure-Mode | 2 | ineligible — panel 1: 2 HOLD / 3 REFUTE |
| C-07 | P1 | Contrarian | 1 | ineligible — 0/10, no function body in frozen text |
| C-02 | P2 | Script & Python-Quality | 2 | ineligible — panel 1: 0/5; panel 2: 2 HOLD / 3 REFUTE |
| C-19 | P2 | Outsider | 1 | ineligible — 0/10, no check body, plus constraint 6 |

Material distinction confirmed: the three P1 candidates differ on what the coverage referent quantifies over (source-page `file:` fields, `#page=` citations across four page types, `#page=` citations across all of `1-wiki/**`) and on which integrity conditions they carry. Not five rewordings of one design.

## Step 3 — evaluator panels

Two panels of five fresh evaluator-only agents. Both healthy (5 usable returns each; floor is 3). Eligibility floor applied exactly: ≥ 3 explicit HOLD and zero REFUTE in **each** panel.

| C_ID | Panel 1 | Panel 2 | Eligible |
| --- | --- | --- | --- |
| C-11 | 5 HOLD / 0 REFUTE | 5 HOLD / 0 REFUTE | **yes** |
| C-04 | 2 HOLD / 3 REFUTE | 5 HOLD / 0 REFUTE | no |
| C-02 | 0 HOLD / 5 REFUTE | 2 HOLD / 3 REFUTE | no |
| C-07 | 0 HOLD / 5 REFUTE | 0 HOLD / 5 REFUTE | no |
| C-19 | 0 HOLD / 5 REFUTE | 0 HOLD / 5 REFUTE | no |

Launch integrity: Council 1's five evaluator calls went out as 4 + 1 across two messages rather than one. No sibling had returned when the fifth was spawned, so no panel member could see another's output and independence held in fact — but this run cannot claim it by construction. Recorded in the self-report.

## What the councils found beyond the manifest

**The sister vault's schema was never amended.** Six evaluators independently discovered that `/home/user/llm-wiki-mas/CLAUDE.md:569` still reads "Most bullets have no suffix. Use markers sparingly:" — no position clause, no `> -` exhibit anywhere in the file. The round-1 amendment landed in the template only, on the user's explicit "template only" instruction. Verified: 1 canonical exhibit in the template, 0 in the sister vault.

**Two of five candidates were unappliable.** C-07 and C-19 each substituted prose for their own function body ("Full text is the diff hunk I ran"; "Body exactly as validated above in the integration run"). Ten evaluators were spent discovering this. A freeze-time parse gate would have caught both mechanically — validated after the fact: parsing each candidate's Python blocks rejects exactly C-07 (`expected an indented block after function definition`) and C-19 (defines no `check_*` function at all), and passes the other three.

## Orchestrator-resolved dispute

The locator and entailment refuters appeared to contradict each other on whether anything in the battery reads `pagination-map.md`. The locator refuter searched `check_consistency.py` for mentions of the filename and found only the `AGENT_DATA_FILES` exemption; the entailment refuter named five checks that read it. I settled it by instrumenting `Path.read_text` across a full battery run: **seven** checks read the file on every run (`ai_writing_tells`, `filename_references_resolve`, `old_schema_wording`, `personal_info_leakage`, `referenced_paths_exist`, `retired_feature_mentions`, `retired_skill_references`). Both refuters were right about different things — the file is never *named* by a check, and never parsed *as pagination data*, but it is read as text by seven directory sweeps. Because I settled it empirically, this was not an escalation trigger and no third refuter was spent.

## Step 6 — adversarial verification

Paired role-specialized refuters on the single eligible candidate. Every quote re-grepped against the source before being acted on.

| Edit | Locator | Entailment | Disposition |
| --- | --- | --- | --- |
| C-11 — new check `curated_data_source_coverage` | holds | **refuted** | `[needs-review]` |

**Locator: holds.** All five cited grounds verified verbatim at their anchors — the map's self-declaration as single source of truth and its human-both-margins requirement (`pagination-map.md:9,21`); `CLAUDE.md:461` on the heuristic fallback and ingest-time registration; `SKILL.md:179` on root-level classification; `references/checks.md:5` at 27 checks / styles-files 12, making the 28 / 13 arithmetic correct; and every line anchor exact. One precision it added: the function's last code line is 2378, not 2379.

**Entailment: refuted.** Three grounds, all of which I re-verified:

1. **The rationale's central claim is false.** C-11's own comment says the coverage gap is that "lint's per-citation nudge is `info`, so the obligation itself has no blocking backstop" — but every finding C-11 emits carries `file=.claude/skills/multi-skill/pagination-map.md`, which `SKILL.md:206` classifies as an ordinary root-level proposal that "does not block `clean`". Verified verbatim. So a gutted map still yields `result: clean` and `audit`'s precondition still passes. The check adds a second non-blocking notice for a condition `lint` already reports; it does not provide the backstop its own rationale names as missing.
2. **"Nothing in the battery reads it" is false** — seven checks read it every run, as traced above. My own authored `CHECK_MANIFEST` scope prose repeated the same error ("yet nothing else in the battery reads it"). The accurate claim is "nothing reads it *as pagination data*".
3. **"per-citation" is wrong** — `lint/references/checks.md:85` states "One finding per unregistered raw, reported against the raw path". Verified verbatim.

The protocol's entailment lens is explicit that "an edit whose stated rationale is false is refuted even when the change it makes is harmless." Two of three rationale claims are false of this repository, and I cannot repair them: a refuted frozen candidate is terminal, and any post-evaluation textual change invalidates survivor status.

**What was verified good about C-11, and is worth carrying to a round 3.** I reproduced its behaviour independently rather than trusting any agent: 0 findings on the template, 0 on the populated sister vault (non-vacuously — 43 registered, 40 ingested PDFs, 0 ghosts), and **40 findings on a gutted map, 0 once restored**. That is exactly the defect the audit reported. Its roman-folio immunity is structural, not promised: no regex in it can match a `- <physical> = <printed>` line, so the 33 legitimate roman entries that killed round 1's candidate are invisible to it. It parses cleanly, adds 0 `check_kwargs` findings, and collides with no existing name.

## Completed changes

Applied in-folder: **none**. No file under `.claude/skills/consistency/` was modified; `git status` for the target path is unchanged from the freeze, and the snapshot recomputed after refutation shows no drift.

Post-apply sanity check: not applicable — nothing was applied. Baselines captured for a future round: battery on the template exit 1 / 2 findings (`identity_term_leakage`, `orphan_skill_scripts`); on the sister vault exit 1 / 27 findings; 46 unit tests pass; `check_h2_case` 5 pre-existing findings on `references/checks.md`, `check_kwargs` 1 pre-existing on `acceptance_check_consistency.py`, `check_musts` / `check_structure` / `check_synonyms` clean.

## Needs-review proposals

- **[needs-review]** `.claude/skills/consistency/` — C-11 `curated_data_source_coverage`, refuted by the **entailment** lens. The mechanism is verified correct and the fix is confined to three false sentences, none of which any evaluator's verdict depended on. A round-3 candidate must: strike "Nothing in the battery reads it" in favour of "nothing reads it as pagination data"; correct "per-citation" to "per-raw"; and either drop the "no blocking backstop" rationale or make the check actually blocking, which is cross-file because `CLAUDE.md` enumerates the schema-integrity class by name. Also fold in the two non-decisive defects evaluators recorded: widen `except OSError` to `(OSError, UnicodeDecodeError)` so the "missing or unreadable" message is true, and add a unit test — no existing test requires per-check coverage, so its absence would not have been caught.

## Cross-file proposals

Not applied — these touch shared files. Act on them by hand if you agree.

- **[cross-file]** `/home/user/llm-wiki-mas/CLAUDE.md` → `## Bullet Markers` — the sister vault still carries the un-amended text that produced the 200-marker bug. Six evaluators found this independently, and it is the sole reason both P2 candidates were refuted. Applying the same two-part amendment the template received would close the P2 problem's ground and make a P2 check silent on both vaults.
- **[cross-file]** `.claude/skills/audit/SKILL.md:84` — still claims `consistency` runs "capacity, integrity, and stale-entry checks" on the four curated data files. None exist, and this round added none. Carried forward from round 1, unresolved.

## Preserved dissent

**C-04 deserved to ship and did not.** Both chairs judged Council 2 right on the merits of the primary dispute: C-04's `review(...)` fix hint restates `pagination-map.md`'s own header near-verbatim, targets only a line the map itself calls "invalid as map data", proposes no value, and says "Leave every resolved line untouched". Council 1 fired on the string `none` without checking what the source document licenses. But Council 1's *secondary* ground is a genuine error catch that survives: C-04's own `CHECK_MANIFEST` scope asserts the printed side "never appears in a fix hint", which is false of its own text — a scope line contradicting the code it describes, inside a consistency check. C-04's coverage is a real loss: a broader referent (citations across sources/concepts/entities/syntheses, versus C-11's source-page `file:` fields alone), empty-shell-section detection, unresolved `review(` detection, and the explicit `UnicodeDecodeError` handling that is precisely C-11's recorded weakness. The two were complementary, not redundant.

**P2 was killed by an orchestrator error, not by weak candidates.** Both chairs ruled the constraint mis-scoped, and I agree. See the self-report.

## Self-report

- **I authored one constraint list and applied it to two structurally different problems, and it killed the entire P2 line on a false premise.** Constraint 6 ("silent on both intact repos") is correct for P1, where both vaults hold an intact pagination map. It is wrong for P2, where the sister vault genuinely carries the un-amended schema the check exists to detect — so the constraint demanded that a schema-drift detector not detect the drift. Six evaluators refuted both P2 candidates on it, two flagged the firing as a true positive, and both chairs called it mis-scoped. → upgrade: Step 1 should bind every constraint to a specific `P_ID` and state, per problem, what "intact" means for that problem's referent; a constraint list must never be carried across problems whose success tests quantify over different objects.
- **The freeze accepted two candidates that contained no function body, and ten evaluators were spent discovering it.** Round 1's self-report already prescribed writing each candidate's implementation to its own file at freeze; I did that, but copied whatever the generator returned without checking it held a body. → upgrade: the Step-3 freeze should mechanically reject a script-edit candidate whose implementation blocks do not parse and define a function named `check_<check_id>` with a non-trivial body. Validated against this slate: the gate rejects exactly C-07 and C-19 and passes the other three.
- **The no-repair rule turned a twice-verified working check into nothing over three comment sentences.** The rule is right for mechanism changes — it stops an orchestrator laundering an unreviewed design through a reviewed `C_ID`. But C-11's refutation rests entirely on prose in a code comment and a manifest `scope` string, neither of which any evaluator's verdict depended on and neither of which affects behaviour. Two rounds and roughly thirty subagents have now produced zero applied edits. → upgrade: the protocol should distinguish a *mechanism* freeze from a *prose* freeze — allow the orchestrator to correct a factually false comment or scope string that no HOLD relied on, provided the correction is recorded verbatim in the report and the code path is byte-identical; keep the absolute bar on any change to the predicate, anchors, findings, or fix hints.
- **I authored manifest `scope` prose that repeated the candidate's own false claim.** C-11 specified limbs 1 and 3 by field values rather than bytes, so I wrote the scope string and catalogue bullet — and reproduced "nothing else in the battery reads it" without checking it. I had the means to check: the seven-reader trace took one command, and I only ran it after a refuter forced the question. → upgrade: when the orchestrator authors any prose to a candidate's specification, every factual assertion in that prose needs the same ground check a finding gets, before the refuters see it.
