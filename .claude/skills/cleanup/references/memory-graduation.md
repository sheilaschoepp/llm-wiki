# cleanup — Memory Graduation Classification (Step 3)

The detailed classification logic the memory job assigns from. SKILL.md Step 3 names each entry's permanent home and verifies the substance is actually present there — matching the entry's direction, not just its subject; this file holds the six categories it chooses among, the tie-break order, the sensitive-content screen, and the keep-vs-graduate-vs-delete judgement. The outputs job never loads this.

## Contents

- Categories
- Tie-Break When Two Categories Fit
- Sensitive-Content Screen
- Keep, Graduate, Or Delete Is A Judgement, Not A Count
- Age Is A Hint, Not A Trigger

## Categories

Assign each entry exactly one category:

- **graduated** — the rule's substance is fully present in its home, in the correct tier, and the home does not contradict it. Candidate for removal. If the substance is present but in the wrong tier (a schema rule sitting in a `SKILL.md`, a cross-skill rule duplicated into a per-skill file, a behavioural rule in `CLAUDE.md` that belongs in `MEMORY.md`), or appears in more than one home at once (e.g. both `MEMORY.md` and a `CLAUDE.md` section — over-graduation), do not mark it safe-to-clear: this is recorded as `Category: graduated` with a `Flag:` of `mis-homed` or `over-graduated` (counted under summary line G, not the safe-to-clear A), so the user can consolidate to the single correct tier — behavioural rule keep the `MEMORY.md` copy, wiki-structure or schema rule keep the `CLAUDE.md` copy — then clear the journal entry. Exception: a schema rule present in both `CLAUDE.md` and a `SKILL.md` is the sanctioned schema-to-runtime mirror (CLAUDE.md documents rules for project-level reference; each skill carries its own runtime copy and does not rely on it), not over-graduation — treat it as correctly homed and do not propose consolidating it.
- **partial** — the core is present but a specific clause is missing (e.g. the rule is in CLAUDE.md but an exception it carries is not). Propose the missing delta.
- **not-graduated** — the substance is absent from MEMORY.md, CLAUDE.md, and the relevant skill, and the common-sense test below says it belongs in one of them. Before concluding absence, widen the grep past the entry's literal terms to synonyms and paraphrases of the rule — a graduated rule may have been reworded in its home since, and matching only the entry's original wording would false-negative it to not-graduated and re-propose a duplicate (the over-graduation flagged under G). Propose where it should live and the exact text to add.
- **contradicted** — the current schema or skill states something that disagrees with the entry. The entry is stale, not graduated. Flag it for a decision; do not propose silently deleting it as if it were absorbed.
- **keep-in-memory** — the entry belongs where it is and will be useful again, in either of two ways: (a) a journal entry that is situational but recurring (a lesson tied to a class of sources, frames, or situations that will come up again — too specific for the rulebook, but the next member of that class will need it) or still provisional (a fresh correction that may yet be revised); or (b) a `MEMORY.md` entry that is a stable behavioural rule already in its terminal home — settled, not headed onward to `CLAUDE.md` or a `SKILL.md`. Record it with a one-line reason; it stays.
- **spent** — the entry was used by a single past operation, carries no reusable kernel, and its situation will not recur. It has done its job. Propose deleting it (gated on approval, like any deletion). git history and the original ingest/operation report already preserve what happened — the journal is a working pad, not the archive. Before deleting, check once for a general kernel worth graduating; if there is one, graduate that and then delete.

## Tie-Break When Two Categories Fit

Apply the first that matches: (1) `contradicted`, if the home states a rule that actively disagrees with the entry (not merely a narrower version); (2) `graduated`, if the home states the entry's do/never *and* every clause and exception the entry carries — the clause check is part of the graduated gate, so an entry whose home has the main rule but is missing one exception is not graduated; (3) `partial`, if the home states the do/never but is missing a specific, nameable clause the entry carries — if you cannot name the missing clause, it is not partial; (4) `not-graduated`, if the entry's do/never is absent from every home it should live in (a home documenting only the subject or mechanism counts as absent) — but a `MEMORY.md` entry that is a stable behavioural rule whose only correct home is `MEMORY.md` itself is already home, so it is `keep-in-memory` (terminal), never `not-graduated`; (5) `keep-in-memory` / `spent`, only for entries with no general rule to graduate. A home stating a weaker-scoped version of the rule is `partial` (name the missing scope), never `contradicted`.

## Sensitive-Content Screen

Before proposing any graduation into `MEMORY.md` or `CLAUDE.md`, screen the entry against CLAUDE.md → Memory hygiene (no medical, family, relationship, financial, or legal specifics about anyone). If the entry carries such content, do not propose graduating it — graduation would push the violation into a more permanent, more-read home. Instead route it to the Step 7 per-item gate as a hygiene-flagged entry (redact in place, or remove from the journal — its own gated decision), so a hygiene-violating entry is acted on, not just flagged and left resident.

## Keep, Graduate, Or Delete Is A Judgement, Not A Count

The keep / graduate / delete call is a common-sense judgement about the content, not a frequency count. An entry is written to memory once — it does not need to recur, be re-confirmed across sessions, or appear N times before it can graduate. Read what the entry actually says and ask two questions:

1. **Is there a stable, general rule in it?** A rule that would apply across future operations and is not bound to a single source, frame, or one-time incident belongs in its permanent home (MEMORY.md, CLAUDE.md, or the skill) → not-graduated, propose the graduation now.
2. **If not general — will its situation recur?** A lesson tied to a class of situations that will happen again → keep-in-memory. A lesson tied to one past operation that will not happen again, with nothing reusable left → spent, propose deletion.

## Age Is A Hint, Not A Trigger

Age is a hint for this judgement, not a trigger. Journal entries (the per-skill and multi-skill files) carry their date in the `## YYYY-MM-DD` heading, so the audit can compute their age. `MEMORY.md` entries use topic headings with no date, so age is not available there. Where age is available, use it only to sharpen the spent-vs-keep call: an old, never-graduated, one-off-looking journal entry is a strong spent candidate worth proposing for deletion. Never expire an entry on age alone — a long-dormant situational entry is still valuable the moment its class of situation recurs, so recurrence, not the clock, decides.

CLAUDE.md's graduation-path phrase "held up across multiple operations" means the rule has proven durable (it was not later contradicted or revised), not that it was recorded repeatedly. Durability and generality are the test; repetition is not.
