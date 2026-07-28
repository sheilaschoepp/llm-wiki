# ingest — Report Shapes (Step 8)

The two report body shapes `ingest` writes, and the `Recommended next ingests` spec they close with. Read this when Step 8 writes the report. The verification procedure itself — the two packets, the tiered refuter model, and the routing rule that sends ingest's report here — is in the shared spec `.claude/skills/multi-skill/references/verification.md`; this file holds only the templates, which no other skill uses.

Both modes write to `2-outputs/ingest/ingest-YYYY-MM-DD-HHMM-{stem}.md` (`HHMM` is the 24-hour UTC from `TZ='UTC' date '+%Y-%m-%d-%H%M'` at write time). This report is ingest's single operation output — never a second file, and never another skill's folder.

Record both packet results. If frames or a non-frame depth purpose were used, include them in the report — not on the source page — so the framing/scope decision is recoverable later.

## Recommended Next Ingests

Every report closes with a `Recommended next ingests` section: the papers that would fill a gap *this ingest surfaced* — a single-source page this ingest created or left wanting its primary, a watch item it added, a dangling concept that now warrants its own source, or uningested prior work this source cites and leans on. One entry per paper: author and year, the title, and one line on the gap it fills. This is ingest-derived, not a generic literature dump: list only what this source's gaps actually point to.

**Honesty guard (the academic-integrity rule applies):** list only papers you are confident genuinely exist — never fabricate a title, author, or venue, and mark any whose existence you are unsure of `(verify exists)` rather than asserting it. The section is `none` when the ingest surfaced no specific next-source — it is not a quota, so do not pad it.

## New-Source Report Shape

```markdown
---
type: ingest-report
date: YYYY-MM-DD
stem: "{stem}"
frames: []  # one or more frame texts, or empty if unscoped
purpose: "{non-frame depth purpose, or empty}"
---

# Ingest report: {stem}

Touched:

- [[1-wiki/sources/{stem}.md|{stem}]]
- [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]

## Source-faithfulness packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on metadata, TL;DR, contribution, key claims, evidence pointers, image fidelity.

## Note-quality and coverage packet
Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Notes on one-idea clarity, simple language, source support, image discipline, coverage gaps, intra-page redundancy.

## Fixes applied
- Authoring-tier refuter spend: {owed units authored — aggregate/generalization claims; restated numbers; cross-source clauses} owed; {refuter calls} calls (one per owed unit, batched or not) — more calls than owed units means the run escalated past the authoring tier; say so and why. (or `none — no owed units this run`)
- Short bullet per fix made before finalizing (or "none").
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

## Recommended next ingests
- {author year — "Title" — the gap this ingest surfaced that it fills; "(verify exists)" if unsure}, grouped if several. Only papers you are confident exist. "none" when the ingest surfaced no specific next-source.

## Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

## Existing-Source (Reingest) Report Shape

```markdown
### Source-faithfulness packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/sources/{stem}.md|{stem}]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}

### Note-quality and coverage packet
- Result: pass | fail
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Pages checked:
  - [[1-wiki/concepts/self-attention.md|self-attention]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}
- Authoring-tier refuter spend: {owed units authored — aggregate/generalization claims; restated numbers; cross-source clauses} owed; {refuter calls} calls (one per owed unit, batched or not) — more calls than owed units means the run escalated past the authoring tier; say so and why. (or `none — no owed units this run`)
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

### Recommended next ingests
- {author year — "Title" — the gap this reingest surfaced that it fills; "(verify exists)" if unsure; "none" when none}. Only papers you are confident exist.

### Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```
