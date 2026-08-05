# audit — Report Template (Steps 1, 6, And 9)

The report `audit` creates before dispatch and finalizes at Step 9. Use `audit-YYYY-MM-DD-HHMM.md`, or `audit-YYYY-MM-DD-HHMM-full.md` in full mode, directly under `2-outputs/audit/`, with frontmatter `type: audit`; nested/suffix-matched folders and crossed type/folder pairs are invalid. The Markdown report and bounded JSONL ledger are one atomic artifact.

Initialize the file with `result: incomplete`, nonnumeric marker placeholders, and pending manifest/count fields before the first gate or reader dispatch. Freeze the initial Warning census after Step 1 and write the current verification manifests at Step 5. `check_wiki.py`'s `audit_burndown_stalled` check deliberately ignores the nonnumeric placeholders. Replace them with numeric final values only after all obligations reconcile. A crash leaves a truthful incomplete report; a bare report file is never completion.

## Contents

- Summary and frozen reconciliation
- Neutral transactions and Warning occurrence ledger
- Relationship, raw, bullet, page, and status evidence
- Findings, pending obligations, completion proof, and self-report
- Bounded JSONL verification ledger

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
- Worklist actionable units: carried {N} = terminal {N} + pending {N}; non-mention terminal = `fixed` {N} + `standing_ignore` {N} + `verified_not_applicable` {N} + `needs_update` {N}; initial scanner Warnings {N}; final scanner Warnings {N}
- `unlinked_page_mention`: scanner groups {N}; exact occurrences {N}; zero-match defects {N}; pre-census standing-ignore entries preserved {N}; `genuine_wrap` {N}; `accepted_suppression` {N}; `graph_repair` {N}; `graph_ignore` {N}; one-to-one `superseded`/`rekeyed` pairs {N}; pending {N}; final scanner Warnings {N}.

## Baseline captured before edits
- Git state: `{git status --porcelain=v1 -z}` byte digest and exact path/status inventory.
- Existing changes: exact diff/blob evidence for every writable path; ownership boundary and paths Audit may edit.
- Warning baseline: `.claude/skills/audit/scripts/capture_warning_baseline.py 2-outputs/audit/baselines/audit-{run-id}.json --repo-root . --run-id {run-id}` with the supported default Python runtime → status 0; retain the new direct-child path, artifact SHA-256, returned `baseline_id`, matching run ID, and `evidence_context_sha256`. Its payload freezes Warning/enumerator inventories, affected-page preimages, ignore bytes, and maintained target/canonical/relationship-rule hashes before edits.

## Frozen manifests and reconciliation
- Final relationship epoch: READY(n)
- Initial Warning census: {check ID; page/target; exact occurrence identity or report fingerprint}
- Final Warning census: {post-bookkeeping lint run; parseable; Warning count 0 for complete}
- Sources: {complete repo-relative path + raw SHA-256 inventory}
- Pages: {complete scoped page path + final semantic digest inventory}
- Claims: {complete claim count by page; no sampled or truncated bullets}
- Reader obligations: {planned bullet roles, page roles, scanners, status writes}
- Equations: `claims = exempt + required`; `required = reused + backfilled + unresolved`; `planned = terminal + pending`; `initial Warning findings = initial non-mention fingerprints + initial mention groups`; `introduced Warning findings = introduced non-mention fingerprints + introduced mention groups`; every mention group expands through native parity; `initial non-mention + introduced non-mention = terminal non-mention + pending non-mention`; `initial expanded mentions + introduced mention occurrences = terminal mentions + pending mentions`
- Validator: `.claude/skills/multi-skill/scripts/validate_verification_ledger.py {this report} --repo-root .` with the repository-supported default Python runtime → status {0|1}; stdout {JSON}; stderr {empty}. Exit 2, traceback, empty/unparseable output, or wrong root is invalid.
- Wiki checker: `.claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"` with that runtime → status {0|1}; stdout {JSON finding count}; stderr {empty}. A missing-index or single-digit artifactual scan means the invocation is wrong.

## Verification-neutral transactions
- {neutral_page_transactions row ID; page path; preimage/postimage SHA-256; exact postimage_bytes_base64; unchanged before/after status; final verified_hash or null; exact ordered baseline occurrence IDs}
- Suppression batches: {evidence-context SHA-256; canonical full-input SHA-256; batch digest; ordered occurrence IDs; two hash-bound reader rows; exact HOLD/HOLD appends}
- Counts/prose never substitute for the exact reconciliation array. The completion validator replays frozen baseline spans; verification/status rows are absent from a neutral-only verified host only when the shared validator admits its exact raw-proof bridge.

## Warning occurrence ledger
- {occurrence ID; check ID; page/target; page preimage hash; exact span/fingerprint; initial state; terminal disposition; final scanner fingerprint or absence proof}
- Reconciliation: `initial expanded occurrences + introduced occurrences = terminal occurrences + pending occurrences`; non-mention fingerprints reconcile separately; both pending counts are 0 for `complete`.
- Exact closure arrays in the JSONL reconciliation row: `warning_fingerprints`, `mention_occurrences`, `suppression_batches`, `suppression_reader_verdicts`, and `neutral_page_transactions`. Non-mention dispositions are exactly `fixed|standing_ignore|verified_not_applicable|needs_update`. Mention semantic dispositions are exactly `genuine_wrap|accepted_suppression|graph_repair|graph_ignore`; frozen standing ignores are applied before enumeration and therefore have no occurrence disposition row. An identity change adds one old `superseded` row with `rekeyed_to` and one new `rekeyed` row with reciprocal `rekeyed_from` plus a semantic `final_disposition`; the relationship is bijective. Use `[]`; counts/prose do not substitute.

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
- JSONL source terminals: emit one `source` row for every path in the union of claim raw dependencies and every scoped page reader's complete transitive `raw_manifest`, with canonical `raw_path`, current `sha256`, `disposition: available|cannot_confirm`, and evidence. Counts and path/SHA sets equal this union exactly, including zero-claim pages.

## Bullet evidence
- Reused rows: {exact claim ID; producer report path; Git blob; exact HOLD row IDs; role versions; dependency path/SHA discovery; quote re-extraction result} (or "none"; always none in full mode). The producer must use the exact direct-folder/type pair. Discover its source rows by exact dependency path/SHA; do not demand or record producer source row IDs. Reuse imports only the matching claim proof.
- Backfilled rows: {claim ID; locator row; entailment row; terminal disposition}
- Exemptions: {claim ID; closed exemption reason}
- Refute/cannot-confirm rows: {claim ID; exact failure and safe terminal disposition}
- Every claim in scope has one claim row and one terminal row, including clean claims. Ask: could the marker/status decision be reconstructed tomorrow from this ledger alone?

## Fresh page readers
- {page path; final semantic digest; READY(n); complete ordered transitive raw_manifest of exact raw path/SHA pairs} — locator page: {HOLD|REFUTE|CANNOT_CONFIRM}; entailment/argument page: {HOLD|REFUTE|CANNOT_CONFIRM}
- Defects: {bullet_local|cross_bullet|page_only; exact claim IDs/callouts; repair generation}
- Both page roles are fresh and blind on every scoped page; neither receives bullet verdicts or the counterpart output.

## Status changes applied
- Promoted to `verified`: {pages and final hashes} (or "none")
- Set `needs-update`: {pages and precise reasons} (or "none")
- Markers cleared: {claim IDs; HEAD-anchor proof; atomic-write proof} (or "none")
- Markers remaining: none for `complete` or `unconverged`; exact pending identities only for `incomplete`

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

## Pending obligations
- {exact occurrence, claim, page, reader role, batch, or scanner identity plus hard external failure} (must be "none" for `complete`)

## Recommendations
- {non-blocking information outside the current authored tier} (or "none"; never current-run work or a requested decision)

## Completion proof
- Post-bookkeeping final lint: {run}; status 0; result clean; audit-blocking 0; stdout {parseable JSON}; stderr {empty}; Warning count 0; carried 0; introduced 0; stale-target applications 0
- Frozen Warning reconciliation: scanner-group censuses and actionable-unit ledgers both balance; all pending counts are 0
- Final full-ledger validator: `.claude/skills/multi-skill/scripts/validate_verification_ledger.py {this report} --repo-root .` with the supported default Python runtime → status 0; stdout {JSON}; stderr {empty}
- Completion validator: `.claude/skills/audit/scripts/validate_audit_completion.py {this report} --repo-root .` with that runtime → status 0; stdout {JSON}; stderr {empty}. It reruns the native checker and rejects any live Warning/blocking status or process marker.
- Running every planned batch is not completion evidence; any residual Warning keeps the report `incomplete`.

## Self-report
- Follow `.claude/skills/multi-skill/references/self-report.md`: {specific limitation that bit audit this run → upgrade that would prevent it} (or "none noted this run")

<!-- verification-ledger:start -->
```jsonl
{"schema_version":1,"row_type":"manifest","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","mode":"partial","planned_sources":1,"planned_pages":1,"planned_claims":1,"planned_bullet_roles":2,"planned_page_readers":2,"planned_scanners":1,"planned_status_writes":1}
{"schema_version":1,"row_type":"source","row_id":"source-row","run_id":"...","raw_path":"0-raw/papers/example.pdf","sha256":"64 lowercase hex","disposition":"available","evidence":"Raw bytes present, hashed, and readable for this terminal source obligation."}
{"schema_version":1,"row_type":"claim","row_id":"...","run_id":"...","claim_instance_id":"...","page_path":"1-wiki/concepts/example.md","page_type":"concept","page_title":"Example","semantic_frontmatter":{},"callout_type":"idea","callout_id":"idea","duplicate_ordinal":1,"claim_text":"> - full untruncated bullet ([[0-raw/papers/example.pdf#page=1|sec. 1, p. 1]])","claim_bytes":78,"locators":[{"raw_path":"0-raw/papers/example.pdf","physical_page":1,"printed_page":1,"structural_anchor":"sec. 1"}],"raw_dependencies":[{"raw_path":"0-raw/papers/example.pdf","sha256":"64 lowercase hex"}],"context_digest":"same page_generation","classification":"required"}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"locator-row","run_id":"...","relationship_epoch":"READY(n)","claim_instance_id":"...","role":"locator_bullet","role_version":"...","agent_id":"...","blind_to":["entailment_bullet"],"verdict":"hold","quote":"...","quote_raw_path":"0-raw/papers/example.pdf","physical_page":1,"printed_page":1,"structural_anchor":"sec. 1","reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"entailment-row","run_id":"...","relationship_epoch":"READY(n)","claim_instance_id":"...","role":"entailment_bullet","role_version":"...","agent_id":"...","blind_to":["locator_bullet"],"verdict":"hold","quote":"...","quote_raw_path":"0-raw/papers/example.pdf","physical_page":1,"printed_page":1,"structural_anchor":"sec. 1","reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"claim_terminal","row_id":"...","run_id":"...","claim_instance_id":"...","disposition":"backfilled_hold","role_rows":["locator-row","entailment-row"]}
{"schema_version":1,"row_type":"page_reader","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","page_path":"1-wiki/concepts/example.md","page_generation":"...","raw_manifest":[{"raw_path":"0-raw/papers/example.pdf","sha256":"64 lowercase hex"}],"role":"locator_page","agent_id":"...","blind_to":["entailment_argument_page"],"verdict":"hold","defects":[],"evidence":"..."}
{"schema_version":1,"row_type":"page_reader","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","page_path":"1-wiki/concepts/example.md","page_generation":"...","raw_manifest":[{"raw_path":"0-raw/papers/example.pdf","sha256":"64 lowercase hex"}],"role":"entailment_argument_page","agent_id":"...","blind_to":["locator_page"],"verdict":"hold","defects":[],"evidence":"..."}
{"schema_version":1,"row_type":"status_write","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","page_path":"1-wiki/concepts/example.md","page_generation":"...","before_status":"draft","after_status":"verified","pre_semantic_hash":"same page_generation","post_semantic_hash":"same page_generation","marker_action":"none","pre_marker_count":0,"post_marker_count":0,"verified_hash":"..."}
{"schema_version":1,"row_type":"scanner","row_id":"...","run_id":"...","relationship_epoch":"READY(n)","scanner":"final_lint_post_bookkeeping","target":"1-wiki","status":0,"result":"clean","lint_result":"clean","audit_blocking_count":0,"stdout_json":true,"stderr_runtime_error":false,"warning_count":0,"carried_warning_count":0,"introduced_warning_count":0,"stale_target_applications":0,"terminal":true}
{"schema_version":1,"row_type":"reconciliation","row_id":"...","run_id":"...","result":"complete","pending":0,"warning_baseline_path":"2-outputs/audit/baselines/audit-run-id.json","warning_baseline_sha256":"64 lowercase hex","warning_baseline_id":"non-placeholder baseline ID","evidence_context_sha256":"64 lowercase hex","planned_pages":1,"terminal_pages":1,"pending_pages":0,"planned_sources":1,"terminal_sources":1,"pending_sources":0,"planned_claims":1,"terminal_claims":1,"pending_claims":0,"planned_bullet_roles":2,"terminal_bullet_roles":2,"pending_bullet_roles":0,"planned_page_readers":2,"terminal_page_readers":2,"pending_page_readers":0,"planned_scanners":1,"terminal_scanners":1,"pending_scanners":0,"planned_status_writes":1,"terminal_status_writes":1,"pending_status_writes":0,"initial_warning_findings":0,"initial_nonmention_warning_fingerprints":0,"initial_mention_groups":0,"expanded_mention_occurrences":0,"zero_match_scanner_defects":0,"introduced_warning_findings":0,"introduced_nonmention_warning_fingerprints":0,"introduced_mention_groups":0,"introduced_mention_occurrences":0,"terminal_nonmention_warning_fingerprints":0,"pending_nonmention_warning_fingerprints":0,"terminal_mention_occurrences":0,"pending_mention_occurrences":0,"warning_fingerprints":[],"mention_occurrences":[],"suppression_batches":[],"suppression_reader_verdicts":[],"neutral_page_transactions":[]}
```
<!-- verification-ledger:end -->
````
