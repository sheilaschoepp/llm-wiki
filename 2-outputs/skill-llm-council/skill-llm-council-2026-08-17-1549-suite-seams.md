---
type: skill-llm-council
run_mode: off-label — whole-suite seam review, full protocol
target: .claude/skills/ as a system (14 skills + multi-skill shared materials)
councils_convened: 2
council_members: 5 + 5
peer_review: 5 + 5 (full)
chair_subagents: 2 (full)
auto_apply: disabled — every finding is a proposal
date: 2026-08-17
status: complete — 22 subagents, 11 ranked proposals, nothing applied
---

# Whole-suite seam review — 14 skills as one system

## Declared deviations from the skill

This run is **off-label**, and that belongs at the top so no reader mistakes it for a standard single-skill pass.

**Off-label target.** `skill-llm-council` Step 1 resolves a directory containing `SKILL.md`, or a `SKILL.md` file, and says "If the path does not exist or has no `SKILL.md`, stop and say so. Do not council the wrong thing." Its Limits say "Reviews one skill per run." `.claude/skills/` has no root `SKILL.md`, so the standard resolution refuses this target.

It was run anyway, at the user's explicit direction, because the skill itself names the gap: a skill reviewed in isolation "hides defects that only surface against its siblings (a drifted shared boundary, a duplicated rule, an inconsistent hand-off)". The target here is therefore **the seams between skills**, not any skill's internal contents — the review a single-skill council structurally cannot perform.

**Protocol: full.** The orchestrator initially scaled the run to 10 subagents on cost grounds, after the user flagged that their weekly usage limit was close, and recorded peer review and both chair syntheses as skipped. The user overrode that reduction ("don't scale down the council") and the full protocol was run: 5 + 5 council responses, 5 + 5 anonymized peer review, 2 chair subagents, meta-chair reconciliation — 22 subagents.

That override is load-bearing for everything below. Peer review killed two findings, refuted the run's headline safety claim, corrected an orchestrator error, and produced the item both chairs called the most valuable in the council. None of it was reachable from the Step-2 responses the reduced run would have stopped at.

| Step | Standard | This run |
|------|----------|----------|
| 2 — council responses | 5 + 5 | 5 + 5 |
| 3 — anonymized peer review | 5 + 5 | 5 + 5 |
| 4 — chair synthesis (subagent per council) | 2 | 2 |
| 5 — meta-chair | orchestrator | orchestrator |
| 6 — auto-apply in-folder edits | yes | **disabled entirely** |

**Auto-apply disabled.** The skill's in-folder/cross-file split is defined relative to "the target skill's folder". With the suite as target, that rule would make every file under `.claude/skills/` in-folder and hand this run write authority over all fourteen skills at once — the opposite of the rule's intent, which is that "one skill's council should not silently rewrite the project's rules or another skill". So the conservative reading governs: **everything is a proposal, nothing is applied.**

## Roster

**Council 1 — cognitive lenses (fixed by the skill, one-line tuning each):**

| Role | Tuning |
|------|--------|
| Contrarian | the worst way the fourteen fail *as a set* — a chain where A hands B something B cannot act on |
| First-Principles | is fourteen the right decomposition, or are some skills artifacts of how the set grew |
| Expansionist | a discipline one skill evolved that its siblings would obviously benefit from |
| Outsider | a researcher who just cloned this template — can they pick the right skill from descriptions alone |
| Executor | the cross-skill dependency graph — the cycle, the deadlock, the contract only one side honours |

**Council 2 — specialists, composed by the selection rule in `references/roles.md`:**

| Role | Why selected |
|------|--------------|
| Description & Trigger | core — always included |
| Structure & Token-Economy | core — always included |
| Best-Practices-Compliance | core — always included |
| Adversarial Failure-Mode | mandatory: the suite acts destructively (`forget`, `cleanup`) and autonomously (`audit`, `skill-linter`) |
| Script & Python-Quality | selected: `multi-skill/scripts/` is shared across skills |

**Dropped for the two-slot limit**, recorded as the rule requires: Schema-Compliance, Source-Fidelity, Prompt-Engineering, Instruction-Clarity. All four were genuinely indicated — the suite writes the wiki, reads raw sources, spawns subagents, and branches heavily — so this roster is more over-subscribed than the rule anticipates. The fixed priority order was followed rather than substituting judgement, which is the rule's purpose (it exists so two valid rosters are not possible for one target). Schema-Compliance's angle is partly covered by tuning Best-Practices-Compliance at schema-versus-skill drift.

## Task brief

- **Purpose.** Fourteen skills maintain one LLM wiki. They share `multi-skill/references/` (9 files), hand off via contracts — most explicitly `audit` gating on `lint`'s and `consistency`'s report `result:` frontmatter — and are meant to own non-overlapping trigger territory.
- **Good-version criteria.** Every task has exactly one owning skill; every "when not to invoke" routes to a sibling that genuinely owns it; shared logic lives once in `multi-skill/references/` and is cited, not copied; hand-off contracts agree on both sides; CLAUDE.md's schema matches what the skills implement.
- **Binding rules.** CLAUDE.md (Skill authoring, Stay in your lane, Operations, Safety rules, Workflow rules); `a-archive/reference/skill-authoring-best-practices.md`; `a-archive/style/ai-writing-tells.md`; `a-archive/style/coding-best-practices.md`.
- **Useful disagreement.** Whether a boundary is genuinely drifted or deliberately overlapping; whether a duplicated rule is drift or a sanctioned local statement; whether a schema/skill mismatch is schema staleness or skill drift — those need opposite fixes.
- **Known-wrong going in.** `2-outputs/skill-linter/` is empty, so no structural baseline exists and the councils were not given one. No whole-suite review has ever run, so there is no prior report to build on. An earlier session today made and reverted edits to `verification.md` and `audit/`; the tree is back to `77e6ce4` state and councils were told to expect CLAUDE.md's audit `result:` paragraph to be currently correct.

## Method notes

Councils were given **bounded read access** rather than inlined excerpts — 2,662 lines of `SKILL.md` plus per-skill and shared references cannot be inlined. The skill sanctions this when inlining is impractical, and flags the cost: correlated output is the expected risk, so the Step-2 divergence check is mandatory for a read-access council and apparent consensus gets more scrutiny, not less. Read scope was bounded to `.claude/skills/`, `CLAUDE.md`, and `a-archive/`; `0-raw/` and `2-outputs/` were excluded.

Each role was additionally required to name, for its strongest finding, the one check that would falsify it **and report the result of running that check** — the tuning recorded in `skill-llm-council-memory.md` (2026-08-16, "The refutation rate is a tuning signal"), which observed that roughly half to two-thirds of load-bearing proposals fall to facts a single grep would have surfaced before the proposal was written.

## Correction to this brief, made mid-run

The brief said **15 skills**. It is **14** — `multi-skill/` has no `SKILL.md` and is a shared library, not a peer. The repo's own tooling already counts correctly (`check_structure.py:617`, "all 14 skills"). Council 1's First-Principles member caught it and reported it as its do-not-ignore.

This is the exact failure `skill-llm-council-memory.md` records on 2026-08-16 ("Put every measurement in a task brief in the unit the finding will be argued in" — a brief carrying a wrong premise can manufacture a finding that survives review because everyone downstream shares the premise). The wrong count went into all ten prompts. It appears not to have manufactured a finding — the member that caught it was the one whose angle depended on it — but no reader should assume that without checking, so it is recorded here rather than silently fixed.

## Verified findings

Every finding below was re-checked by the orchestrator against the files before being recorded. Findings the councils raised that are *not* here either await verification or are held for the chair pass.

### 1. Hard deadlock: audit is locked out by the one Critical only audit can fix

`check_wiki.py:566` registers `locator_page_mismatch` at severity `error` (renders as Critical). `check_wiki.py:522-526` holds `STANDING_NONBLOCKING` — exactly three ids, and that is not one of them. So lint computes `result: blocking`, and `audit/SKILL.md:82` stops the run on a blocking lint.

But both sides name audit as the owner. `lint/SKILL.md:47`: "`audit` or the user resolves `locator_page_mismatch`, opening the raw to correct the citation or the map." `audit/SKILL.md:39` claims it as a Step 5 fact-check cause. Audit can never reach the step that fixes the only thing blocking it.

This is a true cycle, not a sequencing preference. Raised by Council 1's Executor; verified independently here.

### 2. The shared spine cannot be linted, and already carries broken refs

`python3 check_structure.py .claude/skills/multi-skill` returns `Error: SKILL.md not found` and **exits 2**. The scanner requires a `SKILL.md` at the target root, which the shared library has none of. So `broken_inline_ref`, `nested_reference`, `missing_toc` and `html_tag` have never run over `multi-skill/references/`, the most-cited material in the suite.

**Correction, recorded rather than quietly fixed.** This report first stated the scanner exits **0**, making the failure silent. That was wrong twice over: the reviewer who claimed it was wrong, and the orchestrator's verification of it was wrong in the same direction. The verifying command piped the script through `head`, so `$?` captured `head`'s status, not the script's. Three Council 2 peer reviewers independently caught it. The scanner fails loudly, and `skill-linter/SKILL.md:224` already treats exit 2 as blocking.

**The coverage gap itself survives intact** — the shared spine is genuinely unlinted, and the three broken refs below prove the check never ran over it. Only the silent-failure framing dies. Noted because it cuts the finding's severity roughly in half: an unlinted folder is a real gap; an unlinted folder whose scanner *reports success* would have been a much worse one.

Three broken refs confirmed missing on disk, exactly the class the unrun check would have caught:

- `skill-authoring-checks.md:68` places `synonym-ignore.md` "in the skill-linter folder"; it is at `multi-skill/synonym-ignore.md`, and `skill-linter/` has no `references/` directory at all.
- `skill-authoring-checks.md:92` cites `references/checklist.md` — missing.
- `skill-authoring-checklist.md:48` cites `references/checks.md` — missing.

Raised by Council 2's Structure reviewer; all four claims verified here by execution and `test -e`.

### 3. The script-completion guard is absent from the consumers that most need it

`lint/SKILL.md` and `skill-linter/SKILL.md` guard `check_wiki.py`'s stdout — empty or unparseable output is a crashed run, not zero findings. `cleanup`, `forget` and `ingest` invoke the same script without it.

The sharpest case is `cleanup/SKILL.md:199` (step 8.2b), which confirms a hot-thread prune landed by re-running the script and checking "that entry's finding is gone". A crashed run prints nothing, which reads as gone — the guard's absence turning into a false confirmation of a destructive edit.

Raised independently by Council 1's Expansionist and Executor. Verified here, with one correction: the Expansionist reported the guard present in three files including `consistency`; the orchestrator's grep found the phrasing in two (`lint`, `skill-linter`). The discrepancy is recorded rather than resolved — consistency may state it differently.

### 4. Latent deadlock: the ingest→audit chain can make audit's own precondition unsatisfiable

`ingest/SKILL.md:88` writes `pagination-map.md` for every PDF raw. `audit/SKILL.md:88`'s staleness pathspec excludes three agent-data files and says explicitly that `pagination-map.md` "still trips the gate". So an ingest→lint→audit chain leaves an uncommitted `.claude/skills` change that makes audit declare consistency stale — and re-running consistency writes only to `2-outputs/`, never clearing it. The instruction is "re-run consistency rather than stopping", with no bound.

The Contrarian ran the falsifying check and reported honestly that the loop is **not currently live**: `git status --porcelain` over audit's exact pathspec is empty. Mechanism confirmed, latent, fires on the next PDF ingest before a commit.

Related drift on the same seam: audit's exclusion list is a 3-element subset of consistency's 4-element `AGENT_DATA_FILES` (`consistency/references/checks.md:36`). The two sides disagree about what counts as runtime data.

### 5. "Merge these two pages" fires three skills, and the autonomous one has no fence

`supersede` triggers on "replace, swap, merge, split"; `synthesis` on "merge overlapping syntheses"; `audit` advertises "applies content fixes (splits, merges, rewrites)" and "Acts autonomously". None disclaims the other two. `audit` is the only one of the three that edits without asking, and its When-not-to-invoke names only `query`.

Converged on independently by three members — Council 1's First-Principles and Outsider, Council 2's Description & Trigger. Under the read-access correlation caveat, convergence is scrutinized rather than trusted, but these three reached it from different angles (decomposition, naive reading, routing-table analysis).

### 6. No skill owns the task this run was convened to perform

Council 2's Description & Trigger member grepped all 14 descriptions for `all skills|every skill|suite|across skills|overlap|multiple skills`. Sole hit was `synthesis` "merge overlapping syntheses" — wiki pages, not skills. `skill-llm-council` is scoped to "a single skill", `skill-linter`'s "mandate is to fix the one skill the user invoked it on", and `consistency` explicitly disclaims skill quality.

The whole-suite review has no owner, which is why this run is off-label.

### 7. RETRACTED IN LARGE PART — audit's merge is quarantine-with-redirect, not an ungated deletion

**This finding was first recorded as "the most serious finding of the run" and that was wrong.** A peer reviewer tasked specifically with attacking it refuted the core, and the orchestrator verified the refutation. What survives is one real but much narrower defect. The original text is kept below the retraction so the error is legible rather than erased.

**What the reviewer established, verified directly:**

- `apply-fixes.md:109` — "**When a structural call is genuinely ambiguous** — is this one idea stated twice or two distinct ideas? **does the merge target page survive or the merged-away one?** — and the fact-check does not settle it, **do not perform the surgery.** Downgrade the finding to a Warning that names the options and leave the page for the user." The survivor choice is explicitly user-gated whenever it is not determinate.
- `apply-fixes.md:99` — the prior version is copied to `2-outputs/supersede/preserve/` before removal, under the shared quarantine convention.
- `apply-fixes.md:100` — inbound wikilinks are found and rewritten.

So a merge retirement is a **quarantine-with-redirect under a determinacy gate**, not a bare deletion, and it is authorized by `CLAUDE.md:672`/`:426`. The `CLAUDE.md:744` per-file rule governs deletions that destroy content; this preserves it.

**What survives, and it is worth fixing:** `apply-fixes.md:99` carries only the `-N` clash suffix and `git check-ignore -q`. It **omits the `cmp -s` byte-identity check** that `quarantine-path-convention.md:11-16` makes mandatory and that `forget` and `supersede` both wire in — and `:16` names forget/supersede/ingest, not audit. A truncated copy therefore passes audit's check and becomes the only copy. That is a genuine gap in a preservation path, one line wide.

**Also downgraded:** the claimed self-contradiction at `audit/SKILL.md:214` is scoped to the unsupported-page case, not merges. Two reviewers called it sloppy phrasing rather than a contradiction, which matches the orchestrator's own earlier note.

**One thing no member found:** the preserved copy that audit's merge depends on is itself prunable by `cleanup`'s opt-in preserve-folder sub-mode. The retirement's only fallback is deletable by a sibling skill.

---

*Original finding, retained for the record and now known to be substantially wrong:*

`audit/references/apply-fixes.md:101` reads, verbatim:

> "Inherit those mechanics but not supersede's approval gates: audit is the autonomy exception and asks the user nothing."

And `audit/SKILL.md:186` confirms the outcome — "a merge removes one". So audit's merge path deletes a live wiki page without asking.

The identical deletion is gated twice elsewhere: `forget/SKILL.md:103` (per-file, "never as one question") and `supersede/SKILL.md:71` (naming the deletion explicitly). And `CLAUDE.md:744`, which states the per-file deletion rule, closes: "`forget`, `supersede`, and `cleanup` apply this uniformly." **Audit is not named.** Its deletion is undefined by the safety rule rather than exempted from it.

Three aggravating factors, each verified:

- **The skill contradicts itself.** `audit/SKILL.md:214` ends "audit does not auto-remove a page". In context that clause is scoped to a *support* finding (which it routes to `forget`), but it reads as absolute, and a reader checking whether audit deletes will find the reassuring half. The reviewer called this "directly false"; that is slightly stronger than the context warrants — it is a scoped statement phrased absolutely, which is a real defect but a different one.
- **Half the quarantine convention is honoured.** `apply-fixes.md:99` cites `quarantine-path-convention.md` but carries only the `-N` clash suffix and `git check-ignore -q`. It omits the byte-identity check and the "before unlinking the original" ordering that the convention makes mandatory and that both `forget` and `supersede` wire in. A truncated copy passes audit's check and is then the only copy.
- **No git-state precheck.** `forget` and `supersede` both check git state before deleting; audit does neither, so merging a page created this session leaves nothing recoverable.

The reviewer ran its own falsifying check — grepping all of `audit/` for `AskUserQuestion|approval|gate|delete|forget|auto-remove` — and found the sole `AskUserQuestion` in audit is a scope question at `SKILL.md:53`. Zero deletion gates. Orchestrator re-verified `apply-fixes.md:101`, `SKILL.md:186`, `SKILL.md:214`, and `CLAUDE.md:744` directly.

### 8. A skill instructs the inverse of what its own scanner enforces, breaking its convergence loop

`check_h2_case.py:178-183` emits "uses title case; project convention is sentence case" with fix hint "Rewrite as sentence case". `skill-linter/SKILL.md:92` states the exact inverse: "flags sentence-case H2 headings (`## Worked example`) and proposes the title-case rewrite (`## Worked Example`)", calling it "The H2 title-case rule".

This is load-bearing, not cosmetic. `skill-linter/SKILL.md:201` auto-applies `h2_heading_case` as a mechanical fix, and `:221-224` iterates until two consecutive passes find nothing. An agent following line 92 title-cases headings the scanner immediately re-flags — **the loop cannot converge.**

The same file states the correct direction at `:226` ("title case is the defect… that check was inverted once"), and `skill-authoring-checklist.md:62` warns "Do not run the conversion in reverse". So the skill contradicts itself and the shared reference already anticipated this exact regression.

The reviewer ran the committed regression suite as its falsifying check — 14 tests, OK, with `test_flags_title_case_h2_in_a_file` asserting `## When To Invoke` yields a finding. The script is right; line 92 is the stale claim. **Do not "fix" the scanner.**

### 9. Two documentation claims about the scripts are false

- **A named constant that does not exist.** `skill-authoring-checks.md:78` says stopwords "are defined once in `TITLE_CASE_STOPWORDS` (`scripts/check_h2_case.py`)". Grep across `.claude/` returns only that doc line. The script has `PROPER_NOUNS` and `TITLE_CASE_WORD_RE` and no stopword list. A maintainer told to extend it edits nothing.
- **A scanner count that is one short.** `skill-llm-council/SKILL.md:137` says "`skill-linter`'s five deterministic scripts" and lists five; skill-linter runs six. The omitted one is `check_internal_refs.py`, which emits `stale_step_reference` — the only scanner that catches a cross-reference orphaned by step renumbering, which is precisely what a council rewriting procedure steps produces. The reviewer verified the script accepts the council's argument form.

### 10. Clean, and reported as such

The Script reviewer confirmed by execution rather than reading: every invoked script exists, every documented flag is accepted (`--single-file`, `--verify`, `--list-checks`), and the five data files the scripts load match `CLAUDE.md:803`. The Contrarian likewise reported the lint→cleanup `hot_thread_spent` seam holds, because `cleanup` runs `check_wiki.py` itself rather than depending on a lint report that may not exist — which matters, since `2-outputs/lint/` and `2-outputs/consistency/` are both empty right now, so a report-reading design would have silently no-opped.

### 11. The schema is behind the skills in four places — and the fix direction is the opposite of the obvious one

Council 2's Best-Practices-Compliance member returned the run's most consequential framing: **all four of its cross-file findings are schema staleness, not skill drift. The skills are right; `CLAUDE.md` is behind.** Anyone who "fixed" the skills to match these paragraphs would delete working behaviour — a severity mapping, two re-stamp paths, two verification bindings, and four read-only memory reads.

Verified by the orchestrator:

- **`CLAUDE.md:762` contradicts `CLAUDE.md:666`.** `:762` says multi-skill memory is "Read by every write skill at the start of every operation"; `:666` says "Read-only skills are included because scope and framing corrections to those skills also need somewhere to live". All four read-only skills implement the broader rule. The schema disagrees with itself and the skills follow the correct half.
- **`CLAUDE.md:803` enumerates five shared references; nine exist.** Omitted: `self-report.md` (cited by 13 skills), `relationship-sweep.md`, `skill-authoring-checklist.md`, `skill-authoring-checks.md`. The same sentence calls `verification.md` "the ingest-family verification spec run by `ingest` (Step 8) and `query`", but `CLAUDE.md:670` itself binds four skills, adding `synthesis` Step 8 and `supersede` Step 7.
- **`CLAUDE.md:510` misattributes a severity vocabulary.** It credits skill-facing `error / warning / suggestion` to "`consistency`'s judgment-drift packet", which emits no severity at all; consistency's canonical statement is that the sole carrier is the `ai_writing_tells` check. The reviewer ran the falsifying grep and found two hits, both saying the opposite.
- **`CLAUDE.md:544` under-enumerates the stamp writers** — "`lint`, `ingest`, `audit`" — while `:559` itself assigns re-stamping to `supersede` and `forget`. Two re-stamping skills sit outside the "never hand-compute a hash" rule that is supposed to bind them.

This member also re-checked the audit `result:` contract the brief flagged as worth re-verifying and reported it **currently correct** across `CLAUDE.md:682-684`, `lint`, `consistency`, `audit`, and `cleanup` — the negative result the brief asked for.

### 12. Any description fix must trade characters out, not append

`skill-linter`'s description sits at 1018/1024 chars and `ingest` at 1010/1024. Several members proposed appending disclaimers to descriptions; on those two skills an append silently breaks frontmatter validation. Recorded as a constraint on the whole proposal set.

## Peer review (Step 3)

The user directed that the protocol not be scaled down after an initial cost-based reduction. That call is vindicated by what this step produced — none of it was reachable from the Step-2 responses alone.

**A finding was killed.** Council 1's Expansionist claimed `skill-linter/SKILL.md:190` declines a `result:` gate field on a false premise, citing `cleanup/SKILL.md:55` as reading it. Two peer reviewers independently found the referent inverted: `cleanup:52-57` reads `result:` for `lint`, `consistency` and `audit` only, and `:57`/`:213` explicitly place `skill-linter` among the subject-bearing kinds with **no** kept-latest and no gate read. **`skill-linter:190` is correct and the finding is wrong.** It never reached this report's findings list, but it was in the orchestrator's chat summary and is retracted here.

**A severity was overstated.** Two reviewers confirmed the `locator_page_mismatch` deadlock mechanically — `error` severity, absent from `STANDING_NONBLOCKING`, both skills naming audit as resolver — but corrected its characterization: `audit/SKILL.md:82` **stops and puts the findings to the user** rather than failing silently. So it is an unreachable-clause bug with a human escape, not a hard deadlock. Real, and one notch less severe than Finding 1 states.

**Two findings no council member reached:**

- **A fifth agent-writable data file, missing from both carve-out lists.** `synonym-ignore.md` is agent-writable per `CLAUDE.md:803` and written autonomously by `skill-linter/SKILL.md:73,200` — yet it is absent from `AGENT_DATA_FILES` (`check_consistency.py:1650-1656`) *and* from audit's Step 2 exclusion pathspec. So any `skill-linter` run stales audit exactly as the `pagination-map.md` path in Finding 4 does. The Contrarian found one instance of this class and stopped; the class has at least two members.
- **Three incompatible `result:` vocabularies across one seam.** `clean | blocking` (lint), `clean | findings | blocked` (consistency), `settled | interim | blocked` (audit) — all parsed by consumers at the same hand-off.

**The set's shared blind spot.** Every Step-2 member reasoned from `SKILL.md` prose; only the Executor opened the script that actually decides severity. Prose seams are cheap to find and the registry is authoritative — which is why the one script-grounded response was judged strongest by all three reviewers so far.

**A second finding dissolved.** The First-Principles member's claim that `query` is a third page-authoring skill contradicting `CLAUDE.md:764`'s "read-only" list does not survive: `CLAUDE.md:671` already qualifies it as "a plain `query` with no promotion". The schema is consistent; the reviewer read one half of it.

**Convergence was correlated, not corroborative.** The sharpest peer-review result. Three Step-2 members independently indicted `audit` — and the reviewer assigned to the correlation angle judged that this happened because `audit/SKILL.md` is the longest and most cross-referencing file in the suite, not because three probes converged on one defect. Each named a *different* mechanism. So "audit is the fragile hub" gains **zero** independent support from the three-way agreement, even though the three specific findings each stand on their own evidence. Recorded because the read-access grant made exactly this failure mode likely, and the naive reading of Findings 1, 4, 5 and 7 together is the one the reviewer rules out.

**Nobody costed a fix, and the obvious fixes are traps.** The fixability reviewer found that most proposed fixes land in `CLAUDE.md` or the shared scripts — which `consistency` and `skill-linter` may only *propose*, never apply. So this proposal set is largely not autonomously actionable by the suite that produced it. Two specific traps:

- **Widening `STANDING_NONBLOCKING` to fix the deadlock would silently relax every other consumer**, because `lint/SKILL.md:81` has the same set drive the script's exit code. A real fix needs a third severity class and touches the script, `lint`, `audit` and `CLAUDE.md` together.
- **Widening audit's Step 2 pathspec to fix the staleness loop blinds the gate to genuine hand-edits** — the condition the gate exists to catch.

The one cheap, purely additive fix in the whole set is the stdout guard of Finding 3.

**A third missed seam.** `cleanup/SKILL.md` never names `query`, `brief`, `compare`, `reflect` or synthesis outputs, so those fall into the unprotected aged-out sweep while `log.md` and synthesis's promotion path still link to them.

**An unvalidated trust root, flagged as the thing all five missed.** `pagination-map.md` is written by `ingest` on human footer-confirmation, is never grown by `audit`, and is exempt from consistency's content scan — so the one data file no check validates is the ground truth that `locator_page_mismatch` fires against. A wrong map yields confidently-wrong Criticals. That is a correctness seam, and the set found only control-flow ones.

## Repair order — one fix gates all the others

Council 2's fixability reviewer found a dependency that changes how this whole set should be worked, and it is the most actionable result of the run.

**Fix the `h2_heading_case` inversion first, by hand, before anything else.** `skill-linter` auto-applies that check and loops until two consecutive passes are clean (`SKILL.md:201`, `:221-224`). While `SKILL.md:92` states the inverse of what the scanner enforces, that loop **cannot converge and actively corrupts H2 headings across all 14 skills**. Every other fix in this report would be applied *through* that loop. So the ordering is not a preference: applying anything else first runs it through a mechanism that is currently mis-transforming the files it touches.

**And fixing `:92` alone is insufficient.** `multi-skill/references/skill-authoring-checks.md:78` repeats the same inversion — its "stopwords stay lowercase mid-heading" framing is a *title-case* concept — and names the phantom `TITLE_CASE_STOPWORDS` constant in the same sentence. The rubric and the skill must be corrected together, then the regression suite run.

**One proposed fix would cause a storm.** The Structure reviewer's proposal to merge `dependent-cascade.md`, `inbound-reference-discovery.md` and `quarantine-path-convention.md` into one file renames paths cited inline across the suite — inside the one folder `check_structure.py` cannot validate (Finding 2, where it exits 0 on failure). Non-atomic application yields a broken-reference storm that no scanner would catch. This proposal should be declined or done as a single atomic change with manual verification.

## Council conflict for the meta-chair

The two councils disagree on repair *direction* for the same file, and it is a genuine conflict rather than a merge:

- **Council 2's Best-Practices member:** the schema is behind the skills. `CLAUDE.md` should be corrected to describe what the skills already do, and "fixing" the skills to match the schema would delete working behaviour.
- **Council 2's Adversarial member:** `CLAUDE.md:744` should be *extended* to gate a deletion that `audit/SKILL.md` does not currently gate — i.e. the schema should lead and the skill should follow.

Both cannot be applied as stated. The reconciliation is that they concern different paragraphs and different kinds of gap — one is documentation lagging implementation, the other is a safety rule that never covered a case — but a maintainer applying them in sequence without noticing would first make the schema descriptive of current behaviour, then be unable to see that the deletion gap is a gap. Recorded as an explicit dissent to preserve rather than a conflict to split.

## Chair synthesis — Council 1

**The chair overrode its own majority, which is what a chair is for.** Four of five peer reviewers ranked the Executor's `locator_page_mismatch` deadlock strongest. The chair adopted the lone dissenting reviewer's ranking instead, and the reasoning holds: the deadlock is *textual* and has a human escape (`audit:82` stops and asks the user), whereas the missing stdout guard is a **silent** failure on a **destructive** path with no escape and no detector. Silent-and-destructive outranks loud-and-blocked.

**It also reversed a finding this report had recorded.** The Contrarian proposed adding `pagination-map.md` to audit's Step 2 exclusion pathspec, and Finding 4 above carried that uncorrected. The chair rejected it, and verification confirms: `audit/SKILL.md:224` names exactly three agent-writable data files — `hyphenation-lists.md`, `unlinked-mention-ignore.md`, `alias-detect-exempt.md` — and `pagination-map.md` is not among them. Audit reads that file but never maintains it, so a genuine hand-edit there **should** stale the gate. Excluding it would blind the trust root that peer review separately flagged as unvalidated.

The real finding is narrower and survives: **the carve-out lists disagree**, and `synonym-ignore.md` is genuinely missing from both `AGENT_DATA_FILES` and audit's pathspec while being written autonomously by `skill-linter`. That one is the fix; `pagination-map.md`'s exclusion is correct as it stands and needs only a one-line note at `audit:88` saying *why* the sets differ, so the next editor does not "fix" it by widening.

**Council 1's consolidated change-set**, as the chair ranked it:

| | Change | Weight |
|---|---|---|
| A | Propagate the stdout guard to `cleanup/SKILL.md:139,199`, `forget:122`, `ingest:124`. Purely additive, relaxes no consumer. Highest priority — `cleanup` 8.2b confirms a destructive prune by checking a finding disappeared, and a crash reads as success. | load-bearing |
| B | Add `synonym-ignore.md` to `AGENT_DATA_FILES` and audit's Step 2 pathspec. | load-bearing |
| C | One-line note at `audit:88` explaining why its 3-file exclusion differs from consistency's 4. | load-bearing |
| D | Do **not** widen `STANDING_NONBLOCKING` — `lint:81` has the same set drive the script's exit code. Instead amend `lint:47` and `audit:39` to stop naming audit as resolver of a finding that blocks audit's own entry, routing it to the user as `audit:82` already does. | load-bearing |
| E | Give `audit:104` the same-minute collision suffix its siblings have. | trivial |
| F | Cap audit's Step 9→7 fold-back (lint caps at 3, consistency at 6, audit at nothing). | load-bearing |

**Chair's confidence: high.** Its stated remaining uncertainty: nobody costed a fix; `cleanup` protects no `query`/`brief`/`compare`/`reflect`/`synthesis` output; and whether the unvalidated `pagination-map.md` trust root warrants a validator is unresolved.

*One orchestrator counter-correction:* the chair states the stdout guard exists in `lint` only and that the Expansionist under-counted. It is present in `lint` **and** `skill-linter`. This does not change the change-set — `cleanup`, `forget` and `ingest` lack it either way — but the chair's incidental claim that `lint:55`'s "consistency already applies this" is unverified prose does appear correct, and is worth checking separately.

## Chair synthesis — Council 2

The chair tiered its set and rejected one proposal outright.

**Tier 0 (by hand, before any loop):** the `h2_heading_case` inversion at `skill-linter/SKILL.md:92` and `:87`, plus `multi-skill/references/skill-authoring-checks.md:72` — which carries the same inversion and **contradicts its own table at `:76`** — and `:78`'s phantom `TITLE_CASE_STOPWORDS`. **Tier 1 (safety):** add the `cmp -s` byte-identity check at `apply-fixes.md:99`. **Tier 2:** the three broken inline refs; `skill-llm-council:137`'s five-of-six scanner count. **Tier 3 (trivial):** the four `CLAUDE.md` staleness items, `skill-linter:226`'s reference offload, and the description disclaimers within the char ceilings. **Rejected:** the shared-reference merge.

**Its sharpest move was an error catch on its own strongest member.** Council 2's Best-Practices reviewer had delivered a blanket rule — "all of this is schema staleness; the skills are right." The chair judged that false *as policy*, with the h2 inversion as the standing counterexample: there the doc is wrong and the script is right. The direction of repair is **per-item, not policy**. Applied per-item the four `CLAUDE.md` items still resolve the reviewer's way, so **the conclusion survives and the rule does not** — a distinction worth more than either finding.

It also preserved the Adversarial member's residue after the refutation, reclassified: `audit` is the only deletion-capable skill absent from `CLAUDE.md:744`'s enumeration. Not a safety hole, since the guards exist — a **discoverability** defect, because the next author reading `:744` will not know to check audit's.

## Meta-chair reconciliation

### A measurement that corrects both chairs and five peer reviewers

Chair 2 named an untested assumption and said to settle it before re-running. Settled: **`check_h2_case.py` across all 14 skills returns zero `h2_heading_case` findings.**

The headings are currently correct. So the inversion is **latent, not active**. Chair 2 called it "active corruption, not drift" and "a loop that currently corrupts headings across all 14 skills"; all five Council 2 peer reviewers ranked it first on that framing, one calling it "the only file-corrupting defect here." **The measurement refutes all six.** What is true: the prose is inverted, the script is right, nothing is damaged, and the hazard is prospective — an agent following `:92` would title-case correct headings, which the scanner would then flag, and the two-clean-passes loop would oscillate rather than converge.

*Flagged as a meta-chair addition:* no council member or chair produced this; it is the orchestrator's own check, and it is the single reason the final ranking differs from both chairs'.

### Reconciling the two rankings

The chairs disagreed on what comes first. Chair 1 ranked the stdout guard above everything, overriding its own majority. Chair 2 put the h2 inversion in Tier 0 on the "gates every other fix" argument.

**Chair 1's ranking wins, and the measurement is why.** Chair 2's ordering rested entirely on the loop actively corrupting files as it ran; with blast radius zero, that argument dissolves and the h2 fix becomes important-but-not-urgent. Chair 1's stdout guard, meanwhile, is what it always was: a **silent** failure on a **destructive** path, with no escape and no detector, and the only purely additive fix in the set. Silent-and-destructive outranks latent-and-loud.

### Final ranked proposal set

Every item traces to a chair line or is flagged as a meta-chair addition. **Nothing here was applied.**

| # | Proposal | Traces to | Weight |
|---|---|---|---|
| 1 | Propagate the stdout guard to `cleanup/SKILL.md:139` and `:199`, `forget:122`, `ingest:124`. `cleanup` 8.2b confirms a destructive prune by checking a finding disappeared; a crashed run prints nothing, which reads as success. Purely additive. | Chair 1 change A | load-bearing |
| 2 | Add the `cmp -s` byte-identity check at `audit/references/apply-fixes.md:99`, before unlinking the original, per `quarantine-path-convention.md:11-16`. | Chair 2 Tier 1 | load-bearing |
| 3 | Correct the h2 inversion in all four places: `skill-linter/SKILL.md:92`, `:87`, `skill-authoring-checks.md:72`, and `:78`'s phantom constant. Latent, not active — but it must be fixed before any skill-linter loop is trusted. | Chair 2 Tier 0, re-ranked by the measurement above | load-bearing |
| 4 | Add `synonym-ignore.md` to `AGENT_DATA_FILES` and audit's Step 2 pathspec. Do **not** add `pagination-map.md` — `audit:224` shows audit never maintains it, so a hand-edit there should stale the gate. | Chair 1 change B | load-bearing |
| 5 | Investigate why `shared_reference_integrity` does not already catch the misplaced `synonym-ignore.md`. **The enforcer is the seam, not the instances** — Chair 2 called this the most valuable item in the whole council, and I agree. | Chair 2, from peer review | load-bearing |
| 6 | Stop naming `audit` as resolver of `locator_page_mismatch` at `lint:47` and `audit:39`; route to the user, as `audit:82` already does. Do **not** widen `STANDING_NONBLOCKING` — `lint:81` has the same set drive the exit code. | Chair 1 change D | load-bearing |
| 7 | Give `check_musts.py` and `check_kwargs.py` tests. Their absence is the mechanism by which the h2 inversion survived. | Chair 2, from peer review | load-bearing |
| 8 | Cap audit's Step 9→7 fold-back; add the same-minute collision suffix at `audit:104`; one-line note at `audit:88` on why the carve-out sets differ. | Chair 1 changes C, E, F | mixed |
| 9 | Fix the three broken inline refs; correct `skill-llm-council:137`'s scanner count to six. | Chair 2 Tier 2 | load-bearing |
| 10 | The four `CLAUDE.md` staleness items — applied **per-item**, not under a blanket rule. Add `audit` to `:744`'s enumeration as a discoverability fix. | Chair 2 Tier 3 + preserved dissent | trivial |
| 11 | Description disclaimers for the query/brief and consistency/skill-linter collisions — trading characters out, not appending (`skill-linter` 1018/1024, `ingest` 1012/1024). | Council 2 Description & Trigger | trivial |

**Rejected:** merging the three shared cascade references. It renames paths cited inline across the suite, inside the one folder `check_structure.py` cannot validate, so a non-atomic application produces a broken-reference storm no scanner would catch. Both the fixability reviewer and Chair 2 rejected it independently.

**Open, unowned:** concurrent writes by `skill-linter` and `skill-llm-council` into one folder; whether `cleanup`'s preserve-folder sub-mode can prune the copy audit's merge depends on; whether the unvalidated `pagination-map.md` trust root warrants a validator; and that `cleanup` protects no `query`/`brief`/`compare`/`reflect`/`synthesis` output.

## Self-report

- **The brief carried a false count into all ten prompts.** It said 15 skills; the repo's own tooling says 14. → upgrade: compute every quantity in a brief from the repo before writing it, and state the command used.
- **The orchestrator's own verification was wrong in the same direction as the claim it was checking.** The exit-code check piped through `head`, so `$?` was `head`'s. A verification that can only confirm is not a verification. → upgrade: when checking an exit code, never pipe; capture status directly.
- **The headline finding was the one that most needed an adversary and nearly did not get one.** The safety claim was recorded as the run's most serious result and survived until a reviewer was pointed at it specifically. → upgrade: assign a dedicated refuter to the single highest-severity finding of any run, before it is written up rather than after.
- **Six independent agents propagated an unmeasured premise.** Two chairs and five peer reviewers all ranked the h2 inversion first on "active corruption", which one command disproved. Nobody ran it. → upgrade: any severity claim resting on a measurable blast radius must carry the measurement, exactly as this skill's own memory already requires for counts.
- **The run was scaled down for cost and the user had to override it.** That reduction would have skipped peer review, which killed two findings, refuted the headline, and produced the run's most valuable item. → upgrade: when cost pressure and protocol integrity conflict, surface the trade-off as a decision rather than resolving it silently toward the cheaper option.

## Self-report

*Pending — written after the run completes.*
