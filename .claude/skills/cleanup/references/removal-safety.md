# cleanup — removal safety: recoverability and the removal record (Steps 4, 7, 8)

How cleanup proves a removal is reversible and records it so git history stays a usable archive. Removing a memory entry or an output file has no quarantine fallback — git history is the only preservation — so a removal is safe only if the content was committed and a reader can later find it by path and commit.

SKILL.md keeps the rules this file serves: resolve every pointer before removing anything (Step 8.0), gate by what the pointer returned (Step 7), and record every removal in the run's log entry (Step 8.3). This file holds the mechanics — the script, the guards that make it correct, the memory-file variant, and the record format. Load it once a run has at least one removal candidate; a run that proposes nothing never needs it.

## Contents

- When to run the determination
- The ignored-path pre-check
- The pointer resolution script
- The four guards
- The memory-file variant
- One determination per run
- The removal record

## When to run the determination

Step 4 establishes recoverability for every candidate, and Step 8.0 re-uses the result. Run the procedure below per candidate at Step 4 and record what it returns: a verified commit SHA (git-recoverable) or `uncommitted — not recoverable`.

Do not improvise a shorter test, and do not run the bare `git show "$SHA:<path>"` construct without the guards below — an empty `SHA` silently resolves to the git index.

Step 8.0 runs before any removal in Step 8, because once a file is deleted or an entry excised there is nothing left to verify a pointer against and every removal line would degrade to `uncommitted — not recoverable`.

## The ignored-path pre-check

Run `git check-ignore -q "<path>"` first — **exit 0 means the path is ignored**, exit 1 means it is not.

An ignored file produces the same empty `git status` output as a clean committed one, so silence alone cannot distinguish "committed and recoverable" from "never tracked at all". This bites the junk category hardest, whose members (`.DS_Store`, `Thumbs.db`) are usually ignored. Treat an ignored path as not recoverable whatever the script returns.

Quote every path in every command; `2-outputs/` filenames inherit raw-source stems, which may contain spaces.

## The pointer resolution script

Run this from the repo root (`git show <rev>:<path>` resolves paths from the root, `git log` from the working directory), with `P` set to the repo-root-relative path:

```bash
P="<path>"
SHA=$(git --literal-pathspecs log -1 --format=%H -- "$P")     # --literal-pathspecs: a [ or ? in a stem is not a glob
if [ -z "$SHA" ]; then
  PTR="uncommitted — not recoverable"                          # never tracked; an empty SHA makes "$SHA:$P" the INDEX
else
  git show "$SHA:$P" >/dev/null 2>&1 || SHA=$(git rev-parse "$SHA^" 2>/dev/null)
  if [ -n "$SHA" ] && git show "$SHA:$P" >/dev/null 2>&1 && git show "$SHA:$P" | diff -q - "$P" >/dev/null 2>&1; then
    PTR="$SHA"                                                 # tree holds the path AND its bytes match what is being removed
  else
    PTR="uncommitted — not recoverable"
  fi
fi
echo "$PTR"
```

## The four guards

Four failures those guards catch, each verified against real git behaviour:

- `git log -1` names the commit that last *touched* the path, which is the commit that *removed* it if the file was once deleted and later restored. `git show` then fails and the parent holds it — hence the `^` fallback, resolved to a literal SHA so the log line records a commit id rather than a rev expression.
- An **empty** `SHA` is not an error to git: `git show ":$P"` is index-revision syntax and succeeds against staged content, so an untracked-but-staged file would otherwise verify and be recorded with a blank SHA. The `-z` branch stops that, which is why the emptiness test comes first.
- `git rev-parse` on a bad rev exits non-zero *and prints its argument to stdout*, so its output is re-tested rather than trusted. This is the root-commit case, where `^` has no parent.
- `git log`'s pathspec honours fnmatch wildcards while `git show`'s is a literal tree lookup, so a stem containing `[`, `?`, or `*` would match a different file or none. `--literal-pathspecs` makes both halves agree.

## The memory-file variant

The `diff -q` clause is the one that catches a path tracked while its current bytes were never committed. **For a memory file, replace it with containment**: the file legitimately differs from its committed state because other entries may have been added since, so the test is whether `git show "$SHA:$P"` still holds *this entry's* heading and body — byte equality would fail on a file that is perfectly recoverable.

Either way a failed comparison yields `uncommitted — not recoverable`. A removal line naming a commit that does not hold the deleted content is worse than one admitting the loss, because it stops anyone looking further.

## One determination per run

These pointers are the run's single recoverability determination: Step 4 recorded them, Step 7 gated on them, and Step 8.3 writes them. Nothing between those points changes a committed blob, so they are not recomputed per removal — resolve once, carry forward.

Where a pointer reads `uncommitted — not recoverable`, say so at the moment of removal and, per CLAUDE.md → Safety rules, offer to commit first.

## The removal record

git history preserves what this skill deletes, but only if a reader knows what to look for — a path and a commit. `1-wiki/log.md` is already the permanent, complete record of every operation, so the removal record goes there rather than into a separate file: fill in the `Removed:` sub-list of the Step 6 log entry, one line per removal, from both jobs, output files and cleared memory entries alike. No kind is exempt — whether an artifact will be wanted again is not knowable at deletion time, and a line costs nothing against a lost report.

```markdown
- Removed:
  - `2-outputs/query/query-YYYY-MM-DD-HHMM-{topic}.md` — query report | {one-line topic} — `{40-char SHA}`
  - `.claude/skills/{skill}/{skill}-memory.md` — memory entry | "{entry heading}" — `{40-char SHA}`
  - `2-outputs/brief/brief-YYYY-MM-DD-HHMM-{topic}.md` — brief | {one-line topic} — uncommitted — not recoverable
```

Each line is: path, what it was, a short human descriptor, and the pointer — the verified SHA, or the `uncommitted — not recoverable` marker in its place, as the third example shows. The entry's own heading supplies the date, so the line does not repeat it. The descriptor is the report's topic or the entry's heading; a filename alone is a poor search key once the report itself is gone. Record the full 40-character SHA, not an abbreviation, which can go ambiguous as a repo grows. Recover with `git show <sha>:<path>`. A recorded SHA is reachable in the object store but not immortal: a later `rebase`, `--amend`, or squash of that commit orphans it, so the descriptor is what survives to identify the content by hand.

This is also what repairs the dangling-link case: `CLAUDE.md` expects a historical `log.md` link into `2-outputs/` to dangle once its target is pruned, and now the entry that pruned it carries the recovery pointer, so a dead link and its remedy sit in the same file.
