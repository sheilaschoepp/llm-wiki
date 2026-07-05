# LLM-council panels for a mock defence

Backstop for the two council committees (`committees/cognitive-council/` and `committees/specialist-council/`), the same role `mock-committee-best-practices.md` plays for the proxy panel. It gives the role sets, the reasoning-method mapping, the chair's synthesis structure, and the failure-mode caveats — adapted to a defence drill.

The council pattern follows Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council) — several models answer the same question, review one another's answers anonymously, and a chairman model synthesizes — adapted here from separate models to role-played seats in one context. Distilled for this skill from `a-archive/reference/llm-council-best-practices.md` (the full survey: practitioner lineage, academic citations, cost realities). The skill stays self-contained on this file; reach into the a-archive doc only if the user wants the underlying evidence.

## What a Council Panel Is, in a Defence

A council panel role-plays examiners as **reasoning roles or review criteria**, not as named people. Its value over the proxy panel is enforced diversity — each seat is pinned to a distinct reasoning method (cognitive council) or a concrete review criterion (specialist council), so the panel cannot collapse into five versions of the same question. Its limit: same-model role-play shares blind spots, so a council is weaker than a real near-field expert on *domain-specific* critique. Use it to harden reasoning, communication, and the contribution statement; do not treat it as a substitute for field expertise.

## Cognitive Council — the 5-Role Set (Option B)

| Role | Primary job in the exam | Reasoning method |
|---|---|---|
| **Contrarian** | Find failure modes, hidden risks, overclaims | Inversion — assume it fails, trace backward |
| **First-Principles Thinker** | Rebuild the question from primitives, challenge assumptions | Decomposition — break into atomic claims, challenge each |
| **Expansionist** | Find upside, alternatives, neglected opportunities | Analogy — what did an adjacent domain do differently? |
| **Outsider** | Flag jargon, missing context, curse-of-knowledge gaps | Naive questioning — flag anything needing insider knowledge |
| **Executor** | Convert the plan into concrete actions and dependency order | Dependency graphing — what blocks what, first irreversible step |
| **Chairman** | Frame, synthesize, arbitrate, preserve dissent | Aggregation + arbitration (not vote-counting) |

Structural tensions the set creates: Contrarian vs Expansionist (downside vs upside), First-Principles vs Executor (rethink vs do), Outsider keeping everyone honest. The five advisors question; the Chairman frames and closes.

## Specialist Council — the Paper-Review Set (Option C)

For a research proposal or thesis, concrete review criteria often extract more useful pressure than generic cognitive lenses.

- **Methods reviewer** — experimental design, controls, baselines.
- **Theory / conceptual reviewer** — framing, definitions, theoretical claims.
- **Statistics / evaluation reviewer** — statistical validity, metrics, significance.
- **Related-work reviewer** — positioning, missed prior art.
- **Contribution / novelty reviewer** — what is actually new, overclaim detection.
- **Reproducibility reviewer** — code, data, hyperparameters, replicability.
- **Chair** — frames and synthesizes the reviews into a verdict.

The six reviewers question through their criterion; the Chair frames and closes. For the question banks behind these criteria, draw on `mock-committee-best-practices.md` §5 (research-design-and-methods, interpretation-and-limits, framing-and-contribution).

## Chair Synthesis Structure (Both Councils)

The chair arbitrates, it does not vote-count. The closing verdict states:

1. Final verdict — calibrated to the event (candidacy: is the plan sound? thesis: is the work done?).
2. Where the panel agrees (high-confidence signals).
3. Where the panel clashes — value tensions vs error catches; do not smooth them over.
4. The strongest dissent or minority objection, preserved rather than averaged away.
5. What would change this verdict.
6. The one thing to fix first.
7. What the candidate loses or risks by their current framing.

## Failure-Mode Caveats (Why the Structure Is Shaped This Way)

Same-model debate can *degrade* under specific conditions; the panel design guards against them:

- **Sycophancy / consensus pressure.** Role-played examiners optimize for agreement. The Contrarian (and the closing "strongest dissent, preserved") is the structural defence — keep at least one seat explicitly trying to break the claim.
- **Same-model echo / persona theatre.** Roles that "sound different but reason the same" add nothing. Diversity must be in the *reasoning method or review criterion*, not just the label — that is why each profile pins a method/criterion, not a personality.
- **Majority collapse.** Do not let the verdict be a head-count; a single strong objection can outweigh four agreements. The chair states when a minority objection is the stronger argument.
- **Lower confidence on domain critique.** A same-model council is weaker than a real near-field expert on field-specific flaws. Surface this honestly in the verdict; pair a council drill with the proxy panel or real committee for technical depth.

## How the Drill Uses This File

- Fix each seat's lens from its profile in the committee's `profiles/`; take the reasoning method / review criterion and the chair structure from here.
- Generate questions against the **document under defence** — never attribute a real paper or stance to a council seat (they are roles, not people).
- Attribute each question to the role by name (e.g. `Contrarian:`, `Methods reviewer:`), the same way the proxy panel attributes by role.
- Calibrate the closing verdict to the event using `mock-committee-best-practices.md` §3 (candidacy vs final defence).
