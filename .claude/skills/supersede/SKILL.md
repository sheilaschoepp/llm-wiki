---
name: supersede
description: Replace an active concept/entity page, synthesis page, source page, or specific supported idea with a user-supplied corrected version while preserving the prior view. Use when the user says a note is stale, outdated, wrong, or superseded by newer evidence and wants it fixed, corrected, or revised, or asks to replace, swap, merge, split, or re-extract an existing wiki page or attachment while keeping a record of the prior version. Different from forget, which removes without replacement; different from ingest existing-source mode, which re-derives a source page from its own raw — route a same-raw source-page correction there, and use supersede when the user supplies the replacement (taken on trust, not re-derived from the raw) and it warrants an explicit preserved prior view under 2-outputs/supersede/preserve/.
---

# supersede

Replace content while keeping an audit trail.

## Purpose

Supersede keeps the active wiki current without pretending the older view never existed. The prior view is preserved as a vault-navigable artifact — a `2-outputs/supersede/preserve/` file or an in-callout bullet, browsable in Obsidian and linkable from `log.md` — which is why supersede captures it explicitly rather than leaving it to git: git preserves the bytes, but not a view the user can open and link. (A plain in-place correction from the raw, where a git blob suffices, is `ingest` existing-source mode, not supersede.)

Two terms recur below and refer to distinct things: a **prior-view artifact** is the preserved old content (a `Prior view` bullet inside a callout, or a file under `2-outputs/supersede/preserve/`), while a **log entry** is the dated reverse-chronological line written to `1-wiki/log.md`.

## Conventions (Recap From CLAUDE.md)

- Source-page filenames match the raw source stem exactly; concept/entity/synthesis filenames are kebab-case lowercase. When a supersession also renames a source page (e.g., a legacy kebab-case stem migrating to the raw stem), surface the rename as its own `AskUserQuestion` and cascade the new wikilink to every page that references it.
- Every wikilink is path-qualified from the repo root, includes `.md`, and uses a pipe-rendered display name: `[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]]`. Authors: `[[1-wiki/entities/ashish-vaswani.md|Ashish Vaswani]]`. The pipe-rendered display is required on every wikilink; attachment embeds `![[...]]` take the path but no pipe.
- No bold and no italic in the wiki body. LaTeX math and the bullet markers `*\[unverified\]*` / `*\[tentative\]*` / `*\[disputed — see Contradictions\]*` are the only structural exceptions. Inline backticks for paths and code are fine.
- Use `AskUserQuestion` for every user-facing decision (each replacement, each cascade marking, each attachment swap). One decision per question call.

## When To Invoke

Use when the user names existing wiki content and provides a replacement reason: newer source, corrected interpretation, better concept/entity page split, merge, or schema correction.

## When Not To Invoke

- The change is an ordinary in-place correction of an existing source page from its raw — corrected interpretation, missed evidence, deeper coverage. Use `ingest` in existing-source mode; git preserves the prior version, so no separate prior-view artifact is needed. Reserve supersede for replacements that warrant an explicit preserved prior view: a whole-page or source swap, or a structural split, merge, or re-extraction.
- The user wants removal without replacement. Use `forget`.
- The user wants to add a new unrelated note. Use `ingest`, `query`, or direct editing.
- Two sources disagree and neither replaces the other. Use `Contradictions` or `Tensions`.

## Procedure

```text
Supersede Progress:
- [ ] Step 1: Confirm old content, new content, and reason
- [ ] Step 2: Load hot.md, index.md, supersede-memory.md, and multi-skill-memory.md
- [ ] Step 3: Build supersession plan
- [ ] Step 4: Wait for approval
- [ ] Step 5: Apply replacement and prior-view artifact
- [ ] Step 6: Maintain metadata
- [ ] Step 7: Verify the supersession landed cleanly
- [ ] Step 8: Update index, hot, and log
```

1. **Confirm scope.** **Route before replacing:** the decidable test is the target type — `ingest` existing-source mode only ever reingests a **source page** from its raw, so any correction to a concept, entity, or synthesis page, and any swap, merge, split, or re-extraction, stays in supersede. Route to `ingest` only when the target is a **source page** whose fix is a plain in-place re-derivation from its raw (git preserves that prior version, so no explicit artifact is needed). Reserve supersede for swaps, merges, splits, and re-extractions that warrant an explicit preserved prior view. When it is unclear which the user wants, ask one `AskUserQuestion` (correct-in-place-from-the-raw via ingest / replace-with-an-explicit-preserved-view via supersede) and route accordingly. Scope is one of:
   - Bullet or small section.
   - Whole concept/entity page.
   - Whole source page.
   - Merge/split of notes.
   - A single attachment being replaced by a better extraction (different page render, tighter crop, higher DPI, corrected figure).

2. **Load orientation.** Read `1-wiki/hot.md`, `1-wiki/index.md`, `.claude/skills/supersede/supersede-memory.md`, and `.claude/skills/multi-skill/multi-skill-memory.md`. Find inbound links and source-support relationships by following the shared procedure in `.claude/skills/multi-skill/references/inbound-reference-discovery.md` (anchored stem grep with an eyeball pass; body-prose wikilinks, located raw-file deep-links, `authors:` lists, `aliases:` strings, and `hot.md` bullets; the `check_wiki.py` blind spot for body-prose links). Collect the hits here for the Step 6 cascade and Step 7 verification. Use both memory files to apply prior corrections before drafting any replacement.

3. **Build the plan.** Post a single chat context message that shows:
   - Old text/page.
   - New text/page.
   - Reason for replacement.
   - Where the prior view will be preserved.
   - The target's git state (`git status --short -- <target>`): if it has uncommitted changes, flag that git holds no recoverable pre-edit baseline, and that a small in-callout overwrite has no separate `2-outputs/supersede/preserve/` file fallback (its prior view is the in-callout `Prior view` bullet) — so the user commits first or proceeds knowingly (CLAUDE.md Safety rules).
   - Pages whose `sources:`, `Connections`, or `Concepts and Entities` sections change.
   - For attachment replacements: which file is being replaced, where the prior file will be preserved (`2-outputs/supersede/preserve/attachments/{stem}/preserve-YYYY-MM-DD-HHMM-{name}.png`), the new extraction parameters, and which other pages embed the file.

4. **Ask every decision via `AskUserQuestion`.** One decision per call, never batched; order the recommended option first and mark it `(Recommended)` in its label (CLAUDE.md → Behavioural defaults). Typical questions:
   1. "Apply the replacement on `{target}`?" Options: apply (Recommended) / change-the-new-content / skip / other.
   2. One question per affected dependent page, e.g., "Mark `[[1-wiki/concepts/page.md|page]]` `needs-update` because of the supersession?" Options: mark-needs-update / no-cascade-cosmetic / other.
   3. One question per attachment swap (if any), e.g., "Replace `{file}` with re-extracted version at `{params}`?" Options: replace / keep / other.
   4. One question per new page a split creates, e.g., "Create split page `[[1-wiki/concepts/new.md|new]]` and move the {idea} content into it?" Options: create / adjust-content / skip / other.
   5. One question per merge weaker-page removal, naming the deletion explicitly, e.g., "Merge `[[...weaker...]]` into `[[...stronger...]]`, then delete the weaker page from `1-wiki/` (preserved copy kept under `2-outputs/supersede/preserve/`)?" Options: merge-and-delete-weaker / keep-separate / other. When both pages are `verified` (a duplicate audit surfaced), there is no automatic "stronger" — put the merge-direction (which page survives) in this question; the merged-in content lands on the surviving page as `*[unverified]*` claims, and the survivor keeps `status: verified` unless it gains a new source — a merge that adds the weaker page's source(s) grows the `Sources` callout, an unmarked body change that demotes the survivor to `draft` (Step 6) — per the claim-level model (Step 6, `CLAUDE.md` → Page Status).

   Verification is claim-level for additions on a `verified` page, so status is not a discretionary question (`CLAUDE.md` → Page Status): a supersede that **adds** a new non-obvious claim it does not re-fact-check against the raw in this pass marks that added claim `*[unverified]*`, and the page stays `verified` with the marked claim as its pending delta; a supersede that **changes** an existing claim demotes the page to `draft` (a changed claim moves the hash whether or not it is marked), and a re-extraction that leaves the body text byte-identical stays `verified` with the affected claim marked (see Step 6). Either way the outcome is mechanical, so do not offer "preserve current status" as a choice. Confirm in the plan how each `verified` target lands — an added claim marked `*[unverified]*` (page stays `verified`), or the page demoted to `draft` by a change — and that any demotion will be noted in the log; a page already at `draft` / `needs-update` needs no status question.

   Dependents the plan marks cosmetic (no cascade) are authorized by the single plan approval — each is still named on the plan for individual veto. Only material cascades (those that set `needs-update`), splits, merges, attachment swaps, and the replacement itself get their own call.

   Apply only what the user approves. If the user pauses mid-sequence, wait for their next message.

5. **Apply the supersession.** The command mechanics live in `.claude/skills/supersede/references/preservation-mechanics.md` — the preserve-and-verify guard (`cp` → `cmp -s` for a file / `diff -rq` for a folder → the git-check-ignore exit-1 gate, run *before* any overwrite), the two-tool-call overwrite rule (supersede's overwrite is a Write call for a page or `cp` for a binary, so the Bash guard must exit 0 first and the overwrite is a separate step issued only then — never chained the way `forget` chains `rm`), the name-clash suffix, the capture-timestamp-once rule, the binary-never-through-Read/Write rule, the git-state precheck, and the Restore Active Page rollback. Run the commands from there. Two invariants hold regardless of scope: the prior view is captured — as an in-callout `Prior view` bullet (small replacement), or as a preserve file confirmed byte-identical and not git-ignored (every file scope) — *before* the active content is overwritten, never after (a post-overwrite check can only report a lost prior view, not prevent it); and every `status:` change happens in Step 6, not here. This step owns the per-scope *decisions* below; the reference owns the commands. On any apply failure, follow the reference's Restore Active Page rollback, reverse any cascade edits already made, and surface the failure — never leave a half-applied overwrite.
   - Small replacement: compose the `Prior view` bullet from the exact current text first, then change the active text in the same edit — never reconstruct the old wording from memory. Add the note as the last content bullet, immediately above the callout's `> ^block-id` line (so the block ID stays the callout's last line):
     `> - Prior view, superseded YYYY-MM-DD: {old text}. Reason: {reason}.`
     If the callout already carries a `Prior view` line from an earlier supersession of the same bullet, keep at most one in-callout `Prior view` per callout — the older history lives in git.
   - Whole-page replacement: preserve the old page — and its `1-wiki/attachments/{stem}/` folder if it owns one — per the reference's single-file and folder guards, then overwrite the active page with the Write tool once the guard has passed.
   - Source-page replacement splits on the stem: if the replacement re-extracts the same raw (same stem), replace in place as above. If it is a different source with its own bibkey/stem, the source-page filename must match the new raw stem (CLAUDE.md → Page Filenames), so this is a rename cascade — create the new page at `1-wiki/sources/{new-stem}.md` with its `file:` frontmatter pointing at the new raw (`[[0-raw/...]]`), preserve the old page per the reference guard, re-point every inbound reference found in Step 2 to the new stem — including BOTH halves of every inline citation: the `[[1-wiki/sources/{old-stem}.md|…]]` source-page wikilink AND its paired `[[0-raw/.../{old-stem}…#page=N|…]]` raw deep-link, whose stem also changes. Step 2's discovery already collected the `0-raw/` raw-link half (via `inbound-reference-discovery.md`'s anchored `0-raw/…{old-stem}…#` sweep, which the source-page-stem grep misses), so rewrite each such hit alongside its paired source-page wikilink (apply the Step 6 link-rewrite mechanics here, not deferred). This neutral stem-swap is correct only for a same-source filename migration (a legacy stem → the raw stem, same source — re-stamp `verified_hash:` on any `verified` inbound page); when the new source is genuinely different, the mechanical swap is unsafe — re-judge each inbound page with `dependent-cascade.md`'s genuine-draw test before re-pointing its `sources:` / citation (source B may not support the claim source A backed), and treat the transplanted `#page=N` and printed-page locators as the OLD paper's coordinates: do not carry them over unchanged, but re-verify each against the new raw or mark the claim `*[unverified]*` rather than ship a plausible-but-wrong deep-link. Verify by re-grepping that no inbound link names the old stem in EITHER half, and only then delete the old source page. Surface the rename as its own `AskUserQuestion` (Conventions recap).
   - Split: preserve the current old page per the reference guard before mutating it (a split rewrites the donor page's body), then create the approved new page(s), move only the relevant idea, and leave a connection from the old page. Each split-off page ships schema-complete: full required frontmatter (`type`, `aliases: []` for a concept/entity page, `tags: []`, `sources`, `source_count` matching, `created` today, `updated`, `status: draft`, and `origin:` for a synthesis — use `direct` or a pipe-rendered wikilink to the donor synthesis page, since a split has no query/brief/reflect/compare origin) and the full required callout set for its page type — each callout carrying its block ID, with an empty placeholder where a section has nothing genuine. A split that creates a new synthesis must satisfy the ≥2-source rule or set `single_source_stub: true`. After the split, confirm the donor page still reads coherently and that any citation which relocated with the moved idea now lands on the new page (no orphaned locator left on the donor).
   - Merge: keep the surviving page (the stronger page — `verified` over `draft`, else the higher `source_count`, else ask; or, when both are `verified`, the user-chosen survivor from Step 4 Q5, since there is no automatic "stronger" between two verified pages); first preserve BOTH the weaker duplicate AND the surviving page per the reference guard (the surviving page is overwritten by the moved-in content, so it needs its own preserved snapshot as a rollback source; preserve-and-confirm precedes moving content — a half-moved page must already be preserved), then move useful content into the surviving page, then delete the weaker page from `1-wiki/`. If the user wants outright removal with no preserved view, hand off to `forget` rather than improvising a quarantine here — supersede keeps every prior view under `2-outputs/supersede/preserve/`.
   - Attachment replacement: preserve the existing file per the reference guard (`cmp -s` — this binary cannot be eyeballed or recovered once the original is overwritten), then place the new extraction at `1-wiki/attachments/{stem}/{name}.png` (same path, so existing embeds keep resolving without edits) with `cp` — never the Write tool, which corrupts binaries. Supersede does not re-render the figure itself: the new binary is supplied by the user or re-extracted by `ingest` (`pdftoppm`) out of band, and must already exist on disk at the target path — confirm it is present before the swap; supersede only swaps it in. Record the replacement and its reason in the Step 8 report and log entry (the source page reads as the current state of the world, not its history — `CLAUDE.md` → Source Pages), not as a free-floating note on the page.
   - Any callout written into a new or replacement page carries its block ID as the last line inside the `>` block (`> ^idea`, `> ^evidence`, …; see `CLAUDE.md` → Callout Block IDs). Preserve existing block IDs when editing a callout in place. Page locators on a source page carry a `#page=N` raw-file deep-link whose display holds both the structural anchor and the printed page (`[[0-raw/papers/<stem>.pdf#page=N|<anchor>, p. M]]`, e.g. `sec. 3.2, p. 5`), where N is the physical PDF page in the fragment and M the printed page in the display (see `CLAUDE.md` → Source Support And Verification for the printed→physical offset). On a replacement concept/entity/synthesis page, any non-obvious claim's inline citation uses the two-form canonical citation (source-page wikilink paired with the located raw deep-link; same reference).

6. **Maintain metadata and cascade `needs-update`.**
   - Cascade to dependents: walk every page that referenced the superseded source page, page, or specific claim, because the supersession can invalidate downstream interpretations even when the immediate replacement looks contained. For each dependent, judge whether the supersession materially changes what it claims:
     - Material change (e.g., the new evidence flips a result, a corrected interpretation removes a claim a concept page was building on, the replacement page now covers a different subset of the old idea) → set `status: needs-update` and add a `needs_update_reason:` line naming the supersession.
     - Cosmetic change (typo fix, schema migration, tighter wording with no claim impact) → no cascade. Note "no cascade, cosmetic" in the log entry.
   - Link rewrite (target renamed or removed): when a merge deletes a page or a split/source rename changes a filename, rewrite every inbound wikilink found in Step 2 to point at the surviving target, preserving the pipe-rendered display. This is a required mechanical fix, not a `needs-update` flag — a `needs-update` page with a dead inbound link is still broken. On a `verified` inbound page the status handling splits by what the rewrite means: a same-page stale-path repair (display unchanged, still the same logical page under its new path) is a verification-neutral edit that re-stamps `verified_hash:` in the same pass rather than demoting (`.claude/skills/multi-skill/references/verification-neutral-fixes.md`); a different-source retarget (the link now points at a source that may not support the claim) is not neutral — mark the affected claim `*[unverified]*` or demote per this step's status rule.
   - Attachment content change: when a re-extraction changes the image content (a corrected figure or table, not merely a tighter crop or higher DPI), treat every page embedding it as a dependent — find them by grepping the embed path `1-wiki/attachments/{stem}/{name}` across all of `1-wiki/` (not only the source's own pages — a path-qualified embed can be reused by a page belonging to a different stem). Set `needs-update` on a `verified` embedding page if the corrected image changes what the page asserts (a material change). If the page text still reads correctly but the now-changed image backs a non-obvious claim that has not been re-checked against it this pass, mark that claim `*[unverified]*` and leave the page `verified` (claim-level model, `CLAUDE.md` → Page Status). Because the embed path is unchanged, the page body text is byte-identical, so `verified_hash` does not change and lint's hash check cannot catch a forgotten mark the way it does for a text edit — this mark is the only guard here, so it is mandatory, not discretionary. A pure crop/DPI improvement is cosmetic, no cascade.
   - Preserve `created:` on active pages when replacing in place; new pages from a rename or split take today's `created:` (only in-place replacements preserve it).
   - Touch `updated:`.
   - Status on the edited page (claim-level for additions, `CLAUDE.md` → Page Status): a supersede that **adds** new non-obvious claims (a merge moving content into the surviving page), or that leaves the body text byte-identical (a re-extraction — the embed path is unchanged, so `verified_hash` does not move), marks each such claim it does not re-fact-check against the raw in this pass `*[unverified]*` (`CLAUDE.md` → Bullet Markers), and the page keeps `status: verified`: the marked claims — excluded from, or invisible to, `verified_hash` — are the pending delta a later `audit` re-checks. **A supersede that changes existing claim text demotes the page to `draft`,** because a changed claim's line was already in `verified_hash` and altering it (or marking it) moves the hash — marking cannot hold a changed claim `verified`. A small in-callout bullet rewrite demotes for this reason and a second: it co-adds an unmarked `Prior view` bullet (Step 5) that moves the hash again; preserving the prior view to a `2-outputs/supersede/preserve/` file instead of an in-callout bullet removes that second trigger, but the changed claim itself still demotes the page (note it in the log). A change that rewrites essentially the whole verified body — a whole-page replacement, or a split that restructures the donor — cannot mark claim-by-claim anyway (marking every claim would empty the hashed body), so it demotes (see the whole-page Worked Example). A claim the supersede does re-fact-check against the raw this pass needs no marker. On any demotion, reset to `draft`, strip the stale `verified_hash:`, and note it in the log, per the shared `verified_hash` mechanics in `.claude/skills/multi-skill/references/dependent-cascade.md`. A page already at `draft`/`needs-update` carries no marker (its status already means unverified) and no hash; leave its status as is. (The cascade reference's `verified → draft` strip covers every change the supersede does not mark; a genuine addition rides in `*[unverified]*` claims.)
   - On every page that cited the superseded source, apply the shared source-support bookkeeping and under-supported-page rules in `.claude/skills/multi-skill/references/dependent-cascade.md` — `sources:` / `source_count` / `Sources` sync, the zero-source decision (a page left citing no source — quarantine, re-source, or needs-update; including an author entity left with no surviving source), and the single-source-synthesis decision (a synthesis dropping below two sources — stub, re-source, or forget); when re-sourcing, add the replacement only if the page genuinely draws on it. A merge survivor that *gains* the weaker page's source(s) syncs its own `sources:` / `source_count` / `Sources` callout to match — the bookkeeping above covers pages that cited the *superseded* source, but a merge survivor is gaining one, not losing one. Adding a `Sources` callout bullet is an unmarked body change a claim marker cannot carry (`.claude/skills/multi-skill/references/dependent-cascade.md` → verified_hash / status reset), so a `verified` survivor that gains a source demotes to `draft` (strip `verified_hash:`, note it in the log), even though the moved-in content bullets stay marked `*[unverified]*`.
   - Add optional `superseded_claims:` or `supersedes:` metadata when useful.
   - Clear `needs-update` only when the reason is resolved; otherwise keep it with an explanation.

7. **Verify the supersession landed cleanly.** Before touching the log, run content verification over what this operation wrote, then confirm the structural landed-cleanly checks:
   - **Verify newly-authored content against the raw** (`.claude/skills/multi-skill/references/verification.md`): run its two packets (Source-Faithfulness + Note-Quality and Coverage) over the claims this supersession newly authored or changed — a replacement bullet, a merged-in claim, a re-extracted figure's caption — re-deriving each load-bearing claim from the raw source (not the drafted replacement), with one late-section detail as proof of re-read and a `#page=N` spot-check per distinct raw. Both packets clean in the same round; a fix re-runs both. This runs over what this operation wrote, not content moved intact from an already-verified page (unchanged claims keep their prior verification). A claim this pass could not re-fact-check against the raw is marked `*[unverified]*` per the Step-6 status rule, not shipped unchecked; the page then stays `draft` (or `verified` with the marked delta) for a later `audit` to re-check independently. Record both packet results in the Step 8 log entry.
   - The active page reads as intended; the prior-view artifact is in the place you said it would be (`Prior view` bullet, or `2-outputs/supersede/preserve/...` file).
   - Inbound wikilinks that pointed at the old page or claim now land on the active surviving page, not the `2-outputs/supersede/preserve/` copy. Where a rename, split, or merge changed a filename, confirm each inbound link was rewritten to the surviving target — any link still pointing at the removed/renamed name is a failure to fix here, not to defer.
   - The cascade landed cleanly (`.claude/skills/multi-skill/references/dependent-cascade.md` → Verifying the cascade landed): `sources:`/`source_count:`/`Sources` agree on every touched page and no inbound body-prose wikilink is left dangling.
   - `attachments:` frontmatter and embed paths still resolve, and no `sources:` link is left dangling — run `python3 .claude/skills/multi-skill/scripts/check_wiki.py "1-wiki"` whenever attachments were involved OR a page was deleted or renamed (a merge or source rename can strand a `sources:` frontmatter link that the by-eye body-prose check misses; the sibling `forget` runs it on every removal).
   - Preserved copies verify (`.claude/skills/multi-skill/references/quarantine-path-convention.md` → Verifying the preserved copy): each quarantined or superseded file is byte-identical to the original it preserves (`cmp -s` for a file, `diff -rq` for a folder — existence alone passes on a truncated binary) at the path recorded in the active page, and none was written to a git-ignored name.

   Fix anything that doesn't pass before continuing. If a check fails in a way you can't resolve inside the supersede scope, stop and surface it.

8. **Write the supersede report, then update index, hot, and log.** First save the operation report to `2-outputs/supersede/supersede-YYYY-MM-DD-HHMM-{target}.md` (create the folder if needed; reuse the single operation timestamp captured in Step 5 — the same value as the preserve filename, the log heading, and the `Preserved:` link — not a fresh `date`, so the report, the log, and the preserved-file link all agree). `{target}` is the superseded page's stem or slug — the raw stem for a source page, the kebab slug otherwise. The report carries the operation summary and the `## Self-report` section (per `.claude/skills/multi-skill/references/self-report.md`); the log entry then links it. Report shape:

```markdown
---
kind: supersede
date: YYYY-MM-DD
target: {target}
reason: {reason}
---
# Supersede: {target} - {reason}

- Superseded: [[1-wiki/concepts/old-page.md|old page]] or "{old idea}"
- Active: [[1-wiki/concepts/new-or-updated-page.md|new or updated page]]
- Preserved: [[2-outputs/supersede/preserve/preserve-YYYY-MM-DD-HHMM-{filename}.md|prior view]] (or "Prior view bullet, in-callout")
- Updated: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]]
- Marked needs-update: [[1-wiki/concepts/self-attention.md|self-attention]] (or "none — cosmetic")

## Self-report
- {a specific limitation that bit supersede this run — a mis-route, a cascade case it mishandled, a prior-view capture it had to stop at} → upgrade: {how the supersede skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
```

Then update `index.md` for any created, removed, or renamed page; rewrite or remove any `hot.md` Open-threads / Watchlist bullet (found in Step 2) that named the target, and add a Recent-activity line in the `- [YYYY-MM-DD HH:MM] supersede | {target}` form (24-hour UTC, the same timestamp as the log heading). Then prepend the log entry, which links the report:

```markdown
## [YYYY-MM-DD HH:MM] supersede | {target} - {reason}
- Report: [[2-outputs/supersede/supersede-YYYY-MM-DD-HHMM-{target}.md|supersede-YYYY-MM-DD-HHMM-{target}]]
- Superseded: [[1-wiki/concepts/old-page.md|old page]] or "{old idea}"
- Active: [[1-wiki/concepts/new-or-updated-page.md|new or updated page]]
- Preserved: [[2-outputs/supersede/preserve/preserve-YYYY-MM-DD-HHMM-{filename}.md|prior view]] (or "Prior view bullet, in-callout")
- Updated: [[1-wiki/concepts/self-attention.md|self-attention]], [[1-wiki/concepts/positional-encoding.md|positional encoding]]
- Marked needs-update: [[1-wiki/concepts/self-attention.md|self-attention]] (or "none — cosmetic")
```

## Worked Example: Small Replacement

User says: "On [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]], the bullet claiming the limit applies per step is wrong. Re-read [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] sec. 3.2; the limit is per message, not per step."

Plan surfaced for approval:

```text
Target: bullet inside [[1-wiki/concepts/multi-head-attention.md|Multi-Head Attention]] `Idea` callout
Old: "The mechanism applies the limit per step."
New: "The mechanism applies the limit per message."
Reason: misread of sec. 3.2.
Prior view: preserved as a `Prior view` bullet inside the same callout.
Cascade: none (single bullet, no dependents claim per-step bandwidth).
```

Then one `AskUserQuestion` call: "Apply this small replacement?" Options: apply / change-the-new-content / skip / other.

Apply: edit the `Idea` callout, append the prior-view note, touch `updated:`. Status: this example targets a draft page, so it stays draft (no `*[unverified]*` marker — `draft` already means unverified); had the page been `verified`, this small in-callout rewrite would demote it to `draft` (log the demotion): the corrected claim's text changed, which moves `verified_hash` whether or not the bullet is marked, and the appended `Prior view` bullet is a second unmarked body change — preserving the prior view to a `2-outputs/supersede/preserve/` file rather than in-callout removes only that second trigger, not the changed-claim demotion (Step 6, claim-level model). Log entry: `supersede | multi-head-attention - corrected per-step → per-message claim`.

## Worked Example: Whole-Page Replacement

User says: "[[1-wiki/concepts/positional-encoding.md|positional encoding]] is built on a single 2017 source ([[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]). A newer review covers the same ground better; supersede with the new source page [[1-wiki/sources/{bibkey}.md|{bibkey}]]."

Plan:

```text
Target: [[1-wiki/concepts/positional-encoding.md|positional encoding]] (whole page)
Reason: 2017 source superseded by a newer review with broader coverage.
Prior view: copy current page to 2-outputs/supersede/preserve/preserve-{YYYY-MM-DD-HHMM}-positional-encoding.md
Cascade:
  - [[1-wiki/concepts/self-attention.md|Self-attention]] (cites positional-encoding in `Connections`): material? Yes; the newer review reframes the relationship. Set needs-update with reason "supersession of positional-encoding ({YYYY-MM-DD})".
  - [[1-wiki/concepts/residual-connection.md|Residual connection]] (Connections-only): cosmetic; no cascade.
sources:/source_count: rewrite to point at [[1-wiki/sources/{bibkey}.md|{bibkey}]].
```

The plan-build is one context post. Then per-decision `AskUserQuestion` calls follow: one for the whole-page replacement, one for the `self-attention` cascade decision. Status is mechanical (Step 6), not a separate question: a whole-page replacement rewrites essentially all of a `verified` page's claims at once, so marking each `*[unverified]*` would empty the hashed body — demote the page to `draft` instead and note it in the log (claim-level marking is for incremental edits that leave most of the verified body intact). Apply only what the user approves: copy old page to `2-outputs/supersede/preserve/`, replace active page, cascade `needs-update` to `self-attention` only, touch `updated:`, log the supersession with the cascade decision.

## Edge Cases

- A contradiction remains live: do not clear `needs-update`.
- Replacement is really a deletion: switch to `forget`.
- New version has weaker support: mark it `*\[tentative\]*` or keep status `draft`.
- Botched or vetoed supersession: the prior view captured in Step 5 is the rollback source. If the user vetoes a remaining cascade decision after the active content was already overwritten, or the new content proves wrong, restore the active page from its `2-outputs/supersede/preserve/` copy (or re-apply the verbatim `Prior view` bullet text for a small replacement) following the reference's Restore Active Page sequence (`cp` back, then `cmp -s` to confirm the restore), reverse any cascade edits already made, and abort — never silently re-supersede.
- Target is itself a preserved prior view: a file under `2-outputs/supersede/preserve/` is frozen audit trail (same guarantee as historical log entries) — never supersede or overwrite it. To revise content that now lives only there, target the active page instead, or re-ingest the raw.
- High-fan-out cascade (a source page cited by many pages): list the full dependent set in the Step 3 plan with each one's material/cosmetic call. Material cascades still get individual `AskUserQuestion` calls, but when many dependents share one identical material reason, ask once whether to apply that `needs_update_reason:` to the named set as a group rather than one call per page.
- Trust the user's replacement decision; don't re-derive it from the raw: supersede takes the user-supplied replacement on trust and does not re-derive it from the raw the way `ingest` existing-source mode does — route to `ingest` when the fix should be re-derived from the raw rather than supplied. This does not exempt Step 7, which still verifies that the claims supersede newly authored faithfully represent the raw (a `#page=N` spot-check per raw): supersede verifies its own authored text, it just does not re-adjudicate the user's replacement choice.
- Historical and output content references the superseded page: Step 2 greps `1-wiki/` only by design, so wikilinks from `2-outputs/` (including a synthesis `origin:` pointing at a now-superseded prior view) into the live wiki are frozen danglers — not repaired in this skill and not Step 7 failures.

## Limits

- Preserve the prior view on every substantive replacement, including when the user does not explicitly ask for it.
- Never modify `0-raw/`.
- Never rewrite historical log entries — the log is the audit trail, and rewriting it defeats the prior-view guarantee this skill exists to provide.

## Supersession Path Convention

Pages: prior copy goes to `2-outputs/supersede/preserve/preserve-YYYY-MM-DD-HHMM-{filename}.md` (date-prefixed filename). Whole-page attachment snapshots: `2-outputs/supersede/preserve/attachments/{stem}/preserve-YYYY-MM-DD-HHMM/` (date as subfolder of {stem}, holding the full attachment set at that date). Single-file attachment replacements: `2-outputs/supersede/preserve/attachments/{stem}/preserve-YYYY-MM-DD-HHMM-{name}.{ext}` (date prefix on filename). Both attachment shapes group by {stem} so all prior versions of one source's attachments live together.

On a name clash in `2-outputs/supersede/preserve/` — a same-minute page supersession (a `preserve-...-{filename}.md` already present, e.g. a re-run after a partial failure) **or** two attachment replacements of the same `{name}` in one minute — apply the shared name-clash suffix rule in `.claude/skills/multi-skill/references/quarantine-path-convention.md` (so the second copy never overwrites the first prior view — the safety net itself), and point the replacement note at the suffixed name. The page path carries only a minute-resolution timestamp, so this clash guard is what protects it.
