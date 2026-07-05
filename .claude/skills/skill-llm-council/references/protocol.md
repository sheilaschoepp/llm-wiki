# Step mechanics, peer review, and synthesis prompts

This file holds the operational detail for the workflow in `SKILL.md`. The rosters and role prompts live in `roles.md`; the report shape lives in `report-template.md`.

## Contents

- Spawning subagents
- Step 3 — anonymization and the peer-review prompt
- Step 4 — the chair prompt
- Step 5 — the meta-chair prompt
- Step 6 — the adversarial-verification (refuter) prompt
- Why no self-revision round
- Why no convergence loop

## Spawning Subagents

Use the Agent tool. Within one council, the five Step-2 calls go out in a single message so they run in parallel — five separate tool calls in one response, not five turns. Parallel launch is what keeps the responses independent; a sequential launch lets an earlier response leak into a later one's context.

Subagents read and reason only. They do not edit files. Spawn every Step-2 subagent — and every chair and refuter — with read-only tools (Read, Glob, Grep, and no Edit / Write / shell-write), so the no-edit rule is enforced by the toolset on every path, not left to the prompt to promise. Every edit is made by the orchestrating agent in Step 6, so all writes pass through one place and one set of safety rules. Pass each subagent the shared preamble + its role block (from `roles.md`) + the task brief + the full target-skill text + the relevant rule and reference excerpts gathered in Step 1 + any related-skill or repo context the orchestrator selected in Step 1 (sibling skills the target couples to, shared `multi-skill/` references, and the like) + the Output Contract from `roles.md` as the closing element, so the subagent returns in the required shape. When the relevant breadth is too large to inline, grant the subagent read access to the named related skills and files instead (still read-only tools, bounded to those files — never `0-raw/`, and on a self-run never prior `2-outputs/skill-llm-council/` reports). A subagent that cannot read a named file reports it as missing context and judges only what it could read — a finding that rests on context the subagent never actually read is invalid, the same as the preamble's omitted-excerpt rule applied to the read-access path. The report records the related files each council actually received.

If a subagent fails to return, continue with the responses you have, as long as the council keeps at least three advisors plus its chair (the chair is not spawned until Step 4 — this rule reserves a quorum of three advisor responses so that synthesis has enough independent reads to chair). If it drops below that, re-run the failed role rather than synthesizing from a thin council, and note the re-run in the report. Do not re-run the same role more than once: if the re-run also fails, proceed with the under-quorum council and flag it explicitly as reduced-confidence in that council's report section; if both councils fall below quorum, stop the run and report the failure rather than synthesizing a final change-set from two thin councils.

Three further failure paths beyond a missing advisor: (a) a chair subagent that fails or returns no locatable change-set is re-run once; if the re-run also fails, stop the run and report it rather than applying edits from an unsynthesized council. (b) A refuter that fails to return counts as `refuted` — its edit is demoted to `[needs-review]`, never applied on a missing verdict. (c) If exactly one council falls to zero usable advisors while the other is healthy, do not silently proceed on the one: stop, or proceed single-council only after demoting every auto-apply edit to a proposal and flagging the independence downgrade in the report — a one-council run has lost the two-independent-reads guarantee the whole design rests on.

A response that returns but whose proposed edits carry no locatable anchor (no file plus a findable heading or old-text) has those unusable edits discarded — never apply an edit whose anchor cannot be located in the target; re-anchor it or drop it, and note the drop in the report. Whether the response still counts toward the advisor floor turns on its findings, not its edits: a response carrying usable findings counts toward the floor even when every edit it proposed was unanchored (discard the edits only, keep the findings for the chair); only a response with neither a usable finding nor a single anchored edit is a non-return. Re-run the role if dropping a genuine non-return would put the council below three usable advisors plus a chair.

## Step 3 — Anonymization And The Peer-Review Prompt

Before peer review, relabel a council's five Step-2 responses as A, B, C, D, E with a mapping you store but the reviewers never see (e.g. `A → Outsider`, `B → Contrarian`, ...). Randomize which role gets which letter so position carries no signal. Reviewers judge content, not authorship; the report de-anonymizes afterward for transparency.

Send each reviewer all five anonymized responses with this prompt:

```text
You are reviewing five anonymous council responses about one skill. Judge only the content, not who wrote it.

Answer these four questions in order, numbered 1–4, one short paragraph each:
1. Which response is strongest, and why?
2. Which response has the biggest blind spot, and what does it miss — or say none has a significant one?
3. What, if anything, did ALL FIVE responses miss? This is the most valuable question — answer it carefully, but if the set's coverage is genuinely complete, say so rather than inventing a gap.
4. Is there a minority argument the chair should preserve even if the others disagree?

Keep it under 200 words. Do not rewrite anyone's proposal; you are judging the set.
```

There is no separate self-revision call — reviewers do not get their own Step-2 answer back to rewrite.

## Step 4 — The Chair Prompt

Run one chair pass per council over the de-anonymized Step-2 responses plus all Step-3 peer reviews. The chair is a subagent — the council's sixth agent, spawned after its peer review — never the orchestrating agent, so each council's synthesis is independent of the meta-chair that applies edits in Step 6. (The meta-chair is the one synthesis layer that is the orchestrating agent, because it is the agent that applies; see Step 5.) The chair arbitrates, it does not count votes.

```text
You are the chair of one LLM council reviewing a skill. You receive the original task brief, all five advisor responses (now de-anonymized), and all five peer reviews. Synthesize — do not vote-count.

Return:
1. The consolidated change-set: the concrete edits this council recommends, each with its file and anchor. Exclude any proposed edit you cannot locate to a specific anchor — an edit the orchestrator cannot apply does not belong in the change-set.
2. Where the council agrees (high-confidence signals).
3. Where it clashes — and say whether each clash is a value tension (judgement call) or an error catch (one side is just right).
4. The strongest dissent or minority view, preserved even if you rule against it.
5. What peer review surfaced that no single response had.
6. Remaining uncertainty.
7. Your confidence in the change-set.

If a minority argument is stronger than the majority view, say so and rank it accordingly.
```

## Step 5 — The Meta-Chair Prompt

The orchestrating agent runs this over both chair syntheses to produce the single final change-set. This is where the two councils' reads are reconciled.

```text
You are the meta-chair over two independent councils that reviewed the same skill — a cognitive-lens council and a skill-specialist council. You receive both chairs' consolidated change-sets, clashes, and dissents.

Produce the final change-set. The dominant operation is merge-and-dedupe, not conflict arbitration:
- First merge the two change-sets: where both councils propose the same edit (even if worded differently), collapse it to one. Before tagging anything as cross-council agreement, check whether both councils surfaced it only because their rosters overlap (e.g. both carry an adversarial angle) — shared-roster coverage is not independent confirmation, so do not upgrade a finding to high confidence on duplicate coverage alone.
- A change both councils support → include it, high confidence.
- A well-argued change from only one council → include it, and record the reasoning that earned its place.
- A direct conflict between the councils → resolve it on the merits, state which side wins and why; do not average them into a vague middle.
- Dissent worth keeping → carry it into the report even when you apply or drop the related change.

For every edit in the final set, tag its scope:
- in-folder: touches only files under the target skill's folder → will be applied automatically.
- cross-file: touches CLAUDE.md, README, another skill, multi-skill-memory, a-archive, or shared scripts → will be surfaced as a proposal, never applied here.

Each edit must either quote the chair-synthesis line it derives from or be marked a meta-chair addition with its reason; a final set whose meta-chair additions outnumber its chair-traced edits is a defect to explain. The quotes you give will be checked against the recorded chair syntheses, so quote each line as it actually appears, not a paraphrase. Output the final set as an ordered list of edits, each with file, anchor, the change, scope, and one line of rationale.
```

## Step 6 — The Adversarial-Verification (Refuter) Prompt

Before Step 6 applies the change-set, each load-bearing in-folder judgement edit is checked by one refuter subagent, run in parallel and independent of the meta-chair. This is the independent check the meta-chair cannot be, since the meta-chair both decides the final set and applies it. The refuter's job is to kill a weak edit before it reaches disk, so an edit does not ship on the meta-chair's say-so alone.

```text
You are an independent verifier reviewing ONE proposed edit to a Claude Code skill, before it is applied. Your job is to REFUTE the edit, not to be fair to it. Default to "refuted" unless the edit clearly holds up against the ground truth.

You are given: the edit (file, anchor, old → new) and the reason the council gave for it. You also have read access to fetch your own ground truth — open the current target file and the rule or reference the edit claims to satisfy (CLAUDE.md, the Anthropic skill-authoring best practices, or the style files) and read the relevant part yourself. Do not rely on excerpts handed to you: a curated excerpt can pre-frame the check, so read the source. A cited rule the edit misattributes — the rule does not actually say what the edit claims — is itself grounds to refute.

Check against the ground truth, not against the edit's own wording:
1. Is the claim the edit rests on actually true in the file or rule it cites? Quote the part of the ground truth that confirms or contradicts it.
2. Does the edit contradict another part of the skill, weaken a safety / independence / quorum mechanism, or merely restate something already covered?
3. Would the edit read correctly in context, or does it depend on something that is not there?

If your answer to question 2 is that the edit weakens a safety, independence, or quorum mechanism, the verdict is `refuted` regardless of your answer to question 1 — a safety-weakening edit does not ship on this skill's own say-so, even when the edit is internally well-argued.

Return:
VERDICT: holds | refuted
WHY: one or two sentences, quoting the ground truth you checked.
```

An edit a refuter marks "refuted" is demoted to a `[needs-review]` proposal in Step 6, not applied; record the verdict and the one-line reason in the report. Absence of ground-truth support for a load-bearing edit is itself a refutation, not a pass. This is not a self-revision round — the refuters are fresh agents attacking a claim, the opposite of authors caving to the group (see "Why No Self-Revision Round" below); it is also where ground-truth checking happens, so there is no separate ground-truth pass.

## Why No Self-Revision Round

The user asked early on whether agents should revise their proposals after seeing each other's; the decision was to drop it. The council literature (`a-archive/reference/llm-council-best-practices.md`, citing Wynn et al. 2025) finds that revision rounds pull agents toward agreement — sycophancy and social conformity can shift a correct position to an incorrect one once an agent sees the group. Anonymized peer review still shares every answer and lets the chair act on cross-pollination, without giving each agent the chance to cave. If this turns out to cost real signal on some skill, record it in the per-skill memory file and revisit — do not quietly add a revision call back in.

Note the deliberate asymmetry: the conformity risk is accepted at the synthesis layer (a chair, then the meta-chair, each absorb the group's signal by design — that is their job) and refused at the advisor layer (independent first responses, no self-revision). The protection is placed where it matters most — keeping the five first reads independent — not pretended to exist everywhere.

## Why No Convergence Loop

`skill-linter` iterates its fix-and-recheck until two consecutive clean passes, because a cheap deterministic pass can re-run freely and a fix can introduce drift in a check it did not touch. This skill does not loop the council. After the meta-chair's change-set is applied, it verifies with a single orchestrator pass — the deterministic scripts plus one semantic re-read (see SKILL.md Step 6) — and stops; it does not re-convene the councils. The reason is cost: re-councilling is ~20 subagent calls per iteration, so an iterate-to-convergence loop would multiply the most expensive part of the skill for diminishing returns. The single re-read is the bounded substitute for `skill-linter`'s re-run discipline. If applied edits routinely need rework that the single pass misses, record it in the per-skill memory file and revisit — do not silently add a re-council loop.
