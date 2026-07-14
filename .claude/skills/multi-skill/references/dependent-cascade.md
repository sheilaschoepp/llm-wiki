# Dependent-cascade mechanics

Shared reference for the dependent-cascade step in `forget`, `supersede`, and `ingest` (existing-source mode). Each skill triggers the cascade in its own context — removal, replacement, or reingest — and decides what counts as a *material* change there; this file holds the mechanics that are identical across all three. Read it from the calling skill's cascade step. (It is a shared skill-family reference, like `.claude/skills/multi-skill/multi-skill-memory.md`; edit it only on explicit instruction, and keep it aligned with `CLAUDE.md` → Page Status and the three skills when the cascade rules change.)

## What a dependent is

Every page that lists the changed source page (or the changed page itself) in its `sources:` frontmatter, reconciled against the source page's `Concepts and Entities` callout. A page in `sources:` but absent from that callout — synthesis pages especially, which never appear there — is still a dependent and still cascades.

## Material vs non-material change

The calling skill defines what *material* means in its context (a removal that drops support, a supersession that flips a result, a reingest that corrects a claim a dependent built on). Given that judgement:

- **Material** → set `status: needs-update` with a precise `needs_update_reason:` that names the specific claim or support that changed and what a later re-ingest or the user must resolve — a hand-off, not a bare label (matching what `audit` reads back). A genuine `Contradictions`/`Tensions` entry is the schema-valid alternative. **If the dependent already carries a `needs_update_reason:`, append the new cause rather than overwriting, so the prior hand-off survives.**
- **Non-material** (extra evidence, typo fix, schema migration, tighter wording with no claim impact, a still-correct fuller write-up, a cosmetic change) → no cascade. Touch `updated:` only where the `Sources` callout changed mechanically, and note "no cascade, cosmetic" where the skill logs its cascade decisions.

## Source-support bookkeeping (every touched page)

- Update `sources:` — drop a removed source page; add a replacement only if the page genuinely draws on it.
- Recompute `source_count` as the length of the resulting `sources:` list — never a blind ±1.
- Keep the `Sources` callout in sync with `sources:`.
- Reconcile any body bullet that attributed a claim to a now-removed or now-changed source.

## verified_hash / status reset

Verification is claim-level (see `CLAUDE.md` → Page Status). When a cascade adds or changes a non-obvious claim on a `verified` dependent without re-fact-checking that claim against the raw — **including adding a new claim bullet, or retargeting a citation to a different source** — mark just that claim `*[unverified]*` (Bullet Markers) and the page stays `verified` with the marked claim as the pending delta: `verified_hash` excludes marked claims, so the hash does not move, and the next `audit` re-checks only it. **A single added statement is this case — mark the statement; it is never grounds to reset the whole page.** Reset the page to `status: draft` (stripping its now-stale `verified_hash:` in the same edit; a non-`verified` page carries none, a later `audit` re-adds it on verify) only for a change a claim marker cannot carry: a change to existing *unmarked* (already-checked) prose that you leave unmarked, an embed added or removed, or a `Sources` / `sources:` entry added or removed — a support-level change that alters what the page rests on rather than one locatable claim. If you do not reset such a page explicitly, `lint` demotes it via `verified_hash` on its next run anyway — set it so the page is honest immediately. Mechanical frontmatter touches (`updated:`, `source_count:`) are hash-safe.

**Verification-neutral link maintenance re-stamps instead of demoting** (CLAUDE.md → Page Status, the verification-neutral allowlist). Two link operations change no claim and so keep the page `verified`: wrapping an already-present plain-text reference in a wikilink (the rendered display stays byte-identical and the target page exists — the `unlinked_page_mention` fix), and a stale-path repair that rewrites an inbound link to the *same* page under its new path/name (display unchanged). For these, apply the edit and **re-stamp** `verified_hash:` to the fresh `body_hash.py` output in the same pass, keeping `status: verified` — no fact-check. This carve-out is *only* those two operations. Changing *which* source backs a claim — a `sources:` add or removal, a citation retargeted to a different source page or a different locator — is claim-relevant, not neutral: mark `*[unverified]*` or demote as above. When unsure whether a link edit changes a claim, treat it as non-neutral and demote. Note any `verified → draft` demotion in the log entry so the audit trail captures the regression.

## Under-supported pages

- **Zero-source page** (including an author entity left with no surviving source it authored): surface via `AskUserQuestion` — quarantine it (`forget`), re-source it, or set `status: needs-update` with a `needs_update_reason:` naming the missing support. A zero-source page cannot sit as a clean draft.
- **Synthesis dropping to one source**: this violates the two-source rule unless made an explicit stub. Surface via `AskUserQuestion` — set `single_source_stub: true`, re-source it, or hand off to `forget`. Never leave a lint-failing single-source synthesis behind.

## Approval and reciprocity

Each cascade decision is gated per the calling skill's approval rules (`AskUserQuestion`, one decision per call, never batched). The reciprocal edit on the other page is part of the approved action for that decision, not a separate later pass.

## Verifying the cascade landed

After applying the cascade, read back every touched page and confirm `sources:`, `source_count:`, and the `Sources` callout agree on each, and that no inbound body-prose wikilink to a removed or renamed page is left dangling (find these with `.claude/skills/multi-skill/references/inbound-reference-discovery.md`; `lint`'s `check_wiki.py` does not catch them). For preserved-file checks (quarantined/superseded copies exist and are not git-ignored), see `.claude/skills/multi-skill/references/quarantine-path-convention.md`.
