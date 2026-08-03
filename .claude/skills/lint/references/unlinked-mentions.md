# Unlinked-Mention Semantic Census and Shared Replay

`check_wiki.py` emits aggregate `unlinked_page_mention` groups. Those groups and counts are reconciliation evidence only, never occurrence-discovery scope.

## Freeze Common Inputs and Verified Ignores

Freeze the bytes and repo-relative paths of every Markdown page directly under `1-wiki/sources/`, `entities/`, `concepts/`, and `syntheses/`. The same inventory supplies semantic hosts and targets.

Read `.claude/skills/multi-skill/unlinked-mention-ignore.md` as UTF-8. Missing or unreadable input yields no entries.

Parse lines in order with 1-based source-line numbers:

1. Strip surrounding whitespace.
2. A stripped line beginning `## ` sets the current section to the stripped, lowercased text after `## `, then continues.
3. Ignore a line unless the current section is exactly `verified-ignore` and the stripped line begins `- `.
4. Remove `- ` and strip the item.
5. Skip an empty item or one beginning `<!--`.
6. Split on literal `::`, strip every field, and require exactly three nonempty fields: page, target, phrase. Skip malformed items.
7. Compile `re.compile(r'\s+'.join(re.escape(word) for word in phrase.split()), re.IGNORECASE)`.
8. Retain page, target, phrase, source line, and compiled pattern in input order.

Missing, unreadable, malformed, skipped, or unmatched evidence suppresses nothing.

## Freeze Origins and Literal Relations

For each target, freeze separate origins for its `stem.replace('-', ' ').strip()` display, its nonempty scalar string `title:` returned by the shared frontmatter parser, and every nonempty string in list-valued `aliases:` in declared occurrence order.

Sort targets bytewise by repo-relative path and origins as stem-display, title, then alias occurrence. Assign:

```text
origin ID | target path | stem-display|title|alias-N | canonical form
```

Canonical origin text is the trimmed stem-display, trimmed scalar title, or trimmed alias string. Before literal generation, reject any origin whose canonical text is empty after trimming and record:

```text
empty-origin exclusion ID | target path | stem-display|title|alias-N | original value | reason=empty-after-trim
```

Do not assign an origin ID or semantic obligation to an excluded origin. After separator variation, reject any literal whose `literal.strip()` is empty before assigning a literal ID, and record its producing origin/exclusion IDs plus `reason=blank-after-trim`. Every frozen literal therefore contains at least one non-whitespace character. Compiling, searching, reporting, or terminalizing an empty or whitespace-only semantic literal is forbidden and makes expansion `incomplete`.

Retain distinct origins even when their case-folded forms match.

For each origin, generate every distinct literal obtained by independently choosing one ASCII space or one ASCII hyphen at every internal ASCII space-or-hyphen separator. Relate the origin to the literal as `exact` when their case-folded texts match and `separator-derived` otherwise.

Within each target, collapse only byte-identical literal text into one literal record. Do not collapse merely case-fold-identical but byte-distinct spellings; they remain separate searches and their relations are united on any shared occurrence span.

Sort literal records bytewise by target path and literal bytes. Assign:

```text
literal ID | target path | literal text | complete origin ID:exact|separator-derived relation set
```

Never select one provenance label or discard an origin. Do not infer undeclared aliases, inflections, abbreviations, synonyms, translations, paraphrases, or semantic near aliases.

## Freeze Semantic Literal Obligations

Before searching, freeze one obligation for every non-self `(host path, target path, literal ID)` tuple:

```text
semantic obligation ID | host path | target path | literal ID | literal text | complete frozen origin relation set | planned
```

Every obligation receives one terminal:

```text
semantic obligation ID | completed|pending|failed | semantic row IDs | verified-ignore source lines/spans | failure
```

A successful zero-match search is completed with no row IDs and no ignore spans. Missing, unreadable, interrupted, or partially enumerated work is pending or failed.

## Original Body, Coordinates, and Protected Intervals

For each host call shared `parse_frontmatter`, bind its zero-based closing-delimiter line index as `frontmatter_end`, and construct exactly:

```python
body = '\n'.join(text.split('\n')[frontmatter_end + 1:])
```

Body offsets are zero-based half-open Python string offsets and remain the semantic/replay mapping identity. For `match_start` compute:

```python
body_line = body.count('\n', 0, match_start) + 1
body_line_start = body.rfind('\n', 0, match_start) + 1
body_column = match_start - body_line_start + 1
file_line = frontmatter_end + 1 + body_line
file_column = body_column
```

All displayed lines and columns are 1-based. Body line 1 is physical file line `frontmatter_end + 2`. Derive the displayed full line from the original file at `file_line`; never label a body-relative coordinate as file-relative.

Semantic discovery searches the original unblanked `body`. It never searches space-filled text. Freeze authoritative half-open intervals:

```text
protected interval ID | host path | body start:end | fenced-code|inline-code|wikilink-or-embed|ascii-double-quote|H1
```

Enumerate shared-style intervals over the original body with exactly:

```python
re.compile(r'`[^`]*`')
re.compile(r'\[\[[^\]]*\]\]')
re.compile(r'"[^"\n]*"')
re.compile(r'(?m)^#[ ].*$')
```

Retain their actual cross-line and overlap behavior. Also enumerate complete fenced blocks from the original body. An opener matches `^ {0,3}(`{3,}|~{3,})[^\n]*$`; the closer is the next line with up to three leading ASCII spaces, the same fence character repeated at least the opener length, and only trailing ASCII spaces or tabs. Freeze from opener start through closer end, including delimiters and line endings. An unmatched opener is not protected and is recorded as a malformed-fence coverage limit.

Retain overlapping intervals. A candidate `[match_start,match_end)` overlaps an interval exactly when `match_start < interval_end and interval_start < match_end`. Reject every overlapping candidate before boundaries, ignore suppression, occurrence creation, or classification. Thus length-preserving blanking can never synthesize a semantic candidate.

## Semantic Ignore Spans

Run every applicable parsed verified-ignore phrase pattern over the original unmasked body. The entry applies only when its page equals the repo-relative host path and its target equals the target filename stem. Reject a phrase match that overlaps any protected interval. Otherwise freeze:

```text
semantic ignore span ID | host path | target stem | phrase source line | body start:end
```

Suppress a semantic candidate only when its complete body span lies inside a matching-target semantic ignore span. Record every covering source line and phrase span in every producing semantic terminal. Malformed, skipped, protected, unmatched, missing, or unreadable ignore evidence suppresses nothing.

## Execute Semantic Searches

Freeze one independent semantic obligation per non-self `(host path,target path,literal ID)`. Compile `literal_re = re.compile(r'(?=(' + re.escape(literal) + r'))', re.IGNORECASE)` and run one `finditer` pass over the original unmasked `body`. For each zero-width lookahead match set `match_start = match.start(1)` and `match_end = match.end(1)`, then apply the common protected-interval, boundary, and ignore rules. Because the literal is captured inside a zero-width lookahead, ordinary `finditer` advances through every possible start and preserves overlapping occurrences. Do not use a combined alternation.

Every obligation terminates completed, pending, or failed, including completed zero results, and records its semantic rows and verified-ignore spans. Require `positive_lookahead_searches = planned_semantic_obligations = completed_positive_lookahead_searches`, with zero pending or failed obligations and `shadowed_semantic_occurrences = 0`.

Search every non-self host-target-literal obligation independently, preserve overlapping occurrences, and preserve matched text from `body[match_start:match_end]`.

For a candidate that overlaps no protected interval, assess boundaries against the original body. A side passes at body edge, when the adjacent character is neither a Unicode letter, digit, nor underscore, or when it is an ASCII hyphen. An adjacent ASCII hyphen always passes and no character beyond it is inspected. Reject when `body[match_end:match_end + 1] == '.'`, a following character exists, and that following character is a Unicode letter, digit, or underscore. Then apply semantic ignore spans.

Key occurrences by `(host path,target path,body start,body end)`. Unite every producing obligation and its complete immutable origin-relation set. Retain separate target rows for a multi-target span and initialize each as `uncertain`.

```text
semantic row ID | semantic obligation IDs | complete origin relation set | body start:end | body_line:body_column | file:line:column | matched text | target path | normal|hyphen-boundary | full original file line | genuine-reference|generic-wording|uncertain
```

Every row satisfies `file_line = frontmatter_end + 1 + body_line` and `file_column = body_column`. Same-line, overlapping, and multi-literal occurrences retain distinct body spans or complete producing-relation unions. Every row terminates as `genuine-reference`, `generic-wording`, or `uncertain`; adjacent-hyphen and grammatical coincidences remain candidates.

## Exact Shared-Check Replay

The shared replay is read-only and exists only to reconcile emitted `N`. It never adds semantic hosts, targets, literals, or rows.

Run it in the same Python process as a fresh call to the unmodified shared `check_unlinked_page_mentions`, against the frozen bytes. The paired call’s groups must equal the pinned Step-1 groups.

Mirror the current `check_wiki.py` positive-group matcher by exact unique source endpoints, from `UNLINKED_MENTION_MIN_LEN = 5` through `counts[target] = counts.get(target, 0) + 1`, inclusive. Require both endpoint lines to occur exactly once and in that order in the unchanged checker bytes; otherwise expansion is `incomplete`. Mirror the resolved span exactly:

1. Use minimum form length `5`.
2. Traverse folders in `('sources', 'entities', 'concepts', 'syntheses')` order and `folder_path.glob('*.md')` yielded order.
3. For each target, parse frontmatter and build a set containing `stem.replace('-', ' ').strip().lower()` plus every nonempty string in list-valued `aliases:` as `alias.strip().lower()`. Titles do not participate.
4. Drop forms shorter than five by Python string length.
5. Preserve `own_forms[stem] = forms`, `page_paths[stem] = page`, and `form_to_stem.setdefault(form, stem)` exactly, including first collision winners and later same-stem overwrites.
6. Build `alt` from `sorted(form_to_stem, key=len, reverse=True)` and compile:
   ```python
   re.compile(r'(?<![\w-])(' + alt + r')(?![\w-])(?!\.\w)', re.IGNORECASE)
   ```
7. Traverse hosts in the same folder and glob order. Construct the body after shared frontmatter parsing.
8. Apply exactly:
   ```python
   scan = re.sub(r'`[^`]*`', spaces_of_equal_length, body)
   scan = re.sub(r'\[\[[^\]]*\]\]', spaces_of_equal_length, scan)
   scan = re.sub(r'"[^"\n]*"', spaces_of_equal_length, scan)
   scan = re.sub(r'(?m)^#[ ].*$', spaces_of_equal_length, scan)
   ```
   Do not apply the semantic fenced-code mask.
9. Build ignore spans by exact page and target strings, parser-entry order, and compiled pattern `finditer` over the replay scan.
10. Iterate the mention regex with ordinary non-overlapping `finditer`.
11. Lowercase the matched form, resolve it through `form_to_stem`, and skip a missing target, `target == page.stem`, or `form in own_forms.get(page.stem, set())`.
12. Suppress when the complete match span is inside a matching-target ignore phrase span; retain every covering ignore source line and span.
13. Every remaining match is one replay span and increments its group once.

Assign:

```text
shared replay ID | host path | winning target stem | final target path | body start:end | body_line:body_column | file:line:column | matched replay text | winning form | qualifying final-target semantic origin/literal/obligation IDs|none | semantic row ID|shared-only reason
```

For each replay host bind the shared parser's zero-based closing index as `frontmatter_end`. Compute body and file coordinates from the original replay body with `file_line = frontmatter_end + 1 + body_line` and `file_column = body_column`.

Map a replay row only to the semantic row with identical host path, final target path, `match.start()`, and `match.end()`; require independent coordinate agreement. Use the actual C14 replay variables in the same loop: `body` is the original replay body, `scan` is the four-mask length-preserving replay text, `match` is the current `mention_re.finditer(scan)` match, and `form = match.group(1).lower()` is the winning shared form. Do not introduce replay aliases.

When no semantic row exists, compile:

```python
winning_re = re.compile(re.escape(form), re.IGNORECASE)
scan_fullmatch = winning_re.fullmatch(scan[match.start():match.end()]) is not None
body_fullmatch = winning_re.fullmatch(body[match.start():match.end()]) is not None
```

The replay match itself requires `scan_fullmatch`; if it is false, replay is inconsistent and expansion fails. Then permit exactly one mutually exclusive shared-only proof:

1. `shared-only:native-mask-artifact=<protected interval IDs>` only when `body_fullmatch` is false and the replay span intersects at least one frozen shared-style protected interval. Record the original-body slice, replay-scan slice, and every proving interval/reason. This proves the shared blanking synthesized the matched form.
2. `shared-only:census-mask-reason=fenced-code` only when all of the following hold: `body_fullmatch` is true; the replay's final target path has at least one frozen semantic origin whose exact literal compares equal to `form` under the semantic search's `re.IGNORECASE`; the corresponding non-self host-target-literal semantic obligation exists; the original-body semantic boundary tests pass; no eligible original-body semantic-ignore span suppresses the occurrence; and the replay span intersects a frozen complete fenced-code interval. Record the final target path, every qualifying semantic origin/literal/obligation ID, boundary and ignore tests, and every proving fence interval. This proves that the semantic row for the final resolved target is absent only because the census has the broader fence protection. A first-winner replay form inherited from an earlier same-stem page does not qualify after `page_paths[stem]` was overwritten unless the final target independently declares that exact form.

Because the first proof requires `body_fullmatch` false and the second requires it true, they cannot both hold. Each shared-only row counts once toward native `N`, never enters the semantic table, and receives no semantic disposition. Any other missing or multiple mapping, missing or multiple proof, failed scan fullmatch, or anchor disagreement makes expansion incomplete. A semantic row need not have a replay row.

## Pinned, Native, and Replay Union Aggregates

Freeze one terminal for every `(host,target)` group in the union of pinned Step-1 groups, the paired fresh unmodified native call, and replay-derived positive groups:

```text
aggregate ID | host path | target stem | final target path | pinned N|missing | paired-native N|missing | replay M|missing | replay row IDs | semantic row IDs | shared-only row IDs | completed|failed | failure
```

Count each replay row once regardless of literal, origin, or relation count. Complete only when all three groups exist and `pinned N = paired-native N = replay M`. A missing side or mismatch receives a failed terminal; replay-only groups never become semantic findings.

Require:

```text
planned_semantic_obligations = completed_semantic_obligations
pending_semantic_obligations = 0
failed_semantic_obligations = 0
semantic_rows = genuine_reference_rows + generic_wording_rows + uncertain_rows
planned_union_aggregates = completed_union_aggregates
failed_union_aggregates = 0
replay_rows = mapped_replay_rows + shared_only_fence_rows + shared_only_native_mask_artifact_rows
unmapped_replay_rows = 0
multiply_mapped_replay_rows = 0
unproven_shared_only_rows = 0
multiply_proven_shared_only_rows = 0
ungrounded_fence_only_rows = 0
anchor_mismatch_rows = 0
shadowed_semantic_occurrences = 0
semantic_protected_overlap_rows = 0
duplicate_origin_ids = 0
duplicate_literal_ids = 0
blank_frozen_origin_ids = 0
blank_frozen_literal_ids = 0
unrecorded_blank_origin_or_literal_exclusions = 0
duplicate_semantic_obligation_ids = 0
duplicate_semantic_occurrence_keys = 0
duplicate_protected_interval_ids = 0
duplicate_semantic_ignore_span_ids = 0
duplicate_replay_ids = 0
duplicate_aggregate_ids = 0
pending_semantic_rows = 0
```

Also require one terminal per semantic obligation and union aggregate with none outside its manifest; explicit completed zero-result terminals; exact literal relation sets and occurrence unions; all candidate-specific execution arithmetic; no semantic row overlapping a protected interval; every replay row mapped once or carrying one proven shared-only reason; unchanged frozen bytes across the paired call/replay; and no mutation. Missing work or any duplicate, mismatch, pending item, failure, or changed byte makes expansion `incomplete`.

## Coverage and Mutation Boundary

Semantic coverage is complete only for frozen stem-display forms, literal scalar titles, declared aliases, and ASCII space/hyphen variants under the documented semantic mask and boundaries. Undeclared near aliases, inflections, paraphrases, malformed protected syntax, single- or curly-quoted prose, multiline quotations, ordinary Markdown links, and grammatical meaning remain outside deterministic coverage.

The replay establishes exact parity with the current aggregate checker only. It does not define the semantic census.

Both ledgers are read-only. Lint never rewrites prose, inserts wikilinks, changes hyphenation, changes titles or aliases, or adds, edits, or removes verified-ignore data.
