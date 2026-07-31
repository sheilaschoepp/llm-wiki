# audit — Report Template (Step 6)

The report body `audit` drafts at Step 6 and finalizes at Step 9. Read this when writing the report; the procedure around it — what each section must reflect, and the Step 9 reconciliation that fills the deferred sections — is in SKILL.md.

The file is `2-outputs/audit/audit-YYYY-MM-DD-HHMM.md`, or `audit-YYYY-MM-DD-HHMM-full.md` for a `full`-mode run so a deep full pass is distinguishable from routine partials. The `-full` is the registry's `-extra` suffix (it sits *after* the timestamp, so `file_naming_consistency` accepts it); never put the mode marker before the date. Obtain the timestamp at save time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context provides the date but not the current minute.

**Status changes applied** and **Verification proof** record what Steps 7-8 actually did, so they are finalized in Step 9 — never let the report claim a change that a partial Step 7/8 failure left undone.

```markdown
---
type: audit
date: YYYY-MM-DD
mode: partial | full
markers_pending: {N}    # total *[unverified]* markers wiki-wide at run end (counted directly — check_wiki.py's per-page unverified_claim messages summed, or a direct count of the marker)
inherited_cleared: "{C} of {I}"  # inherited (anchor-at-HEAD) markers cleared this run / at run start
---

# Audit - YYYY-MM-DD-HHMM

## Summary
- Mode: partial | full
- Critical: N
- Warning: N
- Info: N
- Worklist ledger, per class (lint check_id, or a short audit finding-class label), this run vs the newest prior audit report: carried in {N} → resolved {A} + marker-pending {P} (authored this run; the next post-commit audit clears them) + handed to the user {B} (genuinely ambiguous structural calls only). Resolved means reached its durable final-state disposition this run — including a barrier repair — fixed, or set `needs-update` with its derivation, or `*[tentative]*`-marked per the dispositions in `references/apply-fixes.md`; N = A + P + B, and there is no other bucket, because the edits themselves never stage. Invalidated verification never supplies ledger credit: count a barrier item from the repair or other final disposition itself. Inherited markers — those whose `#page=N` anchor is at git HEAD, the set `references/apply-fixes.md` permits clearing (markers left by a prior run that has not yet been committed are not inherited for this purpose and are carried forward with the new arrivals): {I} at run start, {C} cleared in the final epoch, {Ir} still pending; while I is above zero, Ir must be strictly below I — an inherited-marker class that did not shrink is a Warning naming the specific blocker (a class at zero staying at zero is not a finding). New arrivals since the prior run are listed separately and excluded from these comparisons. (or "no open worklist")
- Refuter spend, final epoch only: {claims certified through the refuter gate in final epoch READY(n)} claims, {final-epoch refuter calls} calls, {escalations} escalated to a third (name each trigger: evidence-backed split / destructive correction / aggregate recomputation). A run whose final-epoch calls exceed twice its certified claims escalated more than the triggers warrant; say so and why. Invalidated calls are excluded here and recorded separately below.

## Relationship-integrity barrier
- Final verification epoch: READY(n)
- Post-repair evidence: consistency {report/run}; complete lint including LLM walk {report/run}; whole-inventory relationship sweep {run}
- Required missing targets: {initial N} → repaired {R} → final 0. If final is not zero, write `barrier blocked`; there is no Verification proof and no promotion.
- Allowed dangling links recorded, not changed: {containing page; context; target; policy class — one-off author metadata / genuine first-use future term / other explicit current-policy exception} (or "none")

## Invalidated verification spend
- Invalidated epochs: {epoch and graph-affecting repair reason} (or "none")
- Discarded work: {pages}, {claims/probes}, {refuter calls}. Cost only — excluded from promotions, marker clearance, inherited-marker burn-down, certified claims, Verification proof, and partial/full completion.

## Status changes applied
(finalized in Step 9, after the final-epoch fixes and stamping run; invalidated-epoch outcomes never appear here)
- Promoted to `verified`: [[1-wiki/concepts/self-attention.md|self-attention]], ... (or "none")
- Set `needs-update`: [[1-wiki/concepts/positional-encoding.md|positional encoding]], ... (or "none")

## Verification proof
(for each page promoted to `verified` from the final epoch this run, mirroring ingest's proof-of-read — see `references/verification-spec.md` coverage gate; invalidated-epoch evidence is never proof)
- [[1-wiki/concepts/self-attention.md|self-attention]] - late-section raw detail re-located: {final section / last figure / appendix, fact-checked}; `#page=N` spot-checked: {N + cited content confirmed} (or `n/a` for a non-PDF raw)
- A promotion recorded with no re-located late-section detail and no confirmed locator is not complete. (or "none promoted this run")
- A `full` run is not complete until its cold post-repair full scope finishes in the final epoch.

## Recommendations
- (e.g. "Re-check needed: the CLAUDE.md change tightening the summary-claim rule may stale verified aggregate claims — demote [[1-wiki/concepts/example.md|example]] for the next partial to re-verify." — only for a change to a raw-judgement criterion, never a format, structural, presence, or process edit.) (or "none")

## Critical
- [[1-wiki/concepts/positional-encoding.md|Positional encoding]] - fact-check against raw failed: listed source [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] does not support one of the page's claims - set `needs-update`; propose removing the unsupported bullet and the bad sources entry
- [[1-wiki/concepts/multi-head-attention.md|Multi-head attention]] and [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] - distortion by generalization: the shared claim "BLEU falls whenever attention heads are reduced" is true of the one cited row (the single-head ablation) but false of the recomputed table - both set `needs-update` with a `needs_update_reason:` carrying the full derivation (distortion-disposition rule, `references/apply-fixes.md`)

## Warning
- ...
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] - page covers two distinct ideas; should split - propose splitting into [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] and [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]]

## Info
- ... (each bullet labelled with sub-type: *verified candidate* / *missing page* / *next source*)
- *verified candidate* — [[1-wiki/concepts/residual-connection.md|residual connection]] - looks ready but not raw-fact-checked this run

## Verification Candidates
- Pages that look ready for `verified` but were not fact-checked against their raw source this run, and pages whose content edit landed this run but whose Tier-2 re-verification was staged to a later run (the staged valve) — flag for the next audit so the backlog burn-down stays visible. Also list any `verified` page audit notices has taken repeated delta-only re-checks — markers cleared on it across several runs with no end-to-end fact-check since, judged from `log.md` and the run history in `2-outputs/audit/` (the newest `full` audit is the last whole-wiki re-read) — and demote it deliberately so the next `partial` re-verifies it end to end. When that history does not settle it, list the page without demoting rather than guessing. Once every path is delta-scoped, nothing re-reads a page whole, and `verified` otherwise decays from "this page is faithful to its sources" into "each line was once checked in isolation". (or "none")

## Self-report
- {a specific limitation that bit audit this run — a rule it lacked, a case it mishandled, a check it couldn't run} → upgrade: {how the audit skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```
