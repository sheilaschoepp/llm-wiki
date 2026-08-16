---
type: skill-llm-council-report
date: 2026-08-16
target: multi-skill/references/verification.md (with ingest, audit, supersede, check_structure.py)
mode: refuter-gate only (no council convened)
result: settled
---

# Refuter gate over the eleven held findings

The prior session surfaced eleven findings against the shared verification spec and `ingest`, verified that each described defect existed, and deliberately withheld all of them because each changed a verification gate rather than fixing a contradiction. This run put them through the adversarial gate and applied what survived. No council was convened — that is Jobs 1 and 2, still outstanding.

## Method

Three refuters, spawned read-only, each given a different angle rather than the same prompt three times, per the spec's own "vary the shape across them" rule:

- **Redundancy** — is the rule already stated somewhere the same run would load?
- **Harm and cost** — assume the defect is real; attack the proposed fix instead. Given `verification.md` is loaded by five skills, every addition is paid five times.
- **Misreading** — does the described defect actually exist, or did the diagnosis misread the text?

Every returned quote was re-grepped against its file before being acted on. All quotes re-grepped; no fabrication in any of the three returns.

Agent-type deviation: no available agent type has an exact Read/Glob/Grep toolset. `Explore` was used (no Edit/Write/NotebookEdit) with an explicit instruction to read every file in full rather than sampling excerpts.

## Outcome

Eleven findings in, five gate changes plus two structural changes out. Six proposals were refuted.

### Applied

| Finding | What shipped |
|---|---|
| 3a | Proof-of-read on a `holds` verdict, once per batch |
| 3c | Setting Status condition 2 clause for pre-existing unmarked claims |
| 3e | Crop-sourced evidence carve-out to the discard rule |
| 3g | Tier-overlap tie-break (the higher tier governs) |
| 3h | "No refuters, no stamp" terminal rule |
| 3j(i) | Report templates moved to `ingest/references/report-shapes.md` |
| 3k | Reference depth/TOC check made able to fire, with two exemptions |

### Refuted — not applied

| Finding | Why it died |
|---|---|
| 3a as proposed | Requiring a quote on every `holds` manufactures the failure it closes |
| 3b | Orchestrator proof-of-read is already a re-checkable artifact |
| 3d | Non-PDF question 1 would make every media ingest a permanent non-stamp |
| 3f | Correct as written — the handoff misread the parenthetical |
| 3g (report half) | Per-claim tier ledger buys no detection the tier breakdown lacks |
| 3j(ii) | The audit copy is not a near-verbatim duplicate |

## The findings in detail

### 3a — the unfalsifiable certifying path

**Diagnosis sound, proposed fix wrong.** The evidence duty is scoped to a refuter that refutes or cannot confirm, so a unanimous batch returns nothing showing any refuter opened the raw, and both report shapes collapse the whole quorum to the literal words `all held`.

The proposed cure — require a verbatim quote on every `holds` — was refuted on mechanism. At the Tier-3 default the claim is usually a summary, where the spec already requires each refuter to recompute the whole set cold, "not the single cell the claim cites (the cited cell is the evidence the author selected because it fits, so confirming it certifies the distortion)". Demanding a quote demands exactly that cell. The requirement would have pushed refuters toward the one artifact the spec names as distortion-certifying, at roughly 75 evidence items and 75 orchestrator greps per batch, paid by five skills.

One refuter also corrected the handoff's reasoning: the "default to refuted unless the raw plainly supports the claim" instruction cuts the *other* way, making `holds` the epistemically expensive verdict. The load-bearing text is the evidence asymmetry, not the prompt instruction.

**Shipped instead:** each refuter returns one proof-of-read per batch — a verbatim quote plus the physical page, for any one claim it held — and the orchestrator re-greps that one quote. Three greps per batch rather than seventy-five, and the certifying path stops being unfalsifiable.

### 3c — reingesting a draft page

The claim check's scope is "exactly the claims this run wrote or changed", but Setting Status condition 2 requires every non-obvious claim on the finished page to sit in one of three routes, and a pre-existing unmarked bullet on a `draft` page fits none.

The redundancy refuter argued this is already safe: such a claim is "neither certified nor honestly marked", so the page simply stays `draft`. True, and the safety net holds — but it leaves the common path permanently unstampable while the spec asserts twice that ingest normally stamps.

The sharper problem is a contradiction the handoff did not name: `existing-mode.md` says every claim cited to this raw "is inside this run's reach — it is this run's to certify or fix", which the scope sentence denies. Condition 2 now states that on a non-`verified` page the inherit route is unavailable, so a pre-existing unmarked claim cited to the raw this run read is the run's to certify or fix, and one cited to another raw is marked.

### 3f — the replaced-attachment parenthetical

**Refuted.** Both the misreading refuter and an independent read reached the same conclusion. The parenthetical's two consequents chain to the *unmarked* state: an attachment swap alters no page text, so the hash does not move and lint cannot catch a *missing* mark — which is precisely why the mark is declared mandatory rather than left to a mechanical check. It asserts nothing about the hash after the mark lands. No contradiction with `body_hash.py`, whose docstring governs the post-mark state.

Applying the handoff's reading would have inverted a correct rule.

### 3k — the scanner all-clear

Understated in the handoff, which framed it as an ingest problem. Measured: **all fourteen skills use zero Markdown links**, so `check_reference_depth_and_toc` was dead repo-wide.

Turning it on naively produced about fifteen findings across five skills, nearly all against patterns the schema prescribes. Two principled exemptions were needed — shared `multi-skill/` targets, and siblings that `SKILL.md` already cites directly. After both, one finding remained, and it was a comparative aside the authoring rules expressly permit; that aside now names forget's removal mechanics in prose rather than as a path.

Also measured, contradicting part of the handoff's framing: `missing_toc` fires above 100 *lines*, and every reference file over that already carries a `## Contents`. And `broken_md_link`'s job on backticked paths was already being done by `broken_inline_ref`. The genuine dead check was depth, not existence.

## Verification

- 296 tests pass (286 before; ten added for the checker change).
- `check_structure`, `check_h2_case`, `check_internal_refs`, `check_musts`, `check_synonyms`, `check_kwargs`: zero findings across all fourteen skills.
- `check_wiki.py 1-wiki`: `[]`.
- `check_consistency.py`: one finding, pre-existing — see below.

## Not done

- **Jobs 1 and 2** — the `ingest` council re-run, and first councils on `lint` and `consistency`. Untouched. The `verification.md` changes above should be in the ingest council's brief as current state, not re-litigated.
- **3j(iii)** — `ingest`'s pre-write gate is listed in the checklist between Steps 3 and 4 but its text lives in Step 5. Confirmed real, deferred: `ingest/SKILL.md` sits at 6497 of 6500 body words and the fix needs about four, which would mean shaving prose not reviewed this run. Step 4 back-references the gate explicitly, so it is discoverable.
- **3j(ii)** — the audit batching paragraph is *not* the near-verbatim duplicate the handoff described. It carries an extra constraint (the per-claim verdict rule) that the shared spec keeps in a different bullet, plus a cross-reference to `apply-fixes.md`. A pointer swap would drop material; needs a real decision rather than a deduplication.
- **3j(iv)** — the description rewrite. Current `ingest` description measures 1010 characters against the 1024 ceiling. Not attempted; the handoff's own warning about a mis-measured description applies.
- **Pre-existing consistency finding.** `2-outputs/skill-llm-council/HANDOFF-next-session-prompt.md` does not match the output naming pattern. Introduced by commit `3d2c16f`, the handoff's own commit — so the handoff's "zero findings" claim was accurate one commit before it was written. Renaming it is a file rename on a user-authored document, so it is flagged rather than done.

## Self-report

- The refuter gate again killed most of what it was given — six of eleven, including the finding the handoff called most serious. The three-angle split did the work: the redundancy angle alone would have wrongly killed 3c, and the cost angle alone would have wrongly cleared 3g. Two refuters reached opposite conclusions on the tier question and the split was settled by reading the text directly, not by vote → upgrade: when refuters disagree on a textual question, the orchestrator should always settle it against the file rather than counting verdicts, and this should be stated in the gate procedure rather than left to judgement.
- An advisor measurement was wrong again, exactly as the prior session warned. The cost refuter quoted `ingest` at 6528 words and `audit` at 6501 — `wc -w` figures including frontmatter, where the checker counts body words only (6492 and 6458). Its conclusion survived because every surviving fix landed elsewhere, but a fix targeting `ingest` would have been sized against a number 36 words wrong → upgrade: the gate prompt should state the measurement method for any budget the refuter is asked to reason about.
- Measuring the blast radius before shipping the checker change was what prevented a bad edit: the naive fix looked correct and would have fired fifteen findings against sanctioned architecture → upgrade: a proposal to enable a dormant check should carry a required simulate-first step, since a dead check's true-positive yield is unknown until measured.
