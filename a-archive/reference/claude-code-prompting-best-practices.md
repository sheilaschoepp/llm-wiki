# Prompting in the Claude Code VS Code extension

A working guide to applying Anthropic's prompt-engineering advice inside the VS Code extension rather than through the API.

> **What this is derived from.** The technique in this guide comes from two sources: Anthropic's prompt-engineering documentation, and an earlier synthesis of that documentation plus the guardrail pages and the interactive tutorial. Both are written for people calling the API. The translation onto the extension's actual surface — which files, which commands, which settings — was verified against Claude Code's current documentation on 2026-07-12 and is marked where it matters. Context-window management is deliberately **not** covered here; the companion to this guide is `claude-code-context-management-best-practices.md`.
>
> **Terminology.** The VS Code extension is Claude Code in a VS Code wrapper. Same engine as the terminal CLI, different chrome. Almost everything below applies to both; the handful of genuinely VS Code–only points are flagged as such.

---

## What changes when you leave the API

In the API, a prompt is one string you assemble and send. You control the system prompt, the message list, the temperature, the token ceiling, the thinking configuration, and whether the response is forced into a schema. Anthropic's prompt-engineering docs are written for that world, and roughly half of what they teach is about parameters you cannot reach from a chat box.

In Claude Code the prompt is not a string. It is a workspace, assembled from layers that load at different moments and cost different amounts. `CLAUDE.md` loads every session whether you need it or not. A skill's body loads only when its description matches what you asked for. A subagent's instructions never enter your context window at all. What you type in the chat box is only the last layer.

So the durable technique survives — be clear and direct, explain why, show examples, structure with XML, say what to do instead of what to avoid — but each technique now has a *home*, and putting it in the wrong home is the characteristic failure. A long block of few-shot examples pasted into `CLAUDE.md` is paid for in every session, including the ones where you are fixing a typo. The same block inside a skill costs one line of description until the moment it is needed.

Choosing the layer is the part the source documents cannot help you with. It is most of the job.

---

## Part 1 — Where a prompt lives

### The layers

| Layer | When it loads | What belongs there | What it costs when unused |
|---|---|---|---|
| `CLAUDE.md` | Every session, always | Durable rules that hold across all work: role, tone, conventions, safety posture, spelling | Paid in full, every session |
| `.claude/skills/<name>/SKILL.md` | Lazily, when its description matches your request | Task-specific procedure, examples, output formats, long instruction blocks | One line — only the name and description are always present |
| `.claude/agents/<name>.md` (subagents) | Inside the subagent's own fresh context | A delegated role, its tools, its model, its effort level | Nothing. It never touches your window |
| `.claude/commands/<name>.md` | When you invoke it as a slash command | A parameterized one-shot prompt you run often | Nothing |
| `.claude/settings.json` | Every session | Model, effort level, permissions, hooks | — |
| The chat box | Now | The immediate task, the data, the question | — |

Two facts drive most of the placement decisions, and both are verified. Skills are lazy: the body enters context only when the skill fires, and then stays for the session. Subagents run in a genuinely isolated context window and return only their final message to you, so anything a subagent reads is a cost you never pay.

Skills are the currently preferred form for anything reusable. `.claude/commands/` still works — the `cp` commit-and-push command shipped alongside this guide is one — but skills carry richer frontmatter (`model`, `effort`, `allowed-tools`, `argument-hint`, and more) and are the direction the tooling is moving.

### Anthropic's ten-element prompt, relocated

The capstone of the source synthesis is a ten-element skeleton for building a complex prompt from scratch. It is still the right checklist. In Claude Code the elements scatter across layers instead of stacking in one string, and this table is the translation:

| Element | Where it goes in Claude Code |
|---|---|
| 1. Task context (role, overarching goal) | `CLAUDE.md` if it holds for all your work; a skill body if it is task-specific; a subagent body if you are delegating the role |
| 2. Tone context | `CLAUDE.md` |
| 3. Background data and documents | The chat box, as `@`-references — and they go *above* your question, not below |
| 4. Detailed task description and rules | A skill body for anything you will do more than twice; the chat box for a one-off |
| 5. Examples | A skill body. Because skills load lazily, a long `<examples>` block is close to free until the skill fires |
| 6. Conversation history | The session itself. Use `/clear` when you change topic, so stale turns stop competing for attention |
| 7. Immediate task | The chat box, and it is the last thing you type |
| 8. Precognition (reason before answering) | The effort level, mostly. Add explicit reasoning instructions only when you need to *see* the reasoning |
| 9. Output formatting | Skill body or chat box. Tags like `<response>` still work |
| 10. Prefill | Gone. Prefill returns a 400 on current models and has no analogue in the extension. Say "respond directly, without preamble" instead |

Note that elements 3 and 7 encode the long-context rule from both sources: put long inputs near the top of the prompt and the question near the bottom, which testing showed can improve response quality by up to about 30% on complex multi-document inputs. In the chat box that means paste or `@`-reference your material *first*, then ask. The habit of typing the question and then attaching the file inverts the ordering the model does best with.

### Getting material into the chat box

`@`-referencing a file reads its contents into context. `@`-referencing a folder gives you a directory listing, not the contents of everything inside — a useful distinction when you are tempted to point at `src/` and hope. You can scope to a line range with `@file.py#40-80`, which is the cheapest way to hand over a specific function without dragging in the whole module.

Two VS Code–specific conveniences: your editor selection is passed automatically (the status bar shows the line count, and the eye-slash icon suppresses it), and `Option+K` inserts an `@file#line-line` reference for the current selection. One oddity worth knowing on macOS: pasting an image uses `Ctrl+V`, not `Cmd+V`.

---

## Part 2 — What carries over unchanged

These are the techniques from both sources that pay off most, and they work here exactly as documented. The only thing that changes is which layer you write them into.

**Be clear and direct.** The golden rule from the docs is a test you can actually run: show your prompt to a colleague with no context and ask them to follow it. If they would be confused, so is Claude. Be specific about the output you want and the constraints on it. If the order or completeness of steps matters, number them. And if you want work that goes beyond the obvious, ask for that explicitly — "create an analytics dashboard" and "create an analytics dashboard, include as many relevant features and interactions as possible, go beyond the basics" produce very different results from the same model.

**Explain why, not just what.** A rule with a reason attached generalizes to cases you did not enumerate; a bare prohibition does not. The documented example is instructive: "never use ellipses" is weaker than "your response will be read aloud by a text-to-speech engine, which cannot pronounce ellipses." This matters more in `CLAUDE.md` than anywhere else, because a rule written there will meet situations you never imagined when you wrote it.

**Show examples.** Few-shot examples remain the most reliable way to steer format, tone, and structure, and the docs call this the single most effective lever in knowledge-work prompts. Aim for three to five. Make them relevant (mirroring your real case), diverse (covering edge cases, and varied enough that Claude does not latch onto an accidental pattern), and structured (each in `<example>` tags, the set in `<examples>`). Put them in a skill, not in `CLAUDE.md` — this is the placement decision that pays for itself most obviously. You can also ask Claude to critique your examples for relevance and diversity, or to generate more from a seed set.

**Structure with XML tags.** When a prompt mixes instructions, context, examples, and data, wrapping each kind in its own descriptive tag stops the model from conflating them. There are no magic tag names outside of tool calling, so name them whatever is clearest, but be consistent, and nest where the content has a real hierarchy. This is worth doing in `CLAUDE.md` and skill bodies, which are exactly the mixed-content prompts the technique was designed for.

**Say what to do, not what to avoid.** "Compose your response in flowing prose paragraphs" beats "do not use markdown." Positive examples of the behaviour you want outperform prohibitions, and matching your own prompt's style to the output style you want nudges in the same direction.

**Ask for action when you want action.** "Can you suggest some changes to improve this function" will sometimes get you suggestions when you wanted edits. "Change this function to improve its performance" gets you edits. In an IDE this is the difference between a paragraph and a diff, and it is worth being deliberate about. You can set the default posture in `CLAUDE.md` in either direction — act by default, or research and recommend by default and only act when asked. The `CLAUDE.md` shipped alongside this guide already takes the second position for anything non-trivial.

**Small details matter.** Typos, sloppy grammar, and disorganized structure in the prompt measurably degrade the output. Proofread instructions to a model for the same reason you would proofread instructions to a person.

**Ground long documents in quotes.** For anything over roughly 20k tokens, asking Claude to first pull out the verbatim passages relevant to the task, and only then to do the task, helps it cut through the surrounding noise. It is also the most effective defence against near-miss distractor passages, because a quote-first pass lets the model notice that the available evidence does not actually answer the question.

**Watch ordering effects on close calls.** On genuinely borderline judgements Claude is somewhat more likely to pick the second of two options. When you ask it to weigh alternatives, know that swapping the order can flip the verdict, and that asking it to lay out the case for each side before committing reduces the fragility.

---

## Part 3 — Reasoning and effort

The API controls reasoning depth with the `effort` parameter and turns thinking on with `thinking: {type: "adaptive"}`. Neither is a per-message control in the extension, and this is the translation people get wrong most often.

There is no `/effort` slash command — verified absent. Effort is set three ways: the `CLAUDE_CODE_EFFORT_LEVEL` environment variable in `settings.json`, an `effort` field in a skill's frontmatter, or an `effort` field in a subagent's frontmatter. Check what yours is set to before assuming; the `settings.json` shipped alongside this guide pins neither, leaving both to the session.

The calibration ladder from the source, worth knowing even though you are pinned at the top of it:

- `max` — can help on intelligence-demanding work, with diminishing returns and some tendency to overthink.
- `xhigh` — the recommended setting for most coding and agentic work.
- `high` — the recommended minimum for anything intelligence-sensitive.
- `medium` — for cost-sensitive work, trading intelligence for tokens.
- `low` — short, scoped, latency-sensitive tasks only.

The operational rule: **if you see shallow reasoning on a hard problem, raise effort rather than prompting around it.** Opus 4.8 respects effort strictly at the low end, scoping its work narrowly to what was asked, so under-thinking on a moderately complex task at `low` or `medium` is a settings problem wearing the costume of a prompting problem. The reverse is also true — a per-skill `effort: low` is the honest way to make a mechanical skill cheap, rather than writing "be brief" into its body and hoping.

Two smaller points from the sources. When you do want reasoning visible rather than internal, structured tags still work: ask for `<thinking>` and `<answer>` blocks, and remember that reasoning only counts when it happens out loud — you cannot ask the model to think silently and emit only the answer, because in that case no thinking has occurred. And when thinking is off, some models are sensitive to the literal word "think," so "consider," "evaluate," or "reason through" can work better. Prefer a general instruction ("reason thoroughly") over a hand-written step-by-step plan; the model's own reasoning routinely exceeds what a human would prescribe.

Finally, the cheapest reliability win in the whole document: **ask for a self-check.** "Before you finish, verify your answer against these criteria" catches errors reliably, especially in coding and maths, and Claude tends to hold firm when its first answer was already right rather than second-guessing itself into a worse one.

---

## Part 4 — Working agentically in a repo

This is where the two sources are richest, because it is where current models actually spend their time.

**Dial back anti-laziness prompting.** Instructions tuned for older models — "CRITICAL: you MUST use this tool" — now cause *over*triggering. Normal phrasing ("use this tool when…") is correct. Likewise, "if in doubt, use [tool]" and blanket "default to using [tool]" defaults will over-fire; prefer "use [tool] when it would improve your understanding of the problem."

**Guard against overengineering.** Recent Opus models tend to create extra files, add abstractions nobody asked for, and build in flexibility for hypothetical futures. The source's counter-instruction is a good candidate for `CLAUDE.md`: do not add features, refactor, or make improvements beyond what was asked; a bug fix does not need the surrounding code cleaned up; do not add error handling for scenarios that cannot happen; do not create abstractions for one-time operations. The right amount of complexity is the minimum the current task needs.

**Guard against test-gaming.** Claude can focus on making tests pass at the expense of a general solution, or reach for helper scripts instead of the standard tools. Ask for a principled implementation that works for all valid inputs rather than the test cases, and tell it to say so if a task is infeasible or a test is wrong rather than working around it.

**Guard against claims about unopened code.** This is the one to actually write down if you write down nothing else, given how much of research work is reading unfamiliar repositories. The source's snippet: never speculate about code you have not opened; if the user references a file, read it before answering; investigate before making claims about the codebase.

**Be explicit about reversibility.** Without guidance, models will take actions that are hard to undo — deleting files, force-pushing, posting to external services. The documented instruction asks Claude to weigh reversibility and impact, to freely take local reversible actions like editing files and running tests, and to check first for anything destructive, hard to reverse, or visible to others. The `settings.json` shipped alongside this guide enforces the same posture structurally through its `permissions.deny` list, which is stronger than a prompt, because a prompt can be reasoned around and a deny rule cannot.

**Steer subagents deliberately.** Opus 4.8 spawns fewer subagents than its predecessors by default, and the behaviour is promptable in either direction. Delegation is warranted for parallelizable work, isolated context, and independent workstreams; it is not warranted for simple sequential work, single-file edits, or anything where context needs to carry across steps. Ask for parallel tool calls when the calls are independent, and never let the model guess a missing parameter.

**Let the repository be the memory.** For work that spans context windows, the sources converge on a pattern that fits a research workspace almost exactly: use structured formats (JSON) for state like test results, freeform text for progress notes, and git for checkpoints and history. Write tests early and treat them as immutable. Build small quality-of-life scripts so a fresh window does not repeat setup. And when a window fills, consider starting a genuinely fresh one rather than compacting — current models are very good at rediscovering state from the filesystem, and a fresh context that reads `progress.md` and the git log is often cleaner than a compacted one carrying the residue of everything you have already resolved.

**Front-load the first turn.** Opus 4.8 uses more tokens in interactive, multi-turn sessions than in single-turn autonomous ones, because it reasons again after every user turn. That improves long-horizon coherence but costs tokens, and the fix is to specify the task, the intent, and the constraints fully in the first message rather than dribbling them out across ten. A well-specified opening turn is both cheaper and better. Ambiguous prompts delivered progressively are the worst case on both axes.

---

## Part 5 — Guardrails worth keeping, and ones you can skip

**Reducing hallucination.** No technique eliminates it, so critical facts still need checking, but the rate drops sharply with a few habits. Give Claude an explicit out — "only answer if you know with certainty; say you don't know otherwise" — because the default failure mode is a plausible answer rather than an admission of ignorance. For long documents, extract quotes before answering. Require a supporting quote or citation for each claim, and ask it to retract anything it cannot support. Where a claim is load-bearing, ask for the reasoning explicitly, which exposes the faulty assumption.

**Increasing consistency.** Beyond examples and format specification, ground answers in a fixed retrieved set where you can, and break large tasks into focused subtasks. The most useful chaining pattern is self-correction: draft, review against explicit criteria, then refine.

**What you can skip.** Both sources devote real space to jailbreak mitigation, prompt-injection screening, prompt-leak hardening, and latency tuning. All four are concerns for people shipping a Claude-powered product to third-party users. None of them is a concern for you writing prompts in your own IDE against your own repository, and the prompt-leak section says outright that leak-resistant prompting degrades performance elsewhere and should be a last resort. Skip them. Structured Outputs is likewise the correct answer to strict JSON conformance in the API and is simply unavailable here.

---

## Part 6 — Claude Opus 4.8 specifics

> This section is tied to whichever model your session is running, and will date faster than everything above. Check which model you are on, and re-check this section against the live documentation on any model change.

**It follows instructions literally.** Opus 4.8 interprets prompts explicitly and does not silently generalize an instruction from one item to the next, especially at lower effort. This is a feature for structured extraction and pipelines and a trap for casual phrasing: if you want a rule applied broadly, say so. "Apply this to every section, not just the first" is not redundant with this model.

**It calibrates length to task complexity.** Expect short answers on lookups and long ones on open-ended analysis, rather than a fixed verbosity. If you want it shorter, ask for concise focused responses that skip non-essential context — and note that positive examples of appropriately concise output steer better than instructions about what not to do.

**It favours reasoning over tool calls.** Usually the right trade, but if you want more tool use, raising effort is the first lever; explicitly describing when and why to use a given tool is the second.

**It gives good progress updates unprompted.** If you have scaffolding that forces interim summaries every N tool calls, try removing it.

**Code review has a severity trap.** Opus 4.8 finds more bugs than its predecessors but also obeys "only report high-severity issues" more faithfully, which can look like a recall regression. Prompt for coverage at the finding stage — report everything, including low-confidence and low-severity findings, with a confidence and severity attached — and filter downstream.

**Frontend work has a house style.** Warm cream backgrounds, serif display type, terracotta accents. Fine for editorial briefs, wrong for dashboards. Generic negation ("don't use cream") just moves it to a different fixed palette. Either specify a concrete alternative palette and typography precisely, or ask it to propose several distinct directions and pick one.

**It creates scratchpad files.** Temporary scripts and helper files during agentic coding are normal and often improve outcomes. Ask for cleanup at the end of the task if you do not want them.

---

## Part 7 — What does not transfer

Everything in this table is confirmed unavailable in the extension. When a source document tells you to reach for one of them, this is what to reach for instead.

| API technique | Status here | Use instead |
|---|---|---|
| Response prefill | Absent (and returns a 400 on current models generally) | An explicit instruction: "respond directly, no preamble"; or ask for output inside tags |
| Structured Outputs / JSON schema enforcement | Absent | Describe the schema and show an example; retry on mismatch |
| `temperature`, `top_p` | Not settable | Effort level; for design variety, ask for several distinct directions |
| `max_tokens` | Not settable | Ask for a length in sentences or paragraphs — models count tokens, not words, so word limits steer badly |
| `budget_tokens` | Absent | Effort level |
| Authoring the system prompt | Not directly available | `CLAUDE.md`, skill bodies, subagent bodies |
| Mid-conversation system messages | Absent | A new chat-box turn; `CLAUDE.md` is read at session start |
| Streaming, latency tuning, model-choice-for-speed | Not your lever | — |

---

## Part 8 — The short version

1. Put durable rules in `CLAUDE.md`, and keep it under about 200 lines — the current guidance. Run `/context` to see what yours actually costs.
2. Put examples, procedures, and long instruction blocks in skills, where they cost nothing until they fire.
3. Delegate to subagents when work is parallel, isolated, or independent — their reading never enters your context.
4. In the chat box, material first, question last.
5. Specify the task, the intent, and the constraints in your first message. Do not dribble.
6. Ask for action when you want action.
7. Give the reason behind a rule. A rule with a reason attached generalizes to cases you never enumerated; a bare prohibition does not.
8. Raise effort before you write a prompt to compensate for shallow reasoning.
9. Ask for a self-check before it finishes.
10. Tell it never to make claims about code it has not opened.

---

## Sources

- Anthropic, prompt-engineering documentation: the overview (when prompt engineering is the right tool at all), general principles, output and formatting, tool use, thinking and reasoning, agentic systems, the model-specific pages for Claude Opus 4.8, Claude Fable 5, and Claude Sonnet 5, and migration considerations.
- A general synthesis of Anthropic's prompt-engineering docs, the guardrail pages (hallucination, consistency, prompt leak, jailbreaks, latency), and the interactive tutorial, including the ten-element complex-prompt skeleton relocated in Part 1.
- Claude Code documentation, consulted 2026-07-12 for the extension surface: instruction-file scopes and precedence, `@`-reference behaviour, slash commands, plan mode, skill and subagent frontmatter, settings keys, and confirmation of the absences listed in Part 7.
