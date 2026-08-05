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
