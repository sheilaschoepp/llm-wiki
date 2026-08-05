# Verification-neutral fixes

The shared operational spec for the verification-neutral fix allowlist — the closed set of determinate, meaning-preserving edits that a skill may apply to a `status: verified` page and then **re-stamp** `verified_hash:` for, instead of demoting the page to `draft`. Run by `lint` (Step 3, its own format fixes) and `audit` (Step 4a, the de-hyphenation / spelling / link wrap and unwrap fixes), so the logic lives in one place rather than drifting across both copies.

This file is the skills' shared runtime copy. `CLAUDE.md` → Page Status is the canonical schema statement of the same rule; this reference exists because a skill must be runnable from its own folder plus `multi-skill/` without reading `CLAUDE.md` at runtime (CLAUDE.md → Skill Authoring). It is the verification-neutral companion to `verification.md`, the same way that file is the runtime copy of the ingest-verification spec. `consistency`'s `shared_reference_integrity` guards it as a genuine ≥ 2-skill shared reference.

## Contents

- The principle
- The allowlist (and which skill applies each)
- Exact transaction proof
- Re-stamp vs demote
- Text-content exclusion (the hard carve-out)
- Locator relocation vs addition (the hard exclusion)

## The Principle

A change to a `verified` page's unmarked (checked) body normally resets it to `draft`, because the `verified_hash:` no longer matches and lint cannot tell a real claim edit from a meaning-preserving one. The allowlist is the narrow exception: a closed set of *determinate, machine-identifiable string transforms* that provably change no claim's truth. A skill that applies one recomputes and rewrites `verified_hash:` in the same pass — no raw re-read — and the page stays `verified`. The allowlist is deliberately small and string-transform-shaped precisely so that "is this edit claim-neutral?" never becomes a judgement call that could let a real claim change ride.

An allowlisted edit made *outside* a re-stamping skill (a hand edit) is not re-stamped, so lint's next hash check demotes the page — the safe fallback, never a silently-unverified claim.

## The Allowlist (And Which Skill Applies Each)

The allowlist is partitioned by which skill applies each edit; each re-stamps under the same rule.

`lint` owns the four format fixes (it never edits callout body prose):

- `callout_block_id` — the callout's `> ^<block-id>` last-line ID.
- `wikilink_pipe_spacing` — collapse `[[path | display]]` → `[[path|display]]`.
- `citation_bracket_style` — the superseded square-bracket Form 2 (`[[[…]]; […]]`) → round brackets `(…)`.
- `embed_not_isolated` — blank `>` lines around a standalone image embed.

`audit` owns the prose-text transforms (running prose only — see the exclusion below):

- Open-compound de-hyphenation, two published mappings: the always-open mapping (`reinforcement-learning` → `reinforcement learning`, opened in every position; lint's `hyphenated_open_compound`) and the slug-derived noun-only mapping (`the belief-state evolves` → `the belief state`; lint's `hyphenated_open_compound_noun`, bidirectional — opens a hyphenated bare noun, and inversely re-hyphenates an open compound used as a modifier before a curated head noun). The noun-vs-modifier call is a context judgement against the page's own prose, not a raw fact-check.
- Canadian/US spelling normalization (`behavior` → `behaviour`).
- Wrapping an existing plain-text genuine reference in a wikilink to an existing page (`unlinked_page_mention`), where the rendered display is byte-identical to the plain text it replaces and the target page exists.
- Unwrapping an existing wikilink to plain text inside a reciprocity callout (`Contradictions` / `Tensions`) where the linked page is an incidental (non-party) mention and the rendered display stays byte-identical — the symmetric inverse of the wrap above, and the cure for a `missing_reciprocal_contradiction` over-count (the reciprocity check treats every callout wikilink as a party, so it cannot tell an incidental link from a real one). `audit` unwraps only a confirmed non-party and records the now-unlinked occurrence in `unlinked-mention-ignore.md`. Uncertain party status supplies no verification-neutral edit authority: Audit's specific rule preserves the body, sets `needs-update`, retains the exact obligation pending, and finalizes `incomplete` rather than guessing an unwrap or reciprocal. While the root wording differs, Audit records that alignment as an outside-scope `[cross-file]` proposal; it neither edits the root nor asks the user.

A stale-path repair — rewriting an existing inbound wikilink to the *same* page under its new path or name (display unchanged) — is applied by whichever skill runs the rename cascade (`forget` / `supersede` / `ingest`).

A content-identical claim relocation — moving a bullet whose text stays byte-identical and whose meaning its new position does not change (a within-callout reorder is meaning-neutral by construction; a cross-callout move is confirmed meaning-preserving by the moving skill, which treats an uncertain case as a change and demotes) — is applied by whichever skill performs the move (`supersede` / `ingest` / `audit`). A relocation that alters the moved text, or a cross-callout move whose new section changes what the claim asserts, is a change, not a move, and demotes.

## Exact Transaction Proof

Before the first page or shared-data edit, record Git status/diff ownership and run Audit's `.claude/skills/audit/scripts/capture_warning_baseline.py 2-outputs/audit/baselines/audit-{run-id}.json --repo-root . --run-id {run-id}` with the supported default Python runtime. It exclusively creates the run/baseline-ID-bound canonical artifact with exact Warning/enumerator inventories, affected-page preimages, ignore bytes/hash, maintained target-page hashes, canonical/relationship-rule hashes, and `evidence_context_sha256`. Group the complete neutral plan per page, reject overlaps, and apply replacements in descending byte order. The executable reconciliation proof below is specifically the frozen-occurrence proof for `genuine_wrap`; the other allowlisted categories preserve status under the re-stamp rule but do not borrow that schema or its partial-scope raw-proof bridge.

The reconciliation contains `neutral_page_transactions`, with exactly one row for each host changed by a `genuine_wrap` and none for pages without a wrap. Each row has exactly `schema_version`, unique `row_id`, terminal `run_id`, `page_path`, `preimage_sha256`, `postimage_sha256`, exact `postimage_bytes_base64`, unchanged `before_status`/`after_status`, `verified_hash` (final 64-hex only for a verified host; `null` otherwise), and canonical ordered `baseline_occurrence_ids`. `validate_audit_completion.py` loads the hash-bound baseline, replays those frozen spans, rejects overlap/staleness, and requires retained semantic bytes, attested/current postimage bytes, final file hash, status, and applicable body hash to match. For partial-inventory raw-proof reuse, the shared ledger validator admits only this current report's one replay-valid host pre-generation-to-current-post-generation edge: it combines the direct committed host proof with direct current-generation proofs for every newly wrapped target, requires their manifest union to equal the current host raw closure, and rejects chaining, changed raw, or malformed proof data. A neutral-only verified genuine-wrap host has no claim/page-reader/status-write rows only when that bridge is admitted; otherwise it remains verified but enters ordinary scope. A draft/needs-update host retains its ordinary fact-check rows and status. Counts/prose cannot substitute for the array.

## Re-stamp Vs Demote

- Allowlisted edit on a `verified` page → apply it, recompute the hash with `.claude/skills/multi-skill/scripts/body_hash.py`, write the fresh `verified_hash:` in the same pass, keep `status: verified`. No raw re-read.
- Any other unmarked body change (a new/changed claim, reworded bullet, changed citation target/locator, changed embed target, number, or quote) is not neutral. In Audit it enters the current fact-check scope: delta-certify a bounded change, completely certify an unbounded change, or end `needs-update` without a hash or process marker when it cannot certify. Other skills demote and strip the stale hash under their own procedure.
- When in doubt whether a fix is claim-neutral, treat it as not — demote, don't re-stamp.

## Text-Content Exclusion (The Hard Carve-out)

The two text transforms — de-hyphenation and spelling normalization — apply only to running prose, and must skip every verbatim quote (`"…"`), inline `` `code` `` span, math (`$…$`) span, and proper-noun / title / dataset-or-model-identifier token. A hyphenated compound or US spelling *inside* one of those is not claim-neutral — rewriting it would change what the page asserts the source wrote (a quote would no longer match the source verbatim; an identifier or title would no longer be the thing it names) — so it is excluded: leave the token exactly as written, and if it is the only candidate the page is left untouched. An edit that does change such a token is not on the allowlist and demotes rather than re-stamps.

## Locator Relocation Vs Addition (The Hard Exclusion)

A source-page locator-anchor *relocation* that repositions an **already-present** structural anchor relative to the `#page=N` deep-link without changing which section/figure or page it names (`sec. 3.2, [[…#page=9|p. 9]]` → `[[…#page=9|sec. 3.2, p. 9]]`; lint's `source_locator_incomplete`) is on the allowlist — the reader reads the same locator, so no claim moves.

Hard exclusion: *adding* an anchor to a page-only locator, or *changing* which section/figure/page a locator names (e.g. relabelling abstract-drawn content `sec. 1`), is **not** on the allowlist. That asserts a new fact about where the cited content sits, which only the raw can settle — so it must be confirmed against the raw (then the page earns `verified` from that fact-check), or — since changing which section or page a locator names is a change to an existing claim, not an addition — the page demotes to `draft` for a later `audit` to re-verify. It is never self-re-stamped: a single agent inventing an anchor and stamping its own work `verified` is not verification (it is what produced the abstract→`sec. 1` mislabels). `lint` emits the Critical `verified_anchor_unaudited` when a `verified` page's locator anchor changed versus git HEAD (an addition or relabel; a pure relocation is exempt).
