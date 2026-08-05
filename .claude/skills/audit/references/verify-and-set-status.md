# audit — Verify And Set Status (Step 8)

The verify-and-stamp mechanics for `audit` Step 8 — the terminal writes each in-scope page receives. SKILL.md Step 8 is the overview; this file is the detail. Scope/terminal invariants are in SKILL.md, bullet evidence identity/reuse is in the shared `verification-ledger.md`, and audit's coverage/page-reader checks are in `references/verification-spec.md`.

Step 8 runs after every remaining content edit from Step 7 (`references/apply-fixes.md`) has landed and the final relationship-integrity epoch is current. It applies only to fact-check-scope pages. In `partial`, a Step 4a neutral-only verified genuine-wrap host skips this step only when the shared validator admits its exact raw-proof bridge; otherwise it remains verified but enters this scope. In `full`, every page remains in whole-wiki fact-check scope despite a neutral transaction. Verification is terminal: this is the last write each fact-check-scope page receives — no content edit follows the stamp.

## Contents

- Final Relationship-Epoch Gate
- Re-Fact-Check Anything You Rewrote
- Central Locator-Format Pass
- Execution Order For A Rewritten Page
- Set The Status

## Final Relationship-Epoch Gate

Before any Step 8 reader or stamp, confirm current successful `READY(n)`: post-repair consistency, complete lint/walk, relationship sweep, zero unresolved required targets, frozen final manifests, and no later graph/support/provenance/page-inventory edit. Every claim has a terminal exact-valid bullet disposition and each page has both fresh final-generation reader rows.

If the record is missing, incomplete, unparseable, stale, or followed by a graph edit, stamp nothing. Return to Step 4b and discard every verdict launched in that invalidated epoch. A new partial epoch may re-admit exact-valid evidence only from a previously finalized committed terminal report; never salvage the just-invalidated epoch. Full restarts every bullet role.

## Re-Fact-Check Anything You Rewrote

Every content-changing Audit item puts its page in current fact-check scope. For a bounded delta on a hash-stable page, run both bullet roles for every changed/new/revoked/dependent claim, retain only exact-valid unaffected rows, then run both fresh page roles over the complete final body/raw manifest. For an unbounded rewrite, rebuild every claim row and role before the same page pair. A page HOLD never supplies a missing bullet row. On a surviving non-HOLD, repair and rerun or set `needs-update`, strip the hash, and remove any process marker; never self-stamp.

Three checks beyond raw-faithfulness apply to any rewritten body before stamping:

- **Semantic re-check.** Step 4's catalogue ran before this authoring existed, so an audit-authored split-off, merge survivor, or rewrite has never had its authored prose seen by any semantic pass — re-run the Step 4 catalogue (`references/semantic-checks.md` — one-idea atomicity, plain language, citation form, semantic AI-writing tells, reworded intra-page redundancy) over each authored or rewritten body before stamping. The confirming lint catches only the mechanical tells, not these.
- **Structural re-validation.** Audit's clean-lint precondition held before these edits, but surgery can re-introduce drift. Run `.claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"` with the repository-supported default Python runtime and confirm the edit introduced no new Critical/Warning. Fix a structural finding or set `needs-update`; never stamp through it.
- **Merge content conservation.** Before stamping a merge survivor, confirm every load-bearing bullet from each merged-away page survives (re-voiced) in the survivor, or was deliberately dropped as redundant. The raw-faithfulness check passes a survivor that is internally accurate yet silently lost a parent's claim the raw under-emphasizes.
- **Delta collateral (mandatory on every bounded delta-certify).** Recompute declared dependencies and the conservative full-page fallback. Every neighbouring/aggregate claim whose context changes loses reuse and reruns both bullet roles. The fresh page pair is mandatory.

Bound this loop: re-verify, fix, and re-check at most three rounds per rewritten page (the three-round rewrite re-check loop — a separate counter from the three-pass non-support re-read in Step 7; mirroring ingest's fix-and-rerun cap and lint's regression guard). If the page is still not faithful after three rounds, stop — do not loop, ask a question, or stamp `verified`; set the page `needs-update` with a `needs_update_reason:` naming the residual failure and record the terminal non-convergence. Oscillation is different and ends the loop immediately: set `needs-update` and record the finding a later round reintroduced. The run may be `unconverged` only when every planned unit has this or another terminal safe disposition and no Warning remains pending; missing reader/scanner work or a surviving Warning is `incomplete`.

## Central Locator-Format Pass

After a fanned-out audit, run one central locator-format pass before any `verified_hash` re-stamp. When fact-checking is parallelized (one subagent per raw source), subagents apply the citation format divergently and mislabel sections — a known failure mode this pass guards against. Centrally re-verify every `#page=N` and section anchor against the raw (never trust a subagent's section label or page number), confirm each locator sits inside its `[[…]]` display or a backticked span, and normalize to `sec.` (not a bare `§`). Run this pass after the re-fact-check and the structural re-validation, immediately before the stamp, and apply fact-check-lane shared writes — `index.md`, `log.md`, and co-cited pages — centrally from the top-level agent so parallel writes never collide. Step 4a has already applied and rescanned the two agent-writable check-data files; Step 8 must not reopen them. Only then stamp.

Lint emits `verified_anchor_unaudited` when a page verified at Git HEAD carries a newly added or relabelled locator anchor; a pure relocation of the same anchor/page is exempt, as is promotion from draft/needs-update because that promotion performs the fact-check. A new/relabelled anchor on an already-verified page therefore cannot be re-stamped in the same run. Apply the determinate correction, set `needs-update` with the exact anchor reason, strip the hash, remove any process marker, and record the Warning disposition `needs_update`.

## Execution Order For A Rewritten Page

Before any stamp: (1) apply the fixes (Step 7, `references/apply-fixes.md`); (2) confirm the final relationship-epoch gate above, looping through Step 4b first when stale; (3) re-fact-check the rewritten body against the raw in that epoch; (4) the three pre-stamp checks — semantic re-check, structural re-validation, merge content conservation — within the three-round cap; (5) the central locator-format pass; (6) set status / stamp.

## Set The Status

**Set `verified`** only when full-text coverage holds, every required claim has an exact-valid locator/entailment HOLD pair, both fresh final-page readers HOLD, and reconciliation is terminal. A non-HOLD page ends `needs-update`, hashless and marker-free. Marker clearance requires its anchor already at Git HEAD. Page readers bind the pre-clear candidate; the only permitted post-reader semantic-line write is marker removal with status/hash fields. Compare pre/post canonical payloads to prove nothing else changed, rerun the structural check, then write `verified_hash:` with `body_hash.py`.

`body_hash.py` needs well-formed frontmatter delimited by `---` lines before hashing: it silently hashes the whole file when there is no opening `---` (lint then reads a mismatch and demotes the page), and aborts with a non-zero exit when an opening `---` has no closing `---`. Before hashing, confirm the page begins with a `---` line and has a matching closing `---`; if the delimiters are missing or malformed, repair them or abort the promotion rather than stamping a hash of the whole file (a valid 64-hex return is not proof the body was isolated). If `body_hash.py` is missing, exits non-zero, or does not return a 64-character hex, abort the promotion for that page, leave it non-`verified`, and report it as a Critical — never write an empty or unverified `verified_hash:`.

**Set `needs-update`** when the page carries an unresolved problem: unavailable source/re-extraction, coverage failure, a confirmed correction audit cannot certify in-pass, a new/relabelled anchor blocked by the HEAD gate, or an unresolved contradiction. Making a contradiction visible is not resolving it. Remove every process marker, strip `verified_hash:`, and give the page either the real `Contradictions`/`Tensions` entry or one precise `needs_update_reason:`. Append a new cause rather than overwriting an existing reason (`dependent-cascade.md`). A terminal Warning uses disposition `needs_update`; complete and unconverged reports require a zero marker count.

Never resolve a contradiction by deleting one side — preserve genuine disagreement. Every fix and every status change is recorded in the audit report.
