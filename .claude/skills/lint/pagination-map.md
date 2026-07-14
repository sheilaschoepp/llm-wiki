---
type: lint-data
purpose: Curated per-raw pagination map for the locator-page lint checks.
updated: 2026-07-12
---

# Pagination map

Data for the pagination-aware locator checks in `scripts/check_wiki.py` — `locator_page_mismatch`, and the anchor-only exemption inside `citation_locator_incomplete` / `source_locator_incomplete`. The script parses the `## <raw path>` sections below at load time; this file is the single source of truth (the script holds no hardcoded copy).

## Why this file exists

A locator states two page facts: **where** the page sits in the file (`#page=N`, the physical page — the Nth page of the PDF, what the deep-link opens) and **what** the page prints (`p. M`, the number a reader cites). These are equal only when a PDF is paginated 1, 2, 3… from its first physical page. They diverge whenever it is not:

- proceedings that start at a high number (physical page 1 prints `4171`);
- an appendix that restarts its numbering (physical page 20 prints `1`) or continues the body's sequence;
- a page that prints no number at all (a divider, a full-page figure, an unpaginated body).

The printed number is a fact about the raw, not derivable by rule, and getting it wrong yields a confidently-wrong citation that renders plausibly and passes every structural check. So it is recorded here once per raw, before any locator is written, and `locator_page_mismatch` checks every `p. M` against it.

`check_wiki.py` never opens a PDF — it reads only this map — so lint stays cheap and dependency-free. `scripts/pagination_map.py` proposes a map from the PDF's rendered footers; **a human confirms each line against a rendered footer before it lands** (a wrong `none` would license stripping a correct printed page from a citation and certifying the damage), then adds the section here.

This file is **agent-writable data, not script logic** (`CLAUDE.md` → Stay In Your Lane). A missing or unreadable file degrades every raw to "unregistered": the locator checks fall back to the older `app.`-anchor heuristic and `locator_page_mismatch` does not run — the safe direction, recoverable from git — so keep it valid. A malformed line is skipped, never fatal.

## Entry format

One `## <raw path>` heading per raw — the path as it appears in a `#page=N` deep-link — then one `- <physical> = <printed>` line per page. Illustrative shape (placeholder heading, so the parser ignores it):

```text
## <raw path — e.g. 0-raw/papers/Vaswani2017AttentionIA.pdf>
- 1 = 1             # this PDF is paginated from 1: physical 1 prints 1
- 1-13 = 4171-4183  # a span; both sides equal length, mapped in order (a proceedings offset)
- 14 = none         # this physical page prints no number (divider / full-page figure)
```

- **left side** — the physical page N (the Nth page of the file, what `#page=N` points to). A `lo-hi` span covers a run of pages.
- **right side** — the printed number `M` that page shows, or `none` when it prints nothing. A span on the right must be the same length as the left and maps in order.
- a trailing `# comment` is ignored.

`printed_page(raw, N)` then answers, for any cited page: it prints `M` (a locator must give `p. M`), it prints nothing (a locator cites its structural anchor alone), or the raw is unregistered (the checks fall back rather than invent a fact).

## Registered raws

<!-- One `## 0-raw/…` section per registered raw, added on ingest after the
     footers are eyeballed. Empty in a fresh vault — register a raw when you
     ingest it. The lines below are a schematic example, inert to the parser
     (leading `#`); a real entry has no leading `#` and a literal 0-raw path:
# ## 0-raw/papers/Devlin2019BERTPO.pdf
# - 1-16 = 4171-4186
-->
