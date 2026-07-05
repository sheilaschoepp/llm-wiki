# Removal Mechanics

The exact disk operations behind `forget` Step 5, plus the restore path. Run these only after the cascade plan is approved (Step 4). SKILL.md Step 5 owns the per-scope *decisions* and the three ordering invariants; this file owns the *commands*.

Substitute every `{...}` literal before running. Obtain the timestamp with `TZ='UTC' date '+%Y-%m-%d-%H%M'`.

## Two Rules That Override Convenience

- Copy, then verify, then unlink. Use `cp` for the copy so the original survives until the quarantine copy is confirmed. Reach for `mv` only on the source-page folder case, and even there per-file, never as one atomic move whose half-failure leaves no original.
- Never round-trip a binary attachment through Read/Write — a PNG read as text and rewritten is corrupted. Move attachments with shell `cp`/`rm` only. Pages are text and may use Read/Write, but the `cp` sequences below are simpler and safer.

## Git-State Precheck

Quarantine covers whole pages and attachments. In-place edits (bullet, section, support link, embed) are not quarantined, so git history is their only fallback — and it holds nothing if the change was never committed.

```bash
git status --short -- "{target-path}"
```

If the target is modified or untracked and the scope is an in-place edit, the cascade plan already flags it `note: uncommitted — no git fallback`. Recommend the user commit first; do not block the forget.

## Safe Copy-to-Quarantine: Whole Page

```bash
mkdir -p 2-outputs/quarantined
dest="2-outputs/quarantined/quarantined-{YYYY-MM-DD-HHMM}-{name}.md"
n=2; while [ -e "$dest" ]; do dest="2-outputs/quarantined/quarantined-{YYYY-MM-DD-HHMM}-{name}-$n.md"; n=$((n+1)); done
cp "1-wiki/{folder}/{name}.md" "$dest"
cmp -s "1-wiki/{folder}/{name}.md" "$dest" \
  && ! git check-ignore -q "$dest" \
  && rm "1-wiki/{folder}/{name}.md" \
  || { echo "ABORT: quarantine copy missing/truncated OR on a git-ignored name; original kept"; exit 1; }
```

The `while [ -e "$dest" ]` loop retargets a same-minute name clash to `-2` (suffix before `.md`, never `.md.1`) so a re-run cannot silently overwrite a prior quarantine copy, and `! git check-ignore -q "$dest"` refuses to unlink the original when the copy landed on a git-ignored name. The not-git-ignored check runs here, before the `rm`, exactly as `supersede` Step 5 mandates — a Step-7 check can only report a lost copy, not prevent it.

## Safe Move: Single Binary Attachment

```bash
mkdir -p "2-outputs/quarantined/attachments/{stem}"
dest="2-outputs/quarantined/attachments/{stem}/{name}.png"
n=2; while [ -e "$dest" ]; do dest="2-outputs/quarantined/attachments/{stem}/{name}-$n.png"; n=$((n+1)); done
cp "1-wiki/attachments/{stem}/{name}.png" "$dest"
cmp -s "1-wiki/attachments/{stem}/{name}.png" "$dest" \
  && ! git check-ignore -q "$dest" \
  && rm "1-wiki/attachments/{stem}/{name}.png" \
  || { echo "ABORT: attachment quarantine copy missing/truncated OR on a git-ignored name; original kept"; exit 1; }
```

## Safe Move: Whole `{stem}/` Folder (Source-Page Removal)

Embeds in supported pages are removed first (SKILL.md Step 5 ordering). Then guard against orphaning a file a surviving page still embeds:

```bash
grep -rn "attachments/{stem}/" 1-wiki/ | grep -v "^1-wiki/sources/{stem}.md"
```

The `grep -v` excludes the source page being removed, so its own embeds and `attachments:` frontmatter do not register as "shared". Any remaining hit from a page outside the removal scope names a file to keep live — move only the unshared files, leaving the shared ones in `1-wiki/attachments/{stem}/`. If no file is shared, move the whole folder with per-file verification:

```bash
mkdir -p 2-outputs/quarantined/attachments
cp -R "1-wiki/attachments/{stem}" "2-outputs/quarantined/attachments/{stem}"
if grep -rl "attachments/{stem}/" 1-wiki/ | grep -qv "^1-wiki/sources/{stem}.md$"; then
  echo "ABORT: a surviving page still embeds attachments/{stem}/; remove those embeds first"; exit 1
fi
diff -rq "1-wiki/attachments/{stem}" "2-outputs/quarantined/attachments/{stem}" \
  && rm -rf "1-wiki/attachments/{stem}" \
  || { echo "ABORT: folder quarantine incomplete, original kept"; exit 1; }
```

`diff -rq` is the folder-level analogue of `test -f` — it catches a partial copy that a directory-exists check would pass. If the destination `{stem}/` folder already exists from a prior forget or a supersede, merge per file with the `-2` suffix-before-extension rule on each name clash, rather than copying the whole folder into a nested `{stem}/{stem}/`.

## Name-Clash Suffix Rule

Insert `-N` immediately before the final extension, starting at `-2` and incrementing: `fig-1.png` → `fig-1-2.png`; `quarantined-…-foo.md` → `quarantined-…-foo-2.md`. Never append after the extension — `.1` / `.2` match the repo `.gitignore` (`*.[1-9]`) and silently drop the copy out of version control. Confirm with `git check-ignore -q "$dest"` (a non-zero exit means tracked, which is what you want).

## Inbound-Link Repair

Step 2 already located inbound links with the path-stem grep. For each hit, decide in Step 6 whether to rewrite the link (the reference still makes sense pointing elsewhere) or remove the bullet (the reference only made sense via the removed page). This file just supplies the search; the rewrite-vs-remove judgement is Step 6's.

## Restore From Quarantine

Recovery is not improvised — reverse the move:

```bash
cp "2-outputs/quarantined/quarantined-{YYYY-MM-DD-HHMM}-{name}.md" "1-wiki/{folder}/{name}.md"
test -f "1-wiki/{folder}/{name}.md" && echo "restored"
```

Then reverse the cascade, in order: (1) re-add the page's `index.md` entry; (2) restore each dependent's `sources:` / `Sources` / `source_count`; (3) revert each `needs-update` flip and its `needs_update_reason:`, and any `verified → draft` reset where the prior `verified_hash:` is recoverable from git; (4) restore each rewritten or removed inbound link; (5) touch `updated:` on every page changed. In-place edits (bullets, links, embeds) were never quarantined — recover them with `git show` / `git checkout` only if the change was committed. Use this path on a mid-cascade veto that would otherwise leave inbound danglers.
