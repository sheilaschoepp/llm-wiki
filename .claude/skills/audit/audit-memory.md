---
type: memory
skill: audit
updated: 2026-08-17
---

# Audit memory

Corrections, rewrites, and scope adjustments specific to the `audit` skill. Read at the start of every audit operation.

Cross-skill rules live in `.claude/skills/multi-skill/multi-skill-memory.md` — read that file too.

Newest entry on top, one entry per heading.

## 2026-08-17 — audit holds no state between runs, so no mechanism may depend on one

A session proposed bounding the staged valve with "a page may stage once", carrying the stage count in audit's report. Five refuters killed it, and the reason generalizes well past that one edit: **audit cannot know what a previous audit did.** It reads lint's report (`SKILL.md:82`) and consistency's (`SKILL.md:88`); its only touch of `2-outputs/audit/` is `verification-spec.md:38`, which reads a timestamp for a git-log comparison, never content. And even given the count, three rules forbid acting on it — `apply-fixes.md:24` ("Never inherit a finding from a prior report. Re-derive it, or drop it"), `SKILL.md:166`, and `SKILL.md:221` ("a new status ... never in recollection or a prior report's say-so").

So any proposed audit mechanism whose behaviour depends on run history — a counter, a "second time is different" rule, an escalation across passes — is unimplementable here, not merely unimplemented. The only state audit may read is the current state of the wiki: page status, `verified_hash:`, `needs_update_reason:`, markers, and the pages themselves. Design against that surface, and treat "what did the last run do?" as a question the skill is built never to ask.

Two corollaries that also bit: a staged page needs no help re-entering scope (`SKILL.md:36` already admits every `draft` and `needs-update` page unconditionally), and a terminal of `needs-update` naming *clearable* residual work can never reach `settled` under `CLAUDE.md`'s definition, so it keeps counting in `pages_pending:` forever rather than closing.
