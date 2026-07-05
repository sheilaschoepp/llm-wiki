# AI writing tells

> Rules for avoiding AI-writing tells in any output Claude produces. Primary source: Wikipedia, *Signs of AI writing* (https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), an advice page from WikiProject AI Cleanup. Supplemented with peer-reviewed and reputable-press work: Kobak et al. 2025 (*Science Advances*, excess vocabulary); Reinhart, Brown et al. 2025 (*PNAS*, grammatical/rhetorical features); Russell, Karpinska & Iyyer 2025 (ACL, human detection accuracy); Gorrie 2025 (rhetorical analysis); and reporting from the Reuters Institute, Rolling Stone, and Slate on the false-positive backlash. Update when new tells are spotted.

## How to use this file

Read at session start. Apply across all written output — drafts, code comments, emails, chat replies, anything Claude produces.

Two cautions govern everything below, and both come straight from the source.

First, **these are probabilistic signs, not proof.** LLMs are trained on human writing, so every pattern here also appears in human text — editorials, blogs, fan fiction, press releases, the writing of non-native English speakers, the writing of people in technical fields. The source is explicit that the list is descriptive, not a set of rules, and that any single tell is weak. A 2025 study (Russell, Karpinska & Iyyer, ACL 2025) found that heavy LLM users identify AI text correctly about 90% of the time while light users do barely better than chance, and that detector tools (GPTZero and the like) have non-trivial error rates and are defeated by paraphrasing, markup changes, and spacing changes. The signal is never one marker; it is *several markers stacking in one passage*.

Second, and more important for a rules file: **the surface tells are not the actual problem, and scrubbing them cosmetically makes things worse.** The source warns directly against treating the visible markers (boldface, em dashes, "delve") as the thing to fix, because doing so just makes the deeper problems harder to detect while leaving them in place. The real problems are fabricated citations, unattributed synthesis, fake authority, regression to generic mush, and non-neutral puffery. The fixes throughout this file therefore target *substance* — replace generic with specific, cut unsupported claims, name concrete facts — not word-swaps. A blog source making the same point independently noted that prompting out every tell at once produces stiff, generic prose that reads *more* artificial, not less. So: do not sand the character off good writing in the name of this list. Fix the underlying laziness; the surface tells mostly follow.

The root cause is worth stating plainly because it tells you what to do. LLMs infer the most statistically likely continuation, which regresses to the mean — the generic statement that applies to the widest range of cases. Famous people in training data are described in positive, important-sounding language, so the model omits the rare, specific, nuanced fact and substitutes a common, positive, generic one: "inventor of the first train-coupling device" becomes "a revolutionary titan of industry." The subject gets simultaneously less specific and more exaggerated. Every tonal tell below is a symptom of that one mechanism. The fix is always to push back toward the specific, surprising, falsifiable fact.

When editing the user's drafts, flag instances the same way American spellings are flagged: identify the offender, propose a plain-language (Canadian-spelled) replacement, mark severity. But apply the false-positive caution first — see the "Not actually tells" section before flagging anything as AI.

## Not actually tells (guard against false positives)

The source devotes a whole section to indicators people *assume* mean AI but that don't, because false accusations drive away good writers. Do not flag these in the user's work, and don't contort Claude's own prose to avoid them:

- **Perfect grammar.** Many humans write flawlessly, especially professional and academic writers.
- **Mixed casual and formal register**, or prose that reads both "clinical" and "emotional." Common in technical-field writing, youth writing, playful writing, neurodivergent writing, or any multi-author document.
- **"Bland" or "robotic" prose** on its own. Real AI output has *specific* traits (positive skew, verbosity, the patterns below); generic blandness alone is not diagnostic.
- **"Fancy," "academic," or "formal" prose** on its own. The AI correlation is with *specific overused words*, not with formality, difficulty, or long words in general.
- **Letter-like formatting in isolation** (salutations, sign-offs, subject lines). Humans write this way out of habit or formality. Stronger tells are vertical lists, placeholders, abrupt cutoffs.
- **Transition words in isolation.** Only a handful (*Additionally, Consequently, Notably*, especially as sentence openers) are AI-overused, and even those have heavy human precedent and style-guide approval. Weak tell.
- **The presence of citations.** Most uncited content predates LLMs, and modern retrieval-augmented chatbots cite frequently (often inaccurately). Citations existing proves nothing either way.
- **Em dashes, curly quotes, or a single rule-of-three on their own.** The em-dash panic is the canonical false positive: Emily Dickinson, Nietzsche, and most professional editors use them heavily, and the mark long predates ChatGPT. Rolling Stone, Slate, and the Reuters Institute have all documented "merely polished writing" being misread as AI. Weight punctuation only when stacked with substantive tells.
- **"Bizarre" wikitext or markup errors.** Usually browser extensions, editor bugs, or translation tools — not AI.
- **Low perplexity / formal regularity in genres that demand it.** Detector tools flag legal documents, technical specs, and academic prose as AI because those genres are predictable by design; the Declaration of Independence and Wikipedia's own articles get mislabelled. Non-native English writers are flagged disproportionately for the same reason (lower lexical complexity). Don't treat formality or regularity as evidence.

The corollary, also from the source: a consistent writing style across edits that predate ChatGPT (Nov 30 2022) and edits after it is a sign *against* AI. So is the writer's ability to explain their own choices and supply the real source behind a citation when asked. And the empirical backstop (Russell, Karpinska & Iyyer 2025): even heavy LLM users misjudge AI text roughly 1 in 10 times and light users do barely better than chance, while detector tools have non-trivial error rates and fall to light paraphrasing — so hold any AI judgement loosely.

---

The rest of this file is the pattern catalogue: a lookup table of the markers themselves. Treat it as reference, not a checklist to run mechanically. Some tells (em dashes, an occasional rule of three, copulative substitutes) appear in good human writing too; the problem is only mechanical overuse, and the strongest signal is several stacking at once.

## Vocabulary

Words that became markedly more common in text after late 2022 (when chatbots became widely accessible) and now act as LLM fingerprints. Multiple studies document the overuse; the words co-occur, so where there is one there are likely others. Avoid when a plainer word will do; never stack several in one paragraph. One or two is coincidence — lots of them, lots of times, in post-2022 text is one of the strongest tells.

**High-density "AI vocabulary."** additionally (especially as a sentence opener), align with, boasts (meaning "has"), bolstered, camaraderie, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (as a verb), interplay, intricate / intricacies, key (as an adjective or abstract noun), landscape (as an abstract noun), meticulous / meticulously, palpable, pivotal, realm, robust, showcase, tapestry (as an abstract noun), testament, underscore (as a verb), valuable, vibrant. (Kobak et al. measured the largest 2024 excess for *delves*, *underscores*, *showcasing*, *intricate*, *meticulously*, *realm*, *pivotal*.)

**Model-specific vocabulary.** The *PNAS* study found different instruction-tuned models have distinct lexical fingerprints, useful for guessing the source: ChatGPT variants overused "camaraderie" and "tapestry" ~150× relative to humans; Llama variants overused "unease" 60–100×; both leaned hard on "palpable" and "intricate." Idiolect varies by model and version, so the exact words shift, but the phenomenon (a small set of wildly over-represented words) is stable.

**Vocabulary shifts by era.** The distribution changed over time and differs slightly by model, which is itself a dating signal. Rough cohorts from the source:

| Era | Cluster |
|-----|---------|
| 2023 – mid-2024 (GPT-4) | additionally, boasts, bolstered, crucial, delve, emphasizing, enduring, garner, intricate/intricacies, interplay, key, landscape, meticulous, pivotal, underscore, tapestry, testament, valuable, vibrant |
| Mid-2024 – mid-2025 (GPT-4o) | align with, bolstered, crucial, emphasizing, enhance, enduring, fostering, highlighting, pivotal, showcasing, underscore, vibrant |
| Mid-2025 on (GPT-5) | emphasizing, enhance, highlighting, showcasing — plus the notability/coverage vocabulary below |

Note the trajectory: "delve" was the famous GPT-3.5/4 tell, faded through 2024, and dropped off sharply in 2025. Keep context in mind — "underscore" can mean a literal underline or incidental music; "key" is often an ordinary adjective.

Each model and version has its own idiolect, so the cluster present is a rough fingerprint of *which* tool was used: ChatGPT and Grok lean into broader-context framing and run long, while Claude and Gemini tend to be more concise. ChatGPT is the most prevalent source of this kind of text.

**Significance-puffing phrases.** stands as / serves as, is a testament to / reminder of, plays a [vital / significant / crucial / pivotal / key] role / moment, underscores its importance / significance, reflects broader, symbolizes its [ongoing / enduring / lasting], contributing to the, setting the stage for, marking / shaping the, represents / marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted, continue to captivate, leaves a lasting impact, watershed moment, solidifies, steadfast dedication.

**Promotional puffery.** boasts a, vibrant, rich, profound, enhancing, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking, renowned, featuring, diverse array, breathtaking, must-visit / must-see, stunning natural beauty, rich cultural tapestry.

**Notability / coverage tells.** independent coverage, [region-name] media outlets, profiled in, written by a leading expert, active social media presence, maintains a strong digital presence, has been mentioned in (when the mention is trivial), syndicated through, multiple high-quality independent and widely-read outlets. (This cluster is more common in newer, 2025+ retrieval-augmented tools, which echo Wikipedia's own notability language back at it.)

**Vague attribution / weasel words.** industry reports, observers have cited, experts argue, some critics argue, several sources / publications (when only a few are cited), such as (before exhaustive lists), it is widely believed, many believe. Watch also for *exaggerated quantity* of attribution: presenting one source's view as widely held, citing "scholars" or "reviewers" plural while quoting one, or implying a list is non-exhaustive when the source gives no such indication.

**Editorializing / didactic disclaimers.** it's important / critical / crucial to note / remember / consider, worth noting, may vary, it is worth, no discussion would be complete without, in this article. Older models (~2023) especially added safety-style advice to an imagined reader or "this differs by jurisdiction" disambiguation. The source treats this as a historical tell, but it still surfaces.

**Section-summary tells.** in summary, in conclusion, overall, plus paragraphs that restate the core idea at the end of a section. Historical (older "write an article" outputs), but worth cutting.

**Superficial-analysis tells.** highlighting / underscoring / emphasizing ..., ensuring ..., reflecting / symbolizing ..., contributing to ..., cultivating / fostering ..., encompassing ..., valuable insights, align / resonate with.

**Hedging / knowledge-cutoff tells.** as of [date], up to my last training update, as of my last knowledge update, while specific details are limited / scarce, not widely available / documented / disclosed, in the provided / available sources / search results, based on available information, maintains a low profile, keeps personal details private. Newer RAG chatbots produce a variant: claiming information "isn't publicly available" and then speculating about what it "likely" is — the non-availability claim and the speculation are both often fabricated. Skip all of this — say "I don't know" and use the Verified / Confident / Unsure / Guess confidence scheme from `CLAUDE.md`.

**Wikilawyering / defensiveness tells (avoid in chat replies).** concrete evidence, concrete examples (when defending), align with [X]'s aim, adhere to [X]'s policies / standards, I am committed to ..., I assure you that ..., my intention / goal is to.

## Structural patterns

The deeper diagnosis (Gorrie's rhetorical analysis): the individual structural tells below — parallelism, antithesis, tricolon — are not separate quirks but one posture. An LLM writes like someone who just learned every rhetorical device and can't stop using them, deploying Churchillian technique to write a customer-support email. The fault is *saturation*, not the devices themselves: technique without taste. So the fix is rarely "delete this one triple"; it's "stop reaching for a rhetorical figure in every sentence." If a passage has a parallelism *and* an antithesis *and* a tricolon in three consecutive sentences, that stacking is the tell, even when each device is individually fine.

**Negative parallelisms / antithesis.** Pat AI tics in several forms: "Not only X, but also Y"; "It is not just X, it's Y"; "Not X, but Y"; "no X, no Y, just Z." The "not X but Y" form asserts the subject lacks the first quality entirely ("not a mirror but a portal") and often poses as correcting a misconception the reader never held. Can span two sentences. Also watch lower-grade paired antithesis/parallelism — "profound and paradoxical," "errors or quirks," doubled adjectives that add symmetry but no content. Use sparingly — one in a paragraph is already too many.

**Rule of three (tricolon).** Triple structures — "adjective, adjective, adjective" or "short phrase, short phrase, and short phrase," often imperfectly ascending ("impersonal, authoritative, and homogenized") — make superficial points sound comprehensive without adding content. Default to two or four when natural; use a triple only when each item is doing real work.

**Noun-heavy, information-dense grammar.** The *PNAS* study (Reinhart, Brown et al.) found instruction-tuned LLMs differ from humans on measurable grammatical features, not just word choice, and the gaps are largest for instruction-tuned models like ChatGPT:
- *Present participial clauses at 2–5× the human rate* — the "-ing clause" used as a modifier, e.g. "Brian, leaning on his agility, dances around the ring, evading Show's heavy blows." This is broader than the sentence-final analysis tail under Tone below: it's a structural habit anywhere in the sentence. Cut or convert to a finite clause.
- *Nominalizations at 1.5–2× the human rate* — turning verbs and adjectives into abstract nouns ("the implementation of," "a reduction in," "the utilization of") instead of plain verbs ("implemented," "fell," "used"). Prefer the verb.
- *Agentless passive at about half the human rate* — a reverse signal. AI prose is noun-heavy and active-framed in a particular dense way; suspiciously few agentless passives in otherwise formal prose can itself read as machine-like. (Don't overcorrect by inserting passives — just know the profile.)

**Low burstiness (uniform sentence rhythm).** Human prose alternates short punchy sentences with long elaborate ones; the variance in sentence length and complexity is high. LLM prose tends to a narrow band — sentence after sentence landing in the same ~15–20 word range with similar structure. This low burstiness is one of the more robust statistical tells and is independent of vocabulary. Vary sentence length deliberately; let some sentences be very short. (Caveat: genuinely uniform genres — legal boilerplate, API docs, ISO specs — score low naturally, so this is weak in those registers.)

**Elegant variation.** Swapping synonyms for a previously-named subject (Yayoi Kusama → the artist → the Japanese sculptor → the avant-garde figure) to dodge repetition; driven by the model's repetition penalty. In academic and technical writing this is misleading. Repeat the term; pronouns are fine. (The Guardian's newsroom nickname for this is "popular orange vegetables" — synonyms invented to avoid writing "carrots" twice.)

**Avoidance of "is" / "are."** AI prefers serves as a, marks the, stands as, boasts, features, offers, maintains, refers to over plain is / has. A documented study found GPT-3.5 revisions cut the words "is" and "are" by over 10%. Also watch elaborations like "ventured into politics as a candidate" for "was a candidate," and lead sentences that write "X refers to ..." as though the article were about the term rather than the thing. Use the plain copula unless the verb is genuinely active. (Past-participle "has" — "has written" — is fine.)

**Conclusion / outlook templates.** Don't write paragraphs that begin "Despite [its / these] challenges, [subject] continues to ..." or sections titled "Future Outlook," "Future Prospects," "Challenges and Legacy," or "Challenges and Future Directions" filled with vague forward-looking puffery. The tell is the *rigid formula* (positive-words → "faces challenges" → vaguely upbeat close), not the mention of a challenge. If there's a specific challenge or forecast, name it concretely; otherwise drop the section.

**Leads that define list / descriptive titles as proper nouns.** When the topic is a description rather than a real name (e.g. "List of songs about Mexico"), don't open with "[Title] refers to ..." or "[Title] is a curated compilation of ...". Open with substance.

**Formulaic openers.** Beyond list leads, watch for stock opening moves that recur across a genre regardless of content: parliamentary speeches that all begin "I rise to speak," emails that open "I hope this message finds you well," essays that open "In today's world / In an era of ...". The tell is that the opener is interchangeable across topics — it carries no information specific to this piece. Start with the actual substance instead.

## Tone patterns

**Puffing up significance.** AI adds statements about how an arbitrary aspect of the subject represents or contributes to a broader topic — even for mundane subjects like etymology or population figures, sometimes with a hedging preamble admitting the subject is minor before inflating it anyway. Replace "a revolutionary titan of industry" with "the inventor of the first train-coupling device."

**Promotional / advertisement-like voice.** Travel-guide register ("nestled in the heart of," "rich cultural heritage," "bustling commerce") and press-release register ("the company's commitment to sustainability and customer focus") both leak in by default, often while the model claims it removed them. Older models skew blatantly positive; newer ones are more subtly positive. Stay specific and neutral.

**Notability hammering.** Don't list every outlet a subject was mentioned in ("featured in The Guardian, BBC, Wired ..."); summarize what those sources actually said. Don't manufacture a "Media coverage" section that itemizes sources in a list instead of summarizing their content and citing them as footnotes. Don't attach attribution to trivial coverage a human would either cite inline or leave unsourced.

**Cultural-heritage reflex.** When a topic touches a place or tradition, AI defaults to "vibrant" + "rich cultural heritage" + "diverse tapestry," and keeps reminding the reader of the subject's importance. Never use that combination.

**Tangential broader-context reflex.** For biology, geography, or any specialized domain, AI attaches generic statements about the broader ecosystem, conservation status, or societal context even when the connection isn't load-bearing. With species it belabours conservation status and "preservation efforts" even when the status is unknown and no efforts exist. "Plays a role in the ecosystem and contributes to the region's rich cultural heritage" is the tell. Mention the broader frame only when a specific fact ties it to the subject. (This reflex is more pronounced in ChatGPT and Grok than in Claude and Gemini.)

**Manufactured debate.** AI claims that a thing or action "has generated debate / prompted broader reflection / raised questions about" related abstract concepts, with no source for the debate. Don't assert discourse exists unless it does and is cited.

**Non-existent categories / typologies.** AI invents structural partitions ("There are three main types of X," "X falls into four categories: ...") when no canonical taxonomy exists. Hallucination-adjacent — authoritative form, fabricated content. Don't impose a typology unless one is established; if the territory is genuinely uncategorized, say so.

**Failure to adapt register across genres (the root of the style-shift tell).** The *PNAS* study's central finding: humans adjust voice to context — a text message, a legal brief, and a wedding toast read differently — whereas LLMs apply one homogenized register everywhere, and don't reliably shift it even when prompted with examples of a target genre. Two consequences for Claude. (1) When editing within an existing document — the user's draft, a paper section, a code file's comments — match the surrounding voice exactly; AI defaults to its own house style (more formal, more puffed-up, more bolded) and the seam shows. If the prose around the edit is terse and informal, stay terse and informal. (2) When writing fresh, consciously fit the genre rather than emitting the default authoritative-explainer register: a Slack message is not a report, a commit message is not an essay. A noticeable register mismatch — to the document or to the genre — is itself one of the strongest real-world tells.

**Superficial analysis tacked on.** AI appends "-ing" phrases to the end of sentences ("..., highlighting the enduring legacy of ...", "..., reflecting the broader trend toward ..."). Newer RAG models may pin these to a named source ("Roger Ebert highlighted the lasting influence") whether or not the source says anything close. Cut these participial tails unless they make a specific, supported point.

**"Concrete" as defensive shield.** Demanding "concrete examples" or "concrete evidence" when challenged is a tell. State the actual disagreement.

**Gambling-metaphor framing ("the bet").** Casting a premise, assumption, hypothesis, or design rationale as a wager — "the bet is that X," "X's bet is that Y," "on the bet that Z," "the falsifiable bet that ...," and the verb forms "betting / wagering on." It dresses an ordinary epistemic commitment in punchy gambling language so an assumption reads as a bold insight, and it recurs as a tic (a recurring Claude habit, not from the cited literature). The fix is substance, not a synonym swap: name the actual epistemic status — premise, assumption, hypothesis, prediction, claim, design rationale — or state the claim plainly. "The transformer's bet is that attention can replace recurrence" becomes "The transformer's premise is that attention can replace recurrence." Reserve "bet" or "wager" for an actual stake or a deliberately framed, falsifiable prediction, never as the default way to introduce an assumption.

## Formatting

**Boldface overuse.** Don't bold every key term, every section opener, or "key takeaways." This habit is inherited from READMEs, fan wikis, how-tos, sales decks, and listicles. Bold sparingly for real emphasis.

**Inline-header vertical lists.** The signature ChatGPT list shape — marker, then a **bolded phrase**, then a colon, then description, where the bolded phrase is just reworded in the sentence that follows — is near-absent in good prose and adds little. Prefer prose when it reads well. When pasted as plain text the formatting and line breaks often get mangled (stray •, -, –, #, or run-together numbers), which is its own tell.

**Em-dash overuse.** AI uses em dashes formulaically, often "punching up" sales-style emphasis, and especially where a human would use commas, parentheses, or a colon. It's a weak tell alone and far more common on discussion pages than in article prose, so weight it only in combination. (Note: GPT-5.1 was specifically tuned to suppress em dashes, and Claude/Gemini use them less than ChatGPT historically did.) Prefer commas, parentheses, colons, or sentence breaks; moderate use is fine.

**Curly / smart quotes.** ChatGPT and DeepSeek default to curly quotes and apostrophes (" ' '), sometimes mixing curly and straight in one response. Use straight quotes (`"`, `'`) by default in code, LaTeX, and Markdown; don't mix. Weak tell on its own — Word, macOS/iOS, LanguageTool, and Chicago-style typesetting all produce curly quotes legitimately, and Claude and Gemini typically *don't* use them. Still worth flagging in the user's drafts.

**Title case in headings.** AI capitalizes every main word ("Impact of Technology and Digitalization"). Sentence case is the academic and Wikipedia default ("Impact of technology and digitalization").

**Markdown leakage and markup mixing.** Don't sprinkle `##` headers or `**bold**` into LaTeX, Overleaf, plain-text emails, BibTeX, or anywhere they won't render — match the destination format. A stronger, related tell: Markdown syntax mixed with another markup language's syntax (e.g. wikitext), especially content dumped inside a fenced ```` ```wikitext ```` code block. Faulty target-format syntax wrapped in Markdown is a strong AI signature.

**Thematic breaks (`---`) before every heading.** AI does this from a Markdown habit. Use them only for genuine section breaks.

**Heading-level skipping.** Don't start at H3 because it "looks tighter," and don't jump levels. Use the natural hierarchy from H1 down. (In wikitext this shows up as starting sections at `===` instead of `==`.)

**Unnecessary tables.** Don't tabulate three or four facts that read fine as prose.

**Emoji as decoration.** Don't open section headings or bullet points with decorative emoji (🧠, 🪷, 🚨, 📌, 🌕, etc.). LLMs do this when prompted to "make it more engaging." Reserve emoji for cases where the user has used them or where they carry actual information.

**Subject lines where they don't belong.** Pasted-from-chatbot text often opens with `Subject: ...` — leftover from the model treating the prompt as an email. Strip these.

## Citation hygiene

Overlaps with the global no-fabricated-citations rule, but the failure here is usually fabrication dressed as formatting, which is exactly the kind of *real* problem the surface-tell warning says to prioritize. Specific modes:

- **Broken external links** — URLs that don't resolve, dead links absent from any archive. Several dead links in a new page, none archived, is a strong sign the links were never real.
- **Invalid DOIs and ISBNs** — failed checksums (citation templates warn on these), or DOIs that resolve to unrelated articles. A plausible-looking DOI assigned to a completely different paper is a classic hallucination.
- **Book citations missing page numbers**, or with page numbers that don't verify the claim. Suspect a general-topic book cited with no URL where the cited page, when checked, doesn't contain the claim.
- **Fabricated scholarly references** — real-sounding journal/volume/author combinations that don't exist or where the named author was dead at the purported publication date.
- **Placeholder dates** (`2025-XX-XX`, `2022-11-XX`) or fields (`INSERT_SOURCE_URL`, `SOURCE_PUBLISHER`, `PASTE_SPOTIFY_TRACK_URL_HERE`, `PASTE_YOUTUBE_VIDEO_URL_HERE`).
- **Bracketed name/link placeholders** (`[Your Name]`, `[link to revised article]`, `[Entertainer's Name]`, `[Insert Date]`, `[Describe the specific section ...]`). Mad-Libs template language the user forgot to fill in.
- **UTM / referrer leakage** (`utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`). Strip from any URL before pasting. Near-definitively proves a chatbot fetched the source, though not that it wrote the prose.
- **Named references defined but never cited inline** (a `<references>` block or named ref with no matching inline use).
- **Reference-markup leakage** — none of these belong in output: `:contentReference[oaicite:0]{index=0}`, `oai_citation`, `Example+1`, `turn0search0` / `turn0image0` / `turn0news0` / `turn1file0` (often wrapped in Private-Use-Area Unicode), `citegenerated-reference-identifier`, `[attached_file:1]`, `[web:1]` (Perplexity), `<grok-card data-id="...">` (Grok), the JSON form `({"attribution":{"attributableIndex":"X-Y"}})`, and footnote arrows (`↩`, `↩2`).
- **Outdated access-dates** — an access-date noticeably older than the edit (e.g. a Dec 2025 page citing `access-date=12 December 2024`). Weak and has innocent causes (copied citations, offline work).

Every citation must be one Claude is confident actually exists. If unsure, say so or offer to search.

## Hallucinated authority

A family of fabrication-as-formatting tells beyond citations:

- **Non-existent templates / parameters** — plausible-sounding infoboxes or fields that don't exist (red links, or silently no-op parameters).
- **Non-existent categories** — generic-sounding or renamed category labels that red-link.
- **Fabricated policies, standards, or shortcuts** — citing an authoritative-sounding rule ("WP:NOTENGLISH states ...", "Per WP:LAW ...") that doesn't exist or doesn't say what's claimed. The general form — inventing a named authority and quoting it — generalizes well beyond Wikipedia. Never invent a standard, RFC, statute, or guideline name and attribute claims to it.

## English variety

A mismatch between the topic's national ties (or the writer's location) and the English variety used can indicate AI defaults — e.g. American spelling on a topic with strong Canadian or British ties, when the writer would not normally use it. Only a *sudden and complete* shift is suspicious; non-native speakers mix varieties routinely. Relevant here given the standing Canadian-spelling rule: keep variety consistent and matched to context, and treat a clean wholesale variety-switch in the user's draft as worth a flag.

## Conversational tells

When chatting (not producing a deliverable), avoid these — collectively they're the loudest tell:

- "I hope this helps." / "Let me know if you have any other questions!"
- "Of course!" / "Certainly!" / "Absolutely!"
- "You're absolutely right!" / "Great question!"
- "Would you like me to ...?" / "Is there anything else?"
- "Here is a more detailed breakdown:"
- Canned offers to refine, improve, or expand on request.
- "I am committed to ..." / "I assure you ..." / "My intention is to ..."
- "I am open to / would appreciate / welcome any additional input / guidance / feedback."

Direct, terse replies beat any of these.

## Truncation and refusal artifacts

Output artifacts that scream "raw chatbot dump." Catch and remove before sending.

**Prompt-refusal phrases.** "As an AI language model ...", "As a large language model ...", "I cannot offer medical / legal / financial advice, but I can ...", "I'm sorry, but I can't ..." — and the polite-pivot variants where the model declines, then offers a near-equivalent. None of these belong in a deliverable. If a refusal is right, it's the user's call, phrased as a person would phrase it.

**Abrupt cut-offs.** Sentences truncated mid-clause, lists ending with a trailing comma, paragraphs that stop at a token-limit boundary, "(continued)" / "[continues]" stubs. Re-read the last paragraph of every deliverable and finish any sentence that breaks. (Innocent causes exist — a bad copy/paste — so this isn't proof on its own.)

**AI self-disclosure / meta-narration inside content.** "In this section, I will discuss ...", "Here is a draft of ...", "Below is a curated list of ...", "Would you like me to turn this into ...?", "I can guide you step-by-step." Strip the narration; keep the content. This includes chatbot-to-user correspondence accidentally left in the body, and self-itemizing edit summaries ("I revised the tone to be more encyclopedic and less promotional," "ensured WP:NPOV compliance") — verbose, first-person, policy-echoing summaries of trivial edits. Also: unprompted "submission statements" or reviewer notes a model attaches to a deliverable arguing why it meets some standard — they only advertise that the thing was machine-generated.

## Overall hygiene

LLM output regresses to the mean. Specific, surprising, falsifiable beats generic and positive. When Claude finds itself writing a sentence that could apply to almost any subject in the same category, delete it — that sentence is the disease, and the vocabulary and tone tells above are just its symptoms.

One AI vocabulary word, one negative parallelism, or one "Despite challenges ..." opener may be coincidence; several stacking in one passage is the actual signal. The fix is always the same and it is always about substance, not cosmetics: replace generic with specific, replace formula with content, cut unsupported claims, cut the puff. Do not strip every surface tell at the cost of voice — over-correction reads as artificial as the tells do, and (per the source) cosmetic scrubbing only hides the real problems it should be exposing.

For the user's drafts: apply the "Not actually tells" caution first, then flag genuine instances, propose a Canadian-spelled plain-language replacement, and mark severity (fabrication: citations / hallucinated authority / placeholders > truncation & refusal artifacts > vocabulary > structural patterns > tone > formatting > conversational tells).
