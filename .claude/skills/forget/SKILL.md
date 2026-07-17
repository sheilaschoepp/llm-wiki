---
name: forget
description: Remove a source page, concept/entity page, synthesis page, source-support link, a single bullet or section, or an attachment that has been decided wrong, retracted, irrelevant, or unwanted. Quarantines removed whole pages and attachments to 2-outputs/forget/quarantine/ and updates downstream source lists, source_count, index, hot, and log. Use when the user asks to remove, delete, drop, discard, retract, purge, get rid of, or take out a wiki page, source, claim, support link, or attachment. Also use when the user says a page is wrong, a mistake, irrelevant, or no longer wanted, even if they don't say "forget". Different from supersede, which replaces content with a corrected version — forget leaves nothing in its place, so a bare "this is wrong" that wants a fix routes to supersede, not forget.
---

# forget

Remove unwanted wiki content without destroying the paper trail.

## Purpose

Forgetting removes content from the active wiki while preserving a quarantined record when a whole page or attachment is removed, and it leaves the wiki graph consistent behind the removal — repairing inbound references, both halves of every inline citation, `source_count`, and the zero-source, single-source-synthesis, author-entity, and `verified_hash` decisions a removal triggers. The cascade (Steps 2, 6, 7) is as much the work as the deletion.

Recoverability differs by scope. Whole pages and attachments are copied to `2-outputs/forget/quarantine/` before deletion, so a vault-navigable, log-linkable copy survives: a git blob is not a page the user can open and link in Obsidian, and a page that was never committed has no git history at all, so quarantine is then its only copy. In-place edits — a bullet or section removed, a support link dropped, an embed deleted — leave no quarantine artifact: they are recoverable from git history only, and not at all if the change was never committed. The cascade plan tags which is which so the user can weigh each veto honestly.

## Conventions (Recap From CLAUDE.md)

- Every wikilink is path-qualified from the repo root, includes `.md`, and uses a pipe-rendered display name: `[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]`. Authors: `[[1-wiki/entities/ashish-vaswani.md|Ashish Vaswani]]`. Attachment embeds `![[...]]` take the path but no pipe. Because no wikilink uses a bare basename, every path-qualified wikilink to a removed page is found by an exact-path grep; un-linked alias or acronym mentions need the separate alias sweep in the inbound-reference-discovery reference.
- No bold and no italic in the wiki body, in `hot.md`, `index.md`, or `log.md`. The bullet markers `*\[unverified\]*` / `*\[tentative\]*` / `*\[disputed — see Contradictions\]*` are the only exceptions. Inline backticks for paths and code are fine.
- Use `AskUserQuestion` for every user-facing decision. One decision per call, never batched — each git-only removal, each zero-source quarantine, each status reset is its own question. Order the recommended option first and mark it `(Recommended)` (CLAUDE.md → Communication style); on these gates the lean is usually clear (the most-likely scope; `proceed` on a deletion the user invoked forget to make; the editorial default for a zero-source or stub call), so declare `no recommendation` only for a genuine no-lean.
- Obtain the operation timestamp **once** at write time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` (the session context provides the date but not the current minute), and reuse that single value everywhere a `YYYY-MM-DD-HHMM` appears in this operation — the quarantine filename, the report filename, the log heading, and the Recent-activity line — never re-running `date` for a later reference, or a minute rollover between calls yields a filename and a link that point at different names (a dangling link).
- Terms: a *cascade plan* (Step 3) is the full preview of every removal, repair, and status change; a *support link* is a source page's listing in a concept/entity/synthesis page's `sources:` frontmatter and `Sources` callout; a *stem* is the raw filename without extension, shared by the source page and its `1-wiki/attachments/{stem}/` folder.

## When To Invoke

Use when the user names a page, source, claim, or support relationship that should no longer be active, with a reason: wrong, retracted, irrelevant, duplicated elsewhere, or simply unwanted.

## When Not To Invoke

- The user wants to replace content with a better version. Use `supersede`.
- The user wants to refresh an existing source page. Use `ingest` in existing-source mode.
- The user wants to remove raw files from `0-raw/`. That is outside this skill — removing the raw is the user's job.

## Procedure

```text
Forget Progress:
- [ ] Step 1: Confirm scope and reason
- [ ] Step 2: Load orientation and find every inbound reference
- [ ] Step 3: Build the cascade plan
- [ ] Step 4: Approve via AskUserQuestion
- [ ] Step 5: Apply removal and quarantine
- [ ] Step 6: Repair source support, links, and downstream status
- [ ] Step 7: Verify the removal landed cleanly
- [ ] Step 8: Write the forget report, then update index, hot, and log
```

1. **Confirm scope and reason.** Capture both — the reason is recorded in the log entry and the cascade plan, so ask for it if the user did not give one.

   **Route before removing.** "Wrong" is a trigger word for both forget and supersede, and forget runs autonomously and leaves nothing in its place. So if the stated reason is that the page is *wrong / a mistake / incorrect* (as opposed to retracted, irrelevant, duplicated, or simply unwanted), the user may want it fixed, not removed — ask one `AskUserQuestion`: remove with nothing in its place (forget), or replace with a corrected version (supersede, or ingest existing-source mode)? Recommend the replace option, and hand off rather than proceeding if the user wants a fix. The three unambiguous reasons (retracted / irrelevant / unwanted) carry no implied replacement and skip this gate. `Duplicated` gets the same one-question ask, for the same reason "wrong" does: a duplicate whose copy holds content the survivor lacks routes to a `supersede` merge (which preserves both), not a bare `forget` that drops it — so confirm the survivor subsumes the target before removing.

   Scope is one of:
   - A single bullet or section.
   - A support link from a source page to a concept/entity or synthesis page.
   - A whole concept/entity or synthesis page.
   - A source page and all support it provides.
   - A single attachment (image embed and the underlying file in `1-wiki/attachments/{stem}/`).

   Use `AskUserQuestion` to confirm scope when the user's wording is ambiguous — one focused question, the five scope options above as choices.

2. **Load orientation and find every inbound reference.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/forget/forget-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Use the memory files to apply prior corrections about scope, cascade aggressiveness, and what counts as "still referenced" before drafting the plan.

   Then find every inbound reference to the target — not only its `sources:` listers, since these are what break when the page disappears — following the shared procedure in `.claude/skills/multi-skill/references/inbound-reference-discovery.md` (anchored stem grep; body-prose wikilinks, located raw-file deep-links, `authors:` lists, `aliases:` strings, and `hot.md` bullets; the `check_wiki.py` blind spot for body-prose links). Collect the hits here and repair them in Step 6, not at a later check.

3. **Build the cascade plan.** Show:
   - What will be removed, each removal line tagged with recoverability: `(quarantined + git)` for whole pages and attachments, `(git history only)` for in-place bullet, section, support-link, and embed removals. Status-change and link-repair lines carry no tag — they are reversible edits.
   - For any in-place removal whose target has uncommitted changes (`git status --short -- <path>` shows it modified or untracked), add `note: uncommitted — no git fallback`, since git-only recovery does not exist until the change is committed.
   - Which pages lose source support; which become single-source or zero-source.
   - Which concept/entity or synthesis pages should become `needs-update`, and which were `verified` (a body change demotes them to `draft` in Step 6).
   - Which inbound body wikilinks (from Step 2) need rewriting or removal, and in which pages.
   - Any attachment file in scope that a surviving page still embeds (Step 5 must keep it, not orphan it).
   - Any author entity page left with no remaining source support.
   - Any synthesis page dropping to exactly one source (needs a deliberate stub-or-remove decision — `single_source_stub: true`, re-source, or `forget` — not a blanket `needs-update`); a synthesis dropping to zero sources takes the zero-source decision instead (`single_source_stub: true` is invalid with no sources).
   - Which `hot.md` Open-threads/Watchlist bullets reference the target.
   - Where quarantined content will go; if forgetting a source page whose `0-raw/` file remains, note the standing `uningested_raw_source` lint Critical that persists until the raw is removed or the source re-ingested.

   Example cascade plan:

   ```text
   Target: forget source page [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]
   Reason: paper retracted by authors
   Will be removed:
     - 1-wiki/sources/Vaswani2017AttentionIA.md                          (quarantined + git)
     - 1-wiki/attachments/Vaswani2017AttentionIA/ (fig-1.png, fig-3.png)  (quarantined + git)
   Pages losing source support:
     - [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] (2 sources -> 1, single-source)
     - [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] (1 source -> 0, zero-source)
   Status changes:
     - Scaled Dot-Product Attention -> needs-update (lost a supporting source — an unmarked change to verified content, so it exits `verified`; flagged needs-update for the lost support)
     - Multi-Head Attention -> ask whether to quarantine (zero-source)
   Inbound links to repair (git history only):
     - [[1-wiki/concepts/self-attention.md|Self-attention]] Connections bullet links the removed page -> rewrite/remove
   Shared attachments to keep live:
     - fig-1.png is also embedded by [[1-wiki/entities/some-entity.md|some entity]] -> keep in place, do not move
   Quarantine targets:
     - 2-outputs/forget/quarantine/quarantine-2026-05-04-1430-Vaswani2017AttentionIA.md
     - 2-outputs/forget/quarantine/attachments/Vaswani2017AttentionIA/
   hot.md: remove Open-threads bullet naming Multi-Head Attention
   ```

4. **Approve via `AskUserQuestion`.** Do not remove content silently. The cascade plan is the user's full preview; approval works in two tiers, decided by a binary test on each line — does it delete a file or remove content, or is it only a reversible edit?
   - **Tier 1 — the single plan approval** authorizes every reversible edit and every edit *mechanically entailed* by an approved deletion: the enumerated status flips, `source_count` recomputes, inbound body-wikilink rewrites/removals, and the support-strips and surviving-page embed removals a page or attachment deletion forces on the pages that survive. These are named on the plan for individual veto but ride under the one approval, and each is *contingent on its triggering deletion* — if that deletion is vetoed in Tier 2, its entailed edits do not apply (never strip a still-live source from its dependents).
   - **Tier 2 — its own `AskUserQuestion`** before executing, for every line that deletes a file or removes content unrecoverably in place: each whole-page deletion; each attachment **file** deletion individually (a `{stem}/` folder is confirmed file by file, never as one question — `CLAUDE.md` Safety: every single file individually, not in bulk); and each *standalone* in-place removal whose target is itself the thing being forgotten — an in-place bullet/section removal, a support-link removal, a standalone embed removal whose underlying file stays live. Show the exact text being removed; when the target carries `note: uncommitted — no git fallback`, state that the removal is permanent (no git recovery) so the user vetoes or commits first knowingly. Each zero-source page's quarantine decision is also its own call. (A removal *entailed* by an approved parent — an embed under its attachment, a support-strip under its source page — rides under that parent in Tier 1; only a *standalone* removal that is itself the named target takes its own Tier-2 call.)

   One decision per call, never batched. Apply only what the user approves. If a veto mid-sequence would leave a removed page with surviving inbound references, either restore the page from quarantine and abort the forget (`references/removal-mechanics.md` → Restore From Quarantine, which lists the cascade edits to reverse), or record the accepted dangler explicitly (a one-line note in the Step 8 log entry, so a later lint/audit reads it as intentional) — never leave a silently inconsistent half-cascade. The same applies to an *interrupted* run: if forget stops between Step 5 and Step 8 (some quarantines or edits landed, the cascade incomplete), treat the wiki as half-cascaded — re-run Step 2 discovery and the Step 7 checks before any further edit, and use Restore From Quarantine to reverse a removal that cannot be completed cleanly. If the user pauses, wait for their next message.

5. **Apply approved removal.** This step is the dispatcher; the exact copy, verify, and move command sequences live in `references/removal-mechanics.md`. Run them only after Step 4 approval. Three ordering invariants hold regardless of scope and must not be reordered even if the reference is skipped: copy to quarantine and confirm the copy exists, is byte-identical to the original (`cmp -s` for a file, `diff -rq` for a folder — existence/`test -f` passes on a truncated binary), and is not on a git-ignored name (`git check-ignore -q` returns non-zero) before unlinking the original; for any attachment removal (single file or whole folder), remove embeds from referencing pages before unlinking the underlying file; all `status:` changes happen in Step 6, not here.
   - Bullet/section: remove or rewrite only the approved text — a *section* removal empties the callout to its schema placeholder (`> - None noted` on source pages, `> - None yet` elsewhere) and never deletes the callout, since every required section must stay present. If the removed bullet anchors a surviving Key Claim (its verbatim quote plus locator in Evidence), flag it — re-anchor the claim or remove it too. If the bullet held an image embed, follow the attachment branch for the underlying file.
   - Support link: remove the source from `sources:` and the `Sources` callout; recompute `source_count` as the length of the surviving `sources:` list, never a blind decrement. Reconcile any body bullet that attributed a claim to the now-removed source.
   - Concept/entity or synthesis page: copy to quarantine, then delete from `1-wiki/`.
   - Source page: remove embeds and source-support entries from every supported page first, then move the `1-wiki/attachments/{stem}/` folder — but keep any file a surviving page still embeds (the plan lists these), moving only the unshared files. See the reference for the shared-attachment check and folder-move verification. Also reconcile every inline body citation that named the removed source — both halves of the canonical form: the `[[1-wiki/sources/{stem}.md|…]]` source-page wikilink AND its paired `[[0-raw/…/{stem}…#page=N|…]]` raw deep-link — by rewriting or removing the citing bullet, so no surviving claim keeps an unanchored deep-link to the removed source. Step 2's discovery already collected that raw-link half (via `inbound-reference-discovery.md`'s anchored `0-raw/…{stem}…#` grep, which the source-page-stem grep and `check_wiki.py` both miss), so reconcile each such hit alongside its paired source-page wikilink.
   - Single attachment: remove the embed from every referencing page first — on a source page, also remove or rewrite the parent locator bullet so no orphaned `fig. N, p. M` line points at a missing image; on a concept/entity page the embed sits in `Idea` with no locator bullet, so remove the bare embed line and confirm the surrounding prose still stands — then copy-verify-and-quarantine the file per `references/removal-mechanics.md` (confirm the copy before unlinking the original). Drop the entry from the source page's `attachments:` frontmatter, and touch `updated:` (Step 6) even on an attachment-only forget that has no support cascade.

6. **Repair source support, links, and downstream status.**
   - Rewrite or remove every inbound body wikilink found in Step 2 so the wiki has no dangling prose links to the removed page. A page that only body-links the removed page is not a `sources:` dependent, but rewriting or removing that bullet still changes checked content, and — because the target is gone, not moved — it is not a verification-neutral stale-path repair: on a `status: verified` page it is an unmarked body change, so demote the page to `draft` and strip its `verified_hash:` in the same pass here (per `.claude/skills/multi-skill/references/dependent-cascade.md` → verified_hash / status reset), not left to lint's later hash check.
   - Apply the shared dependent-cascade rules in `.claude/skills/multi-skill/references/dependent-cascade.md` for the pages this removal touches: the `needs_update_reason:` hand-off and append-don't-overwrite rule when a page loses support but stays meaningful (e.g. `lost sole supporting source Vaswani2017AttentionIA; re-source or quarantine`), the `verified_hash` / status reset on any body-changed `verified` page, the zero-source-page decision (including an author entity left with no source), and the single-source-synthesis decision (`single_source_stub: true` / re-source / `forget`). The zero-source-page and single-source-synthesis decisions are each their own `AskUserQuestion` (a genuine choice — Tier 2 in Step 4); the routine `needs_update_reason:` hand-off and the `verified_hash`/status reset ride under the plan approval as entailed edits (Tier 1).
   - Touch `updated:` on every page whose frontmatter or body you changed.

7. **Verify the removal landed cleanly.** Before touching the log, read back every changed page and confirm:
   - Each page that lost support reads coherently; no orphaned locator bullet or dangling embed remains.
   - The cascade landed cleanly (`.claude/skills/multi-skill/references/dependent-cascade.md` → Verifying the cascade landed): no inbound body-prose wikilink still points at a removed page (confirm by eye against the Step 2 list — `check_wiki.py` misses these); when a source page was forgotten, no surviving inline citation keeps an unanchored `[[0-raw/…/{stem}…#page=N|…]]` raw deep-link to it; every alias/acronym candidate surfaced in Step 2 was dispositioned (wikilinked to a survivor, rewritten, or left with an explicit note — not an un-dispositioned live mention); and on every touched page `source_count == len(sources:) == count(Sources callout bullets)`; and every author entity that lost its last supporting source took the zero-source decision (quarantine / re-source / `needs-update` with reason), none left sitting as a clean `draft` (the case the Step-2 `authors:` sweep surfaces). If Step 5 flagged a removed Key Claim's verbatim anchor, confirm the claim was re-anchored to a surviving Evidence quote+locator or removed — no surviving Key Claim is left without its anchor.
   - Run `python3 .claude/skills/lint/scripts/check_wiki.py "1-wiki"` on every forget to confirm no embed or `sources:` link is left dangling (it does not catch body-prose wikilinks — those are the by-eye check above).
   - Preserved copies verify (`.claude/skills/multi-skill/references/quarantine-path-convention.md` → Verifying the preserved copy): each quarantined page and attachment exists at its recorded path AND is byte-identical to the original it preserved (`cmp -s` / `diff -rq` — existence alone passes on a truncated copy), and `git check-ignore -q <path>` returns non-zero (not ignored) for each preserved copy — run these as commands, not by eye, since a truncated copy or one on a git-ignored name is silently lost. See `references/removal-mechanics.md` for restoring a file if a check fails.

   Fix anything that fails before logging. If a failure can't be resolved inside forget's scope, stop and surface it.

8. **Write the forget report, then update `index.md`, `hot.md`, and `log.md`.** First save the operation report to `2-outputs/forget/forget-YYYY-MM-DD-HHMM-{target}.md` (create the folder if needed; timestamp from `TZ='UTC' date '+%Y-%m-%d-%H%M'`, the same stamp as the log heading). `{target}` is the removed page's stem or slug — the raw stem for a source page, the kebab slug for a concept/entity/synthesis page, or a short kebab slug of the target for a bullet or support-link removal. The report carries the operation summary and the `## Self-report` section (per `.claude/skills/multi-skill/references/self-report.md`); the log entry then links it. Report shape:

```markdown
---
kind: forget
date: YYYY-MM-DD
target: {target}
reason: {reason}
---
# Forget: {target} - {reason}

- Quarantined: [[2-outputs/forget/quarantine/quarantine-YYYY-MM-DD-HHMM-{filename}.md|quarantine-YYYY-MM-DD-HHMM-{filename}]] (or "none")
- Quarantined attachments: {stem}/fig-1.png, {stem}/fig-3.png (or "none")
- Removed support: {source} no longer cited by [[1-wiki/concepts/self-attention.md|self-attention]] (or "none")
- Updated: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]]
- Marked needs-update: [[1-wiki/concepts/layer-normalization.md|layer normalization]] (or "none")

## Self-report
- {a specific limitation that bit forget this run — a scope it misjudged, a cascade case it mishandled, a deletion gate it had to stop at} → upgrade: {how the forget skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Then remove the forgotten page's entry from `index.md` (Sources/Entities/Concepts/Syntheses), and confirm it no longer appears there. Remove or rewrite any `hot.md` Open-threads, Watchlist, or stale Recent-activity bullet that named the target (Active focus is user-owned — surface a mention there rather than auto-rewriting it), and add a Recent-activity line for this forget in the schema's `- [YYYY-MM-DD HH:MM] forget | {target}` form (24-hour UTC, the same timestamp as the log heading). Then prepend the `log.md` entry, which links the report:

```markdown
## [YYYY-MM-DD HH:MM] forget | {target} - {reason}
- Report: [[2-outputs/forget/forget-YYYY-MM-DD-HHMM-{target}.md|forget-YYYY-MM-DD-HHMM-{target}]]
- Quarantined: [[2-outputs/forget/quarantine/quarantine-YYYY-MM-DD-HHMM-{filename}.md|quarantine-YYYY-MM-DD-HHMM-{filename}]] (or "none")
- Quarantined attachments: {stem}/fig-1.png, {stem}/fig-3.png (or "none")
- Removed support: {source} no longer cited by [[1-wiki/concepts/self-attention.md|self-attention]] (or "none")
- Updated: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]]
- Marked needs-update: [[1-wiki/concepts/layer-normalization.md|layer normalization]] (or "none")
```

## Edge Cases

- **Historical and quarantined content reference removed pages.** Leave outputs and quarantined pages unchanged; they are history. Step 2 greps `1-wiki/` only by design — wikilinks from quarantined or output files into the live wiki, from a surviving page into a quarantined output (e.g. a synthesis `origin:` pointing at a now-quarantined query), and between quarantined pages are all frozen danglers, not repaired and not lint findings. `1-wiki/log.md` lives inside the grep scope but its historical entries are frozen too — exclude log.md matches from the repair set.
- **Only one source support link is wrong.** Do not delete the whole note if other sources still support it.
- **An author entity is also a concept-supporter.** An entity counts as still supported if it remains an author on any surviving source or appears in any surviving `sources:` list; quarantine only when both are empty. An author entity kept despite losing all source support must take the zero-source decision (quarantine / re-source / `needs-update` with a `needs_update_reason:` naming the missing support) — it must not be left sitting as a clean `draft`.
- **Botched, vetoed, or interrupted forget.** The quarantine copy is the rollback source, not something to improvise: restore via `references/removal-mechanics.md` → Restore From Quarantine and reverse the cascade (Step 4 covers the mid-cascade-veto decision). In-place bullet, support-link, and embed removals were never quarantined, so they recover from git only if the change was committed.

## Limits

- Always ask before removal — `forget` deletes wiki content, and silent removal destroys context the user may need to recover later; the cascade plan in Step 3 and the per-item approvals in Step 4 are the user's chance to veto.
- Never modify or delete `0-raw/`.
- Never rewrite historical log entries.

## Quarantine Path Convention

Pages quarantine to `2-outputs/forget/quarantine/quarantine-YYYY-MM-DD-HHMM-{filename}.md` (date-prefixed). Attachment files and whole-stem folders move to `2-outputs/forget/quarantine/attachments/{stem}/` with their original names — no date stamp, because the `{stem}` folder is the grouping key. For the name-clash suffix rule (`-N` before the extension; the `.gitignore` trap) and the preserved-copy verification, see `.claude/skills/multi-skill/references/quarantine-path-convention.md`; point the log link at the suffixed name.
