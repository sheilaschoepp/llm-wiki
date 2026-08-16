---
type: skill-llm-council
date: 2026-08-16
target: "ingest"
target_path: "./.claude/skills/ingest/"
applied: 14
cross_file_proposals: 9
---

# Skill LLM council: ingest

Path: `./.claude/skills/ingest/`
Run: 2026-08-16 20:23
Outcome: 14 edits applied, 9 cross-file proposals, 6 of 15 load-bearing edits killed by refuters — including two that would have contradicted rules landed earlier the same day.
Value over the skill-linter baseline: all six deterministic scanners returned zero findings on `ingest` before this run and zero after, so every finding here was invisible to the cheap pass. The load-bearing ones: a scope incoherence between the claim check and Setting Status condition 2 that lets a reingest stamp `verified` over never-checked bullets; a proof-of-read rule that lets a refuter choose which claim it proves it read; the repeated-literal sweep writing outside the approved plan; and two hardcoded `draft` outcomes in `existing-mode.md` that contradict the current certification model. None is mechanical.
Churn vs prior run: `skill-llm-council-2026-08-13-2146-ingest-audit` covered `ingest` jointly with `audit`. No overlap in applied lines — that run's edits were to verification framing; this run's are to scope, status routing, and duplication. Not oscillation.

## Task brief

Purpose: `ingest` processes one named raw source from `0-raw/` into a source page plus the atomic concept/entity pages it supports; auto-detects new vs. reingest mode; supports deep mode and optional frames; extracts figures; then certifies every claim it wrote against the raw through independent refuters and sets page status.

Good-version criteria: never stamps `verified` on a page carrying an unchecked non-obvious claim; never fabricates a locator, mechanism, or citation; the per-decision `AskUserQuestion` gate fires for every candidate; reads the whole raw every run (a book is the sole exception); stays inside its word budget; does not duplicate rules whose canonical home is `CLAUDE.md` or the shared spec.

Binding rules: `CLAUDE.md`; the two skill-authoring references under `multi-skill/references/`; `a-archive/reference/skill-authoring-best-practices.md`; `a-archive/style/ai-writing-tells.md`; `a-archive/style/coding-best-practices.md`; the prompting and context-management references.

Useful disagreement: whether the claim check's scope is coherent with Setting Status condition 2; whether refuter tiering is affordable and correctly graded; whether the 11 steps are the right decomposition; whether frames earn their complexity; whether the `AskUserQuestion` volume is workable.

Known-wrong at brief time: the five gate changes landed earlier on 2026-08-16 (recorded in `skill-llm-council-2026-08-16-1950-held-findings-refuter-gate.md`) were given to every advisor as current state and fenced off from re-litigation. Structural baseline: all six scanners clean.

Related context: every advisor was granted bounded read-only access (Read/Glob/Grep, no Edit/Write) rather than inlined excerpts, because the relevant breadth — `ingest/` plus six references, the 8179-word shared spec, `CLAUDE.md`, and five sibling skills — was impractical to inline. Named files: `.claude/skills/ingest/**`, `.claude/skills/multi-skill/references/verification.md`, `dependent-cascade.md`, `quarantine-path-convention.md`, `inbound-reference-discovery.md`, `verification-neutral-fixes.md`, `CLAUDE.md`, and the `SKILL.md` of `audit`, `query`, `synthesis`, `supersede`, `lint`, `forget`. Every advisor was barred from `0-raw/` and from prior `2-outputs/skill-llm-council/` reports, so no council member anchored on an earlier verdict. Per the protocol, read-access use makes the Step 2 divergence check mandatory; it was performed and both councils diverged.

## Council 1 — cognitive lenses

### Step 2 responses

Independence: the five calls were issued as five tool uses in a single message, in parallel. No sequential leakage.

Full responses are preserved at `/tmp/.../scratchpad/council/anon-c1.md` as issued to peer review; the substance of each:

**Contrarian** — Condition 2 obligates claims the claim check's own scope disowns, and the report has no slot for them: a reingest of a 30-bullet `draft` page that rewrites 6 bullets can truthfully report "6 written, 6 certified, all held" and stamp `verified` over 24 never-checked claims. A split on a claim cited to this run's own raw has two spec routes and the cheap one stamps. The refuter picks which claim it proves it read, so one genuine read launders 24 rubber stamps. No report slot records that the `AskUserQuestion` gate fired. Confidence: high.

**First-Principles** — Same scope incoherence, reached independently: "an agent reading the spec top-down checks set A, then meets a status rule demanding A ∪ B, and the cheapest reconciliation is to stamp." Frames buy less than they cost, and planning question 5 gates nothing durable. Steps 6 and 7 claim a draft-then-apply split that does not exist. The certify-at-authoring rationale ("nearly free, the raw is open") is false for the expensive part, since refuters open the raw cold either way. Confidence: high on scope and labels, medium on frames.

**Expansionist** — `ingest` is the only skill in the check chain with no machine-readable terminal state in its report. The shared spec promises "the escape valve the calling skill defines" and only `audit` defines one. ~150 words of ingest-only content sit in the five-caller spec. Step 8 restates Setting Status condition 3 nearly verbatim. Confidence: high.

**Outsider** — A new user's first ingest fails twice before Step 5: the PDF is not in `0-raw/` (hard read-only, no route defined) and the conda env is not active (never mentioned in `ingest/`). Description spends 32 characters on non-triggering ballast. Empty-wiki first run unguarded. The spec never names how a refuter is spawned. Confidence: high.

**Executor** — The three-round cap has no terminal status. Step 1 and Step 8 disagree on refuter batch composition. Step 7's cascade `needs-update` can be silently overwritten by Step 8's four conditions — an ordering default, not an edge case. Reingest question volume is undercounted at 10–20; realistic is 25–35. Confidence: high.

### Anonymization

A = Expansionist, B = Executor, C = Contrarian, D = Outsider, E = First-Principles. Letters were assigned so position carried no signal; reviewers never saw this mapping.

### Step 3 peer reviews

Preserved in full at `.../scratchpad/council/peer-c1.md`. Summary of the five:

Strongest: B (3 reviewers) or C (2). Biggest blind spot: D (4 reviewers) — it spends its allowance on onboarding while missing the certification core, and one of its description claims is factually wrong. Biggest all-five miss, named by three reviewers independently: every response edits the five-caller shared spec without checking blast radius on `query`, `synthesis`, `supersede`, `audit`, and reviewer 3 caught the sharpest form — **C and E want ingest-specific vocabulary inserted *into* the spec, which is precisely the contamination A argues to remove from it, and the conflict is unflagged**. Reviewer 2 added the other structural miss: the real budget slack is the 410-word "Conventions (recap)" section, not the 11–57-word parentheticals every advisor scavenged. Minority to preserve: E's frames verdict (4 reviewers), D's first-run findings (2).

### Step 4 chair synthesis

The chair netted the change-set against a 3-word headroom, funding it from a single measured 53-word cut, and resolved the central conflict with a distinction both sides missed: **direction is not the issue, caller-neutrality is.** A is right that ingest-only content should leave the spec; C and E are right that the scope hole needs patching there; both ship, with the patch worded "a raw this run read" rather than "this run's raw", so a caller that opened no raw gets an empty second set and is unaffected. Ruled B's ingest-side copy of the scope fix out (belongs in the spec, one copy). Ruled against D's conda finding (canonical in `CLAUDE.md`) and corrected D's description claim. Preserved E's frames verdict as the strongest dissent while ruling against it — no single anchor, and it would cascade through four files. Confidence: high on the funding cut, scope patch, and three verified drifts.

## Council 2 — skill specialists

Roster, composed per the selection rule: the three core specialists (Description & Trigger, Structure & Token-Economy, Best-Practices-Compliance) always run. The two selectable slots went to **Adversarial Failure-Mode** (mandatory — ingest auto-applies edits, quarantines attachments, cascades `needs-update`, and stamps `verified`) and **Schema-Compliance** (ingest writes and maintains the wiki). Dropped for the slot limit, in the fixed priority order: Source-Fidelity (ingest reads raw sources), Prompt-Engineering (it spawns refuter subagents), Instruction-Clarity. Script & Python-Quality not indicated — `ingest` bundles no `scripts/`.

### Step 2 responses

Independence: five calls in one message, in parallel. Full text at `.../scratchpad/council/anon-c2.md`.

**Description & Trigger** — `ingest` is the only skill whose description states no boundary, while `supersede` and `audit` descriptions actively claim its trigger vocabulary. Genuine over-trigger on "write up or summarize this PDF" where the body says "into the wiki". ~130 characters go to mechanics with zero discovery value. Mixed point-of-view. Proposed a measured 1006-character replacement. Confidence: high on the diagnosis, medium on wording.

**Structure & Token-Economy** — The shared spec carries an ingest-only block paid five times. SKILL.md spends ~200 words re-arguing its own architecture; the Limits closing line "spends 33 words saying it is not spending words". The re-voicing rule is written three times at full length. `planning-questions.md` (1951 words, 31 lines, zero H2) is the one reference genuinely needing a Contents, and the 100-line TOC checker structurally cannot reach it. Confidence: high on cuts, medium on the "Ingest owns its claims" trim.

**Best-Practices-Compliance** — Nested reference two levels deep (SKILL.md → `planning-questions.md` → `relationship-sweep.md`, never named in SKILL.md). The certification-reach rule stated three times. Step 9 points at the wrong file for report shapes. `report-shapes.md` mixes `##` and `###`. `CLAUDE.md`'s shared-reference list omits files and misstates the spec's callers. Confidence: high.

**Adversarial Failure-Mode** — The Step 8 repeated-literal sweep is an ungated write channel: it applies "the same fix wherever the claim recurs" across all of `1-wiki/`, on pages never in the plan, never through the clean-tree gate, never given a question. The clean-tree gate covers pages, not attachment binaries. The "genuinely image- or media-based source" clause is an escape hatch on a scanned PDF that ends in a `verified` page whose checked body is empty. Confidence: high on the first three, medium on the empty-hash case.

**Schema-Compliance** — `existing-mode.md` hardcodes `draft` in two places and hands re-verification to `audit`, contradicting "the run that certifies may stamp" and `audit` "does not re-certify by routine". Source-page locator coverage is under-stated. The two canonical citation forms are never in context when concept/entity bullets are drafted. Dropping `*[tentative]*` on a `verified` page moves the hash with no stated consequence. Confidence: high.

### Anonymization

A = Schema-Compliance, B = Description & Trigger, C = Adversarial Failure-Mode, D = Structure & Token-Economy, E = Best-Practices-Compliance.

### Step 3 peer reviews

Preserved at `.../scratchpad/council/peer-c2.md`. Strongest: C, unanimously (5/5) — the only response reasoning about runtime consequence rather than text hygiene. Biggest blind spot: D (4 reviewers) — it optimizes the budget while others need it, and its headline cross-file deletion rests on an unverified assumption. All-five misses: the budget is one shared pot nobody netted; mid-run interruption is wholly undefined (reviewers 3 and 4); nobody proposed validating against the repo's own enforcement layer (reviewer 5); `ingest-memory.md` is loaded at Step 1 and empty. Reviewer 4 caught that C's stem-collision finding overstates. Minority to preserve: C's terminal-state rule, B's boundary clause, D's cross-file cut.

### Step 4 chair synthesis

Netted cuts of −125 against adds of +81 for a 6453 landing. Split D's programme in half: cutting navigational meta-text is free, cutting *rationale* is not — three reviewers independently flagged that the rationale is what stops certification degrading into a checkbox. **Corrected peer review itself**: reviewer 1's double-spend claim was wrong, since D cuts Limits bullet 4's tail (31 words) and E cuts the final bullet (36) — different text, so the pot is larger than the brief assumed. Ruled delete-not-move on the spec paragraph, against Council 1's Expansionist, because Step 9 already states the guard in full. Confidence: high on the status fixes, repoint, description, and arithmetic; medium-high on the spec deletion pending a test-suite check.

## Step 5 — meta-chair reconciliation

Full ordered set at `.../scratchpad/council/final-changeset.md`. Merge notes:

- **Cross-council agreement (high confidence):** the Step 8 condition-3 restatement is dead duplication and is the funding source (both councils, four advisors); Step 9's pointer is wrong; the shared spec is over-billed with ingest-only content; `existing-mode.md`'s hardcoded `draft` contradicts the current model. Shared-roster check: these did not arise from overlapping angles — the cut was found by cognitive lenses and specialists on different grounds (budget vs. compliance), so the agreement is genuine corroboration.
- **Single-council changes carried:** the raw-not-in-`0-raw/` edge case (Council 1 only), the `*[tentative]*` hash note and source-page locator rule (Council 2 only). Each earned its place on a verified absence.
- **Conflicts resolved on the merits:** Expansionist's *move* vs Structure's *delete* of the spec paragraph — resolved to **delete**, because `SKILL.md` Step 9 states the guard in full and a move would create a third copy. Chair 1's Step 9 wording vs Chair 2's — resolved to **Chair 1's**, because the spec deletion is a cross-file *proposal* and does not land this run, so the honesty-guard pointer must stay valid.
- **Scope split:** every `verification.md`, `dependent-cascade.md`, `CLAUDE.md`, and `audit/` edit is cross-file and was never applied, per Step 6's rule. That rule is why the highest-value findings below sit in the proposals section rather than in the diff.
- **Meta-chair additions:** none. Every edit in the final set traces to a chair-synthesis line.
- **Explicit deviation from a chair:** Chair 2 accepted Expansionist's `result:`/`pages_pending:` report fields; the meta-chair excluded them, following Chair 1 — no consumer reads them, and "detection without consequence" is the trap this skill names.

## Completed changes

Adversarial verification — 15 load-bearing edits, one refuter each (batched by relatedness), all read-only and independent of the meta-chair. **9 hold, 6 refuted.** The deletion refuter was given the "is this the only statement of this rule anywhere?" hunt that `skill-llm-council-memory.md` (2026-08-15) records as catching four of five bad deletions.

| Edit | Verdict | Ground-truth reason |
|---|---|---|
| Step 8 condition-3 cut | holds | Spec condition 3 carries the text almost verbatim; only "not by the word Critical" is novel and the replacement keeps it |
| Three-round-cap terminal status | **refuted** | Premise false — the spec already states it ("never left at `draft`"), and a categorical "never `draft`" collides with the "No refuters, no stamp" bullet where `draft` *is* mandated |
| Repeated-literal-sweep gate | **refuted** | Already bound by CLAUDE.md Safety; and it converts a mandatory sweep into a declinable step with no fallback disposition |
| Clean-tree gate → attachment binaries | **refuted** | Its parenthetical is false: `quarantine-path-convention.md` verifies a byte-identical copy before unlinking, so quarantine preserves the file whether or not git held it |
| existing-mode `needs-update` → Setting Status | holds | Spec: "the run that certified the claims is the run that may stamp it"; CLAUDE.md: "`audit` does not re-certify by routine" |
| existing-mode frames-widening re-stamp | **refuted** | CLAUDE.md states a hard rule: a scope-widening change "**still** resets the page to `draft`" — the edit converts a mechanical reset into a judgement call |
| `*[tentative]*` hash note | holds | `body_hash.py` masks only `*[unverified]*`; the re-stamp branch is the schema's legitimate re-stamp (1), and the check already requires certification against the raw |
| source-page locator rule | holds | CLAUDE.md states it almost verbatim; the file states it nowhere else; SKILL.md Step 5 scopes locator *form*, not which claims owe one |
| Description replacement | **refuted** | The boundary clause is false — `audit`'s description says it "applies content fixes (splits, merges, rewrites)", so "audited (re-verify, no rewrite)" misstates a sibling; it also deletes an accurate external-database boundary |
| Step 6 inline citation forms | **refuted** | Both forms are in CLAUDE.md, read at session start; inlining breaks ingest's own rule to "cite `CLAUDE.md` rather than copying (copying drifts)" |
| Raw-not-in-`0-raw/` edge case | holds | Nothing in ingest routes a raw outside `0-raw/`; the adjacent rules forbid the copy but define no stop-and-ask route |
| Deletion D1 (Limits meta-tail) | holds | Every rule it names is stated at the named location; the span states no rule of its own |
| Deletion D2 (Limits reach bullet) | holds | Canonical in the spec's Setting Status and in ingest's own Conventions recap; Step 8 routes to the recap, not to Limits, so no pointer dangles |
| Deletion D3 (Pattern paragraph) | holds | The Procedure checklist below states the same mapping operationally; only the label was unique, and a label is not a rule |
| Deletion D4 (Step 4 inline restatements) | holds | Both verbatim in ingest's own Limits; CLAUDE.md → Skill authoring forbids restating a Limits rule inline |

Applied in-folder (14 edits), smallest reasonable change each:

- Judgement edits: `ingest/SKILL.md` Step 8 condition-3 span 78→25 words; `ingest/SKILL.md` Edge cases +1 bullet (raw not under `0-raw/`); `ingest/references/existing-mode.md` `needs-update` check → Setting Status routing; `ingest/references/existing-mode.md` `*[tentative]*` check + hash consequence; `ingest/references/source-page-writing.md` self-cite line → locator-coverage rule.
- Deletions: `SKILL.md` Purpose "Pattern:" paragraph (−39); Limits bullet 4 tail (−31); Limits reach bullet (−35); Step 4 two inline restatements (−14).
- Mechanical: 4 (Step 9 pointer repointed; Steps 6/7 headings + matching checklist lines relabelled to match their bodies; `report-shapes.md` reingest template `###`→`##` ×5; `report-shapes.md` stale honesty-guard pointer; `planning-questions.md` gained `## Contents` and two promoted H2s).

Budget: 6497 → **6363** of 6500 body words. 137 words of headroom recovered, which also pays for the previously-deferred Pre-write-gate relocation whenever a later pass takes it.

Skipped / reverted: the 6 refuted edits above, demoted to `[needs-review]` and listed below. Also excluded at Step 5: Expansionist's `result:`/`pages_pending:` fields (no consumer); Outsider's conda-env precondition (canonical in `CLAUDE.md`); Structure's cuts of "Verification stands in for human re-voicing" and the "Ingest owns its claims" trim (three reviewers flagged this as load-bearing framing; not needed, the pot balanced without it); Adversarial's Conventions "Status and markers" trim (Step 8 delegates to it — cutting orphans the pointer); Executor's reingest question-count guidance (load-bearing, no refuter issued, so not applied by default rather than by judgement).

Post-apply sanity check: `check_structure`, `check_h2_case`, `check_internal_refs`, `check_musts`, `check_synonyms` all return zero findings on `ingest` and across all 14 skills. `check_kwargs` not applicable (no `scripts/` in `ingest`). 296 unit tests pass. `check_wiki.py 1-wiki` returns `[]`. `check_consistency.py` returns one finding, pre-existing and unrelated (the 2026-08-15 handoff filename).

## Cross-file proposals

Not applied — these touch shared files. Act on them by hand if you agree. The first two are the run's highest-value findings.

- [cross-file] `.claude/skills/multi-skill/references/verification.md`, claim-check scope sentence — append, caller-neutral: ", plus — on a page entering the run non-`verified` — every pre-existing unmarked claim cited to a raw this run read". Without it, Setting Status condition 2 obligates a set the claim check disowns, and the cheapest reconciliation is to stamp. Four advisors found this independently.
- [cross-file] `.claude/skills/multi-skill/references/verification.md`, "for any one claim it held" → "for a claim the orchestrator names when it issues the batch, a different claim to each refuter in the tier". As written the refuter chooses which claim it proves it read, so one genuine read launders the rest of a 25-claim batch.
- [cross-file] `.claude/skills/multi-skill/references/verification.md` — delete the whole "Recommended next ingests" paragraph (~150 words × 5 callers). Verified safe: no test asserts it, `audit` references it only as a comparative aside, and `SKILL.md` Step 9 states the guard in full. If taken, also repoint Step 9 to drop the honesty-guard half.
- [cross-file] `.claude/skills/multi-skill/references/verification.md`, coverage bullet — scope the media exemption "by kind (a raw under `0-raw/media/`, or `type: media`) — never an image-only scan of a text document, which fails condition 1 however legible its pages".
- [cross-file] `.claude/skills/multi-skill/references/verification.md`, after Setting Status condition 2 — "a page on which this run certified no non-obvious claim, and which entered non-`verified`, is not stamped." **Verified empirically this run**: two pages with entirely different all-marked claims hash identically, so a fully-marked page's checked body is effectively empty.
- [cross-file] `.claude/skills/multi-skill/references/verification.md`, line 7 — the certify-at-authoring rationale ("nearly free … the raw is open") is false for the expensive part, since refuters open the raw cold either way. Replace with provenance and fix-locality.
- [cross-file] `.claude/skills/multi-skill/references/dependent-cascade.md` — "A `needs-update` the cascade sets survives the calling skill's later verification pass; only resolving the named cause clears it." Closes the Step 7 → Step 8 overwrite, and is correct for `supersede` too.
- [cross-file] `CLAUDE.md` → Stay in your lane — the enumerated `multi-skill/references/` list omits `relationship-sweep.md`, `skill-authoring-checklist.md`, and `skill-authoring-checks.md` (three, not the four an advisor claimed — `self-report.md` is named), and it says the spec is "run by `ingest` (Step 8) and `query`", contradicting its own Workflow rules and the spec's header, which bind `synthesis` and `supersede`.
- [cross-file] `.claude/skills/audit/SKILL.md` description — a reciprocal disambiguator against ingest's reingest path, conditional on measuring `audit`'s description against the 1024 cap first.

## Preserved dissent

- **First-Principles on frames** (ranked strongest dissent by both chairs and four peer reviewers). The raw is fully read every run and source pages have no word cap, so frames' entire yield is a shorter source page — bought with union semantics, a scope-widening test, reuse/append/clear, a widening-resets-to-`draft` rule, a widening-must-grow-the-body guard the claim check has to carry because lint cannot, and a recursive planning question whose own default is "chat-only, not page content". The cost accounting is correct. Ruled against only because it is a product decision with no single anchor that would cascade through four files. It is the right charge for a future council, not a defect of this change-set.
- **Structure & Token-Economy on duplication earning its cost.** D itself conceded, at medium confidence, that "Ingest owns its claims" may be doing rhetorical work. Three reviewers agreed and the meta-chair ruled to keep it. But D's underlying instinct — that 6497/6500 is a symptom rather than a constraint to route around — is right, and the 410-word "Conventions (recap)" section remains the standing reserve no advisor anchored a cut in.
- **Description & Trigger on discovery order.** One reviewer called B a blind spot for "advertising a body it never checked"; that inverts the order of operations, since a skill that never fires is not saved by a correct body. B's diagnosis survives even though its proposed replacement was refuted: `ingest` still states no boundary while two siblings claim its trigger vocabulary. The fix needs a clause that describes `audit` accurately.

## Not addressed this run

- **Mid-run interruption** (peer review, both councils' reviewers 3 and 4). Steps 4–7 write multiple files with no partial-run marker, no rollback, and no resume rule; a run abandoned after the source page is written leaves an uncertified page the next invocation treats as a prior view to reingest. No advisor anchored a fix, so nothing was applied. Top item for the next pass.
- The Pre-write-gate checklist/text mismatch, now affordable at 137 words of headroom.

## Self-report

- The refuter gate killed 6 of 15 load-bearing edits, the third consecutive run at or near a majority — and this run inverted the failure mode again. The 2026-08-15 entry recorded over-deletion; here **all four deletions held** and the kills were concentrated in *additions*, three of which asserted something factually false about a sibling file (`quarantine` preserves nothing; `audit` does not rewrite; the spec defines no terminal state). The deletion refuter's "only statement anywhere?" hunt worked; nothing equivalent guards an addition → upgrade: give the refuter prompt for an *addition* a symmetric hunt — "does the file this edit describes actually say what the edit claims about it?" — since a false claim about a neighbour is the shape that got through this run's chairs and both peer-review rounds.
- I under-scoped the refuter batch: two load-bearing edits (the `*[tentative]*` hash note and the source-page locator rule) were bundled into a prompt covering only two others, so they initially had no verdict. I caught it before applying and spawned them, but nothing in the skill forces the count to reconcile → upgrade: Step 6 should require the run to state `load-bearing edits: N / refuter verdicts: N` and halt on a mismatch, rather than leaving coverage to the orchestrator's memory.
- Six advisor or refuter measurements were wrong this run (two `wc -w` figures against a body-word budget, a description at 1012 and another at 1008 where it is 1010 and 1006, a 6533 word count, and a four-file omission that is three). None changed an outcome because the orchestrator re-measured each, but the rate is high enough to be structural → upgrade: the brief should state the measurement command for every budget it cites, not just the number.
