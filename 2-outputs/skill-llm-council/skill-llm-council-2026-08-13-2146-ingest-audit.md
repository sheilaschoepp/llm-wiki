---
type: skill-llm-council-report
date: 2026-08-13
target: "ingest + audit (reviewed as a pair)"
councils: 2
advisors: 10
peer_reviews: 10
chairs: 2
refuters: 6
applied: 7
refuted: 5
proposals: 12
---

# Skill LLM council — ingest + audit — 2026-08-13-2146

## Scope deviation (stated up front)

The skill reviews **one** skill per run. The user asked for both `ingest` and `audit` in one call, and the review question was explicitly the boundary between them — the case where the skill's own guidance says a skill reviewed in isolation hides the defect ("a drifted shared boundary, an inconsistent hand-off"). Both folders sit under `.claude/skills/`, so the write-scope safety property held. Recorded as a deliberate deviation, not an oversight.

Second deviation: the environment offers no Read/Glob/Grep-only agent type. All subagents ran as `Explore` (no Edit/Write/NotebookEdit) plus an explicit no-write instruction, rather than the toolset-enforced read-only the protocol specifies.

## Task brief

- **Purpose.** `ingest` turns one raw source into a source page plus the concept/entity pages it supports; `audit` is the wiki's quality pass. They had just been restructured to divide verification: ingest certifies exactly the claims it writes against the raw it has open — three questions per claim (is the locator right, does the source really say this, is the claim attached to the source that states it) — through independent refuters, and sets each page's status including `verified`. Audit became the whole-page judgement pass and re-opens a raw only on cause.
- **Good-version criteria.** The division is complete (no duty falls between them, none done twice); each skill runnable standalone; ingest's self-certification guarded so a wrong `verified` is not cheap to produce; audit still catches what ingest cannot see.
- **Binding rules.** CLAUDE.md; Anthropic skill-authoring best practices; `a-archive/style/ai-writing-tells.md`; the shared `verification.md` spec.
- **Useful disagreement.** Whether the split holds; whether either skill has a gap the other assumes it covers; whether ingest self-certifying is adequately guarded.
- **Known-wrong (structural baseline).** `ingest/SKILL.md` over the 6500-word body budget (6764) — pre-existing. All other deterministic scanners clean on both skills. No prior `skill-linter` report existed, so the five scanners were run for the baseline.

## Rosters

**Council 1 — cognitive lenses (fixed):** Contrarian, First-Principles Thinker, Expansionist, Outsider, Executor.

**Council 2 — specialists (composed).** Core three: Description & Trigger, Structure & Token-Economy, Best-Practices-Compliance. Selectable two, by the risk surface:
- **Adversarial Failure-Mode** — mandatory; both skills act autonomously and destructively (ingest overwrites pages, quarantines attachments, stamps `verified`; audit auto-applies splits, merges, rewrites).
- **Schema-Compliance** — both write and maintain the wiki.

Dropped for the two-slot limit, in the registry's priority order: Source-Fidelity (ingest reads raw sources), Prompt-Engineering (both spawn refuters), Instruction-Clarity (branching multi-step). `Script & Python-Quality` not indicated — neither skill bundles `scripts/`.

## Divergence check

Both councils diverged genuinely — distinct findings per role, not five rewordings of one critique. Neither council was flagged low-confidence, and neither fell below the advisor quorum. All 10 advisors and all 10 peer reviews returned.

## Outcome summary

| | Count |
|---|---|
| Mechanical edits applied (no refuter required) | 6 |
| Load-bearing edits sent to refuters | 6 |
| — held, applied | 1 |
| — refuted, demoted to `[needs-review]` | 5 |
| Cross-file proposals (never auto-applied) | 12 |
| Held for the user (chair flagged medium confidence) | 1 |

**Five of six load-bearing edits were refuted.** This is a documented revisit signal (councils over-reaching) and is recorded in the skill's memory file.

## Applied — mechanical (verified against the registry and filesystem, no refuter required)

1. `audit/references/verify-and-set-status.md` — `verified_anchor_unaudited` called "Critical" twice → **Warning**. Registry says `warning`; audit Step 1 treats a non-standing Critical as blocking, so audit would have hard-stopped on an anchor change it had just legitimately made. *Drift introduced by the restructure.*
2. `audit/references/apply-fixes.md` — the two agent-writable data files pointed at `.claude/skills/lint/` → `.claude/skills/multi-skill/`, both named. *Pre-existing.*
3. `audit/references/verification-spec.md` — coverage gate justified itself with "audit needs it more, because audit is what writes the `verified` stamp" → rewritten; ingest normally writes it now. *Drift introduced by the restructure.*
4. `audit/SKILL.md` — "finalized in Step 9" → **Step 10** (prose). Step 9 is the confirming lint. *Pre-existing.*
5. `audit/SKILL.md` — same fix in the report template. *Pre-existing.*
6. `ingest/SKILL.md` — `body_hash.py` given its full invocation path. *Trivial.*

## Applied — load-bearing, refuter verdict `holds`

7. `ingest/SKILL.md` Step 8, "**Set each page's status**" bullet — ingest now runs `check_wiki.py` and scopes its JSON to the page being stamped, satisfying Setting Status **condition 3**, which it previously asserted with no step for it. `check_wiki` appeared **zero times** anywhere in `ingest/`, while the spec says "`ingest` normally stamps" — the skill most likely to promote a page was the one skill with no step executing the structural gate, and nothing in an ingest run triggers `lint` (lint is separately invoked; a clean lint report is a precondition *of audit*).

   The refuter volunteered a refinement that was incorporated: synthesis's version of the same call parses the JSON to filter by `file` and warns that a freshly written page **absent** from the whole-tree output was not scanned at all rather than found clean. That caveat is now in the edit.

## Refuted — demoted to `[needs-review]`, not applied

Each was killed by an independent refuter reading its own ground truth.

**R1. Name the refuter tier inline in ingest Step 8.** *(Council 2 chair ranked this "the cheapest high-value edit in Tier 2"; it was the one finding that rescued the council's lowest-ranked advisor.)*
Refuted: the premise fails against Step 8's own first sentence — "Run all three from the shared spec … which defines each in full" — and the report template demands a tier breakdown unproducible without opening the spec. The edit would contradict ingest's own Conventions ("this skill cites `CLAUDE.md` rather than copying (copying drifts) … one canonical copy") and CLAUDE.md ("defined once, with the full mechanics"; "one canonical place per rule"). Worse, the proposed gloss is **lossier than the original**: it drops the Tier-3 cold-recompute discipline (the guard against certifying a distortion) and "agreement certifies; a split does not", and compresses Tier 1's three-part test into "a low-stakes single-locator fact", which fits most first-read source-page bullets — a downgrade path with no distortion guard.

**R2. Sample the certifier (a sixth `partial` fact-check cause).** *(Both chairs ranked this Tier 1; Council 1's chair built it by synthesizing two advisors' competing remedies.)*
Refuted on three grounds. (a) The instrument already exists: `full` mode is defined as "use it … when a batch was certified by a run you have reason to distrust, or as a periodic deep-confirmation pass." (b) Sampling would **weaken** the model — `verification-spec.md` rejects the inference twice in its own words ("where it applies, it applies in full, with no sampling shortcut"; "A single correct sample does not certify the rest … a mis-located citation hides behind a good sibling"), so "a sample that holds is the recorded evidence for the skip" downgrades the skip's basis from a per-claim guarantee to a per-run inference the spec says does not follow. (c) **Unimplementable:** audit keeps no ledger of which runs a prior audit sampled, and claims carry no run provenance — a page is certified "one source at a time" across several runs, so audit cannot attribute a claim to the run that certified it. The unit the edit indexes on is not recoverable from the wiki. *(No council member caught (c).)*

**R3. Make ingest's Limits reach rule conditional.**
Refuted: the conditional form is sound only **inside the Setting Status frame** it was lifted from. Unscoped in Limits, "otherwise mark `*[unverified]*`" over-fires on pages headed for `draft`, contradicting CLAUDE.md → Bullet markers ("Not used on `draft` pages, where the page status already means something on the page is unchecked"). The free disjunction plus the load-bearing prohibition ("never certified on the strength of the page's other citations") is the correct shape for a limit statement. The bad case is already closed by Setting Status condition 2, and CLAUDE.md confirms the failure mode is "a full-page demotion (safe), never a silently-unverified claim."

**R4. Ingest confirms the entering `verified_hash` before inheriting prior certification.** *(Both chairs called this the single highest-value edit in the set. The orchestrator endorsed it to the user twice before the verdict landed.)*
Refuted on executability. The three factual claims are true — `body_hash.py` appears once in ingest, condition 2 does say "confirm that before relying on it", audit does have the mirror check — **and that is not enough**. `body_hash.py` hashes the file **on disk**; by Step 8, Steps 4–7 have already rewritten those pages, so "the page as it entered this run" no longer exists and the edit supplies no way to reconstruct it (no `git show HEAD:{page}`, no entering-hash capture at Step 1). Taken literally against the on-disk file it misfires on exactly the population Step 8 governs: every reingest that edited a `verified` page mismatches, because the run's own writes moved the hash — voiding prior certification precisely where ingest's Conventions say to rely on it. Audit's mirror check is sound only because it gates a **skip** on a page audit has not edited; ingest's Step 8 population is the pages it just wrote. The "not rolled into a fresh stamp" remedy also has no mechanism: `verified_hash` is the SHA of the whole unmarked body, so the only way to exclude a line is the `*[unverified]*` mask — which would hide the suspect content behind a marker on a still-`verified` page.

**R5. Audit reads the authoring runs' hand-off records.** *(Two advisors headlined this; three peer reviewers independently confirmed the zero-reference finding.)*
Refuted: the factual claim is true — zero references to `2-outputs/ingest` anywhere in `audit/` — but the edit contradicts a stated safety rule. `apply-fixes.md`: "**Never inherit a finding from a prior report.** Re-derive it, or drop it. A finding copied forward carries the earlier run's errors with laundered authority." And audit's Limits: a page-level judgement is grounded in the pages themselves, "never in recollection or a prior report's say-so." The hand-off items are exactly page-level judgements. The lint analogy launders the authority: lint's Warnings are deterministic mechanical detections, while the spec calls the page self-check "a light read … run without refuters and non-blocking" — yet Step 1's rule would make an item audit's own read did not re-notice a mandatory fix. Separately, audit's Step 4 already asks these five questions over **every** page, and two of the three named channels (query's `Promotion verification`, synthesis's and supersede's log shapes) have no `Handed to audit` field defined at all.

## Held for the user — not applied

**H1. The Step 5 / Step 7 / Verification-Model edit-ownership contradiction (`audit/SKILL.md`).** Real and blocking: Step 5 says "Apply the detection-time content worklist … before fact-checking it", the Verification Model says every content edit "is applied in Step 7", and Step 7 says "This step applies every content edit." Council 1's chair established this is a **three-way** disagreement, not two-way — one advisor claimed `apply-fixes.md` forbids the front-load, but it in fact *endorses* it.

Its proposed reconciliation partitions by whether a finding turns on truth: lint's authored tier needs no raw and front-loads at Step 5 to demote pages into fact-check scope; Step 4's truth-turning findings travel to Step 5 as *cause* and their edits land in Step 7. That is the only reading found that keeps both `apply-fixes.md` and `semantic-checks.md` true. **The chair flagged it as its own construction at medium confidence** — no advisor proposed it, and it has not been walked through a fanned-out run or an `audit → lint → audit` cycle. Not applied on a chair's say-so.

## Cross-file proposals — never auto-applied

Each names the exact target and edit.

1. **`CLAUDE.md` → the fact-check cause list** enumerates **four** causes; `audit/SKILL.md` now states **five** (the fifth: "every locator lint flags"). Amend the schema upward — the fifth is real behaviour, and `locator_page_mismatch` cannot be settled without the raw. *Drift introduced by the restructure.* Three peer reviewers predicted an in-folder chair would drop this; it is preserved here for that reason.
2. **`multi-skill/references/verification.md`** — same four-cause list; same fix.
3. **`CLAUDE.md`: "`audit` acts on them … rather than stamping"** (mirrored twice in `verification.md`) contradicts audit's Step 8, which sets `verified` and writes `verified_hash:`. Reword to "rather than settling the page-level question with a stamp; it still sets and re-stamps status on the claims it checks." *Drift introduced by the restructure.*
4. **The refuter-split disposition contradicts across three files.** `verification-spec.md` says a split sets the page `needs-update` unconditionally; `verification.md` qualifies it to pages being promoted; `CLAUDE.md` → Bullet markers says the marker rides and the page stays `verified`. The **promotion branch** is genuinely unsettled and needs a decision, not an edit — see Open Questions.
5. **`lint/references/checks.md`** files `verified_anchor_unaudited` under the `#### Info` heading while its own prose calls it a Warning; audit Step 1 states "Info-tier findings are not audit's to action", so a reader triaging from the catalogue drops the check entirely. Move it to the Warning block. Also move `verified_hash_mismatch` out of the block whose lead says "neither lint nor audit auto-actions (so they sit at Info, not Warning)" — false for it.
6. **`multi-skill/scripts/check_wiki.py`** — four user-facing remediation strings still route certification work to audit alone: `'Run /audit to fact-check the marked claims and clear them.'` (2174), `'audit re-checks just these'` (2172), `'Run /audit and consider promoting to verified…'` (1907), `"let 'audit' re-verify"` (1695). Under the new division a reingest of the cited raw is often the correct route. *Found by peer review; no advisor read what the checks tell the user to do.*
7. **`multi-skill/references/verification.md` → Refuter mechanics** — a refuter that never returns (errors, never spawned, empty, budget exhausted) has **no defined disposition** and falls through as "nothing refuted it." Add: an un-run tier is not a pass; a run that cannot spawn refuters finishes every touched page at `draft`.
8. **Same file** — evidence is required of a **refutation** but not of a **hold**, and a hold is what writes `verified`. The report records it as the unfalsifiable token `all held`.
9. **Same file** — each refuter in a tier should get a **different access route into the raw**. The rule already exists in `apply-fixes.md`'s bullet-removal guard ("three passes over one blind spot are one pass") and is absent from the gate ingest runs.
10. **Same file** — batch a tier's refuters over claims from the same raw (three calls per raw, per-claim verdicts, never split a batch), the device `apply-fixes.md` already uses for its data-list quorum. Addresses the fan-out cost below.
11. **`lint/SKILL.md` description** — "Different from audit, which judges note quality and source support." After the restructure audit does not routinely judge source support.
12. **`cleanup/SKILL.md` description is 1345 characters** against the hard 1024 cap — a frontmatter failure outside the target pair, free to catch.

## What peer review surfaced that no advisor had

1. **`verification.md` is a four-caller contract, not ingest's file** — `query`'s promotion path, `synthesis` Step 8 and `supersede` Step 7 all run it, and all three finish at `draft` by design. Every advisor edit to that file was written and justified against ingest alone. Three reviewers found this independently. It is a gating requirement on proposals 7–10.
2. **The hand-off gap is symmetric; every proposed fix was asymmetric.** Synthesis and supersede route findings through the same unread channel. (Refuter R5 later showed the fix itself was wrong in kind.)
3. **Nobody costed the gate.** Tier 3 is the stated default, so an ingest pays dozens of refuter calls on top of 10–20 `AskUserQuestion` calls, with no cap or batching, while both files call the arrangement "nearly free". Raised independently by four reviewers. *Orchestrator note: this is not new total cost — the same quorum moved from audit to ingest — but it is now front-loaded into one run rather than amortized, and the "nearly free" wording conflates the raw being open (free) with the fan-out (not free).*
4. **Refuter correlation.** Three refuters are the same model, same orchestrator, same "default to refuted" prompt — correlated draws, not independent ones. `verification.md` names shared blind spot as the reason a same-assistant second pass fails, then answers it with same-model duplicates.
5. **`verified` carried two guarantees the restructure separated** — *claims certified* and *page judged* — and nothing records the second. See Open Questions.
6. **Nothing has ever run.** `1-wiki/` and `0-raw/` are empty. Every finding in this review is a textual inference about a system with zero execution history.

## Chair conflicts the meta-chair resolved

- **Audit's description budget.** Both chairs wanted a `skill-linter` boundary clause and both faced the 1024-char ceiling. Council 2's chair proposed paying by deleting "Claims arrive certified, so it re-opens a raw only on cause" — the one sentence encoding the new division. Council 1's chair paid from the preconditions sentence, pure internal mechanism no router matches on. **Council 1's ruling taken.** (Neither applied — see Not carried, below.)
- **Reconcile before deduplicating.** The token-economy advisor's headline lever was collapsing 3–5× restatements; two other advisors showed several of those copies disagree. Passed to both chairs as a constraint. Council 2's chair then found the concrete case: the printed→physical offset formula is stated one way in `audit/SKILL.md` and contradicted in `verification-spec.md`, which says that single-offset formula *breaks* on a restarting appendix.
- **A chair verification error, corrected.** Council 2's chair excluded the raw-angle-bracket finding after grepping `audit/SKILL.md` for `<` and finding none — but the finding was about `>`, which is present at both cited lines, and CLAUDE.md's rule names both characters. The finding is real but genuinely trivial (`> 0` does not read as an HTML tag), so it is recorded here at that weight rather than dropped.

## Not carried

- All rule-consolidation and relocation edits (Purpose trim, the "sections are not quotas" deletions, the Step 6 three-rules split, the `semantic-checks.md` 590-word bullet trim, the offset-rule merge, the audit Worked-example move, the `## Contents` additions). Held under the reconcile-before-dedupe constraint, and — after R1, R3 and R5 — under the stronger lesson that this pair's defects are not fixed by moving or copying rule text.
- The description edits (ingest scope wording and routing-out clause; audit's `skill-linter` boundary and `full` hook). Both descriptions sit within 12 characters of the hard cap, so each needs a displacement decision that is the user's call, not an autonomous edit.
- The advisor proposal to carry ingest's per-anchor certifications forward so audit skips *more* raw re-reads. Rejected on direction: it optimizes trust in a certification whose evidence nobody checks.
- One advisor's Step 4 hash-skip (skip per-page questions on a byte-identical page). Council 1's chair rejected it on direction and the meta-chair agrees: adding a hash-keyed skip to the one pass audit exists for, in the same change-set that admits the certifier is never sampled, is the wrong order of operations.

## Open questions for the user

1. **Can a page *being promoted* reach `verified` while carrying a masked claim?** Genuinely unsettled across `CLAUDE.md`, `verification.md` and `verification-spec.md`. Proposal 4 fixes the copy that is unconditionally wrong; it does not decide this.
2. **Should there be a second status axis recording that a page was judged as a page?** A peer reviewer identified this as the root of four separate findings — the hand-off gap, the provenance gap, the `*[tentative]*` backlog and the anchor seam all dissolve if a page records that audit judged it. It touches CLAUDE.md, lint, and every skill that reads status, so it is a design decision, not an edit.
3. **`*[tentative]*` has no clearing path and no surface.** It has no lint check at all, appears in no fact-check cause and no report section, and a fact-check does not clear it — so a `*[tentative]*` claim can sit on a `verified` page indefinitely with nothing surfacing the backlog.
4. **`full` mode has no cadence and no owner.** R2 established that `full` already *is* the instrument for testing a certifying run. What is missing is anything that generates the "reason to distrust" that triggers it.
5. **Run one real ingest.** Every finding here is textual. One ingest of one real paper would settle the fan-out question and the un-run-tier question better than another review pass.

## Sanity check

Structural: `check_structure`, `check_synonyms`, `check_musts`, `check_h2_case` — clean on `audit`; `ingest` carries only the pre-existing `body_over_length` (6817 words against 6500; was 6764 before this run, +53 from the applied condition-3 edit). `check_kwargs` not applicable (no `scripts/` in either skill). `check_internal_refs` clean on both. `check_consistency` clean (exit 0).

Semantic re-read: the one applied load-bearing edit was re-read in context against the task brief — it adds a pre-stamp gate, weakens no trigger, deletes no because-clause, and inverts no instruction. This is a self-consistency pass by the agent that applied it, not independent verification.

## Value over the `skill-linter` baseline

The five deterministic scanners returned one finding (a pre-existing word-count overage). This run produced 7 applied edits, 12 cross-file proposals, and 5 arguments-against that a single-context pass would have applied unchecked — including four edits that both chairs ranked in their top tier and that ground-truth checking killed.

## Self-report

- Five of six load-bearing edits were refuted, and four of those five were chair-ranked Tier 1 or "highest-value". The councils systematically over-proposed in one direction: adding local copies of rules whose canonical home is the shared spec. The peer-review round warned against collapsing duplicates before reconciling them; nobody warned against the inverse, which is what actually bit. → **upgrade:** the role prompts should carry an explicit prior against the fix-by-restatement pattern — before proposing a local copy of a shared rule, check whether the executing step already routes to the canonical spec, and whether the copy would be lossier than the original.
- The chair syntheses ranked edits by argued severity, and refuter verdicts correlated poorly with that ranking. → **upgrade:** the chair prompt should require, for each load-bearing edit, one sentence naming what would have to be true of the ground truth for the edit to be wrong — the same discipline the Critical-finding audit-assumption framing already imposes elsewhere.
- The orchestrator relayed two edits to the user as "the highest-value single edit" before their refuter verdicts landed, and both were later refuted. → **upgrade:** state a chair's ranking as a chair's ranking until the gate has run.
- One chair excluded a real finding on a mis-scoped grep (searched `<`, the finding was about `>`). → **upgrade:** where a chair excludes an advisor finding on a verification it performed itself, the meta-chair re-checks the exclusion, not just the inclusions.
