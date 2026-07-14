# llm-wiki

A personal knowledge base that an AI agent builds and maintains for you, following a fixed set of rules. Built for academic research, but the rules are general.

The design blends two ideas. From Andrej Karpathy's LLM knowledge base sketch it takes a three-part split: your original sources stay untouched, the agent writes and maintains a wiki of notes about them, and a rulebook tells the agent how to behave. From Sönke Ahrens' smart-note method it takes the note-writing discipline: each note captures one reusable idea, stays tied to its source, and links to related notes. It is packaged as a set of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) commands ("skills") that read, write, and check a local [Obsidian](https://obsidian.md) vault — a plain folder of markdown files.

## What this is

The repo is three layers:

- **Raw sources** in `0-raw/` — immutable PDFs, articles, transcripts, and other captured material. The agent never edits these.
- **A wiki** in `1-wiki/` — the notes the agent writes and maintains. *Source pages* summarize one source and point to exactly where each claim came from. *Concept* and *entity* pages each explain one reusable idea in plain language. *Synthesis* pages tie several sources together and act as starting points into a topic.
- **Skills** in `.claude/skills/` — a small set of Claude Code commands that do the work: ingest a source, answer a question, check the wiki's health, replace a page, and so on.

The full rulebook lives in [CLAUDE.md](CLAUDE.md). Every skill follows it; anywhere a skill and the rulebook disagree, the rulebook wins.

## Layout

```text
llm-wiki/
├── CLAUDE.md                  # the rulebook: structure, workflow rules, behavioural defaults
├── MEMORY.md                  # long-term notes that stay true across machines and sessions
├── 0-raw/                     # your original sources, never edited (papers, articles, media)
├── 1-wiki/
│   ├── sources/               # one page per raw source, with evidence pointers
│   ├── concepts/              # one reusable idea per page, simple language
│   ├── entities/              # one named thing per page (people, models, datasets)
│   ├── syntheses/             # cross-source argument pages, topic entry points
│   ├── attachments/           # figures and images extracted from sources
│   ├── hot.md                 # short "what's going on right now" cache
│   ├── index.md               # full catalog of every page
│   └── log.md                 # log of every operation, newest first
├── 2-outputs/                     # dated working files (answers, briefs, check reports)
├── a-archive/
│   ├── about-me/
│   │   └── about-me.md            # high-level professional identity (only personal-info location)
│   ├── palettes/            # colour palettes (user assets)
│   ├── reference/            # best-practices digests and design-rationale docs
│   └── style/
│       ├── ai-writing-tells.md    # patterns to avoid in any output
│       └── coding-best-practices.md  # design principles + Python style for any code Claude writes
├── docs/
│   └── examples/                 # rendered sample pages and answers (see "Examples" below)
└── .claude/skills/                # operation skills
    ├── multi-skill/              # cross-skill shared materials
    │   ├── multi-skill-memory.md  # cross-skill corrections, read by every write skill
    │   └── references/            # shared mechanics cited by forget/supersede/ingest
    └── <skill>/                   # one folder per skill, each with its own <skill>-memory.md
```

At the start of each session the agent reads a fixed set of files in order: the rulebook first, then (when relevant) your profile and writing-style rules, then its long-term memory, then the wiki's two orientation files (`hot.md` and `index.md`). Each skill also reads its own short memory file plus one shared across all skills. The exact order is in `CLAUDE.md` → "Workflow Rules".

The number/letter prefixes on the folders (`0-`, `1-`, `2-`, `a-`) just keep Obsidian's file list sorted in the order you work in.

## Quick start

Requirements:

- [Obsidian](https://obsidian.md) for browsing the vault.
- [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) for running the skills.

Steps:

1. Clone the repo and open the folder as an Obsidian vault.
2. Drop a paper or article into `0-raw/papers/` or `0-raw/articles/`.
3. From Claude Code in the repo root, run `/ingest <filename>`. The skill drafts a page summarizing the source, proposes short pages for the ideas it found, and asks your approval before writing anything. If you've ingested that source before, it updates the existing page instead of making a duplicate. Ask for "deep" mode when you want exhaustive, paper-grade detail on an important source.
4. That's your first pages written. The everyday loop is in **Start here**, just below.

## Start here

You can get the whole point of this system with two skills:

- **`/ingest <file>`** — add a source. Drop a paper or article into `0-raw/`, ingest it, and the agent drafts the notes (asking before it writes). This is how knowledge gets *in*.
- **`/checkup`** — keep it healthy. Run it now and then; it checks and tidies the whole wiki for you, bundling the maintenance skills so you don't have to remember them.

And one more, to actually use what you've built:

- **`/query <question>`** — ask the wiki a question and get an answer with its sources.

That's the daily loop: **ingest** sources, **query** them, run a **checkup** once in a while. Everything else is icing — finer control you can pick up whenever you want it.

## Skills

Run each from Claude Code as `/<name>`. They're listed in the order an end user typically reaches for them — the everyday research loop first, then editing and upkeep, then the internals you rarely touch once things are running. Each entry says what it does and when to reach for it.

Day-to-day research:

- **ingest** — Read a paper or article and turn it into wiki pages: one page that summarizes the source and points to its exact evidence, plus short pages for each reusable idea it introduces. It reads the whole source, shows you its plan, and asks before writing anything. Run it again on the same source later to refresh, deepen, or re-angle the notes. *Use it whenever you add a source, or to update one you've ingested before. This is where everything starts.*
- **query** — Ask a research question and get an answer drawn from the wiki, with its sources shown. Every answer is saved so you can find it again. *Use it when you have a specific question the wiki might answer.*
- **brief** — Get a quick lay-of-the-land on a topic — what the wiki knows and where the gaps are — without changing anything. *Use it when you're new to a topic and want the overview before diving in.*
- **compare** — Put 2–4 similar pages side by side to see where they agree, where they differ, and what's missing. *Use it when you have two to four pages and want them lined up.*
- **synthesis** — Build a durable "entry point" page that pulls several sources together to answer a bigger question. These are the pages you start from when exploring a developed topic. *Use it when several sources have piled up around one question (asks before writing).*
- **reflect** — A short "compass" note on where the wiki is heading — blind spots, overloaded notes, and what to read next. *Use it when you want to step back and pick what to do next.*

Correcting and maintaining the wiki:

- **supersede** — Replace a page with a corrected version (or merge, split, or re-extract one), keeping the old version on record. *Use it when a page is wrong or out of date and you want to fix it without losing the old view.*
- **forget** — Remove a page or a link you no longer want, keeping a quarantined copy so nothing is ever truly lost. *Use it when a page or source no longer belongs.*
- **lint** — A fast, automatic check of the wiki's *structure* — missing sections, broken links, miscounted sources, stray formatting — that quietly fixes the safe, mechanical problems. Cheap, so run it often. *Use it right after an ingest, or any time for a quick structural pass.*
- **audit** — A slower, deeper read that judges whether the notes are actually *good*: one clear idea per page, properly supported, honest about disagreements. It re-checks pages against the original sources and either promotes them to "verified" or flags what needs fixing. *Use it before you rely on the wiki for something important, or after a batch of ingests.*
- **checkup** — Run consistency, then lint, then audit back-to-back, hands-off, so the whole wiki gets checked and fixed in one go. The easiest way to keep things healthy. *Use it when you just want everything checked at once and don't want to think about order.*

Internals (rarely needed once you're running):

- **consistency** — Check that the project still agrees with its own rulebook (CLAUDE.md, the skills, the templates) after you change something. It catches drift and *proposes* fixes rather than silently editing the rules. *Use it after you edit the rulebook or a skill (or just run `/checkup`).*
- **cleanup** — Two housekeeping jobs. First, look through the agent's saved notes-to-self and decide which have hardened into permanent rules (and can be cleared) versus which are still live guidance. Second, prune unneeded files from `2-outputs/` — junk, superseded check reports, reports about a deleted source or skill, and old artifacts. Every deletion is confirmed one file at a time. *Use it when the memory files or the outputs folder feel cluttered.*
- **skill-linter** — Review a skill file itself against good skill-writing practices, and tidy it up. *Use it when you're writing or editing a skill.*
- **skill-llm-council** — Put one skill in front of two independent "councils" of five reviewers each — one judging it through general thinking lenses, one through skill-specialist lenses — let them critique it anonymously, then apply the changes they agree on and save the whole debate. The slower, deeper companion to `skill-linter`. *Use it when a quick lint isn't enough and you want a skill stress-tested from many angles.*

Each skill is self-contained in `.claude/skills/<name>/SKILL.md`.

## How the skills fit together

Nothing runs on its own — you invoke each skill yourself with `/<name>`. A few relationships are worth knowing:

- **The everyday loop.** Ingest sources, query them, and run `/checkup` from time to time. That's the whole core cycle; the rest is there when you need finer control.
- **One skill runs the others.** `/checkup` runs `consistency`, then `lint`, then `audit`, in that order, hands-off — so you rarely call those three directly. (`audit` needs a recent clean `lint` and `consistency` first; `checkup` handles that ordering for you.)
- **Write vs. read.** Skills that change the wiki — `ingest`, `supersede`, `forget`, `synthesis` — always show you their plan and ask before writing. Read-only skills — `query`, `brief`, `compare`, `reflect` — never touch the wiki; they save their output under `2-outputs/` for you to keep or discard.

## Examples

This repo ships with an empty wiki — you fill it with your own sources. To show what the pages and answers actually look like once you do, here are a few real exports (Obsidian → PDF) from a working research vault. GitHub previews each inline; the callout colours, inline citations, and extracted figures are what the skills produce.

**Concept and entity pages** — each one reusable idea in plain language, written and maintained by the agent:

- [foundation-model.pdf](docs/examples/foundation-model.pdf) — a **concept page**. One idea, an extracted figure embedded in *Idea*, citations at the point of each non-obvious claim, and a *Disconfirming Evidence* box that names where the idea breaks down.
- [role-prompting.pdf](docs/examples/role-prompting.pdf) — another **concept page**, this one carrying a dozen worked examples pulled from across the source corpus, with a *Disconfirming Evidence* section that cuts against its own central claim.

**Synthesis pages** — durable cross-source argument pages that act as entry points into a topic:

- [are-fm-mas-modelled-on-human-teams.pdf](docs/examples/are-fm-mas-modelled-on-human-teams.pdf) — a **synthesis page**. A yes-and-no answer across six sources, with *Scope* fencing where it applies, *Tensions* preserving the live disagreements, and *What Would Change This Answer* naming the evidence that would overturn it.

**Query answers** — saved under `2-outputs/`, never folded into the wiki without your say-so:

- [query-…-fm-debate-better-answers.pdf](docs/examples/query-2026-06-03-1106-fm-debate-better-answers.pdf) — a **query answer** that separates what the wiki supports from what it doesn't, and flags that the whole case rests on a single source.
- [query-…-why-use-nasa-tlx.pdf](docs/examples/query-2026-06-22-1646-why-use-nasa-tlx.pdf) — a **query answer** built entirely on `draft` pages, marked *[from draft]* throughout and up front that it is unverified until `/audit` runs.

## Design notes

A few choices that may matter if you adapt this for your own use:

- **Claims are cited at the point of use.** A non-obvious claim on a concept, entity, or synthesis page carries an inline citation right there — the source page plus a link to the exact spot in the original (section and page). Obvious or definitional bullets stay uncited, and every page still lists its overall sources once at the bottom, so the small idea-pages stay readable without losing the trail.
- **Source pages separate four kinds of doubt**, each in its own boxed section so they don't blur together: what the source admits it can't do, what it quietly takes for granted, your own judgement of how far to trust it, and where other sources disagree with it. Concept and synthesis pages add a fifth — evidence you went looking for *against* the page's own claim, in the spirit of Darwin's rule to write down what cuts against your theory before you forget it.
- **Synthesis pages say what would change their mind.** Each one names the future evidence that would overturn it — kept separate from present-day pushback and from questions that are simply still open. It forces honest writing.
- **One idea per concept/entity page.** A page that grows a second idea gets split. Soft limit: about 400 words.
- **Empty sections stay empty.** Every page carries the same set of sections even when one has nothing to say — it just shows a short placeholder. A blank placeholder is better than padding the page to fill it.
- **Notes are bullets, not paragraphs.** Each bullet is one fact you can check on its own. The wiki is something you look things up in, not something you read front-to-back, so "scannable" beats "flowing."
- **Jargon is allowed, but defined on first use.** The first time a page uses a technical term, it adds a one-line plain-language gloss and links to the page that explains it fully. Chat answers do the same — define the term, then use it.
- **Tags are for finding things later, not for labelling.** A good tag answers "what future project or thread will make me want this page again?" — not "what is this page about" (that just repeats the title). When in doubt, no tag.
- **Pages have a lifecycle.** A new page is a *draft*. `audit` promotes it to *verified* after re-reading it against its source. Any page can be flagged *needs-update* when something goes stale or a contradiction turns up — and it has to say why. Verification is claim-level: replacing a page wholesale sends it back to *draft*, but a small edit (say, adding one citation) just marks that one claim as unverified so the rest of the page stays trusted and only that claim gets re-checked.
- **Every ingest is double-checked.** After writing, two separate passes confirm the new pages are faithful to the source and well-formed before the job is called done.
- **Two kinds of health check.** `lint` is the cheap, automatic one: it checks structure — sections present, links valid, counts correct, formatting clean — and fixes the safe problems itself. `audit` is the slower, thoughtful one: it judges whether each note is one clear, well-supported idea and decides what's ready to be trusted.
- **Outputs aren't the wiki.** Answers, briefs, comparisons, and reflections are saved under `2-outputs/` and never change the wiki itself without your say-so.

## Acknowledgments

The rulebook and skills draw on four primary sources, plus a small set of independent implementations.

**Primary sources.**

- **Andrej Karpathy.** *LLM knowledge base* (gist), [https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). The three-part split — untouched sources, an agent-maintained wiki, and a rulebook that drives the agent — and the idea of treating Obsidian as the workspace and the wiki as something the agent keeps re-building from your sources.
- **Sönke Ahrens.** *How to Take Smart Notes: One Simple Technique to Boost Writing, Learning and Thinking — for Students, Academics and Nonfiction Book Writers*. CreateSpace, 2017. ISBN 978-1542866507. The note-writing discipline: one idea per note, every claim tied to a source, notes linked to each other, and a clean split between notes *about a source* (here, source pages) and notes *about an idea* (here, concept and entity pages).
- **Anthropic.** *Skill authoring best practices*, [https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices). How to write good agent skills — keep them short, reveal detail only as it's needed, and avoid both time-sensitive notes and unexplained magic numbers. The internal `skill-linter` skill checks skills against this guidance.
- **Wikipedia.** *Signs of AI writing*, [https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). The catalogue of tells that give away AI-written text — overused buzzwords, empty significance-puffing, vague hedging — collected into `a-archive/style/ai-writing-tells.md` and checked across the repo: `lint` and `consistency` scan for them, `skill-linter` checks skill text, and `ingest`'s verification keeps them out of the wiki.

**Independent implementations consulted.**

These projects build on Karpathy's pattern, or solve one piece of it well. Each contributed an idea this repo borrowed.

- [kfchou/wiki-skills](https://github.com/kfchou/wiki-skills) and [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) — splitting the work into many small, single-purpose commands, and a rule that the agent shows you its proposed takeaways and waits for your edits before it writes. Source for this repo's plan-before-write step and its split into many focused skills.
- [Pratiyush/llm-wiki](https://github.com/Pratiyush/llm-wiki) — a rule that every page traces back to one real source page, never to another wiki page. Source for this repo's guard against the wiki citing itself as proof (idea-pages trace to source pages, never to each other).
- [maeste/my-2nd-brain](https://github.com/maeste/my-2nd-brain) — a `reflect` command that writes a short compass note (current direction, blind spots, one question worth sitting with), a `forget` command, and a cap on how many files one operation may change. Source for this repo's `reflect` and `forget` skills.
- [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) — the files on disk are the truth, and the search index can always be rebuilt from them. Source for the "the notes are plain markdown; the index is disposable" stance.
- [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) — automated checks over the link graph and for contradictions, plus dedicated maintenance commands. Source for this repo's `consistency` → `lint` → `audit` check sequence.
- [simonsysun/seeklink](https://github.com/simonsysun/seeklink) — jumping straight to the exact lines you need in a big file instead of re-reading the whole thing. Not used directly here yet, but the reasoning informs `query`'s "wiki first, original source only if needed" approach.

The idea that every reference on a page must point to something real — and that a checker should reject invented citations — traces to *TheKnowledge*, a project described only in the comment thread on Karpathy's gist. The pattern is adopted (this repo's verification confirms that any other work a page names actually appears in the source), but the project itself could not be found at a working link, so it is credited here as an idea, not a project you can clone.

**Community discussion.** Conversations in the Obsidian and Claude Code communities in 2026 about splitting one giant rulebook into many small per-skill files (so each session loads less) shaped the decision to keep `CLAUDE.md` rules-only and put the actual workflows in individual skills under `.claude/skills/`.

**LLM-council lineage.** The `skill-llm-council` skill builds on the multi-LLM deliberation pattern: ask several agents independently, let them review each other anonymously, and have a chair synthesize. The full survey, with confidence tiers, lives in `a-archive/reference/llm-council-best-practices.md`; the references that drove the skill's design are below.

*Canonical.*

- Andrej Karpathy. *LLM Council*, [https://github.com/karpathy/llm-council](https://github.com/karpathy/llm-council). The three-stage protocol — independent answers, anonymized peer review, chairman synthesis — that the skill's councils follow. Technical notes: [https://github.com/karpathy/llm-council/blob/master/CLAUDE.md](https://github.com/karpathy/llm-council/blob/master/CLAUDE.md).
- Ole Lehmann. *How to finally trust Claude's advice (using Karpathy's LLM Council method)*, [https://www.xrticles.com/article/how-to-finally-trust-claude-s-advice-using-karpathy-s-llm-council-method](https://www.xrticles.com/article/how-to-finally-trust-claude-s-advice-using-karpathy-s-llm-council-method). The Claude-only adaptation.
- Jason Flynn. *Your AI agrees with you too much*, [https://jasonmflynn.substack.com/p/001-your-ai-is-agreeing-with-you](https://jasonmflynn.substack.com/p/001-your-ai-is-agreeing-with-you). The role-based council and the case against the agreeable single assistant.

*Practitioner Claude Code skills consulted.* [tenfoldmarc/llm-council-skill](https://github.com/tenfoldmarc/llm-council-skill), [ngmeyer/council-review](https://github.com/ngmeyer/council-review) (reasoning-method-mapped roles, auto-context, dissent preservation), [RyanHouchin gist](https://gist.github.com/RyanHouchin/f8221de64f56ba815e48248f4b8e96dc), [ciphertxt gist](https://gist.github.com/ciphertxt/291fd4ea0077093de17df6f9ad5e4e58), and [ajfisher/llm-advisors](https://github.com/ajfisher/llm-advisors).

*Academic, design-driving.*

- Du, Li, Torralba, Tenenbaum, & Mordatch (2023). *Improving Factuality and Reasoning in Language Models through Multiagent Debate*, [https://arxiv.org/abs/2305.14325](https://arxiv.org/abs/2305.14325). The "society of minds" debate procedure.
- Liang, He, Jiao, et al. (2023). *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate*, [https://arxiv.org/abs/2305.19118](https://arxiv.org/abs/2305.19118).
- Chan, Chen, Su, et al. (2023). *ChatEval*, [https://arxiv.org/abs/2308.07201](https://arxiv.org/abs/2308.07201). Multi-agent referees with explicit roles.
- Wang, Wang, Athiwaratkun, Zhang, & Zou (2024). *Mixture-of-Agents Enhances Large Language Model Capabilities*, [https://arxiv.org/abs/2406.04692](https://arxiv.org/abs/2406.04692).
- Li, Du, Zhang, et al. (2024). *Improving Multi-Agent Debate with Sparse Communication Topology*, [https://aclanthology.org/2024.findings-emnlp.427/](https://aclanthology.org/2024.findings-emnlp.427/). Why a sparse topology (independent answers, then a chair) holds up.
- Liu et al. (2025). *Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate (DMAD)*, [https://openreview.net/forum?id=t6QHYUOQL7](https://openreview.net/forum?id=t6QHYUOQL7). Reasoning-method diversity, not persona diversity, is what makes same-model councils work — the reason Council 1's lenses each carry a distinct method.
- Wynn, Satija, & Hadfield (2025). *Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate*, [https://arxiv.org/abs/2509.05396](https://arxiv.org/abs/2509.05396). Revision rounds can pull agents toward agreement and lower accuracy — the reason this skill has no self-revision step.
- Wu, Li, & Li (2025). *Can LLM Agents Really Debate?*, [https://arxiv.org/abs/2511.07784](https://arxiv.org/abs/2511.07784). Intrinsic reasoning strength and group diversity dominate; majority pressure suppresses independent correction.
- Schneider & Schramm (2025). *The Wisdom of Deliberating AI Crowds*, [https://arxiv.org/abs/2512.22625](https://arxiv.org/abs/2512.22625). Homogeneous groups without engineered diversity show little gain.
- Marvin Minsky (1986). *The Society of Mind*. Simon & Schuster. The original framing of intelligence as many specialized agents.

## License

Released under the [MIT License](LICENSE).
