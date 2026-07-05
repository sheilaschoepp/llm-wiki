# Multi-LLM Deliberation: Best Practices for Council-Style Tools

> Reference document for designing a council tool. Surveys academic literature, the Karpathy / Lehmann / Flynn practitioner ecosystem, alternative architectures (MoA, voting, dialectical, role-team), failure modes, multi-agent framework landscape, and cost realities. All cited sources are verified by direct fetch unless flagged in the Confidence notes. Comprehensive References section at the bottom.

## Executive summary

Six findings drive the design.

**The 5-role council pattern is the practitioner consensus for Claude-only deliberation.** Contrarian, First Principles Thinker, Expansionist, Outsider, Executor + Chairman. Originated with Ole Lehmann's March 2026 adaptation of Karpathy's LLM Council; popularized by Jason Flynn's April 2026 Substack post. Multiple published Claude Code skill implementations exist (tenfoldmarc, ngmeyer, RyanHouchin, ciphertxt). Multiple practitioner posts converge on the same set.

**For paper-analysis and draft-critique specifically, a specialist-role council may serve better than the generic 5-role one.** Paper-analysis roles: methods reviewer / theory reviewer / statistics reviewer / related-work reviewer / contribution-novelty reviewer / reproducibility reviewer / chair. Draft-critique roles: argument / structure / evidence / audience / style / adversarial / chair. The cognitive 5-role set is task-agnostic; the specialist sets give each advisor a more concrete evaluation criterion.

**Reasoning-method diversity, not persona diversity, is what makes same-model councils work.** DMAD (Liu et al., ICLR 2025) shows that persona-only diversity often produces uniform reasoning; explicit reasoning-method assignment (inversion, decomposition, analogy, naive questioning, dependency graphing) is what breaks shared mental sets.

**Debate can actively hurt under specific conditions.** Wynn, Satija, & Hadfield (ICML MAS Workshop 2025, "Talk Isn't Always Cheap") show empirically that multi-agent debate can *decrease* accuracy over time — models shift from correct to incorrect answers under peer pressure (sycophancy, social conformity), even when stronger models outnumber weaker ones. Wu, Li, & Li 2025 ("Can LLM Agents Really Debate?") add a controlled finding: intrinsic reasoning strength and group diversity dominate; structural parameters like order or confidence visibility offer limited gains; majority pressure suppresses independent correction. Implication: trigger discipline matters — councils should only fire on genuine decisions where reasoning diversity adds value.

**Anonymized peer review is uncontroversial and cheap.** "Response A/B/C" relabelling removes favouritism. Every practitioner skill does it. Keep it.

**Cost is a real constraint at scale.** Output tokens cost 3–5× input tokens; high-end models cost 20–30× low-end ones. A full council session is 11 sub-agent calls — non-trivial when triggered for low-stakes questions. Build a Quick mode (3 advisors, no peer review) from day one.

## When to use a council

Good fits: research-paper analysis where one model may miss methodological flaws; draft critique where you want separate checks for argument / evidence / clarity / novelty / reader objections; design decisions involving tradeoffs; forecasting or judgement tasks where calibrated uncertainty matters; evaluation of generated text or proposals; safety / robustness / adversarial review where a single supportive assistant may over-polish the user's existing idea.

Poor fits: simple factual lookups, deterministic calculations, tasks with one clearly verifiable answer, low-stakes drafting where speed matters more than assurance, and — critically — any task where the council would just amplify the same missing context across multiple agents.

The Wynn 2025 and Wu et al. 2025 findings together mean trigger discipline is now a *quality* concern, not just a cost concern. Bad triggers actively degrade quality. The SKILL.md description should explicitly list both *do trigger* and *do not trigger* cases following the tenfoldmarc / RyanHouchin pattern.

## The lineage

**Academic root:**

- **Minsky (1986). *The Society of Mind.*** Original framing — intelligence as emergent from many specialized agents.
- **Du, Li, Torralba, Tenenbaum, & Mordatch (2023; ICML 2024). Improving Factuality and Reasoning in Language Models through Multiagent Debate.** Identical procedure and prompts; 3 agents × 2 rounds; "society of minds" callback. arXiv:2305.14325.
- **Liang, He, Jiao, et al. (2023; EMNLP 2024). Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate.** arXiv:2305.19118.
- **Chan, Chen, Su, et al. (2023; ICLR 2024). ChatEval.** Multi-agent referee with explicit roles (General Public, Critic, Scientist). arXiv:2308.07201.
- **Madaan et al. (2023). Self-Refine: Iterative Refinement with Self-Feedback.** arXiv:2303.17651. Single-model iterative critique.
- **Shinn et al. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning.** arXiv:2303.11366.
- **Wang, Wang, Athiwaratkun, Zhang, & Zou (2024). Mixture-of-Agents Enhances Large Language Model Capabilities.** arXiv:2406.04692. *Alternative architecture* — layered MoA; 65.1% AlpacaEval 2.0 with open-source models, surpassing GPT-4 Omni.
- **Li, Du, Zhang, Hou, Grabowski, Li, & Ie (2024). Improving Multi-Agent Debate with Sparse Communication Topology.** EMNLP Findings 2024. Sparse topologies can match or beat fully-connected debate with lower cost.
- **Liu et al. (ICLR 2025). DMAD: Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate.** ✅ Key paper for same-model councils — persona diversity isn't enough; reasoning-method diversity is.
- **Wynn, Satija, & Hadfield (ICML MAS Workshop 2025). Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate.** ⚠️ Key counterpoint — debate can decrease accuracy; sycophancy + social conformity drive correct-to-incorrect shifts. arXiv:2509.05396.
- **Wu, Li, & Li (November 2025). Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning.** arXiv:2511.07784. Controlled study with Knight-Knave-Spy puzzle. Findings: intrinsic reasoning strength and group diversity dominate; structural parameters (order, confidence visibility) offer limited gains; majority pressure suppresses independent correction.
- **"Unlocking the Power of Multi-Agent LLM for Reasoning: From Lazy Agents to Deliberation"** (November 2025). arXiv:2511.02303. Identifies the "lazy agent" failure — one agent dominates while others contribute little.
- **"Debate Only When Necessary: Adaptive Multiagent Collaboration for Efficient LLM Reasoning"** (April 2025). arXiv:2504.05047.
- **"iMAD: Intelligent Multi-Agent Debate for Efficient and Accurate LLM Inference"** (November 2025). arXiv:2511.11306.
- **"Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs."** arXiv:2311.17371. Critical survey.
- **Schneider & Schramm (December 2025). The Wisdom of Deliberating AI Crowds.** arXiv:2512.22625. 202 Metaculus questions; diverse-model deliberation helps (4% relative gain, p=0.017); homogeneous-model deliberation does not when no method diversity is engineered.
- **Salewski et al. (2023). In-Context Impersonation Reveals Large Language Models' Strengths and Biases.**
- **Zhang et al. (2026). Dynamic Role Assignment for Multi-Agent Debate (Meta-Debate).** arXiv:2601.17152.

**Practitioner canonical lineage:**

- **Karpathy (November 22, 2025). LLM Council.** GitHub repo (19.3k+ stars). 4 vendor models + chairman; 3-stage protocol. <https://github.com/karpathy/llm-council>
- **Karpathy. LLM Council technical notes (`CLAUDE.md`).** <https://github.com/karpathy/llm-council/blob/master/CLAUDE.md>
- **Ole Lehmann (@itsolelehmann; March 30, 2026). Claude-only adaptation.** Canonical Claude-subagent version. <https://www.xrticles.com/article/how-to-finally-trust-claude-s-advice-using-karpathy-s-llm-council-method>
- **Jason Flynn (April 15, 2026). "Your AI agrees with you too much."** Established the 5-role set's standard form; 4-level adoption ladder. <https://jasonmflynn.substack.com/p/001-your-ai-is-agreeing-with-you>

**Practitioner Claude Code skill implementations:**

- **tenfoldmarc/llm-council-skill** — clean SKILL.md; HTML report output. <https://github.com/tenfoldmarc/llm-council-skill>
- **ngmeyer/council-review** — DMAD-aware reasoning-method mapping; Full / Quick / Adversarial modes; auto-context loading; "What You Lose" dissent preservation. <https://github.com/ngmeyer/council-review>
- **RyanHouchin gist** — <https://gist.github.com/RyanHouchin/f8221de64f56ba815e48248f4b8e96dc>
- **ciphertxt gist** — <https://gist.github.com/ciphertxt/291fd4ea0077093de17df6f9ad5e4e58>
- **ajfisher/llm-advisors** — <https://github.com/ajfisher/llm-advisors>

**Reference implementations of academic methods:**

- **THUNLP/ChatEval** — <https://github.com/thunlp/ChatEval>
- **Skytliang/Multi-Agents-Debate** — <https://github.com/Skytliang/Multi-Agents-Debate>
- **MraDonkey/DMAD** — <https://github.com/MraDonkey/DMAD>
- **priorb-source/delib-ai-wisdom** (Schneider & Schramm code/data) — <https://github.com/priorb-source/delib-ai-wisdom>

**Variant council patterns in the wild:**

- **James Stanier (October 2025). "Councils of agents: group thinking with LLMs"** (The Engineering Manager). Role-team councils — Technical Council (Principal Engineer / Platform Engineer / Security Engineer / QA Lead / AI/ML Engineer), Executive Council (CEO / CPO / COO / CRO / CMO / CCO). Different philosophy: roles map to *job functions* rather than *cognitive lenses*.
- **Edoardo Schepis. "Patterns for Democratic Multi-Agent AI: Voting-Based Council."** Voting aggregation instead of chairman synthesis.
- **Wisepanel** (commercial) — "dialectical roles" approach: construct roles to *maximize cognitive contrast* and preserve disagreements rather than flatten them.
- **4-turn council pattern** — Turn 1 free answers; Turn 2 role-switching (Explorer / Skeptic); Turn 3 task assignment; Turn 4 finals.

## Council composition

### Option A — Multi-model council (cross-vendor diversity)

Use different frontier or specialized models when budget and privacy allow. Most straightforward way to get capability diversity. Recommended for: high-stakes tasks, model-specific blind spots matter, forecasting / research judgement / complex reasoning, latency and cost acceptable.

Implementation notes: assign roles based on model strengths when known; don't assume the largest model should fill every role; consider a capability-aware assignment stage for important tasks; use one strong model as chair, but allow it to side with a minority argument.

### Option B — Same-model multi-role council (the 5-role pattern)

Use when tool constraints, privacy, or cost prevent multi-model calls. **Only useful if the roles enforce different reasoning methods**, not just different vocabularies. Each role paired with a DMAD-style reasoning method:

| Role | Primary job | Reasoning method |
|---|---|---|
| **The Contrarian** | Find failure modes, hidden risks, overclaims | **Inversion** — assume failure, trace backward |
| **The First Principles Thinker** | Rebuild question from primitives, challenge assumptions | **Decomposition** — break into atomic claims, challenge each |
| **The Expansionist** | Find upside, alternatives, neglected opportunities | **Analogy** — what adjacent domain solved this differently? |
| **The Outsider** | Identify jargon, missing context, curse-of-knowledge problems | **Naive questioning** — flag anything requiring insider knowledge |
| **The Executor** | Convert answer into concrete actions and dependency order | **Dependency graphing** — what blocks what? |
| **The Chairman** | Synthesize, arbitrate, preserve dissent, recommend | Aggregation + arbitration |

Three structural tensions the role set creates: Contrarian vs Expansionist (downside vs upside), First Principles vs Executor (rethink vs do), Outsider in the middle keeping everyone honest.

**Same-model councils should be evaluated more sceptically than multi-model councils** because they can share the same blind spots. Per Schneider & Schramm 2025, homogeneous groups without explicit method diversity show no improvement and slight degradation.

### Option C — Specialist-role council (for paper-analysis or draft-critique)

For task-specific use cases like the two locked modes, specialist roles may serve better than the cognitive 5-role pattern. The Wu et al. 2025 finding that "intrinsic reasoning strength and group diversity are the dominant drivers" suggests that for tasks with concrete evaluation criteria (does this paper have valid statistics? does this draft have a clear thesis?), specialist roles with task-specific evaluation criteria may extract more useful diversity than generic cognitive roles.

**Paper-analysis roles:**
- methods reviewer (experimental design, controls, baselines)
- theory / conceptual reviewer (framing, definitions, theoretical claims)
- statistics / evaluation reviewer (statistical validity, metrics, significance)
- related-work reviewer (positioning, missed citations, prior art)
- contribution / novelty reviewer (what's actually new, overclaims)
- reproducibility reviewer (code, data, hyperparameters, replicability)
- chair

**Draft-critique roles:**
- argument reviewer (logical structure, validity of claims)
- structure reviewer (organization, flow, paragraph-level clarity)
- evidence reviewer (citation quality, evidence-claim fit)
- audience / reader reviewer (does this land for the intended reader?)
- style / clarity reviewer (prose quality, jargon, sentence-level)
- adversarial reviewer (steelman the strongest objection)
- chair

**Tradeoff to weigh:** Option B (5-role) is reusable across all use cases — simpler tool, less prompt engineering. Option C (specialist) is task-specific — better extraction at higher maintenance cost. Could also be hybrid: keep Option B as the default mode, swap in Option C lens prompts for paper-analysis / draft-critique invocations.

### Alternative architectures (not council-style)

- **Mixture of Agents (MoA; Wang et al. 2024).** Layered: layer-1 proposers generate independently; layer-2+ agents take all previous-layer outputs as context and refine. A final aggregator produces the final answer. With 2 layers and 4 LLMs, beats GPT-4o on AlpacaEval 2.0 (65.1% vs 57.5%) using open-source models. Better for iterative refinement than independent peer review. Together AI productized version: <https://docs.together.ai/docs/mixture-of-agents>
- **Voting councils.** Aggregate via majority / weighted / approval voting instead of chairman synthesis. Cheaper but less interpretable. Comet / Agenta caveat: "LLM judges exhibit correlated errors caused by shared latent confounders — verbosity, stylistic preferences, training artifacts — so majority vote may provide little gain or amplify systematic mistakes."
- **Dialectical-role councils** (Wisepanel). Construct roles to *maximize cognitive contrast* and *preserve* disagreements rather than synthesize them away. Opposite of chairman synthesis — the disagreements *are* the output.
- **Role-team councils** (James Stanier). Job-function roles (Technical Council, Executive Council) instead of cognitive roles. Good for organizational simulation; weaker on cognitive diversity (engineers all reason like engineers).

## Stage protocol (practitioner consensus)

Essentially identical across all four practitioner Claude Code skills.

**Stage 0 — Frame the task.** Before convening agents, produce a short task brief: user goal, relevant context and constraints, what a good answer must include, what kind of disagreement is useful, what evidence standard applies, known uncertainty. Scan available context files (CLAUDE.md, memory/, referenced docs). ~30s budget. A poorly framed council produces five polished versions of the wrong question.

**Stage 1 — Independent responses (parallel).** Each advisor receives the same task brief but a distinct role / reasoning method. Prevent agents from seeing each other's first responses. Ask for compact, evidence-focused responses (150–300 words). Require explicit assumptions, confidence, and failure modes. **Always parallel, never sequential** — sequential lets earlier responses contaminate later ones.

**Stage 2 — Anonymized peer review (parallel).** Responses relabelled A–E with randomized advisor-to-letter mapping (no positional bias). Each reviewer answers three questions:
1. Which response is strongest? Why?
2. Which has the biggest blind spot? What's it missing?
3. **What did ALL five responses miss?** ← practitioner consensus that this is the most valuable question.

Peer reviews under 200 words. Avoid simple majority voting as the only decision rule; keep rounds bounded.

**Stage 3 — Chair synthesis.** One agent gets the question, all advisor responses (de-anonymized), and all peer reviews. The chair is not a vote counter — it arbitrates among arguments. Structured verdict:
- Final recommendation
- Where the council agrees (high-confidence signals)
- Where the council clashes (value tensions vs error catches — don't smooth them over)
- Strongest dissent or minority view
- What changed because of peer review
- Remaining uncertainty
- The one thing to do first
- What the user loses by following this recommendation
- Confidence level

**Stage 4 — Audit trail.** Two outputs:
- *Short report* (`council-report-[timestamp].html`) — conclusion, rationale, dissent, action. Visual, for scanning.
- *Full transcript* (`council-transcript-[timestamp].md`) — task brief, agent responses, anonymous-review mapping, peer reviews, chair synthesis, source/context list.

Makes the council inspectable instead of mysterious. Practitioner consensus: skip revision rounds before synthesis (Wynn 2025 suggests revision can introduce sycophancy).

## Recommended prompts

These are ready-to-paste into a SKILL.md. From a companion original-sources doc, lightly tightened.

### Generic advisor system instruction

```text
You are one member of an LLM council. Stay inside your assigned role and reasoning method. Do not try to be balanced. Your job is to surface the best contribution from your angle.

Return:
1. Your main finding or recommendation.
2. The strongest evidence or reasoning.
3. The biggest risk, missing assumption, or uncertainty.
4. One thing the chair should not ignore.

Keep it concise and specific.
```

### Per-role prompts (Option B — same-model 5-role)

**Contrarian:**
```text
Role: Contrarian.
Reasoning method: inversion and red-team analysis.
Assume the proposal fails or the answer is wrong. Work backward to identify why. Focus on hidden risks, overclaims, brittle assumptions, missing evidence, and failure modes.
```

**First Principles Thinker:**
```text
Role: First-principles analyst.
Reasoning method: decomposition.
Break the problem into atomic goals, assumptions, constraints, and evidence claims. Identify which parts are solid, which are unsupported, and whether the original question is the right question.
```

**Expansionist:**
```text
Role: Expansionist.
Reasoning method: analogy and lateral search.
Look for upside, alternative framings, adjacent solutions, and opportunities the obvious answer misses. Do not focus on risk unless it blocks the upside.
```

**Outsider:**
```text
Role: Outsider.
Reasoning method: naive questioning.
Assume no insider context. Identify unclear terms, hidden background assumptions, audience confusion, missing definitions, and places where the answer relies on unstated knowledge.
```

**Executor:**
```text
Role: Executor.
Reasoning method: dependency graphing and implementation planning.
Convert the answer into actions. Identify the first irreversible step, dependencies, blockers, sequencing, and what should be done Monday morning.
```

### Peer-review prompt

```text
You are reviewing anonymous council responses. Judge only the content.

For each response, identify:
1. Strongest contribution.
2. Weakest assumption or blind spot.
3. Whether it should affect the final answer.

Then answer:
- Which response is strongest overall, and why?
- Which response is most dangerous to follow uncritically, and why?
- What did all responses miss?
- Is there a minority argument the chair should preserve?
```

### Chair prompt

```text
You are the chair of an LLM council. You receive the original task, all advisor responses, and all peer reviews. Your job is to synthesize, not vote-count.

Return:
1. Final recommendation.
2. Where the council agrees.
3. Where the council disagrees.
4. Strongest dissent or minority view.
5. What changed because of peer review.
6. Remaining uncertainty.
7. What the user should do first.
8. What the user loses or risks by following this recommendation.
9. Confidence level and why.
```

## Operating modes

Four modes worth considering, derived from ngmeyer plus a companion original-sources doc:

| Mode | Calls | Best for | Composition |
|---|---|---|---|
| **Quick** | 4 | Routine decisions, gut-checks | 3 advisors (Contrarian, Outsider, Executor) + chair; no peer review |
| **Full** | 11 | High-stakes decisions; paper analysis; draft critique | 5 advisors + 5 peer reviews + chair |
| **Adversarial** | 11 | Yes/no decisions, proposals needing stress-test | 2 advocates FOR + 2 skeptics AGAINST + 1 neutral analyst; full peer review and chair |
| **Evidence** | 11+ | Tasks where factuality dominates (literature search, citation-heavy claims) | Standard 5 advisors but each must cite sources; one evidence auditor checks unsupported claims; chair distinguishes facts vs. inference vs. speculation |

Quick mode addresses the cost concern by skipping peer review entirely. Adversarial mode is a deliberate hack to defeat the sycophancy-toward-consensus failure mode by forcing structurally opposed positions. Evidence mode is for tasks like paper-analysis where unsupported claims are a specific failure mode the council should catch.

## Evidence-backed design principles

Ten principles, each with the evidence trail.

**1. Use independent first responses.** Karpathy's LLM Council sends the query to all models in parallel before any cross-talk. Independent first responses reduce early contamination and preserve alternative hypotheses.

**2. Anonymize peer review.** Karpathy anonymizes model identities during review so reviewers judge content rather than favourites. Reviewers see "Response A/B/C"; the system stores the mapping for transparency. Cheap, uncontroversial, mandatory.

**3. Preserve raw outputs.** A council should not hide individual answers behind the final synthesis. Karpathy's implementation exposes individual responses, raw evaluation text, parsed rankings, aggregate rankings, and the final synthesis. Important for user trust and debugging.

**4. Design for graceful degradation.** If one agent fails, continue with successful responses unless the council falls below a minimum quorum. Karpathy's implementation continues with successful responses. Quorum recommendations:
- Quick review: at least 3 advisors + chair
- Full council: at least 4 advisors + chair
- High-stakes: rerun failed critical roles rather than silently proceeding

**5. Real diversity beats decorative personas.** DMAD (Liu et al., ICLR 2025) argues that traditional multi-agent debate can rely on homogeneous reasoning even when agents are given different personas. Fix: specify a reasoning operation, evidence standard, and failure mode to detect for each role — not just a persona label.

**6. Majority is not enough.** Wu et al. 2025's controlled study found intrinsic reasoning strength and group diversity dominate, and majority pressure suppresses independent correction. Chair synthesis should not simply average or majority-vote. Practical rule: require the chair to state when a minority argument is stronger than the majority view.

**7. Avoid unlimited fully-connected debate.** Li et al. 2024 (EMNLP Findings) showed sparse communication topologies can match or beat fully-connected debate with significantly lower cost. Practical options:
- Independent responses + peer review + chair (the LLM Council pattern — sparse by design)
- Two opposing camps + neutral chair
- Star topology where agents speak to chair, not every other agent
- Small-world / sparse connections for large councils

**8. Use debate rounds sparingly.** Liang et al. 2024 (divergent-thinking MAD) argues debate can counter degeneration-of-thought in self-reflection but also reports adaptive stopping and modest back-and-forth are important. Practical rule: default to one peer-review round. Add a second only when agents identify concrete unresolved contradictions. Wynn 2025 reinforces this — more rounds means more sycophancy risk.

**9. Match models to roles (multi-model councils only).** Dynamic Role Assignment (Zhang et al. 2026) proposes meta-debate that selects which model fills which role, with improvements over uniform or random assignment. For high-stakes multi-model councils, role assignment should be capability-aware:
- Strongest long-context model → chair or paper-methods reviewer
- Strongest coding model → executor or implementation reviewer
- Strongest factual / retrieval model → evidence reviewer
- Strongest adversarial model → contrarian
- Most concise model → summary / report generator

Less relevant for Claude-only councils (all roles are the same model), but useful if scope ever expands.

**10. Treat same-model councils as lower-confidence unless method diversity is enforced.** Schneider & Schramm 2025 found benefit for diverse models with shared information, but no benefit when homogeneous groups deliberated. This doesn't prove same-model councils are useless — DMAD shows method-diverse same-model councils can work — but it means same-model councils need explicit reasoning-method diversity and careful local evaluation.

## Failure modes — when debate hurts

One of the most important sections — the most consequential recent academic work sits here. Structured table of failure modes with mitigations, then narrative detail:

| Failure mode | Why it happens | Mitigation |
|---|---|---|
| **Polite agreement** (sycophancy) | Assistants optimize for helpfulness and coherence | Assign adversarial roles; require explicit disagreement |
| **Same-model echo** | Agents share weights and priors | Multi-model diversity *or* force distinct reasoning methods (DMAD) |
| **Majority collapse** | Agents conform to dominant answer | Preserve minority dissent; chair can override majority |
| **Persona theatre** | Roles sound different but reason the same way | Specify reasoning methods and evaluation criteria, not just personas |
| **Over-debate** | Too many rounds amplify noise and cost | One review round by default; adaptive stopping |
| **Context overload** | Agents receive too much irrelevant context | Stage 0 brief; include only task-relevant context |
| **Hidden synthesis bias** | Chair smooths disagreement into vague compromise | Require strongest dissent + "what you lose" in chair output |
| **Opaque output** | User sees only final answer | Save raw responses and review transcript |
| **Weak evaluation** | Team assumes council is better because it's longer | Benchmark against single-model baseline |
| **Capability-mismatch contamination** | Weak agent drags down strong agent in debate | Avoid mixing tiers without role assignment; for Claude-only, less of an issue |
| **Inter-agent misalignment** (~37% of production failures) | Context collapse as agents pass messages | Keep agent count small; keep state-passing structured (chairman-synthesis pattern is well-defended) |
| **Error compounding in sequential chains** | Errors propagate through agent chains | Parallel execution structurally safer |
| **Infinite loops** | No agent knows when task is complete | Hard-stop in chair-synthesis pattern |
| **Lazy agents** | One agent dominates while others contribute little | Explicit role differentiation (DMAD reasoning methods help) |
| **Debate-when-unnecessary** | Council triggered on trivial questions, override correct answer with incorrect one | Conservative triggers; "do not council" examples in skill description |

**Detail on the most consequential findings.**

*Sycophancy and social conformity (Wynn et al. 2025).* "Talk Isn't Always Cheap" tested across diverse-capability groups. Even when stronger models outnumbered weaker ones, debate could decrease accuracy over time — models frequently shift from correct to incorrect answers in response to peer reasoning, favoring agreement over challenging flawed reasoning. The paper recommends agents be explicitly *incentivized and equipped* to resist persuasive but incorrect reasoning. Design implication: the Contrarian role (and Adversarial mode) is a partial structural defence; for high-confidence factual questions the council may underperform a single well-prompted call.

*Majority pressure (Wu et al. 2025).* "Can LLM Agents Really Debate?" used a controlled Knight-Knave-Spy logic puzzle to isolate factors. Findings: intrinsic reasoning strength and group diversity dominate; structural parameters (order, confidence visibility) offer limited gains; majority pressure suppresses independent correction; effective teams overturn incorrect consensus only when rational validity-aligned reasoning is strongest.

*Inter-agent misalignment (~37% of production failures).* Per the "Why Do Multi-Agent LLM Systems Fail?" line of work, this is the single most common failure mode in production systems and the hardest to debug. Context collapse happens as agents pass messages and lose track of earlier decisions. The 4-stage chairman-synthesis pattern is well-defended here because state-passing is structured (each stage receives all of the previous stage's outputs in one go, not a chain).

*Lazy agents.* arXiv:2511.02303 identifies a failure where one agent dominates while others contribute little, with theoretical analysis of why this naturally arises. Proposed fix: verifiable reward mechanism allowing agents to discard noisy outputs. Design implication: explicit role differentiation with DMAD-style reasoning methods is a partial defence — agents are less likely to be "lazy" if their role compels a specific cognitive method.

## Multi-agent framework landscape

For a council tool specifically, the implementation is plain Claude sub-agents — no framework needed. But it's worth knowing the landscape:

| Framework | Style | Best for | Status |
|---|---|---|---|
| **LangGraph** | Graph-based workflows | Production stateful systems, fault-tolerance | Active; tightly coupled to LangChain |
| **CrewAI** | Role-based (organizational metaphor) | Fast prototyping, role-delegated parallel tasks | Active; A2A protocol support |
| **AutoGen** | Conversational collaboration | Multi-party agent dialogues | **Maintenance mode** — superseded by Microsoft Agent Framework |

Learning curve: CrewAI (easiest) > AutoGen (medium) > LangGraph (steepest). Control: LangGraph > AutoGen > CrewAI. For a Claude-only council living as a single SKILL.md, none of these are necessary; sub-agent spawning is handled directly by Claude Code / Cowork.

## Cost and latency realities

- Output tokens cost 3–5× input tokens across major providers.
- High-end models cost 20–30× low-end models for the same token count.
- A full council session (5 advisors × ~250 words + 5 peer reviews × ~150 words + 1 chairman × ~500 words) ≈ 2,000 output tokens distributed across 11 sub-agent calls. Meaningful but not catastrophic on Sonnet pricing.
- Multi-model routing (cheap for easy, escalate to expensive for hard) saves 60–80% in production setups.
- Sparse-topology councils (Li et al. 2024) achieve comparable quality at significantly lower cost.

Implications for the council tool: Quick mode cuts cost by ~⅔; trigger discipline matters financially as well as for quality (Wynn 2025); if the same council is triggered frequently, consider caching the framed question or memoizing role-instruction prompts.

## Implementation checklist

### Minimum viable council
- [ ] Task brief builder (Stage 0)
- [ ] 3–5 independent advisor calls (parallel)
- [ ] Anonymous labels for peer review
- [ ] One peer-review round
- [ ] Chair synthesis
- [ ] Raw transcript saved
- [ ] Short report generated

### Production-ready council
- [ ] Role-specific prompts with reasoning methods
- [ ] Model-role assignment rules (multi-model only)
- [ ] Quorum and retry logic
- [ ] Source / context capture
- [ ] Ranking parser with validation
- [ ] Minority-dissent preservation
- [ ] Cost and latency logging
- [ ] User-visible confidence and uncertainty
- [ ] Test set of known decisions / drafts / papers
- [ ] Evaluation comparing council output against single-model baseline

## Evaluation rubric

Evaluate the council against a single strong model, not against intuition.

| Dimension | What to measure |
|---|---|
| Error catch | Did the council identify flaws the single model missed? |
| Novelty | Did it generate useful alternatives, not just rephrase? |
| Calibration | Did it state uncertainty accurately? |
| Dissent quality | Did it preserve a strong minority view? |
| Actionability | Did the final answer lead to a concrete next step? |
| Cost-benefit | Was the improvement worth extra latency / tokens? |
| Auditability | Can the user inspect why the recommendation emerged? |
| Robustness | Does rerunning the council produce stable conclusions? |

**Task-specific rubrics:**

*Paper analysis:* correctness of methodological critique, missed related work, statistical validity, reproducibility issues, contribution clarity, overclaim detection.

*Draft critique:* thesis clarity, argumentative coherence, evidence fit, audience fit, structure, style, objection handling.

## Architecture for the council tool

```text
User request
  ↓
Task classifier / mode selector  (Quick / Full / Adversarial / Evidence?)
  ↓
Context collector  (CLAUDE.md, MEMORY.md, referenced files)
  ↓
Task brief  (Stage 0 — framed question with context)
  ↓
Advisor calls in parallel  (Stage 1 — 3 or 5 sub-agents, role-specific prompts)
  ↓
Anonymized peer review  (Stage 2 — relabel A–E, parallel review sub-agents)
  ↓
Chair synthesis  (Stage 3 — single sub-agent, structured verdict)
  ↓
Short report (HTML) + transcript (Markdown)  (Stage 4 — outputs/ folder)
```

Use the same underlying council composition for many tasks but swap in task-specific framing templates: paper-analysis template, draft-critique template, decision-review template, adversarial-review template, evidence-audit template. **Do not create too many modes at first** — the important distinction is not the label of the mode; it is whether the prompt assigns distinct reasoning work and whether the output is evaluated against the task's quality standard.

## Implications for the council tool

**Trigger discipline is a quality concern, not just a cost concern.** Wynn 2025 and Wu et al. 2025 both show empirically that bad triggers degrade quality, not just waste tokens. The SKILL.md description should explicitly list both *do trigger* and *do not trigger* cases following the tenfoldmarc / RyanHouchin pattern.

**The "two modes" question can be reframed.** The genuine differences across use cases may map cleanly to Quick / Full / Adversarial / Evidence mode dimensions instead of paper-analysis / draft-critique. Or: keep two modes (paper-analysis and draft-critique) but make them *framing templates* over a shared council composition (Option B 5-role) rather than fully separate councils. Or: use specialist roles (Option C) per-mode. This is the most foundational open call.

**A Quick mode is worth implementing from day one.** ngmeyer's Quick mode (3 advisors, no peer review) covers the routine case at ~⅓ the cost.

**An Evidence mode is worth considering for paper-analysis specifically.** Citation-heavy material is where unsupported claims are the dominant failure mode; the Evidence mode's evidence-auditor catches this.

**Output should default to the HTML + Markdown two-artefact pattern.** All four practitioner skills converge on this; solves the "huge council output in chat is hard to navigate" problem.

**Auto-context means:** the repo-root `CLAUDE.md` and `MEMORY.md` (always); project-scoped brief and memory files (when invoked in a project context); an about-me file (for personal-style context); explicitly referenced files in the user's invocation. Cowork's session has `Read`, `Glob`, `Grep` — the auto-context step is straightforward.

## Design decisions and their status

| Design decision | Status | Notes |
|---|---|---|
| Two modes (paper-analysis + draft-critique) | **Still re-open; alternative framings surfaced** | Could be (a) one council with task framings, (b) Quick / Full / Adversarial / Evidence operating modes, (c) Option B vs Option C role sets, or (d) some combination. |
| Single SKILL.md with mode sections | Still good | Independent of the modes question. |
| Claude subagents only | **Vindicated with caveats** | DMAD shows reasoning-method diversity makes this work. Wynn 2025 and Wu et al. 2025 show triggers matter — bad triggers cause real quality degradation. |
| Tool name | Still good | |
| 5-role pattern (with reasoning-method mapping) | **Confirmed as practitioner standard, with specialist-role alternative documented** | Option B for general use; Option C for task-specific paper-analysis / draft-critique. |
| No revision round | **Now empirically backed** | Wynn 2025 suggests revision rounds may introduce sycophancy. |

## Open questions

- **Option B vs Option C vs hybrid** for paper-analysis and draft-critique modes specifically.
- **Add Quick mode?** Practitioner consensus has it; cost-and-quality argument for it; no real downside. Recommended yes.
- **Add Evidence mode?** Useful for paper-analysis if citation-heavy material dominates that use case.
- **Trigger discipline format.** Match tenfoldmarc / RyanHouchin's "MANDATORY TRIGGERS / STRONG TRIGGERS / DO NOT TRIGGER" pattern in the SKILL.md description, or invent your own?
- **HTML report styling.** Match the tenfoldmarc clean-document aesthetic, or do something project-specific?
- **Outsider role tuning for the user's research contexts.** Should the Outsider be tuned to a reader outside the target research domain so the jargon-flagging is actually useful, or stay generic?
- **Local evaluation set.** The user should run the council against single-Claude on 5–10 known papers / drafts before treating its outputs as authoritative. Without this, the council's value is presumed rather than measured.

## References

All links verified by direct fetch this session unless flagged in Confidence notes.

### Academic — multi-agent debate / deliberation

- Du, Y., Li, S., Torralba, A., Tenenbaum, J. B., & Mordatch, I. (2023). *Improving Factuality and Reasoning in Language Models through Multiagent Debate.* arXiv:2305.14325 (ICML 2024). <https://arxiv.org/abs/2305.14325>
- Liang, T., He, Z., Jiao, W., et al. (2023). *Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate.* arXiv:2305.19118 (EMNLP 2024). <https://arxiv.org/abs/2305.19118>
- Chan, C.-M., Chen, W., Su, Y., et al. (2023). *ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate.* arXiv:2308.07201 (ICLR 2024). <https://arxiv.org/abs/2308.07201>
- Wang, J., Wang, J., Athiwaratkun, B., Zhang, C., & Zou, J. (2024). *Mixture-of-Agents Enhances Large Language Model Capabilities.* arXiv:2406.04692. <https://arxiv.org/abs/2406.04692>
- Li, Y., Du, Y., Zhang, J., Hou, L., Grabowski, P., Li, Y., & Ie, E. (2024). *Improving Multi-Agent Debate with Sparse Communication Topology.* EMNLP Findings 2024. <https://aclanthology.org/2024.findings-emnlp.427/>
- Liu et al. (ICLR 2025). *Breaking Mental Set to Improve Reasoning through Diverse Multi-Agent Debate (DMAD).* <https://openreview.net/forum?id=t6QHYUOQL7> · code <https://github.com/MraDonkey/DMAD>
- Wynn, A., Satija, H., & Hadfield, G. (2025). *Talk Isn't Always Cheap: Understanding Failure Modes in Multi-Agent Debate.* arXiv:2509.05396 (ICML MAS Workshop 2025). <https://arxiv.org/abs/2509.05396>
- Wu, H., Li, Z., & Li, L. (November 2025). *Can LLM Agents Really Debate? A Controlled Study of Multi-Agent Debate in Logical Reasoning.* arXiv:2511.07784. <https://arxiv.org/abs/2511.07784>
- Schneider, P. & Schramm, A. (December 2025). *The Wisdom of Deliberating AI Crowds: Does Deliberation Improve LLM-Based Forecasting?* arXiv:2512.22625. <https://arxiv.org/abs/2512.22625> · code <https://github.com/priorb-source/delib-ai-wisdom>
- *Unlocking the Power of Multi-Agent LLM for Reasoning: From Lazy Agents to Deliberation.* November 2025. arXiv:2511.02303. <https://arxiv.org/abs/2511.02303>
- *Debate Only When Necessary: Adaptive Multiagent Collaboration for Efficient LLM Reasoning.* April 2025. arXiv:2504.05047. <https://arxiv.org/pdf/2504.05047>
- *iMAD: Intelligent Multi-Agent Debate for Efficient and Accurate LLM Inference.* November 2025. arXiv:2511.11306. <https://arxiv.org/pdf/2511.11306>
- *Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs.* arXiv:2311.17371. <https://arxiv.org/pdf/2311.17371>
- Zhang et al. (2026). *Dynamic Role Assignment for Multi-Agent Debate (Meta-Debate).* arXiv:2601.17152. <https://arxiv.org/abs/2601.17152>
- *Why Do Multi-Agent LLM Systems Fail?* OpenReview. <https://openreview.net/pdf?id=wM521FqPvI>

### Academic — single-model iterative / persona

- Madaan, A., Tandon, N., Gupta, P., et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* arXiv:2303.17651. <https://arxiv.org/abs/2303.17651>
- Shinn, N., Cassano, F., Berman, E., et al. (2023). *Reflexion: Language Agents with Verbal Reinforcement Learning.* arXiv:2303.11366. <https://arxiv.org/abs/2303.11366>
- Salewski, L., et al. (2023). *In-Context Impersonation Reveals Large Language Models' Strengths and Biases.*

### Practitioner — canonical lineage

- Karpathy, A. (November 22, 2025). *LLM Council* (GitHub repo, 19.3k+ stars). <https://github.com/karpathy/llm-council>
- Karpathy LLM Council technical notes (`CLAUDE.md`). <https://github.com/karpathy/llm-council/blob/master/CLAUDE.md>
- Karpathy, A. (November 2025). *LLM Council* announcement on X. <https://x.com/karpathy/status/1992381094667411768>
- Lehmann, O. (@itsolelehmann; March 30, 2026). *How to finally trust Claude's advice (using Karpathy's LLM Council method).* <https://www.xrticles.com/article/how-to-finally-trust-claude-s-advice-using-karpathy-s-llm-council-method>
- Flynn, J. (April 15, 2026). *001 / Your AI agrees with you too much.* <https://jasonmflynn.substack.com/p/001-your-ai-is-agreeing-with-you>

### Practitioner — Claude Code skill implementations

- **tenfoldmarc/llm-council-skill** — <https://github.com/tenfoldmarc/llm-council-skill>
- **ngmeyer/council-review** (DMAD-aware reasoning methods, Full / Quick / Adversarial modes, auto-context) — <https://github.com/ngmeyer/council-review>
- **RyanHouchin gist** — <https://gist.github.com/RyanHouchin/f8221de64f56ba815e48248f4b8e96dc>
- **ciphertxt gist** — <https://gist.github.com/ciphertxt/291fd4ea0077093de17df6f9ad5e4e58>
- **ajfisher/llm-advisors** — <https://github.com/ajfisher/llm-advisors>

### Reference implementations of academic methods

- **THUNLP/ChatEval** — <https://github.com/thunlp/ChatEval>
- **Skytliang/Multi-Agents-Debate** — <https://github.com/Skytliang/Multi-Agents-Debate>
- **MraDonkey/DMAD** — <https://github.com/MraDonkey/DMAD>
- **priorb-source/delib-ai-wisdom** (Schneider & Schramm code/data) — <https://github.com/priorb-source/delib-ai-wisdom>

### Practitioner — variant council patterns

- Stanier, J. (October 30, 2025). *Councils of agents: group thinking with LLMs.* The Engineering Manager. <https://www.theengineeringmanager.com/growth/councils-of-agents-group-thinking-with-llms/>
- Drenski, K. (December 6, 2025). *Stop Asking One LLM. Ask a Council Instead.* System Shogun. <https://systemshogun.com/p/stop-asking-one-llm-ask-a-council>
- Schepis, E. *Patterns for Democratic Multi-Agent AI: Voting-Based Council — Part 2, Implementation.* Medium. <https://medium.com/@edoardo.schepis/patterns-for-democratic-multi-agent-ai-voting-based-council-part-2-implementation-2992c3e7c2be>
- Lâasri, H. *The Multi-LLM Strategy: Build Your Own AI Council.* Medium. <https://hassan-laasri.medium.com/the-multi-llm-strategy-c9f3c46a69db>
- *Multi-Agents Solution That Conducts 20 Product Interviews in Minutes.* AI for Product Substack. <https://aiforproduct.substack.com/p/multi-agents-solution-that-conducts>
- *Turning an LLM prompt into a multi-agent discussion.* fedecarg Substack. <https://fedecarg.substack.com/p/turning-an-llm-prompt-into-a-multi>
- Wisepanel — dialectical-role council (commercial; referenced in System Shogun comments).

### Practitioner — frameworks and infrastructure

- **OpenRouter** (API gateway Karpathy's council uses). <https://openrouter.ai/>
- **Together AI — Mixture-of-Agents docs.** <https://docs.together.ai/docs/mixture-of-agents> · GitHub <https://github.com/togethercomputer/MoA>
- **Perplexity Model Council** (Max plan). Native multi-vendor council; "Level 3" in Flynn's adoption ladder.
- **HuggingFace Space — Karpathy LLM Council demo by burtenshaw.** <https://huggingface.co/spaces/burtenshaw/karpathy-llm-council>
- **CrewAI vs LangGraph vs AutoGen comparison.** DataCamp tutorial. <https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen>

### Practitioner — LLM-as-judge / jury / ensemble literature

- Comet. *LLM Juries for Evaluation.* <https://www.comet.com/site/blog/llm-juries-for-evaluation/>
- Agenta. *LLM as a Judge: Guide to LLM Evaluation & Best Practices.* <https://agenta.ai/blog/llm-as-a-judge-guide-to-llm-evaluation-best-practices>
- *Majority Rules: LLM Ensemble is a Winning Approach for Content Categorization.* arXiv:2511.15714. <https://arxiv.org/pdf/2511.15714>
- *Increasing LLM response trustworthiness using voting ensembles.* arXiv:2510.04048. <https://arxiv.org/pdf/2510.04048>
- *CARE: Confounder-Aware Aggregation for Reliable LLM Evaluation.* arXiv:2603.00039.
- *LLM Chain Ensembles for Scalable and Accurate Data Annotation.* arXiv:2410.13006.

### Industry journalism

- VentureBeat (December 2025). *A weekend 'vibe code' hack by Andrej Karpathy quietly sketches the missing layer of enterprise AI orchestration.* <https://venturebeat.com/ai/a-weekend-vibe-code-hack-by-andrej-karpathy-quietly-sketches-the-missing>
- Analytics Vidhya (December 2025). *LLM Council: Andrej Karpathy's AI for Reliable Answers.* <https://www.analyticsvidhya.com/blog/2025/12/llm-council-by-andrej-karpathy/>
- Nargund, N. *Andrej Karpathy's LLM COUNCIL — Fully Explained.* Medium. <https://medium.com/@nisarg.nargund/andrej-karpathys-llm-council-fully-explained-5251bdc9a95f>
- Walby, D. *Multi-model AI advisory board (building LLM Councils).* Medium. <https://medium.com/@davidwalby/multi-model-ai-advisory-board-building-llm-councils-65bf7a4d77a3>
- Hacker News thread on Karpathy's LLM Council. <https://news.ycombinator.com/item?id=46036767>
- Intellectually Curious podcast (Embersilk). *Karpathy's LLM Council.* <https://embersilk.com/podcast/intellectually-curious/karpathy-s-llm-council-a-deliberative-ensemble-of-ai-minds>
- Akillness blog. *LLM Council: A Complete Architecture Analysis of Karpathy's Multi-Agent Deliberation System.* <https://akillness.github.io/posts/llm-council-complete-architecture-analysis/>
- BDTechtalks. *Understanding LLM ensembles and mixture-of-agents (MoA).* <https://bdtechtalks.com/2025/02/17/llm-ensembels-mixture-of-agents/>

### Failure-modes literature (practitioner-side)

- Galileo. *Why do Multi-Agent LLM Systems Fail.* <https://galileo.ai/blog/multi-agent-llm-systems-fail>
- Future AGI Substack. *Why do multi agent LLM systems fail (and how to fix) — 2026 Guide.* <https://futureagi.substack.com/p/why-do-multi-agent-llm-systems-fail>
- Redis. *Why Multi-Agent LLM Systems Fail & How to Fix Them.* <https://redis.io/blog/why-multi-agent-llm-systems-fail/>
- Orq.ai. *Why Multi-Agent LLM Systems Fail: Key Issues Explained.* <https://orq.ai/blog/why-do-multi-agent-llm-systems-fail>
- ICLR Blogposts 2025. *Multi-LLM-Agents Debate — Performance, Efficiency, and Scaling Challenges.* <https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/>
- *When collaboration fails: persuasion driven adversarial influence in multi agent large language model debate.* Nature Scientific Reports 2026. <https://www.nature.com/articles/s41598-026-42705-7>
- Mjgmario (Medium, April 2026). *Single-Agent vs Multi-Agent Systems: When Coordination Helps, Hurts, and Pays Off.*

### Conceptual

- Minsky, M. (1986). *The Society of Mind.* Simon & Schuster.

## Confidence notes

**High confidence** (verified by direct fetch this session, or core findings appear consistently across multiple cited sources):

- Independent first-pass + anonymized peer review + chair synthesis is the core LLM Council pattern (Karpathy README + practitioner skill implementations all converge on it).
- Anonymized peer review is a practical design improvement for reducing identity bias.
- Diversity matters; homogeneous debate without method diversity is weaker and can fail to improve (Schneider & Schramm 2025; DMAD ICLR 2025).
- Debate can hurt — sycophancy / social conformity can degrade accuracy (Wynn et al. 2025; Wu et al. 2025).
- Strong dissent should be preserved; chair should not rely only on majority vote (Wu et al. 2025).
- Raw transcripts improve auditability (Karpathy implementation).

**Medium confidence** (claims drawn from search summaries or single sources without secondary verification):

- Same-model councils can be useful when roles enforce distinct reasoning methods (DMAD claim; ngmeyer skill's mapping of 5 roles to 5 reasoning methods is plausible but the DMAD paper itself doesn't define the 5-role set).
- Five advisors plus chair is a good default for many qualitative tasks (practitioner consensus, not academic finding).
- One peer-review round is usually the right default (practitioner consensus + Liang 2024 finding on adaptive stopping).
- Sparse communication topologies can reduce cost without large quality loss (Li et al. EMNLP 2024).
- AutoGen is in maintenance mode under Microsoft Agent Framework (recent industry reporting).
- The 4-stage chairman-synthesis pattern is structurally well-defended against inter-agent misalignment (inferred from the failure-mode literature, not a specific paper claim).

**Low confidence / needs local testing**:

- The best exact role set for the user's paper-analysis and draft-critique workflows (Option B 5-role vs Option C specialist vs hybrid). Practitioner consensus is general; specialist-role councils for these specific tasks are less well-validated empirically.
- Whether same-model role diversity will outperform a single strong model for these specific use cases. Local evaluation set required.
- Whether a dynamic role-assignment stage is worth the additional cost outside high-stakes tasks.
- DMAD authorship — a companion source cites "Liu et al." but the OpenReview page didn't render usable content this session, so this is taken on that companion doc's authority.
- Quorum recommendations (3+chair for Quick, 4+chair for Full) — practitioner convention from a companion source; not separately validated in academic work.

**Cross-checks**:

- Wu et al. 2025 author attribution and arXiv ID verified by direct fetch.
- Li et al. 2024 sparse-topology paper authorship verified via ACL Anthology fetch.
- Karpathy repo content verified by direct fetch.
- Wynn et al. 2025 abstract, authors, and ICML MAS Workshop venue verified by direct arXiv fetch.
- All practitioner skill GitHub repos verified by direct fetch.
