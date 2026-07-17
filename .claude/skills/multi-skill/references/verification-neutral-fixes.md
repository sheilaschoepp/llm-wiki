# Verification-neutral fixes

The shared operational spec for the verification-neutral fix allowlist — the closed set of determinate, meaning-preserving edits that a skill may apply to a `status: verified` page and then **re-stamp** `verified_hash:` for, instead of demoting the page to `draft`. Run by `lint` (Step 3, its own format fixes) and `audit` (Step 7, the de-hyphenation / spelling / link-wrap fixes), so the logic lives in one place rather than drifting across both copies.

This file is the skills' shared runtime copy. `CLAUDE.md` → Page Status is the canonical schema statement of the same rule; this reference exists because a skill must be runnable from its own folder plus `multi-skill/` without reading `CLAUDE.md` at runtime (CLAUDE.md → Skill Authoring). It is the verification-neutral companion to `verification.md`, the same way that file is the runtime copy of the ingest-verification spec. `consistency`'s `shared_reference_integrity` guards it as a genuine ≥ 2-skill shared reference.

## Contents

- The principle
- The allowlist (and which skill applies each)
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

A stale-path repair — rewriting an existing inbound wikilink to the *same* page under its new path or name (display unchanged) — is applied by whichever skill runs the rename cascade (`forget` / `supersede` / `ingest`).

A content-identical claim relocation — moving a bullet whose text stays byte-identical and whose meaning its new position does not change (a within-callout reorder is meaning-neutral by construction; a cross-callout move is confirmed meaning-preserving by the moving skill, which treats an uncertain case as a change and demotes) — is applied by whichever skill performs the move (`supersede` / `ingest` / `audit`). A relocation that alters the moved text, or a cross-callout move whose new section changes what the claim asserts, is a change, not a move, and demotes.

## Re-stamp Vs Demote

- Allowlisted edit on a `verified` page → apply it, recompute the hash with `.claude/skills/lint/scripts/body_hash.py`, write the fresh `verified_hash:` in the same pass, keep `status: verified`. No raw re-read.
- Any other unmarked body change (a new or changed non-obvious claim, a reworded bullet even when "it means the same thing", a citation whose source-page target or locator changes, an embed whose target image changes, an edited number or quote) → reset `status: verified → draft` and strip the now-stale `verified_hash:` in the same edit. A prose reword you *judge* faithful is not a string transform you can *prove* claim-neutral — it demotes, and a later `audit` re-verifies.
- When in doubt whether a fix is claim-neutral, treat it as not — demote, don't re-stamp.

## Text-Content Exclusion (The Hard Carve-out)

The two text transforms — de-hyphenation and spelling normalization — apply only to running prose, and must skip every verbatim quote (`"…"`), inline `` `code` `` span, math (`$…$`) span, and proper-noun / title / dataset-or-model-identifier token. A hyphenated compound or US spelling *inside* one of those is not claim-neutral — rewriting it would change what the page asserts the source wrote (a quote would no longer match the source verbatim; an identifier or title would no longer be the thing it names) — so it is excluded: leave the token exactly as written, and if it is the only candidate the page is left untouched. An edit that does change such a token is not on the allowlist and demotes rather than re-stamps.

## Locator Relocation Vs Addition (The Hard Exclusion)

A source-page locator-anchor *relocation* that repositions an **already-present** structural anchor relative to the `#page=N` deep-link without changing which section/figure or page it names (`sec. 3.2, [[…#page=9|p. 9]]` → `[[…#page=9|sec. 3.2, p. 9]]`; lint's `source_locator_incomplete`) is on the allowlist — the reader reads the same locator, so no claim moves.

Hard exclusion: *adding* an anchor to a page-only locator, or *changing* which section/figure/page a locator names (e.g. relabelling abstract-drawn content `sec. 1`), is **not** on the allowlist. That asserts a new fact about where the cited content sits, which only the raw can settle — so it must be confirmed against the raw (then the page earns `verified` from that fact-check), or — since changing which section or page a locator names is a change to an existing claim, not an addition — the page demotes to `draft` for a later `audit` to re-verify. It is never self-re-stamped: a single agent inventing an anchor and stamping its own work `verified` is not verification (it is what produced the abstract→`sec. 1` mislabels). `lint` emits the Critical `verified_anchor_unaudited` when a `verified` page's locator anchor changed versus git HEAD (an addition or relabel; a pure relocation is exempt).
