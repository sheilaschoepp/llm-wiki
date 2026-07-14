---
name: consistency
description: Run project-level consistency checks after schema or skill changes. Checks CLAUDE.md, README.md, skill files, wiki page section templates, index/hot/log structure, callout CSS, and scripts for drift from the current schema. Use after a schema change, skill rewrite, feature removal, or major refactor. Also use when the user asks whether a refactor broke anything, whether the project is consistent with its schema, whether a skill or its description still matches the schema after editing a SKILL.md or CLAUDE.md, or to propagate a renamed or moved section, callout, or field across the project. Different from lint and audit, which check individual wiki pages (lint structurally, audit semantically); from checkup, which runs all three together; from cleanup, which checks memory-entry content and prunes unneeded outputs (consistency only counts memory entries against a cap); and from skill-linter, which reviews one skill's authoring quality, not the project's agreement with its schema.
---

# consistency

Check that the project agrees with its own schema.

## Purpose

Consistency is for cross-file drift: old section names, old citation rules, stale skill descriptions, outdated scripts, and missing callout styles.

## Scope

Check:

- `CLAUDE.md`
- `README.md`
- `.claude/skills/*`
- `.obsidian/snippets/custom_callouts.css`
- `1-wiki/hot.md`, `1-wiki/index.md`, `1-wiki/log.md`
- wiki pages under `1-wiki/sources`, `entities`, `concepts`, and `syntheses`
- attachment files under `1-wiki/attachments`

Beyond the deterministic file checks above, the judgment-drift packet (Step 2) reads recently changed `CLAUDE.md`, `README.md`, and skill files for schema and skill drift the scripts cannot settle.

Do not check or modify `0-raw/`.

## When To Invoke

- After changing `CLAUDE.md`.
- After rewriting skills.
- After removing a feature or a skill (to catch dangling references to it).
- After changing page templates or callout sections.
- To propagate a renamed or moved section, callout, or field across the project.
- After changing lint/audit behaviour.

## When Not To Invoke

- Single-page structural check. Use `lint`.
- Semantic note review. Use `audit`.
- One skill's authoring quality (vague description, length, first-person, nested refs). Use `skill-linter`.
- Memory-entry graduation or output pruning. Use `cleanup` — consistency only counts memory against a cap, it never reads or removes entries.
- Research answer. Use `query`.

## Procedure

```text
Consistency Progress:
- [ ] Step 1: Load memory; load the deterministic check manifest
- [ ] Step 2: Run independent check packets
- [ ] Step 3: Return per-packet result format
- [ ] Step 4: Merge packet results
- [ ] Step 5: Fix mechanical drift
- [ ] Step 6: Prepare root-level findings as proposals
- [ ] Step 7: Iterate independent re-runs until two consecutive clean passes
- [ ] Step 8: Save report
- [ ] Step 9: Prepend log entry
- [ ] Step 10: Present proposals to the user
```

1. **Load memory, then load the deterministic manifest.** First read `.claude/skills/consistency/consistency-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` to apply prior corrections about which checks the user has tuned, how aggressively to surface root-level proposals, and any project-specific drift definitions layered onto the schema. Then load the manifest — this shows the available atomic checks and their packet grouping.

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py --list-checks
```

2. **Run independent check packets.** Run packets serially in this assistant — the deterministic script finishes in under a second, so there is nothing to parallelize. Do not rely on tool-specific names or agent-framework features; each packet must return the result format below. The six procedure packets are defined in the subsections that follow; run all of them. A packet is a named group of checks that returns one result block. Five are deterministic (the script packets); the sixth, judgment-drift, is a model reading task with no script command. So `--list-checks` groups its checks under those five script packets — it prints every deterministic check (27 today), not five.

### Packet: schema-language

Checks stale schema prose, retired feature mentions, skill-count drift, the Operations-list-vs-folders match, references routing to merged-away skill names, and whether the script's `EXPECTED_SECTIONS` matches the `CLAUDE.md` callout lists. See `references/checks.md` for the per-check roster and scope (`catalogue_matches_manifest` keeps that catalogue equal to the script) — do not re-enumerate the checks here, as an in-SKILL roster is unguarded and drifts.

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py . --packet schema-language
```

### Packet: wiki-pages

Checks wiki page placeholders, section order, source venue/year fields, and index-vs-files drift.

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py . --packet wiki-pages
```

### Packet: styles-files

This packet carries the highest-stakes scans in the battery — the personal-info, identity-term, and domain-literature leakage checks — alongside callout CSS, `.gitkeep`, path/filename resolution, orphan scripts, the directory-tree drift check, and the memory-file graduation counter. See `references/checks.md` for per-check scope.

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py . --packet styles-files
```

### Packet: ai-writing-tells

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py . --packet ai-writing-tells
```

Implemented as `ai_writing_tells`: scans project-documentation prose for mechanical AI-writing tells, source list `a-archive/style/ai-writing-tells.md`. See `references/checks.md` for the file set, the self-skip list, and the severity mapping. Semantic tells (puffing tone, broader-context reflex) are out of scope; review the documentation directly when needed.

### Packet: naming

```bash
python3 .claude/skills/consistency/scripts/check_consistency.py . --packet naming
```

Implemented as `file_naming_consistency` (plus `output_kinds_match_disk`): verifies kebab-case wiki pages, attachments, and skill folders, and the `{kind}-YYYY-MM-DD-HHMM(-extra)?.md` output-file convention. See `references/checks.md` for the exact patterns, the `OUTPUT_KIND_DIRS` roster, and the `synthesis` / `quarantined` / `superseded` / `mock-defence` exemptions. Raw sources under `0-raw/` are user-curated and exempt.

### Packet: judgment-drift

Review recently changed `CLAUDE.md`, `README.md`, skill files, scripts, and visible wiki control pages for schema decisions the deterministic checks cannot settle. Bound the read with:

```bash
git diff --name-only HEAD~5 -- CLAUDE.md README.md .claude/skills 1-wiki/hot.md 1-wiki/index.md
```

On a repository with fewer than five commits — a freshly scaffolded vault — `HEAD~5` does not resolve; fall back to `git diff --name-only $(git rev-list --max-parents=0 HEAD)` (against the root commit) or review all the control files directly.

Flag drift like: a skill's frontmatter `description:` no longer matches its `## Purpose` section (e.g., description still names a behaviour the body has dropped, or Purpose introduces a goal the description doesn't surface); `CLAUDE.md` naming a section that a wiki page template no longer requires; severity vocabulary used inconsistently across reports; a skill's "When To Invoke" trigger list that contradicts the description line. Return the same `Result / Commands run / Findings / Judgement calls / Files changed` block as the deterministic packets.

Also run a **domain-leakage sweep** over `CLAUDE.md` and the whole of each skill — not just its `SKILL.md`, but its `references/*` and `scripts/*` too, including function names, variable names, comments, example data, and prose. The generic infrastructure should illustrate itself only with neutral placeholders; flag anything that leaks the vault's own research corpus into reusable infra: research-corpus system or benchmark proper nouns used as substantive examples, domain-specific identifiers baked into code (a function or variable named after the corpus, a hardcoded example drawn from it), domain examples in prose, and substantive claims about the research domain's findings or taxonomy. The deterministic `domain_literature_leakage` check is the bibkey-citation backstop; this sweep covers the forms a regex cannot safely catch. Do NOT flag: generic tooling vocabulary (multi-agent, subagent, council, LLM, agent), the placeholder papers in `PLACEHOLDER_BIBKEYS` (currently `Vaswani2017AttentionIA`, `Kingma2015AdamAM`, `Devlin2019BERTPO` — the example keys a template adopter replaces with their own corpus's; adding real bibkeys means editing that script constant, itself a root-level proposal, or `domain_literature_leakage` flags every real paper), the `*-memory.md` journals (exempt), the standalone skill's folder (`mock-defence` — the `STANDALONE_SKILL_NAMES` set, wiki-orthogonal prep material), tooling-provenance citations that justify a skill's own method (e.g. a deliberation tool built on the deliberation literature it implements), and any instance recorded as sanctioned in `consistency-memory.md`. The standalone skill is exempt structurally (whole folder skipped by the leakage and personal-info checks); any *other* domain-specific skill that legitimately cites the corpus is handled by sanctioning its citations in `consistency-memory.md`, not carved into this generic skill.

Note on description ↔ Purpose: scope asymmetry is expected — `description:` is trigger breadth (exhaustive about scenarios so triage works), `## Purpose` is mission statement (the core thing the skill is for). Flag contradictions, not breadth differences.

Each finding here is a "judgement call" in the packet result and flows into Step 6 as a root-level proposal — never auto-applied.

3. **Return each packet in this format.**

```markdown
### Consistency Packet: {packet-name}
- Result: clean | findings | blocked
- Commands run:
- Findings:
  - `file:line` — issue — proposed fix
- Judgement calls:
- Files changed:
```

Example:

```markdown
### Consistency Packet: schema-language
- Result: findings
- Commands run:
  - `python3 .claude/skills/consistency/scripts/check_consistency.py . --packet schema-language`
- Findings:
  - `CLAUDE.md:142` — stale phrase "literature note" remains after schema rename — replace with "source page"
- Judgement calls: none
- Files changed: `CLAUDE.md`
```

Use `Result: clean` only when the packet's deterministic commands are clean and no manual drift was found. Use `Result: findings` when the packet ran to completion but surfaced drift. Use `Result: blocked` when the packet could not run to completion (missing tooling, unreadable file, permissions error, script failure).

4. **Merge packet results.** Combine findings by file and resolve duplicates before editing. Keep judgement-heavy findings separate from mechanical fixes.

5. **Fix mechanical drift.**
   - Update stale section names in wiki pages. A section-name or callout-order fix is a pure rename/move — never alter callout body content or block IDs while doing it. And because reordering or renaming a callout changes a page's hashed body, do not silently apply it to a `status: verified` page (that would trip the body-hash and demote the page without a record): surface such a page as a finding for `lint`/`audit` to handle under the verification model rather than editing a verified body here.
   - Add missing callout CSS for new slugs.
   - Update README if the user-facing summary no longer matches `CLAUDE.md`.
   - Skill descriptions that mention old citation behaviour, and scripts that no longer match the required sections, are skill/script drift — a Step 6 proposal, not an auto-fix (the autonomy boundary is stated in Step 6).

6. **Prepare root-level findings as concrete proposals.** Drift in `CLAUDE.md`, a skill file, or a script is never auto-fixed, because the schema and the skills change only on the user's explicit say-so. For each such finding, and for any judgement call that could be resolved by changing the schema or a skill, prepare a concrete proposed change: the exact edit, not just a description of the drift. Do not ask mid-run; these proposals are presented together at the end (Step 10).

   - Autonomy boundary: schema, skill, and script files are never auto-edited — every finding becomes a concrete proposal surfaced to the user in Step 10. The boundary is decision type, not only file identity: a change to an auto-fixable file (README, a control page) that would settle a schema or skill question — rewording a user-facing behavioural claim, choosing between two readings of the schema — is a proposal, not an auto-fix; when a finding's target is genuinely ambiguous (a control file that is part-regenerated, part-curated), default to a proposal.

7. **Iterate independent re-runs until two consecutive passes are clean.** This is a loop, not a single closing re-run:

   1. Re-run the full deterministic script as one independent pass: a fresh complete run over the whole project, not an incremental re-check of only the lines you just edited. A mechanical fix can break a check it did not touch, so the pass must be whole.

   ```bash
   python3 .claude/skills/consistency/scripts/check_consistency.py .
   ```

   2. If the pass surfaces auto-fixable mechanical drift (in a wiki page, the callout CSS, `.gitkeep`, index-vs-files, README), fix it (step 5) and surface any new judgement calls (step 6), then return to 7.1.
   3. A pass is clean when an independent full pass leaves the auto-fixable partition empty (the script still exits 1 while non-blocking findings remain — exit 1 is not the not-clean signal). Four kinds of finding do not block convergence, because the skill cannot resolve them itself: surfaced judgement calls; surfaced root-level proposals — classify these by the finding's target `file`, not a memorized check-id list: a finding whose `file` is `CLAUDE.md`, any path under `.claude/skills/` (a skill file or a script), or `(internal)` (a crash/wiring finding whose fix is in the script — it also signals `blocked`, see Step 8) is root-level, never auto-fixed; and findings recorded as sanctioned in `consistency-memory.md` (e.g. a `domain_literature_leakage` hit on content the memory marks accepted) — surfaced as sanctioned, never as drift and never as a proposal to remove them; and advisory findings the skill only counts and is structurally forbidden from acting on — a `memory_file_graduation_prompt` over-cap notice on `MEMORY.md` (memory graduation is `cleanup`'s job, not consistency's) or an `identity_term_leakage` inactive-source notice — surfaced for the user but never blocking, since consistency cannot clear them itself. Surface each once; an unchanged set of these across passes is the settled terminal state, not a reason to keep looping. The pass is `clean except for surfaced proposals` — report the pass as clean (its auto-fixable partition is empty) and carry the proposals to Step 10. One nuance carries to Step 8: a *schema-integrity* proposal (`section_lists_match_schema` or a judgment-drift contradiction) still does not block the loop from converging, but it does set the Step 8 `result:` field to `findings` rather than `clean`, because audit must not run against a schema in dispute.
   4. The loop converges only after **two consecutive clean passes**: even after a clean pass, run one more. The first shows the project settled after the last fix; the second guards against the agent itself running a pass incompletely or misreading its output. The checks are deterministic, but the agent's execution of them is not.

   Bound the loop: stop after 6 iterations, or earlier when an iteration makes no progress (the same findings persist or fixes oscillate). When bounded out without reaching two consecutive clean passes, stop and report the unresolved findings as `Result: blocked` rather than continuing to spin.

8. **Save report** to `2-outputs/consistency/consistency-YYYY-MM-DD-HHMM.md`. Obtain the timestamp at write time with `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context gives the date but not the current minute. If a consistency report already exists for the same minute, do not overwrite it — append a suffix (`-rerun`, `-after-fixes`, or an ordinal `-2`/`-3`), mirroring lint, so a same-minute re-run never silently clobbers the prior report and a standalone `audit` reads an unambiguous newest. A bounded-out run (Step 7) still writes this report and the Step 9 log entry before stopping, so the newest report on disk reflects the `blocked` state, not a stale prior clean one.

   The report must open with this frontmatter — `audit` gates its project-level precondition on the `result:` field (the same way it gates Step 1 on lint's), stopping on `findings` or `blocked`:

   ```yaml
   ---
   result: clean | findings | blocked
   errors: <int>
   warnings: <int>
   suggestions: <int>
   proposals: <int>         # root-level proposals awaiting the user
   judgment_drift: performed | skipped   # was the model-read judgment-drift packet actually run this battery? (`clean` requires performed)
   ---
   ```

   Below the frontmatter, the report body carries: each packet's `### Consistency Packet: {name}` result block (the Step 3 format); a `## Sanctioned (accepted, not drift)` section listing any sanctioned findings with their `consistency-memory.md` entry; a `## Proposals (root-level, awaiting user)` section giving each concrete proposed edit from Step 6 — matching lint's and audit's body specificity, not frontmatter alone; and a `## Self-report` section (per `.claude/skills/multi-skill/references/self-report.md`) — a specific limitation that bit consistency this run (a drift class it could not catch, a false positive, a fix it could not apply) and how the skill should be upgraded, or `none noted this run`.

   The per-severity counts use this skill's `error / warning / suggestion` vocabulary (the same one the judgment-drift packet uses). Set `result: clean` when the loop reached two consecutive clean passes (Step 7) with the auto-fixable partition empty, the judgment-drift packet was actually performed (`judgment_drift: performed`), and no *schema-integrity* proposal is outstanding — an ordinary surfaced root-level proposal (a wording fix, a new skill) does not block `clean`, it is counted in `proposals` (a clean report can carry `proposals:` > 0). Two carve-outs force `findings` instead of `clean`, because each means `audit` would run against ground its precondition exists to protect: (a) an unresolved *schema-integrity* proposal — a `section_lists_match_schema` finding (the `CLAUDE.md` callout templates vs the script's `EXPECTED_SECTIONS`) or a judgment-drift contradiction — says the schema is itself internally inconsistent, so auditing pages against it is exactly what the gate must block; (b) a `judgment_drift: skipped` attestation — that packet is a model read with no deterministic script backstop, so a skipped read must not pass as `clean` on the strength of an exit-0 battery that never covered it. Findings recorded as sanctioned in `consistency-memory.md` are likewise subtracted before computing `result:` and the `errors`/`warnings`/`suggestions` counts: a run whose only non-clean findings are sanctioned (or root-level proposals) is `clean`, with the sanctioned instances listed in the report body under a `Sanctioned (accepted, not drift)` note citing the memory entry — not counted as drift, never proposed for removal. A sanction entry in `consistency-memory.md` is an H2 section — the `check_id`, the exact accepted `file` or string, and a one-line rationale (e.g. `## Sanctioned: domain_literature_leakage — <bibkey> in <path>`, followed by an `Accepted: …` reason line) — which the run matches findings against before subtracting them. The script exits 1 on any finding (including standing proposals and sanctioned hits), so exit 1 is not the not-clean signal. Set `findings` when unsanctioned auto-fixable drift remains unresolved, and `blocked` when the battery did not run to completion — script exit code 2 (a check crashed: an `(internal)` finding on stdout while the rest of the battery still ran, so its coverage is incomplete), or the loop bounded out (Step 7) without two consecutive clean passes.

Derive `result:` from the script's exit code — capture it with `$?` after the final independent pass; do not infer the gate from stdout alone. Exit 2 ⇒ `blocked`, always: a crashed check, broken manifest wiring, OR a malformed invocation (bad path / unknown check / bad `--packet`). The invocation-error case prints nothing to stdout and a message to stderr, so an empty or absent JSON array must never be read as `clean` — that is the trap, since the gate audit depends on would silently pass over a battery that never ran. Exit 1 ⇒ `findings` when unsanctioned auto-fixable drift remains, otherwise `clean` (its only residue is sanctioned hits and root-level proposals — proposals are themselves findings, so a clean-but-with-proposals run exits 1, not 0). Exit 0 ⇒ `clean`. Any loop iteration ending bounded-out or with unresolved auto-fixable drift is `blocked`/`findings`, never `clean`, even if a single pass momentarily showed an empty partition. The enum differs from lint's `clean | blocking`; `audit` reads each skill's own vocabulary. This contract is recorded in `CLAUDE.md` → Audit preconditions and `audit`'s Step 2.

9. **Prepend log entry.** Use the schema's dated-and-timed heading (`## [YYYY-MM-DD HH:MM] verb | subject`, 24-hour UTC from the same `TZ='UTC' date` call as Step 8):

```markdown
## [YYYY-MM-DD HH:MM] consistency | schema/skill check
- Saved: [[2-outputs/consistency/consistency-YYYY-MM-DD-HHMM.md|consistency-YYYY-MM-DD-HHMM]]
- Fixed: [[1-wiki/...|display]] (or "none")
- Proposed (root-level, awaiting user): CLAUDE.md / skill / script change (or "none")
```

10. **Present the proposals.** End the run by presenting every root-level proposal from Step 6 to the user as a concrete, actionable change: the exact edit to `CLAUDE.md`, the skill file, or the script. A proposal must not exist only inside the report or the log. If the user approves one, apply it then, on that explicit instruction. When consistency runs inside `checkup`, the proposals are carried up into checkup's closing summary instead of presented here.

## Deterministic Checks

The script supports `--list-checks` for the live check manifest, `--packet <name>` for a named packet, and `--checks <id,id>` for an exact subset. With no selector, it runs every deterministic check across the five script packets (schema-language, wiki-pages, styles-files, ai-writing-tells, naming).

`--list-checks` and `references/checks.md` are the source of truth for the check roster and per-check scope; `catalogue_matches_manifest` keeps `references/checks.md` equal to the script's manifest. Do not maintain a separate check enumeration here — an in-SKILL.md roster is unguarded and would silently drift. The per-function comments and docstrings in `check_consistency.py` carry the exact behaviour; keep `references/checks.md` aligned when a check is added or changed.

## Tests

The script requires Python 3.10+ (it uses `X | None` unions and built-in generics); the test suite uses Python's stdlib `unittest` (no extra dependency).

Regression tests for the script live in `scripts/tests/test_check_consistency.py` — they pin the wiring invariants, the clean-repo anchor, output determinism, and the specific bug classes (missing-subfolder crash, fence false positives, parser misattribution, output-kind coverage). After changing `check_consistency.py`, run:

```bash
python3 -m unittest discover -s .claude/skills/consistency/scripts/tests
```

## Limits

- Do not read or edit raw sources.
- consistency never edits `CLAUDE.md`, a skill file, or a script. Every finding in those, mechanical or judgement-heavy, is prepared as a concrete proposal and presented to the user at the end of the run (Step 10); the schema and the skills change only on the user's explicit say-so. Every other mechanical fix (missing callout CSS, `.gitkeep`, index-vs-files gaps, stale phrasing in wiki pages, README drift) proceeds without asking.
- Historical output files under `2-outputs/` are not rewritten.
