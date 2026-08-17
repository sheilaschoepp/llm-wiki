# Deterministic checks reference

This is the catalogue of checks performed by `scripts/check_structure.py` and the five separate scanner scripts (`check_synonyms.py`, `check_musts.py`, `check_h2_case.py`, `check_kwargs.py`, `check_internal_refs.py`). Each entry lists what triggers the finding, the severity, and the rationale (so you can explain it back to the user when they ask "why is this a warning").

## Contents

- Frontmatter checks (errors)
- Body length and paths (warnings)
- Reference depth, inline refs, and TOC (warnings / suggestions)
- Heavy-handed imperative candidate scan (separate script)
- Synonym candidate scan (separate script)
- H2 sentence-case scan (separate script)
- Keyword-argument scan (separate script)
- Severity rationale

## Frontmatter checks

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

## Body length, formatting, and paths

| `check_id` | Severity | Triggers when |
|---|---|---|
| `body_over_length` | warning | SKILL.md body (after frontmatter) exceeds the word budget (`SKILL_MD_MAX_WORDS`, ~6500 — the primary signal) or the line budget (`SKILL_MD_MAX_LINES`, 500); both in `scripts/check_structure.py`. Word count leads because this repo writes one paragraph per physical line (no hard wrap), so the line count under-measures a dense body — the guide's real concern is token cost, which words track and physical lines don't here. Long bodies eat context and signal that detail should move into reference files. |
| `html_tag` | warning | SKILL.md or a reference file contains a raw HTML tag outside a fenced code block or inline-code span. Skill text should stay portable Markdown. |
| `process_substitution` | error | A line outside a code fence contains bash process substitution `<(...)`, which some skill-upload pipelines reject as a malformed HTML tag (upload-breaking). Replace with a temp file or a pipe. |
| `windows_path` | warning | A line contains a backslash-separated path with a typical extension (`.md`, `.py`, `.json`, etc.). Windows paths break on Unix; use forward slashes. |

## Reference depth, inline refs, and table of contents

| `check_id` | Severity | Triggers when |
|---|---|---|
| `broken_md_link` | warning | SKILL.md links to a `.md` file that doesn't exist in the skill directory. Broken links waste tokens and confuse the model. |
| `nested_reference` | warning | A reference file (linked from SKILL.md) itself links to another `.md` file. Claude may only partially read deeply-nested files; keep references one level deep. |
| `missing_toc` | suggestion | A reference file is longer than 100 lines but has no `## Contents` / `## Table of contents` / `## TOC` heading within the first 100 lines (see `scripts/check_structure.py` `REFERENCE_TOC_THRESHOLD`, which the TOC search window now matches). Without a TOC, Claude may preview with `head -100` and miss content below. |
| `broken_inline_ref` | warning | An inline-code path to a skill file resolves nowhere on disk (checked repo root, `.claude/skills/`, and the skill dir). Recognized forms: a `.claude/`-prefixed path, a `references/`- or `scripts/`-prefixed path, any path containing a `/references/` or `/scripts/` segment, a path whose last segment is `SKILL.md`, and — disk-gated on the leading segment naming a real skill dir — the bare abbreviated `<skill>/<file>.md` form that drops the `references/`/`scripts/` segment (e.g. a broken `<skill>/removal-mechanics.md` for `<skill>/references/removal-mechanics.md`, the shape that once shipped uncaught). `broken_md_link` only sees Markdown-hyperlink references; this covers the inline-code path syntax these skills actually use. Runs in directory mode only and needs a CLAUDE.md-rooted repo (`find_repo_root`); it is skipped, with no finding, in single-file mode and for an out-of-repo or `.skill`-bundle target with no repo root. Scanned across SKILL.md and every `references/*.md`; fenced code blocks, `{…}`/`<…>` templates, and wiki/raw/output/archive paths are excluded (they carry legitimate examples). |

## Heavy-handed imperative candidate scan (separate script)

`check_musts.py` scans the SKILL.md body for ALL-CAPS imperatives (`ALWAYS`, `NEVER`, `MUST`, `MUST NOT`, `DO NOT`, `DON'T`) and flags any paragraph that contains one without a nearby explanation cue (`because`, `to avoid`, `to ensure`, em-dash, parenthetical, etc.).

| `check_id` | Severity | Triggers when |
|---|---|---|
| `heavy_handed_must_candidate` | suggestion | A body paragraph contains an ALL-CAPS imperative but no recognizable rationale phrase. |

The agent reading these findings must decide whether the imperative genuinely needs reasoning (keep as a finding, ideally promoted to `heavy_handed_musts`) or whether the why is obvious from surrounding context (drop the candidate).

## Synonym candidate scan (separate script)

`check_synonyms.py` scans the SKILL.md body for known synonym groups (image/photo/picture, customer/client/user, field/box/element, extract/pull/get, etc.) and flags any group where two or more terms each appear at least twice.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `terminology_candidate` | suggestion | Two or more synonyms from the same group each appear ≥2 times in the body. |

These are *candidates*, not confirmed findings. The agent reading this output must decide whether the terms genuinely refer to the same concept (keep as a finding) or are intentionally distinct (drop). The script's job is to surface candidates so judgement-only review can't miss them; the agent's job is the disambiguation.

A per-skill confirmed-distinct allow-list, `.claude/skills/multi-skill/synonym-ignore.md`, suppresses groups a prior run already adjudicated as distinct *for that skill*, so the same false positives don't re-surface every run (they used to, since the check has no memory) — mirroring lint's verified-ignore data files. The parser suppresses a finding whose present terms are a subset of a listed group under the target skill's `## <skill-name>` section. When a run confirms a candidate is a genuine domain distinction, append it there (agent-writable curated data); never record a genuine inconsistency, and removing an entry re-surfaces its candidate.

## H2 sentence-case scan (separate script)

`check_h2_case.py` walks SKILL.md and every `references/*.md` sibling, flagging H2 headings that are not in sentence case (e.g. `## Worked Example`). The check skips H2s inside fenced code blocks so markdown examples are not flagged, and skips identifier tokens after a colon-terminated label (`## Packet: schema-language`, `## Mode: full`) — a slug that names a literal argument carries no case to correct, and title-casing it would rename the thing it points at. The carve-out is deliberately narrow: it applies only to an all-lowercase word that follows a `Label:` and either contains a hyphen or is the sole word after the colon, so prose after a colon (`## Note: this is prose`) and hyphenated prose without a label (`## Working with well-formed pages`) are both still flagged.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `h2_heading_case` | suggestion | An H2 heading in SKILL.md or any `references/*.md` is not in sentence case (only the first word, proper nouns, and acronyms may start with a capital letter). |

Unlike the synonym and musts scanners, every finding here is actionable — there is no judgement call to drop a candidate. Prior judgement-only passes reliably checked SKILL.md but forgot the reference files; this script makes coverage mechanical. Sentence case needs no stopword list — every word after the first is lowercase unless it is a proper noun or an acronym — so the script carries no stopwords. What it does carry is `PROPER_NOUNS` (`scripts/check_h2_case.py`), the allowlist of terms that keep their capital mid-heading, and `TITLE_CASE_WORD_RE`, which matches the mid-heading capitalized word that triggers a finding. Extend `PROPER_NOUNS` when a legitimate proper noun is being flagged.

## Keyword-argument scan (separate script)

`check_kwargs.py` AST-walks every Python file under `scripts/` and flags positional calls to bare-name functions that are not in the allow-list. Attribute calls (`obj.method()`, `module.func()`) are always allowed, matching the stdlib-helper exception in `coding-best-practices.md`.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `positional_call` | error | A bare-name call (not an attribute) passes one or more positional arguments and the target name is not in the allow-list of built-ins, exception types, or stdlib constructors (`Path`, `datetime`, `Counter`, etc.). |
| `script_syntax_error` | error | A script under `scripts/` fails to parse. Always block — the other deterministic checks cannot run against an unparseable file. |
| `script_unreadable` | error | A script under `scripts/` cannot be read as UTF-8 text (binary content or a wrong encoding). Emitted instead of crashing the scanner, so the run still produces JSON and the loop can act on it. |

The allow-list lives in `scripts/check_kwargs.py` (`ALLOW_LIST_BUILTINS`, `ALLOW_LIST_EXCEPTIONS`, `ALLOW_LIST_OTHER`). Add to `ALLOW_LIST_OTHER` only when a real call site is flagged that the user decides should be allowed; record the reason in a one-line comment next to the entry so the allow-list stays auditable.

The severity is `error` (not `suggestion`) because `coding-best-practices.md` lists keyword-only calls as a hard project rule, and `.claude/skills/multi-skill/references/skill-authoring-checklist.md` says "missing type hints, positional args at a call site that has kwargs available" are `error`-tier deviations.

## Internal cross-reference scan (separate script)

`check_internal_refs.py` checks a skill's references to its own procedure. It collects every step the file defines — a numbered `1. **Label.**` line and a bolded sub-step label such as `**8.0 — …**` — then flags any `Step N` or `Step N.M` citation in prose with no matching definition. Fenced blocks are skipped, so an example `Step 99` in a template is not a live reference.

| `check_id` | Severity | Triggers when |
|---|---|---|
| `stale_step_reference` | warning | Prose cites a step or sub-step number the same file does not define. Almost always renumbering damage: a step was inserted or removed and the cross-references were not repointed. |

The step check runs on `SKILL.md` only. A `references/*.md` sibling legitimately cites its parent's steps ("SKILL.md Step 3 names each entry's home") and defines none of its own, so running it there would flag every correct citation.

Severity is `warning`, not `suggestion`, because a dangling step pointer is a factual error in the procedure rather than a style preference — a reader who follows it lands nowhere — and the fix is determinate once you know which step now holds the work.

Two limits, stated so the check is not trusted for more than it does. It is an **existence** check: a reference that resolves to the *wrong* existing step (`8.4` where `8.3` was meant) passes, and only a reader catches it. And it deliberately does **not** check renamed template *fields* — a reconcile step still naming a `Ledger:` line after the template renamed it to `Removed:`. That was built and cut: a backticked `Foo:` in a skill's prose is usually a field of some *other* document (a wiki page's `sources:`, a report's `result:`), so the check fired on all fourteen skills in this repo without finding one real defect. Separating a field this skill's own template dropped from a field it never had needs the file's prior state, which a single-file scanner does not have; a git-diff variant is the way to revive it.

## Severity rationale

The severity tier reflects user-facing impact, not authoring effort:

- **Error** — the skill technically won't load, won't trigger reliably, or will be rejected by validators. Always fix.
- **Warning** — the skill works but violates a documented best practice with measurable cost (longer context, missed triggers, broken paths on Unix). Fix unless there's a specific reason.
- **Suggestion** — quality nit. Helpful to fix but the skill is fine without it.

When in doubt between two tiers, the script picks the lower one. The script is conservative on purpose; the LLM judgement pass is where richer interpretation happens.
