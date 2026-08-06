---
type: skill-llm-council
mode: solve
result: solved-no-survivor
date: 2026-08-06
target: .claude/skills/consistency
snapshot: 8470d34
advisors: 10
evaluators: 0
refuters: 6
applied: 0
needs_review: 3
cross_file_proposals: 3
---

# Skill LLM council — consistency — 2026-08-06 15:07

Mode `solve`. Terminal result **`solved-no-survivor`**: three load-bearing candidates were
selected, all three were refuted at the adversarial gate, and **nothing was written to the
target skill**. This is a complete outcome, not a failed run — two of the three would have
shipped real damage.

## Snapshot and dirty-tree gate

- Baseline commit `8470d34`; `git status --porcelain -- .claude/skills/consistency/` empty at freeze.
- Target files hashed at freeze: `SKILL.md` (247L), `references/checks.md` (49L),
  `scripts/check_consistency.py` (2560L), `scripts/tests/test_check_consistency.py` (693L),
  `scripts/acceptance_check_consistency.py` (71L), `consistency-memory.md` (13L).
- Cited authorities hashed: `CLAUDE.md`, `multi-skill/scripts/body_hash.py`,
  `multi-skill/scripts/check_wiki.py`, `multi-skill/pagination-map.md`, `lint/SKILL.md`,
  `audit/SKILL.md`.
- No prior `skill-linter` report for this skill existed; the five deterministic scanners were
  run for a structural baseline. Pre-existing, untouched: `h2_heading_case` suggestions on
  `references/checks.md`; one `positional_call` error on `scripts/acceptance_check_consistency.py:54`.

## Problem manifest (frozen before launch)

- **P1** — no integrity check for the curated data files consistency declares single sources of
  truth. Ground: emptying all 43 `## 0-raw/` sections of `pagination-map.md` in a scratch copy of
  the populated vault produced a **byte-identical 167-finding set**; `lint` raises
  `pagination_map_unregistered` only at `info`, which never blocks `result: clean`.
- **P2** — no check that a schema rule and the tooling enforcing it agree. Ground: `CLAUDE.md:573`
  states no marker position; `body_hash.py`'s `_UNVERIFIED_RE` accepts exactly one. Measured
  consequence on the populated vault: 200 markers, **200 trailing, 0 canonical**, `unverified_claim`
  findings **0**, `verified_hash_mismatch` **90**, `consistency` reporting `clean` throughout.

## Rosters

- **Council 1 (fixed cognitive lenses):** Contrarian, First-Principles, Expansionist, Outsider, Executor.
- **Council 2 (composed per risk surface):** Description & Trigger, Structure & Token-Economy,
  Best-Practices-Compliance (the three core), plus **Adversarial Failure-Mode** (mandatory — the skill
  auto-fixes wiki pages, CSS, `.gitkeep`, README without asking) and **Script & Python-Quality**
  (bundles a 2560-line `scripts/`). Dropped for the two-slot limit, in the fixed priority order:
  Schema-Compliance, Instruction-Clarity.
- Both councils returned 5/5. Divergence confirmed: 30 candidates across 8 materially distinct
  mechanisms, with a genuine four-way split on disposition.

## What the councils found beyond the manifest

Three defects neither the audit nor the orchestrator had named:

1. **`audit/SKILL.md:84` promises coverage that does not exist** — it tells its reader that changes
   confined to the four curated data files "are not schema-drift by themselves; consistency still runs
   their own capacity, integrity, and stale-entry checks." Consistency runs none of the three. The
   downstream gate waives a class of `.claude/skills/` change against nonexistent coverage.
2. **`AGENT_DATA_FILES` (3) vs `CLAUDE.md` Stay In Your Lane (4)** — `synonym-ignore.md` is declared,
   on disk, and loaded by `check_synonyms.py:73`. (See the EDIT 1 refutation: the naive repair is wrong.)
3. **The description has 32 characters of headroom** — 992 against `DESCRIPTION_MAX_CHARS = 1024`
   at `check_structure.py:67`. Two candidates each adding a coverage clause individually pass and
   collide at 1069.

## Orchestrator-resolved unknown

Three advisors independently named the same blocking unknown and hedged toward a weaker design
because of it: whether per-raw pagination coverage would false-positive on an intact populated vault.
Measured after Step 2: **41 raws cited with `#page=`, 43 registered, 0 genuine gaps** (the single
apparent miss is `0-raw/papers/<stem>.pdf`, placeholder text already skipped by `PLACEHOLDER_TOKENS`).
The hedge was unnecessary; the unknown is closed.

## Selected candidates and adversarial verification

Paired role-specialized refuters (locator + entailment) on each load-bearing edit, per
`references/protocol.md`. Every refuter quote was re-grepped against the source before being acted on.

| Edit | Locator | Entailment | Disposition |
| --- | --- | --- | --- |
| 1 — add `synonym-ignore.md` to `AGENT_DATA_FILES` + anchor table | holds | **refuted** | `[needs-review]` |
| 2 — new check `curated_data_file_integrity` | holds | **refuted** | `[needs-review]` |
| 3 — new check `schema_states_marker_position` | holds | **refuted** | `[needs-review]` |

### EDIT 2 — the refutation that matters most

The entailment refuter executed the frozen code against the populated vault and found **31 findings
on legitimate roman-numeral front matter** (`- 11 = viii`, `- 21 = xviii`) under three raws.
`_pagination_span_len` is digits-only. Orchestrator re-verification: **33** such entries exist.

The `fix_hint` reads *"Use digits or an equal-length `lo-hi` span on both sides, or `none` on the
right"* — instructing an agent to overwrite a correct printed folio. `pagination-map.md` forbids
exactly this: *"a wrong `none` would license stripping a correct printed page from a citation and
certifying the damage."* The check would have driven autonomous corruption of the single source of
truth it was written to protect.

**None of the ten generators caught it.** The Script & Python-Quality advisor reported the design
"validated end-to-end against a temp copy" — but validated against the *template*, which has no front
matter. The defect exists only against real data.

Secondary, also upheld: the coverage arm's scope claim overreaches its ground (the map documents
"unregistered" as the intended *safe* fallback), and the finding message is false of the flagged
lines' effect (`_load_pagination_map` does `out.setdefault(raw, {})`, so the raw stays registered).

Hazards probed and cleared, recorded for a future round: archive exclusion works; `- 1-13 = 4171-4183`
and `- 14 = none` both pass; prose bullets under `## Entry format` are correctly ignored; the
`CLAUDE.md` semicolon falls after the file list; `re.escape(anchor)` matches all anchors; no name
shadowing.

### EDIT 1 — a category error

`AGENT_DATA_FILES` is not a permission roster. Its own comment states the membership criterion:
*"their content is by construction this vault's own — page paths, per-raw pagination maps — so a
corpus bibkey in them is content, not leakage."* `synonym-ignore.md`'s content is generic English
term pairs (`route / path`, `record / row / entry / item`), not corpus-derived. Adding it would grant
an **unearned leakage exemption** and surrender real scanning coverage. The declared 3-vs-4 "drift" is
between two genuinely different sets — a write-permission roster and a content-based scan exemption —
so declaration parity is itself the wrong predicate.

### EDIT 3 — brittle against the fix it demands

The extracted pattern is `^`-anchored under `re.MULTILINE`, so the exhibit must begin the line.
Verified against every plausible rendering of the approved `CLAUDE.md` wording:

| form | result |
| --- | --- |
| approved form (indented, inline backticks) | **fires** |
| un-indented, still backticked | **fires** |
| mid-sentence inline, escaped | **fires** |
| fenced / column-0 bare | clears |

The section's own convention is inline backticks for every token, so the natural fix is the one the
check rejects — and once the wording lands, the finding's message becomes factually false about the
repo. This is verbatim the failure the councils named in the abstract: *"a correct fix phrased without
the token leaves the check firing forever, and the natural response is to delete the check."*

## Disposition of the run

- **Applied: 0.** No file under `.claude/skills/consistency/` was modified. `git status` for the
  target path is unchanged from the freeze.
- **`[needs-review]`: 3.** Per `references/protocol.md`, a refuted frozen candidate is terminal for
  the run — not repaired, reworded, or re-frozen. A corrected mechanism is a new candidate in a later
  `solve` round, with these constraints in the manifest: non-digit printed folios are legitimate map
  data; no fix hint may instruct writing `none`; the permission roster and the leakage exemption are
  different sets; a schema-exhibit predicate must tolerate indentation and inline-code delimiters.
- **Cross-file proposals: 3** (never applied by this skill).
  - **P-1** `CLAUDE.md` → Bullet Markers: state the canonical position, plus a worked example.
    **Applied** — on the user's explicit instruction, outside the council's autonomy (the council
    itself may not write `CLAUDE.md`). The example is written at column 0 inside a fenced block, so it
    satisfies the `^`-anchored enforcing pattern; verified after the edit. Battery re-run afterwards
    returns its 2-finding pre-existing baseline and the 46-test suite passes.
  - **P-2** `CLAUDE.md` → Audit preconditions enumerates the schema-integrity class by name. Any
    future gating variant needs that sentence amended. User declined gating; filed for the record.
  - **P-3** `audit/SKILL.md:84` should be narrowed — it claims consistency runs capacity, integrity,
    and stale-entry checks on the curated data files; none exist, and this run added none.

## Value over the skill-linter baseline

The five deterministic scanners found two pre-existing style findings and nothing about either named
problem. The council found three unnamed defects, resolved one measurement ambiguity, and — decisively
— the paired refuters killed three candidates that a single-context pass would have shipped, one of
which would have corrupted the pagination map. On this run the depth paid for itself.

## Self-report

Three limitations, all genuine to this run.

1. **The orchestrator put two in-folder decisions to the user that the council machinery existed to
   settle.** Coverage breadth and the `synonym-ignore.md` repair are pure in-folder edits; evaluators,
   chairs, and refuters were the sanctioned deciders. The prompt was context economy, not judgement.
   Worse, one of the two questions carried a wrong premise — it described adding `synonym-ignore.md`
   as "restoring the exemption your schema says it should have," which the EDIT 1 refutation then
   showed to be a category error. Asking the user to ratify a mis-framed option is a strictly worse
   failure than spending the subagents. The upgrade: Step 1 should compute a subagent budget for the
   whole run — advisors + evaluators + chairs + refuters — and if the budget cannot cover the gates,
   narrow the problem manifest up front rather than shedding gates later and back-filling with user
   questions.
2. **The Step-3 evaluator panels and Step-4 chairs were never run.** The run went from Step-2
   generation straight to meta-chair selection and Step-6 refutation, so candidates were never judged
   by fresh evaluators blind to their authorship, and no chair arbitrated. The refuters caught the
   three defects anyway, which is evidence the gate is load-bearing — but the eligibility floor
   (three explicit HOLDs, zero REFUTEs, in each healthy panel) was never applied, so no candidate in
   this run was ever *eligible* under the skill's own contract. `solved-no-survivor` is the honest
   result and would have been reached regardless, but a run that skips a quorum gate should say so in
   its frontmatter, not only its prose. The upgrade: add an `evaluators:`/`chairs:` count to the report
   frontmatter (done here) and have the skill refuse to record any candidate as *applied* when either
   count is zero.
3. **The frozen ledger condensed 30 candidates to 8 design-level mechanisms rather than 30
   implementation-complete C_IDs.** The protocol's freeze is meant to preserve each candidate's exact
   implementation so evaluators judge the thing that would be written. Condensing was a context
   decision, and it is why the three refuted edits had to be re-authored by the orchestrator from
   converged designs rather than lifted verbatim from a generator — which is precisely where the
   roman-numeral gap and the `^`-anchor gap entered. The upgrade: the freeze should write each
   candidate's implementation to disk as its own file at Step 3 and pass paths, so the ledger never
   has to fit in the orchestrator's context and no candidate is ever paraphrased into the slate.
