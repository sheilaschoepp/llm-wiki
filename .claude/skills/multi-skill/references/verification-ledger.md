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

A **bullet pair** certifies only one exact logical Markdown bullet against its exact ordered locators and raw bytes: the locator role confirms where the evidence is; the entailment role confirms what that evidence supports. A **page pair** is fresh audit evidence about the complete final page: attribution, consistency, omissions, contradictions, and argument flow. Neither pair substitutes for the other. Its `page_generation` is the canonical semantic-page SHA-256 printed by `.claude/skills/multi-skill/scripts/validate_verification_ledger.py --page-generation {page}`, run with the repository-supported default Python runtime: exact UTF-8/LF page text with only terminal bookkeeping frontmatter (`created`, `updated`, `status`, `verified_hash`, `needs_update_reason`) and the process marker plus one following horizontal space excluded. That makes a marker/status/hash-only terminal write generation-neutral while any semantic page change invalidates the pair.

Cross-run reuse is claim-scoped, never report- or page-scoped. It is allowed only from the two HOLD rows and `backfilled_hold` terminal row bound to the same exact `claim_instance_id` in a producer report committed and clean at Git HEAD. The producer is exactly one Markdown file directly under the folder/type pair `2-outputs/audit/` + `type: audit`, or `2-outputs/ingest/` + `type: ingest-report`; the pairs are not interchangeable. Record its repo-relative path and Git blob ID. An uncommitted report from a prior operation, a modified report, a report outside those two directories, a mismatched folder/type pair, or a report without a terminal reconciliation supplies no credit. Unrelated claims in a producer never supply evidence for the selected claim: validate and import only the exact claim row, its exact terminal row, its actual source rows, and the two role rows that terminal names. The current coordinator may use its own sealed rows during the same uninterrupted operation. If committed terminal evidence REFUTEs or CANNOT_CONFIRMs that same exact claim identity, no selected producer wins by omission: invalidate the pair and backfill both roles.

The folder/type test is exact: the producer is a Markdown file whose POSIX parent is exactly `2-outputs/audit` with frontmatter `type: audit`, or exactly `2-outputs/ingest` with `type: ingest-report`. Nested paths, suffix matches, symlink aliases, and crossed pairs are invalid. Discover the producer source proof from each reused claim's exact dependency path/SHA pairs and require one matching producer `source` row per pair; neither the claim terminal nor current report records producer source row IDs.

Only the top-level coordinator writes ledger rows. Readers return records; they never append to reports. The coordinator freezes manifests before dispatch, validates complete role batches, writes through one report update, and finalizes the terminal reconciliation atomically. A torn or incomplete final row makes the report non-reusable.

## Canonical Claim Identity

Parse callout body bullets in document encounter order, including continuation lines, markers, citations, and locators. Frontmatter, callout headings, block-ID lines, fenced-code examples, and HTML-comment bodies are context, not claim rows. Every retained bullet receives exactly one manifest occurrence in the same per-page encounter order; do not sort claim rows by ID, title, or text before writing them. An absent, extra, reordered, or duplicate occurrence invalidates the ledger. The shared validator extracts the retained inventory and compares it to the claim rows after removing only the canonical process marker plus one following horizontal space.

Canonical text uses UTF-8 and LF line endings. Do not trim whitespace or normalize Unicode. Remove only the literal process marker `*[unverified]*` when it is line-anchored immediately after the canonical `> - ` callout-bullet prefix, plus at most one following horizontal space, so terminal marker clearance does not change identity. Fence- and comment-aware parsing never counts or strips marker-shaped text inside inline/fenced code or HTML comments; those bytes remain semantic for the page digest, while HTML-comment bodies remain invisible to claim extraction. A suffix marker or marker in any other noncanonical position is also semantic, not process state. Keep `*[tentative]*`, `*[disputed]*`, all other punctuation/whitespace, and citation text. Store the original full logical bullet as `claim_text` and its byte length as `claim_bytes`; truncation or an ellipsis substituted for content invalidates the row.

Within one page path and callout block, group byte-identical canonical bullets and assign `duplicate_ordinal` in the order those claim rows are encountered in the retained body and ledger, starting at 1. The first encountered member is 1, the next identical member is 2, and so on; never derive the ordinal from a sorted collection. Any insertion, deletion, or reorder inside an identical group invalidates that group. A cross-callout or page-path move invalidates the occurrence.

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

Paths are resolved from the repository root and stored repo-relative with `/` separators. Every dependency and verdict evidence path must be a canonical regular file strictly beneath `0-raw/`; a maintained wiki page can never certify itself. Reject symlink escapes and case aliases. `locators` preserve authored encounter order and the exact target/display, raw path, physical page or inclusive range, printed page or inclusive range, and structural anchor. Every authored raw wikilink fragment has one locator in that same order: `#page=N` binds to the single physical page N and cannot widen to a range, while a heading fragment binds to the normalized structural anchor. If the authored display says `p. M` or `pp. M-K`, its printed coordinates must exactly equal the locator's `printed_page` or `printed_page_start`/`printed_page_end`; if the display has no printed page, the locator declares none. `raw_dependencies` are ordered by repo-relative path and record SHA-256 of the current raw bytes.

For a registered PDF region, `.claude/skills/multi-skill/pagination-map.md` is authoritative. Each claim locator and each HOLD/REFUTE verdict row binds its declared physical coordinates to that map: the printed coordinate or range must equal the mapped sequence exactly; a region mapped to `none` must not invent a printed page; and a mixed or missing declaration is invalid where the map supplies authoritative pagination. For an unregistered physical region, the validator cannot infer pagination, but the exact authored-display-to-locator equality above still applies. Self-reported reader coordinates never override either binding.

The context digest binds the page title/subject, page type, all semantic frontmatter (`sources`, `frames`, attachments/provenance and other meaning-bearing fields), callout type, Sources/support callout, pagination-map entries used, and declared claim dependencies. A causal, comparative, aggregate, generalization, relationship, or framework claim declares the exact claim instances it depends on. If complete dependency closure cannot be proven, its context is the full semantic page digest and any semantic page edit invalidates it. **Audit always uses this conservative full-semantic-page digest for every claim.** Its validator independently extracts the retained title (frontmatter `title`, otherwise the first H1), page type, semantic frontmatter, callout type and block ID, and requires them plus `context_digest == page_generation` to match each manifest occurrence. Mechanical stamp/date fields are excluded.

## Evidence Rows

Each retained report contains one fenced `jsonl` ledger section. Every JSON object has `schema_version: 1`, `row_type`, `run_id`, and `row_id`. One report has exactly one non-placeholder `run_id`; every row must match the manifest's run. An audit manifest also declares the final `relationship_epoch`, and every audit page-reader and status-write row matches that epoch.

- `manifest`: planned source, page, claim, bullet-role, page-reader, scanner, and status-write counts plus final relationship epoch. Audit `mode` exactly matches frontmatter; `full` rejects reuse. Partial includes every non-verified/process-marked/stale-hash/content-change target and every page lacking a committed terminal raw proof. For the exact current semantic page generation, that proof must be a Markdown report directly under the matching `2-outputs/audit/` + `type: audit` or `2-outputs/ingest/` + `type: ingest-report` pair, committed at HEAD with terminal reconciliation, one proof-specific status row whose pre/post semantic hashes equal the generation and whose marker action/counts are coherent, two distinct page-reader HOLDs carrying identical complete raw manifests, and `disposition: available` source rows. The page blob retained at the proof report's commit must itself be verified, marker-free, generation-matching, and body-hash-bound to the status row. The current complete transitive raw path/SHA closure must equal that proof; dirty/untracked/changed/missing raw bytes or no proof makes the page mandatory. Commit ancestry or timestamps alone never establish safety. One replay-valid neutral edge in the **current Audit report** may carry a direct committed host pre-generation proof to its current post-generation: the shared validator loads the current reconciliation's hash-bound baseline, validates exact pre/post bytes, hashes, statuses, frozen-span replay, and current postimage, then unions the old host manifest with direct current-generation proofs for every newly wrapped target and requires that union to equal the host's current raw closure. It never chains historical/transitive edges, and any changed or malformed raw remains mandatory.
- `source`: one actual terminal row for every raw path in the union of all claim `raw_dependencies` **and every scoped page reader's complete transitive `raw_manifest`**. Record canonical `raw_path`, current 64-hex `sha256`, `disposition: available|cannot_confirm`, and evidence. The regular file exists strictly beneath `0-raw/` and hashes to the row. `planned_sources`, `terminal_sources`, and exact path set equal this union, including zero-claim pages.
- `claim`: the complete identity payload above, `classification: required|exempt`, and a closed exemption reason when exempt: `obvious_definitional`, `own_voice_judgement`, `empty_placeholder`, or `verification_neutral_bookkeeping`.
- `bullet_verdict`: `claim_instance_id`, `role: locator_bullet|entailment_bullet`, nonempty role version, distinct nonempty agent/run identity, role-specific `blind_to` counterpart provenance, `verdict: hold|refute|cannot_confirm`, full evidence and quote, physical page/range or structural anchor, nonempty reasoning and confidence, an explicit correction field, and `quote_validated: true` for HOLD. HOLD and REFUTE both require a literal located quote from the claim's raw dependencies. `CANNOT_CONFIRM` instead requires `searched_raw_paths` equal to the claim's complete sorted dependency list and a nonempty `search_summary`; it never invents evidence. A current audit verdict also carries the manifest's final `relationship_epoch`; a verdict from an invalidated earlier epoch is inadmissible even within the same run. Missing/null versions or provenance are malformed and pending, never reusable.
- `claim_terminal`: one terminal disposition per manifest occurrence: `exempt`, `reused_hold`, `backfilled_hold`, `refute`, `cannot_confirm`, or `invalidated`, with both role row IDs when required and the producer report/blob when reused. Only a claim classified `exempt` may use the exempt disposition; a required claim uses the closed remaining set, and every current verdict row must be consumed by its matching terminal disposition.
- `page_reader`: audit only; page path/generation, final relationship epoch, role, distinct nonempty reader identity, role-specific `blind_to` counterpart provenance, verdict, an explicit defect list (empty on HOLD; otherwise one or more objects whose `scope` is exactly `bullet_local`, `cross_bullet`, or `page_only` and whose `detail` is nonempty), and nonempty full evidence. `bullet_local` carries one or more exact sorted `claim_instance_ids`; `cross_bullet` carries at least two exact sorted same-page claim IDs as its dependency set. Missing/malformed evidence, defects, dependencies, or blindness provenance is pending and cannot support a stamp.
- `status_write`: audit only; page path/generation, final relationship epoch, closed before/after statuses, pre/post semantic hashes, marker action, exact pre/post marker counts, and final `verified_hash` or `needs_update_reason`. Marker action is exactly `none`, `added`, `retained`, or `cleared`; its direction must match the counts, and the post-count must match the retained page. Its pre/post semantic hashes both equal `page_generation`, and the retained current page must recompute to that digest and carry the row's actual `after_status`. `after_status: verified` requires every required claim on that page to end `backfilled_hold` or valid `reused_hold`, both final page roles to HOLD, and the retained page's `verified_hash` plus `body_hash.py` output to equal the row's 64-hex hash. Conversely, a fully held scoped page must end `verified`; an unexplained draft is unfinished audit work. A non-HOLD claim or page reader must end `needs-update` with the precise hand-off reason; a bare `draft` cannot hide the defect. A non-verified retained page carries no `verified_hash`; a `needs-update` row and page carry the same nonempty reason.
- `scanner`: nonempty scanner identity and target, nonnegative process status, nonempty result, Boolean stdout-JSON and stderr-runtime-error attestations, and `terminal: true`. Audit scanner rows also bind the manifest's final relationship epoch. A structurally empty row never satisfies a planned scanner obligation.
- `reconciliation`: terminal counts and report result. Audit also embeds the hash-bound Warning baseline path/SHA, `evidence_context_sha256`, and five exact arrays: `warning_fingerprints`, `mention_occurrences`, `suppression_batches`, `suppression_reader_verdicts`, and `neutral_page_transactions`. Use `[]`, never counts/prose.

Audit applies these additional executable constraints:

- Its scoped page set uses exactly `.md` files under the four maintained roots `1-wiki/sources`, `1-wiki/entities`, `1-wiki/concepts`, and `1-wiki/syntheses`; nested look-alike roots, other extensions, duplicate/case-aliased paths, and paths outside those roots are invalid. Every content-changing Audit target is in scope.
- Each `page_reader` carries `raw_manifest`, an ordered array containing only canonical `raw_path` and current `sha256`, exactly equal to that page's complete transitive raw closure. The two page roles for one generation carry identical manifests. The Audit `source` path/SHA set is the union of all claim `raw_dependencies` **and every page-reader `raw_manifest`**, so a zero-claim page still contributes its full closure. `planned_sources` and terminal source rows equal this union exactly.
- `neutral_page_transactions` contains one schema-exact row for every host changed by a `genuine_wrap`, and none for pages without a wrap. It carries pre/post file hashes, exact base64 postimage bytes, unchanged before/after status, final hash only when verified, and ordered `baseline_occurrence_ids`; the validator replays frozen spans. It forbids claim/page-reader/status rows only when the shared validator admits that verified host's exact raw-proof bridge; otherwise the host remains verified but enters ordinary fact-check scope. A draft/needs-update host keeps ordinary fact-check rows and status (`verification-neutral-fixes.md`).
- A complete/unconverged status row permits marker action only `none|cleared` and has `post_marker_count: 0`. An uncertifiable or new-anchor content change ends `needs-update` with a precise reason, no hash, and no process marker.
- Non-mention Warning disposition is exactly `fixed`, `standing_ignore`, `verified_not_applicable`, or `needs_update`. Mention semantic disposition is `genuine_wrap`, `accepted_suppression`, `graph_repair`, or `graph_ignore`; pre-existing standing ignores are frozen and applied before the mention census, not emitted as occurrence rows. An identity change additionally emits one old `superseded` row with `rekeyed_to` and one new `rekeyed` row with reciprocal `rekeyed_from` and semantic `final_disposition`; the relation is bijective.

For Audit, frontmatter `markers_pending` equals the sum of every status row's retained `post_marker_count`. A complete or unconverged report requires both to be zero; a marker in the retained pages cannot be hidden behind a frontmatter zero.

Readers are blind: the locator and entailment reader for one unit do not receive each other's prompt, evidence, verdict, adjudication, prior findings, or cached rows. A batch may carry several same-raw claims, but it returns one full record per claim. A pooled batch/page verdict, missing record, truncated evidence, duplicate role, mixed generation, or malformed record is pending, never HOLD.

Before acting on or reusing HOLD, or accepting REFUTE, mechanically re-extract its literal quote from the exact raw physical page/range. For a non-PDF raw carrying a structural anchor, extract only that Markdown-style section rather than searching the entire file. Collapse line-wrap whitespace only for this literal check. A Boolean attestation alone is insufficient. Semantic adjudication remains the coordinator's: verified text can still fail to entail the claim.

Every HOLD row's `quote_raw_path` must belong to that exact claim's `raw_dependencies` and, when the claim has explicit locators, match one locator's exact declared coordinates: raw path plus physical page/range, printed page/range, and structural anchor where present. A PDF record declares either one positive physical page or one complete ordered inclusive physical range, never both; literal re-extraction uses exactly that page or range. A true literal from an unrelated raw, page, range, or section cannot certify the claim. Reused producer rows undergo the same binding check before they receive credit. Their producer report must also have matching terminal frontmatter/reconciliation results, zero balanced pending counts, and balanced planned/terminal/pending equations matching its manifest.

When `claim_text` authors a raw wikilink fragment, its locator records must cover that exact fragment. A `#page=N` fragment binds only to the single `physical_page: N`; it cannot be widened into a range whose later page happens to contain the quote. Any other fragment binds to the normalized structural anchor. A declared locator for that raw may not contradict the authored fragment. Self-reported locator coordinates never override the retained claim text.

## Reuse And Invalidation

Only an adjudicated `hold/hold` pair is reusable. Reuse requires an exact `claim_instance_id`, ledger and both role versions, an allowed committed producer report/blob, ordered locators, context digest, and raw path/SHA set. A `reused_hold` row names that exact producer claim's two HOLD row IDs; it never imports a whole page, neighbouring claim, or report by association. Before granting credit, inspect the committed terminal blobs under `2-outputs/audit/` and `2-outputs/ingest/` for the same exact claim identity. Any valid REFUTE or CANNOT_CONFIRM counterpart for that exact claim invalidates reuse and backfills both fresh roles; a verdict about another claim does not. Never combine one historical role with one new role. Missing, legacy, versionless, malformed, truncated, nonterminal, dirty selected-producer report, changed-raw, changed-context, conflicting, or one-sided evidence is backfilled through both fresh roles.

A changed/new bullet invalidates its occurrence. Changed raw bytes invalidate every dependent occurrence. A context or dependency change invalidates the affected occurrence; the full-page fallback makes uncertainty conservative. A page-level REFUTE does not automatically poison unrelated locally valid bullet rows, but a `bullet_local` defect revokes the named pair and a `cross_bullet` defect records its exact dependency set as a continuing page blocker.

Results launched in an audit epoch that later becomes `INVALIDATED` are discarded cost and never survive. A new epoch may admit exact-valid rows only from a previously finalized terminal report, never from the just-invalidated epoch.

`audit partial` may reuse exact-valid pairs. `audit full` is cold: it creates two new bullet-role rows for every required claim and records `reused: 0`. Authoring evidence never stamps a page, and reusable evidence never preserves an old stamp across a source/support change.

## Audit Page Readers

Every page actually audited receives two fresh blind readers tied to the final semantic page digest and final `READY(n)`:

- `locator_page`: source identity, exact locator truth, and clause-to-source assignment across the complete page.
- `entailment_argument_page`: meaning, scope, subject/reason attachment, aggregates, contradictions, internal consistency, and argument flow across the complete page.

Each receives the complete page and complete current transitive raw manifest, not selected snippets or bullet verdicts. Each returned row stores that identical ordered `raw_manifest` of exact path/SHA objects; it must equal the page's computed closure and source-row union contribution. Each returns `hold|refute|cannot_confirm` with exact defects and full evidence. Both must HOLD before promotion or marker clearance. A page HOLD never supplies missing bullet evidence.

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

Every planned source, page, claim, bullet role, page reader, scanner obligation, and status write needs exactly one terminal final-epoch disposition. Exact neutral transaction rows additionally cover every qualifying changed verified host.

- `complete`: every equation reconciles, every status write landed, `pending = 0`, and retained process markers are zero; pages may terminally be `needs-update`.
- `unconverged`: all work is terminal, the bounded repair loop exhausted or oscillated, affected pages ended safely non-verified, and retained process markers are zero.
- `incomplete`: any planned work is missing, undispatched, nonterminal, malformed, unparseable, stale-epoch, scanner-blocked, or unreconciled.

An empty reader pipeline is not completion. If runnable work remains and active readers are zero, dispatch a backstop before adjudicating. “Sources were waved” is not evidence that every claim was read.

## Recovery And Validator

Run `validate_verification_ledger.py` after manifest construction, after every repair cycle, and before final report/status completion. The validator checks structure, exact hashes/lengths, duplicate cardinality, role separation, literal quote location, terminal producer provenance, inventories, and equations. It never decides whether evidence semantically entails a claim and never edits wiki content.

On recovery, ignore a torn tail only to diagnose the interrupted report; the report remains `incomplete` and supplies no reusable evidence until the coordinator validates and writes a new terminal reconciliation. Resume by recomputing current page/raw/context identities and dispatching only missing or invalid obligations.
