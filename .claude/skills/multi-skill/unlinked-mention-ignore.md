---
type: lint-data
purpose: Curated verified-ignore list for the `unlinked_page_mention` lint check.
updated: 2026-07-11
---

# Unlinked-mention verified-ignore

Data for the `unlinked_page_mention` check in `scripts/check_wiki.py`. The script parses the `## verified-ignore` section below at load time; this file is the single source of truth for the list (the script holds no hardcoded copy).

The check is heuristic: it matches an existing page's title or alias appearing as plain text in another page's prose. Whether a given occurrence is a **genuine reference** (wikilink it) or **generic wording** (leave it) is a judgement CLAUDE.md → Wikilink Format leaves to a reader — a homograph, a common noun that happens to be a page title, or the term sitting inside a larger established phrase is not a reference to that page. `audit` makes that call per occurrence (audit Step 7). An occurrence it confirms is generic is recorded here, so the next lint run does not re-flag it and the next audit does not re-litigate it.

This file is **agent-writable data, not script logic** (CLAUDE.md → Stay In Your Lane lists it alongside `hyphenation-lists.md` and the memory journals). `audit` grows it autonomously; it never edits the check's code. **Every new entry must be sub-agent-verified before it is written**: spawn independent sub-agents and add the entry only on consensus (default ≥ 2 of 3 confirm the occurrence genuinely reads as generic wording rather than a reference to that page); on a split or refutation, leave it out and wikilink the occurrence. A malformed or unreadable line is skipped, not fatal; a missing file degrades the check to fully unsuppressed (the safe direction — every mention flags again), so keep it valid.

## Entry format

One entry per line under `## verified-ignore`, three `::`-separated fields:

```text
- {page path} :: {target stem} :: {phrase}
```

- **page path** — repo-root-relative path of the page the mention sits *in* (the page lint flagged), e.g. `1-wiki/concepts/{host-slug}.md`.
- **target stem** — the stem of the page being mentioned (the one lint says should be linked), e.g. `{target-slug}`.
- **phrase** — the prose phrase the generic occurrence sits in, copied from the page, long enough to pin the occurrence. Matched case-insensitively, with flexible whitespace; everything else matches literally.

Two properties make an entry safe:

- **Page-scoped.** Genuine-versus-generic is a per-page call, so an entry only ever suppresses the mention on the page it was recorded for. The same wording on another page is judged again, and a genuine reference there still flags.
- **Phrase-anchored, so self-invalidating.** The entry suppresses only occurrences falling inside the recorded phrase. Reword the sentence and the entry stops matching, so the mention re-flags. A stale entry suppresses nothing and is inert — the failure mode is a re-flag, never a silently swallowed genuine reference.

An entry suppresses one occurrence context, not a whole page: other unlinked mentions of the same target on that page still flag.

Dead entries do not accumulate silently: lint's `stale_mention_ignore` check reports any entry that suppresses nothing — because the page it was recorded on is gone, its target page is gone, or no unlinked mention falls inside the recorded phrase any more (the wording changed, or the mention has since been wikilinked). `audit` deletes a reported entry; that needs no sub-agent verification, since the check has already proven the entry is inert. If the occurrence still exists but was reworded, re-record it against the current phrase — re-confirming it still reads as generic wording — rather than editing the old phrase to match, which would carry the old judgement onto text nobody re-checked.

## verified-ignore

<!-- Example of the entry shape (schematic paths; a real entry names real ones and has no leading `#`):
# - 1-wiki/concepts/{host-slug}.md :: {target-slug} :: reasoning proceeds as a chat chain
-->
