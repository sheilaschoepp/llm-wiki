# ingest — Existing-Source (Reingest) Checks (Step 1)

The always-on checks a reingest runs once Step 1 has detected existing-source mode (`1-wiki/sources/{stem}.md` already exists). SKILL.md Step 1 does the new/existing detection and the depth ask; this file is the existing-mode-only detail it points to. A new-source ingest never loads this.

**Dependents.** Throughout, "dependents" means every page that lists this source in its `sources:` frontmatter — the concept/entity and synthesis pages that lean on it. Locate every dependent here so Step 7's cascade can reach it.

## Contents

- Confirm The Reason
- `needs-update` Check
- `*[tentative]*` Resolution Check
- Schema-Migration Check
- Frames Check
- Depth-Purpose Check
- Depth Is Never Auto-Instigated

## Confirm The Reason

Confirm one of: `schema refresh` (to the current source-page template), `missed evidence`, `fuller write-up` (more thorough writing within the existing scope), `contradiction` surfaced by a newer source, `corrected interpretation`, or a concept/entity page that got too source-shaped and needs cleanup. The reason sets what changes on the page — schema-refresh and missed-evidence are high-level; fuller-write-up writes more; contradiction and corrected-interpretation are targeted and scope-limited. It does not change how much is read: every reingest fully re-reads the raw (Step 2) — for a book, its recorded chapter or page range (named in `title:`), re-asked only to change it, per the Step 1 read-range rule. Nor does it by itself turn on the reference-grade deep mode (a separate explicit opt-in; see SKILL.md → Depth). **No reason given → ask; reingest without a reason creates drift.**

## `needs-update` Check

If the source page is `status: needs-update`, read its `needs_update_reason:` and any `Contradictions`/`Tensions` entries — that is the precise statement of what an earlier `audit` flagged. Fold resolving it into scope; clear the status back to `draft` once addressed (a later `audit` re-verifies). Same for any `needs-update` dependent the reingest repairs.

## `*[tentative]*` Resolution Check

A reingest that attaches a genuinely-supporting source walks each `*[tentative]*` claim on the touched pages — the source page and every dependent concept/entity/synthesis page the attached source now supports. Where the attached source covers the *marked claim* (confirmed against the raw this pass — Step 2 re-read plus the Step 8 packets), drop the `*[tentative]*` marker and cite the claim to it: the marker flags thin support or a needs-a-second-source gap, and resolving that gap is exactly what the attach does, so ingest — the operation adding the support — owns the update. Where the source supports only an adjacent fact and not the marked claim, leave the marker (judge that honestly; do not stretch "supports an adjacent fact" into "supports the claim"). `*[tentative]*` marks epistemic uncertainty, distinct from `*[unverified]*`: its "persists even after verification" property means `audit`'s *checking* a claim does not auto-clear it, not that only `audit` may touch it — adding the resolving evidence is a distinct event that retires it (`CLAUDE.md` → Bullet Markers).

## Schema-Migration Check

Compare the existing source page's section list against the current required callouts in `CLAUDE.md`; record any missing ones (Step 5 adds them). Run the same check against the concept/entity and synthesis pages this source supports.

## Frames Check

Read the existing page's `frames:` frontmatter. State the chosen outcome and its consequence back to the user:

- **reuse the saved frames** (default): scope unchanged — existing bullets stay, evidence is refreshed, breadth does not move.
- **append a new lens**: existing bullets stay and the new lens's content is written this pass (the full re-read makes it available).
- **clear to unscoped** (`frames: []`): existing bullets stay and the page is rewritten to whole-source breadth.

**Scope-widening test:** a change widens scope only when the new `frames:` union admits source material the old union did not (a strict superset). A reword that admits the same material, or appending a lens the body already covers, is not widening — treat it as reuse (no forced body growth, no status change). A genuine widening (an append or clear that admits new material) is substantive. It grows the body to match this pass and resets the page to `status: draft`; a `verified` page resets too, and a later `audit` re-verifies it. A genuine widening also overrides a purely targeted reason: you cannot widen `frames:` while writing only a few bullets. A `frames:` value (including `frames: []`) that claims more scope than the body covers fails the Step 8 faithfulness packet. Reframing only ever adds, then widens the body to match; narrowing (dropping a lens while keeping its content) is not a reingest operation — use `forget` or `supersede`.

## Depth-Purpose Check

A frame is recovered from frontmatter above; a non-frame depth purpose from a prior deep ingest is not on the page — it is in the `purpose:` field of the latest `2-outputs/ingest/ingest-*-{stem}.md` report. Only when the Depth ask (SKILL.md Step 1) returned Deep, recover the prior purpose from there and offer to keep, replace, or drop it for this reingest. If no report is found or its `purpose:` is empty — the record was pruned, or a later normal reingest overwrote the latest report with an empty purpose — do not proceed on an unknown purpose: ask for a fresh deep purpose per the Depth rule.

## Depth Is Never Auto-Instigated

Existing-source mode never auto-instigates deep. A reingest is often a re-framing, not a depth change — settle the reason and frame first, and switch to deep only if the user explicitly opts in via the same ask. The `fuller write-up` reason means more thorough writing within the existing scope, not the reference-grade `ingest-deep` treatment.
