---
name: skill-linter
description: Reviews a SKILL.md (or skill directory) against Anthropic's skill-authoring best practices and acts autonomously — applies every actionable fix at every severity inside the linted skill's directory and iterates full passes until two consecutive runs find nothing left to apply; surfaces cross-file findings (CLAUDE.md, other skills, shared files) as proposals. Writes a report to 2-outputs/skill-linter/. Use whenever the user asks to lint, audit, review, check, validate, critique, or improve the quality of a skill, SKILL.md, skill folder, or .skill bundle — even without the word "lint" (e.g., "what's wrong with my-skill?", "is this SKILL.md any good?", "give me feedback on this skill"). Also use when the user asks whether a skill follows best practices (vague description, too long, nested references, first-person language, time-sensitive info, Windows paths). Lints SKILLS, not wiki pages — for a 1-wiki/ page or note use lint; for a deep multi-agent skill review use skill-llm-council.
---

# Skill linter

Review a skill against Anthropic's best practices and produce a lint report. Combine deterministic Python checks with judgement-based reading. The report groups findings by severity, points at exact file:line locations, and suggests a concrete fix for each. After producing the report, the skill acts autonomously: it applies in-scope fixes and iterates to convergence (Steps 5-6), and surfaces cross-file findings as proposals rather than auto-applying them.

## Purpose

Skill-linter keeps an individual skill well-formed and best-practice-compliant without a deep multi-agent review: deterministic scripts catch mechanical drift, and a judgement checklist catches what pattern-matching misses.

## When To Invoke

Use whenever the user asks to lint, audit, review, check, validate, critique, or improve the quality of a skill, SKILL.md, skill folder, or `.skill` bundle — even without the word "lint" ("what's wrong with my-skill?", "is this SKILL.md any good?", "give me feedback on this skill"). Also use when the user asks whether a skill follows best practices (vague description, too long, nested references, first-person language, time-sensitive info, Windows paths).

## When Not To Invoke

- The target is a wiki page or note under `1-wiki/`. Use `lint`.
- The user wants a deep, multi-angle review of a skill — many independent reviewers arguing over it. Use `skill-llm-council` (heavier and slower).
- The user wants a project-wide schema and skill consistency check. Use `consistency`.

## Procedure

```
Lint Progress:
- [ ] Step 1: Load memory; resolve and validate the input path
- [ ] Step 2: Run deterministic checks (check_structure.py, check_synonyms.py, check_musts.py, check_h2_case.py, check_kwargs.py)
- [ ] Step 3: Read SKILL.md and reference files for judgement-based checks
- [ ] Step 4: Compile the lint report (lint-report.md)
- [ ] Step 5: Auto-apply every actionable fix within the skill directory; surface cross-file findings as proposals
- [ ] Step 6: Iterate full passes until two consecutive runs return zero actionable findings
```

1. **Load memory, then resolve and validate the input path.**

   First read `.claude/skills/skill-linter/skill-linter-memory.md` and `.claude/skills/multi-skill/multi-skill-memory.md` to apply prior corrections about which findings have been accepted as project conventions (e.g., the H2 title-case rule), what counts as a cross-file proposal vs. in-scope fix, and any tuning the user has applied to the autonomous behaviour. Then auto-detect what the user pointed at:

   - **Directory** containing `SKILL.md` → lint the whole skill (frontmatter + body + bundled files like `scripts/`, `references/`, `assets/`).
   - **File** ending in `SKILL.md` → lint just that file: pass `--single-file` to `check_structure.py` (Step 2), give the other scanners the bare `SKILL.md` path with no flag, and skip `check_kwargs.py`. Bundled-file checks are skipped: reference traversal, `check_kwargs.py`, and `broken_inline_ref` (inline-path resolution runs in directory mode only, so a broken inline-code path in the SKILL.md body is not caught in single-file mode). Note these skips in the report header.
   - **`.skill` bundle** (zip) → unzip into a temp directory first, then treat as a directory.

   If the path doesn't exist or doesn't contain a SKILL.md, stop and tell the user. Don't lint the wrong thing.

   Then check the target's git state with `git status --porcelain -- <resolved-skill-path>` (scoped to the target, so unrelated churn elsewhere in the repo does not trip the gate) before any fix is applied. Step 5's "preserved by git history" safety net only covers committed state, so if the linted skill's files have uncommitted changes (common — the user just edited the skill and asked what's wrong with it), do not silently auto-apply on top of them: surface the dirty paths and ask whether to proceed, stash, or commit first. skill-linter does not rely on any git outside this repo, and a temp-unzip is discarded after the run, so an external directory or an unzipped `.skill` bundle is always propose-only regardless of whether it happens to be independently version-controlled — see Step 5's out-of-repo rule.

2. **Run deterministic checks.**

   Execute the script and parse its JSON output from stdout. Don't try to reimplement these checks by reading — the script is faster and more reliable. Invocations are path-qualified from the repo root (cwd is the repo root and resets between bash calls, so a bare `scripts/...` path fails), matching the sibling `lint` skill, and read stdout directly rather than redirecting to scratch files.

   **Capture the exit code and stderr on every invocation** — e.g. append `; echo "EXIT=$?"`. A run succeeded only when it exits 0 AND prints a JSON array to stdout. Any non-zero exit, or empty/non-JSON stdout, means the scanner did not run (a bad path, a missing SKILL.md, a layout mismatch when the linter was copied elsewhere) — surface the stderr text as a hard error and do not count that check as clean. An exit-2 empty stdout is a failed run, not a clean `[]`. These five scanners exist because judgement-only review reliably misses mechanical drift — terminology slips, bare imperatives, reference-file headings, call sites scattered across scripts — once richer findings compete for attention; run all five every pass.

   ```bash
   # Full skill directory
   python3 .claude/skills/multi-skill/scripts/check_structure.py <skill-path>

   # Single SKILL.md file (skips reference traversal)
   python3 .claude/skills/multi-skill/scripts/check_structure.py <path-to-SKILL.md> --single-file
   ```

   Pass `--single-file` only when the user explicitly pointed at a single SKILL.md file rather than a directory; without the flag the script also examines any `references/*.md` file that SKILL.md links as a Markdown hyperlink (a bracketed label with a parenthesized `.md` target), rather than as an inline-code path. Three of its reference-structural checks (`broken_md_link`, `nested_reference`, `missing_toc`) key on that hyperlink syntax, so a skill that cites its references only as inline-code paths gets no *depth/TOC* coverage from those three — but `broken_inline_ref` (added for this repo's inline-code citation style) does verify those inline-code skill paths resolve on disk, including the abbreviated bare `<skill>/<file>.md` form that drops the `references/`/`scripts/` segment, scanned across SKILL.md and every `references/*.md`. That scan runs only in directory mode against a CLAUDE.md-rooted repo; it is skipped, with no finding, in single-file mode or when no repo root is found. `check_h2_case.py` globs every `references/*.md` sibling directly. `check_structure.py` produces a JSON list of structural findings. Each finding has `severity`, `check_id`, `file`, `line`, `message`, and `fix_hint`. See `.claude/skills/multi-skill/references/skill-authoring-checks.md` for the complete list of what this script checks and the severity each check uses.

   Then run the synonym-candidate scanner:

   ```bash
   python3 .claude/skills/multi-skill/scripts/check_synonyms.py <skill-dir-or-SKILL.md>
   ```

   This script flags pairs of near-synonyms appearing in the body (for example, "image" / "photo" / "picture"). It uses `check_id: terminology_candidate` because each candidate needs your judgement: terms that look like synonyms might genuinely refer to distinct things in this skill's domain. For each candidate, decide:

   - **Real inconsistency** (the terms refer to the same thing) → keep as a `suggestion` finding, ideally promoted to `check_id: inconsistent_terminology`, with a fix that picks one term.
   - **Intentional distinction** (the terms refer to different concepts) → drop the candidate, and append the confirmed-distinct group under the target skill's `## <skill-name>` section in the shared `.claude/skills/multi-skill/synonym-ignore.md` (keyed by the linted skill's name; create the file or the `## <skill-name>` heading if a fresh install lacks it) so future runs auto-suppress it instead of re-surfacing the same false positive every pass. Record the minimal confirmed-distinct subset actually present, not the whole synonym group: a listed group suppresses every sub-pair within it, so an over-broad entry can mask a later genuine inconsistency among terms you did not mean to clear. See `.claude/skills/multi-skill/references/skill-authoring-checks.md` → Synonym Candidate Scan for the mechanism.

   Then run the heavy-handed-imperative scanner:

   ```bash
   python3 .claude/skills/multi-skill/scripts/check_musts.py <skill-dir-or-SKILL.md>
   ```

   This script flags ALL-CAPS directives (`ALWAYS` / `NEVER` / `MUST` / `DO NOT`) in body paragraphs that don't contain a nearby explanation cue (e.g. `because`, `to avoid`; the full cue set is in `.claude/skills/multi-skill/references/skill-authoring-checks.md`). The check uses `check_id: heavy_handed_must_candidate` for the same reason as the synonym scanner: a script can detect *that* the imperative is bare, but you have to decide *whether* the missing reasoning matters. For each candidate:

   - **The why is non-obvious** → keep as a `suggestion` finding (ideally promote to `heavy_handed_musts`), with a fix that adds the reasoning. Models follow well-justified rules more reliably than bare directives.
   - **The why is obvious from context** → drop the candidate. Not every directive needs a "because"; some rules are self-evident.

   Then run the H2 title-case scanner across SKILL.md and every `references/*.md`:

   ```bash
   python3 .claude/skills/multi-skill/scripts/check_h2_case.py <skill-dir-or-SKILL.md>
   ```

   This script flags sentence-case H2 headings (`## Worked example`) and proposes the title-case rewrite (`## Worked Example`). It uses `check_id: h2_heading_case` and severity `suggestion`. Unlike the synonym and musts scanners, an `h2_heading_case` finding is actionable on its face — not a keep-vs-drop decision on the whole candidate. The H2 title-case rule (see `.claude/skills/multi-skill/references/skill-authoring-checklist.md`) applies uniformly to `SKILL.md` AND every reference file. Among the terminology, imperative, and heading scanners, only `check_h2_case.py` extends to `references/*.md` siblings (and only in directory mode — handing it a single `references/*.md` path exits 2); `check_synonyms.py` and `check_musts.py` scan `SKILL.md` only and reject any other file path, so terminology and bare-imperative coverage of the reference files is judgement-only (Step 3), not a scanner pass — do not point those two scanners at a reference file expecting a clean run. Its one judgement call is the code-token carve-out (the full rule is in `.claude/skills/multi-skill/references/skill-authoring-checklist.md` `h2_heading_case`): the script only skips words whose first character is non-alphabetic, so a bare code token starting with a letter (`## Run check_structure.py first`) is still flagged — title-case only the natural-language words, leave the code token untouched, and drop a finding whose only change would be re-casing that token (so although `h2_heading_case` is otherwise auto-applied as mechanical at Step 5, a code-token-only finding is dropped, not applied).

   Then run the keyword-argument scanner across every `scripts/*.py`:

   ```bash
   python3 .claude/skills/multi-skill/scripts/check_kwargs.py <skill-path-or-scripts-dir>
   ```

   In single-file mode, pass the SKILL.md file path to `check_synonyms.py`, `check_musts.py`, and `check_h2_case.py` (each accepts a file); `check_kwargs.py` returns an empty result for a single SKILL.md since it scans only `scripts/*.py`, so it may be skipped.

   This script AST-walks every Python file under `scripts/` and flags positional calls to bare-name functions that are not in the allow-list (built-ins, exception constructors, and stdlib helpers like `Path`, `datetime`, `Counter`). It uses `check_id: positional_call` and severity `error` because `coding-best-practices.md` lists keyword-argument-only calls as a hard project rule. Attribute calls (`obj.method()`, `module.func()`) are always allowed.

3. **Read for judgement-based checks.**

   Some best-practices issues require reading the skill, not pattern-matching. Open `SKILL.md` (and any `references/*.md` files referenced from it) and apply the rubric in `.claude/skills/multi-skill/references/skill-authoring-checklist.md`. That file lists each judgement check, what to look for, what to flag, what severity to assign, and how to phrase the fix suggestion.

   Apply the full checklist on every lint pass, including for requests that sound narrowly scoped. If the user said "just check the description and workflow", that's a hint about what they care about most, not permission to skip everything else. A linter that only checks what the user asks about will miss the issues they didn't know to ask about, which defeats the point.

   Common judgement checks include: vague descriptions, missing "when to use" cues, abstract rather than concrete examples, inconsistent terminology, time-sensitive info, magic numbers in scripts, and over-formatted MUSTs that should explain *why* instead. Use your judgement: don't flag something as a problem unless you can articulate why it would hurt a real user. If a finding is a close call, mark it `suggestion` rather than `warning`.

   Project rule sets: when linting a skill inside a project that ships its own writing and coding rules, also apply those rule sets (they take precedence over generic skill-authoring style for body prose and bundled scripts):

   - AI-writing tells: if `a-archive/style/ai-writing-tells.md` exists at the repo root, read it and flag instances of the listed tells in the SKILL.md prose and any `references/*.md` files (banned vocabulary, em-dash density, conclusion templates, puffing tone, citation-markup leakage, placeholder leakage). Mechanical tells → `warning`; semantic tells (puffing, conclusion templates) → `suggestion`. Cite `ai-writing-tells.md` in the fix hint so the user knows which rule set the finding came from.
   - Best coding practices: if `a-archive/style/coding-best-practices.md` exists at the repo root, read it and review every Python file under the skill directory (`scripts/*.py`, etc.) against it. Flag deviations from the rules the user has marked as theirs (single quotes, mandatory keyword arguments, mandatory type hints with PEP 585/604 syntax, NumPy-style docstrings, inline comments above the code, the testing layout) as well as the verbatim PEP 8/257 rules. Mark per-file path:line. Severity: `error` for outright violations the user has flagged as hard rules (e.g. missing type hints, positional args at a call site that has kwargs available); `warning` for stylistic deviations; `suggestion` for borderline judgement calls. Cite `coding-best-practices.md` in the fix hint.

   These passes only run when the rule files exist; outside this project, skip them silently.

   Append each judgement finding to the same in-memory list of findings as the script produced (same schema), so the compile step is uniform.

4. **Compile the lint report.**

   Write the report to `2-outputs/skill-linter/skill-linter-YYYY-MM-DD-HHMM-{skill-name}.md` (project convention: `{type}-YYYY-MM-DD-HHMM-{description}.md` so reports sort by date alongside `consistency`, `audit`, `lint`, etc.). Obtain the timestamp at write time by running `TZ='UTC' date '+%Y-%m-%d-%H%M'` — the session context provides the date but not the current minute. The `{skill-name}` segment is the linted skill's folder name (or, for a single-file lint, the SKILL.md's parent folder name). For a `.skill` bundle — and as a fallback whenever the resolved folder name is a temp directory that does not map to a real skill — derive `{skill-name}` from the `name:` field in the (unzipped) SKILL.md frontmatter, not the temp folder name, so the report's `{skill-name}` segment names the real skill rather than a temp directory. If multiple lints of the same skill happen in the same minute, append a disambiguating suffix from the allow-list — never overwrite a prior dated report. Allowed suffixes, in order of preference: `-rerun` (re-running with no changes since the prior report), `-after-fixes` (after applying fixes from the prior report), or `-N` ordinal (`-2`, `-3`, ...) when neither label fits. Pin to this list so a future search across the report folder is predictable. Reports accumulate here and are not auto-pruned; the folder is uncapped (CLAUDE.md → `2-outputs/`).

   If skill-linter is invoked outside a project that has a `2-outputs/skill-linter/` folder, fall back to writing `<skill-dir>/lint-report.md` next to the skill being linted; mention the fallback in the chat reply so the user knows where the file went.

   Path hygiene: `target_path:` (frontmatter) and `Path:` (report body) must be repo-relative, starting with `./` (e.g., `./.claude/skills/lint/`, not `/Users/{name}/Documents/llm-wiki/.claude/skills/lint/`). Convert any absolute path the user supplies to repo-relative before writing. When the linted skill lives outside this repo (a directory the user pointed at elsewhere, or a `.skill` bundle), there is no repo-relative form — write the path with the home directory abbreviated to `~` so the username still stays out of the committed report, and for a bundle record the original `.skill` file path the user supplied, not the temp-unzip location. This keeps the user's home-directory path (which often contains a username) out of the committed report. Same rule for the `File:` field on each finding bullet: write `SKILL.md:42` or `references/<file>.md:120`, not the absolute equivalent.

   Use this exact structure — it's what makes the report scannable and what makes per-finding fix-application possible later.

   ```markdown
   ---
   type: skill-linter
   date: {YYYY-MM-DD}
   target: "{skill-name}"
   target_path: "{resolved-path}"
   errors: {N}
   warnings: {N}
   suggestions: {N}
   ---

   # Lint report: {skill-name}

   Path: `{resolved-path}`
   Checked: {YYYY-MM-DD}
   Summary: {N errors}, {N warnings}, {N suggestions}

   ## Errors

   ### E1. {short title}
   - File: `SKILL.md:42`
   - Check: `{check_id}`
   - Issue: {one-sentence description}
   - Fix: {concrete suggested fix}

   ## Warnings

   ### W1. ...

   ## Suggestions

   ### S1. ...

   ## Applied

   - {finding ID} — {one-line what was applied}

   ## Skipped

   - {finding ID} — {report-cited reason}

   ## Cross-file proposals

   - {finding ID} — {target path}: {exact proposed edit}

   ## Self-report
   - {a specific limitation that bit skill-linter this run — a check it lacked, a false positive/negative, a fix it couldn't safely apply in-scope} → upgrade: {how the skill-linter skill should change} (or the single line: none noted this run; per `.claude/skills/multi-skill/references/self-report.md`)
   ```

   The `## Errors` / `## Warnings` / `## Suggestions` sections are the found-state record (written at Step 4, pre-fix). The `## Applied` / `## Skipped` / `## Cross-file proposals` sections carry the action taken on each finding by ID; write them as `_Pending — populated after Step 6 convergence._` at Step 4 and fill them once the loop converges (see Step 6). Write one report file per invocation and update it in place across loop iterations — do not re-derive the timestamp or write a new dated file each pass.

   Frontmatter is required so the report sits alongside other dated outputs (lint reports, consistency reports, audit reports) with the same dated-filename convention and per-severity count frontmatter. (Unlike `lint` and `consistency`, this report carries no machine-readable `result:` gate field, because nothing downstream reads it — `audit` and `checkup` do not consume skill-linter reports.)

   Number findings within each severity (`E1`, `E2`, `W1`, `W2`, `S1`...) so the user can refer to them by ID when reading the closing summary. If a severity has no findings, write "_None._" under the heading rather than dropping the section — the consistent shape helps the user trust the lint pass was thorough.

   If there are zero findings overall, still write the report with all three sections empty and a one-line summary saying the skill passes the checks. Don't skip writing the file.

5. **Auto-apply every actionable fix within the skill directory; surface cross-file findings as proposals.**

   Split the report's findings into two classes by **scope**, not severity:

   - **In-scope** — the fix touches only files under the linted skill's folder: its `SKILL.md`, `references/*.md`, `scripts/*.py`, or `assets/*` — but never the skill's own `*-memory.md` or an agent-curated data file (e.g. a `hyphenation-lists.md`), which are append-only / user-curated per CLAUDE.md → Stay In Your Lane and are surfaced as proposals, not auto-edited. (The one exception is the shared `.claude/skills/multi-skill/synonym-ignore.md`: appending a confirmed-distinct terminology group there (Step 2) is autonomous bookkeeping that captures the keep-vs-drop judgement the skill already makes on a `terminology_candidate`, the same autonomy by which `audit` grows lint's ignore lists — though skill-linter's append is single-context self-judged, not sub-agent-verified. It is the one shared-folder file skill-linter writes, keyed by the linted skill's name: sanctioned agent-writable data, never a finding-fix or a cross-file proposal, whichever skill is being linted.) Apply every in-scope finding at every severity (errors, warnings, suggestions alike) in the smallest reasonable edit, without asking. Exception: when the linted skill lives outside this repo (an external directory or an unzipped `.skill` bundle), the "preserved by git history" guarantee does not hold and a temp-unzip is discarded after the run, so treat those targets as propose-only — write the fixes into the report and ask before editing, never silently. This covers:
     - Mechanical / deterministic findings from `check_structure.py` whose fix is a determinate rewrite (frontmatter schema, Windows paths, raw HTML, process substitution, H2 case, and broken Markdown-hyperlink targets). Detected and mechanically remediable, so apply them.
     - Judgement-heavy findings from the checklist (vague descriptions, terminology drift, inline-header bold, em-dash density, magic numbers, heavy-handed imperatives) and from the project rule sets (`ai-writing-tells.md` tells, `coding-best-practices.md` deviations). When rewriting a `description:`, preserve every existing trigger cue (the natural-language phrasings that make the skill fire) — the deterministic checks only confirm the new description isn't vague / first-person / too-long, none of which catches a rewrite that silently dropped a trigger and left the skill undiscoverable. So before applying a description rewrite, diff the trigger phrasings of the old and new text and confirm every old cue survives (a renamed sibling or a "use X instead" pointer counts as a cue); record that old-vs-new cue diff on the rewrite's `file:line — old → new` Applied line. If the rewrite would drop a cue you cannot otherwise preserve, do not auto-apply it — surface it as a held finding for the user, since a lost trigger is higher-cost than a vague description.
     - Scanner candidates (`terminology_candidate`, `heavy_handed_must_candidate`): make the judgement call yourself — keep as a real finding and apply the fix, or drop and note in the report. Do not ask the user.
     - Detected-but-judgement-to-remedy findings (`body_over_length`, `broken_inline_ref`): deterministically detected, but the fix needs judgement, so surface them rather than blindly auto-applying. For `body_over_length`, relocating detail into `references/` is a judgement-heavy refactor, not a smallest-reasonable edit: surface it as a held finding with a proposed extraction plan rather than trimming the body toward the threshold across passes. For `broken_inline_ref`, a path that resolves nowhere is either a genuine broken skill-infra reference (fix it, or surface it when the fix is cross-file) or an illustrative teaching path in prose (drop the finding; never rewrite correct prose or fence a deliberate example): make that keep-vs-drop call yourself, as with `terminology_candidate`. A held or dropped finding here is a dispositioned no-action verdict, so it does not block Step 6 convergence.

   - **Cross-file** — the fix would touch files outside the linted skill's directory: `CLAUDE.md`, `README.md`, another skill's folder, `.claude/skills/multi-skill/multi-skill-memory.md`, `a-archive/`, or shared scripts. Never auto-apply. Rewrite the finding's `Fix:` line as a concrete proposal (target path and the exact edit), prefix the finding's title with `[cross-file]`, and leave the report showing the finding was surfaced rather than applied. The cross-file boundary is shared with `consistency`; the in-folder autonomy is not — `consistency` surfaces every skill-file finding as a proposal, while skill-linter's mandate is to fix the one skill the user invoked it on, so that skill's own directory is in-scope.

   A finding that spans both scopes is split: apply the in-skill portion under the in-scope posture and surface the cross-file portion as a separate `[cross-file]` proposal naming the external edit the in-skill change depends on. Don't hold the in-skill half hostage to the cross-file half, and never auto-apply the external edit; note the split in the report.

   When a finding offers multiple options ("either (a) or (b)"), pick the option the report labels as preferred, or the lighter-touch option when no preference is stated. When the report explicitly says "Recommended drop", "Optional", or "Defer until X happens", skip the finding and record the decision in the report's closing summary — these are explicit no-action verdicts, not pending judgement.

   Auto-apply is gated by the Step 1 dirty-tree check: on an uncommitted or out-of-repo target there is no git safety net, so those stay propose-only (never auto-applied without the user's go-ahead). After any edit to a script under `scripts/`, run that script once against the skill being linted and confirm it exits 0 and emits parseable JSON before counting the pass clean — re-running the pattern-matchers alone does not prove an edited script still works (a kwargs rewrite that guessed the wrong parameter name passes the scanner but breaks the script). When reporting back to the user, link to the report and give a per-severity tally of what was applied, what was skipped (with the report-cited reason), and what was surfaced as a cross-file proposal. Because the in-folder files are soft-read-only (CLAUDE.md → Stay In Your Lane), every applied **judgement-level** edit (a description rewrite, terminology standardization, an AI-writing-tell re-voicing, a heavy-handed-must reframing) is also listed as `file:line — old phrasing → new phrasing`, one line each, so the auto-applied prose changes are reviewable rather than a bare count — this is the "summarize the diff" the project safety rules require. Purely mechanical fixes (schema, Windows paths, broken links, H2 case, kwargs) stay as counts.

6. **Iterate full passes until two consecutive runs return zero actionable findings.**

   An **actionable** finding is an in-scope finding not yet applied or dropped; surfaced cross-file proposals and already-dropped or skipped candidates are not actionable and never block convergence. When the target is propose-only (an out-of-repo or `.skill`-bundle target per Step 5, or an uncommitted tree the user declined to commit at Step 1), the loop does not auto-apply: run one full pass, write every fix as a proposal, and skip the two-clean-pass convergence requirement — there is nothing to converge when nothing is applied.

   This is a loop, not a single closing re-run:

   1. Apply every in-scope fix from Step 5, each in the smallest reasonable edit.
   2. Re-run the **full skill-linter pass** as one independent run: all five deterministic scripts (the path-qualified `python3 .claude/skills/multi-skill/scripts/check_structure.py`, `check_synonyms.py`, `check_musts.py`, `check_h2_case.py`, `check_kwargs.py` invocations from Step 2 — in single-file mode keep the same single-file argument forms from Step 2, not directory traversal) plus the judgement-based reading from Step 3 and the project rule-set checks from Steps 3-4. A fresh full pass over the whole skill, not an incremental re-check of the lines just edited. A fix can introduce drift in a check it did not touch, and a judgement-level rewrite can re-trigger a deterministic check downstream.
   3. If the pass surfaces new actionable findings (anything in-scope at any severity), apply them and return to step 6.2.
   4. A pass is clean when the full re-run finds **zero remaining actionable in-scope findings after Step 5 disposition** — not when every scanner literally prints `[]`. The two differ: `check_structure.py` and the judgement checklist routinely surface standing warnings and suggestions on a real skill, and after you apply or drop each one, a re-run can still print findings that are already dispositioned (a dropped `terminology_candidate`, a surfaced cross-file proposal). Clean means nothing new is left to apply in-scope, not that the raw scanner stdout is empty. Each deterministic script must still have *run* successfully — exited 0 with a JSON array (`[]` is the valid-JSON example of a scanner that itself found nothing); a non-JSON stdout with a non-zero exit (an exit-2 result) is a failed run, not a clean pass, and blocks convergence. A scanner legitimately skipped (`check_kwargs.py` in single-file mode, or any scanner on a target with no `scripts/`) is vacuously clean, not a failed run. The judgement checklist plus project rule sets must report nothing new to apply. Surfaced cross-file proposals and explicitly dropped / skipped "Recommended drop" / "Optional" findings are surfaced output, not drift, and do not block convergence.
   5. The loop converges only after **two consecutive clean passes** — even after a clean pass, run one more. The first shows the skill settled after the last fix; the second guards against the agent itself running a pass incompletely or misreading its output. An unchanged set of surfaced cross-file proposals across passes does not block convergence.

   Shared-scanner caveat: the deterministic scanners live in `.claude/skills/multi-skill/scripts/` and the rubric in `.claude/skills/multi-skill/references/` — shared infra, so a fix to either is a cross-file change (surfaced as a proposal, not auto-applied), but were one applied it changes the scanner the loop re-runs; the two-clean-pass counter — which the loop already resets on any applied fix — therefore measures convergence against the post-edit scanner. Before trusting a modified scanner's output, run it against an input you know it should flag (a deliberately-broken fixture) and confirm it still flags — an edit that makes a scanner wrongly emit `[]` exit 0 on bad input converges falsely, and the exit-2 guard cannot catch a scanner that incorrectly exits 0. The committed regression suite pins the scanners' load-bearing behaviour and encodes that fixture discipline: `.claude/skills/multi-skill/scripts/tests/test_check_structure.py` covers the ref recognizers (the `broken_inline_ref` bare `<skill>/<file>.md` catch and the fenced-illustrative no-false-positive) and `body_over_length` (fence-counting as intended, and the budget-conditional message tail), and `.claude/skills/multi-skill/scripts/tests/test_check_synonyms.py` covers subset-suppression and the hyphen-preserving rationale split. Run it after any scanner edit: `python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests`. Likewise, when a run appends to the shared `synonym-ignore.md` (Step 2), that data write changes the next pass's suppression; it is monotonic (only confirmed-distinct groups are added, and suppression only drops candidates already adjudicated), so it cannot cause a false convergence, but treat it as a self-edit to the data the scanner reads.

   Bound the loop: stop after 6 iterations (matching `consistency`'s bound — each pass re-reads and re-judges the whole skill, unlike `lint`'s cheaper mechanical-only re-run), or earlier when an iteration makes no progress. Detect "no progress" operationally: record each pass's set of **unresolved in-scope actionable** findings (surfaced cross-file proposals and already-dropped candidates persist by design and are excluded) keyed on `(check_id, file, normalized message)` — not on `line` (applying a fix shifts the line numbers of every later finding, and `line: null` findings such as `terminology_candidate` would collide into one tuple), and not on the `E1`/`W1`/`S1` display IDs (renumbered per pass from the found-state output, so the same residual finding gets a different ordinal across passes). Stop if a tuple-set repeats one seen in any earlier pass — a fixed point (identical consecutive sets) or a cycle (fix A re-triggers B, fix B re-triggers A, presenting as alternating sets). A two-pass oscillation is not "the same findings persisting", so comparing only consecutive passes would miss it. When bounded out without reaching two consecutive clean passes, stop and report the unresolved findings rather than continuing to spin. Rewrite — not merely re-tally — the report's frontmatter counts and its `Applied` / `Skipped` / `Cross-file proposals` sections to the final post-convergence state, so the persisted file describes what was *done*, not only what was *found* (the E/W/S sections stay as the found-state record).

## What The Deterministic Scripts Catch

For the full list with severities and rationales, see `.claude/skills/multi-skill/references/skill-authoring-checks.md`. At a glance: missing/invalid frontmatter, name and description schema violations (length, casing, reserved words, third-person), `SKILL.md` body over the word budget (`SKILL_MD_MAX_WORDS`, ~6500, the primary signal) or 500 lines (`SKILL_MD_MAX_LINES`), both in `.claude/skills/multi-skill/scripts/check_structure.py`, raw HTML tags in markdown prose, bash process substitution `<(...)` in prose (upload-breaking), Windows-style paths in markdown, references nested more than one level deep from `SKILL.md`, reference files over 100 lines that lack a table of contents (see `.claude/skills/multi-skill/scripts/check_structure.py` `REFERENCE_TOC_THRESHOLD`), obviously-broken markdown link targets that point at files that don't exist in the skill directory, and inline-code skill paths that resolve nowhere on disk (`broken_inline_ref`, directory mode only). The four separate scanners (`check_synonyms.py`, `check_musts.py`, `check_h2_case.py`, `check_kwargs.py`) are documented there too.

## Severity Tiers

- **Error** — the skill is technically broken or won't trigger reliably (e.g., missing required frontmatter, invalid name, description over 1024 chars).
- **Warning** — clearly violates a best practice with concrete cost to users (e.g., first-person description, 800-line SKILL.md, two-level nested references).
- **Suggestion** — stylistic or judgement-based improvements (e.g., terminology inconsistency, abstract example, magic number in a script).

When in doubt between two tiers, pick the lower one. False alarms erode trust in the linter faster than missed nits.

## Limits

- Lints skills, not wiki pages — for a `1-wiki/` page or note use `lint`; for a deep multi-agent review use `skill-llm-council`.
- Auto-applies only in-folder fixes (the linted skill's own `SKILL.md`, `references/`, `scripts/`, `assets/`); cross-file findings (`CLAUDE.md`, other skills, shared files) are surfaced as proposals, never auto-applied.
- The git-history safety net covers committed state only; on an uncommitted or out-of-repo target, fixes are surfaced for approval rather than silently applied (Step 1 dirty-tree gate).
