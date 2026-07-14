# Skill self-report

The canonical statement of the skill self-report convention, kept as a shared `multi-skill/references/` file so every skill carries the rule in its own tree — self-sufficient of `CLAUDE.md` at run time (the Skill Authoring self-sufficiency principle; `CLAUDE.md` → Skill Self-Report is the project-level summary). It binds every skill, read-only and write alike, and is a durable rule, not a provisional in-use correction — those, and only those, live in the `*-memory.md` files.

Every skill run ends with a self-report: a short, honest account of the limitations it hit *this run* and how the skill itself should be upgraded. It appears in the skill's report — or, for a skill that writes only a log entry (`synthesis`, `supersede`, `forget`), in that entry — as a `## Self-report` section, and is mirrored (one line per item) in the chat summary. `checkup` aggregates its sub-skills' self-reports plus its own.

It is present on **every** run: when the run genuinely hit no limitation the self-report reads `none noted this run`, so a reader can always see the skill checked itself.

This is a skill-improvement channel, not a reflective essay and not a quota:

- Each item is a **specific, genuine gap that actually bit this run** — a rule the skill was missing, a case it handled wrong, a capability it lacked — concrete enough to act on. The two founding examples set the shape: "audit confirmed a distorted claim it could not safely fix but left it as a passive finding instead of setting `needs-update`", and "ingest marked a whole page `draft` when it only added one bullet".
- **Never invent or pad.** A generic weakness ("could have been more thorough"), a limitation that did not actually arise this run, or self-flagellation to fill the section is the fabrication the wiki forbids everywhere else — `none noted this run` is the correct and expected content for a clean run, exactly as an empty callout placeholder is.
- Pair each limitation with its **upgrade**: how the skill's instructions should change so the gap does not recur.

Format, at the end of the report or log entry, and mirrored (one line per item) in the chat summary:

```markdown
## Self-report
- {specific limitation that bit this run} → upgrade: {how the skill should change}
- (or the single line: none noted this run)
```

A self-report item is the first surfacing of a skill limitation, not its resolution: a confirmed item graduates to the skill's memory file (`.claude/skills/<skill>/<skill>-memory.md`, which holds only provisional in-use corrections) or to a skill fix, through the ordinary user-gated path. The self-report itself never writes to memory or edits a skill.
