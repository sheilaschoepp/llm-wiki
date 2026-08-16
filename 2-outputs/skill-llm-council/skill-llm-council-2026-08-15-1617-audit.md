---
type: skill-llm-council
skill: audit
date: 2026-08-15
councils: 2
advisors: 10
peer_reviews: 10
chairs: 2
refuters: 10
edits_applied: 14
edits_demoted: 5
proposals: 7
---

# Skill LLM council — audit — 2026-08-15-1617

Deep review of `audit` as the primary target, with the rest of commit `5ee1be5` passed as related context. That commit ported lessons from the active `llm-wiki-mas` wiki's skill memory journals into this template. The user's framing was to review the changed set as one coherent unit rather than one skill in isolation.

## Target resolution and scope

Resolved target: `.claude/skills/audit/` (SKILL.md + four references). Audit took 5 of the 11 files the commit changed and is the skill the others couple to, so the remaining changed files — `lint/references/checks.md`, `consistency/references/checks.md` + `scripts/check_consistency.py` + tests, `ingest/references/attachments.md`, `multi-skill/references/verification.md`, `multi-skill/alias-detect-exempt.md`, and `CLAUDE.md` — were supplied as related context. Findings against those are surfaced as `[cross-file]` proposals, never auto-applied.

Git state at Step 1: clean (`git status --porcelain -- .claude/skills/audit` empty), so every prior version is git-recoverable.

## Deterministic baseline (Step 1)

No prior `skill-linter` report for audit existed, so the five scanners were run for a structural baseline:

- `check_structure.py` — **1 warning**: `body_over_length`, SKILL.md 7060 words against a 6500 budget.
- `check_synonyms.py`, `check_musts.py`, `check_h2_case.py` — clean.
- `check_kwargs.py` — not applicable (no `scripts/`).

## Rosters

**Council 1 — cognitive lenses (fixed):** Contrarian, First-Principles Thinker, Expansionist, Outsider, Executor.

**Council 2 — skill specialists (composed):**

| Role | Reason for selection |
|---|---|
| Description & Trigger | core specialist, always included |
| Structure & Token-Economy | core specialist, always included |
| Best-Practices-Compliance | core specialist, always included |
| Adversarial Failure-Mode | mandatory — audit auto-applies content fixes and sets page status |
| Schema-Compliance | audit writes and maintains the wiki |

Dropped for the two-slot limit, in the selection rule's priority order: Source-Fidelity (audit reads raws), Prompt-Engineering (audit spawns refuters), Instruction-Clarity (branching workflow). `Script & Python-Quality` not indicated — audit bundles no `scripts/`.

**Context grant.** Inlining was impractical (SKILL.md alone is ~7k words, plus four references, five sibling skills, and a 127KB CLAUDE.md), so advisors were given a bounded read grant to named files with read-only tools.

**Recorded deviation.** No available agent type offers an exact Read/Glob/Grep-only toolset. Advisors, chairs and refuters ran as `Explore` (no Edit/Write/NotebookEdit), with the no-edit rule also stated in every prompt and full-read instructions overriding its excerpt-by-default behaviour. The toolset rail is preserved; the exact tool list is not.

## Council health

Both councils reached full quorum: 5/5 advisors, 5/5 peer reviews, 1 chair each. **The divergence check passed clearly** — Council 1's lenses surfaced workflow, dependency and ordering failures; Council 2's specialists surfaced schema, compliance and description failures. No collapse onto a single critique, so neither council was flagged low-confidence and no edit was demoted on health grounds.

## What the councils found

Ten defects, every one independently verified by the orchestrator against the files or by executing the code:

| # | Defect | Severity |
|---|---|---|
| 1 | commit-at-milestones disarms the HEAD-keyed guards (`_git_show_head` diffs live HEAD; marker-clearing gates on "anchor already at git HEAD") | Critical |
| 2 | Step 8's `git diff <base>` had no bound `<base>`; after a milestone commit `git diff HEAD` returns empty, scoping the re-check to zero bullets | Critical |
| 3 | Step 5 batching read as one refuter per 25-claim batch, collapsing Tier 3 to Tier 1 | Critical |
| 4 | The contradiction closeout rule reversed `CLAUDE.md:377` and `verify-and-set-status.md:54` — 21 lines apart in one file | Critical |
| 5 | "Clear an unconfirmable `venue:`/`year:`" targets a `REQUIRED_FIELDS` key | Critical |
| 6 | `## Worked example` heading deleted by the commit, orphaning 444 words | Warning |
| 7 | `apply-fixes.md:51` still said "two agent-writable data files" | Warning |
| 8 | `verify-and-set-status.md:40` still said "the two agent-writable shared data files" | Warning |
| 9 | `semantic-checks.md` said "five questions", listed six | Warning |
| 10 | The mandated count-comment "beside the entry" voids the exemption (loader splits on `::`) | Warning |

A fifth incomplete-wiring site — the staged-valve clause at `SKILL.md:45` and `apply-fixes.md:73`, both naming only `unlinked-mention-ignore.md` — was surfaced by peer review, not by any advisor.

## Arbitrations

**"Two lint checks" vs "Three lint checks".** Both chairs independently ruled that the convergent advisor proposal was **wrong**. `ALIAS_DETECT_EXEMPT` is consumed inside `check_unlinked_page_mentions` itself, and `CLAUDE.md:801` says the file sits "behind the same check". `stale_alias_exempt` is a hygiene check *on* the data file, the analogue of `stale_mention_ignore`, which nobody counts. Ruling: **two checks, three data files**. Three of ten advisors had converged on the wrong edit; one advisor had it right; a peer reviewer caught it.

**Revert vs carve out.** Both chairs ruled **revert** for the disputed rules, on the ground that the commit ported backlog-burn-down tuning into a template whose `1-wiki/` ships empty — so the rules' own stated reasons cannot obtain — and that no prose carve-out can reach the deterministic backstop, which lives in `check_wiki.py`, a file audit is forbidden to edit. The refuters then narrowed this ruling substantially (below).

## Adversarial verification (Step 6)

Ten refuters, one per load-bearing edit. **Five verdicts came back `refuted`**, and the demotions materially improved the outcome.

| Edit | Verdict | Disposition |
|---|---|---|
| Revert the `## A single pass` section; restore `## Worked example` | holds | applied |
| Delete the contradiction closeout bullet | holds | applied (with the "Three rules" → "Two rules" follow-on it required) |
| Batching quorum fix | holds | applied |
| Dedup `verification-spec.md:19/21` | holds | applied (fan-out tail preserved, as the refuter required) |
| `apply-fixes.md:51` two-vs-three | refuted **as scoped** | applied in the larger form the refuter demanded |
| Revert the venue/year rule | refuted | **not applied** → proposal |
| Revert drop-the-quantifier | refuted | **not applied** → proposal |
| Crop certify/preserve asymmetry | refuted | **dropped entirely** |
| Revert the link-worklist bullet | refuted | **not applied** |
| Fold the enumeration bullet into pre-stamp checks | refuted (destination) | bullet kept in place; not moved |

Why each refutation mattered:

- **venue/year** — the shared spec's claim check explicitly covers "Metadata matches the raw source", so frontmatter is in scope; and `parse_frontmatter` stores `fm[key] = []` for a bare `venue:`, so "clear" read as *emptying* trips nothing. Deleting would have removed the only "do not state an unconfirmable value" rule for frontmatter.
- **drop-the-quantifier** — it is the only guidance anywhere for a repeatedly-failing count, and both council grounds misattributed: the rule spends the third permitted round rather than bypassing the cap, and `CLAUDE.md`'s "standalone" means *readable without the source paper*, not grammatically complete.
- **crop asymmetry** — would have gutted the fix it was attached to. `CLAUDE.md:159` *requires* the `Figure N` label inside every crop, which is precisely the crop-to-locator tie the council claimed was absent; and marking an already-verified claim `*[unverified]*` moves the hash and demotes the page.
- **link-worklist** — `apply-fixes.md:34` states that verification-neutral fixes on hash-matched `verified` pages are explicitly *not* in Step 5's scope. No collision existed; the bullet is the only ordering rule for a class Step 5 excludes.
- **enumeration bullet** — the KEEP call held (it ranges over *raws* and guards staleness, where the sibling rules range over *cells* and guard cherry-picking), but the destination list is scoped to "any rewritten body" and four hardcoded "three pre-stamp checks" references would have been left contradicting the file.

## Completed edits

All in-folder (`.claude/skills/audit/**`), applied autonomously.

Judgement edits:

1. `SKILL.md` — deleted `## A single pass is not the deliverable` (4 paragraphs, 263 words, containing run-to-completion and commit-at-milestones); restored `## Worked example` above the example prose.
2. `references/verify-and-set-status.md` — deleted the `**Disagreement is something to report…**` bullet; `Three rules` → `Two rules`.
3. `SKILL.md` — deleted the `**Batch the claims, and batch the refuters.**` paragraph (88 words).
4. `references/verification-spec.md` — added the corrected batching rule after the tiered-refuter-gate paragraph: whole batch to **each refuter in the tier**, three at the Tier-3 default; never split a batch across a tier's refuters; explicit per-claim verdict for every claim, a return that omits a claim means unread not held; dropped the undefined "concurrency cap".
5. `references/verification-spec.md` — collapsed the duplicated `**Name the defect shape…**` and `**A split is an explicit disagreement…**` paragraphs into a pointer at the paragraph that already cites the shared spec; preserved the audit-specific fan-out tail sentence verbatim.
6. `references/apply-fixes.md` — `two agent-writable data files` → `three`, keeping `Two lint checks`, and noting that the last two files both feed `unlinked_page_mention`; `Both are data … both are loaded` → `All three`; `Both files are version-controlled` → `All three files`.
7. `references/apply-fixes.md` — added the third data-file bullet: the ignore-list-versus-exemption distinction, the `{page-stem} :: {display form}` format, the escalation trigger, the per-form-not-per-page rule, and the count-on-its-own-line-above rule with the loader reason.
8. `references/apply-fixes.md` — added the exemption's refuter question to the quorum list.
9. `SKILL.md` and `references/apply-fixes.md` — staged-valve clause now names `alias-detect-exempt.md` alongside `unlinked-mention-ignore.md`.
10. `references/verify-and-set-status.md` — `two agent-writable shared data files` → `three`.
11. `SKILL.md` — compressed the escalation clause to the judgement only (~114 words), mechanics now in the reference.
12. `references/verify-and-set-status.md` — `git diff <base>` → `git diff HEAD`, with the reason (audit does not commit mid-run).
13. `references/semantic-checks.md` — reframed the synthesis check as a labelled sixth question so "The five questions" stays true, and corrected the corpus authority: counts check against `sources:` / `source_count:` / the `Sources` callout, not against `Scope`, which is not a source list.
14. `SKILL.md` → `references/verification-spec.md` — pure move of the 299-word CLAUDE.md-change re-check gate into a new `## The CLAUDE.md-change re-check gate` section, with a pointer left in Step 6 and the dangling "Then" opener repaired.

Mechanical edits: 2 (sentence-case `Execution order for a rewritten page` in heading and TOC; missing `Closeout rules` entry added to the Contents block).

## Budget outcome

SKILL.md body: **7060 → 6377 words** against the 6500 budget. `body_over_length` cleared. Council 2's chair correctly identified that Council 1's inherited arithmetic (from advisor E) was wrong — it used whole-file `wc -w` for the delta and block estimates for the revert.

## Sanity check (Step 6)

Structural — all five scanners against the edited skill:

- `check_structure.py` clean (`body_over_length` cleared), `check_synonyms.py` clean, `check_musts.py` clean, `check_h2_case.py` clean, `check_kwargs.py` not applicable (no `scripts/`).
- Additionally: `check_internal_refs.py` clean; full test suite 316 passed; `check_consistency.py` whole-repo 0 findings.

Semantic — re-read of each applied judgement edit in context. One defect caught and fixed: the moved re-check gate opened with a dangling "Then judge whether…" connective, repaired to a standalone opener naming when the gate runs.

## Cross-file proposals (not applied)

1. `.claude/skills/multi-skill/alias-detect-exempt.md` → "Adding an entry": change `Record the count in the comment beside the entry` to *on its own comment line directly above the entry*, with the reason — `_load_alias_detect_exempt` splits the entry line on `::` and strips no trailing `<!-- … -->`, so a same-line comment becomes part of the exempted form and the entry silently exempts nothing. **Empirically confirmed** by an advisor running the parser.
2. `.claude/skills/lint/references/checks.md` → the `unlinked_page_mention` entry: append that the matching vocabulary is further reduced per page by `alias-detect-exempt.md`, scoped to the named page, with `stale_alias_exempt` as its hygiene check. Today only the `stale_alias_exempt` entry names the file, so a reader of the canonical registry cannot learn the exemption exists.
3. **Severity mislabel across four files.** `check_wiki.py:595` registers `verified_anchor_unaudited` as `'error'` (Critical) and it is absent from `STANDING_NONBLOCKING`, but `audit/references/verify-and-set-status.md:42`, `lint/SKILL.md:47`, `lint/references/checks.md:76`, and `multi-skill/references/verification-neutral-fixes.md:57` all call it a Warning — and `checks.md:76` argues at length that it *should* be one. One of the two is wrong and which is a design call, not audit's to make.
4. `.claude/skills/audit/SKILL.md` frontmatter `description:` (1016/1024 chars): add the missing `verify` / `promote to verified` / `clear a needs-update backlog` triggers and the `skill-linter` boundary, paid for by cutting "Claims arrive certified, so it re-opens a raw only on cause." and ", preserving the prior version". Not applied: load-bearing and unrefuted this run. **Do not add "commits as it goes"** — that behaviour was reverted.
5. `.claude/skills/skill-linter/SKILL.md` description: `for a 1-wiki/ page or note use lint` → `use lint (structure) or audit (quality)`. A user typing "audit my notes" currently lands in skill-linter and is routed to lint, which cannot answer a quality question. Measured at 995 chars, so it fits.
6. `references/verify-and-set-status.md` venue/year bullet: disambiguate `Clear the field` to *empty the value and keep the key*, since deleting a `REQUIRED_FIELDS` key trips `frontmatter_missing_field`. The refuter confirmed the emptying reading is mechanically safe; the wording is still ambiguous.
7. `references/verify-and-set-status.md` drop-the-quantifier: replace the sentence-fragment example with a standalone atomic bullet, and state that the rewrite re-enters the refuter tier. Kept as a rule per the refuter; only the example and the re-check note need repair.

Also recorded, not proposed: advisor E's `references/preconditions.md` extraction (~537 words) and its sub-heading split of the 898-word Coverage gate paragraph — both real and anchorable, both excluded as over-correction once the budget closed without them.

## Follow-up pass — all proposals resolved

On the user's instruction to fix everything outstanding, the seven proposals above and the two defects were all applied in a follow-up commit. Three needed a determination rather than a transcription:

**`verified_anchor_unaudited` severity — the code was wrong, not the prose.** Determined from the functional consequence rather than by counting sources. The check is registered `'error'` (Critical) and sits outside `STANDING_NONBLOCKING`, so it counts toward `audit_blocking`. But audit's Step 1 says a blocking finding lint cannot mechanically fix means "stop there and put them to the user" — and `verified_anchor_unaudited` is explicitly *not* auto-fixable, sits on **audit's** authored worklist, and is named a Step 5 cause audit settles by opening the raw. As a blocking Critical it deadlocks: audit stops at Step 1 over a finding it is the designated resolver for and can never reach Step 7 to resolve it. The legitimate paths are already exempt in code (`test_diffguard_unverified_marker_is_exempt` proves a `*[unverified]*`-marked claim does not fire it; the head-status gate exempts a page audit is promoting this run), so nothing is lost by the Warning tier. Changed to `'warning'` with the reasoning in a code comment; the two tests that pinned `'error'` updated. Four prose files (`lint/SKILL.md`, `lint/references/checks.md`, `audit/references/verify-and-set-status.md`, `multi-skill/references/verification-neutral-fixes.md`) now agree with the code, and the sibling `stale_mention_ignore` carries the same tier on the same "the tier says who acts" reasoning.

**The shared spec's split rule.** `multi-skill/references/verification.md` still carried the half that enabled audit's Tier-3 collapse — "Refuters return findings plus a selective list of what they positively checked". `ingest` and `query` run that file. Reconciled: silence is neither dissent **nor assent**, an omitted claim is unread and cannot be certified until re-issued, and where several claims go to one refuter an explicit per-claim verdict is required rather than a selective list.

**`skill-linter`'s description.** The advisor measured it at 995 chars and judged the boundary addition would fit; it measured 1026 after the edit — over the 1024 hard ceiling, which `check_structure.py` grades an error. Trimmed ("page or note" → "page") to 1018. A reminder that an advisor's measurement is a claim to check, not a fact.

Also repaired while verifying: `lint/references/checks.md` referenced `scripts/pagination_map.py` and `scripts/cited_figure_check.py` as bare paths that resolve nowhere from lint's own folder (both live in `multi-skill/scripts/`), tripping `broken_inline_ref` twice. Pre-existing, and a stale-path repair, which `CLAUDE.md` → Stay in your lane permits in any file.

Audit's description was rewritten to 983 chars (from 1016, so headroom went 8 → 41): added the `verify` / `promote pages to verified` / `clear a needs-update backlog` triggers and the `skill-linter` boundary, paid for by cutting "Claims arrive certified, so it re-opens a raw only on cause." and "preserving the prior version". "Commits as it goes" was deliberately **not** added — that behaviour was reverted.

**Pre-existing findings recorded, not fixed** (confirmed identical at HEAD, on skills this run did not touch): `ingest` and `cleanup` `check_structure`; `query`, `brief`, `compare`, `reflect` `check_synonyms`. Per the protocol, pre-existing findings on untouched files are recorded rather than repaired in this run.

Final state: 316 tests pass, `check_consistency.py` 0 findings, `check_wiki.py` 0 findings, and all four scanners clean on every skill this work touched.

## Preserved dissent

**Ranked above the majority and adopted:** the Contrarian's minority branch that the commit rule should be *dropped* rather than carved out. Four of five Council-1 advisors assumed it stays and wrote prose to contain it; peer review supplied the reason the minority was right — the deterministic backstop is script-resident and unreachable from audit's own files, so every carve-out was a non-fix.

**Preserved but ruled against:** the Expansionist's audit-report frontmatter (`type: audit`, `result: settled|interim|blocked`, `pages_pending:`). All five Council-1 peer reviews asked to preserve it — the only unanimous cross-review verdict in the run. Audit gates on lint's and consistency's `result:` while emitting nothing machine-readable back. Deferred rather than dropped: its strongest leg was telling a successor pass whether the prior pass ended interim, which the revert amputates, and it needs a cross-file `CLAUDE.md` registration. If the multi-pass loop is ever re-proposed, this should land in the same change.

**Preserved but ruled against:** the Description reviewer's position that run-to-completion and commit-as-you-go *must* reach the description. Sound conditional on the rules shipping; they do not. If a maintainer reinstates either, this edit becomes mandatory.

**Rehabilitated against peer review:** all five Council-2 peer reviews ranked the Structure reviewer last ("zero correctness findings"). Its *method* deserved that; its *result* did not. It was the only reviewer to test the commit against the shared spec, and the cross-file duplication it found is a direct hit on a criterion the brief names, invisible to every script in the repo. Council 2's chair separated the evidence from the disposition and adopted the finding while rejecting the proposed pure move.

## What peer review surfaced that no advisor had

1. **The convergent fix was itself wrong** — three advisors proposed "Three lint checks"; none consulted the canonical text. Convergence across independent reviewers read as confirmation and was correlated error.
2. **No prose carve-out can reach the deterministic backstop** — the single load-bearing reason both chairs ruled revert.
3. **The set over-corrects** — four advisors were about to bolt caveats onto a body already 560 words over budget, making the known-wrong baseline worse while fixing it.
4. **commit-at-milestones is a governance change.** `SKILL.md:18` calls audit's autonomy "a conscious departure from that document's human-commit-point model" and closes "Do not weaken either check without re-introducing a human re-voicing step in its place." The uncommitted working tree was the surviving human checkpoint — one reviewable, discardable diff per run. All ten advisors treated commits mechanically.
5. **The non-transferability frame** — all ten advisors reviewed llm-wiki-mas tuning as if it were template rules, and none noticed the commit message had already rejected one lesson on exactly those grounds. This reframing is what turned ~600 words of carve-out into a set of deletions while solving the budget.
6. **The alias port was incomplete in five places, not two.**
7. **The severity mislabel**, caught independently by two reviewers.

## Value over the skill-linter baseline

The deterministic baseline found one finding: `body_over_length`. The council found ten defects — three of them capable of silently minting a wrong `verified` stamp — plus five cross-file gaps and a governance question, and its refuters then killed five of its own proposals, two of which would have removed correct rules. A single-context pass would not have produced the revert-versus-carve-out reframing, which came only from peer review reading across five advisors at once.

## Self-report

Limitations this run hit, and the upgrades that would prevent them:

- **No agent type matches the protocol's required toolset.** `protocol.md` requires refuters and advisors spawned with Read/Glob/Grep and no shell-write, "so the no-edit rule is enforced by the toolset rather than merely promised". The closest available type (`Explore`) excludes Edit/Write/NotebookEdit but retains Bash, and its charter is excerpt-reading rather than deep review — both worked around by prompt, which is exactly the "merely promised" enforcement the protocol rejects. Upgrade: name a concrete fallback ordering in `protocol.md` for environments with no exact-match agent type, and state that the deviation is recorded in the report rather than left implicit.
- **The skill reviews one skill per run, but the request was a changed *set*.** Resolving to the most-changed skill and passing the rest as context worked, and the cross-file proposal path caught the remainder — but findings against `lint`, `consistency` and the shared spec could only be proposed, never verified by a refuter against their own ground truth. Upgrade: allow a multi-skill target whose auto-apply scope is the union of the named skill folders, or state explicitly that a changed-set review resolves to one target and the rest are proposal-only.
- **The refuter step has no path to apply a refuter's own corrected version.** Five edits were refuted; in three cases the refuter supplied a demonstrably better edit (the larger `apply-fixes.md` fix, the venue/year disambiguation, the quantifier example repair). Only the first was applied, because it was a strict superset of the proposed edit; the other two became proposals, since applying a refuter's counter-proposal would ship an unrefuted load-bearing edit. Upgrade: define a bounded second refuter pass for a counter-proposal a refuter supplies, so a refutation that comes with a correct fix is not downgraded to a manual item.
- **Peer review outranked the advisors on the single most valuable finding, and the protocol has no way to record that.** The non-transferability reframing existed only in peer review, and the report template has a slot for it, but nothing feeds it back into role design. Upgrade: add a specialist to the bank for a review whose subject is a *port* between repos — the angle no roster seat covered.
