---
type: skill-llm-council
date: 2026-08-06
mode: solve
result: solved-proposals
target: "skill-llm-council"
target_path: "./.claude/skills/skill-llm-council/"
self_target: true
snapshot_id: "a977dbb"
baseline_commit: "a977dbb"
dirty_paths: 0
drift: none
advisors: 10
evaluators: 10
chairs: 2
refuters: 0
applied: 0
proposals: 3
needs_review: 0
cross_file_proposals: 0
---

# Skill LLM council: skill-llm-council (self-run)

Path: `./.claude/skills/skill-llm-council/`
Run: 2026-08-06 18:09
Mode/result: solve / `solved-proposals`
Outcome: 30 candidates across four named problems. Six cleared the eligibility floor unanimously (10/10 HOLD, zero REFUTE, both panels). Coherence conflicts reduced six to three. All three are proposal-only under the Step-6 self-target protection, so nothing was written. **Zero candidates survived on the cost problem the run was convened for.**
Value over the skill-linter baseline: the five deterministic scanners find one `terminology_candidate` suggestion on this skill and nothing about any of the four problems. The councils found that the skill's own cited design reference recommends the cheap tier it never built, that the skill has 39 hard-coded roster counts no cost mechanism on the slate covered, and that the eligibility floor tightens rather than loosens as a panel shrinks — a property stated nowhere.

## The four problems

Every fact in the Step-1 brief was measured at snapshot `a977dbb` and marked measured or orchestrator-attested. That discipline is itself the subject of P2, and it was applied because the prior run's brief carried a false inherited figure into six generators.

- **P1** — cost is fixed regardless of problem size. Ground: `protocol.md:17` forbids "a smaller roster"; the literal string `budget` is absent from all six files.
- **P2** — the Step-1 brief is unverified and reaches every generator identically. Ground: `roles.md:29`; `re-measure` and `fact-check` absent.
- **P3** — a self-run on a cost or quorum problem can apply nothing, and is not told so before the spend. Ground: `SKILL.md:161`.
- **P4** — panel size silently changes the eligibility bar. Ground: `protocol.md:21`; `panel size`, `roster size`, `stricter` all absent.

## Rosters

**Council 1 (cognitive lenses, fixed):** Contrarian, First-Principles, Expansionist, Outsider, Executor.
**Council 2 (specialists, composed):** Description & Trigger, Structure & Token-Economy, Best-Practices-Compliance (the three core), plus Adversarial Failure-Mode (mandatory — this skill auto-applies edits) and Prompt-Engineering (its body is largely a prompt and it spawns subagents). Instruction-Clarity was dropped for the slot limit under the over-subscribed priority order.

Both evaluator panels ran at full strength, five each. The protocol forbids a smaller roster, and a proposal to spend less would carry little weight coming from a council deliberately under-spent to produce it.

## What survived

| C_ID | Problem | Mechanism | Disposition |
| --- | --- | --- | --- |
| C-10 | P2 | Sixth brief field; per-fact inline `[measured: {how, this run}]` / `[inherited: {producer}; unverified this run]` tags; an inherited fact may not stand as the sole ground of a candidate or manifest entry | **proposal** |
| C-17 | P3 | Step-1 precheck classifying each frozen `P_ID` against the class Step 6 defines; states the subagent count and that the run will apply nothing; confirmation scoped to spend, never apply | **proposal** |
| C-26 | P4 | One append at the floor's canonical site stating that shrinking a panel raises the bar **and** lowers detection — "stricter and blinder at once" | **proposal** |

Nothing was applied. See Scope, below.

## Coherence — three forced choices

Six eligible candidates formed three conflicting pairs. Each pair is two answers to one problem, and each pair collides.

- **C-10 vs C-14** — both edit `SKILL.md:97`, contradictorily (six fields vs five). **Chairs split.** Chair 1 took C-10 for its teeth clause; Chair 2 took C-14 for not changing a count, "the exact pattern this run was burned on".
- **C-17 vs C-23** — same mechanism, different anchors. Both chairs took C-17. C-23's text instructs reading "the frozen manifest" from an anchor 26 lines *before* the manifest is frozen.
- **C-26 vs C-28** — both append to the same sentence. Both chairs took C-26, on C-28's own admission that its sentence is "true of the ELIGIBILITY BAR and silently false of DETECTION".

**Meta-chair resolution of the split.** C-10. Chair 2's objection is that changing "five fields" to "six" repeats the pattern that killed the tiering candidates. It does not: those left 39 occurrences standing, and `five fields` occurs exactly once in the entire skill — the line C-10 itself rewrites — so it orphans nothing. Both chairs verified this independently. Chair 2's second objection, that C-10's sole-ground clause restates `SKILL.md:112`, does not hold either: `:112` governs an advisor's ungroundable ground, C-10's governs an inherited brief fact. Different objects. Chair 1's positive argument decides it — P2's measured harm is causal, a false figure propagating as the slate's premise, and a label with no downstream consequence documents that harm without preventing it. C-14 says so itself: "an inherited figure may still be used". Chair 1 also notes C-14 states a brief rule at line 97, separated from the field list at 89–93, where a brief-builder will not see it.

## Scope — why nothing was applied

All three are proposal-only.

- **C-26** edits `references/protocol.md`. Doubly protected: `references/` is the enumerated governance class, and the text is the quorum mechanism itself. Both chairs agree.
- **C-17** edits `SKILL.md`, but its added text operationalizes the self-target protection, which `SKILL.md:161` names explicitly. Chairs split; the meta-chair takes Chair 2's reading, because `SKILL.md:157` resolves unclear scope conservatively and the split is itself evidence of unclarity.
- **C-10** edits the Step-1 brief specification. Chair 2 flagged this as the one call it could be overruled on. The meta-chair classifies it proposal-only: the defect it fixes is a common-mode input defeating ten otherwise-independent reads, which is an independence property whether or not the file states it as one; and `SKILL.md:161`'s own reasoning applies with full force here — a self-run cannot certify that its own rail edit is a strengthening, because that judgement is made by the very pass the rail constrains. This orchestrator would be the beneficiary of a better brief rule. It is not the right party to declare that rule ordinary content.

## The cost result

Eight candidates, two independent design families, zero survivors. Both chairs agree the outcome is correct and that its two halves fail for different reasons.

**The tiering family (C-01 to C-04) died of candidate defects.** Each changes roster size and leaves the skill self-contradictory: 39 whole-word occurrences of `five` across 30 lines stay standing, including `mode-contract-tests.md:3` ("five advisors per council" — the skill's own deterministic preflight), `SKILL.md:108` ("send its five role prompts as five Agent calls in one message"), `protocol.md`'s verbatim reviewer prompt ("What did ALL FIVE responses miss?"), and `report-template.md:109`, which makes a *deliberate* three-member run report as damage. Beyond incompleteness: C-03 rewrites "never turn a two-council run into a one-council evaluation or auto-apply path" to permit exactly that, and C-04 drops the Adversarial Failure-Mode reviewer that `roles.md:37` makes mandatory for a skill that auto-applies edits.

**The routing family (C-05 to C-08) died of the success test.** P1's test as written — "a **run** on a small, low-risk problem demonstrably spends fewer subagents" — presupposes that a run occurs, and so excludes by construction every candidate that answers by not convening. C-05 flagged this about itself and was refuted on the flag. Chair 1: "the test was the wrong test, and the outcome would have been the same under a right one."

**On the lineage reference.** `a-archive/reference/llm-council-best-practices.md` recommends a Quick mode four separate times (L19, L264, L435, L457) and calls five advisors "practitioner consensus, not academic finding" (L581). The skill adopted that reference's five-role roster and its no-revision finding, left the cost recommendation, and then added a prohibition the reference never supported. Chair 2's resolution is the sharpest result of this run: the reference's Quick mode drops peer review, and peer review is what this skill's eligibility floor rests on. That advice was written for a council whose output is an answer; here the output is an applied edit to the skill's own governing files, so the evaluator panel is the product, not overhead. And C-26's arithmetic makes the economics worse than the reference assumes — at three the floor becomes unanimity, so a cheap tier buys fewer calls *and* more no-survivor runs. **Five is unjustified and cutting it is unsafe here.**

**P1 is real and unsolved.** Both chairs converge on the fix: split it into two success tests — a run that occurs is cheaper, and a small problem does not convene one — and make exhaustive `five` → `N` coverage a stated constraint, so no candidate can look complete while touching four sites out of thirty.

## Recorded orchestrator fault

C-01, C-03, C-04 and C-07 were transcribed into the frozen ledger with parts of their implementation **described rather than written** ("tier definitions as in mechanism", "PREPEND a new paragraph deriving the scope"). The generators supplied full verbatim text; this orchestrator condensed it while freezing thirty candidates. Four evaluators refuted on that basis, citing the skill's own "no placeholder prose" and "byte-for-byte" rules — correctly about the ledger, unfairly about the candidates.

Weight: none against P1's direction, since each of the four also fell to grounds no transcription-citing evaluator raised. Real weight against P1's finality, and sharply on C-01 — Chair 1 notes the condensed portion is precisely where a full `five` sweep would have lived, so its decisive refutation cannot be separated from the ledger's defect. **C-01 is owed re-adjudication on verbatim text.** C-03 and C-04 would fall again.

## Preserved dissent

- **C-07's fail-direction taxonomy, which died with its candidate:** a production cut fails toward `solved-no-survivor` (nothing ships), a verification cut fails toward shipping a wrong edit, and a launch cut cannot fail at all. True independently of C-07's implementation, and the right frame for any future cost work.
- **C-08's ground, from the skill's own lineage:** trigger discipline is a quality concern, not just a cost concern — a size-inappropriate council amplifies one missing context across ten agents. That reframes the routing family as a correctness answer misfiled as a cost answer.
- **C-01's observation:** nothing in the apply path reads the roster count, so roster size buys coverage, not safety.
- **Chair 1 on unanimity:** 10/10 HOLD means "no defect visible at this reading depth", not corroboration. All six eligible candidates are small additive prose edits — exactly the class where a same-model panel converges cheaply. The refutations carried counted facts; the holds carried none.

## Evaluator-only findings, addressed by no candidate

- `protocol.md:147` and `:149` state the refuter re-grep rule near-verbatim twice, two paragraphs apart — a one-canonical-place violation inside the target itself.
- `report-template.md:109` ("If a council ran with fewer than five advisors… note how it affected confidence") blocks any future roster-scaling fix regardless of slate, because it frames a deliberate small roster as damage.
- The frontmatter description has 101 characters of headroom against the 1024 cap. Two description-editing candidates together spend 91.

## Ground-check record

Every anchor cited by every candidate was grep-verified unique before freezing. Absent-strings confirmed zero across all six files: `budget`, `triage`, `proportion`, `early exit`, `stop early`, `re-measure`, `fact-check`, `panel size`, `roster size`, `stricter`, `AskUserQuestion`, `unanimity`, `attested`, `provenance`, `blast`, `radius`. Skill totals verified at 712 lines / 12,021 words.

Three candidate grounds failed verification and were recorded rather than silently dropped:

- A tradeoff claiming the roster count appears at "roughly ten sentences" and another claiming "26 sites"; the true figure is 39 occurrences across 30 lines. Both understate, in the direction that flatters their own argument.
- One candidate's line enumeration for `proposal` in `SKILL.md` was partly wrong; its load-bearing half (absent from `## When To Invoke` and `## Cost`) verified.
- One candidate read the shared preamble's untrusted-evidence list as five categories; it names six. Verified against the file. That candidate held with three evaluators and died on the fourth's catch.

## Self-report

- **The orchestrator degraded four candidates while freezing them, and evaluators refuted them for it.** Condensing implementation text during transcription is the same failure as last run's mis-decoded candidate text, one stage later, and both times the pressure came from slate size. The protocol specifies the generator's output contract and the evaluator's, and says nothing about the transcription between them. → upgrade: state that the frozen ledger carries each candidate's implementation byte-for-byte as returned, that condensing or paraphrasing it invalidates the freeze, and that a slate too large to transcribe verbatim is a slate that must be split across runs rather than summarized.
- **Nothing bounds the slate.** Ten generators × three candidates is thirty by construction, and thirty candidates × ten evaluators is the quadratic that produced the transcription pressure above. The skill states a per-generator cap and no total. → upgrade: cap the slate, or make the per-`P_ID` candidate limit a function of generator count, so the evaluation phase cannot grow quadratically with the roster.
- **The problem manifest's success tests decided the P1 outcome, and one of them was wrong.** P1's test presupposed a run occurs, which excluded an entire family of answers on a technicality rather than on merit; both chairs said so independently. Nothing in the skill requires a success test to be checked for what it forecloses. → upgrade: require each frozen `P_ID` to state which classes of answer its success test admits and which it rules out, so a test that excludes a whole solution family does so visibly and deliberately.
- **The self-target protection makes a self-run on cost or quorum proposal-only by construction, and the skill discloses that only after the spend.** This run spent 22 subagents to produce three proposals, and that outcome was fixed before the first launch. Three of the four problems on the manifest could only ever end this way. → upgrade: this is exactly what C-17 proposes, and its being proposal-only is the defect demonstrating itself.
- **The refuter gate was not reached.** With nothing applied, the paired locator/entailment refuters had no load-bearing in-folder edit to check, though `mode-contract-tests.md` states they still run on a self-target solve touching governance text. That tension between "refuters guard application" and "refuters still run when nothing is applied" is unresolved in the skill and was surfaced to the user rather than settled unilaterally.
