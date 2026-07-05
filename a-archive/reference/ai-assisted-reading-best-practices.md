# AI-assisted reading practices

> A reference sheet for using AI to read technical and academic papers. Output conventions: Canadian spelling, plain prose, no AI-writing tells. Confidence flags (Verified / Confident / Unsure / Guess, per `CLAUDE.md`) mark which claims are soft.
>
> Nothing here was verified against a primary source. The stable principles are **Confident** from general recall and broad agreement across the material. Named frameworks, statistics, benchmark numbers, and publisher-policy specifics are **Unsure** — useful as leads, not citable facts; verify any load-bearing one before relying on it. Tool and product details date within a year; treat them as a snapshot.

## The spine: first pass, not final pass

The same shape recurs everywhere. AI is a triage, explanation, and synthesis *layer* inserted between older multi-pass reading habits and a final pass of source verification. It is not a substitute for the deep read. The strongest cross-platform norm is "AI for the first pass, the source for the final pass." Everything below is an elaboration of that one rule.

## Split "reading" into four jobs

The clearest behavioural shift in the community is that reading is no longer one activity. It is four, and they want different tools:

- **Discovery** — finding candidate papers worth your time.
- **Orientation** — working out what a paper is about and whether to read it deeply.
- **Interrogation** — getting unstuck on a specific term, method, equation, or claim.
- **Capture** — turning what you learned into reusable notes, quotes, and citations.

General-purpose assistants (Claude, ChatGPT, Gemini) are strongest for orientation and interrogation. Source-grounded specialist tools are preferred for discovery, citation tracing, multi-paper synthesis, and capture. Matching the tool class to the job is the recurring recommendation: general assistants dominate usage share, but source-grounded specialist tools dominate for anything that needs traceability.

## Keep the multi-pass method; let AI compress it

The reference workflow is still Keshav's three-pass approach (Confident, recall): a 5–10 minute skim (title, abstract, intro, headings, conclusion) to decide whether to continue; a ~1 hour pass on figures, tables, and method, skipping proofs; a multi-hour pass for full understanding, including mentally reproducing the work.

AI's correct role is to compress Pass 1 triage and scaffold Passes 2 and 3 — not to replace Pass 3 on a paper you actually need to understand. A widely shared prompt pattern asks for all three passes at once ("a quick skim; the main ideas and why they matter; the deeper details I should attend to; and what a critic would say"), used to decide whether the manual Passes 2 and 3 are worth it. A related framework circulating in 2025–2026 is "FOCUS" (Find, Organize, Condense, Understand, Synthesize), shipped by some users as a reusable prompt (Unsure — the framework name and its *Nature Biotechnology* attribution are not verified).

## The prompt is the dominant variable

Output quality depends more on prompt structure than on which model you use. The cleanest framing of *why* is to **separate retrieval, interpretation, and formatting** into different steps with different trust levels: retrieval from PDFs, metadata systems, and scholarly databases; interpretation from evidence-constrained prompts; formatting from reference managers or DOI metadata. That separation is the single most effective hallucination-mitigation pattern for paper reading — most failures come from collapsing the three into one prompt. Concrete patterns that recur:

- **Ask one thing at a time.** Narrow, specific questions beat "summarize this paper." Short focused prompts reportedly outperform sprawling templates. Prefer "explain this term," "compare these two methods," "extract this table," "what follow-up work exists," "critique this weakness."
- **Use a frame, not a request.** Problem–idea–evidence ("what problem, what main idea, how supported, what the results mean"); limitations probe; steelman-then-red-team ("steelman the methodology, then the strongest critique a reviewer would write"); glossary/notation extraction ("every symbol in Section 3, what it means, first equation of use, flag overloaded symbols"); prerequisite map ("background concepts and prior papers needed, one canonical reference each"); argument-structure map ("trace how the author moves from premise to conclusion; mark the evidentiary pivots"); unstated-assumptions check ("what must be true for the conclusion to hold").
- **Separate source from instruction, and label the input.** For dense PDFs plus complex instructions, wrap the paper text and the instructions in distinct delimiters so the model does not confuse the two. Labelled or XML-style blocks reportedly beat JSON *as input* in long-context testing (Unsure). The useful asymmetry: **labelled blocks in, structured JSON schema out** — don't wrap the source document in verbose JSON, but do constrain the *output* to a schema when you want machine-usable extraction.
- **Prefer affirmative instructions.** "Write in flowing prose paragraphs" works better than "do not use bullet lists."
- **Give an example.** One or two worked examples of the output you want (few-shot) anchors structure and reduces variance.
- **Paste the actual text**, not a description of it.
- **The colleague test.** If a colleague with minimal context would be confused by your prompt, the model will be too.
- **Persist good prompts.** Claude Skills and ChatGPT Projects/custom-instruction blocks let you reuse a prompt across many papers without re-pasting, which is the difference between a one-off and a workflow.
- **Summarize sections, not whole papers.** Shift away from "paste the abstract, ask for a summary" toward narrower targets: summarize just the discussion, outline methods and results separately, or summarize a single citation's context. The narrower the target, the less room the model has to flatten or invent.
- **Chunk by structure, not by token window.** Good chunks track the paper's rhetoric — title/abstract, intro, methods, results, discussion, limitations, appendix, plus separate "figure/table + caption" bundles — rather than arbitrary token spans. Two reasons: *Lost in the Middle* (Confident — recall) showed recall drops when the relevant evidence sits mid-context, and more context is not automatically better because recall degrades as token count grows. Put the longform data near the top of the prompt and the query near the end.

Reusable templates for the common jobs are in [Prompt templates](#prompt-templates) below.

## Ground the model in sources for anything you will keep

For anything you intend to cite, summarize, or remember, use a retrieval-grounded tool that answers only from documents you supply and shows inline citations back to the passage — NotebookLM is the repeated community favourite for this; the local equivalent in this workspace is the llm-wiki. Bare chatbots are flexible but ungrounded: they will answer from training data and silently merge details across papers.

Source-grounded synthesis reportedly drops attribution error far below that of raw chatbots (figures cited as roughly under 2% versus 15–25%; Unsure — methodology unstated). The signature multi-paper prompt: upload the corpus and ask for a three-part report — (1) every claim at least N sources agree on, with which sources; (2) every direct contradiction, quoting the conflicting passages; (3) findings that appear in only one source. Require direct quotes; quotes are what make verification cheap.

Two further practices ride on grounding. For an empirical question ("does X cause Y"), an evidence-grounded scholarly search that returns sentences from peer-reviewed papers is a better instrument than an expository chatbot answer; reserve the chatbot for explanation, not for the fact itself. And save noteworthy AI responses back into the grounded corpus as notes, so later questions build on your accumulated reading rather than the raw PDFs alone; the corpus compounds over the life of a project instead of resetting every session.

## Get the file into the right form first

Before any prompt, normalize the input — a summary built on a bad extraction inherits every error silently.

- **Born-digital PDF.** Use a tool that keeps both extracted text *and* page images, and preserves page numbers, so figures, tables, and captions stay on the answer path. Text-only extraction quietly drops anything the query depends on visually.
- **Scanned PDF or image.** OCR to a searchable PDF *first* (OCRmyPDF adds a text layer over the scan via Tesseract, with deskew and other preprocessing), then summarize. If the PDF is really a stack of images, a chat prompt over it is reading nothing. OCR errors propagate into summaries — verify uncertain names, values, and equations against the page image.
- **LaTeX source.** If you have `.tex` and `.bib`, prefer them over the compiled PDF for methods, equations, and references. Scientific-PDF parsing is a reconstruction problem (the existence of tools like GROBID and PaperMage is the tell); source files are usually more faithful for notation and citations, and stable citekeys flow straight into a BibTeX pipeline.

## Reduce context-switching

A consistent complaint is "app fatigue" — the friction of moving one paper between a discovery tool, a reading tab, a chat tab, and a note tool. The recurring fix is to keep the AI in the document rather than in a separate tab (in-PDF reading assistants, reader-integrated chat), and to consolidate capture into one place rather than scattering it across tools. Power users single out tab-switching between paper and chatbot as a primary reason to prefer in-document tools. Fewer tools touched per paper means more attention left for the paper. That is a real gain if context-switching is a known drain.

## Verify, because the dangerous errors are subtle

The failure mode is not obvious nonsense. It is plausible, well-formatted, subtly wrong output that a busy reader will not catch. Documented patterns:

- **Fabricated references.** Models invent citations that mimic real formatting, plausible titles, and real authors who publish in the field. One audit reportedly put fabricated references at roughly 1 in 277 papers in early 2026, a large jump from 2024 (Unsure — 2026-dated, not verified; the *direction* is consistent with the general hallucination literature, the *number* is not something to repeat as fact). Never cite anything you have not confirmed exists.
- **Confidently wrong math.** Right surface vocabulary, wrong substantive claim, especially where notation is overloaded across sections.
- **Misattribution across papers.** Given several papers at once, ungrounded models merge details between them.
- **Invented detail for under-specified papers.** Asked to summarize a paper that omits its own training data or hyperparameters, the model supplies confident specifics the paper never contained. Treat any generated reproduction as a first draft to diff against the paper, not a faithful one.
- **Paywall blindness.** A model given only an abstract, or blocked from the full text, will summarize what it can see while appearing to summarize the paper. Confirm it actually has the full document, not just the abstract, before trusting a summary.

Reported per-summary hallucination benchmarks and the claim that a newer model summarized *worse* than an older one (Unsure) all point the same way: spot-check load-bearing claims against the PDF, and never let the AI's output stand as your final understanding. Fabrication is also reported to be worse in niche or data-poor subfields, where sparse training data pushes the model to guess (Unsure). This matters for any narrow specialty. A cheap external check: citation-context tools that show whether later work supports, contrasts, or merely mentions a claim surface rebuttals you would otherwise miss.

## Math and code: use AI as a Socratic partner

For equations and notation outside your specialty: snip the equation (or screenshot for a vision model) and ask for a plain-language reading of every symbol, what happens at a limiting value (set λ to zero), and the missing derivation steps. Then ask for a small worked numerical example — "walk through this loss for a batch of two with concrete numbers." The reported value here is not the model's answer but that producing the example surfaces *your own* misunderstanding: you see what looks wrong and go back to the paper. For unreleased algorithms, a generated reference implementation is a starting point to compare against the text, not a reproduction.

## Passive consumption has a real but capped use

Audio overviews (NotebookLM's two-host podcast generation) are genuinely useful for Pass-1 triage on papers outside your core area, consumed while commuting or away from a screen, and are an accessibility gain for non-native English readers. The ceiling: they over-dramatize minor results, mispronounce technical terms, and flatten the exact nuance a PhD reader needs. Useful for orientation; a false sense of mastery if used as the deep read.

## Take the de-skilling critique seriously

The strongest objection is not that AI summaries are sometimes wrong — that is catchable. It is that *correct* summaries can still damage understanding, because the comprehension that builds expertise comes from the struggle of extracting the argument yourself. Skip the struggle and you retain the conclusion without the structure of reasoning under it; curiosity (the drive to keep asking *why*) is what dies first. The same point arrives from a writing-skill angle: chatting with a model feels easier than deep thinking, and ease is the warning sign, not the goal.

This is the part of the literature most worth internalizing, and it has concrete countermeasures: require yourself to produce *output* from a reading (criticisms, open questions, a note) rather than consume a summary; timebox reading into a fixed read block followed by a forced synthesis block, so the synthesis that builds retention is non-optional; periodically self-check whether you are reaching for AI to avoid deep work; treat AI as a magnifier of attention on the papers that matter, not a way to read fewer of them attentively. The empirical picture is mixed — one HCI deployment study reportedly found comprehension and engagement gains but flagged overreliance as the central risk (Unsure — study not verified).

## Integrity and confidentiality guardrails

- **Confidentiality.** Do not paste confidential or unpublished material into a cloud model casually. A useful heuristic: if you would not put it on a third-party cloud drive, do not put it in front of a model. This aligns with CLAUDE.md's rule to treat unpublished work as confidential — it extends to AI tools, and a local-grounded stack is the lower-risk option for sensitive drafts.
- **Disclosure.** Disclose AI use where venue or publisher policy requires it; publisher policy is consistently stricter than informal practice (no AI authorship, disclosure of AI assistance, and confidentiality limits on reviewers using AI are the common throughlines). Specific per-publisher and per-agency rules (arXiv submission bans, journal-by-journal policy tables, funding-agency misconduct referrals) are **Unsure** — 2026-dated, and the kind of policy that changes fast; check the actual venue policy when it is load-bearing.
- **Reading-side vs. review-side asymmetry.** A line worth keeping: using AI to critique a paper *you* are reading surfaces issues you would miss and is good practice; using it to generate an *actual peer review* is contested and has reportedly put AI-fabricated citations into real reviewer reports (Unsure). The same prompt is a reading aid in one seat and a misconduct risk in the other.
- **Citation hygiene.** The hallucinated-citation problem is real and the safe rule is absolute: every reference you carry forward must be one you have confirmed exists. This is the reading-side counterpart of the no-fabricated-citations rule in `CLAUDE.md`.

## Prompt templates

Reusable starting points for the common jobs. Each does the same four things: define the task narrowly, restrict the evidence base, fix the output format, and grant explicit permission to say "not found" instead of improvising. Use them in a source-grounded environment that can return page-linked evidence; adapt the wording, the shape is the point.

**Triage brief (fast Pass-1 decision):**

```
You are analyzing a single research paper. Create a triage brief for deciding
whether to read it fully. Return exactly:
1. Research question  2. Why it matters  3. Study design / method
4. Data or corpus  5. Main findings  6. Limitations
7. What to read next in the paper
8. Five evidence-backed bullets with page numbers or quoted phrases
Rules: use only the provided paper; if a point is not clearly stated, write
"Not clearly stated"; do not infer effect sizes or unsupported claims;
2–4 sentences per section.
```

**Structured methods/results extraction (schema-first beats prose — less omission, easier review):**

```
Extract the paper into this JSON schema:
{ "study_type":"", "domain":"", "research_question":"",
  "dataset_or_population":"", "sample_or_corpus_size":"",
  "independent_variables":[], "dependent_variables":[],
  "model_or_intervention":"", "baseline_or_control":"",
  "evaluation_metrics":[], "main_results":[], "limitations":[],
  "quoted_evidence":[{"field":"","quote":"","page_or_section":""}] }
Rules: populate only fields explicitly supported; arrays for multiple items;
null if absent; every non-null analytical field needs >=1 supporting quote.
```

**Reviewer-style memo (forces the "states" vs "infers" split — the guard against turning a plausible reading into a claim the paper never made):**

```
Read this as a critical but fair peer reviewer. Headings: What the paper claims;
What the evidence actually supports; Methodological strengths; Threats to validity;
Missing comparisons or baselines; Ambiguities in reporting; Reproducibility concerns;
Three questions to answer by checking the paper directly.
Rules: separate "paper states" from "you infer"; do not recommend accept/reject;
cite exact page/section/quote for every major criticism; label any point that
needs outside knowledge "external comparison needed".
```

**Annotated bibliography across several papers** — same as the triage brief per entry, plus a one-line problem/method/finding/limitation and a `central | contextual | exclude` tag. Critical instruction: **"use the supplied metadata for the citation string; do not invent missing fields — list them instead."** Let AI annotate; keep citation formatting under bibliographic control (Zotero/Crossref/DOI), never free-text.

**Verify a citation, don't generate one:**

```
Here is a reference and the source metadata I have. Confirm whether the cited
claim is actually supported by the source text I provided. If the source does not
support it, say so. Do not fill in missing bibliographic fields from memory —
report them as missing.
```

## Applied to a research stack

Mapping the above onto a working research stack — adapt the specific tools to whatever you use:

- **Discovery + prerequisite mapping** — a citation-graph tool (Litmaps, Connected Papers, Research Rabbit) is the discovery layer. The high-value AI move that pairs with them: after a Pass 1, ask for the prerequisite-concept and prior-paper list, then resolve each through the graph tool. This converts "I don't know what I don't know" into a concrete reading list — the highest-value AI workflow for entering a new subfield.
- **Grounded synthesis** — the llm-wiki (`ingest`/`brief`/`compare`/`query`/`audit`) is the local, source-grounded multi-paper tool; it is the local, self-hosted equivalent of NotebookLM. Use it, not a bare chatbot, for anything that will feed a major writing project such as a survey or thesis. The consensus/contradictions/outliers three-part prompt maps directly onto `compare` over an ingested corpus.
- **Capture** — a reference manager (Paperpile, Zotero, or similar) handles reference capture and PDF→assistant handoff; a high-level paper-summary database (a Notion table, a spreadsheet, or the wiki itself) is the capture surface. The note-capture method itself lives in the smart-note digests (`a-archive/reference/smart-notes-summary.md`, `a-archive/reference/navigating-a-zettelkasten.md`, Zettelkasten) — the partner to this guide, not a duplicate of it.
- **The reading-minimization default** — a sound default is to minimize the reading rather than power through it. AI's correct job here is Pass-1 skim-categorization handed back as a structured artefact to review and refine, with actual deep reading reserved for keystone papers. A light-read convention (intro, contributions, key sections only) *is* Pass 1; that is precisely the pass AI compresses well, which makes the method a good fit for AI assistance and a bad fit for AI substitution.
- **Active-format default** — every AI-assisted read should leave an artefact (a categorization, a wiki note, a database row), which is also the structural defence against the de-skilling failure mode: producing output forces the struggle the critique says you lose.
- **Output hygiene** — anything an assistant drafts for downstream writing is governed by `a-archive/style/ai-writing-tells.md`. Cross-reference, do not restate.

## Bottom line

1. Use source-grounded tools for anything you will cite or remember; bare chatbots are verify-everything scratchpads.
2. Keep the multi-pass method as the spine; let AI compress Pass 1 and scaffold 2–3; do not skip Pass 3 on papers that matter.
3. Structure the prompt — separate retrieval, interpretation, and formatting; one question at a time; labelled source in, schema out; persist what works. The prompt beats the model.
4. For math and code, make the model a Socratic partner and verify against the paper.
5. Audit for subtle hallucination explicitly; require quotes; confirm every citation exists.
6. The deepest risk is not wrong summaries but skipped struggle. Make every read produce an artefact, and reserve attentive reading for the papers that earn it.

Tool names will be stale within a year. Items 1–6 have held across the 2024–2026 evolution and are the part to keep.
