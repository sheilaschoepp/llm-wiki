# Managing context in the Claude Code VS Code extension

A working guide to defending the context window from inside the extension, rather than configuring it through the API.

> **What this is derived from.** Two sources in `../sources/`, and they are not equal. `claude-context-management.md` is Anthropic's own API documentation (context windows, compaction, context editing, prompt caching, mid-conversation system messages) — authoritative, but it never once mentions Claude Code, VS Code, or the extension. It supplies *mechanism*, not levers. `claude-code-context-optimization.md` is a research report about the extension specifically — it supplies the levers, but it mixes official documentation with community and experiential claims, and flags several of its own numbers as heuristics. Where the two disagree, or where a claim is load-bearing, the API documentation wins and the quote is given. Verified against the source files on 2026-07-12; version-gated behaviour is marked.
>
> **Companion folder.** `references/prompting/outputs/claude-code-prompting-best-practices.md` covers *what to write and where it lives*. This covers *what each layer costs and how to stop the window filling*. The layer table there (Part 1) and the cost argument here are the same structure seen from two sides; read that one first if you have not.

---

## What changes when you leave the API

In the API, managing context is something you configure. You assemble the `messages` list yourself. You set a compaction trigger and write the summarization prompt. You choose which tool results get cleared and how many to keep. You place cache breakpoints. You call `count_tokens` before you send. The 17,000 lines of API documentation in `../sources/claude-context-management.md` are almost entirely about those knobs.

In Claude Code, every one of those knobs belongs to the harness. You cannot set a compaction trigger, write a summarization prompt, clear a specific tool result, place a cache breakpoint, or count tokens before sending. What you get instead is a handful of product-level commands, a few environment variables, and one capability the API user does not have: the ability to keep material **out of the window in the first place**, through subagents, lazily-loaded skills, and targeted reads.

So the job inverts. The API user tunes a pipeline that processes a context they have already assembled. You have almost no pipeline, and you win or lose on assembly discipline. Nearly everything actionable is upstream of the model, not inside it.

That is also why most of the API source does not apply, and Part 5 says exactly which parts to stop reading.

---

## Part 1 — How the window actually fills

Five mechanisms from the API documentation, each of which overturns something people assume.

**Everything counts, including the output.** "Everything in the request counts toward the context window: the system prompt, every message in `messages` (including tool results, images, and documents), and your tool definitions. The output Claude generates for the turn, including its extended thinking, counts too." Conversation is progressive — each turn carries the entire history forward and reprices it. A turn at 150k input costs five times a turn at 30k for the same question.

**Caching does not save space.** This is the misconception worth killing first, because it is the one that sends people down a useless path. "Cached prompt prefixes still occupy the context window: prompt caching changes what you pay for those tokens, not whether they count." Caching is a cost and latency lever. It does nothing for window occupancy, and in the extension you do not control it anyway — Claude Code places the breakpoints. Anything you read about `cache_control`, TTLs, or the 20-block lookback is not a context lever for you. Skip it.

**Thinking is kept, and re-billed as input.** On Opus 4.5 and later, and Sonnet 4.6 and later, "the API keeps previous thinking blocks by default, and they count toward the context window like any other input tokens." Billing follows: thinking tokens are charged as output when generated, and then "the kept blocks are then part of later requests' input and are billed as input tokens." Older models stripped them; current ones do not. This workspace runs `CLAUDE_CODE_EFFORT_LEVEL: max`, which means deep reasoning on every turn, accumulating in the history, re-sent and re-billed on every turn after. Max effort is not a flat per-turn cost. It compounds.

**Your model cannot see its own fuel gauge.** Some models get a token budget injected into every request — a `<budget:token_budget>` tag in the system prompt, and after each tool call a `<system_warning>Token usage: 35000/200000; 165000 remaining</system_warning>`. The documentation is specific about who: "Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, and Claude Haiku 4.5 have context awareness." And then: "Newer models don't receive these injected tags. On Claude Opus 4.7 and later…" This workspace pins `opus[1m]`. Claude is therefore *not* tracking its remaining budget in your sessions, and will not warn you as it fills. If you have been waiting for it to say something, it never will. Instrument it yourself.

**The same text costs about 30% more than it used to.** "Claude Opus 4.7 and later Opus models, Claude Fable 5, Claude Mythos 5, Claude Mythos Preview, and Claude Sonnet 5 use a newer tokenizer. The same input text produces approximately 30% more tokens than on earlier models." A file that comfortably fit last year does not necessarily fit now, and a 1M window is not as much headroom as the number suggests. If your context numbers jumped after a model upgrade, suspect the tokenizer before you suspect yourself.

**What happens at the wall.** If the input alone exceeds the window, the API returns a 400, `prompt is too long`. On 4.5-and-later models, if input plus the output ceiling would exceed the window, the request is accepted and generation simply stops with `model_context_window_exceeded`. In the extension you rarely hit either, because auto-compaction fires first — which is the problem, since it fires when the model is already degraded.

---

## Part 2 — The levers you actually have

Ordered by how much space they buy, for this workspace.

### Measure first: `/context`

Your substitute for the API's `count_tokens`. It breaks usage down by category — system prompt, tools, MCP, memory, skills, messages — with optimization hints; `/context all` expands everything. `/memory` shows which instruction files loaded. Run it *before* a large task, not after the window is full.

The VS Code context indicator only surfaces prominently near about 80%, by which point your options have narrowed to compacting a degraded session. Do not rely on it. The rule from the API side transfers cleanly: measure before you optimize, and do not trust intuition.

### Keep material out: subagents

A subagent runs in its own context window and returns only its final message to the parent. Everything it reads — the greps, the file contents, the logs — stays in its window and never touches yours. This is the single most effective lever available, because it is the only one that prevents tokens rather than reclaiming them.

Concretely: this guide was written after reading a 650 KB source file that never entered the main session, because a Sonnet subagent read it and returned a brief.

Three things to get right.

*Route the model.* A subagent inherits the main conversation's model unless told otherwise, so on `opus[1m]` your file-discovery worker is running on Opus. Set `model:` in the subagent's frontmatter (`haiku`, `sonnet`, `opus`, or `inherit`), or set `CLAUDE_CODE_SUBAGENT_MODEL` globally. Haiku for discovery, search, extraction, and reformatting; Sonnet for implementation; Opus only when the subagent must genuinely reason.

*Override `Explore`.* The built-in `Explore` agent now inherits your main model rather than always running on Haiku. To force it back, define a project subagent literally named `Explore` with `model: haiku`.

*Ask for extractive returns.* Tell a research subagent to return the specific findings relevant to your task, not to summarize everything it saw. When several subagents each return a long report, those reports accumulate in *your* window and you have moved the problem rather than solved it. Terse and extractive beats thorough and abstractive.

### `/clear` between unrelated tasks

The cheapest reset, and the most underused. One conversation per intent. If you have corrected Claude more than twice on the same point, the context is now polluted with the wrong turns — clear it and restart with a better first message rather than arguing with the residue. `CLAUDE.md` and memory reload automatically afterwards, so you lose less than you think.

### `/compact` early, and with a focus

Auto-compaction fires around 83% of the window, which is to say it fires after quality has already dropped. Compact deliberately at a task boundary instead, and steer it: `/compact focus on the memory-file edits, ignore the source-reading` keeps what matters instead of producing a generic précis.

Know what compaction actually is: it summarizes older content and replaces it. The API documentation is candid about where that goes wrong, and lists as poor fits "tasks requiring precise recall of early conversation details" and "tasks that need to maintain exact state across many variables." The default summary keeps five things — the task, the current state, discoveries, next steps, and context to preserve. Assume anything outside those five buckets is gone.

The consequence is a habit, not a setting: **write the plan, the decisions, and the file paths to disk before a long task**, so compaction cannot lose them. In this workspace that is what the memory files already do. After a compaction, ask Claude to restate the goal, the files changed, and what remains.

To move the trigger earlier, export `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75` **in your shell profile**, not in `settings.json` — there is a known bug where the `env` block silently ignores it.

### Read narrowly

Unscoped reads are the largest recurring sink after conversation length itself.

- Reference lines, not files: `@file.py#40-80` hands over one function instead of the module.
- Prefer grep and search over full reads. Scope the prompt — "in `src/routes/users.ts` line 42 the null check is wrong" costs a fraction of "fix the bug."
- Delegate anything large to a subagent, per above.
- Use a `PreToolUse` hook to preprocess. The documented example: rather than let Claude read a 10,000-line log, the hook greps for `ERROR` and returns the matching lines.
- Microcompaction already offloads large tool results to disk automatically, keeping a reference and a recent tail. You do not configure it; it is the product-level stand-in for the API's tool-result clearing.

### MCP tool hygiene

Tool definitions load per request and can be enormous — a documented 13-server setup consumed 82,000 tokens (41% of a 200K window) on an empty conversation.

Tool search (deferred loading) is on by default: only tool names load at startup, and full definitions load on demand. That is why this workspace's six connectors are cheap despite exposing 60-odd tools. Control it with `ENABLE_TOOL_SEARCH` — unset defers everything (the default), `auto` loads upfront only if the tools fit within 10% of the window, `false` restores the old load-everything behaviour.

**Measured here, this is not your lever.** `/context` puts *all* system tools at 15.8k — built-ins and six connectors together, against sixty-odd exposed tools. Loaded eagerly those schemas alone would run many times that, so deferred loading is demonstrably working. The research report's own threshold check says that if MCP is small and messages are the bulk, the problem is session length rather than MCP; for this workspace that check now resolves, and it resolves against MCP hygiene. Skip the section.

Keep the rest for the day it stops being true: run `/mcp` to see servers and toggle them. This workspace has no project `.mcp.json` — the connectors are account-level, so `disabledMcpjsonServers` in project settings will not touch them. Where a CLI exists, prefer it: `gh` adds no per-tool listing cost, a GitHub MCP server does.

### The always-loaded tier — and what only looks like it

`CLAUDE.md` is the always-loaded tier, and it is the whole of it. It is injected on every request, it can never be compacted away, and `/context` measures it here at **8.9k tokens**. The guidance is to keep it under about 200 lines and to ask of each line whether removing it would cause a mistake. This workspace's file is 158 lines, comfortably inside.

The trap is assuming the rest of the session-start protocol lives in the same tier. It does not. `/context` lists exactly one memory file. `MEMORY.md`, `about-me.md`, and `ai-writing-tells.md` are not auto-injected — the protocol has Claude *read* them, so they arrive as tool results and live in **Messages**. That difference is not cosmetic. Messages can be compacted, summarized, and cleared; `CLAUDE.md` cannot. So the three protocol reads are recoverable mid-session, and the 8.9k is not.

It also means the readable files are cheaper to fix than they look. `MEMORY.md` was ~37k tokens of mostly historical activity log, read in full every session; archiving its tail cut it to ~18k without deleting anything (Part 3). That fix was available precisely *because* the file is a read and not a floor — you cannot archive your way out of `CLAUDE.md`.

Push detail down a tier wherever you can. Skill descriptions load at startup; skill *bodies* load only when invoked. A long procedure in a skill costs one line until the moment it fires.

### Effort and thinking

Thinking counts toward the window, and on your model it stays there (Part 1). `CLAUDE_CODE_EFFORT_LEVEL` is set to `max` in `.claude/settings.json`. For routine mechanical work — reformatting, extraction, a spelling sweep — that is paying for reasoning you do not need, on every turn, forever. `MAX_THINKING_TOKENS` caps generation; per-skill and per-subagent `effort` frontmatter is the honest way to make a cheap task cheap.

One correction to the research report: it recommends lowering `/effort` as a slash command. There is no `/effort` slash command — the companion prompting guide verified its absence on 2026-07-12. Effort is set through the environment variable or through skill and subagent frontmatter, and nowhere else.

### The 1M window is a valve, not a fix

You are already on `opus[1m]`, so this one is spent. Worth stating anyway: a bigger window delays compaction, it does not improve a noisy context. A million tokens of unclear conversation is still unclear, and thanks to the tokenizer change it is fewer effective tokens than it sounds. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` caps back to 200K if you ever want the smaller, cheaper window.

---

## Part 3 — This workspace, measured

Not estimated. This is `/context` from a real working session on 2026-07-12 — the session in which this guide was written. **168.9k of 1M used (17%), 830.5k free.**

| Category | Tokens | Share of what was used |
|---|---|---|
| Messages | 137.5k | **81%** |
| System tools | 15.8k | 9% |
| Memory files (`CLAUDE.md` only) | 8.9k | 5% |
| System prompt | 4.4k | 3% |
| Skills | 3.0k | 2% |

Three things fall out of this, and two of them contradict what I would have guessed before running it.

**The conversation is the entire problem.** Messages are 81% of everything used. Every other category combined is a fixed floor of roughly 32k that you pay before typing a word, and it is small and boring. So the only levers that matter here are the ones acting on Messages: `/clear`, subagent delegation, `/compact`, narrower reads, and effort. MCP hygiene and `CLAUDE.md` pruning are rounding errors at this scale — real advice in general, noise for you.

**The 1M window is doing more work than it looks.** 168.9k is a comfortable 17% here. On a 200K model the identical session would sit at 84% — past the auto-compaction trigger, in the degradation zone the research report calls the danger zone. That report's thresholds (~147–152K) were written for a 200K window and simply do not describe your situation.

**Only `CLAUDE.md` is always-loaded.** This is the structural point worth internalizing, and the one the first draft of this guide got wrong. `/context` lists exactly one memory file. The other three files the session-start protocol pulls in are read, not injected, so they live in Messages and are compactable — while `CLAUDE.md` is re-sent on every request and never can be.

### The session-start protocol, costed

At the measured ratio (see Caveats), the protocol's reads are not free:

| File | Chars | Tokens | Tier |
|---|---|---|---|
| `CLAUDE.md` | 24,439 | **8.9k** (measured) | Always-loaded. Permanent floor. |
| `MEMORY.md` | 50,518 | ~18.4k | Messages. Compactable. |
| `ai-writing-tells.md` | 35,517 | ~12.9k | Messages. Compactable. |
| `about-me.md` | 11,147 | ~4.1k | Messages. Compactable. |

A full protocol run now costs roughly **44k before you type** — 8.9k of floor plus ~35k of Messages.

**It cost 63k this morning.** `MEMORY.md` was 102,735 characters (~37.4k tokens), almost all of it an append-only activity log reaching back to early May, and the protocol read every line of it every session. On 2026-07-12 the log's tail — everything from 2026-05-31 backwards, twelve of twenty-one dated entries — moved to `MEMORY-archive.md`, which the session-start protocol does not read. Nothing was deleted; the history is a file open away. The saving is ~19k tokens per session, and it recurs.

That is the shape of the best available fix in a workspace like this one. It was not a settings change or a smarter command. It was noticing that a file being read in full every session had quietly become mostly history, and moving the history somewhere the protocol does not look. Look for that pattern before you look for a flag.

One honest wrinkle about the 63k figure: no single session had actually paid it. The session that produced these numbers grepped `MEMORY.md` rather than reading it, so the ~37k never landed — this guide's own advice working by accident. The cost was real but latent, which is exactly how this kind of bloat survives.

### Settings, as configured

| Setting | Current | What it costs you |
|---|---|---|
| `model` | `opus[1m]` | 1M window, but no context-awareness tags — Claude will not warn you as it fills. Instrument with `/context`. |
| `CLAUDE_CODE_EFFORT_LEVEL` | `max` | Thinking blocks are kept on Opus 4.5+ and re-billed as input every turn. They accumulate in Messages — the 81% bucket. |
| `CLAUDE_CODE_SUBAGENT_MODEL` | unset | Subagents inherit Opus, including the built-in `Explore`. The cheapest unclaimed fix. |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | `75`, in `~/.zshrc` | Applied 2026-07-12. Compaction now fires before quality degrades rather than at the ~83% default. |
| `ENABLE_TOOL_SEARCH` | unset | Correct — unset means deferred, and `/context` confirms it is working. |
| Project `.mcp.json` | none | Six connectors are account-level; toggle via `/mcp`, not project settings. |

---

## Part 4 — Smaller commands worth knowing

- **`/rewind`** (or `Esc Esc`) — pick a checkpoint and summarize only part of the conversation, keeping the rest verbatim. Useful when one stretch of a session is bloated and the rest is worth keeping exactly.
- **`/btw`** — ask a question about the current context without tools, and without the answer entering the history. The cheapest possible question.
- **`/fork`** — inherits the full conversation and shares the parent's prompt cache, so it is cheaper than a fresh subagent when the task needs the same context. A named subagent starts fresh with a separate cache.
- **Plan mode** (`Shift+Tab`) — keeps exploration read-only, and the built-in Plan agent researches in a separate window, so its reading stays out of your thread. It adds overhead; skip it for one-line changes.

---

## Part 5 — What does not transfer

The API source is largely about knobs you cannot reach. When it tells you to configure one of these, this is what to reach for instead.

| API mechanism | Status in the extension | Use instead |
|---|---|---|
| `count_tokens` endpoint | Absent | `/context` |
| Compaction `trigger` parameter | Not settable | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (shell export only) |
| Compaction `instructions` parameter | Not settable | `/compact <focus instruction>` |
| `pause_after_compaction` | Absent | — |
| SDK `compaction_control` | Absent — and deprecated in the API too | Ignore that whole section of the source |
| `clear_tool_uses_20250919` | Not settable | Microcompaction, which does this automatically |
| `clear_thinking_20251015` | Not settable | `MAX_THINKING_TOKENS`, or a lower effort level |
| `cache_control`, TTLs, breakpoints | Managed by Claude Code | Nothing — caching does not save context space |
| Cache diagnostics beta | Absent | — |
| Mid-conversation system messages | The harness's lever, not yours | A new turn in the chat box |
| Task budgets (beta) | Absent | `/context`, manually |
| Batch API | Not an extension feature | — |

A note on the last few. Mid-conversation system messages are how an application operator injects authoritative facts partway through a conversation — "files changed on disk, the user toggled an auto-approve setting… the remaining token budget dropped below a threshold." In Claude Code, the harness is the operator, which is what the `<system-reminder>` blocks in a transcript are. They are not something you write.

---

## Part 6 — The short version

1. Claude will not tell you when the window is filling. On `opus[1m]` it cannot see its own budget. Run `/context` yourself, before big tasks.
2. **Measured here, the conversation is 81% of your context.** Everything else is a ~32k floor. Act on Messages; ignore MCP hygiene, which the numbers rule out.
3. Delegate every heavy read to a subagent — it is the only lever that prevents tokens rather than reclaiming them.
4. `/clear` between unrelated tasks. One conversation per intent.
5. `/compact` at a task boundary with an explicit focus, not at 95% under duress.
6. Write plans and decisions to disk before long tasks. Compaction is lossy in a documented, predictable way.
7. Read line ranges, not files. Grep before you read.
8. Max effort compounds, because thinking blocks stay in the history — inside the 81% bucket. Spend it where it earns.
9. Caching does not save context space. Stop looking for savings there.
10. Set `CLAUDE_CODE_SUBAGENT_MODEL` so subagents stop inheriting Opus. Still unset.
11. Audit what gets *read* every session, not just what gets loaded. `MEMORY.md` was ~37k tokens of mostly historical log; archiving the tail halved it and deleted nothing.
12. If you are compacting more than once per task, the task is too big. A larger window will not save you.

---

## Caveats

- **This surface moves fast.** Several behaviours are version-gated (tool search, `Explore` inheriting the main model, `alwaysLoad`). Check against `/context` and `/doctor` for your installed version rather than trusting this file.
- **Provenance differs by claim.** Everything quoted in Part 1 comes from Anthropic's API documentation and was verified line-by-line on 2026-07-12. The extension-level levers in Part 2 come from a research report that mixes official documentation with community claims; it flags several of its own figures (the ~147–152K danger zone, the 60% compaction rule, the 65% verbosity saving) as heuristics rather than Anthropic promises. Treat them as such.
- **Part 3's category table is `/context` output, not an estimate.** The per-file table is `wc` plus a calibration: `CLAUDE.md` is 24,439 characters and `/context` reports it at 8.9k tokens, so this workspace runs at about **2.75 characters per token**. Use that ratio, not the folk-wisdom four-characters-per-token — the naive figure understates these files by roughly 45%, which is the tokenizer inflation from Part 1 showing up in practice. Anything derived from the ratio is marked `~`; only the `CLAUDE.md` figure and the category table are measured.
- **A first draft of Part 3 was wrong, and the error is instructive.** It estimated the session-start protocol at "~42,000 tokens before your first message" and put all four files in the always-loaded tier. `/context` showed both halves to be wrong: the real per-file cost is higher (bad ratio), and only `CLAUDE.md` is actually always-loaded. Intuition about context is unreliable in both directions at once. Run the command.

---

## Sources

- `../sources/claude-context-management.md` — Anthropic's API documentation: context windows, compaction (server-side and the deprecated SDK form), context editing, prompt caching, mid-conversation system messages, token counting. Authoritative on mechanism; silent on Claude Code.
- `../sources/claude-code-context-optimization.md` — a research report on optimizing the VS Code extension specifically: MCP hygiene, subagent routing, the compaction and clearing commands, CLAUDE.md discipline. The source of most levers in Part 2, and the source of the heuristics flagged above.
- `references/prompting/outputs/claude-code-prompting-best-practices.md` — the companion guide. Where a prompt lives; what each layer is for.
