# audit — Unlinked Mention Occurrences (Step 4a)

Use this procedure for the complete `unlinked_page_mention` Warning worklist. Treat scanner findings as candidate groups; adjudicate, apply, and close exact occurrences. This is a verification-neutral/no-raw lane only when wrapping the occurrence cannot create or change a graph assertion.

## Build The Occurrence Ledger

Before the first page or ignore-file edit, record Git status/diff ownership and run `.claude/skills/audit/scripts/capture_warning_baseline.py 2-outputs/audit/baselines/audit-{run-id}.json --repo-root . --run-id {run-id}` with the supported default Python runtime. The path is a new direct child of that directory. Require status 0 and retain its path/SHA, non-placeholder returned `baseline_id`, run ID, and `evidence_context_sha256`. Its immutable payload freezes checker/enumerator inventories, host preimages, ignore bytes, maintained target hashes, and canonical/relationship rule hashes. Every transaction, batch, reader row, and identity transition binds to it.

1. Run the native checker against the current tree. Capture status, stdout, and stderr separately and require parseable complete output.
2. Apply every current entry in `.claude/skills/multi-skill/unlinked-mention-ignore.md` before proposing a new classification. A standing page/target/phrase entry is authoritative for the exact matching occurrence until `stale_mention_ignore` proves it inert.
3. Run `python3 .claude/skills/audit/scripts/enumerate_unlinked_mentions.py --repo-root .`. Require status 0, parseable JSON, `status: ok`, and exact regrouping parity with the native checker's page/target/count multiset. This helper imports the native matcher's masks, aliases, ignore data, and ordering and emits its exact spans; prose-level matcher reimplementation is forbidden. A missing helper, parity mismatch, empty/unparseable output, or non-zero exit makes the audit `incomplete` with the exact group fingerprints rather than guessed spans.
4. Record one row per emitted exact occurrence with:
   - `occurrence_id`: SHA-256 of compact sorted-key UTF-8 JSON containing, exactly, `check_id`, `page_path`, `page_preimage_sha256`, `target_path`, `target_stem`, `matched_text`, `start_byte`, `end_byte`, `line_sha256`, `callout_id`, and `occurrence_ordinal`;
   - page path and preimage SHA-256;
   - target path and target stem;
   - exact matched text and UTF-8 byte start/end;
   - containing-line digest, callout identity, and occurrence ordinal;
   - initial scanner group fingerprint and terminal disposition.
5. Keep repeated identical text as separate rows. A group count, line number, phrase, or target stem alone is not an occurrence identity.
6. Search target aliases and hyphenated/near-alias forms around the candidate group, and reject adjacent-token coincidences that cross a grammatical boundary. Record these separately; never inflate the scanner group count into a span count.
7. Reconcile expansion before triage: `initial Warning findings = initial non-mention fingerprints + initial mention groups`; each native mention group's reported count equals the number of emitted occurrence IDs for the same page/target; and `zero-match scanner defects = 0`. Reconcile non-mention fingerprints and exact mention occurrences as separate units.

Terminal semantic occurrence dispositions are exactly `genuine_wrap`, `accepted_suppression`, `graph_repair`, and `graph_ignore`. The native checker and enumerator apply frozen pre-existing standing ignores before the Warning census, so an enumerated occurrence can never close by merely claiming `standing_ignore`. If an edit changes an occurrence identity before closure, retain the old exact row with `disposition: superseded` and `rekeyed_to`; create exactly one new exact row with `disposition: rekeyed`, reciprocal `rekeyed_from`, and `final_disposition` from the four-value semantic set. Every frozen old ID appears once and every new ID has one predecessor: no arithmetic deletion/recreation or one-to-many mapping.

## Triage Exact Occurrences

Classify each occurrence against the complete host page, target page, and `CLAUDE.md` → Wikilink Format:

- `genuine_wrap`: ordinary prose genuinely refers to the existing target page and wrapping the same rendered words changes no claim or relationship. Queue the exact span for a deterministic wikilink wrap; no reader is needed after this positive classification.
- `candidate_suppression`: the words are generic, a homograph, or part of a larger established phrase rather than a reference to the target. Queue an exact suppression candidate for the two-reader protocol below.
- `graph_sensitive`: the occurrence sits in `Contradictions`, `Tensions`, a source page's `Concepts and Entities`, or a `sources:` / `Sources` / `Supports` / provenance field where a wikilink asserts support or provenance. Remove it from the neutral lane and settle the asserted relationship through Step 4b against the current relationship-check definitions and authoritative evidence. `Connections`, `Not This`, `Examples`, and `Disconfirming Evidence` use ordinary mention triage unless a separate relationship finding independently establishes an obligation. Never use a generic-word suppression to erase a real graph obligation.

Do not let the coordinator's label decide a suppression. The coordinator may deterministically apply `genuine_wrap`; only two independent reader HOLDs authorize `candidate_suppression`.

## Verify Suppression Candidates In Batches

1. Freeze suppression candidates in occurrence-ledger order. Save the complete enumerator records, then run `.claude/skills/audit/scripts/build_suppression_batches.py {candidate file} --evidence-context-sha256 {baseline value}` with the supported default Python runtime (add `--review-kind graph_ignore` when applicable). Each candidate contains exactly the eleven identity fields plus `occurrence_id`; coordinator conclusions are forbidden. Require parseable status 0, exact count, valid unique IDs, canonical order, and maximal batches of 25 except the last.
2. The helper emits `input_sha256`, SHA-256 of a compact sorted-key canonical header (`schema_version`, review kind, `evidence_context_sha256`) followed by the **full ordered candidate JSONL row stream**. Whitespace/key-order reserialization of equivalent input does not change it; semantic row content, order, or re-keying does. Each batch digest then binds schema, review kind, evidence-context hash, input hash, batch number, and that batch's canonical rows. Send identical rows and all hashes to exactly two blind readers; every batch/verdict row repeats `evidence_context_sha256`, `input_sha256`, and `batch_digest`. Changed targets/rules/relationships/ignore data invalidate the context hash. Missing/malformed input/output, wrong hashes, duplicates, count/order mismatch, or non-zero status leaves exact candidates pending.
3. Require one parseable verdict per occurrence ID: `HOLD` means the exact occurrence is generic and safe to suppress; `REFUTE` means it is a genuine reference or graph obligation; `CANNOT_CONFIRM` means evidence or context is insufficient.
4. Add a suppression entry only on `HOLD/HOLD` for the same occurrence ID and batch digest. Route `REFUTE/REFUTE` on ordinary prose to `genuine_wrap`. A split or any `CANNOT_CONFIRM` result remains exact pending work and makes the audit `incomplete`; insufficient evidence never authorizes a link or suppression. Never seek a third vote.
5. Route any relationship-bearing result to `graph_sensitive`. A missing, unavailable, stale, wrong-digest, or unparseable reader result also remains pending and makes the audit `incomplete`. Do not ask the user or carry it as a follow-up.

### Settle Graph-Sensitive Occurrences In Step 4b

- A confirmed genuine party receives the required link/reciprocal/support repair under the ordinary Step 4b evidence and epoch rules.
- A positively settled incidental non-party remains unlinked. Route its exact occurrence through the same consecutive-maximal packing, canonical-row validation, digest, blindness, and two-reader mechanics above, but use a graph-ignore question rather than the generic-word question: `HOLD` means the canonical relationship rules and authoritative evidence confirm this occurrence is an incidental non-party that must stay unlinked to avoid asserting a false relationship; `REFUTE` means it is a genuine party or otherwise carries a real graph obligation; `CANNOT_CONFIRM` means party status remains indeterminate. Append the ignore centrally only on graph-ignore `HOLD/HOLD`, then rerun the native scanner and exact enumerator. A split or `CANNOT_CONFIRM` follows the indeterminate branch below; never reinterpret it through the ordinary generic-suppression verdict meanings.
- An indeterminate party/non-party call receives no relationship/body edit: preserve the body, set `needs-update` with the exact unresolved relationship, strip a stale hash, keep the occurrence pending, and finalize `incomplete`.

Batching changes dispatch cost, not the completion contract. Run every batch required by the frozen occurrence ledger in the same audit.

## Apply Page Transactions

1. Group every accepted `genuine_wrap` by host page and apply page wraps before any new suppression append.
2. For a `verified` host page, run `body_hash.py` once and require the result to equal its current `verified_hash:`. If it does not, apply none of that page's neutral transforms and route the page into ordinary fact-check scope. For a `draft` or `needs-update` host, preserve that status and retain ordinary fact-check scope; no hash is required or written.
3. Validate every occurrence ID against the frozen page preimage and exact byte span. Reject overlapping edits.
4. Apply the complete page plan in descending UTF-8 byte-offset order. Never substitute the first, nearest, same-line, regex, or fuzzy occurrence when an exact identity is stale.
5. Touch `updated:` once. For a verified host, compute the post-edit body hash once and write `verified_hash:` once; keep `status: verified`. For a draft/needs-update host, preserve status and write no hash. Do not read raw, dispatch bullet/page readers, add `*[unverified]*`, or demote any host for these transforms.
6. If any identity fails validation, abort that page transaction, rerun the native scanner/enumerator, and record the old/new exact rows as one reciprocal `superseded`/`rekeyed` pair. Rebuild batches and obtain fresh verdicts bound to the new canonical input hash before editing; never credit the old ID.
7. After every wrap transaction, rerun the native scanner and exact enumerator on post-wrap bytes. Invalidate every proposed suppression whose page preimage or containing-line digest changed, rebuild its candidate row, and rerun both readers on maximal same-digest batches. Only then append final-preimage `HOLD/HOLD` suppressions centrally to the ignore file.
8. Rerun the scanner and exact enumerator after the suppression append. Treat an inert or mismatched new entry as a failed transaction: remove it, rebuild the candidate from current bytes, and rerun both readers before any replacement.

## Close The Worklist

After each page/data wave, rerun the native checker and reconcile old and new fingerprints. Semantic closure uses only `accepted_suppression`, `genuine_wrap`, `graph_repair`, or `graph_ignore`; identity churn additionally requires the one-to-one superseded/re-keyed fields above. Every genuine-wrap host also has its exact status-preserving `neutral_page_transactions` row from `verification-neutral-fixes.md`.

After all writes, run the complete lint procedure against the final tree. `complete` requires:

- zero `unlinked_page_mention` Warnings;
- zero stale ignore entries;
- `initial Warning findings = non-mention fingerprints + mention groups`;
- each mention group's native count equals its exact occurrence count, and zero-match scanner defects are 0;
- `initial non-mention + introduced non-mention = terminal non-mention + pending non-mention`;
- `initial expanded mentions + introduced mention occurrences = terminal mentions + pending mentions`;
- `pending occurrences = 0`; and
- no new Warning introduced by the transactions.

### Executable Completion Rows

Counts are only reconciliation checks; they never close a Warning. The terminal reconciliation row must also carry these four arrays, validated by `validate_audit_completion.py` with exact schemas and no extra fields:

- `warning_fingerprints`: one row per initial/introduced non-mention Warning, with exact identity fields, terminal `disposition` from `fixed|standing_ignore|verified_not_applicable|needs_update`, and nonempty `resolution`. `warning_id` hashes exactly `origin`, `check_id`, `page_path`, `target`, and `message_sha256`.
- `mention_occurrences`: ordinary rows contain the twelve candidate fields, identity/run fields, `origin`, semantic `disposition`, `review_kind`, `resolution`, and `ignore_entry`. Accepted ignores carry the exact appended data-file line including its `- ` prefix; other semantic dispositions carry null. A superseded row has exactly those common fields plus `rekeyed_to`; its matching rekeyed row has exactly the common fields plus `rekeyed_from` and semantic `final_disposition`. Links are reciprocal and bijective.
- `suppression_batches`: one row per canonical maximal batch, with identity/run fields, `review_kind`, `evidence_context_sha256`, `input_sha256`, `batch_number`, `batch_digest`, `size`, and ordered `occurrence_ids`. The validator rebuilds the input and every batch hash from canonical rows.
- `suppression_reader_verdicts`: exactly two rows per reviewed occurrence, with identity/run fields, occurrence/batch identity, `evidence_context_sha256`, `input_sha256`, reader role, distinct `agent_id` and `reader_run_id`, `blind_to`, verdict, fixed question version, and reasoning. A split/hash mismatch/`cannot_confirm` cannot appear in a complete report.
- `neutral_page_transactions`: one exact row per changed genuine-wrap host with the status-preserving schema in `verification-neutral-fixes.md`; use `[]` when none.

For generic suppression, `HOLD/HOLD` requires terminal disposition `accepted_suppression` and `REFUTE/REFUTE` requires `genuine_wrap`. For graph-ignore review, `HOLD/HOLD` requires `graph_ignore` and `REFUTE/REFUTE` requires `graph_repair`. The exact row totals must equal every Warning reconciliation count. Consequently a census such as 700 findings / 648 mention groups cannot pass without the corresponding exact terminal rows and all required reader quorums.

“All batches ran” is never completion evidence. A non-zero residual, including one smaller than the initial backlog, returns to triage. A hard external execution failure produces `result: incomplete` with the exact pending occurrence IDs.
