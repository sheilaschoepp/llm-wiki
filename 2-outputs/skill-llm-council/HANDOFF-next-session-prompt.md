# Handoff prompt — paste into a fresh session

Everything below the line is the prompt. It is written to be self-sufficient: a new session needs no other context.

---

Repo: `sheilaschoepp/llm-wiki`, branch `claude/llm-wiki-skill-upgrades-v4kwju` (HEAD `c7a2f5d`, 7 commits ahead of `develop`). Working tree clean. All 14 skills pass all four scanners; 316 tests pass; `check_consistency.py` and `check_wiki.py` both report zero findings. Do not touch `llm-wiki-mas` — it is read-only reference.

A prior session ported lessons from the active `llm-wiki-mas` wiki into this template, ran a full `skill-llm-council` on `audit`, ran a partial one on `ingest`, and ran an adversarial refuter pass over its own changes. Read `2-outputs/skill-llm-council/skill-llm-council-2026-08-15-1617-audit.md` for the completed audit run, and `git log fa9081e..HEAD` for what changed and why. Three jobs remain.

## Job 1 — finish the `ingest` council

The prior session ran Step 2 only: ten advisors returned, but **peer review, both chair syntheses, the meta-chair reconciliation, and the refuter gate were never run** for that target. It stopped for context, applied only findings it had personally verified against the files or code, and recorded the rest. Do not treat the prior run as complete.

Re-run the council properly on `ingest`, with `.claude/skills/multi-skill/references/verification.md` as the brief's central subject — that shared spec is run by `ingest`, `query`, `synthesis`, and `supersede`, and bound in part by `audit`.

**Targeting constraint:** `.claude/skills/multi-skill/` has no `SKILL.md`, so the council skill cannot resolve it as a target and its auto-apply is scoped to skill folders by construction. Target `ingest` and pass the shared spec as central context; findings against it return as cross-file proposals.

## Job 2 — council runs on `lint` and `consistency`

Neither has had one. Both were changed this session (`lint/references/checks.md` gained the `stale_alias_exempt` entry and the exemption registration; `consistency/scripts/check_consistency.py` gained `LEGAL_ATTRIBUTION_FILES` and an `AGENT_DATA_FILES` entry, with two new tests).

## Job 3 — the held gate-change findings

These were surfaced by ingest's advisors, verified against the files, and deliberately **not applied** because each changes a verification gate rather than fixing a contradiction — exactly the class where a prior refuter pass killed four of five confident proposals. Put each through the refuter gate before applying.

**3a. A `holds` verdict owes no evidence — the certifying path is unfalsifiable.** This is the most serious. In `.claude/skills/multi-skill/references/verification.md`, the bullet "Every refuter finding carries its evidence, or it is discarded" requires a verbatim quote plus physical page **only** from a refuter that refutes or cannot confirm. A `holds` needs nothing, and the orchestrator's re-grep is scoped to "each returned quote", so a unanimous quorum leaves zero proof any refuter opened the raw. Both report shapes record the whole quorum as the literal words `all held`. Combined with the prompt instruction "default to refuted unless the raw plainly supports the claim", the cheapest compliant output a lazy refuter can emit is the one that certifies. Two advisors reached this independently. The asymmetry was presumably designed around "a fabricated refutation is the costly failure, because it overwrites correct content" — true, but only half the risk: a fabricated hold stamps an unchecked claim `verified`, and nothing downstream can tell. Binds all five skills that run the spec.

**3b. The orchestrator's own proof-of-read is taken on trust.** The spec asks for "one late-section raw detail re-located" and one `#page=N`, recorded as prose. The run already read the raw at Step 2, so both can be written from context with no tool call — while a refuter's finding is discarded unless it carries a quote the orchestrator re-greps. The untrusted party must produce re-checkable evidence; the party with every incentive to finish need not.

**3c. Reingesting a `draft` page can never legitimately stamp.** The claim check's scope is "exactly the claims this run wrote or changed", but Setting Status condition 2 requires every non-obvious claim on the *finished page* to be accounted for, and the untouched-claim exemption is available only to a page that entered the run `verified` with a matching hash. A reingest of a `draft` source page — the common path — has pre-existing unmarked bullets certified by nobody, fitting none of the three routes, while "ingest normally stamps" is asserted three times. Note the prior session partly addressed the adjacent case by adding an `*[unverified]*` resolution check to `ingest/references/existing-mode.md`; this is the *unmarked* pre-existing claim, which that check does not reach.

**3d. Non-PDF raws skip question 1 and still reach `verified`.** Question 1 is written wholly in `#page=N` terms, the locator sweep is scoped "Located deep-links (PDF raws)", and both report shapes accept `n/a (non-PDF raw)` for the spot-check. An article or media ingest can be stamped without a single locator ever being opened — and articles are the cheapest, most frequent raws.

**3e. A refuter quote that cannot be re-grepped has no defined disposition.** The spec calls re-grepping "the only thing between a fabricated finding and a fabricated fix", then routes refuters into figure crops (PNGs, ungreppable). Dropping an unconfirmable finding costs one marked claim; acting on it overwrites correct content and re-stamps it.

**3f. `ingest` Step 4's replaced-attachment rule inverts the added-versus-changed asymmetry.** It tells a run to mark an already-hashed claim `*[unverified]*` while asserting "`verified_hash` does not move". `body_hash.py`'s own docstring and CLAUDE.md → Page status say the opposite: newly marking a previously-unmarked claim removes its line from the hash and demotes the page. As written it leaves an embedding page — possibly under a different stem, outside the run's certification reach — stamped `verified` with a stale hash.

**3g. Tier assignment is self-graded and the 1-vs-3 boundary overlaps.** Tier 1 is "a specific fact at a specific page"; Tier 3 includes "a number / metric / result" — most cited facts are both, and the run choosing pays 1 or 3 refuters for the same claim. The report records only counts, not which claims got which tier, so nobody downstream can audit the grading.

**3h. No terminal rule when refuters cannot be spawned.** The spec forbids nesting refuters inside another subagent but never says what happens if the spawn mechanism is unavailable, or if the run is itself a subagent. `skill-llm-council` handles the identical case explicitly ("if they cannot be spawned, the run stops"); here the silence is filled by "ingest normally stamps".

**3i. Step 8's three-round cap has no terminal state in `ingest`.** The shared spec explicitly delegates ("when it arrives, take the terminal state or the escape valve the calling skill defines") and ingest defines neither — only "stop and report on non-convergence". Every sibling defines it: audit sets `needs-update` with a reason plus an `AskUserQuestion` valve; query downgrades and ships. Ingest is the only caller of the spec that leaves the exit undefined.

**3j. Structural, lower stakes.** (i) ~733 words of ingest-only report templates live in the shared spec that four other callers load and never use — moving them to `ingest/references/report-shapes.md` was proposed and not done. (ii) `audit/references/verification-spec.md`'s batching paragraph is now a near-verbatim duplicate of the shared spec's and would be cleaner as a pointer. (iii) `ingest`'s pre-write gate is ordered before Step 4 in the checklist but its text lives inside Step 5. (iv) An ingest description rewrite was proposed and measured at 1010 → 991 chars, adding a `read` trigger and the reingest boundary against `supersede`; not applied.

**3k. The scanners give ingest a false all-clear on distribution.** `check_structure.py`'s `check_reference_depth_and_toc` collects references by Markdown-link regex, and ingest's SKILL.md uses backticked paths throughout — so `nested_reference`, `missing_toc`, and `broken_md_link` cannot fire on it at all. Meanwhile `planning-questions.md` (~1985 words) and `source-page-writing.md` (~1092 words) have zero H2 headings, so every pointer into them loads the whole file, and `relationship-sweep.md` is reachable only two hops from SKILL.md. Consider whether the checker should also recognize backticked paths.

## Process notes from the prior session — read these, they were paid for

- **The refuter gate earns its cost.** Across two passes it killed 5 of 10 council proposals and 3 of 8 of the prior session's own applied changes. Do not skip it, and do not treat council consensus as corroboration: in one case three of ten advisors converged on the *same wrong* edit, and only a peer reviewer caught it.
- **An advisor's measurement is a claim to check.** One advisor measured a description at 995 chars and judged an addition would fit; it came out at 1026, over the 1024 error ceiling. Another council's budget arithmetic was wrong in a way that flipped its conclusion, and two peer reviews endorsed it without re-deriving.
- **Never `str.replace` a Markdown line without its leading indent.** The prior session cut a bullet with a pattern that omitted the indent; the replace stripped the text and left orphaned spaces, which merged with the next line and silently demoted a top-level rule to a sub-bullet. No scanner caught it.
- **Word budgets are tight.** `ingest/SKILL.md` sits at ~6499 of 6500 words and `audit/SKILL.md` at ~6377. Any addition must be paid for with a measured cut, and pure moves to a reference must land in a file that actually *owns* the material — a refuter rejected one relocation because the destination list was scoped to a different case.
- **No available agent type has an exact Read/Glob/Grep toolset.** `Explore` is the closest (no Edit/Write/NotebookEdit) but reads excerpts by default, so instruct full reads explicitly. Record the deviation in the report.
- **`git log` is worth consulting on a disputed rule.** One refuter settled a severity question by finding that a value had been flipped in a commit whose entire message was `u`, which deleted the rationale docstring and gave no justification — evidence no amount of reasoning from the current files would have produced.

Commit and push to `claude/llm-wiki-skill-upgrades-v4kwju` as you go; do not open a PR unless asked.
