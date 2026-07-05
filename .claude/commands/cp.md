---
description: Commit pending changes in logical chunks and push (this session's changes, or everything)
---

Commit pending changes in logical chunks and push to the current branch's upstream.

Scope — from the command argument (`$ARGUMENTS`) if given, otherwise ask once with AskUserQuestion:
- `session` — commit only what **this session** changed, at the hunk level. Concurrent sessions may have their own uncommitted changes in the same files; leave those alone.
- `all` — commit every change in the working tree, regardless of which session made it.

If `$ARGUMENTS` clearly names a scope, use it. Otherwise default to `session` and do **not** ask — `session` is the safe default and never commits work you can't account for. Ask with AskUserQuestion **only** when out-of-session changes look like they might belong with this commit and you can't tell from context (e.g. another session edited a tracked file you also touched, or there's an unexplained modification adjacent to your work) — first option "This session's changes only (Recommended)", second "Everything in the working tree". Untracked output artifacts and other sessions' unrelated changes don't trigger the question; `session` scope leaves them untouched.

Steps:
1. Review what's pending: `git status` and `git diff` (plus `git diff --staged` if anything is already staged).
2. If there's nothing to commit for the chosen scope, say so and stop.
3. Group the work into logical chunks — one commit per coherent change, not one catch-all commit. For each chunk, stage just its content, then commit it before moving to the next:
   - `all` scope: stage with `git add -p` / `git add <path>` so each commit holds one logical change.
   - `session` scope: stage only the hunks you wrote this session. You know the exact before/after of your own Edit/Write edits, so write those hunks — including the `diff --git` / `---` / `+++` headers — to a patch file and stage with `git apply --cached --recount /tmp/cp.patch`. Do **not** use `git add -A`, `git add .`, `git add <file>`, or `git commit -a` in this scope — they sweep in other sessions' hunks.
4. Before each commit, run `git diff --staged` to confirm only that chunk is staged. Write a concise imperative one-line message (short body only if it needs explaining), ending with the `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` trailer. Commit with `git commit` (no `-a`).
5. Push with `git push` (or `git push -u origin HEAD` if there's no upstream).
6. Report each commit hash with the files it covered, and confirm the push succeeded.

Caveats:
- Do not create a new branch — commit and push on whatever branch is checked out, even the default branch (you're explicitly being asked to push it).
- `session` scope: if a hunk overlaps another session's edit on the same lines, it can't be split cleanly — flag it and ask rather than committing their work.
- `all` scope: if you see changes you can't explain or that look unintended (a stray large file, a secret, unrelated work-in-progress), flag them and ask before sweeping them in.
