# Quarantine and preserved-file path convention

Shared reference for naming and verifying files moved out of `1-wiki/` for preservation: `forget` (quarantine to `2-outputs/quarantined/`), `ingest` existing-mode (attachment quarantine to `2-outputs/quarantined/attachments/{stem}/`), and `supersede` (preservation to `2-outputs/superseded/`). Read it from the calling skill's move/verify step. It is a shared skill-family reference, like `.claude/skills/multi-skill/multi-skill-memory.md`; edit it only on explicit instruction.

## Name-clash suffix

On a name clash with an already-preserved file in the target folder (a prior `forget`/`supersede` of the same name, or two operations in the same minute), insert a `-N` suffix immediately before the final extension, starting at `-2` and incrementing (`-2`, `-3`, …) until the name is free: `fig-1.png` → `fig-1-2.png` → `fig-1-3.png`; `quarantined-…-foo.md` → `quarantined-…-foo-2.md`. Never append the suffix after the extension — a trailing `.1` / `.2` matches the repo's `.gitignore` and would silently drop the preserved copy out of version control. Point the log link (or the source-page replacement note) at the suffixed name. (`supersede` additionally date-stamps its `2-outputs/superseded/` attachment paths, because the same source can be superseded repeatedly.)

## Verifying the preserved copy

After the move, verify each preserved copy against two conditions before unlinking the original, and re-check them after:

- **Byte-identity**: the preserved copy is byte-identical to its original — `cmp -s <original> <preserved>` for a single file, `diff -rq <original-dir> <preserved-dir>` for a folder — reporting identical. A truncated or interrupted `cp` / `cp -R` passes a bare existence check but fails this, and the preserved copy is the operation's only fallback, so a silent truncation (worst for an attachment binary that cannot be eyeballed) would be unrecoverable. Confirm identity, not mere existence — a `test -f` / "confirm it exists" check is not sufficient.
- **Not git-ignored**: `git check-ignore -q <path>` returns non-zero (not ignored) for every preserved copy. A file written to an ignored name is effectively lost — re-name it per the suffix rule above and re-point the recorded link.

Run both checks *before* unlinking or overwriting the original; a post-hoc (Step-7-style) check can only report a lost copy, not prevent it. `forget`'s `removal-mechanics.md` wires these into its `cp → cmp -s`/`diff -rq` → `git check-ignore` → `rm` sequences; `supersede` (preservation to `2-outputs/superseded/`) and `ingest` existing-mode (attachment quarantine) apply the same byte-identity-then-not-ignored rule at their capture and verify points rather than restating it.
