# Managing context in the Claude Code VS Code extension

A working guide to defending the context window from inside the extension, rather than configuring it through the API.

> **What this is derived from.** Two sources, and they are not equal. Anthropic's own API documentation (context windows, compaction, context editing, prompt caching, mid-conversation system messages) is authoritative, but it never once mentions Claude Code, VS Code, or the extension. It supplies *mechanism*, not levers. A research report about the extension specifically supplies the levers, but it mixes official documentation with community and experiential claims, and flags several of its own numbers as heuristics. Where the two disagree, or where a claim is load-bearing, the API documentation wins and the quote is given. Verified against the source files on 2026-07-12; version-gated behaviour is marked.
>
> **Companion sheet.** `claude-code-prompting-best-practices.md` covers *what to write and where it lives*. This covers *what each layer costs and how to stop the window filling*. The layer table there (Part 1) and the cost argument here are the same structure seen from two sides; read that one first if you have not.

---

## What changes when you leave the API

In the API, managing context is something you configure. You assemble the `messages` list yourself. You set a compaction trigger and write the summarization prompt. You choose which tool results get cleared and how many to keep. You place cache breakpoints. You call `count_tokens` before you send. The 17,000 lines of Anthropic's context-management API documentation are almost entirely about those knobs.

In Claude Code, every one of those knobs belongs to the harness. You cannot set a compaction trigger, write a summarization prompt, clear a specific tool result, place a cache breakpoint, or count tokens before sending. What you get instead is a handful of product-level commands, a few environment variables, and one capability the API user does not have: the ability to keep material **out of the window in the first place**, through subagents, lazily-loaded skills, and targeted reads.

So the job inverts. The API user tunes a pipeline that processes a context they have already assembled. You have almost no pipeline, and you win or lose on assembly discipline. Nearly everything actionable is upstream of the model, not inside it.

That is also why most of the API source does not apply, and Part 5 says exactly which parts to stop reading.

---

## Part 1 — How the window actually fills

Five mechanisms from the API documentation, each of which overturns something people assume.

**Everything counts, including the output.** "Everything in the request counts toward the context window: the system prompt, every message in `messages` (including tool results, images, and documents), and your tool definitions. The output Claude generates for the turn, including its extended thinking, counts too." Conversation is progressive — each turn carries the entire history forward and reprices it. A turn at 150k input costs five times a turn at 30k for the same question.

**Caching does not save space.** This is the misconception worth killing first, because it is the one that sends people down a useless path. "Cached prompt prefixes still occupy the context window: prompt caching changes what you pay for those tokens, not whether they count." Caching is a cost and latency lever. It does nothing for window occupancy, and in the extension you do not control it anyway — Claude Code places the breakpoints. Anything you read about `cache_control`, TTLs, or the 20-block lookback is not a context lever for you. Skip it.

**Thinking is kept, and re-billed as input.** On Opus 4.5 and later, and Sonnet 4.6 and later, "the API keeps previous thinking blocks by default, and they count toward the context window like any other input tokens." Billing follows: thinking tokens are charged as output when generated, and then "the kept blocks are then part of later requests' input and are billed as input tokens." Older models stripped them; current ones do not. If you run `CLAUDE_CODE_EFFORT_LEVEL: max`, that is deep reasoning on every turn, accumulating in the history, re-sent and re-billed on every turn after. Max effort is not a flat per-turn cost. It compounds.

**Your model cannot see its own fuel gauge.** Some models get a token budget injected into every request — a `<budget:token_budget>` tag in the system prompt, and after each tool call a `<system_warning>Token usage: 35000/200000; 165000 remaining</system_warning>`. The documentation is specific about who: "Claude Sonnet 5, Claude Sonnet 4.6, Claude Sonnet 4.5, and Claude Haiku 4.5 have context awareness." And then: "Newer models don't receive these injected tags. On Claude Opus 4.7 and later…" So if you are pinned to Opus 4.7 or later, Claude is *not* tracking its remaining budget in your sessions, and will not warn you as it fills. If you have been waiting for it to say something, it never will. Check which model you are on, and if it is one of the newer ones, instrument it yourself.

**The same text costs about 30% more than it used to.** "Claude Opus 4.7 and later Opus models, Claude Fable 5, Claude Mythos 5, Claude Mythos Preview, and Claude Sonnet 5 use a newer tokenizer. The same input text produces approximately 30% more tokens than on earlier models." A file that comfortably fit last year does not necessarily fit now, and a 1M window is not as much headroom as the number suggests. If your context numbers jumped after a model upgrade, suspect the tokenizer before you suspect yourself.

**What happens at the wall.** If the input alone exceeds the window, the API returns a 400, `prompt is too long`. On 4.5-and-later models, if input plus the output ceiling would exceed the window, the request is accepted and generation simply stops with `model_context_window_exceeded`. In the extension you rarely hit either, because auto-compaction fires first — which is the problem, since it fires when the model is already degraded.

---

## Part 2 — The levers you actually have

Ordered by how much space they typically buy.

### Measure first: `/context`

Your substitute for the API's `count_tokens`. It breaks usage down by category — system prompt, tools, MCP, memory, skills, messages — with optimization hints; `/context all` expands everything. `/memory` shows which instruction files loaded. Run it *before* a large task, not after the window is full.

The VS Code context indicator only surfaces prominently near about 80%, by which point your options have narrowed to compacting a degraded session. Do not rely on it. The rule from the API side transfers cleanly: measure before you optimize, and do not trust intuition.

### Keep material out: subagents

A subagent runs in its own context window and returns only its final message to the parent. Everything it reads — the greps, the file contents, the logs — stays in its window and never touches yours. This is the single most effective lever available, because it is the only one that prevents tokens rather than reclaiming them.

Concretely: this guide was written after reading a 650 KB source file that never entered the main session, because a Sonnet subagent read it and returned a brief.

Three things to get right.

*Route the model.* A subagent inherits the main conversation's model unless told otherwise, so if you are pinned to Opus, your file-discovery worker is running on Opus. Set `model:` in the subagent's frontmatter (`haiku`, `sonnet`, `opus`, or `inherit`), or set `CLAUDE_CODE_SUBAGENT_MODEL` globally. Haiku for discovery, search, extraction, and reformatting; Sonnet for implementation; Opus only when the subagent must genuinely reason.

*Override `Explore`.* The built-in `Explore` agent now inherits your main model rather than always running on Haiku. To force it back, define a project subagent literally named `Explore` with `model: haiku`.

*Ask for extractive returns.* Tell a research subagent to return the specific findings relevant to your task, not to summarize everything it saw. When several subagents each return a long report, those reports accumulate in *your* window and you have moved the problem rather than solved it. Terse and extractive beats thorough and abstractive.

### `/clear` between unrelated tasks

The cheapest reset, and the most underused. One conversation per intent. If you have corrected Claude more than twice on the same point, the context is now polluted with the wrong turns — clear it and restart with a better first message rather than arguing with the residue. `CLAUDE.md` and memory reload automatically afterwards, so you lose less than you think.

### `/compact` early, and with a focus

Auto-compaction fires around 83% of the window, which is to say it fires after quality has already dropped. Compact deliberately at a task boundary instead, and steer it: `/compact focus on the memory-file edits, ignore the source-reading` keeps what matters instead of producing a generic précis.

Know what compaction actually is: it summarizes older content and replaces it. The API documentation is candid about where that goes wrong, and lists as poor fits "tasks requiring precise recall of early conversation details" and "tasks that need to maintain exact state across many variables." The default summary keeps five things — the task, the current state, discoveries, next steps, and context to preserve. Assume anything outside those five buckets is gone.

The consequence is a habit, not a setting: **write the plan, the decisions, and the file paths to disk before a long task**, so compaction cannot lose them. A memory file that the session-start protocol reads back is exactly this mechanism. After a compaction, ask Claude to restate the goal, the files changed, and what remains.

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

Tool search (deferred loading) is on by default: only tool names load at startup, and full definitions load on demand. That is why a handful of connectors can stay cheap despite exposing dozens of tools. Control it with `ENABLE_TOOL_SEARCH` — unset defers everything (the default), `auto` loads upfront only if the tools fit within 10% of the window, `false` restores the old load-everything behaviour.

**Check whether this is your lever before you spend time on it.** Run `/context` and read the system-tools line. In one measured session with six connectors and sixty-odd exposed tools, deferred loading held *all* system tools — built-ins included — to 15.8k, a rounding error next to the conversation. Loaded eagerly those schemas alone would run many times that. The research report's own threshold check says that if MCP is small and messages are the bulk, the problem is session length rather than MCP. On any setup where deferred loading is working, that check resolves against MCP hygiene, and you can skip the section.

Keep the rest for the day it stops being true: run `/mcp` to see servers and toggle them. Note that account-level connectors are not reachable from project settings — if you have no project `.mcp.json`, `disabledMcpjsonServers` will not touch them. Where a CLI exists, prefer it: `gh` adds no per-tool listing cost, a GitHub MCP server does.

### The always-loaded tier — and what only looks like it

`CLAUDE.md` is the always-loaded tier, and it is the whole of it. It is injected on every request and it can never be compacted away. Run `/context` to see what yours costs — in one measured session a 158-line file came in at **8.9k tokens**, which is a useful sanity check on the usual advice: keep it under about 200 lines, and ask of each line whether removing it would cause a mistake.

The trap is assuming the rest of a session-start protocol lives in the same tier. It does not. `/context` lists exactly one memory file. Any other file your protocol names — a memory file, a personal-context file, a style guide — is not auto-injected; the protocol has Claude *read* it, so it arrives as a tool result and lives in **Messages**. That difference is not cosmetic. Messages can be compacted, summarized, and cleared; `CLAUDE.md` cannot. So the protocol reads are recoverable mid-session, and the always-loaded floor is not.

It also means a long-lived memory file is bigger than it looks and cheaper to fix than it looks. It grows every session, it is usually mostly historical activity log, and it is read in full every time. It is the first thing to prune, and pruning it does not touch the permanent floor.

Push detail down a tier wherever you can. Skill descriptions load at startup; skill *bodies* load only when invoked. A long procedure in a skill costs one line until the moment it fires.

### Effort and thinking

Thinking counts toward the window, and on current models it stays there (Part 1). `CLAUDE_CODE_EFFORT_LEVEL` can be set in `.claude/settings.json`; check yours. If it is running at `max`, then for routine mechanical work — reformatting, extraction, a spelling sweep — you are paying for reasoning you do not need, on every turn, forever. `MAX_THINKING_TOKENS` caps generation; per-skill and per-subagent `effort` frontmatter is the honest way to make a cheap task cheap.

One correction to the research report: it recommends lowering `/effort` as a slash command. There is no `/effort` slash command — the companion prompting guide verified its absence on 2026-07-12. Effort is set through the environment variable or through skill and subagent frontmatter, and nowhere else.

### The 1M window is a valve, not a fix

If you are already on a 1M-context model such as `opus[1m]`, this one is spent. Worth stating anyway: a bigger window delays compaction, it does not improve a noisy context. A million tokens of unclear conversation is still unclear, and thanks to the tokenizer change it is fewer effective tokens than it sounds. `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` caps back to 200K if you ever want the smaller, cheaper window.

---

## Part 3 — Measure your own

Do not estimate this, and do not trust intuition about it. The worked example below exists because a careful estimate turned out to be wrong in two directions at once. Run `/context` on a real working session rather than a fresh one, and read the category table it prints.

### What a measurement looks like

These numbers are from one real session — a documentation-writing session on a 1M-context Opus model. **They are not yours.** They are here to show the shape of the answer and what to conclude from it. **168.9k of 1M used (17%), 830.5k free.**

| Category | Tokens | Share of what was used |
|---|---|---|
| Messages | 137.5k | **81%** |
| System tools | 15.8k | 9% |
| Memory files (`CLAUDE.md` only) | 8.9k | 5% |
| System prompt | 4.4k | 3% |
| Skills | 3.0k | 2% |

Three things fell out of it, and two contradict what most people would guess before running the command.

**The conversation is usually the entire problem.** Messages were 81% of everything used. Every other category combined was a fixed floor of roughly 32k, paid before typing a word — small and boring. When your own table looks like this, the only levers worth pulling are the ones acting on Messages: `/clear`, subagent delegation, `/compact`, narrower reads, and effort. MCP hygiene and `CLAUDE.md` pruning are rounding errors at that scale — real advice in general, noise in this situation. Find out which case you are in before optimizing.

**Window size decides which advice applies to you.** 168.9k is a comfortable 17% of a 1M window. On a 200K model the identical session would sit at 84% — past the auto-compaction trigger, well into degradation. Most published thresholds (the research report's ~147–152K danger zone, for one) were written for a 200K window. Check your own window before adopting someone else's numbers.

**Only `CLAUDE.md` is always-loaded.** This is the structural point worth internalizing, and the one the first draft of this guide got wrong. `/context` lists exactly one memory file. Every other file a session-start protocol pulls in is read, not injected, so it lives in Messages and is compactable — while `CLAUDE.md` is re-sent on every request and never can be.

### Cost your own session-start protocol

If your `CLAUDE.md` tells Claude to read a set of files before answering, those reads are not free, and they are usually the largest saving available. Cost them:

1. `wc -c` every file the protocol names.
2. Calibrate a chars-per-token ratio: divide your `CLAUDE.md`'s character count by the token figure `/context` reports for it. In the measured example this came to about **2.75 characters per token** — not the folk-wisdom 4:1, which understates these files by roughly 45%. That gap is the tokenizer inflation from Part 1 showing up in practice.
3. Divide each file's characters by your ratio.

### The fix you are most likely to find

In the example workspace, that arithmetic surfaced one dominant line item: a memory file of 102,735 characters (~37.4k tokens), almost all of it an append-only activity log reaching back months, read in full every single session. The protocol cost ~63k before the first message was typed.

The fix was not a settings change or a smarter command. The log's tail — everything older than about six weeks, twelve of twenty-one dated entries — moved into a separate archive file that the session-start protocol does not read. Nothing was deleted; the history is one file-open away. The protocol dropped to ~44k, and the saving recurs every session.

That is the pattern to look for first: **a file being read in full every session that has quietly become mostly history.** Move the history somewhere the protocol does not look. Reach for that before you reach for a flag.

One honest wrinkle, because it shows how this bloat survives: no single session had actually paid the full 63k. The session that produced the measurement grepped the memory file rather than reading it, so the ~37k never landed — this guide's own advice working by accident. The cost was real but latent, which is exactly why nobody had noticed it.

### Settings worth checking

Run `/context` and `/doctor`, then look at each of these:

| Setting | What to check | Why it matters |
|---|---|---|
| `model` | Which model, and how big the window | Opus 4.7+ receives **no context-awareness tags** — Claude will not warn you as it fills. Instrument with `/context` yourself. |
| `CLAUDE_CODE_EFFORT_LEVEL` | Whether it is pinned high | Thinking blocks are kept on Opus 4.5+ and re-billed as input every turn. They accumulate in Messages — usually the dominant bucket. |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Whether it is set at all | Unset means subagents inherit your main model, including the built-in `Explore`. Often the cheapest unclaimed fix. |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | Whether it is exported **in your shell profile** | Moves compaction earlier than the ~83% default, so it fires before quality degrades. A known bug makes the `settings.json` `env` block silently ignore it. |
| `ENABLE_TOOL_SEARCH` | Unset is correct | Unset means deferred loading. Confirm via `/context` that system tools are small. |
| Project `.mcp.json` | Whether one exists | Account-level connectors are not reachable from project settings; toggle them via `/mcp`. |

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

1. Claude will not tell you when the window is filling. On Opus 4.7+ it cannot see its own budget. Run `/context` yourself, before big tasks.
2. **Measure before you optimize.** In the worked example the conversation was 81% of context and everything else a ~32k floor. If your own `/context` looks like that, act on Messages and ignore MCP hygiene.
3. Delegate every heavy read to a subagent — it is the only lever that prevents tokens rather than reclaiming them.
4. `/clear` between unrelated tasks. One conversation per intent.
5. `/compact` at a task boundary with an explicit focus, not at 95% under duress.
6. Write plans and decisions to disk before long tasks. Compaction is lossy in a documented, predictable way.
7. Read line ranges, not files. Grep before you read.
8. Max effort compounds, because thinking blocks stay in the history — inside the 81% bucket. Spend it where it earns.
9. Caching does not save context space. Stop looking for savings there.
10. Set `CLAUDE_CODE_SUBAGENT_MODEL` so subagents stop inheriting Opus. Still unset.
11. Check whether a memory file read every session has become mostly historical log. Archive the tail out of the protocol's reach. It is usually the biggest prunable item there is.
12. If you are compacting more than once per task, the task is too big. A larger window will not save you.

---

## Caveats

- **This surface moves fast.** Several behaviours are version-gated (tool search, `Explore` inheriting the main model, `alwaysLoad`). Check against `/context` and `/doctor` for your installed version rather than trusting this file.
- **Provenance differs by claim.** Everything quoted in Part 1 comes from Anthropic's API documentation and was verified line-by-line on 2026-07-12. The extension-level levers in Part 2 come from a research report that mixes official documentation with community claims; it flags several of its own figures (the ~147–152K danger zone, the 60% compaction rule, the 65% verbosity saving) as heuristics rather than Anthropic promises. Treat them as such.
- **Part 3's numbers are one workspace's, not yours.** The category table is real `/context` output and the per-file figures are `wc` plus a calibration — in that workspace a 24,439-character `CLAUDE.md` measured 8.9k tokens, giving about **2.75 characters per token**. Calibrate your own the same way rather than reusing 2.75, and in either case do not use the folk-wisdom four-characters-per-token: the naive figure understated those files by roughly 45%, which is the tokenizer inflation from Part 1 showing up in practice. Anything derived from a ratio is marked `~`; only `/context` output is measured.
- **A first draft of Part 3 was wrong, and the error is instructive.** It estimated the session-start protocol at "~42,000 tokens before your first message" and put all four files in the always-loaded tier. `/context` showed both halves to be wrong: the real per-file cost is higher (bad ratio), and only `CLAUDE.md` is actually always-loaded. Intuition about context is unreliable in both directions at once. Run the command.

---

## Sources

- Anthropic's API documentation on context management: context windows, compaction (server-side and the deprecated SDK form), context editing, prompt caching, mid-conversation system messages, token counting. Authoritative on mechanism; silent on Claude Code.
- A research report on optimizing the VS Code extension specifically: MCP hygiene, subagent routing, the compaction and clearing commands, CLAUDE.md discipline. The source of most levers in Part 2, and the source of the heuristics flagged above.
- `claude-code-prompting-best-practices.md` — the companion guide. Where a prompt lives; what each layer is for.
