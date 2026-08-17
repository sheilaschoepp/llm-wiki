---
type: skill-llm-council
run_mode: reduced — adversarial-verification pass only
target: this session's three edits (not a skill)
councils_convened: 0
refuters: 5
load_bearing_edits: 3
edits_applied: 0
edits_reverted: 3
date: 2026-08-17
---

# Reduced refuter pass — this session's edits to verification.md and audit

## What actually ran

**This was not a council run, and the report must not be read as one.** The user asked for `skill-llm-council` with five subagents. A full run is about 22 calls: two five-agent councils, anonymized peer review within each, a chair subagent per council, then a meta-chair. Five agents cannot produce that structure. What ran instead was Step 6's adversarial-verification gate on its own — five independent refuters, distinct angles, read-only by toolset, each instructed to default to REFUTED and to open ground truth itself rather than accept the orchestrator's framing.

So: no councils convened, no peer review, no chair syntheses. The skill warns that role-playing councils in one context "produces a confident audit trail describing independent councils that never existed", and this file exists partly to make sure that did not happen by omission either.

The orchestrator was also the author of every edit under test. That is the position the skill says the refuter step exists to check, so refutations were treated as decisive rather than argued with.

## Edits under test

| id | file | change |
|----|------|--------|
| E1 | `.claude/skills/multi-skill/references/verification.md` | two bullets added after `:37` — a permission default is not mechanical unavailability; invoking a refuter-mandating skill is the request; taking the draft exit must be declared in `## Self-report` |
| E2 | `.claude/skills/audit/references/apply-fixes.md:74` | budget removed as a staging ground; "a page may stage once" bound added |
| E3 | `.claude/skills/audit/SKILL.md:158` | report line extended to carry each staged page's mechanical reason and stage count |

Commits `d4bf810` (E1) and `af244b2` (E2, E3). Both reverted in `8d2cc57`.

## Verdicts

All five refuters returned REFUTED overall. Every load-bearing quote below was re-grepped against the files by the orchestrator before being acted on, per the spec's rule that a subagent can fabricate a plausible quote and that a fabricated refutation reversing a correct edit is the costliest failure.

### The decisive finding — E2's premise was false

E2 rested on a claimed contradiction: that `apply-fixes.md:74` licensed staging on budget what `verify-and-set-status.md:19` says cost can never justify skipping.

The two texts govern different scopes. `:19` scopes the **re-fact-check of rewritten bullets** with `git diff`. The cost the staged valve actually stages is the page's **full return to `verified`**, and `verify-and-set-status.md:50` conditions that stamp on "confirmed full-text coverage (Step 5 coverage gate) and every non-obvious claim on it has passed the tiered independent-refuter gate", with `verification-spec.md:15` requiring every cross-source locator opened, "no sampling".

That is page-wide. E2 therefore wrote a false statement into the exact sentence where a run decides whether to stage: *"'the remaining work looked large' is the estimate of an operation this skill does not perform."* The skill does perform it. A run obeying E2 would under-scope a genuinely page-wide re-promotion, decline to stage it, and be forced to abandon it mid-pass with no valve left.

And with the scopes distinguished, the contradiction dissolves. `:19`'s named harm is *stamping without the read*; the pre-edit `:74` explicitly withheld the stamp ("a page never keeps or earns `verified` while a content-changing worklist item on it is unapplied or its post-edit body unverified"). Skip-and-stamp and defer-while-withholding are different dispositions. What existed was a difference in rationale, not a licence against a prohibition.

### The bound was unimplementable

Three independent grounds, each verified:

- **No readable carrier.** The stage count was written to audit's report. Audit reads lint's (`SKILL.md:82`) and consistency's (`SKILL.md:88`) newest reports; its only touch of `2-outputs/audit/` is `verification-spec.md:38`, which reads a timestamp for a git-log comparison, never content.
- **Consuming it is forbidden anyway.** `apply-fixes.md:24` — "Never inherit a finding from a prior report. Re-derive it, or drop it." `SKILL.md:221` — a new status "never in recollection or a prior report's say-so." `SKILL.md:166` says the same a third time. The bound's whole payload is a new status derived from a prior report's count.
- **The clause was inert and the payoff false.** "Enters the next run's Step 5 scope first" adds nothing: `SKILL.md:36` already admits "every `draft` and `needs-update`" page unconditionally. "Closes within two runs" fails against CLAUDE.md's `settled`, which requires "a blocker no further pass can clear" — unspawnable refuters and an unreachable raw are both transient, so the page stays `needs-update` and keeps incrementing `pages_pending:` exactly as before.

### E1 — substance held, framing did not

The permission-default distinction survived its angle. A user who says "don't spawn subagents" and then invokes `/ingest` is correctly routed to the draft exit, because the permissive clause is scoped to the conditional form and `:38` sends an unconditional default back to the first clause.

But:

- **The headline is false.** "Those two reasons are the whole class, and both are mechanical" is contradicted three sentences later by the same bullet, which concedes an unconditional default *is* a member. Two refuters found this independently. The second reason — "may not nest them" — is a project-imposed rule, the same shape as the permission default the bullet excludes, so the mechanical/permission dichotomy the argument rests on does not hold.
- **The declaration duty had no carrier.** `self-report.md:19` fixes the item shape as `{limitation} → upgrade: {how the skill should change}`; `:12` forbids inventing an upgrade to fill it. A run that took the exit because it is itself a subagent has no upgrade to pair. There is no count field, nothing mechanical reads `## Self-report`, the duty already exists in two places pointed at *the report*, and the same file eight bullets away (`verification.md:45`) already prescribes a stronger page-level remedy for exactly this disease.
- **An unverifiable ordinal shipped.** "on the first run instead of the eighth" describes a downstream repository this checkout cannot see. It was written into a shared file that propagates to every seeded wiki.

### Schema drift created

`audit/SKILL.md:186` computes `result:` and `pages_pending:` "per the definitions in `CLAUDE.md` → Audit preconditions". E2 introduced a terminal state that paragraph does not enumerate and its `settled` clause excludes. The schema needed a companion edit and did not get one.

### What was clean

Four of the five prose-and-authoring angles failed, reported here because a refuter pass that only records hits is not a check:

- `check_structure.py`, `check_synonyms.py`, `check_musts.py`, `check_h2_case.py` — all exit 0, all `[]`, no crashes. (Caveat: only the first and fourth traverse `references/*.md`; the other two read `SKILL.md` only and structurally could not see the largest edit.)
- No forbidden cross-skill reference. The pointer to `multi-skill/references/` is the sanctioned sharing path (`CLAUDE.md:659`); the pointer to `verify-and-set-status.md` is intra-skill.
- No HTML-tag violation. `<page>` sits inside an inline code span, which `check_structure.py:491` strips before checking, and `page` is not in `HTML_TAGS`.
- No restated Limits rule. Audit's Limits section contains no staging rule.

Prose quality did not clear: `apply-fixes.md:74` went 115 → 340 words for two one-sentence rules, carrying eight antithesis constructions against a house rule of "one in a paragraph is already too many" (`ai-writing-tells.md:82`).

## Disposition

Both commits reverted in full (`8d2cc57`). The working tree is byte-identical to `77e6ce4`. Nothing from this session's edits ships to wikis seeded from this template.

The problem that prompted the work is unfixed and correctly diagnosed: the session system prompt carries a conditional instruction ("Do not call the AgentTool unless the user requested it") that is absent from every file in this repo, and past downstream runs recorded it as a standing user-imposed prohibition. That misreading is real. The repair attempted here was not sound.

## Self-report

- The orchestrator proposed three bound options to the user and recommended one, without first checking whether audit can carry state between runs. Two of the three were unimplementable for the same unexamined reason; the one that needed no cross-run state was the option argued against. → upgrade: before offering the user a choice between design options, verify each option is implementable in the target architecture; an option list is a claim that every entry is viable.
- The false-premise finding in E2 was reachable before writing — it needed one read of `verify-and-set-status.md:50`, in the same file whose `:19` was cited as the contradiction's other half. The orchestrator read `:19` and stopped. → upgrade: when citing two texts as contradictory, read both files whole rather than the two quoted lines.
- Refuters were run after committing rather than before. Every finding here was recoverable only by revert. → upgrade: on shared-spec edits that propagate to downstream repos, run the refuter pass before the commit, not after.
