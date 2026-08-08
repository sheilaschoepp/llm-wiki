---
type: skill-llm-council
date: 2026-08-08
mode: solve
result: solved-demoted
target: "audit"
target_path: "./.claude/skills/audit/"
snapshot_id: "audit-council-2026-08-08-0221"
baseline_commit: "5c16b4a754e27ae501adce4940dff56029c05fbe"
dirty_paths: 0
drift: none
applied: 0
cross_file_proposals: 0
---

# Skill LLM council: audit

Path: `./.claude/skills/audit/`
Run: 2026-08-08 03:17
Mode/result: solve / solved-demoted
Outcome: five problems frozen, ten implementation-complete candidates generated, two cleared the eligibility floor, one selected by both chairs and the meta-chair, and it was demoted by the entailment refuter. Nothing applied. One candidate held at `[needs-review]`; eight floor-ineligible; one eligible-but-rejected.
Value over the skill-linter baseline: the deterministic scripts report exactly one finding on this skill (`body_over_length`). This run established, against shipped validator code rather than prose, that audit's documented Step 8 ordering is **unvalidatable** — `validate_verification_ledger.py:3827-3831` requires a `status_write`'s pre/post hashes to equal `page_generation` *and* `semantic_page_digest(page)` recomputed from disk, while `:3749` forbids a second page-reader generation per page. It also corrected the frozen manifest in four places and proved that P4's real scope is every post-reader writing step, not the locator pass alone. None of that is reachable by a checklist pass.
Churn vs prior run: the prior council applied five fixes. This one applied none — every candidate failed on the same axis the prior run failed on (site completeness), at a higher site count than the manifest recorded.

## Task brief

`audit` is the wiki's judgement pass: it fact-checks pages against raw sources, autonomously applies raw-grounded fixes, and is the only skill that writes `status: verified` + `verified_hash:`. A good version keeps every gate/epoch/ordering rule stated consistently at every site that states it; never lets a `verified_hash` cover bytes no page reader saw; never blocks one page's certification on unrelated work; never lets the coordinator certify its own judgement; and fits the 6500-word body budget without deleting a rule. Binding: `CLAUDE.md` (Page Status, Bullet Markers, Source Support And Verification, Stay In Your Lane, Skill Authoring), `multi-skill/references/verification-ledger.md` and `verification-neutral-fixes.md`, Anthropic skill-authoring guidance, `ai-writing-tells.md`, `coding-best-practices.md`. Already known wrong and deliberately not regenerated: six unresolvable validator paths, the `source-reviewed`/`repair-ready` vocabulary, the literal marker census, the mass-mismatch discriminator, and the Limits widening that forbids audit revising any skill or script.

Related context: councils were given a bounded read-only grant (Read/Glob/Grep plus read-only bash; no Edit/Write) over `.claude/skills/audit/**`, `CLAUDE.md`, `.claude/skills/multi-skill/references/**`, `.claude/skills/multi-skill/scripts/**`, `a-archive/reference/skill-authoring-best-practices.md`, `a-archive/style/ai-writing-tells.md`, `a-archive/style/coding-best-practices.md`, and — for the Expansionist and Description reviewers — sibling `lint/`, `consistency/`, `ingest/`, `checkup/`. `0-raw/` and prior `2-outputs/skill-llm-council/` reports were excluded. Inlining was impractical: the target alone is ~25 000 words.

**Provenance corrections made during the run.** Four manifest facts were re-measured and found wrong:

| manifest claim | measured this run |
|---|---|
| "Step 8 alone verifies final bodies" at SKILL.md:120 | SKILL.md:**114** |
| P3 stated at 3 sites | **8** sites (adds SKILL.md:55, frontmatter `description:`, `apply-fixes.md:75`, `verify-and-set-status.md:17`, `report-template.md:73`) |
| next cut ≈175 words | **145** words — and the deficit is **279**, so that cut cannot clear the budget (lands at 6634) |
| 19 sentence pairs ≥ Jaccard 0.55 | **13** by an independent splitter (reported as the measurer's own figure) |

`pytest` is absent from this container, so the "94 contract tests pass" figure stays `[inherited; unverified this run]`; the Script reviewer read the contract tests instead of running them.

## Council 1 — cognitive lenses

### Step 2 responses
Independence: the five Step-2 calls were issued in parallel in a single message, as were Council 2's; the two councils' batches went out together. No call was sequential.
Ground check: none dropped. Every candidate carried a `quote`-form ground that verified.
Ungroundable: none.

Roster and contribution: **Contrarian** (found the fifth P4 site `reader-artifacts.md:35` that the manifest missed, and the general invariant that the three pre-stamp checks and the non-HOLD repair loop each reproduce P4 through a different door — later vindicated by every panel); **First-Principles** (established that `verification-ledger.md:60` makes a per-page *epoch* unexecutable, so P1 must localize *sealing* over a global epoch); **Expansionist** (measured the P6 cut sets and confirmed 145 words is insufficient); **Outsider** (inverted the manifest's P4→P6 dependency by cutting Step 5's reader mechanics instead of the Step 8 bullets, and observed that a locator relocation rewrites the claim line so it invalidates *bullet* rows too); **Executor** (found `apply-fixes.md:79`-adjacent per-page phrasing and the unnamed P1 sites at SKILL.md:30/:104/:123, `verify-and-set-status.md:5`, `reader-artifacts.md:13`).

### Anonymization
A–E → Expansionist, Executor, Contrarian, Outsider, First-Principles (randomized; mapping withheld from evaluators, disclosed here).

### Step 3 fresh reviews
Five fresh evaluator-only calls, one message. Verdicts (E1–E5 in call order):

| C_ID | E1 | E2 | E3 | E4 | E5 | HOLD/REFUTE |
|---|---|---|---|---|---|---|
| C-P4-1 | HOLD | HOLD | REFUTE | HOLD | REFUTE | 3/2 |
| C-P4-2 | REFUTE | REFUTE | REFUTE | REFUTE | HOLD | 1/4 |
| C-P1-1 | REFUTE | REFUTE | REFUTE | REFUTE | REFUTE | 0/5 |
| C-P1-2 | REFUTE | REFUTE | REFUTE | REFUTE | REFUTE | 0/5 |
| C-P3-1 | REFUTE | REFUTE | REFUTE | REFUTE | REFUTE | 0/5 |
| C-P3-2 | REFUTE | REFUTE | REFUTE | REFUTE | REFUTE | 0/5 |
| C-P2-1 | HOLD | HOLD | REFUTE | HOLD | HOLD | 4/1 |
| C-P2-2 | REFUTE | HOLD | REFUTE | REFUTE | REFUTE | 1/4 |
| C-P6-1 | HOLD | HOLD | HOLD | HOLD | HOLD | 5/0 |
| C-P6-2 | HOLD | HOLD | HOLD | HOLD | HOLD | 5/0 |

### Step 4 chair synthesis
Selected C-P6-1. Rejected C-P6-2 as eligible-but-rejected (rule deletion). Confirmed all eight other candidates floor-ineligible. Surfaced that `SKILL.md:128` is a P4 census site absent from the orchestrator's own frozen census.

## Council 2 — skill specialists

Composed roster, with the selection reason for each: **Description & Trigger**, **Structure & Token-Economy**, **Best-Practices-Compliance** — the three core specialists, which bind every skill. **Adversarial Failure-Mode** — mandatory: audit acts autonomously and destructively (overwrites page content, removes bullets, stamps `verified`). **Script & Python-Quality** — the skill bundles `scripts/` (six modules, ~213 KB). Dropped for the two-slot limit, in the fixed priority order: Schema-Compliance, Source-Fidelity, Prompt-Engineering, Instruction-Clarity.

Contribution: **Description & Trigger** found the two P3 sites nobody else did (the frontmatter `description:` and `report-template.md:73`'s hard-coded "→ final 0"). **Structure & Token-Economy** simulated the cut sets with `check_body_length`'s exact algorithm and proved the manifest's cut lands at 6634. **Best-Practices-Compliance** grounded P4's *direction* in `CLAUDE.md:532` rather than audit's internal contradiction. **Adversarial** grounded it further in `CLAUDE.md:558` and self-flagged its own P1 candidate's weakest point. **Script & Python-Quality** produced the run's decisive evidence and correctly returned **no candidate** for a defect whose only fix is a script edit.

### Step 2 responses
Independence: five parallel calls, one message. Ground check: none dropped. Ungroundable: none.

### Anonymization
A–E → Script & Python-Quality, Adversarial, Description & Trigger, Best-Practices-Compliance, Structure & Token-Economy (randomized; disclosed here).

### Step 3 fresh reviews
| C_ID | E1 | E2 | E3 | E4 | E5 | HOLD/REFUTE |
|---|---|---|---|---|---|---|
| C-P4-1 | REFUTE | REFUTE | HOLD | REFUTE | REFUTE | 1/4 |
| C-P4-2 | REFUTE | REFUTE | REFUTE | HOLD | REFUTE | 1/4 |
| C-P1-1 | REFUTE ×5 | | | | | 0/5 |
| C-P1-2 | REFUTE ×5 | | | | | 0/5 |
| C-P3-1 | REFUTE ×5 | | | | | 0/5 |
| C-P3-2 | REFUTE ×5 | | | | | 0/5 |
| C-P2-1 | HOLD | HOLD | HOLD | HOLD | HOLD | 5/0 |
| C-P2-2 | REFUTE ×5 | | | | | 0/5 |
| C-P6-1 | HOLD ×5 | | | | | 5/0 |
| C-P6-2 | HOLD ×5 | | | | | 5/0 |

### Step 4 chair synthesis
Selected C-P6-1; rejected C-P6-2 on the same rule-deletion ground, independently verified. Explicitly recorded an **error catch against its own panel**: the unanimous 5/0 HOLD on C-P2-1 was an omission, because none of its five evaluators checked `SKILL.md:92` and Panel 1 did — "evidence beats our vote count."

## Step 5 — meta-chair reconciliation

Both chairs selected C-P6-1 and rejected C-P6-2; no conflict to resolve. I concurred on the merits, not the agreement: both cleared the floor identically (5/0 in both panels), so the tie breaks on P6's own constraint — a cut may relocate a rule but never delete one. I verified by grep that `symlink` occurs **only** at `SKILL.md:133`, the line C-P6-2's cut 7 rewrites, and that neither claimed home states it; the rule would survive solely as script behaviour at `validate_audit_completion.py:1636`/`:1655`. C-P6-1 deletes nothing. Its larger word margin was not the deciding factor and became moot once every other candidate failed.

Cross-council agreement was treated as shared evidence, not corroboration: the two panels converged on 9 of 10 dispositions, which is a same-model convergence signal recorded to memory rather than counted as confirmation.

## Solve ending

### Problem manifest and frozen candidates

**P5 was not frozen.** The manifest supplied it with no verified ground and no executable success test ("Unmeasured here; treat as a motivating symptom, never as ground"), and Step 1 requires both. Recorded as deferred, dependent on P1 and P3.

| P_ID | candidates | material distinction | disposition |
|---|---|---|---|
| P1 | C-P1-1, C-P1-2 | 3-clause ledger-decidable seal vs. body-precondition-only + stamp revocation | no survivor (0/5, 0/5) |
| P2 | C-P2-1, C-P2-2 | raw read as dispatch precondition vs. reallocating precedence between two adjacent rules | no survivor (4/1 Panel 1) |
| P3 | C-P3-1, C-P3-2 | page-attributed `blocked_targets` closure vs. `U(n)`/`CLEAR(p,n)` one-hop non-transitive | no survivor (0/5, 0/5) |
| P4 | C-P4-1, C-P4-2 | move the pass before both reader kinds vs. strip its write authority in place | no survivor (3/2, 1/4) |
| P6 | C-P6-1, C-P6-2 | cut Step 5 reader mechanics vs. collapse seven blocks across Steps 5/8/9 | C-P6-1 demoted at the refuter gate; C-P6-2 rejected on merits |

Evaluator panel quorum: 5 usable returns in each panel, both healthy. Every one of the slate's ~60 anchors matched verbatim exactly once at this snapshot — **no candidate failed on applicability**. Every refutation was site completeness or an invariant defect.

### Adversarial verification (load-bearing edits)

C-P6-1 took both lenses.

**Locator refuter — HOLDS.** Independently reproduced 6779 → **6432** words with `check_structure.py`'s own formula; confirmed all eight anchors at count 1; quoted a surviving home for each of the eight cut rules, several at greater detail than SKILL.md carried. One mislabelled home (the literal identifiers `locator_page`/`entailment_argument_page` are at `verification-ledger.md:106-107` and `report-template.md:153-154`, not the cited `verification-spec.md:13`) — rule survives, so relocation not deletion.

**Entailment refuter — REFUTED.** Three findings, all re-grepped by the orchestrator before acting:

1. **Cut 1 issues a wrong instruction.** Its replacement says "Follow `references/reader-artifacts.md` Phase A end to end" from Step 5, but Phase A's first item is item **0** — the Step-1-only exclusive `journal-init` (`reader-artifacts.md:12`), already performed at `SKILL.md:78`, which `manage_reader_batches.py:1113` refuses with "reader artifact run already has state; refusing reinitialization". Under audit's own Limits (`:158`) a non-zero helper is an evidence-collection failure, so the literal instruction is a fail-closed dead end at the top of Step 5. *Verified.*
2. **Cut 2 orphans a definite description.** Its anchor ends immediately before "The collector is a structural gate, not semantic adjudication", and after the cut SKILL.md mentions no collector, sidecar, receipt, `collect`, or `journal-append` anywhere (measured: exactly one occurrence in the body, inside the cut span). *Verified.*
3. **Cut 7 orphans a precondition.** Its anchor ends immediately before "If either original role HOLDs or CANNOT_CONFIRM", removing the both-REFUTE precondition from the body — and `Limits:156` does **not** state it, so the gate needs two hops to reconstruct. *Verified.*

On the safety question the refuter cleared the candidate explicitly: all three most safety-bearing rules keep an inline trace, so this is **not** a weakening — the refutation rests on a false instruction and two dangling referents.

Either lens refuting demotes the whole candidate. The refuter noted cut 1 contributes only −14 words and the other seven clear the budget at 6446, but severing a cut from a frozen candidate is precisely what Step 6 forbids, so **C-P6-1 is terminal for this run**.

Target-drift recheck immediately after refutation: `git status --porcelain -- .claude/skills/audit` empty, HEAD still `5c16b4a`. No drift; nothing to apply.

## Completed changes

None. `applied: 0`.

Post-apply sanity check: not applicable — no edit was written. For the record the baseline scanners are unchanged: `check_structure.py` → one finding (`body_over_length`, 6779/6500); `check_synonyms.py`, `check_musts.py`, `check_h2_case.py` → clean; `check_kwargs.py` → clean. `pytest` is not installed in this container, so `test_audit_contract.py` and `test_manage_reader_batches.py` could not be run — recorded as blocking for anyone applying a future candidate, since `SKILL.md:146` requires them before accepting a procedure change.

## Needs-review proposals

Not applied — demoted by a gate.

- **[needs-review] C-P6-1** — `.claude/skills/audit/SKILL.md`, eight replacements clearing the word budget to a measured 6432. Demoted by the **entailment** lens on three verified defects (wrong Phase-A instruction; two orphaned referents). The mechanism is sound and the arithmetic is honest; it needs re-freezing as a new candidate with cut 1's "end to end" replaced by a scoped pointer and cuts 2/7 extended to carry their orphaned referents. Full frozen text: `frozen-ledger.md` § C-P6-1.
- **[rejected-on-merits] C-P6-2** — eligible (5/0 in both panels) but rejected by both chairs and the meta-chair: cut 7 deletes the only prose statement of "symlinked … fails completion", failing its own success test.

Recorded as findings, not candidates — no generator proposed them, so none is applicable this run:

- **Tooling/prose drift in audit's concurrency limit.** `manage_reader_batches.py:29` sets `HARD_MAX_CONCURRENT_CALLS = 8`, and `validate_plan` rejects only values above 8, while `SKILL.md:100` and `reader-artifacts.md:14` both call four a "hard maximum". A plan built with 5–8 concurrent calls validates and passes completion. The Script reviewer correctly returned no candidate, because the only correct fixes are a script edit (forbidden) or weakening the prose. The sanctioned outlet is one `audit-memory.md` entry naming the tool, the exact invocation, the observed acceptance, and the candidate fix `HARD_MAX_CONCURRENT_CALLS = 4` — for the user or a later audit run to write, not this council.
- **P4's real scope is wider than the manifest states.** `SKILL.md:128` and `verify-and-set-status.md:42` both place the page readers *before* the three pre-stamp checks, and `verify-and-set-status.md:28` makes those checks writing steps ("Fix a structural finding"); `:23`'s "On a surviving non-HOLD, repair and rerun" is a third door. The locator pass is one of at least three post-reader write paths, so any future P4 candidate must close all of them or it will fail exactly as these two did.
- **Both P3 mechanisms share an executability defect neither generator saw.** Both gate "any Step 8 reader" — not just the stamp — on target-freedom, which strands an in-scope page with no page-reader rows; `validate_verification_ledger.py:3606` and `:3589-3594` reject that unconditionally because `mandatory_partial_wiki_pages` includes every non-`verified` page. A merely site-complete P3 candidate of this shape would still die at Step 9. **A future P3 must withhold the stamp only, never the readers.**

## Cross-file proposals

None. Every frozen candidate was in-folder.

## Preserved dissent

- **C-P2-1 deserves to re-enter first.** Nine of ten evaluators held it; Panel 2 held it unanimously. Its single refutation cites unedited `SKILL.md:92` ("The Step 4a edit lane itself performs no raw read, verification reader, marker write, or demotion"). The majority read "**edit** lane" as writes only, and `unlinked-mention-occurrences.md:3` makes the no-raw property conditional ("only when wrapping the occurrence cannot create or change a graph assertion") — precisely the condition the graph-ignore lane fails, and `:31` routes graph-sensitive occurrences into Step 4b. Both readings are defensible; the floor is per-panel and mechanical, so it is ineligible regardless. Both chairs recorded that its mechanism is textually sound and its sole live collision is repairable by one clause at `:92` carving the graph-ignore read out of the 4a denial. Its measured cost is +54 words, not the claimed 48.
- **A minority held that C-P6-1's dangling antecedent is worse than C-P6-2's rule deletion**, on the grounds that a newly *introduced* coherence defect is worse than losing a rule a script still enforces. Council 2's chair weighed a dangling antecedent below a vanished rule; I agree, but the argument is real and the entailment refuter effectively vindicated its concern about C-P6-1.
- **One evaluator held C-P4-1 and one held C-P4-2**, each against four refutations in its own panel. Both minorities rested on the literal success-test clause passing; both were overridden because the candidate introduced a fresh contradiction of the same class P4 names.

## Notes

- Both councils ran at full strength: five advisors and five evaluators each, plus a chair. No subagent failed or was re-run.
- The user directed shortlisting to one candidate per problem to reserve refuter budget. I narrowed to **two** per problem instead — the protocol's floor — and said so at the time, because a single candidate per problem is unopposed at evaluation and forfeits the gate the run exists for. Evaluator cost is flat in candidate count, so the narrowing saved orchestrator context, not calls. The frozen ledger was written to disk and read by the panels rather than inlined, which is what preserved budget for the refuters.
- Cross-council convergence on 9 of 10 dispositions is recorded as a revisit signal in memory, per `roles.md`.
- This is a skill-facing operation: no `1-wiki/log.md` entry.

## Self-report

- **My frozen census was undercounted, and the undercount propagated into every candidate.** I froze P3 at 3 sites; the true count is 8. I froze P4's blockers at four; `SKILL.md:128` is a site I never listed, and it is the sentence that sank C-P4-1 in both panels. Because the Step-1 brief is appended to all ten generator prompts, my incomplete census became the premise of ten candidates' site enumerations and contributed directly to eight refutations. Upgrade: Step 1 should require the orchestrator to derive each problem's census by grepping the rule's distinctive phrase **and its paraphrases** (here, "any unresolved required target" was missed by a grep for "zero unresolved required target"), and to state the census as a floor — "at least N sites, enumerate more" — rather than a list generators may treat as complete.
- **Two candidates per problem failed complementarily, and the protocol has no disposition for that.** C-P1-1 missed only `SKILL.md:104` while C-P1-2 missed five different sites; C-P3-1 missed only `:96`'s clause while C-P3-2 left `:55` and `report-template.md:73`. Each covered what the other missed, and merging is forbidden — correctly, but the result is `solved-no-survivor` on a problem where the union of two frozen candidates would have been complete. Upgrade: when candidates for one `P_ID` fail complementarily, the run should record a distinct outcome ("re-freeze with expanded census") rather than reporting no survivor, so the next run starts from the union rather than regenerating from the same brief.
- **I relayed an arithmetic figure I had not measured myself.** I passed an evaluator's 6431 into both chair prompts; a chair corrected it to 6432, and the locator refuter confirmed 6432. Immaterial to the outcome, but I put an unverified number into a decision prompt. Upgrade: the orchestrator should recompute any arithmetic it states in a chair or refuter prompt rather than relaying a subagent's figure.
- **The container could not run the target's contract tests.** `pytest` is absent, and `SKILL.md:146` makes walking `contract-scenarios.md` plus both test files a precondition of accepting a procedure change. Every candidate's contract claim is therefore unexecuted, which is a real gap in this run's verification and would have blocked application even had a candidate survived. Upgrade: Step 1's snapshot should record test-runner availability and mark any candidate whose success test depends on the suite as unverifiable-in-environment before the councils spend on it.
