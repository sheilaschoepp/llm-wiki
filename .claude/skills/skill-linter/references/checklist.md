# Judgement-based checklist

The deterministic script in `scripts/check_structure.py` handles things you can verify by pattern-matching. This file covers the things you can only assess by reading the skill — the kind of issue a reviewer would flag in a PR.

For each check below: read the relevant part of the skill, decide whether the issue is present, and if so emit a finding with the listed severity. Use the same finding schema as the script:

```json
{
  "severity": "error|warning|suggestion",
  "check_id": "<id from below>",
  "file": "SKILL.md or references/foo.md",
  "line": <int or null>,
  "message": "<one sentence>",
  "fix_hint": "<concrete fix>"
}
```

## Contents

- Description quality
- Body content quality
- Examples and concreteness
- Formatting conventions
- Workflows and instruction style
- Time-sensitive content
- Scripts (if the skill bundles any)

## Description Quality

These sit in `SKILL.md` frontmatter, between the `---` markers.

**`description_vague`** (warning). The description doesn't say specifically what the skill does or when to trigger. Generic phrasings like "Helps with documents", "Processes data", "Does stuff with files" are the canonical bad case. The fix is to add concrete capabilities ("Extracts text and tables from PDFs") AND triggering contexts ("Use when working with PDFs, forms, or document extraction").

**`description_missing_when_to_use`** (warning). The description names what the skill does but never says when to use it. Look for explicit cues like "Use when...", "Trigger when...", "Apply this for...". If absent, flag it. The "what + when" pair is what makes the skill discoverable.

**`description_undertriggers`** (suggestion). The description is technically fine but timid — it would only trigger on the most explicit phrasings. If the skill could plausibly help with adjacent or implicit phrasings the user might use, suggest broadening: "Also use when the user mentions <related term> even if they don't explicitly ask for <skill domain>." This is a real failure mode — Claude tends to under-trigger skills.

## Body Content Quality

**`inconsistent_terminology`** (suggestion). The body switches between synonyms for the same concept. This applies to *all* prose, not just technical jargon — narrative writing slips into this constantly. Watch for:

- Technical: "field" / "box" / "element"; "extract" / "pull" / "get"; "API endpoint" / "URL" / "route".
- Domain entities: "image" / "photo" / "picture"; "customer" / "client" / "user"; "vendor" / "seller" / "supplier"; "ticket" / "issue" / "case"; "order" / "purchase" / "transaction".
- Verbs for the same action: "submit" / "send" / "post"; "save" / "store" / "write".

When you read the body, mentally underline every noun phrase that names a thing the skill operates on, and every verb for what the skill does. If two or more variants appear for the same referent, that's a finding. Pick the most concrete or domain-appropriate term, note where the variants appear, and suggest standardizing.

**`heavy_handed_musts`** (suggestion). The body is full of all-caps `MUST` / `NEVER` / `ALWAYS` directives without explaining *why*. Models do better with explanation than with rules. Flag the worst offenders and suggest reframing as "<directive> because <reason>". Don't flag every MUST — only the ones that read as scolding rather than safety-critical.

**`punts_to_claude`** (suggestion). The body says things like "use your best judgement", "do whatever is appropriate", "Claude knows what to do" in places where the user clearly wants a specific behaviour. The whole point of a skill is to provide context Claude doesn't already have; if the skill doesn't add anything, why does it exist? Suggest replacing each punt with concrete guidance.

## Examples And Concreteness

**`abstract_examples`** (suggestion). Examples in the body use placeholders (`<thing>`, `[your value]`, `foo/bar`) where concrete examples would be clearer. Concrete input/output pairs teach more than abstract templates. Flag the example block, suggest replacing with a realistic case.

**`missing_examples_for_format`** (suggestion). The body asks Claude to produce output in a specific format (a report, a commit message, a JSON shape) but doesn't show a concrete example of what good output looks like. Format requirements without examples often don't stick.

## Formatting Conventions

**`h2_heading_case`** (suggestion). H2 section headers in `SKILL.md` and `references/*.md` should be in **title case** (e.g. `## When To Invoke`, `## When Not To Invoke`, `## Edge Cases`, `## Procedure`, `## Limits`, `## Worked Example`). This matches the prevailing convention across the project's skills. Flag sentence-case H2s (`## When to invoke`, `## Worked example`) as `suggestion` with a fix that converts them to title case. **Do not run the conversion in reverse**: title-case H2s are correct, not a defect. **Never alter a literal code token while title-casing** — a backtick span, filename, path, or identifier (anything with a `.`, `/`, or `_`, e.g. a heading like `## What check_structure.py Catches`): title-case only the natural-language words around it, and drop the candidate if re-casing the code token would be the only change. The H1 (`# Skill Name`) is a normal Markdown heading and does not follow this rule. Wikilink display names inside body prose follow CLAUDE.md's wikilink convention (sentence case for common nouns, title case for proper nouns) — that is separate from the H2 rule and not what this check targets.

This check is also enforced deterministically by `scripts/check_h2_case.py`, which walks SKILL.md and every `references/*.md`. The judgement entry remains here because the script's stopword list is intentionally conservative — a heading the script accepts may still read awkwardly and warrants a judgement review. Treat the script as the primary enforcement and the judgement pass as a secondary check.

## Workflows And Instruction Style

**`workflow_no_checklist`** (suggestion). The body describes a multi-step workflow (3+ steps that must be sequenced) but doesn't include a copyable checklist. For complex workflows, a checklist Claude can copy into its response improves follow-through.

**`workflow_no_validation`** (warning). The body describes a quality-critical operation (file edits, document generation, data transformation) but has no validation/verification step before declaring done. Run-validator-then-fix loops dramatically improve output quality. Suggest adding one.

## Time-Sensitive Content

**`time_sensitive_info`** (warning). The body contains phrasing that anchors instructions to a specific date or version transition: "If you're doing this before <date>", "After <month> use the new API", "As of <year>". This information goes stale silently. Suggest moving obsolete content into an `## Old Patterns` section or a reference file so the current path stays clean.

## Scripts (Only If The Skill Bundles `.py` / `.sh` / `.js` Files)

For each script in `scripts/`:

**`magic_numbers`** (suggestion). The script contains numeric constants (timeouts, retries, thresholds) without comments explaining the value. Flag with a pointer to the line and suggest adding a brief comment explaining why the value was chosen.

**`punts_in_script`** (warning). The script catches an error condition and re-raises with a vague message instead of handling it. Skills should handle predictable error conditions in the script itself rather than passing them up to Claude to resolve. Flag the bare `raise` / unhandled `except` and suggest a recovery path or a more specific error message.

**`assumes_install`** (suggestion). The skill body or scripts assume packages are already installed without saying so. If the skill imports `pypdf` or similar, the body should say "requires `pip install pypdf`" explicitly, since the API runtime has no network access.

**`positional_call`** (error). A bare-name call passes positional arguments where the keyword-argument convention from `coding-best-practices.md` applies. This check is now enforced deterministically by `scripts/check_kwargs.py`, which AST-walks every `scripts/*.py`. The judgement entry remains here as a backstop and for surfacing patterns the script's allow-list misses: a positional call to an imported helper across files (the AST scan only knows same-file definitions and the explicit allow-list). Treat the script as the primary enforcement and the judgement pass as a secondary check.

## How To Apply This Checklist

Read SKILL.md once end-to-end and any reference files it points at. As you read, jot findings against the IDs above. Don't grade things into oblivion — if you'd find a check borderline, mark it `suggestion` rather than `warning`. The user trusts the linter more if false alarms stay rare.

If a piece of feedback doesn't match one of the IDs above but you're confident it would help the skill, you can still emit a finding — just give it a descriptive `check_id` (e.g., `description_redundant_with_name`). The checklist isn't exhaustive; it's a starting set.
