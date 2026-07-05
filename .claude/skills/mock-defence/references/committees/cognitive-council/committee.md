# Cognitive council

- **kind**: fictional-roles
- **summary**: The 5-role LLM-council pattern as examiners — Contrarian, First-Principles Thinker, Expansionist, Outsider, Executor + Chairman. Stress-tests a proposal from cognitive lenses rather than field expertise.
- **members**: every profile in `profiles/`. The five advisors question; the chairman synthesizes and runs the closing verdict.
- **question source**: `../../llm-council-panel.md` — the role-to-reasoning-method mapping and the chair's synthesis structure. Each profile fixes one cognitive lens and its reasoning method; questions are generated against the document under defence.
- **fabrication rule**: these are reasoning roles, not real people. Never attribute a paper or stance to a role. Each presses through its assigned reasoning method (inversion, decomposition, analogy, naive questioning, dependency graphing) applied to what the document actually says.
- **use it for**: a method-diverse stress test — the panel that finds failure modes, unfounded assumptions, missed alternatives, jargon gaps, and un-actionable plans. Most distinct from the proxy panel and your real committee.
- **caveat**: same-model cognitive councils are lower-confidence than the proxy panel for *field-specific* critique — the diversity is in reasoning method, not domain knowledge. Use it to harden reasoning and communication, not to substitute for a near-field expert (llm-council-best-practices, principle 10).
