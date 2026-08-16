---
skill: consistency
date: 2026-08-16
time: "21:29"
councils: 2
advisors: 10
peer_reviews: 10
chairs: 2
refuters: 8
load_bearing_proposed: 9
load_bearing_held: 3
load_bearing_refuted: 6
edits_applied: 10
proposals_raised: 5
---

# skill-llm-council — consistency (2026-08-16 21:29)

Full protocol: ten advisors across two independent councils, anonymized peer review by all ten, one chair per council, meta-chair reconciliation, and an adversarial refuter per contested or load-bearing edit.

## Outcome

Ten edits applied across `SKILL.md`, `references/checks.md`, `scripts/check_consistency.py`, and the test file. The battery runs clean apart from one expected standing finding; 33 consistency tests pass (up from 30), 296 multi-skill tests pass, ruff is clean, and the scanner sweep returns zero findings across all fourteen skills.

Of nine load-bearing proposals that reached the refuter gate, **three held and six were refuted** — including both chair disagreements and the single most-proposed structural change. Two refutations produced strictly better repairs than the proposals they killed.

## The finding that motivated most of the change-set

`consistency` emits one value — `result: clean | findings | blocked` — that gates whether `audit` may run. Today that value is underivable, in three independent ways:

1. **A live bound-out.** The battery's only finding is `file_naming_consistency` on a `2-outputs/` file whose fix is a rename. `references/checks.md` line 7 makes every untagged check auto-fixable by default and that check is untagged, so the catalogue files it as drift the run must fix — while Limits forbids rewriting `2-outputs/` and CLAUDE.md → Safety rules bars renaming without asking. No non-blocking class covered it, the auto-fixable partition never emptied, and the loop bounded out to `blocked`. Audit's project-level precondition was unsatisfiable.
2. **A self-contradicting gate.** One line made `clean` conditional on `judgment_drift: performed`; another said "Exit 0 ⇒ `clean`" flatly. The judgment-drift packet has no script, so no exit code can carry it — an exit-0 battery with a skipped model read read `clean` by one line and `findings` by the other, resolving toward wrongly clearing the gate.
3. **Three fabricated counts.** The report mandated `errors:/warnings:/suggestions:` in frontmatter. `finding()` emits no severity, `--list-checks` carries none, and `SKILL.md` pointed at a "severity mapping" in `references/checks.md` that does not exist — the file contained the string "severity" zero times.

## Applied

1. **`SKILL.md` Step 7 — a sixth non-blocking class, keyed on fix-permission.** A finding whose fix a *named* rule forbids this run to apply is surfaced once as a proposal and is clean-compatible. The refuter required the tightening that makes it safe: the run must cite the specific Limits line or Safety clause, and **absent a citable rule the finding is ordinary auto-fixable drift and blocks** — so the class cannot become a parking space for work a run would rather skip. A recurring member is itself raised as a check-tagging proposal.
2. **`SKILL.md` — the exit code is necessary but never sufficient for `clean`.** Both the exit-0 and exit-1 branches now defer to the stated conditions rather than deciding on their own. The `$?` capture, the exit-2 mapping with its `(internal)`-versus-empty-stdout trap, and the bounded-out override are preserved verbatim.
3. **`SKILL.md` — the three severity counts deleted**, with the reason recorded: findings carry no severity, nothing consumes the totals (`audit` gates on `result:` alone), and inventing them per run is worse than omitting them.
4. **`references/checks.md` — the dangling severity pointer repaired** with the mapping that already exists in code: `AI_TELL_PATTERNS`' ten per-pattern severities, in this skill's skill-facing `error / warning / suggestion` vocabulary, with a note that no other check carries one.
5. **`SKILL.md` Step 5 — a freeze on schema-derived fixes while the schema is in dispute.** When `section_lists_match_schema` fires, no `EXPECTED_SECTIONS`-derived fix is applied; each is deferred. The finding is self-contradictory on its face (its `fix_hint` says match `CLAUDE.md` while its `message` prints the stale expectation), so neither direction can be trusted until the roster question is settled.
6. **`SKILL.md` Step 6 — the restated Limits rule deleted.** The step restated the never-auto-fix rule verbatim and then conceded two lines later that Limits is its canonical home. What remains is the decision-type boundary, which is Step 6's own content.
7. **`SKILL.md` Scope — now admits what the battery actually reads**: `MEMORY.md`, `2-outputs/`, and `a-archive/` (read-only, surfaced never fixed), plus an honest note that only `index.md` gets a structural check while `hot.md` and `log.md` structure is `lint`'s.
8. **`SKILL.md` description — 947 → 984 chars.** Drops the unbacked `hot`/`log` structural claim and adds the action posture every sibling states and this one omitted: `Auto-fixes mechanical drift; never edits CLAUDE.md, skills, or scripts — those are proposals.`
9. **`scripts/check_consistency.py` — `placeholder_consistency` now uses the page kind it computed and discarded.** A concept page uniformly using `None noted` passed clean before; it is now flagged. Narrowed per the refuter to an exact two-phrase whitelist, so a content bullet like `> - None of the three trials reported latency` is prose, not a finding. `references/checks.md` updated in the same pass; three regression tests added.
10. **Three ruff `W505` cleared** (two pre-existing, one introduced by this run's own docstring).

## Refuted — six of nine

- **Re-keying the classification rule from file path to fix-permission** (Council 2's chair). It would replace a deterministic, script-checkable key with an agent judgement — the very thing that line was written to prevent — and is redundant once the sixth class exists. The line stands verbatim.
- **A `check_id → severity` registry ported from `check_wiki.py`.** `AI_TELL_PATTERNS` already carries severity *per pattern*; a per-check registry would flatten three severities into one. Severity is not well-defined per check anyway (`domain_literature_leakage` is per-instance, `dir_tree_drift` has two opposite directions), the sibling concedes this by mapping one id to `None`, and `catalogue_matches_manifest` would not guard the new column. Replaced by items 3 and 4, which dominate.
- **`enforcement_constants_match_schema`** (Council 1 ranked it load-bearing; Council 2 omitted it). It would false-positive on day one: CLAUDE.md's paper template carries `attachments: []` which `REQUIRED_FIELDS['paper']` deliberately omits, and synthesis templates carry `single_source_stub:` marked "OMIT entirely". Since such findings force `result: findings`, a brittle parse would close the audit gate on a correct repo. Raised instead as a proposal to share one roster.
- **Requiring a per-file artifact behind `judgment_drift: performed`** (Council 1 load-bearing; Council 2 rejected). Refuted on a ground neither chair saw: the diff-bounded file list would formalize a *narrower* scope than Step 2 specifies, licensing a run that verdicts the diff set and skips the whole-skill sweep — weakening the packet it means to evidence. The list is also exactly as forgeable as the boolean.
- **Making the `identity_term_leakage` inactive-source notice force `findings`.** `judgment_drift: skipped` is agent-caused and agent-clearable; inactive identity is user-state in soft-read-only `a-archive/`, so blocking would create a permanent audit gate the skill can never clear.
- **Widening `SKILL_COUNT_PROSE` to digits.** The fix breaks the check today: both arms share the alternation, so digits make `\bthe\s+(\d{1,3})\b` live and produce nine immediate false positives across five SKILL.md files. At ten working skills the existing regex has two spare.

Also rejected earlier, by the chairs: retiring the `wiki-pages` packet to `lint` (would drop three checks lint does not have), and tagging `file_naming_consistency` "Advisory." (that check also covers wiki pages, attachments and skill folders where auto-rename is correct — the class belongs to the finding's target, not the check).

## Proposals (cross-file, not applied)

1. **Hoist one canonical section/field roster into `multi-skill/scripts/`** and import it in both `check_consistency.py` and `check_wiki.py`, each deriving its own keying. One constant, the drift class gone, no parser to maintain — strictly better than the refuted check.
2. **Reject `<…>`-shaped placeholder values in `_load_identity_terms`.** The live repo's about-me is the unfilled template, so the loader yields `{'<first last>', '<supervisor name; …>'}` — non-empty, so the identity scan reads as *active* while searching for strings that can never appear. A vacuous pass the advisory never fires on.
3. **A deterministic-coverage attestation.** A run invoked with `--packet naming` (2 checks) exits 0 and produces frontmatter byte-identical to a full 27-check pass; `audit` gates on `result:` alone and cannot tell them apart. This is the same unfalsifiability `judgment_drift:` was added to fix, for the script half. Touches the gate contract in CLAUDE.md, so it is a proposal.
4. **A words-only extension of `SKILL_COUNT_PROSE`** (`thirteen`…`twenty`) on the `skills?` arm only, with `expected_word` raising on an unmapped count rather than emitting an unmatchable digit.
5. **A per-check injected-defect test table.** Sixteen of 27 check ids are never named in the test file, and the smoke test iterates findings — so a check returning `[]` passes vacuously. That is precisely how the two broken checks survived.

## Residual, not fixed

- The live `file_naming_consistency` finding still stands. It is now correctly classifiable under item 1 (the fix is a rename, gated on the user by CLAUDE.md → Safety rules), so it no longer blocks — but renaming the file is the user's call, not this run's.
- Item 5 (the Step 5 freeze) and items 6–7 did not go through an individual refuter; both chairs endorsed them after peer review corrected the framing, and they are prose-only. Flagged here rather than presented as gate-passed.
- The vault is empty (zero pages of every type), so the entire `wiki-pages` packet — including the placeholder fix in item 9 — has no live surface. The fix is verified against synthetic pages only.

## Self-report

- **I put a misleading measurement into an advisor's brief.** I told the structure reviewer that `references/checks.md` was "49 lines vs lint's 111", implying a 4× density gap; the real ratio is ~56 versus ~110 words per check. Line counts measure nothing when both files are one-line-per-bullet. The advisor corrected it rather than inheriting it — but a brief that ships a wrong premise is a brief that can manufacture a finding. → upgrade: the skill should require every measurement in a task brief to be stated in the unit the finding will be argued in, and computed, not eyeballed.
- **Five character-count errors this session, one of them by a refuter.** The description refuter certified its own replacement string at 1018 chars; it measured 1029 and would have breached the hard cap had I applied it unmeasured. The refuter gate caught four earlier counting errors and then made the fifth. → upgrade: any edit whose correctness is a measurable quantity should be applied by a script that asserts the quantity, never by an agent asserting it in prose — as this run finally did.
- **The gate keeps refuting the councils, which suggests the councils are mis-tuned rather than merely enthusiastic.** Six of nine load-bearing proposals fell, matching the `ingest` and `lint` runs earlier today. Two of the six were refuted by facts a single `grep` would have surfaced before the proposal was written. → upgrade: require each advisor to state, for its strongest finding, the one check that would falsify it and the result of running that check.
