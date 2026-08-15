---
type: check-data
check: unlinked_page_mention
updated: 2026-08-14
---

# Alias detect-exemptions

Display forms excluded from `unlinked_page_mention`'s matching vocabulary while staying in their page's `aliases:` for Obsidian search and `[[` autocomplete.

Read at import by `check_wiki.py` (`_load_alias_detect_exempt`). One entry per line under `## detect-exempt`:

```text
- <page-stem> :: <display form>
```

The form is matched lowercased, and the entry is scoped to that one page: exempting `interaction` for `interaction-effect` leaves an identical form on any other page detecting normally.

## What this is for

The check finds an existing page's title or alias sitting unlinked in another page's prose. That is a good check for a distinctive multi-word form and a poor one for a form that is also ordinary English. A form like bare `interaction`, in a corpus about agents interacting, fires constantly and almost never on a genuine reference — and every hit costs a per-occurrence judgement plus a permanent entry in `unlinked-mention-ignore.md`.

Dropping such a form from `aliases:` is the wrong fix twice over: it is the form a writer actually types into `[[`, and in this corpus the genuine references are written in the bare form too, so the page would lose its retrieval handle *and* its detection. The exemption separates the two jobs — the YAML keeps the form for retrieval, this file removes it from detection.

## What it costs

An exempted form stops being detected anywhere, so its genuine unlinked references stop being flagged too. That is the trade, and it is why every entry below carries its measured precision.

Exempt a form only when the measurement says the judgement cost is not repaid, and prefer exempting **one form of a page** over exempting the page: a multi-word form usually keeps earning its place while the bare one does not. `interaction effect` still detects; bare `interaction` does not. `scaling laws` still detects; bare `scaling` does not.

The failure mode is a missed link, never a wrong one. A stale entry — the page is gone, or no longer carries the form — is inert and reported as `stale_alias_exempt`.

## Adding an entry

Measure first. An entry needs a genuine-versus-generic count over the form's actual occurrences, produced the same way the verified-ignore judgements are: read every occurrence in context. Record the count in the comment beside the entry so a later reader can re-litigate it against evidence rather than taste.

Removing an entry re-surfaces every occurrence of that form, which is the intended way to reverse the decision.

## detect-exempt

<!-- Each entry -->
