# Verification evidence ledger

This is the canonical schema for durable bullet evidence shared by `ingest` and `audit`. It defines what a retained refuter result certifies, when `audit partial` may reuse it, and how a run proves that every planned claim and reader reached a terminal state. Human-readable Markdown reports remain the authority; there is no mutable global evidence database.

## Contents

- Trust boundary
- Canonical claim identity
- Evidence rows
- Reuse and invalidation
- Audit page readers
- Result and reconciliation rules
- Recovery and validator

## Trust Boundary

A **bullet pair** certifies only one exact logical Markdown bullet against its exact ordered locators and raw bytes: the locator role confirms where the evidence is; the entailment role confirms what that evidence supports. A **page pair** is fresh audit evidence about the complete final page: attribution, consistency, omissions, contradictions, and argument flow. Neither pair substitutes for the other.

Cross-run reuse is allowed only from a producer report that is committed and clean at Git HEAD. Record its repo-relative path and Git blob ID. An uncommitted report from a prior operation, a modified report, or a report without a terminal reconciliation supplies no credit. The current coordinator may use its own sealed rows during the same uninterrupted operation. If two terminal reports conflict for one exact generation, neither wins: invalidate that generation and backfill both roles.

Only the top-level coordinator writes ledger rows. Readers return records; they never append to reports. The coordinator freezes manifests before dispatch, validates complete role batches, writes through one report update, and finalizes the terminal reconciliation atomically. A torn or incomplete final row makes the report non-reusable.

## Canonical Claim Identity

Parse body bullets in document order, including continuation lines, markers, citations, and locators. Frontmatter and callout headings are context, not claim rows. Every bullet receives one manifest occurrence.

Canonical text uses UTF-8 and LF line endings. Do not trim whitespace or normalize Unicode. Remove only the literal process marker `*[unverified]*`; keep `*[tentative]*`, `*[disputed]*`, punctuation, whitespace, and citation text. Store the original full logical bullet as `claim_text` and its byte length as `claim_bytes`; truncation or an ellipsis substituted for content invalidates the row.

Within one page path and callout block, group byte-identical canonical bullets and assign `duplicate_ordinal` by body occurrence order, starting at 1. Any insertion, deletion, or reorder inside an identical group invalidates that group. A cross-callout or page-path move invalidates the occurrence.

Build `claim_instance_id` as the lowercase SHA-256 of canonical JSON with sorted keys and compact separators over:

```json
{
  "schema_version": 1,
  "page_path": "1-wiki/concepts/example.md",
  "page_type": "concept",
  "page_title": "Example",
  "semantic_frontmatter": {},
  "callout_type": "idea",
  "callout_id": "idea",
  "duplicate_ordinal": 1,
  "claim_text_canonical": "> - Full bullet...",
  "locators": [],
  "raw_dependencies": [],
  "context_digest": "64 lowercase hex"
}
```

Paths are resolved from the repository root and stored repo-relative with `/` separators. Reject symlink escapes and case aliases. `locators` preserve textual order and exact authored target/display plus raw path, physical page, printed page, and structural anchor. `raw_dependencies` are ordered by repo-relative path and record SHA-256 of the current raw bytes.

The context digest binds the page title/subject, page type, all semantic frontmatter (`sources`, `frames`, attachments/provenance and other meaning-bearing fields), callout type, Sources/support callout, pagination-map entries used, and declared claim dependencies. A causal, comparative, aggregate, generalization, relationship, or framework claim declares the exact claim instances it depends on. If complete dependency closure cannot be proven, its context is the full semantic page digest and any semantic page edit invalidates it. Mechanical stamp/date fields are excluded.

## Evidence Rows

Each retained report contains one fenced `jsonl` ledger section. Every JSON object has `schema_version: 1`, `row_type`, `run_id`, and `row_id`.

- `manifest`: planned source, page, claim, bullet-role, page-reader, scanner, and status-write counts plus the final relationship epoch.
- `claim`: the complete identity payload above, `classification: required|exempt`, and a closed exemption reason when exempt: `obvious_definitional`, `own_voice_judgement`, `empty_placeholder`, or `verification_neutral_bookkeeping`.
- `bullet_verdict`: `claim_instance_id`, `role: locator_bullet|entailment_bullet`, role version, distinct agent/run identity, blindness provenance, `verdict: hold|refute|cannot_confirm`, full evidence and quote, physical page/range, reasoning, confidence, correction, and `quote_validated`.
- `claim_terminal`: one terminal disposition per manifest occurrence: `exempt`, `reused_hold`, `backfilled_hold`, `refute`, `cannot_confirm`, or `invalidated`, with both role row IDs when required and the producer report/blob when reused.
- `page_reader`: audit only; page path/generation, role, distinct reader identity, verdict, exact defect claim IDs/callouts, and full evidence.
- `status_write`: audit only; page generation, before/after status, pre/post semantic hashes, marker action, and final `verified_hash` or `needs_update_reason`.
- `reconciliation`: terminal counts and report result.

Readers are blind: the locator and entailment reader for one unit do not receive each other's prompt, evidence, verdict, adjudication, prior findings, or cached rows. A batch may carry several same-raw claims, but it returns one full record per claim. A pooled batch/page verdict, missing record, truncated evidence, duplicate role, mixed generation, or malformed record is pending, never HOLD.

Before acting on or reusing HOLD, mechanically re-extract its literal quote from the exact raw physical page/range. Collapse PDF line-wrap whitespace only for this literal check. A Boolean attestation alone is insufficient. Semantic adjudication remains the coordinator's: verified text can still fail to entail the claim.

## Reuse And Invalidation

Only an adjudicated `hold/hold` pair is reusable. Reuse requires an exact `claim_instance_id`, ledger and both role versions, producer report/blob, ordered locators, context digest, and raw path/SHA set. Never combine one historical role with one new role. Missing, legacy, versionless, malformed, truncated, nonterminal, dirty-report, changed-raw, changed-context, or one-sided evidence is backfilled through both fresh roles.

A changed/new bullet invalidates its occurrence. Changed raw bytes invalidate every dependent occurrence. A context or dependency change invalidates the affected occurrence; the full-page fallback makes uncertainty conservative. A page-level REFUTE does not automatically poison unrelated locally valid bullet rows, but a `bullet_local` defect revokes the named pair and a `cross_bullet` defect records its exact dependency set as a continuing page blocker.

Results launched in an audit epoch that later becomes `INVALIDATED` are discarded cost and never survive. A new epoch may admit exact-valid rows only from a previously finalized terminal report, never from the just-invalidated epoch.

`audit partial` may reuse exact-valid pairs. `audit full` is cold: it creates two new bullet-role rows for every required claim and records `reused: 0`. Authoring evidence never stamps a page, and reusable evidence never preserves an old stamp across a source/support change.

## Audit Page Readers

Every page actually audited receives two fresh blind readers tied to the final semantic page digest and final `READY(n)`:

- `locator_page`: source identity, exact locator truth, and clause-to-source assignment across the complete page.
- `entailment_argument_page`: meaning, scope, subject/reason attachment, aggregates, contradictions, internal consistency, and argument flow across the complete page.

Each receives the complete page and complete current raw manifest, not selected snippets or bullet verdicts. Each returns `hold|refute|cannot_confirm` with exact defects and full evidence. Both must HOLD before promotion or marker clearance. A page HOLD never supplies missing bullet evidence.

Classify a page failure as `bullet_local`, `cross_bullet`, or `page_only`. Repair a bullet-local defect and rerun both bullet roles. A cross-bullet defect records its dependency set; locally valid rows may remain, but the page remains blocked. A page-only defect preserves locally valid rows but blocks promotion. Every semantic repair reruns both fresh page roles.

## Result And Reconciliation Rules

Let `C` be planned claims, `X` exemptions, `R` required claims, `E` exact reused pairs, `B` terminal backfills, `U` terminal unresolved claims, and `P` audited pages:

```text
C = X + R
R = E + B + U
locator_backfills = entailment_backfills = required pairs needing backfill
page_locator_rows = page_entailment_rows = P
planned = terminal + pending
```

Every planned source, page, claim, bullet role, page reader, scanner obligation, and status write needs exactly one terminal final-epoch disposition.

- `complete`: every equation reconciles, every status write landed, and `pending = 0`; pages may terminally be `needs-update`.
- `unconverged`: all work is terminal, but the bounded repair loop exhausted or oscillated and affected pages ended safely non-verified.
- `incomplete`: any planned work is missing, undispatched, nonterminal, malformed, unparseable, stale-epoch, scanner-blocked, or unreconciled.

An empty reader pipeline is not completion. If runnable work remains and active readers are zero, dispatch a backstop before adjudicating. “Sources were waved” is not evidence that every claim was read.

## Recovery And Validator

Run `validate_verification_ledger.py` after manifest construction, after every repair cycle, and before final report/status completion. The validator checks structure, exact hashes/lengths, duplicate cardinality, role separation, literal quote location, terminal producer provenance, inventories, and equations. It never decides whether evidence semantically entails a claim and never edits wiki content.

On recovery, ignore a torn tail only to diagnose the interrupted report; the report remains `incomplete` and supplies no reusable evidence until the coordinator validates and writes a new terminal reconciliation. Resume by recomputing current page/raw/context identities and dispatching only missing or invalid obligations.
