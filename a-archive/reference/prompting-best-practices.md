# Prompting Best Practices for Claude

A practical synthesis of Anthropic's prompt-engineering guidance. The document is organized so that the durable, model-agnostic principles come first (Parts 1–3), followed by guardrail and reliability techniques (Part 4), operational concerns like latency (Part 5), and then the material that is tied to a specific current model and will date fastest (Part 6). The foundational learning path from Anthropic's interactive tutorial is summarized in Part 7, and its reusable structure for building complex prompts from scratch is laid out in Part 8.

---

## Part 1 — Foundational principles

These are the highest-leverage techniques and apply across every Claude model.

**Be clear and direct.** Claude responds well to explicit instructions and lacks the implicit context a colleague would have, so treat it like a capable new hire who knows nothing about your norms or workflows: the more precisely you describe the desired output, the better the result. If you want "above and beyond" behaviour, ask for it rather than hoping the model infers it from a vague prompt. The operational test Anthropic recommends is to show your prompt to a colleague with minimal context and ask them to follow it — if they would be confused, Claude will be too. Be specific about output format and constraints, and when the order or completeness of steps matters, lay them out as numbered or bulleted steps.

**Add context and motivation.** Explaining *why* a behaviour matters helps Claude generalize toward your actual goal rather than pattern-matching the literal instruction. Telling the model the reason behind a formatting rule, for instance, lets it apply the spirit of that rule to cases you did not explicitly enumerate.

**Use examples (few-shot / multishot prompting).** A few well-crafted examples are among the most reliable ways to steer output format, tone, and structure, and they typically improve accuracy and consistency more than abstract description does. The terminology counts examples as "shots" — zero-shot means none, one-shot means one, n-shot means several — and showing Claude a few ideal responses is often easier and more effective than describing the desired tone or format in words. Effective examples are relevant (they mirror your actual use case), diverse (they cover edge cases and vary enough that Claude does not latch onto an unintended pattern), and structured (each wrapped in an `<example>` tag, with the set wrapped in `<examples>`, so the model can tell examples apart from instructions). Three to five examples is a good target, and covering common edge cases matters more than sheer count; if the prompt uses a scratchpad, include an example of how the scratchpad should look. You can also ask Claude to critique your examples for relevance and diversity, or to generate additional ones from a seed set.

**Structure prompts with XML tags.** When a prompt mixes instructions, context, examples, and variable input, wrapping each kind of content in its own descriptive tag (`<instructions>`, `<context>`, `<input>`, and so on) reduces the chance the model conflates them. This matters most with templated prompts where you substitute variable data into a fixed skeleton: without delimiters Claude can misread where the data ends and the instruction begins (for instance, treating a "Yo Claude" greeting as part of an email it was asked to rewrite). XML tags are worth preferring over other separators specifically because Claude was trained to recognize them as an organizing mechanism — though outside of tool calling there are no "magic" tag names that boost performance, so you are free to name them whatever is clearest. Use consistent tag names across your prompts, and nest tags where the content has a natural hierarchy — for example, individual `<document index="n">` elements inside a `<documents>` wrapper.

**Small details matter.** Claude is sensitive to the register of your prompt: typos, grammatical errors, and sloppy structure tend to produce lower-quality, more error-prone output, while clear, correct, well-organized prompts produce better output. It is worth scrubbing prompts for mistakes for the same reason you would proofread instructions to a person.

**Give Claude a role.** Setting a role in the system prompt focuses the model's behaviour and tone for your use case, and even a single sentence ("You are a helpful coding assistant specializing in Python") makes a measurable difference. Role prompting changes style, tone, and manner, but it can also improve performance on substantive tasks — including math and logic — much as telling a person to "think like a ______" can sharpen their approach; the more detail you give the role, the stronger the effect. A useful adjunct is telling Claude who its audience is ("you are a cat talking to a crowd of skateboarders" produces a very different response from "you are a cat"). For role-based or character applications, supply detailed personality, background, and quirks so the model can emulate and generalize the character, and prepare it for likely scenarios so it stays in character across diverse situations.

**Tell Claude what to do, not what to avoid.** Positive instructions outperform negative ones. Rather than "do not use markdown," say "compose your response in smoothly flowing prose paragraphs." Positive examples of the behaviour you want are generally more effective than prohibitions, and matching your own prompt's style to the desired output style (for instance, writing the prompt itself without markdown when you want prose) nudges the response in the same direction.

---

## Part 2 — Controlling output and format

**Specify the output format precisely.** Define the shape you want using JSON, XML, or a custom template so the model understands every formatting element you require. For guaranteed conformance to a strict JSON schema, Anthropic's [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) feature is the right tool rather than prompt engineering alone; the prompt-based techniques here are for general consistency or when you need flexibility beyond a fixed schema.

**Constrain format with examples.** Showing the model a sample of the exact output you want trains its understanding better than describing the format in the abstract — this is the few-shot principle applied specifically to formatting.

**Steer formatting through several complementary levers.** Beyond positive instructions and XML format indicators (for example, "write the prose sections in `<smoothly_flowing_prose_paragraphs>` tags"), you can match prompt style to output style and, for fine control over markdown, give explicit guidance. A detailed instruction block that asks for flowing prose, reserves markdown for inline code and code blocks, and forbids lists except for genuinely discrete items is an effective way to suppress over-formatting.

**LaTeX.** Recent Claude models default to LaTeX for mathematical and technical expressions. If you need plain text, instruct the model explicitly to avoid LaTeX, MathJax, and markup notation and to write math with standard characters.

**Verbosity.** Newer models calibrate length to perceived task complexity rather than a fixed default, so they may skip verbal summaries after tool calls and jump to the next action. If you want more visibility into the model's reasoning, ask for a short summary after tool use; if you want less, request concise, focused responses and skip non-essential context. Positive examples of appropriately concise output tend to work better than instructions about what not to do.

**Retrieval for contextual consistency.** For chatbots and knowledge-base applications, grounding responses in a fixed, retrieved information set keeps outputs consistent across calls.

**Prompt chaining for complex tasks.** Breaking a large task into smaller, sequential subtasks — each its own API call — gives the model full attention on each piece and reduces inconsistency at scale. The most common useful pattern is *self-correction*: generate a draft, have the model review it against explicit criteria, then have it refine based on the review. Asking Claude to double-check or improve its own work reliably catches errors, and notably it tends to hold firm when its original answer was already correct rather than second-guessing into a worse one. Chaining also underlies a simple form of tool use: take the result of one call (say, a list of names Claude extracted) and substitute it into a follow-up prompt (alphabetize that list). Separate calls let you log, evaluate, or branch at each step. With modern models' internal reasoning, explicit chaining is now most valuable when you specifically need to inspect intermediate outputs or enforce a fixed pipeline structure.

---

## Part 3 — Reasoning, long context, and agentic work

**Encourage step-by-step reasoning.** Asking Claude to reason through a problem before answering ("precognition," or chain-of-thought) surfaces faulty logic and assumptions and improves results on anything involving multi-step inference. The crucial constraint is that thinking only counts when it happens out loud: you cannot ask Claude to think silently and emit only the answer, because in that case no reasoning has actually occurred — the reasoning has to appear in the output (optionally in a dedicated tag you later strip). When you want clean separation between reasoning and final answer, use structured tags such as `<thinking>` and `<answer>`. General instructions ("think thoroughly") often produce better reasoning than a hand-written step-by-step plan, because the model's own reasoning frequently exceeds what a human would prescribe. Multishot examples that include `<thinking>` blocks teach the model the reasoning *pattern* you want it to generalize. A reliable add-on is a self-check: ask the model to verify its answer against stated criteria before finishing, which catches errors well in coding and math. One wording caveat: when thinking is disabled, some models are sensitive to the literal word "think," so alternatives like "consider," "evaluate," or "reason through" can work better.

**Watch for ordering effects.** On genuinely difficult or borderline judgements, Claude can be sensitive to the order in which options are presented and is somewhat more likely to choose the second of two options — possibly an artifact of its training data, where second options were marginally more often correct. When you ask it to weigh alternatives, be aware that swapping their order can flip the verdict; for sentiment or classification tasks, having Claude lay out the arguments for each side before committing reduces this fragility.

**Long-context prompting (20k+ tokens).** Place long documents and data near the *top* of the prompt, above your query, instructions, and examples — in testing this can improve response quality by up to roughly 30%, especially with complex multi-document inputs. Wrap each document in its own tag with `<document_content>` and `<source>` (plus any other metadata) subtags. For long-document tasks, asking the model to first extract relevant verbatim quotes, then carry out its task, helps it cut through surrounding noise.

**Long-horizon reasoning and state tracking.** For tasks that span extended sessions or multiple context windows, emphasize incremental progress — steady advances on a few things at a time rather than attempting everything at once. Use structured formats (JSON) for state data like test results, freeform text for progress notes, and git for checkpoints and history. When working across context windows, a productive pattern is: use the first window to set up scaffolding (write tests, create setup scripts), then iterate against a todo list in later windows; have the model keep tests in a structured file and treat them as immutable; create quality-of-life scripts (an `init.sh` to start servers and run suites) so a fresh context window does not repeat setup; and provide verification tools so the model can confirm correctness without continuous human feedback.

**Research and information gathering.** Provide clear success criteria for what counts as a good answer, encourage verification across multiple sources, and for complex research ask the model to develop competing hypotheses, track confidence levels in its notes, self-critique its approach, and persist findings to a hypothesis tree or notes file. This structured approach lets it iteratively synthesize and critique findings across a large corpus.

**Tool use.** Be explicit when you want action rather than suggestion — "can you suggest some changes" will sometimes yield suggestions when you wanted edits, so say so directly. You can set a default posture (act-by-default versus research-and-recommend-by-default) in the system prompt. When tool calls are independent, instructing the model to issue them in parallel improves speed; when calls depend on one another's outputs, they must run sequentially, and the model should never guess missing parameters.

**Subagent orchestration.** Modern models recognize when work benefits from delegation and will spawn subagents without explicit instruction. Ensure subagent tools are well-defined, let the model orchestrate naturally, and watch for overuse — if it spawns subagents where a direct call would be faster and simpler, give explicit guidance on when delegation is and is not warranted (parallelizable work, isolated context, and independent workstreams favour subagents; simple sequential or single-file work does not).

---

## Part 4 — Guardrails and reliability

### Reducing hallucinations

No technique eliminates hallucination entirely, so always validate critical information for high-stakes decisions; the following significantly reduce the rate.

Give Claude explicit permission to say "I don't know" — often phrased as "giving Claude an out," for example "only answer if you know the answer with certainty." This alone sharply reduces fabricated answers, because by default Claude tends to supply a plausible-sounding response rather than admit ignorance. For long documents (over ~20k tokens), have the model extract word-for-word quotes relevant to the task *before* answering, grounding its response in the actual text; this is especially effective against "distractor" passages that are nearly but not quite relevant, where a quote-first scratchpad lets the model notice that the available evidence does not actually answer the question. Make outputs auditable by requiring a citation or supporting quote for each claim, and have the model retract any claim for which it cannot find support. More advanced layers include chain-of-thought verification (explain the reasoning step-by-step to expose faulty assumptions), best-of-N checking (run the same prompt several times and treat cross-run inconsistencies as a hallucination signal), iterative refinement (feed outputs back in and ask the model to verify or expand), and external-knowledge restriction (instruct the model to use only the provided documents and not its general knowledge). Lowering the sampling temperature toward 0 also yields more consistent, less speculative answers, which can help where hallucination stems from over-creative variability.

### Increasing output consistency

Beyond the format-specification and example-based techniques in Part 2, consistency benefits from grounding via retrieval, from chaining complex tasks into focused subtasks, and — for role-based applications — from deliberate character maintenance: define the role and personality in the system prompt and prepare the model with common scenarios and expected responses so it does not break character. For strict JSON schema conformance, use Structured Outputs rather than prompting.

### Mitigating jailbreaks and prompt injection

Claude is inherently resilient to these attacks, but layered defences strengthen the guardrails. Use a lightweight model such as Claude Haiku 4.5 as a harmlessness screen on user input, constrained via structured outputs to a simple classification. Validate input against known jailbreak patterns (an LLM can generalize a validation screen from example attack language). Use system prompts that emphasize ethical and legal boundaries. Monitor outputs continuously for signs of circumvention, and consider warning, throttling, or banning users who repeatedly trip the same refusals. For high-stakes applications, chain these safeguards together rather than relying on any single layer.

### Reducing prompt leak

Treat leak-resistant prompting as a last resort: the added complexity can degrade performance elsewhere in the task, so try monitoring approaches first — output screening, post-processing with regular expressions or keyword filters, or a prompted LLM that filters for subtler leaks. When you do harden against leaks, separate context from queries (isolate sensitive information in the system prompt), omit any proprietary detail the model does not actually need for the task (extra content both raises leak risk and distracts from the "no leak" instruction), and audit prompts and outputs periodically. Balance matters — overly aggressive leak prevention degrades results.

---

## Part 5 — Latency

Engineer a prompt that performs well *first*, then optimize latency; premature latency tuning can hide what top performance looks like. The three main levers are model choice, token economy, and streaming. Choose the lightest model that meets your quality bar — Claude Haiku 4.5 offers the fastest responses while retaining high intelligence for speed-critical work. Minimize tokens in both prompt and output while keeping instructions clear enough that the model does not have to guess; ask directly for shorter responses, noting that because models count tokens rather than words, sentence- or paragraph-count limits steer length more reliably than word counts. Set `max_tokens` as a hard ceiling, understanding it is a blunt cut that can truncate mid-sentence and is best suited to short-answer or multiple-choice outputs. Lower `temperature` values sometimes yield more focused, shorter responses. Finally, enable streaming: it does not reduce total generation time but greatly improves *perceived* responsiveness by showing output as it arrives, which matters most for time-to-first-token in interactive applications.

---

## Part 6 — Model-specific tuning (Claude Opus 4.8)

> This section is tied to a specific current model and will date faster than the principles above. Verify against the live documentation before relying on any detail here, and re-evaluate prompts whenever you upgrade models.

Claude Opus 4.8 performs well out of the box on existing Opus 4.7 prompts; the items below are the behaviours that most often need tuning.

**The `effort` parameter is the primary control** for trading intelligence against token spend, speed, and cost. Anthropic recommends starting at `xhigh` for coding and agentic work and using at least `high` for most intelligence-sensitive cases; `medium` suits cost-sensitive work, and `low` is reserved for short, scoped, latency-sensitive tasks. The model respects effort strictly at the low end, scoping its work narrowly — good for cost, but at `low`/`medium` on moderately complex tasks there is some risk of under-thinking. The first lever for shallow reasoning is to raise effort rather than prompt around it. At `max` or `xhigh`, set a large `max_tokens` budget (start around 64k) so the model has room to think and act across tool calls and subagents.

**Thinking is off by default** and is enabled with `thinking: {type: "adaptive"}`, where the model decides when and how much to think based on effort and query complexity. Adaptive thinking reliably outperforms the older extended-thinking-with-`budget_tokens` approach in internal evaluations and is preferred for agentic, multi-step, and long-horizon workloads. If the model thinks more often than you want (common with large system prompts), steer it with a prompt noting that thinking adds latency and should be reserved for problems needing multi-step reasoning. To migrate from extended thinking, replace the `thinking` config with adaptive and move budget control to `effort`; `budget_tokens` still functions on Opus 4.6 and Sonnet 4.6 but is deprecated.

**Literal instruction following.** Opus 4.8 interprets prompts literally and explicitly, especially at lower effort, and does not silently generalize an instruction from one item to another. This yields precision for structured extraction and pipelines, but means you must state scope explicitly when you want broad application ("apply this to every section, not just the first").

**Tool use and subagents.** The model tends to favour reasoning over tool calls and spawns fewer subagents by default; raising effort increases tool usage, and explicit guidance steers subagent spawning in either direction. Older heavy-handed anti-laziness prompting ("CRITICAL: you MUST use this tool…") can now cause *over*triggering and should be dialled back to normal phrasing ("use this tool when…").

**Verbosity, tone, and updates.** The model calibrates length to task complexity, provides regular high-quality progress updates during long agentic traces (so scaffolding that forced interim summaries can often be removed), and tends toward a direct, opinionated style with sparing emoji. Re-evaluate any voice-specific style prompts against this baseline; for a warmer voice, ask for it explicitly.

**Frontend and design defaults.** Opus 4.8 has strong design instincts but a persistent house style (warm cream backgrounds, serif display type, terracotta accents) that suits editorial and hospitality briefs and feels wrong for dashboards or enterprise apps. Generic negative instructions ("don't use cream") tend to shift it to another fixed palette rather than producing variety; two approaches that work are specifying a concrete alternative palette and typography precisely, or asking the model to propose several distinct directions before building and letting the user choose. A short `<frontend_aesthetics>` snippet that forbids generic fonts and clichéd colour schemes helps avoid the "AI slop" aesthetic.

**Other notable behaviours.** Opus 4.8 is meaningfully better at finding bugs, but code-review harnesses tuned to suppress low-severity findings may show *lower* measured recall because the model now follows "only report high-severity" instructions faithfully — prompt for coverage at the finding stage and filter for severity downstream. The model may overengineer (extra files, unnecessary abstractions, speculative error handling); explicit "keep it minimal, only what was asked" guidance counteracts this. It may create temporary scratchpad files during agentic coding, which can be cleaned up with an explicit instruction. To minimize hallucination in coding, instruct it never to make claims about code it has not opened and to read referenced files before answering.

**Interactive vs. autonomous coding.** The model spends more tokens in interactive, multi-turn coding sessions than in single-turn autonomous ones, because it reasons more after each user turn; this improves long-horizon coherence but costs tokens. To get both performance and efficiency, run at `high`/`xhigh` effort, add autonomous features such as an auto mode, and reduce the number of required human turns — which in turn means specifying the task, intent, and constraints fully in the first turn rather than dribbling them out across many.

**Vision.** Recent models handle image extraction and multi-image contexts well, and these gains carry into computer use. A technique with consistent measured uplift is giving the model a crop tool or skill so it can "zoom" into the relevant region of an image; videos can be analyzed by splitting them into frames.

**Prefill is no longer supported.** Starting with the 4.6 generation, prefilled responses on the final assistant turn return a 400 error on Opus 4.8, Opus 4.7, Opus 4.6, and Sonnet 4.6. Use system-prompt instructions or Structured Outputs to achieve what prefill used to — controlling format, eliminating preambles, and enforcing structure.

**Model self-knowledge.** If your application needs Claude to identify itself or emit a specific API model string, state it in the system prompt (for example, that the current model is Claude Opus 4.8 with model string `claude-opus-4-8`); the model does not reliably know its own deployment identity otherwise.

---

## Part 7 — The interactive tutorial: a learning path

Anthropic's [interactive prompt-engineering tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial) (also distributed as a [Claude for Sheets workbook](https://docs.google.com/spreadsheets/d/19jzLgRruG9kjUQNKtCg1ZjdD6l6weA6qRXG5zLIAhC8/edit), which runs on Claude 3 Haiku at temperature 0 for faster, more deterministic results) teaches the foundations above as a hands-on progression. Its structure is a useful checklist of core skills, ordered from basic to advanced:

1. Basic prompt structure
2. Being clear and direct
3. Assigning roles (role prompting)
4. Separating data from instructions
5. Formatting output and "speaking for Claude"
6. Precognition (thinking step by step)
7. Using examples (few-shot prompting)
8. Avoiding hallucinations
9. Building complex prompts from scratch (chatbot, legal, financial, and coding use cases)

An appendix covers chaining prompts, tool use / function calling, and search and retrieval. The progression maps cleanly onto this document: chapters 1–3 and 7 are Part 1's foundations, chapter 4 is the XML-structuring and data-separation practice, chapters 5–6 are Parts 2 and 3 (chapter 5 also covers "speaking for Claude," the older prefill technique — see the note in Part 6 on its removal in current models), chapter 8 is the hallucination guardrail in Part 4, and chapter 9 and the appendix are the complex-prompt assembly and chaining material covered in Parts 3 and 8.

---

## Part 8 — Assembling a complex prompt: the ten-element structure

The tutorial's capstone is a reusable skeleton for complex prompts, such as a roleplay chatbot, a document-analysis tool, or a coding assistant. Not every prompt needs every element, and the usual workflow is to include many elements to get the prompt working, then trim. Ordering is fixed for some elements and flexible for others, as noted. The elements, in their default order:

1. **Task context.** Give Claude the role and the overarching goal up front ("You are an AI career coach named Joe…"). Context belongs early in the prompt.
2. **Tone context.** If tone matters, state it ("maintain a friendly customer-service tone"). Optional.
3. **Background data and documents.** Any material Claude must process, each wrapped in its own XML tags. When this data is long, place it *before* the instructions (consistent with the long-context guidance in Part 3).
4. **Detailed task description and rules.** The specific tasks and any rules to follow, including the "out" for cases where Claude lacks an answer ("if you are unsure, say…"). Show this section to a colleague to check that it is unambiguous.
5. **Examples.** At least one example of an ideal response, each in `<example>` tags; if you give several, label what each illustrates and cover edge cases. This is described as the single most effective lever in knowledge-work prompts.
6. **Conversation history.** Prior user/assistant turns if relevant, in tags such as `<history>`, so the model has continuity. Ordering is flexible.
7. **Immediate task description or request.** Restate exactly what Claude should do right now, and place the user's actual question here. Reiterating the immediate task near the *end* of a long prompt works better than stating it only at the top, and the user's query is best kept close to the bottom.
8. **Precognition (think step by step).** For multi-step tasks, instruct Claude to reason before answering (sometimes literally "before you give your answer…"). Best placed near the end, right after the immediate task. It raises answer quality at the cost of latency from the longer output.
9. **Output formatting.** Specify the exact desired format if it matters (for example, "put your response in `<response>` tags"). Optional; better placed toward the end.
10. **Prefill.** Historically, a few words placed after "Assistant:" to steer the start of the response. Note that prefill is not supported on current models (Part 6), so on those models fold this intent into instructions or Structured Outputs instead.

Two framings from the worked examples are worth carrying over: prompt structure is flexible — the legal and financial examples deliberately reorder elements (for instance, putting long input data earlier) to suit the task — and prompt engineering is iterative trial and error, so the right move is to develop test cases and try several structures rather than expecting one formula to be optimal.

---

## Sources

- Anthropic, "Prompting best practices," Claude API documentation. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic, "Reduce hallucinations." https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- Anthropic, "Increase output consistency." https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/increase-consistency
- Anthropic, "Reduce prompt leak." https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-prompt-leak
- Anthropic, "Mitigate jailbreaks and prompt injections." https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks
- Anthropic, "Reducing latency." https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-latency
- Anthropic, "Prompt Engineering Interactive Tutorial" (GitHub). https://github.com/anthropics/prompt-eng-interactive-tutorial
- Anthropic, "Prompt Engineering Interactive Tutorial" (Claude for Sheets workbook, running `claude-3-haiku-20240307` at temperature 0; Parts 7–8 draw on its lesson text and the Chapter 9 complex-prompt structure). https://docs.google.com/spreadsheets/d/19jzLgRruG9kjUQNKtCg1ZjdD6l6weA6qRXG5zLIAhC8/edit
