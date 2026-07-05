# Deterministic Checks Reference

This is the catalogue of checks performed by `scripts/check_structure.py` and the four separate scanner scripts (`check_synonyms.py`, `check_musts.py`, `check_h2_case.py`, `check_kwargs.py`). Each entry lists what triggers the finding, the severity, and the rationale (so you can explain it back to the user when they ask "why is this a warning").

## Contents

- Frontmatter checks (errors)
- Body length and paths (warnings)
- Reference depth and TOC (warnings / suggestions)
- Heavy-handed imperative candidate scan (separate script)
- Synonym candidate scan (separate script)
- H2 title-case scan (separate script)
- Keyword-argument scan (separate script)
- Severity rationale

## Frontmatter Checks

| `check_id` | Severity | Triggers when |
|---|---|---|
| `frontmatter_missing` | error | SKILL.md doesn't open with `---` or has no closing `---`, or the YAML is unparseable. |
| `name_missing` | error | `name:` is absent or empty. |
| `name_too_long` | error | `name` exceeds 64 characters. |
| `name_invalid_chars` | error | `name` is not lowercase kebab-case (only `[a-z0-9-]`, no leading/trailing/double hyphens). |
| `name_reserved_word` | error | `name` contains "anthropic" or "claude" — these are reserved. |
| `description_missing` | error | `description:` is absent or empty. |
| `description_too_long` | error | `description` exceeds 1024 characters. The description is injected into the system prompt; longer text crowds the context budget. |
| `description_xml_tags` | error | `description` contains `<` or `>`. Angle brackets break the prompt-injection step. |
| `description_first_person` | warning | Description uses first/second person ("I can...", "we will...", "you can use this..."). The description is a third-party statement of capability, not a self-introduction. |

## Body Length, Formatting, And Paths

| `check_id` | Severity | Triggers when |
|---|---|---|
| `body_over_length` | warning | SKILL.md body (after frontmatter) exceeds 500 lines (see `scripts/check_structure.py` `SKILL_MD_MAX_LINES`). Long bodies eat context and signal that detail should move into reference files. |
| `html_tag` | warning | SKILL.md or a reference file contains a raw HTML tag outside a fenced code block or inline-code span. Skill text should stay portable Markdown. |
| `process_substitution` | error | A line outside a code fence contains bash process substitution `<(...)`, which some skill-upload pipelines reject as a malformed HTML tag (upload-breaking). Replace with a temp file or a pipe. |
| `windows_path` | warning | A line contains a backslash-separated path with a typical extension (`.md`, `.py`, `.json`, etc.). Windows paths break on Unix; use forward slashes. |

## Reference Depth And Table Of Contents

| `check_id` | Severity | Triggers when |
|---|---|---|
| `broken_md_link` | warning | SKILL.md links to a `.md` file that doesn't exist in the skill directory. Broken links waste tokens and confuse the model. |
| `nested_reference` | warning | A reference file (linked from SKILL.md) itself links to another `.md` file. Claude may only partially read deeply-nested files; keep references one level deep. |
| `missing_toc` | suggestion | A reference file is longer than 100 lines but has no `## Contents` / `## Table of contents` / `## TOC` heading within the first 100 lines (see `scripts/check_structure.py` `REFERENCE_TOC_THRESHOLD`, which the TOC search window now matches). Without a TOC, Claude may preview with `head -100` and miss content below. |

## Heavy-Handed Imperative Candidate Scan (Separate Script)

`check_musts.py` scans the SKILL.md body for ALL-CAPS imperatives (`ALWAYS`, `NEVER`, `MUST`, `MUST NOT`, `DO NOT`, `DON'T`) and flags any paragraph that contains one without a nearby explanation cue (`because`, `to avoid`, `to ensure`, em-dash, parenthetical, etc.).

| `check_id` | Severity | Triggers when |
|---|---|---|
| `heavy_handed_must_candidate` | suggestion | A body paragraph contains an ALL-CAPS imperative but no recognizable rationale phrase. |

The agent reading these findings must decide whether the imperative genuinely needs reasoning (keep as a finding, ideally promoted to `heavy_handed_musts`) or whether the why is obvious from surrounding context (drop the candidate).

## Synonym Candidate Scan (Separate Script)

`check_synonyms.py` scans the SKILL.md body for known synonym groups (image/photo/picture, customer/client/user, field/box/element, extract/pull/get, etc.) and flags any group where two or more terms each appear at least twice.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `terminology_candidate` | suggestion | Two or more synonyms from the same group each appear ≥2 times in the body. |

These are *candidates*, not confirmed findings. The agent reading this output must decide whether the terms genuinely refer to the same concept (keep as a finding) or are intentionally distinct (drop). The script's job is to surface candidates so judgement-only review can't miss them; the agent's job is the disambiguation.

## H2 Title-Case Scan (Separate Script)

`check_h2_case.py` walks SKILL.md and every `references/*.md` sibling, flagging H2 headings that are not in title case (e.g. `## Worked example`). The check skips H2s inside fenced code blocks so markdown examples are not flagged.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `h2_heading_case` | suggestion | An H2 heading in SKILL.md or any `references/*.md` is not in title case (first word and every non-stopword word must start with a capital letter). |

Unlike the synonym and musts scanners, every finding here is actionable — there is no judgement call to drop a candidate. Prior judgement-only passes reliably checked SKILL.md but forgot the reference files; this script makes coverage mechanical. The stopwords (words that stay lowercase mid-heading) are defined once in `TITLE_CASE_STOPWORDS` (`scripts/check_h2_case.py`) — the conventional small set of articles, short prepositions, and conjunctions.

## Keyword-Argument Scan (Separate Script)

`check_kwargs.py` AST-walks every Python file under `scripts/` and flags positional calls to bare-name functions that are not in the allow-list. Attribute calls (`obj.method()`, `module.func()`) are always allowed, matching the stdlib-helper exception in `coding-best-practices.md`.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `positional_call` | error | A bare-name call (not an attribute) passes one or more positional arguments and the target name is not in the allow-list of built-ins, exception types, or stdlib constructors (`Path`, `datetime`, `Counter`, etc.). |
| `script_syntax_error` | error | A script under `scripts/` fails to parse. Always block — the other deterministic checks cannot run against an unparseable file. |
| `script_unreadable` | error | A script under `scripts/` cannot be read as UTF-8 text (binary content or a wrong encoding). Emitted instead of crashing the scanner, so the run still produces JSON and the loop can act on it. |

The allow-list lives in `scripts/check_kwargs.py` (`ALLOW_LIST_BUILTINS`, `ALLOW_LIST_EXCEPTIONS`, `ALLOW_LIST_OTHER`). Add to `ALLOW_LIST_OTHER` only when a real call site is flagged that the user decides should be allowed; record the reason in a one-line comment next to the entry so the allow-list stays auditable.

The severity is `error` (not `suggestion`) because `coding-best-practices.md` lists keyword-only calls as a hard project rule, and `references/checklist.md` says "missing type hints, positional args at a call site that has kwargs available" are `error`-tier deviations.

## Severity Rationale

The severity tier reflects user-facing impact, not authoring effort:

- **Error** — the skill technically won't load, won't trigger reliably, or will be rejected by validators. Always fix.
- **Warning** — the skill works but violates a documented best practice with measurable cost (longer context, missed triggers, broken paths on Unix). Fix unless there's a specific reason.
- **Suggestion** — quality nit. Helpful to fix but the skill is fine without it.

When in doubt between two tiers, the script picks the lower one. The script is conservative on purpose; the LLM judgement pass is where richer interpretation happens.
