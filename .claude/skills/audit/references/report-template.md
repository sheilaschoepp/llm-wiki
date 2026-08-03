# audit — Report Template (Step 6)

The report `audit` creates before dispatch and finalizes at Step 9. Use `audit-YYYY-MM-DD-HHMM.md`, or `audit-YYYY-MM-DD-HHMM-full.md` in full mode, with `TZ='UTC' date '+%Y-%m-%d-%H%M'`. The Markdown report and its bounded JSONL ledger are one atomic retained artifact.

Initialize the file with `result: incomplete`, nonnumeric marker placeholders, frozen manifests, and planned counts before dispatch. `check_wiki.py`'s `audit_burndown_stalled` check deliberately ignores the nonnumeric placeholders. Replace them with numeric final values only after all obligations reconcile. A crash leaves a truthful incomplete report; a bare report file is never completion.

````markdown
---
type: audit
date: YYYY-MM-DD
mode: partial | full
result: incomplete | unconverged | complete
ledger_schema: 1
pending: N
markers_pending: pending
inherited_cleared: "pending"
---

# Audit - YYYY-MM-DD-HHMM

## Summary
- Mode: partial | full
- Result: incomplete | unconverged | complete
- Critical: N; Warning: N; Info: N
- Pages: {planned} planned, {terminal} terminal; verified {N}, needs-update {N}
- Claims: {planned} = {exempt} exempt + {required} required; reused pairs {N}; backfilled pairs {N}; unresolved terminal {N}; pending {N}
- Final-epoch readers: locator bullets {N}; entailment bullets {N}; locator pages {N}; entailment/argument pages {N}; escalations {N}
- Invalidated spend: {epochs}; {claims}; {calls}. Cost only, never final evidence.
- Worklist by class: carried {N} = resolved {N} + marker-pending {N} + user-decision {N}
- `unlinked_page_mention`: scanner groups {N}; rescanned exact spans {N}; genuine links {N}; generic/ignored {N}; near-alias or hyphenated spans found manually {N}; adjacent-token boundary false matches {N}. Scanner group count is not backlog size.

## Frozen manifests and reconciliation
- Final relationship epoch: READY(n)
- Sources: {complete repo-relative path + raw SHA-256 inventory}
- Pages: {complete scoped page path + final semantic digest inventory}
- Claims: {complete claim count by page; no sampled or truncated bullets}
- Reader obligations: {planned bullet roles, page roles, scanners, status writes}
- Equations: `claims = exempt + required`; `required = reused + backfilled + unresolved`; `planned = terminal + pending`
- Validator: `python3 .claude/skills/multi-skill/scripts/validate_verification_ledger.py {this report} --repo-root .` → status {0|1}; stdout {JSON}; stderr {empty}. Status 0 or 1 is valid checker execution; exit 2, traceback, empty/unparseable output, or wrong root is invalid.
- Wiki checker: `python3 .claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"` → status {0|1}; stdout {JSON finding count}; stderr {empty}. A missing-index result or single-digit artifactual scan means the invocation is wrong.

## Relationship-integrity barrier
- Post-repair consistency: {report/run}
- Complete lint including LLM walk: {report/run}
- Whole-inventory relationship sweep: {run}
- Required missing targets: {initial} → repaired {N} → final 0
- Allowed dangling links: {page; context; target; policy class} (or "none")

## Raw acquisition evidence
- Planned raws: record the exact count.
- Reused raws: record each raw path, current SHA-256, producer report path, producer Git blob, pack payload SHA-256, evidence/coverage versions, pagination-map-section SHA-256, read scope, probe-revalidation result, and reused disposition.
- Backfilled raws: record each reopened raw path, reason it was reopened, final SHA-256, read scope, positive coverage probes, evidence/coverage versions, pagination-map-section SHA-256, and backfilled disposition.
- Reconciliation: `planned_raws = reused_raws + backfilled_raws`; `pending_raws = 0`. Any invalid, missing, duplicate, or unreconciled raw obligation makes the report `incomplete`.
- Report-embedded packs: retain the exact manifest and complete page-addressed payload for every backfilled raw. Do not copy a reused pack forward; bind it to its committed producer report and Git blob.

## Bullet evidence
- Reused rows: {claim ID; producer report path; Git blob; role versions; quote re-extraction result} (or "none"; always none in full mode)
- Backfilled rows: {claim ID; locator row; entailment row; terminal disposition}
- Exemptions: {claim ID; closed exemption reason}
- Refute/cannot-confirm rows: {claim ID; exact failure and safe terminal disposition}
- Every claim in scope has one claim row and one terminal row, including clean claims. Ask: could the marker/status decision be reconstructed tomorrow from this ledger alone?

## Fresh page readers
- {page path; final semantic digest; READY(n)} — locator page: {HOLD|REFUTE|CANNOT_CONFIRM}; entailment/argument page: {HOLD|REFUTE|CANNOT_CONFIRM}
- Defects: {bullet_local|cross_bullet|page_only; exact claim IDs/callouts; repair generation}
- Both page roles are fresh and blind on every scoped page; neither receives bullet verdicts or the counterpart output.

## Status changes applied
- Promoted to `verified`: {pages and final hashes} (or "none")
- Set `needs-update`: {pages and precise reasons} (or "none")
- Markers cleared: {claim IDs; HEAD-anchor proof; atomic-write proof} (or "none")
- Markers retained/authored: {claim IDs and reason} (or "none")

## Verification proof
- {page} — full-text coverage; late-section proof; exact locator proof; bullet terminal count; both page HOLD row IDs; postwrite structural check; final hash/reason
- A page is not promoted from page-level HOLD alone, bullet-level HOLD alone, or an invalidated epoch.

## Invalidated verification spend
- {epoch; invalidating graph/support/provenance/page-inventory edit; discarded pages/claims/calls} (or "none")

## Critical
- {yes/no audit assumption; raw evidence; applied status/fix}

## Warning
- {finding; final disposition}

## Info
- {verified candidate | missing page | next source; explanation}

## Verification Candidates
- {enumerated staged re-verification or ignore-list quorum only} (or "none")

## Recommendations
- {only criterion-changing re-checks or genuine decisions} (or "none")

## Self-report
- {specific limitation → upgrade} (or "none noted this run")

<!-- verification-ledger:start -->
```jsonl
{"schema_version":1,"row_type":"manifest","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","mode":"partial","planned_sources":0,"planned_pages":1,"planned_claims":1,"planned_bullet_roles":2,"planned_page_readers":2,"planned_scanners":1,"planned_status_writes":1}
{"schema_version":1,"row_type":"claim","row_id":"...","run_id":"...","claim_instance_id":"...","page_path":"1-wiki/...","page_type":"concept","page_title":"...","semantic_frontmatter":{},"callout_type":"idea","callout_id":"idea","duplicate_ordinal":1,"claim_text":"> - full untruncated bullet","claim_bytes":27,"locators":[],"raw_dependencies":[],"context_digest":"...","classification":"required"}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"locator_bullet","role_version":"...","agent_id":"...","blind_to":[],"verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"entailment_bullet","role_version":"...","agent_id":"...","blind_to":[],"verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"claim_terminal","row_id":"...","run_id":"...","claim_instance_id":"...","disposition":"backfilled_hold","role_rows":["...","..."]}
{"schema_version":1,"row_type":"page_reader","row_id":"...","run_id":"...","page_path":"1-wiki/...","page_generation":"...","role":"locator_page","agent_id":"...","verdict":"hold","defects":[],"evidence":"..."}
{"schema_version":1,"row_type":"page_reader","row_id":"...","run_id":"...","page_path":"1-wiki/...","page_generation":"...","role":"entailment_argument_page","agent_id":"...","verdict":"hold","defects":[],"evidence":"..."}
{"schema_version":1,"row_type":"status_write","row_id":"...","run_id":"...","page_path":"1-wiki/...","page_generation":"...","before_status":"draft","after_status":"verified","pre_semantic_hash":"...","post_semantic_hash":"...","marker_action":"none","verified_hash":"..."}
{"schema_version":1,"row_type":"scanner","row_id":"...","run_id":"...","scanner":"check_wiki","target":"1-wiki","status":0,"stdout_json":true,"stderr_runtime_error":false,"terminal":true}
{"schema_version":1,"row_type":"reconciliation","row_id":"...","run_id":"...","result":"complete","pending":0,"planned_pages":1,"terminal_pages":1,"pending_pages":0,"planned_sources":0,"terminal_sources":0,"pending_sources":0,"planned_claims":1,"terminal_claims":1,"pending_claims":0,"planned_bullet_roles":2,"terminal_bullet_roles":2,"pending_bullet_roles":0,"planned_page_readers":2,"terminal_page_readers":2,"pending_page_readers":0,"planned_scanners":1,"terminal_scanners":1,"pending_scanners":0,"planned_status_writes":1,"terminal_status_writes":1,"pending_status_writes":0}
```
<!-- verification-ledger:end -->
````
