# cleanup — preservation sub-mode (Step 4, opt-in)

The opt-in path for pruning `2-outputs/forget/quarantine/` and `2-outputs/supersede/preserve/`. SKILL.md Step 4 holds the trigger and the standing rule that these two folders are never swept; this file holds the scope test, the subject-resolution rules, the two folders' differing stakes, and how the sub-mode's gates and report slot differ from the ordinary sweep. Load it only when the user has named one of the two folders exactly — no plain invocation and no age threshold, including "everything not protected", reaches this.

## Contents

- Trigger and scope
- Resolve the subject by path shape
- The two folders' stakes
- Gating, threshold, and report slot

## Trigger and scope

Run this only when the user names `forget/quarantine/` or `supersede/preserve/` exactly, and cover only the folder they named.

Naming a parent is not naming the preservation folder: "prune `2-outputs/forget/`" scopes the ordinary sweep to that kind's operation reports and leaves `quarantine/` alone, because the parent is a legitimate prune target in its own right and the nested folder is not what the user asked about. When the phrasing is ambiguous, confirm before listing anything — the sub-mode's downside is irreversible and the ordinary sweep's is not.

Every other protection still applies inside the named folder: the sub-mode lifts the path protection alone, so a `.gitkeep` there stays protected (it is what keeps the emptied folder in git).

For each preserved file report the wiki page it preserves, whether a page currently exists at that path, and its committed state.

## Resolve the subject by path shape

Resolve the subject by path shape, not by filename alone — the preserved-attachment layouts differ between the two folders and within `supersede/preserve/`:

- A page copy sits directly in the preservation folder as `quarantine-YYYY-MM-DD-HHMM-{filename}.md` or `preserve-YYYY-MM-DD-HHMM-{filename}.md`. The subject is the `{filename}` suffix.
- Anything under an `attachments/` segment is an attachment, whatever its own name: the subject is the `{stem}` directly after `attachments/`. That one rule covers all three layouts — a quarantined attachment keeping its original name, a `preserve-`-prefixed single-file replacement, and a whole-page snapshot nested inside a `preserve-YYYY-MM-DD-HHMM/` date subfolder. Never read the immediate parent folder or the filename prefix as the subject; for two of those three shapes it is a date, not a stem.

## The two folders' stakes

The two folders carry different stakes:

- `supersede/preserve/` — the live page still exists and holds the current view, so the preserved file is a superseded prior version. Propose it per file with **no recommendation** (a genuine no-lean call — cleanup cannot know whether the user will want the prior view again).
- `forget/quarantine/` — the wiki page is gone, so this is the only findable copy of that content anywhere. Say that in the gate, name the page it holds, and propose it per file with **no recommendation**.

For a preserved attachment in either folder (`attachments/{stem}/…`), add the binary caveat per CLAUDE.md → Safety rules: there is no diff to eyeball, so the file's identity rests on its name and folder alone.

## Gating, threshold, and report slot

The sub-mode ignores the age threshold entirely — preserved content is listed by page existence and committed state, never by date — so when the user scoped the run to a preservation folder alone, skip the threshold question and the ordinary `2-outputs/` walk; neither applies.

Every preservation file is gated one item per `AskUserQuestion` call, never batched, whatever its git state: each is the only findable copy of a page's content or prior view, so the git-recoverable batching carve-out does not reach it.

Everything else follows the ordinary path: the Step 7 gate, the Step 8 pointer resolution and removal line (`references/removal-safety.md`), and its own `### preservation (opt-in sub-mode)` section in the report and slot in the log (`references/report-and-log.md`).
