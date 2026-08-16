# ingest — report shapes (Step 8)

The two report bodies `ingest` writes to `2-outputs/ingest/ingest-YYYY-MM-DD-HHMM-{stem}.md`, one per mode. They live here rather than in the shared verification spec because only `ingest` writes them: `query`, `synthesis`, and `supersede` record their verification results in their own outputs, so carrying these templates in the shared file made four callers load ~780 words they never use.

The rules the shapes serve — what the claim check and page self-check must record, the `Recommended next ingests` honesty guard, and the Setting Status conditions — stay in `.claude/skills/multi-skill/references/verification.md`. This file is the layout only.

## Contents

- New-source report shape
- Existing-source (reingest) report shape

## New-source report shape


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

## Claim check
Result: pass | fail
- Coverage: {full-text confirmed — the probe used; for a book, the range read in full}
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Claims written this run: {N}. Certified: {N} ({tier breakdown — e.g. 3 at Tier 0, 2 at Tier 1, 9 at Tier 3}). Marked `*[unverified]*`: {N + why each}. Marked `*[tentative]*`: {N + why each}.
- Refuter outcomes: {claims where a refuter refuted or could not confirm, the verbatim quote it returned, and what the orchestrator did — fixed, marked, or discarded the finding after re-grepping the quote; "all held" when none}.
- Notes on metadata, TL;DR, contribution, key claims, evidence pointers, image fidelity.

## Page self-check
Result: run | run with findings
- Fixed now: {cheap local corrections applied — AI tells re-voiced, vague referents named, repeated bullets dropped, missing wikilinks added; or "none"}
- Handed to audit: {page-level findings needing the whole page or the wiki in view — a possible two-idea page, a suspected near-duplicate, an incomplete connection sweep; specific enough to act on without rediscovery; or "none"}
- Notes on one-idea clarity, simple language, standalone read, image discipline, intra-page redundancy.

## Status set
- [[1-wiki/sources/{stem}.md|{stem}]] - verified | draft | needs-update {+ the reason, when not verified}
- One line per touched page. A page left non-`verified` names which of the four Setting Status conditions it failed.

## Fixes applied
- Short bullet per fix made before finalizing (or "none").
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

## Recommended next ingests
- {author year — "Title" — the gap this ingest surfaced that it fills; "(verify exists)" if unsure}, grouped if several. Only papers you are confident exist. "none" when the ingest surfaced no specific next-source.

## Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

## Existing-source (reingest) report shape

```markdown
---
type: ingest-report
date: YYYY-MM-DD
stem: "{stem}"
frames: []   # the page's frames after this run, or empty if unscoped
purpose: "{deep purpose, or empty — carry the prior report's value forward on a normal reingest rather than blanking it}"
---

# Reingest report: {stem}

### Claim check
- Result: pass | fail
- Coverage: {full-text confirmed — the probe used; for a book, the range read in full}
- Late-section detail re-located (proof of raw re-read): {final section/last figure/appendix + the fact checked}
- #page=N link spot-checked: {physical page N + printed page seen there + content confirmed, or n/a (non-PDF raw)}
- Claims written or changed this run: {N}. Certified: {N} ({tier breakdown}). Marked `*[unverified]*`: {N + why each}. Marked `*[tentative]*`: {N + why each}.
- Refuter outcomes: {refutations and "cannot confirm" verdicts with the verbatim quote returned and what was done; "all held" when none}
- Pages checked:
  - [[1-wiki/sources/{stem}.md|{stem}]]
  - ...
- Findings: {short list, or "none"}
- Fixes applied: {short list, or "none"}

### Page self-check
- Result: run | run with findings
- Pages read:
  - [[1-wiki/concepts/self-attention.md|self-attention]]
  - ...
- Fixed now: {cheap local corrections applied, or "none"}
- Handed to audit: {page-level findings needing the whole page or the wiki in view, or "none"}
- Repeated-literal sweep (after any citation fix): the literal(s) searched and the occurrences re-checked and fixed across the wiki (or "no citation fix this run").

### Status set
- One line per touched page: page - verified | draft | needs-update {+ reason when not verified}.

### Recommended next ingests
- {author year — "Title" — the gap this reingest surfaced that it fills; "(verify exists)" if unsure; "none" when none}. Only papers you are confident exist.

### Self-report
- {a specific limitation that bit ingest this run — a rule it lacked, a case it handled wrong (e.g. over-demoting a page on a single added claim), a step it couldn't complete} → upgrade: {how the ingest skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```
