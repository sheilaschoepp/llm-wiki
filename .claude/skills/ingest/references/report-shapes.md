# ingest — Report Shapes (Step 8)

The two report body shapes `ingest` writes, and the `Recommended next ingests` spec they close with. Read this when Step 8 writes the report. The two packets and role briefs are in `.claude/skills/multi-skill/references/verification.md`; exact claim identity, durable rows, result states, and reconciliation are in `verification-ledger.md`. This file holds only ingest's templates.

## Contents

- Recommended Next Ingests
- New-Source Report Shape
- Existing-Source (Reingest) Report Shape

Both modes write to `2-outputs/ingest/ingest-YYYY-MM-DD-HHMM-{stem}.md` (`HHMM` is the 24-hour UTC from `TZ='UTC' date '+%Y-%m-%d-%H%M'` at write time). This report is ingest's single operation output — never a second file, and never another skill's folder.

Record both packet results. If frames or a non-frame depth purpose were used, include them in the report — not on the source page — so the framing/scope decision is recoverable later.

## Recommended Next Ingests

Every report closes with a `Recommended next ingests` section: the papers that would fill a gap *this ingest surfaced* — a single-source page this ingest created or left wanting its primary, a watch item it added, a dangling concept that now warrants its own source, or uningested prior work this source cites and leans on. One entry per paper: author and year, the title, and one line on the gap it fills. This is ingest-derived, not a generic literature dump: list only what this source's gaps actually point to.

**Honesty guard (the academic-integrity rule applies):** list only papers you are confident genuinely exist — never fabricate a title, author, or venue, and mark any whose existence you are unsure of `(verify exists)` rather than asserting it. The section is `none` when the ingest surfaced no specific next-source — it is not a quota, so do not pad it.

## New-Source Report Shape

````markdown
---
type: ingest-report
date: YYYY-MM-DD
stem: "{stem}"
frames: []  # one or more frame texts, or empty if unscoped
purpose: "{non-frame depth purpose, or empty}"
result: <complete|unconverged|incomplete>
ledger_schema: 1
pending: N
---

# Ingest report: {stem}

Touched:

- [[1-wiki/sources/{stem}.md|{stem}]]
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]

## Source-faithfulness packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- Mid-range detail re-located: {a fact from roughly the middle of the read unit}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on metadata, TL;DR, contribution, key claims, evidence pointers, image fidelity.

## Note-quality and coverage packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- Mid-range detail re-located: {a fact from roughly the middle of the read unit}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on one-idea clarity, simple language, source support, image discipline, coverage gaps, intra-page redundancy.

## Fixes applied
- Bullet evidence: {required} required, {exempt} exempt; locator {hold/refute/cannot-confirm counts}; entailment {counts}; {calls} calls; {pending} pending. Full claim/evidence text is retained in the ledger below.
- Pagination map: {section registered | already registered | re-verified after raw change | n/a — non-PDF | unregistered because {reason}}.
- Verified-page delta sweep: {page → hash matches stamp / demoted with `verified_hash:` stripped}, per swept page (or `none — no verified page touched`).
- Structural check (`check_wiki.py`, filtered to pages this run wrote): {error-severity findings cleared, or "none"}.
- Legacy-page duplicate check (new-source mode): the `file:`-frontmatter and stem-variant greps run over `1-wiki/sources/`, and their hits or `no match`.
- Short bullet per fix made before finalizing (or "none").
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

## Verification ledger

- Inventory: {sources/pages/claims/bullet roles planned and terminal}
- Checker: status {0|1}; stdout JSON-array {yes}; stderr runtime error {no}; global tripwires {cleared}
- Reconciliation: `claims = exempt + required`; required pairs {terminal}; pending {N}

<!-- verification-ledger:start -->
```jsonl
{"schema_version":1,"row_type":"manifest","row_id":"...","run_id":"...","planned_sources":0,"planned_pages":1,"planned_claims":1,"planned_bullet_roles":2,"planned_page_readers":0,"planned_scanners":1,"planned_status_writes":0}
{"schema_version":1,"row_type":"claim","row_id":"...","run_id":"...","claim_instance_id":"...","page_path":"1-wiki/...","page_type":"concept","page_title":"...","semantic_frontmatter":{},"callout_type":"idea","callout_id":"idea","duplicate_ordinal":1,"claim_text":"> - full untruncated bullet","claim_bytes":27,"locators":[],"raw_dependencies":[],"context_digest":"...","classification":"required"}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"locator_bullet","role_version":"...","agent_id":"...","verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"entailment_bullet","role_version":"...","agent_id":"...","verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"claim_terminal","row_id":"...","run_id":"...","claim_instance_id":"...","disposition":"backfilled_hold","role_rows":["...","..."]}
{"schema_version":1,"row_type":"scanner","row_id":"...","run_id":"...","scanner":"check_wiki","target":"1-wiki","status":0,"stdout_json":true,"stderr_runtime_error":false,"terminal":true}
{"schema_version":1,"row_type":"reconciliation","row_id":"...","run_id":"...","result":"complete","pending":0,"planned_pages":1,"terminal_pages":1,"pending_pages":0,"planned_sources":0,"terminal_sources":0,"pending_sources":0,"planned_claims":1,"terminal_claims":1,"pending_claims":0,"planned_bullet_roles":2,"terminal_bullet_roles":2,"pending_bullet_roles":0,"planned_page_readers":0,"terminal_page_readers":0,"pending_page_readers":0,"planned_scanners":1,"terminal_scanners":1,"pending_scanners":0,"planned_status_writes":0,"terminal_status_writes":0,"pending_status_writes":0}
```
<!-- verification-ledger:end -->

## Recommended next ingests
- {author year — "Title" — the gap this ingest surfaced that it fills; "(verify exists)" if unsure}, grouped if several. Only papers you are confident exist. "none" when the ingest surfaced no specific next-source.

## Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
````

## Existing-Source (Reingest) Report Shape

Same frontmatter and heading levels as the new-source shape — `purpose:` in particular, since `references/existing-mode.md` recovers a prior deep purpose by reading it off the latest report for this stem.

````markdown
---
type: ingest-report
date: YYYY-MM-DD
stem: "{stem}"
frames: []  # one or more frame texts, or empty if unscoped
purpose: "{non-frame depth purpose, or empty}"
result: <complete|unconverged|incomplete>
ledger_schema: 1
pending: N
---

# Reingest report: {stem}

Reason: {the Step 1 reingest reason}

Touched:

- [[1-wiki/sources/{stem}.md|{stem}]]
- [[1-wiki/concepts/self-attention.md|self-attention]]

## Source-faithfulness packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- Mid-range detail re-located: {a fact from roughly the middle of the read unit}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/sources/{stem}.md|{stem}]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}

## Note-quality and coverage packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- Mid-range detail re-located: {a fact from roughly the middle of the read unit}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/concepts/self-attention.md|self-attention]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}
- Bullet evidence: {required} required, {exempt} exempt; locator {hold/refute/cannot-confirm counts}; entailment {counts}; {calls} calls; {pending} pending. Full claim/evidence text is retained in the ledger below.
- Pagination map: {section registered | already registered | re-verified after raw change | n/a — non-PDF | unregistered because {reason}}.
- Verified-page delta sweep: {page → hash matches stamp / demoted with `verified_hash:` stripped}, per swept page (or `none — no verified page touched`).
- Structural check (`check_wiki.py`, filtered to pages this run wrote): {error-severity findings cleared, or "none"}.
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

## Verification ledger

- Inventory: {sources/pages/claims/bullet roles planned and terminal}
- Checker: status {0|1}; stdout JSON-array {yes}; stderr runtime error {no}; global tripwires {cleared}
- Reconciliation: `claims = exempt + required`; required pairs {terminal}; pending {N}

<!-- verification-ledger:start -->
```jsonl
{"schema_version":1,"row_type":"manifest","row_id":"...","run_id":"...","planned_sources":0,"planned_pages":1,"planned_claims":1,"planned_bullet_roles":2,"planned_page_readers":0,"planned_scanners":1,"planned_status_writes":0}
{"schema_version":1,"row_type":"claim","row_id":"...","run_id":"...","claim_instance_id":"...","page_path":"1-wiki/...","page_type":"concept","page_title":"...","semantic_frontmatter":{},"callout_type":"idea","callout_id":"idea","duplicate_ordinal":1,"claim_text":"> - full untruncated bullet","claim_bytes":27,"locators":[],"raw_dependencies":[],"context_digest":"...","classification":"required"}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"locator_bullet","role_version":"...","agent_id":"...","verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"bullet_verdict","row_id":"...","run_id":"...","claim_instance_id":"...","role":"entailment_bullet","role_version":"...","agent_id":"...","verdict":"hold","quote":"...","quote_raw_path":"0-raw/...","physical_page":1,"reasoning":"...","confidence":"...","correction":null,"quote_validated":true}
{"schema_version":1,"row_type":"claim_terminal","row_id":"...","run_id":"...","claim_instance_id":"...","disposition":"backfilled_hold","role_rows":["...","..."]}
{"schema_version":1,"row_type":"scanner","row_id":"...","run_id":"...","scanner":"check_wiki","target":"1-wiki","status":0,"stdout_json":true,"stderr_runtime_error":false,"terminal":true}
{"schema_version":1,"row_type":"reconciliation","row_id":"...","run_id":"...","result":"complete","pending":0,"planned_pages":1,"terminal_pages":1,"pending_pages":0,"planned_sources":0,"terminal_sources":0,"pending_sources":0,"planned_claims":1,"terminal_claims":1,"pending_claims":0,"planned_bullet_roles":2,"terminal_bullet_roles":2,"pending_bullet_roles":0,"planned_page_readers":0,"terminal_page_readers":0,"pending_page_readers":0,"planned_scanners":1,"terminal_scanners":1,"pending_scanners":0,"planned_status_writes":0,"terminal_status_writes":0,"pending_status_writes":0}
```
<!-- verification-ledger:end -->

## Recommended next ingests
- {author year — "Title" — the gap this reingest surfaced that it fills; "(verify exists)" if unsure; "none" when none}. Only papers you are confident exist.

## Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
````
