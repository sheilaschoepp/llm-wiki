# audit — Contract Scenarios

Walk these scenarios after changing audit's autonomy, worklist, batching, neutral-fix, verification, or completion rules. Treat any failed expected invariant as a skill defect even when structural linters pass.

## 1. Neutral Fix On A Verified Page

**Given:** In `partial`, a hash-stable `verified` page has three genuine `unlinked_page_mention` occurrences and no content-changing defect.

**Expect:** Before edits Audit records Git/diff ownership and exclusively creates a hash-bound baseline with exact Warning/enumerator, host preimage, ignore, target, and rule inputs. Step 4a applies one non-overlapping page transaction and keeps `status: verified`. One exact `neutral_page_transactions` row names the pre/post file hashes, final verified hash, and all frozen occurrence IDs; the validator replays the spans. If the shared validator admits the exact raw-proof bridge, the neutral-only host has no verification/status rows; otherwise it remains verified and enters ordinary fact-check scope. Final lint reports none of the three Warnings.

## 2. Large Suppression Backlog

**Given:** The frozen ledger contains 52 proposed generic-occurrence suppressions.

**Expect:** `build_suppression_batches.py` receives baseline `evidence_context_sha256`, canonically hashes the header plus full ordered row stream as `input_sha256`, and gives both readers slates of 25, 25, and 2. Equivalent JSON whitespace/key order leaves the input hash unchanged; semantic content, row order, or re-keying changes it. Each batch digest also binds batch number/rows. Batch and reader rows repeat all hashes. `REFUTE/REFUTE` routes to a wrap; split/`CANNOT_CONFIRM` remains pending; no third vote occurs.

## 3. Repeated Text And A Stale Span

**Given:** One page contains the same target phrase four times, and an earlier edit invalidates the third occurrence's byte span.

**Expect:** The four occurrences have different IDs. The transaction aborts rather than substituting a nearby match. Audit rescans; a changed identity emits one exact old `superseded` row with `rekeyed_to` and one exact new `rekeyed` row with reciprocal `rekeyed_from` plus semantic `final_disposition`. It rebuilds input-hash-bound batches/readers; no old/new ID is omitted, duplicated, or mapped one-to-many.

## 4. Ambiguous Graph-Bearing Occurrence

**Given:** An occurrence appears in a relationship-bearing callout and evidence cannot determine whether the target is a genuine party.

**Expect:** Audit makes no relationship/body edit, does not ask the user, and does not guess. It preserves the body, sets `needs-update` with the exact unresolved relationship choice, strips a stale hash, and records the occurrence pending. If final lint still emits the Warning, the audit result is `incomplete`.

## 4a. Proven Incidental Graph Mention

**Given:** A genuine page reference appears incidentally inside a relationship-bearing callout, and authoritative evidence positively establishes that the target is not a party to that relationship.

**Expect:** Both blind readers receive the graph-ignore question, not the ordinary generic-word question. `HOLD/HOLD` confirms that the exact occurrence must remain unlinked to avoid a false graph assertion, authorizes its page-scoped ignore, and is followed by native rescanning. The wording need not be generic.

## 5. External Reader Or Scanner Failure

**Given:** A required suppression reader is unavailable or final lint returns empty/unparseable output after safe retries.

**Expect:** Audit writes no unverified suppression, does not stage work, and does not request continuation. It finalizes `incomplete` with exact pending occurrence, reader-role, batch, or scanner identities.

## 6. Late Content Or Graph Repair

**Given:** Step 7 finds a content-changing or relationship-changing defect after an earlier verification epoch.

**Expect:** A content-only edit invalidates and atomically rebuilds affected claim/page generations and manifest rows before their final readers. A graph/support/provenance/inventory edit additionally invalidates the whole epoch, returns to Step 4b, and restarts its verification cold. Audit never treats Step 4a's neutral proof as content verification.

## 6a. Bounded Content Change On A Verified Page

**Given:** Audit confirms a single bounded reword on a hash-stable verified page; two aggregate bullets depend on it and all other rows remain exact-valid.

**Expect:** The page enters current scope. Audit reruns both bullet roles for the changed bullet and both dependants, retains only unaffected exact-valid rows, sends the complete final page plus complete raw manifest to two fresh page readers, and re-stamps only if all gates HOLD. No masking or later-run deferral occurs.

## 6b. New Locator Anchor

**Given:** Audit confirms a locator correction that adds or relabels an anchor relative to Git HEAD.

**Expect:** Audit applies the determinate correction, sets the page `needs-update` with the exact anchor reason, strips `verified_hash:`, removes any `*[unverified]*` process marker, and records non-mention disposition `needs_update`. Neither `complete` nor `unconverged` may retain a process marker.

## 7. False Completion With Residual Warnings

**Given:** Every planned batch ran, but final lint still reports 45 Warning findings.

**Expect:** Audit folds the exact residual fingerprints into the current worklist and continues. It cannot report `complete`, update hot/log as a success, or relabel the 45 findings as a later follow-up.

## 8. Clean Autonomous Completion

**Given:** All initial and newly introduced Warning identities have terminal dispositions, all verification ledgers reconcile, and final lint is fresh and parseable with zero Warnings.

**Expect:** Audit reports `pending: 0`, `markers_pending: 0`, exact Worklist arithmetic using only `fixed|standing_ignore|verified_not_applicable|needs_update` for non-mention Warnings and the closed occurrence vocabulary, a clean post-bookkeeping scanner row accepted by `validate_audit_completion.py`, and `result: complete` without an operational question.

## 9. Neutral Fix On A Non-Verified Page

**Given:** A `draft` or `needs-update` page has two genuine mention wraps and remains in ordinary fact-check scope.

**Expect:** Step 4a validates and applies one exact page transaction, emits its exact `neutral_page_transactions` row with unchanged before/after status and `verified_hash: null`, touches `updated:` once, writes no page hash, and neither demotes nor prematurely verifies the page. Its ordinary later fact-check uses the post-transaction body and retains its claim/page/status rows.

## 10. Zero-Claim Page Reader Raw Closure

**Given:** A scoped maintained page has no extracted claim bullets but transitively depends on two raw files.

**Expect:** Both fresh page-reader rows carry the identical ordered two-entry `raw_manifest`. The report has one matching `source` row per path/SHA, and `planned_sources` counts the union of claim dependencies and all page-reader manifests. Omitting either raw fails completion.

## 11. Producer Provenance

**Given:** A reusable claim points to a committed report in a nested look-alike folder, or a direct report whose frontmatter type is crossed; another direct valid report has matching role rows and dependency path/SHA source rows.

**Expect:** Audit rejects the first two producers. It may reuse the valid direct-folder/type producer, names only its claim/HOLD row IDs, and discovers source proof by exact dependency path/SHA without requiring reusable source row IDs.

## 12. Page Batching Without Row Loss

**Given:** Final scope has 94 pages over 31 identical complete raw-manifest groups.

**Expect:** The pre-dispatch plan contains 62 page-role calls and 188 page-reader rows. Every page still receives both blind roles. A pooled group verdict, missing page record, or same agent/run used for counterpart roles is rejected.

## 13. Coordinator Context Is Bounded

**Given:** Hundreds of claim/page records HOLD across many batches.

**Expect:** Readers write full evidence to unique plan/epoch/generation/raw-bound sidecars and return only compact receipts. The collector checks transport/schema. The coordinator then opens every accepted record in bounded sequential slices, mechanically re-extracts its quote, and semantically adjudicates it before import; no full reader transcript is returned inline or retained in context all at once.

## 14. Universal Negative Has A Hidden Counterexample

**Given:** A synthesis says “no source varies round count”; its cited source does not, but another source in the page's complete manifest does.

**Expect:** The claim and both bullet units receive `verification_scope: exhaustive_negative` plus a coordinator-frozen `quantified_population` whose raw paths equal the complete dependencies. The second source is recorded as a counterexample and the claim REFUTES. A reader cannot shrink the population: a HOLD sidecar listing only the cited source fails collection and terminal ledger validation.

## 15. Cross-Source Work Cannot Ride A Marker

**Given:** One cross-source bullet has an unchecked locator after final retries; in a separate case, its reader service is unavailable even though the raw and page are unchanged.

**Expect:** The page is not promoted with `*[unverified]*`. A runnable obligation is dispatched. An unreadable raw/evidence region ends marker-free `needs-update` with an exact reason. A reader/tool/service failure finalizes the run `incomplete` with exact pending units and leaves the page body, status, hash, and marker unchanged; infrastructure failure never demotes it. `complete|unconverged` remains marker-free.

## 16. Retained Reader Artifacts Are Terminal Proof

**Given:** A report contains final bullet/page rows, but one numbered plan, sidecar, or collected artifact is deleted, changed, self-rehashed after dropping a unit, or omitted from `reader_executions`.

**Expect:** Completion fails. The validator reconstructs plan input/counts from batches, replays every sidecar, and requires the collected record union to equal the final current reader rows exactly. Counts or ledger rows alone cannot replace retained artifacts.

## 17. Page Readers Bind Final Bodies

**Given:** Initial bullet readers HOLD, Step 7 rewrites one scoped page, and a pre-repair page-reader result exists.

**Expect:** The pre-repair page result is stale and receives no credit. Step 8 computes the final generation and builds a new numbered execution for every final page plus affected bullet reruns. Page-reader estimation may happen in Step 5, but page-reader dispatch happens only after final bodies exist.

## 18. Reader Plan Cannot Self-Declare An Empty Universe

**Given:** The current claim row has two raw dependencies, but a self-rehashed terminal bullet plan names the same claim ID with an empty manifest or old ordinary scope.

**Expect:** Completion fails because the terminal plan unit must exactly equal the current claim's context digest, ordered dependencies, verification scope, and quantified population. The ledger row cannot authenticate a weaker plan merely by sharing its claim ID.

## 19. Superseded Execution Remains Auditable

**Given:** Execution 001 produced stale/refuted rows and execution 002 replaced them, but the report omits execution 001 or drops its records from the final ledger.

**Expect:** Completion enumerates both on-disk directories. Execution 001 remains listed, every row is explicitly superseded by a terminal same-role row, and every retained row has a digest-bound coordinator adjudication. Omitting the directory, execution, row disposition, or adjudication fails.

## 20. Destructive Correction Needs Independent Approval

**Given:** Both bullet roles REFUTE a claim and the final page deletes or destructively rewrites it.

**Expect:** One third agent/run, distinct from and blind to both readers, reviews the exact two hashed REFUTE rows and writes the canonical hash-bound sidecar before approving the exact correction in `destructive_correction_reviews`. Both REFUTE rows remain in their retained execution as superseded cost and terminate at that destructive-review row; they and the removed claim are absent from the final current-claim ledger. A mixed HOLD/REFUTE or CANNOT_CONFIRM/REFUTE pair preserves the claim. A prose claim that a third reader agreed, a reused reader, a forged/missing sidecar, or a missing review fails completion.

## 21. Infrastructure Failure Restores Step 4b And Step 7

**Given:** Step 4b changed a relationship and Step 7 changed prose before the reader service became unavailable.

**Expect:** Both pages have exact pre-first-Step-4b/7 `content_rollback_preimages` copied from the exclusive post-Step-4a checkpoint; both are restored byte-for-byte, listed in `infrastructure_failure_pages`, and pass `validate_audit_completion.py --verify-incomplete-rollback`. The report ends `incomplete`; completed Step 4a neutral work remains, while neither page is demoted, marked, or left partly edited.

## 22. Batch Limits Are Hard

**Given:** A coordinator changes plan parameters to 1,000 claims/pages or concurrent calls to reduce call overhead.

**Expect:** Plan construction and replay reject the values. The maxima remain 25 claims, 4 pages, and 4 concurrent calls; batching changes call count, never evidence-row obligations.

## 23. Execution History Cannot Quietly Shrink

**Given:** Execution 001 was retained and execution 002 later replaced its rows, but the coordinator deletes execution 001, renumbers the directory, adds an ignored-suffix child, or rewrites the journal census to mention only execution 002.

**Expect:** Completion fails while the retained local journal, anchors, report, or execution census exposes the omission. Journal initialization also creates an independent anchor directory in a new empty run root. Every execution atomically publishes one numbered anchor before its matching journal link; anchors are never overwritten. A short/partial write never reaches the final path. Retry removes only the next unpublished temp or a same-inode name for an already published anchor; a cleanup failure aborts before journal advancement. If a later crash leaves exactly one authentic anchor ahead of the journal, an identical retry adopts it; any other mismatch fails. The helper refuses reinitialization while any prior state remains, and completion requires the anchor census, journal chain, report census, and exact direct artifact-root children to agree. This is local fail-closed recovery, not cryptographic non-erasure after deliberate deletion of every local artifact; that stronger threat model requires an authorized committed or external checkpoint.

## 24. One PDF Can Contain Many Quantified Members

**Given:** A claim says none of ten experimental conditions in one PDF used a variable round count.

**Expect:** The frozen population has ten distinct semantic-unit member IDs, each mapped to that one raw path; both roles search all ten before HOLD. Collapsing them into one member called `paper` fails the semantic population requirement. A member spanning two raws fails mechanically, while multiple members mapped to one raw are valid.

## 25. A Split-Off Page Has An Absence Preimage

**Given:** Step 7 autonomously splits an existing page and creates a new maintained path that did not exist when the Warning baseline was captured.

**Expect:** The new path's rollback row declares `preimage_existed: false`, an empty preimage byte string and its SHA-256, null prior status/hash, and zero markers; absence from the post-Step-4a checkpoint authenticates it, and the checkpoint's inventory must exactly equal the Step 1 baseline. Successful terminal certification keeps the new page with `rollback_required: false`. Infrastructure abort sets the flag, removes the path, restores the original page, and requires the final page inventory to equal the checkpoint.

## 26. Step 4a Edits Are The Rollback Boundary

**Given:** Step 4a legitimately corrects spelling or de-hyphenation on a page, then Step 7 changes that page before an infrastructure failure.

**Expect:** Audit captured the exclusive full-page checkpoint after the Step 4a edit and before Step 4b/7. The rollback row must match the checkpoint bytes, not the older Step 1 bytes. Recovery restores the Step 4a-corrected page, the checkpoint path/SHA and complete page inventory validate, and any attempt to substitute already edited Step 4b/7 bytes fails.
