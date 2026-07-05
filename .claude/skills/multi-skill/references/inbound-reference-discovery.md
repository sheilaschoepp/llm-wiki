# Inbound-reference discovery

Shared reference for the "find every inbound reference to a wiki page" step in `forget` (Step 2), `supersede` (Step 2), and `ingest` (the legacy-page / rename cascade). Read it from the calling skill's discovery step. It is a shared skill-family reference, like `.claude/skills/multi-skill/multi-skill-memory.md`; edit it only on explicit instruction, and keep it aligned with the three skills and `lint`'s `check_wiki.py` coverage when the discovery rules change.

Find every inbound reference to the target page, not only the pages that list it in `sources:` — these are what break when the page is removed, renamed, or replaced. Grep the target's repo-relative path stem **anchored** on its trailing `.md` and the delimiter that follows every real wikilink (`]`, `|`, or `#`), so a prefix-of-a-longer-stem neighbour does not over- or under-match:

```text
grep -rnE "1-wiki/concepts/positional-encoding\.md(\]|\||#)" 1-wiki/
```

Eyeball each hit to confirm it links this exact target. Cover all of these:

- **Body-prose wikilinks**: `Connections`, `Not This`, `Contradictions` bullets, inline gloss-on-first-use links, and synthesis `Evidence` mappings.
- **Source-page `authors:` lists**, in case a removed or renamed source leaves an author entity page with no remaining support.
- **The target's own `aliases:` strings**, grepped across `1-wiki/`, to catch prose that names the page by acronym or old name without a wikilink — surface these as candidates, weaker than a wikilink match.
- **`hot.md` Open threads and Watchlist bullets** that name the target.
- **Located raw-file deep-links** (when the target is a *source* page being removed, renamed, or re-extracted): inline claim citations on concept/entity/synthesis pages pair the source-page wikilink with a `[[0-raw/<category>/<stem>.<ext>#page=N|<anchor>, p. M]]` deep-link into the raw. These point at `0-raw/`, not at the source page, so the source-page-stem grep above misses them entirely. Sweep for them separately, anchored on the raw stem and the `#page=` (or `#` for a non-PDF locator) that follows a real deep-link:

  ```text
  grep -rnE "0-raw/[^]]*<stem>[^]]*#" 1-wiki/
  ```

  Each hit is the *located* half of a two-form citation whose source-page wikilink half the stem grep already found; rewrite or drop it alongside its paired source-page link (a rename transplants the deep-link into a page whose pagination may differ — re-verify or `*[unverified]*`-mark, never blind-swap).

`lint`'s `check_wiki.py` catches dangling image embeds and dangling frontmatter `sources:`, but not dangling body-prose wikilinks or these `0-raw/` deep-links — so both must be found here and repaired by the calling skill, not left to a later check.

When a repaired inbound link sits on a `status: verified` page, a stale-path repair that rewrites the link to the *same* page under its new path or name (display unchanged) is a verification-neutral edit: it changes no claim, so re-stamp `verified_hash:` in the same pass and keep the page `verified` rather than demoting it — see `.claude/skills/multi-skill/references/dependent-cascade.md` (verification-neutral link maintenance) and `CLAUDE.md` → Page Status. A rewrite that retargets the link to a *different* page is not neutral and follows the demote / mark rule there.
