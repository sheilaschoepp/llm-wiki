# Removal Mechanics

The exact disk operations behind `forget` Step 5, plus the restore path. Run these only after the cascade plan is approved (Step 4). SKILL.md Step 5 owns the per-scope *decisions* and the three ordering invariants; this file owns the *commands*.

Substitute every `{...}` literal before running. Reuse the single operation timestamp SKILL.md captured once (`TZ='UTC' date '+%Y-%m-%d-%H%M'`) for the `{YYYY-MM-DD-HHMM}` in the quarantine name — do not re-run `date` here, or the quarantine filename and the Step-8 report/log link that points at it could straddle a minute boundary and disagree (a dangling link).

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
mkdir -p 2-outputs/forget/quarantine
dest="2-outputs/forget/quarantine/quarantine-{YYYY-MM-DD-HHMM}-{name}.md"
n=2; while [ -e "$dest" ]; do dest="2-outputs/forget/quarantine/quarantine-{YYYY-MM-DD-HHMM}-{name}-$n.md"; n=$((n+1)); done
cp "1-wiki/{folder}/{name}.md" "$dest"
git check-ignore -q "$dest"; ignored=$?   # 0=ignored, 1=not ignored, 128+=git error
cmp -s "1-wiki/{folder}/{name}.md" "$dest" \
  && [ "$ignored" -eq 1 ] \
  && rm "1-wiki/{folder}/{name}.md" \
  || { echo "ABORT: quarantine copy missing/truncated, on a git-ignored name, or git check-ignore errored (exit $ignored); original kept"; exit 1; }
```

The `while [ -e "$dest" ]` loop retargets a same-minute name clash to `-2` (suffix before `.md`, never `.md.1`) so a re-run cannot silently overwrite a prior quarantine copy, and the `[ "$ignored" -eq 1 ]` guard — `ignored` captured from `git check-ignore -q "$dest"` — unlinks the original only when the copy is confirmed *not* git-ignored (exit 1). An ignored copy (exit 0) or a git error (exit 128) both abort: a git error is not a green light, so the exit-1-only test refuses to proceed on it (a bare `! git check-ignore -q` would, since 128 is also non-zero). The not-git-ignored check runs here, before the `rm`, exactly as `supersede` Step 5 mandates — a Step-7 check can only report a lost copy, not prevent it.

## Safe Move: Single Binary Attachment

```bash
mkdir -p "2-outputs/forget/quarantine/attachments/{stem}"
dest="2-outputs/forget/quarantine/attachments/{stem}/{name}.png"
n=2; while [ -e "$dest" ]; do dest="2-outputs/forget/quarantine/attachments/{stem}/{name}-$n.png"; n=$((n+1)); done
cp "1-wiki/attachments/{stem}/{name}.png" "$dest"
git check-ignore -q "$dest"; ignored=$?   # 0=ignored, 1=not ignored, 128+=git error
cmp -s "1-wiki/attachments/{stem}/{name}.png" "$dest" \
  && [ "$ignored" -eq 1 ] \
  && rm "1-wiki/attachments/{stem}/{name}.png" \
  || { echo "ABORT: attachment quarantine copy missing/truncated, on a git-ignored name, or git check-ignore errored (exit $ignored); original kept"; exit 1; }
```

## Safe Move: Whole `{stem}/` Folder (Source-Page Removal)

Embeds in supported pages are removed first (SKILL.md Step 5 ordering). Then guard against orphaning a file a surviving page still embeds:

```bash
grep -rn "attachments/{stem}/" 1-wiki/ | grep -v "^1-wiki/sources/{stem}.md"
```

The `grep -v` excludes the source page being removed, so its own embeds and `attachments:` frontmatter do not register as "shared". Any remaining hit from a page outside the removal scope names a file to keep live. For the mixed case — the grep returns one or more shared files — do not use the whole-folder block below: it aborts on any shared file by design, and its "remove those embeds first" message does not apply to a surviving page's legitimate embed. Move each unshared file individually with the single-attachment sequence above (`cp` → `cmp -s` → git-check-ignore exit-1 guard → `rm`), leaving every shared file in `1-wiki/attachments/{stem}/`. Use the whole-folder block only when the grep returns no shared files:

```bash
if grep -rl "attachments/{stem}/" 1-wiki/ | grep -qv "^1-wiki/sources/{stem}.md$"; then
  echo "ABORT: a surviving page still embeds attachments/{stem}/; remove those embeds first"; exit 1
fi
mkdir -p 2-outputs/forget/quarantine/attachments
if [ -e "2-outputs/forget/quarantine/attachments/{stem}" ]; then
  echo "ABORT: quarantine {stem}/ already exists — merge per file with the -N suffix rule, never cp -R into a nested {stem}/{stem}/"; exit 1
fi
cp -R "1-wiki/attachments/{stem}" "2-outputs/forget/quarantine/attachments/{stem}"
git check-ignore -q "2-outputs/forget/quarantine/attachments/{stem}"; ignored=$?   # 0=ignored, 1=not ignored, 128+=git error
diff -rq "1-wiki/attachments/{stem}" "2-outputs/forget/quarantine/attachments/{stem}" \
  && [ "$ignored" -eq 1 ] \
  && rm -rf "1-wiki/attachments/{stem}" \
  || { echo "ABORT: folder quarantine copy missing/differs, on a git-ignored name, or git check-ignore errored (exit $ignored); original kept"; exit 1; }
```

`diff -rq` is the folder-level analogue of `test -f` — it catches a partial copy that a directory-exists check would pass. The existence guard above refuses to `cp -R` into an already-populated `{stem}/` (which would nest `{stem}/{stem}/`); on that clash, merge per file with the `-2` suffix-before-extension rule instead, and confirm each moved file byte-identical and not git-ignored as in the single-attachment sequence.

## Name-Clash Suffix Rule

Insert `-N` immediately before the final extension, starting at `-2` and incrementing: `fig-1.png` → `fig-1-2.png`; `quarantine-…-foo.md` → `quarantine-…-foo-2.md`. Never append after the extension — `.1` / `.2` match the repo `.gitignore` (`*.[1-9]`) and silently drop the copy out of version control. Confirm with `git check-ignore -q "$dest"` (exit 1 means not ignored / tracked, which is what you want; exit 0 means ignored; exit 128 is a git error — neither 0 nor an error is safe to proceed on, so test for exit 1 specifically, not merely non-zero).

## Restore From Quarantine

Recovery is not improvised — reverse the move:

```bash
cp "2-outputs/forget/quarantine/quarantine-{YYYY-MM-DD-HHMM}-{name}.md" "1-wiki/{folder}/{name}.md"
cmp -s "2-outputs/forget/quarantine/quarantine-{YYYY-MM-DD-HHMM}-{name}.md" "1-wiki/{folder}/{name}.md" \
  && echo "restored" \
  || echo "RESTORE FAILED: restored page differs from the quarantine copy — do not trust it; investigate before proceeding"
```

`cmp -s` (not a bare `test -f`) confirms the restored page is byte-identical to the quarantine copy it came from — a truncated or interrupted restore passes an existence check but leaves a damaged page, and the quarantine copy is the only source to recover from.

Then reverse the cascade, in order: (1) re-add the page's `index.md` entry; (2) restore each dependent's `sources:` / `Sources` / `source_count`; (3) revert each `needs-update` flip and its `needs_update_reason:`, and any `verified → draft` reset where the prior `verified_hash:` is recoverable from git; (4) restore each rewritten or removed inbound link; (5) touch `updated:` on every page changed. In-place edits (bullets, links, embeds) were never quarantined — recover them with `git show` / `git checkout` only if the change was committed. Use this path on a mid-cascade veto that would otherwise leave inbound danglers.
