---
type: lint-data
purpose: Curated hyphenation lists for the bidirectional `hyphenated_open_compound_noun` lint check.
updated: 2026-06-20
---

# Hyphenation lists

Data for the bidirectional `hyphenated_open_compound_noun` check in `scripts/check_wiki.py`. The script parses the four sections below at load time; this file is the single source of truth for the lists (the script holds no hardcoded copy).

This file is **agent-writable data, not script logic** (CLAUDE.md → Stay In Your Lane lists it alongside the memory journals). `audit` grows all four lists autonomously as it verifies hyphenation uses against the raw — it never edits the check's code, only this data. **Every new entry must be sub-agent-verified before it is written**: spawn independent sub-agents and add the entry only on consensus (default ≥ 2 of 3 confirm the addition is correct); on a split or refutation, leave it out (audit Step 7). Append one entry per line under the matching heading, in the per-section format. A malformed or unreadable line is skipped, not fatal; a missing file degrades the check to a silent no-op (recoverable from git), so keep it valid.

Format per section:
- `disallowed`: `hyphenated-form = open form` (a slug-derived open compound; opened when used as a bare noun — direction 1).
- `allowed`: one hyphenated token per line (a correct, keep-hyphenated look-alike — proper name or established term; never flagged).
- `heads`: one head noun per line (marks an open compound before it as a modifier — the direction-2 gate).
- `verified-ignore`: one lowercased `compound following-word` phrase per line (a use confirmed correct as written; skipped in both directions).

## disallowed

- tool-use = tool use
- belief-state = belief state

## allowed

- fine-tuning
- prefix-tuning
- adapter-tuning
- chain-of-thought
- theory-of-mind
- llm-as-a-judge
- model-based
- foundation-model
- multi-agent
- single-agent
- role-prompting
- gpt-3

## heads

- representation
- representations
- prompt
- prompts
- prompting
- training
- method
- methods
- mechanism
- mechanisms
- loop
- loops
- message
- messages
- content
- paradigm
- channel
- channels
- vector
- vectors
- module
- modules
- improvement
- improvements
- pattern
- patterns
- phase
- phases
- stage
- stages

## verified-ignore
