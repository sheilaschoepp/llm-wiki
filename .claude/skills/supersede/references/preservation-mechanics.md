# Preservation Mechanics

The exact disk operations behind `supersede` Step 5, plus the restore path. Run these only after the plan is approved (Step 4). SKILL.md Step 5 owns the per-scope *decisions* (which scope applies, the rename re-point logic, split-off schema-completeness, the merge survivor choice) and the ordering invariants; this file owns the *commands*. The shared byte-identity-then-not-git-ignored rule and the name-clash suffix live in `.claude/skills/multi-skill/references/quarantine-path-convention.md`; this file wires them into supersede's per-scope sequences rather than restating them.

Substitute every `{...}` literal before running. Capture the operation timestamp **once** with `TZ='UTC' date '+%Y-%m-%d-%H%M'` and reuse that single value for every `YYYY-MM-DD-HHMM` in this operation — the preserve filename(s), and the Step-8 report filename, log heading, Recent-activity line, and the `Preserved:` link that points back at the preserve file — never re-running `date`, or the preserve filename and its Step-8 link could straddle a minute boundary and disagree (a dangling link). For a small in-callout replacement that writes no preserve file, capture the stamp at Step 8 instead.

## The Overwrite Is Two Tool Calls

Unlike `forget` (which chains `rm` behind a Bash guard with `&&`), supersede's active-content overwrite is a **Write tool call** for a page — or a `cp` for a binary — which cannot chain after the Bash guard. So every scope is two steps: (1) a Bash preserve-and-verify guard that must exit 0, then (2) the overwrite, issued **only if** the guard exited 0. Never issue the overwrite when the guard failed — a post-overwrite check can only report a lost prior view, not prevent it.

## Two Rules That Override Convenience

- Capture the prior view, verify it, then overwrite. Copy with `cp` / `cp -R` so the original survives until the preserve copy is confirmed.
- Never round-trip a binary attachment (`.png` / `.jpg` / `.svg`) through Read/Write — a binary read as text and rewritten is corrupted. Move it with `cp` only. Pages are text and may use the Write tool for the overwrite.

## Git-State Precheck

The Step 3 plan already surfaced `git status --short -- <target>`. Do not overwrite a dirty target the user has not committed or knowingly cleared — git then holds no recoverable pre-edit baseline (CLAUDE.md Safety rules), and a small in-callout or merge overwrite has no separate preserve file to fall back on.

## Preserve-And-Verify Guard: Single File

```bash
mkdir -p 2-outputs/supersede/preserve
# {filename} is the target's stem, {ext} its extension: md for a page; png/jpg/svg for an attachment.
# For a single attachment the base path is 2-outputs/supersede/preserve/attachments/{stem}/ instead.
dest="2-outputs/supersede/preserve/preserve-{YYYY-MM-DD-HHMM}-{filename}.{ext}"
n=2; while [ -e "$dest" ]; do dest="2-outputs/supersede/preserve/preserve-{YYYY-MM-DD-HHMM}-{filename}-$n.{ext}"; n=$((n+1)); done
cp "{active-path}" "$dest"
git check-ignore -q "$dest"; ignored=$?   # 0=ignored, 1=not ignored, 128+=git error
cmp -s "{active-path}" "$dest" \
  && [ "$ignored" -eq 1 ] \
  || { echo "ABORT: preserve copy missing/truncated, on a git-ignored name, or git check-ignore errored (exit $ignored); active kept"; exit 1; }
```

The `while [ -e "$dest" ]` loop retargets a same-minute name clash to `-2` inserted **before** the `.{ext}` extension (`…-{filename}-2.md`, never a trailing `…{filename}.md-2` — a `.N` after the extension matches `.gitignore`'s `*.[1-9]` and silently drops the copy; this matches the canonical rule in `quarantine-path-convention.md` and the correct sibling loop in `forget/references/removal-mechanics.md`). Keeping `.{ext}` on the base name also makes the preserve filename match the Step-8 `Preserved:` link template (`preserve-{YYYY-MM-DD-HHMM}-{filename}.md`), so the link never dangles. `cmp -s` (not a bare `test -f`, which passes on a truncated copy) confirms byte-identity, and the `[ "$ignored" -eq 1 ]` gate confirms the copy is not git-ignored (exit 1) — an ignored copy (0) or a git error (128) both abort. Only if this block exits 0, overwrite the active page with the Write tool.

## Preserve-And-Verify Guard: Folder (Attachments)

For a whole-page replacement whose page owns an attachments folder, also preserve the folder:

```bash
dest="2-outputs/supersede/preserve/attachments/{stem}/preserve-{YYYY-MM-DD-HHMM}"
mkdir -p "2-outputs/supersede/preserve/attachments/{stem}"
cp -R "1-wiki/attachments/{stem}" "$dest"
git check-ignore -q "$dest"; ignored=$?
diff -rq "1-wiki/attachments/{stem}" "$dest" \
  && [ "$ignored" -eq 1 ] \
  || { echo "ABORT: attachments preserve copy missing/differs, git-ignored, or git errored (exit $ignored); active kept"; exit 1; }
```

`diff -rq` is the folder analogue of `cmp -s` — it catches a partial `cp -R` that a directory-exists check would pass.

## Per-Scope Command Notes

Each scope runs the single-file guard above on the named target(s) before its overwrite. The *decisions* (re-point logic, schema-completeness, survivor choice) stay in SKILL.md Step 5.

- **Small replacement** — no preserve file. The prior view is the in-callout `Prior view` bullet (SKILL.md Step 5 owns its format and placement). Nothing to copy; capture the timestamp at Step 8.
- **Whole-page replacement** — run the single-file guard on the page; if the page owns an attachments folder, also run the folder guard. Then overwrite the page with the Write tool.
- **Source-page rename** — run the single-file guard on the old page. Create the new page, re-point every inbound reference (a Step 5 decision), and delete the old page only after a re-grep confirms no old-stem link remains in either citation half.
- **Split** — run the single-file guard on the donor page before mutating it (a split rewrites the donor's body). Then create the approved split-off page(s) (schema-complete — a Step 5 decision).
- **Merge** — run the single-file guard on **both** the weaker page and the surviving page before moving content in (the survivor is overwritten by the moved-in content, so it needs its own preserved snapshot). Then move content and delete the weaker page from `1-wiki/`.
- **Attachment replacement** — run the single-file guard (`cmp -s`) on the existing binary. Confirm the new binary already exists on disk at `1-wiki/attachments/{stem}/{name}.png` (supplied by the user or re-extracted by `ingest` out of band — supersede does not render it). Then `cp` the new binary into place at the same path (existing embeds keep resolving).

## Restore Active Page (Rollback)

If an apply step fails after the prior view is on disk but before the active content is consistent, or the user vetoes a later cascade decision after the overwrite already happened, reverse the move — do not improvise:

```bash
cp "$dest" "{active-path}"
cmp -s "$dest" "{active-path}" && echo "restored" || echo "RESTORE FAILED: restored content differs from the preserve copy — do not trust it; investigate"
```

`cmp -s` confirms the restore is byte-identical to the preserve copy it came from (a truncated restore passes a bare existence check but leaves a damaged page). For a small in-callout replacement (no preserve file), re-apply the verbatim `Prior view` bullet text instead. Then reverse any cascade edits already made (revert each `needs-update` flip and its reason, restore each rewritten inbound link, re-add any `index.md` entry), and surface the failure — never leave a half-applied overwrite.
