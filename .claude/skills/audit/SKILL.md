---
name: audit
description: 'Whole-page judgement pass over the LLM wiki — reads each finished page whole and asks what cannot be asked claim by claim: is this one idea or three, does it duplicate an existing page, does it contradict something, is it well connected, does it read like an LLM wrote it. Use before high-stakes synthesis, paper drafting, major reference work, or after large ingests. Also use when the user asks whether wiki notes are any good, atomic or too broad, well-supported, duplicative, or hiding contradictions, asks to fact-check or verify the wiki''s notes against their raw sources, or to promote pages to verified or clear a needs-update backlog, even without saying "audit". Judges wiki pages, not skills (use skill-linter); not a research question (use query) or a structural-only check (use lint). Acts autonomously: applies content fixes (splits, merges, rewrites) and sets page status. Satisfies its own preconditions: runs lint and consistency when stale, and re-runs lint after.'
---

# audit

Audit is the judgement pass. It asks whether the notes are good thinking objects.

## Purpose

Structural lint can say whether a page has the right sections. The run that wrote a page's claims can say whether each is true of its source — it had the raw open and checked there. Neither can say whether the *page* is any good, and that is audit's question: **is this one idea or three that should be split, does it duplicate a page that already exists, does it contradict something the wiki holds, is it well connected, does it read like an LLM wrote it.**

None of those can be asked claim by claim. They need the whole page in view — often the whole wiki, since duplication and connectedness are properties of the graph. That is why they are audit's rather than ingest's: an authoring run sees one source and the pages it just touched; audit sees what the wiki has become.

**Claims arrive certified, so audit does not re-check them by routine.** The run that wrote a claim put it through independent refuters against the raw and either certified it, fixed it, or left it marked `*[unverified]*` (`.claude/skills/multi-skill/references/verification.md`). Re-asking the same questions of every raw would double the cost and add nothing. Audit re-opens a raw **on cause** (Verification Model), and in `full` mode as a deep re-confirmation. Refuters are available throughout: not required where audit's own read settles whether to raise a doubt, required wherever it will overwrite or certify content.

`verified` means every non-obvious claim on the page has been checked against its raw and held. It is not the Ahrens-style human re-voicing gate the foundation design (`a-archive/reference/smart-notes-llm-wiki-integration.md`) assigns to promotion: this wiki relocates that safeguard, keeping pages LLM-drafted and putting the defence against AI-voice prose in the authoring run's page self-check plus audit's Step 4 tell-check. Audit's autonomy is therefore a conscious departure from that document's human-commit-point model, authorized by `CLAUDE.md`. Do not weaken either check without re-introducing a human re-voicing step in its place.

## Verification model

The scope, marker, and status rules every step below relies on, defined once here. The full runtime statement is `CLAUDE.md` → Page status and Bullet markers; this is audit's operating summary.

Four load-bearing terms:

- `verified_hash:` — the SHA-256 of a page body with `*[unverified]*` claim lines excluded. It guarantees the page's unmarked content is byte-identical to what was last fact-checked: immutability since the check, not correctness of the check. Re-confirm correctness with `full` mode.
- `*[unverified]*` — a claim-level marker on a non-obvious claim no run has certified: one the authoring run could not check (most often because it cites a source that run did not open, sometimes because its refuters split or the cited region was unreadable), or one whose backing image was re-extracted without a text change. A *changed* claim demotes the page rather than riding it, so a marker on a `verified` page is an addition, not an edit. It is the standing cause for a raw re-check in `partial` mode, and the hash excludes it so it can ride a `verified` page as the pending delta.
- `*[tentative]*` — a claim-level marker for weak or thin support. Unlike `*[unverified]*` it is an epistemic judgement, not a process state: a fact-check does not clear it, and the two can co-occur on one claim. It is the safe-failure marker audit falls back to whenever the raw cannot positively settle a claim's support — mark `*[tentative]*` and set `needs-update` rather than delete or self-stamp.
- authored-tier worklist — the Warning-tier findings lint detects but leaves for audit to carry out. Audit's authored worklist *is* lint's Warning output, so a Warning check lint adds later automatically becomes audit's job with no edit here.

**Two scopes, not one.** The page-level judgement (Step 4) runs over **every** page in both modes — it needs no raw and it is the pass audit exists for. The raw fact-check (Step 5) is the narrower, cause-driven scope, and the mode sets how wide it gets.

**Fact-check scope by mode.** `partial` (default) re-opens the raw only where there is cause — five causes, elaborated in `references/verification-spec.md`:

- every `*[unverified]*` claim, wherever it sits;
- every page carrying claims no run ever certified: every `draft` and `needs-update`, plus any `verified` page whose `verified_hash:` is missing or stale;
- any claim Step 4 gives a **specific** reason to doubt — specific meaning the doubt names what would refute it, not a general unease;
- every claim audit itself rewrites, splits out, merges in, or drops (Step 8);
- every locator lint flags (`verified_anchor_unaudited`, `locator_page_mismatch`, `page_locator_unlinked`), settled with the raw open, never by inference.

It does **not** re-check a certified page's unmarked claims: they were checked against the raw by the run that wrote them, and `verified_hash:` guarantees they have not changed since. That is what keeps audit affordable as the wiki grows, and why the hash check in Step 5 is not optional bookkeeping — it is the whole basis for the skip.

`full` fact-checks every claim on every page, certified or not. Use it when a CLAUDE.md change tightens a raw-judgement criterion so broadly that the affected claims cannot be bounded (Step 6 — a bounded change demotes just those pages instead), when a batch was certified by a run you have reason to distrust, or as a periodic deep-confirmation pass. A certified page whose re-check still holds keeps its `verified_hash:` and `updated:` unchanged — only a page needing a correction or a cleared marker is fixed and re-stamped.

**Verification is terminal.** The `verified` stamp is the last write a page receives. Every content edit — audit's own Step 4 findings, lint's Step 1 authored worklist, and any cross-page edit landing on the page (a reciprocal mirror, an inherited-distortion fix) — is applied in Step 7, *before* the page is re-verified and stamped in Step 8. No fix ever lands on an already-stamped page. A content-changing worklist item demotes the `verified` page it targets — it moves the body hash — so front-loading it in Step 7 brings the page into this run's fact-check scope, where it is re-verified and re-stamped. The hard invariant: **a page never keeps or earns `verified` while a content-changing worklist item on it is unapplied or its post-edit body unverified.** The edits themselves never stage across runs; only two costs may — the Tier-3 re-verification of a page a content edit demoted this run, and the sub-agent quorum for `unlinked-mention-ignore.md` and `alias-detect-exempt.md` additions — under that same invariant (a page whose edit landed but whose re-verification could not finish stays `draft`/`needs-update`, and the next `partial` audit re-verifies it).

**Marker/hash mechanics.** An addition marked `*[unverified]*` rides a `verified` page because the hash excludes it; a *changed* existing claim demotes the page, because its line was in the hash and altering or masking it moves the hash. `body_hash.py` masks `*[unverified]*` lines before hashing and needs well-formed `---` frontmatter delimiters (Step 8).

## Arguments

`audit` accepts one optional positional argument selecting the verification scope: `partial` (default, equivalent to no argument) or `full` — see Verification Model for what each fact-checks. Routine runs use `partial` to preserve the claim-level optimization; reach for `full` only in the cases named in the Verification Model.

Invoke as `audit` or `audit full`. If the token looks like a page path or name (contains `/`, ends in `.md`, or matches an existing page title), the caller likely wants to scope audit to one page — but audit has no single-page or target mode and would otherwise run an autonomous whole-wiki pass, so confirm scope via `AskUserQuestion` before proceeding rather than disclosing the ignored token only in the after-the-fact report. Any other unrecognized token: default to `partial` and note the ignored token in the report.

## When to invoke

Use before high-stakes synthesis, paper drafting, major reference work, or after large ingests.

## When not to invoke

- The user wants a research answer. Use `query`.
- The wiki is too small to audit meaningfully.

## Procedure

```text
Audit Progress:
- [ ] Step 1: Satisfy the lint precondition (run lint if stale or not clean); collect its authored-tier worklist
- [ ] Step 2: Satisfy the consistency precondition (run consistency if stale or not clean)
- [ ] Step 3: Load memory; read the wiki (and the raw sources Step 5 will need)
- [ ] Step 4: Judge each page as a page — the whole-page pass, over every page
- [ ] Step 5: Front-load the detection-time worklist, then fact-check what there is cause to fact-check
- [ ] Step 6: Draft the audit report
- [ ] Step 7: Apply the fixes (all content edits) — verified pages the edits target demote into scope
- [ ] Step 8: Verify rewritten bodies and set status — verification is terminal
- [ ] Step 9: Run a confirming lint over the pages this run mutated
- [ ] Step 10: Finalize report; update index, hot, and log
```

**Audit satisfies its own preconditions.** Steps 1 and 2 do not merely check for a clean lint and consistency — they produce one when it is missing. Each runs *stale-aware*: read the newest report of that kind, and if it is clean and still current by the recency test below, proceed without re-running it; otherwise execute that skill in full, looping its own layer until clean, then proceed. A repeat audit over an unchanged wiki therefore costs nothing extra, while a first audit after a schema change pays for the consistency run it actually needs. This is the one place a skill invokes another (`CLAUDE.md` → Skill authoring names the audit precondition on lint and consistency as the lone dependency exception); audit owns the sequencing because it owns the requirement.

1. **Satisfy the lint precondition.** Read the newest `2-outputs/lint/lint-*.md` and gate on its frontmatter `result:` field. If it is absent, stale by the recency test below, or `result: blocking` (equivalently `audit_blocking:` > 0), **run `lint` in full** per `.claude/skills/lint/SKILL.md`, looping its deterministic layer to a clean pass and applying every fix it owns; then read the report it just wrote. If the fresh lint still reports `result: blocking`, its `## Audit-Blocking` findings are ones lint cannot mechanically fix — stop there and put them to the user, since auditing over unresolved structural drift is what the precondition exists to prevent. `result: clean` means no audit-blocking finding remains — lint excludes the standing repo-state items audit cannot act on (`raw_without_source_page`, `uningested_raw_source`, `status_needs_update`) from the blocking count, so a clean lint can still carry those Criticals. If the report predates this field, classify manually: a Critical is audit-blocking unless its `check_id` is one of those three; Warnings and Info never block; when a critical's class is unclear, treat it as blocking.

   **Recent** means the lint is at least as new as the most recent `1-wiki/log.md` entry that touched a wiki page, with no uncommitted working-tree wiki edit unaccounted for — also run `git status --porcelain -- 1-wiki` (a hand edit in the editor need not have written a log entry and would otherwise ride through this gate against a drifted wiki). A non-empty git result is not itself the stop signal: no check commits mid-run, so the gating lint's own auto-fixes and its `log.md`/`hot.md`/`index.md` bookkeeping — and any page a prior audit edited before that lint in an `audit → lint → audit` cycle — are expected to sit uncommitted and are what the newest lint report accounts for. Stop only on an uncommitted `1-wiki` change the pipeline does not account for: a wiki page whose content changed after the gating lint, named in neither that lint report's Auto-Fixed list nor a wiki-touching `log.md` entry at or before its timestamp (a genuine post-lint hand edit). That is a stale lint: re-run lint rather than stopping. (Step 5's body-hash self-check and per-page fact-check independently backstop a drifted page that slips past this gate.)

   Then collect lint's open authored-tier findings — **every Warning-tier finding in lint's report** (the ones lint detects but leaves for audit to carry out): e.g. missing reciprocal contradictions, length-cap review (a `length_cap_exceeded` page is split only when it genuinely holds more than one idea — length alone never forces a split, and a page long only from inline-citation density is not over the cap; `CLAUDE.md` → Length), source-context-phrase / vague-source-referent / `unlinked_page_mention` / mechanical AI-writing-tell rewrites, and bare page locators needing a `#page=N` deep-link (`page_locator_unlinked` — audit reopens the raw anyway, so it computes the printed→physical offset: `N = printed − (first_printed − 1)`; never guess offset zero on a source not paginated from 1). Take lint's Warning tier as the worklist, not a fixed sub-list, so a Warning lint adds later is still carried in. **Info-tier findings are not audit's to action** — in particular the user-owned rename/re-path checks `filename_not_kebab`, `source_stem_mismatch`, and `bare_basename_link`, whose only safe fix is a rename the user performs. A finding lint deterministically caught must be resolved even when audit's own Step 4 pass does not independently re-notice it — here the lint report is a worklist, not just a gate.

2. **Satisfy the consistency precondition.** Read the newest `2-outputs/consistency/consistency-*.md` and gate on its `result:` field the same way. If it is absent, stale by the recency test below, or `result: findings` / `result: blocked`, **run `consistency` in full** per `.claude/skills/consistency/SKILL.md`, looping until it reaches `clean`; then read the report it just wrote. If the fresh run still reports `findings` or `blocked` — an outstanding schema-integrity proposal, a skipped judgment-drift read, or a battery that did not complete — stop and put it to the user: those are decisions consistency cannot make autonomously, and they say the schema itself is in dispute. `result: clean` can still carry `proposals:` > 0 (root-level proposals awaiting the user); those do not block audit. If the report predates this field, fall back to the prose check: if any unresolved findings remain in the body, stop. **Recent** means the consistency report is at least as new as the most recent change to `CLAUDE.md`, `README.md`, or `.claude/skills/` — check via `git log -1 --format=%ad -- CLAUDE.md README.md .claude/skills ':(exclude).claude/skills/multi-skill/hyphenation-lists.md' ':(exclude).claude/skills/multi-skill/unlinked-mention-ignore.md' ':(exclude).claude/skills/multi-skill/alias-detect-exempt.md'`, and also `git status --porcelain` over that same pathspec for uncommitted edits the git-log date misses. The three excluded paths are the agent-writable shared data files audit itself grows in Step 7 (runtime data, already exempt from consistency's content scan), so audit's own sanctioned writes to them are never grounds to re-run consistency; every other `.claude/skills` change (and `pagination-map.md`) still trips the gate. If those committed changes postdate the last consistency run, or any uncommitted change to them exists, the report is stale — re-run consistency rather than stopping. Auditing against a drifted schema produces findings against rules the project no longer agrees on.

3. **Load memory, then read the wiki and the raw sources.** First read `.claude/skills/audit/audit-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` to apply prior corrections about scope, fact-check aggressiveness, and which judgement calls audit has been told to make differently. Then read source pages, concept/entity pages, syntheses, `hot.md`, `index.md`, and `log.md` — every page, in full, because Step 4 judges pages as pages and the duplication and connectedness questions are answerable only across the whole inventory. Raw sources are read for Step 5's cause-driven scope only: the raws behind pages carrying claims no run certified, and behind any `*[unverified]*` claim. Read each such raw once and settle everything that traces to it in one pass. A certified page whose hash still matches needs no raw re-read in `partial` mode — it is read as a page, not re-fact-checked.

4. **Judge each page as a page.** The pass audit exists for: it runs over every page (certified or not, both modes) and needs no raw re-read. Read the finished page whole and ask the five questions from Purpose — one idea or three, duplicate, contradiction, connectedness, LLM voice. A page can have every claim certified and still fail all five; that gap is why this pass runs over certified pages too.

   Plus the rest of the catalogue — plain language, source-shaped drift, intra-page redundancy, citation form, tag drift, stale drafts. The full Critical / Warning / Info catalogue, and what each of the five questions looks for, are in `references/semantic-checks.md`; run every check in it. Critical = support/faithfulness failures; Warning = the authored-worklist items Step 7 carries out; Info = candidates and suggestions. A finding that turns on whether a claim is true of its source, rather than on how the page is built, becomes cause for Step 5: name what would refute it and carry it there rather than acting on it unchecked.

5. **Front-load the detection-time worklist, then fact-check what there is cause to fact-check.** Apply the *detection-time* content worklist — the Step 1 lint authored tier and the Step 4 findings — onto each affected page before fact-checking it, because a content-changing edit demotes any `verified` page it targets and brings it into scope (Verification Model, terminal verification). The scope is then the five causes, plus any page a content-changing item just demoted.

   For each, reopen the raw source — not just the wiki source page — and verify it per `references/verification-spec.md`: the coverage gate, the tiered independent-refuter gate (three agreeing refuters on a non-obvious claim being certified or overwritten — the broad default — spawned read-only from this top-level agent), the per-page-type callout checklist, the claim-by-claim support / faithfulness / reasoned axes, the page-scoped citation check (each cited claim verified at the page it cites, every cross-source-bullet locator opened), and the yes/no audit-assumption framing for every Critical and acting Warning. On a certified page carrying a marked or doubted claim, reopen the raw only for that claim; the rest of its content is not re-checked in `partial` mode.

   **Guard an unstamped or stale-stamped verified page.** Treat a page marked `verified` with no `verified_hash:`, or whose hash does not match its body, as uncertified and fact-check it regardless of mode. Before skipping any `verified` page in `partial` mode, run `python3 .claude/skills/multi-skill/scripts/body_hash.py {page}` yourself and compare to its `verified_hash:` — audit owns this check rather than assuming lint ran it this cycle, and it is the entire basis on which the skip is safe. If `body_hash.py` is missing, exits non-zero, or returns a non-64-hex value (e.g. on malformed or unclosed-`---` frontmatter), do not skip the page and do not let the error abort the run: treat it as uncertified, fact-check it, repair the delimiters or set it `needs-update` with a `needs_update_reason:` naming the malformed frontmatter, and surface a Critical.

   **If nothing meets the cause bar** (every page certified and hash-matched, no markers, no doubted claim), there is nothing to fact-check. That is the expected steady state, not a shallow pass: Step 4 still ran over every page and Step 7 still carries out its findings. Write the report with empty fact-check sections and say so. Do not invent work to fill the pass, and do not re-check certified claims to feel thorough — that is the double spend this division of labour removes.

6. **Draft the audit report** at `2-outputs/audit/audit-YYYY-MM-DD-HHMM.md` — or `audit-YYYY-MM-DD-HHMM-full.md` for a `full`-mode run, so a deep full pass is distinguishable from routine partials. The `-full` is the registry's `-extra` suffix (it sits *after* the timestamp, so `file_naming_consistency` accepts it); never put the mode marker before the date. Obtain the timestamp at save time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context provides the date but not the current minute. This is a draft: write the findings now, but the **Status changes applied** and **Verification proof** sections record what Steps 7–8 actually did, so finalize them in Step 10 — never let the report claim a change that a partial Step 7/8 failure left undone.

   Record the run **Mode** (`partial` or `full`). Then run the CLAUDE.md-change re-check gate (`references/verification-spec.md` → The CLAUDE.md-change re-check gate) and record its verdict under **Recommendations**.

Report:

```markdown
---
type: audit-report
date: YYYY-MM-DD
mode: <partial|full>
result: <settled|interim|blocked>   # compute in Step 10 — do not leave the literal `settled`
pages_pending: <N>                  # pages a further audit pass could still close; 0 when settled
critical: N
warning: N
info: N
---

# Audit - YYYY-MM-DD-HHMM

## Summary
- Mode: partial | full
- Pages judged (Step 4, all): N
- Pages fact-checked (Step 5, on cause): N — {which causes fired} (or "none — all certified and hash-matched")
- Critical: N
- Warning: N
- Info: N

## Status changes applied
(finalized in Step 10, after fixes and stamping run)
- Promoted to `verified`: [[1-wiki/concepts/self-attention.md|self-attention]], ... (or "none")
- Set `needs-update`: [[1-wiki/concepts/positional-encoding.md|positional encoding]], ... (or "none")

## Verification proof
(for each page promoted to `verified` this run, mirroring ingest's proof-of-read — see `references/verification-spec.md` coverage gate)
- [[1-wiki/concepts/self-attention.md|self-attention]] - late-section raw detail re-located: {final section / last figure / appendix, fact-checked}; `#page=N` spot-checked: {N + cited content confirmed} (or `n/a` for a non-PDF raw)
- A promotion recorded with no re-located late-section detail and no confirmed locator is not complete. (or "none promoted this run")

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
- Pages that look ready for `verified` but were not fact-checked against their raw source this run, and pages whose content edit landed this run but whose Tier-3 re-verification was staged to a later run (the staged valve) — flag for the next audit so the backlog burn-down stays visible. (or "none")

## Self-report
- {a specific limitation that bit audit this run — a rule it lacked, a case it mishandled, a check it couldn't run} → upgrade: {how the audit skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

7. **Apply the fixes — autonomously.** For every page in Step 5's fact-check scope, act without asking the user; audit is the autonomy exception. This step applies every content edit; Step 8 verifies the results and sets status. Read `references/apply-fixes.md` before editing any page — it holds the full mechanics:

   - **Confirm the defect before fixing it.** A false-positive fix is strictly worse than the defect it imagines, because audit overwrites correct content and certifies it, whereas a missed defect stays visible for the next run. Establish every defect positively against the raw before changing existing content — never from a pattern, an inference, or a prior report's say-so. The mis-located-citation exception, the four per-instance guards, and the yes/no audit-assumption framing for structural fixes are in the reference.
   - **Build the fix list** as the union of audit's Step 4 findings and lint's Step 1 authored tier, and **resolve every item this run** — deferral and batch size are not dispositions (the reference gives the per-check dispositions for `missing_reciprocal_contradiction`, `concept_source_asymmetry`, `unlinked_page_mention`, `stale_mention_ignore`, `stale_alias_exempt`, and `intra_page_redundancy`, and the bounded staged valve).
   - **Clear the link worklist first.** When lint hands audit a large `unlinked_page_mention` backlog, resolve it at the top of this step — before the content fixes the fact-check surfaces, not after them. Each occurrence is individually trivial and collectively large, which makes the backlog the item most likely to be silently dropped once a run gets long; ordering it first is what prevents that, and it costs nothing, since the two kinds of fix do not depend on each other.
   - **Determinate fixes** (a restated number, a distorted claim's wording, a missing citation the fact-check settles, a fabricated mechanism) apply inline; **authored fixes** (splits, merges, source-shaped rewrites) follow ingest's existing-source-mode and the `supersede` preservation/bookkeeping mechanics, inheriting the mechanics but not supersede's approval gates. Bullet removal requires three independent confirming re-reads; a confirmed distortion audit cannot safely correct in-pass is set `needs-update` with a derivation (the distortion-disposition rule); a genuinely ambiguous structural call is downgraded to a Warning for the user. After any citation fix, run the repeated-literal sweep across `1-wiki/`.
   - **Verification-neutral worklist fixes on out-of-scope verified pages** (an `unlinked_page_mention` wrap, a de-hyphenation, a spelling fix, an incidental reciprocity-link unwrap) re-stamp `verified_hash:` with `body_hash.py` rather than demoting — but only after `body_hash.py` confirms the page still matches its stamp. The four format fixes (`callout_block_id`, `wikilink_pipe_spacing`, `citation_bracket_style`, `embed_not_isolated`) are lint's, not audit's.
   - **Grow the check data lists** — `hyphenation-lists.md`, `unlinked-mention-ignore.md`, and `alias-detect-exempt.md` — autonomously, but write no entry on audit's lone judgement: each addition is sub-agent-verified (default ≥ 2 of 3 confirm, each refuter reading its own ground truth). Never touch `check_wiki.py` or its tests. One judgement is audit's alone and is stated nowhere else: **escalate from the per-occurrence ignore list to a per-form exemption when one form dominates the worklist**, because suppression after suppression on a single form says the detector is wrong for that form rather than that the corpus needs more entries — no single occurrence can surface that. The entry mechanics and the measurement gate that must precede one are in the reference. In a fanned-out run these appends and the central locator-format pass are deferred to the central post-fan-out pass (Step 8), spawned from the top-level agent, so parallel writes never collide.
   - **Carry the markup** on anything you author or move: each callout its `> ^block-id`, each locator its `#page=N` deep-link in the form `CLAUDE.md` → Source support and verification defines for the page type (including the unpaginated-supplement exemption). Touch `updated:` on every page whose body audit edits; strip a stale `verified_hash:` on any page audit demotes.

   Step 7 ends with every in-scope page edited and every `verified` page a content edit targeted demoted into scope — nothing stamped.

8. **Verify rewritten bodies and set status.** Verification is terminal: this is the last write each page receives. Follow `references/verify-and-set-status.md`:

   - **Re-fact-check anything you rewrote.** A split, merge, source-shaped rewrite, or dropped bullet produces a body Step 5 never checked. Re-verify it against the raw through the tiered independent-refuter gate like any other claim (three agreeing refuters for the broad default) — a same-agent re-read is most circular exactly where a rewrite happened. Then run the three pre-stamp checks — semantic re-check (`references/semantic-checks.md`), structural re-validation (`python3 .claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"` over the touched pages), and merge content conservation — bounded to three rounds per page; a page still unfaithful after three rounds is set `needs-update`, and an oscillating fix stops immediately.
   - **Central locator-format pass** (after a fanned-out audit, before any stamp): centrally re-verify every `#page=N` and section anchor against the raw, normalize the citation format, and apply all shared-file writes and the data-list quorum from this top-level agent, never nested in a fan-out subagent.
   - **Execution order for a rewritten page:** (1) apply the fixes (Step 7); (2) re-fact-check against the raw; (3) the three pre-stamp checks within the three-round cap; (4) the central locator-format pass; (5) set status / stamp.
   - **Set `verified`** only when, after the fixes and the re-check, the page is fully faithful to its raw with confirmed full-text coverage (for a book, of its scoped range) and every non-obvious claim has passed its refuter tier — then stamp `verified_hash:` with `body_hash.py` (which masks any `*[unverified]*` claims that remain), first confirming well-formed `---` delimiters; abort the promotion and report a Critical rather than writing an empty or unverified hash. **Set `needs-update`** when the page carries an unresolved problem (a residual issue beyond audit's reach, a coverage failure, a confirmed defect audit cannot safely correct in-pass, or a genuine unresolved cross-source contradiction), with a `Contradictions`/`Tensions` entry or a one-line `needs_update_reason:` — a precise hand-off, appended if one already exists. Never resolve a contradiction by deleting one side.
   - **Leave alone what you only judged.** A certified page audit read and did not edit keeps its status, `verified_hash:`, and `updated:` untouched — nothing changed and nothing was re-checked, so there is nothing to re-stamp. Passing Step 4 is not an event the page records.

9. **Run a confirming lint.** Only when Steps 7–8 mutated at least one page — a content fix (split, merge, rewrite), a status change, or a verification-neutral re-stamp. Audit's own edits leave touched pages in a state the Step 1 lint no longer covers, so re-run `lint` in full to confirm the edits introduced no structural drift (broken links, malformed pipes, hash mismatches, index drift) and to let lint apply the mechanical fixes it owns. This is composition, not a new check: it is the same `lint` skill, run again over a wiki audit has since changed. Fold any finding it raises about a page this run touched back into Step 7's fix list and resolve it before finalizing; a finding lint cannot mechanically fix goes to the user with the rest of Step 10's decisions. Skip this step entirely when audit changed no page — there is nothing new for lint to see.

10. **Finalize the report; update index, hot, and log.** Set the report's `result:` and `pages_pending:` from what Steps 7–8 actually left behind, per the definitions in `CLAUDE.md` → Audit preconditions — computed, never left at the placeholder, since a successor pass and `cleanup` gate on it the way audit gates on lint's and consistency's. Then reconcile the draft report to what Steps 7–8 actually did: for each page audit set out to promote or demote, record the actual outcome (promoted / aborted-promotion / downgraded-to-Warning / needs-update) in **Status changes applied**, and drop any page from **Verification proof** that ended non-`verified` — a page that failed the post-rewrite re-check and became `needs-update` must not be left certified as promoted. Then, when Steps 7–8 created or removed a page (a split adds one, a merge removes one, a support-link removal can orphan one), update `1-wiki/index.md` to match. When a merge or support-link removal changed any page's `sources:` list, apply the shared bookkeeping in `.claude/skills/multi-skill/references/dependent-cascade.md`: sync `sources:`, recompute `source_count:` as the resulting list length (never a blind ±1), and keep the `Sources` callout in step. Do **not** autonomously set `single_source_stub: true` on a synthesis a removal leaves at one source — that flag records a deliberate user decision (`CLAUDE.md` → Synthesis pages); set the page `needs-update` naming the lost support instead. Finally update `hot.md` (a Recent-activity entry, newest-first) and prepend the log entry. Record which sub-runs this invocation performed — lint and consistency at Steps 1–2, the confirming lint at Step 9 — so the report shows whether each precondition was reused or freshly produced.

```markdown
## [YYYY-MM-DD HH:MM] audit | {N} findings ({C} critical, {W} warning, {I} info)
- Saved: [[2-outputs/audit/audit-YYYY-MM-DD-HHMM.md|audit-YYYY-MM-DD-HHMM]]
- Promoted to verified: [[1-wiki/concepts/self-attention.md|self-attention]] (or "none")
- Set needs-update: [[1-wiki/concepts/positional-encoding.md|positional encoding]] (or "none")
```

## Worked example

User invokes audit on a wiki of 14 concept/entity pages, 5 source pages, 1 synthesis. Most pages are `verified` — ingest certified their claims as it wrote them — and two are `needs-update`. The newest lint report is clean apart from those two.

Step 4 reads every page, certified or not, and produces:

- **Warning (2):** [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] is `verified` and every claim on it holds, but it covers two distinct ideas; recommend splitting. [[1-wiki/concepts/layer-norm.md|layer norm]] and [[1-wiki/concepts/layer-normalization.md|layer normalization]] are near-duplicates; recommend merging. Neither is visible from inside a single claim, and neither is a reason to doubt one — this is the work only audit does.
- **Critical (1):** a `Not This` bullet on [[1-wiki/concepts/positional-encoding.md|positional encoding]] generalizes over a table it cites one cell of, and reads stronger than that cell could support. A specific, refutable doubt, so it becomes cause for Step 5 rather than a fix applied on the spot.
- **Info (1):** [[1-wiki/concepts/residual-connection.md|residual connection]] carries one `*[unverified]*` claim left by an ingest that could not reach its second source's raw — a standing Step 5 cause.

Step 5 opens two raws: the one behind the doubted claim and the one behind the marked claim. Three refuters recompute the whole table and agree the doubted claim is false of the aggregate; the marked claim checks out. Step 8 sets status: `positional encoding` goes `needs-update` carrying the recomputed derivation in its `needs_update_reason:` (the correction spans the source page too, so it is not a safe in-pass rewrite), and `residual connection` has its marker cleared and is re-stamped. Audit carries out the split and the merge under the `supersede` procedure, quarantining the prior versions; each split-off page earns its own status from its own fact-check rather than inheriting the parent's stamp. (A page slated for a merge is not also independently promoted — structural retirement governs.) The other eleven certified pages are read, judged sound, and left byte-identical.

A second run, in `partial` mode, exercises the marker machinery. [[1-wiki/concepts/self-attention.md|self-attention]] is `verified` but carries one `*[unverified]*` claim whose `#page=N` anchor is already at git HEAD (left by a prior committed run); audit reopens the raw, the claim checks out, so it clears that marker and re-stamps `verified_hash:` — the page returns to fully-clean `verified`. On the same run a `missing_reciprocal_contradiction` finding needs a mirror bullet authored onto [[1-wiki/concepts/layer-normalization.md|layer normalization]], also `verified`; audit writes the reciprocal bullet with a new `#page=N` anchor and confirms the disagreement against the raw, but the anchor is new-versus-HEAD, so it leaves that bullet `*[unverified]*` rather than self-re-stamping — the page stays `verified` with that one pending delta, and the next `partial` audit (after this run commits) clears it.

## Edge cases

- **A note is accurate but too broad.** When the fact-check makes the split boundary clear, audit splits it following the `supersede` procedure rather than leaving one sprawling page in place. When the boundary is genuinely ambiguous, audit downgrades to a Warning and leaves the page for the user.
- **A source page is wrong.** Audit sets the source page and the affected concept/entity pages `needs-update`; a full source-page rebuild from the raw is a job for ingest's existing-source mode, so audit flags that rather than re-extracting the raw itself.
- **A claim distorts the source by generalizing from the cell it cites.** A summary or comparison claim can be true of the single cell it cites yet false of the whole table — Step 5 recomputes the full set rather than confirming the cited cell (`references/verification-spec.md`). When confirmed, the faithful correction usually requires re-deriving the aggregate and often spans the source page and the pages that inherited the framing, so it is rarely a safe in-pass fix: set every affected page `needs-update` with a `needs_update_reason:` carrying the recomputed derivation (the distortion-disposition rule, `references/apply-fixes.md`).
- **A page has no resolvable source.** A concept/entity page whose `sources:` is empty (or a synthesis with none) cannot be fact-checked, so it can never be set `verified`. Set it `needs-update` with a `needs_update_reason:` naming the missing support, or surface removal as a Warning for the user (`forget` territory); audit does not auto-remove a page.
- **A contradiction is productive.** Preserve it; do not treat all contradictions as errors, and never resolve a contradiction by deleting one side.

## Limits

- Audit acts autonomously — it carries out content fixes (splits, merges, rewrites, support-link changes) following the `supersede` and ingest existing-source-mode procedures and preserving the prior version, then sets status. This autonomy is a deliberate departure from the foundation design's human-commit-point model (see Purpose). Its scope model, the terminal-verification invariant, and the marker mechanics are defined once in Verification Model.
- **Audit judges pages; it does not re-certify claims by routine.** Re-asking what the authoring run already asked and answered is not thoroughness — it is the double spend this split removes, and it crowds out the whole-page work only audit does. Re-open a raw on the Verification Model causes or in `full` mode, not to reassure yourself about certified, hash-matched content.
- **But never act on content without grounding.** The moment a finding would change what a page says — a rewrite, a dropped bullet, a corrected claim, a new status — it needs the raw, at the tier `verification.md` sets. A page-level judgement (split, merge, connection, voice) is grounded in the pages themselves, read in full against the inventory; never in recollection or a prior report's say-so.
- Never drop a bullet on a single fact-check. Bullet removal requires three independent confirming re-reads of the raw; on any found support or disagreement, preserve the bullet — add the citation the support enables, or mark `*[tentative]*` and set `needs-update` — rather than deleting. Deletion is the last resort (`references/apply-fixes.md`).
- A confirmed defect always ends the run acted on — fixed when the correction is a safe in-pass determinate edit, set `needs-update` with a derivation when it is not (the distortion-disposition rule). A distortion audit confirms but cannot safely correct in-pass is never force-fixed with a risky rewrite and never left as a passive finding for the user. The only confirmed defect handed back as a bare Warning is a genuinely ambiguous structural call audit cannot settle.
- Audit does not edit `CLAUDE.md`, skill files, or scripts. Schema or skill drift is `consistency`'s domain. The exceptions are the three agent-writable data files `.claude/skills/multi-skill/hyphenation-lists.md`, `.claude/skills/multi-skill/unlinked-mention-ignore.md`, and `.claude/skills/multi-skill/alias-detect-exempt.md`, which audit grows under the Step 7 sub-agent-verification gate — data, not script logic (`CLAUDE.md` → Stay in your lane). The folder holds a fourth data file, `.claude/skills/multi-skill/pagination-map.md`, which audit **reads** (a `p. M` locator is checked against it) but does **not** maintain — it is registered on ingest after a human eyeballs a rendered footer. An audit that meets an unregistered raw reports it (`pagination_map_unregistered`) rather than guessing its pagination.
- A `verified` stamp certifies the page body against the raw *as read at verification time*. `verified_hash:` binds the page body, not the raw, so a raw silently re-OCR'd, re-curated, or replaced under the same stem after verification is not detected. This rests on the `0-raw/` immutability invariant. When a fact-check notices the raw diverging from what a page records (offsets shifted, sections renumbered, different text at a cited `#page=N`), set the page `needs-update` naming the suspected raw change rather than re-verifying against it.
- Never modify `0-raw/`.
