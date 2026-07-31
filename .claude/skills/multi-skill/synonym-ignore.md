# Synonym confirmed-distinct allow-list

Per-skill escape valve for `check_synonyms.py`'s `terminology_candidate` check. That scanner flags any SKILL.md body where two or more near-synonyms from a group both appear — a deliberately noisy net so the reviewer only decides *which* candidates are real, not whether to look. But the same domain-distinct pairs recur every run (a log **entry** vs a memory **record**; **route** the verb vs a filesystem **path**), and with no memory the reviewer re-adjudicates them each pass and the count never reaches zero. This file records the groups a run confirmed distinct **for a specific skill**, so later runs auto-suppress them — mirroring lint's verified-ignore data files (`unlinked-mention-ignore.md`).

Agent-writable curated data (not skill logic): when a `skill-linter` run confirms a `terminology_candidate` is a genuine domain distinction (the terms refer to different things in that skill), append it here under the skill's section. Never suppress a *genuine* inconsistency — only record terms confirmed to name different things. Removing an entry re-surfaces its candidate.

Format: a `## <skill-name>` section per skill; each bullet lists the slash-separated terms confirmed distinct, with an optional ` — rationale` tail (ignored by the parser). A finding is suppressed only when its present terms are a subset of a listed group for that skill. Record the minimal confirmed-distinct subset actually present, not a whole synonym group: because suppression is by subset, an over-broad entry silently clears every sub-pair within it, which can mask a later genuine inconsistency among terms you did not mean to allow.

## audit

- document / file — "document" the verb (to document a decision) vs "file" the artifact on disk
- record / row / entry / item — an audit record vs a table row vs a log/memory entry vs a numbered list item
- field / cell — a frontmatter/form field vs a table cell
- route / path — the verb "routes to" vs a filesystem path
- write / persist — "write" (emit to disk) vs "persist" (a finding or state remaining)

## brief

- save / write — "save the brief" (emit the file) vs "write each section" and the compound "AI-writing tells"

## cleanup

- record / entry / item — "record" the verb (record it `already-cleared`) and the reconciled paper trail vs a memory-journal entry vs a per-item deletion candidate
- save / write — "save the combined report" vs "write time" and the compound "AI-writing tells"

## compare

- record / row / entry — "record" the verb (record each target's status) vs the table's `Support` row vs a log / `targets:` entry

## consistency

- save / write — "save report" vs "write time" and the compound "AI-writing tells"

## forget

- record / entry — the quarantined paper trail vs a log / Recent-activity entry
- route / path — the verb "routes to supersede/ingest" vs a filesystem path

## ingest

- record / item — the wiki's cross-source documentation vs a list element
- route / path — the verb vs a filesystem path
- extract / get — "extract" (pull figures/text from the raw) vs "get" (obtain generally)
- save / write — both emit to disk (the report, the page)

## lint

- document / file — "document" the verb vs "file" the artifact
- record / row / entry / item — four distinct referents
- save / write / persist — emit to disk vs a finding/run-state remaining

## query

- record / entry — "record" the verb (record the stakes level, record the printed page seen) vs a hot / log entry
- route / path — "routes a query's verification", "for the user to route" vs a filesystem path and the procedure's "answer path" / "main path" branches
- save / write — "save the query output" vs "write time", "write `none`", and the compound "AI-writing tells"

## reflect

- record / entry — "the objective record" (log ops and `created:` dates a claim is grounded in) vs a log entry
- save / write — "save the compass note" vs the compound "AI-writing tells"

## supersede

- record / entry — a generic audit record vs the defined "log entry"
- route / path — the skill-routing verb vs a filesystem path

## synthesis

- record / entry / item — "record" the verb vs an index/log entry vs a numbered list item
- route / path — the verb vs a filesystem path
- save / write — Step-10 "save the report" / "write the report" (mild, non-confusing)

## skill-llm-council

- pull / get — "pull in" (load context) vs "get" (obtain a review outcome or timestamp)
- document / file — "document" the verb ("the triggers this skill documents") and the modifier "document-handling guidance" vs "file" the artifact on disk

## skill-linter

- issue / case — "issue" a best-practices problem or finding vs "case" a scenario or the keep-vs-drop decision on a candidate (incl. "title-case" / "H2 case")
