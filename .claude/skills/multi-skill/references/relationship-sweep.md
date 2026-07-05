# Relationship sweep

The shared method for relating a concept/entity to the pages the vault already holds, so cross-cluster and cross-paradigm relationships are found on purpose rather than by free association. Two skills run it: `ingest` (Step 3, for every new or updated concept/entity page, over the pages that ingest creates or touches) and `audit` (its connection-completeness check, against the whole inventory).

The failure this fixes: an open-ended "propose a few weak-tie links" instruction makes the model satisfice — it names one or two obvious links and stops, and the subtle ones (a concept's counterpart in a different framework or paradigm) are silently dropped. The sweep replaces free association with an inventory pass, a fixed relationship taxonomy, and a visible account of what was checked.

## Method

1. **Load the inventory.** Use `1-wiki/index.md` (read in Step 1) — every existing concept, entity, and synthesis page.
2. **Group the inventory by functional role, not by source or framework.** A role is what the idea *does* — the slot it fills among alternatives — independent of which paper, framework, or domain introduced it. Derive the roles from the corpus and the index clusters rather than a fixed list. The roles depend on the corpus: a multi-agent-systems corpus might have roles like communication topology, interaction protocol, member selection, message content, communication paradigm, and agent configuration; an optimization corpus would have search strategy, update rule, convergence criterion, and regularizer — derive them the same way, from what the ideas do. The point of grouping by role is that it puts a new concept next to its counterparts in *other* frameworks, which is exactly where the missed links live.
3. **Identify the new concept's role(s).** A concept can sit in more than one.
4. **Walk the same-role concepts across every framework and paradigm — not only the new source's.** This is the cross-paradigm pass and the heart of the sweep. For each existing concept that shares a role, classify the relationship using the taxonomy below.
5. **Do not stop early.** Walk the inventory role by role. For each role-cluster, either surface a relationship or state explicitly that there is no related page in that cluster. A cluster checked and found empty is recorded, not skipped — that record is what makes a miss visible.
6. **Produce a relationship map**: the concept's role(s); for each role-cluster, the related existing pages with their relationship type and proposed destination; and the clusters with nothing related. `ingest` posts this in its Step 3 context message so the user can point at a miss before drafting; `audit` records it as connection-completeness findings.

## Relationship Taxonomy

Each relationship has a type and a destination. Unless noted, the edit is reciprocal — make it on both pages.

- **Same-as / duplicate / alias** — the new idea already has a page under different wording. Do not create a new page; update the existing one and add the new wording to its `aliases:`. (This is the merge case, not a link.)
- **Specialization-of / generalization-of (is-a)** — the new concept is a kind of an existing one, or the reverse. Destination: `Connections` on both pages, naming the parent/child relationship.
- **Part-of / component-of / composed-of** — the new concept is a component of an existing one, or is built from existing ones. Destination: `Connections` on both pages.
- **Parallel / cross-paradigm analogue** — an existing concept plays the *same role in a different framework or paradigm*, even when the mechanism differs (for example a member-selection step in one framework and a member-recruitment step in another). Destination: `Connections` on both pages, naming the shared role and the analogue; **and** a `Not This` bullet on each to draw the line between them. This is the most-missed type — seek it deliberately for every new concept.
- **Contrast / easily-confused-with** — a neighbouring concept a reader would mix up with this one. Destination: `Not This` on both pages, stating the distinguishing difference.
- **Enables / depends-on / mechanism-for** — the new concept enables, relies on, or is the mechanism behind an existing one (a functional or causal link). Destination: `Connections` on both pages, carrying the reason for the link (per CLAUDE.md → Plain-Language Style, "Claims carry their reason").
- **Contradicts / in-tension-with** — the new concept disputes a claim an existing page makes. Destination: reciprocal `Contradictions` bullets on both pages (never resolve by deleting a side), and `status: needs-update` on the existing page only when the dispute is load-bearing for it. This overlaps the Step 3 contradiction cross-check; record it once.

## Cross-Paradigm Emphasis

A paradigm or framework is a self-contained approach with its own vocabulary; the same functional role recurs across them under different names, and those recurrences are the parallels this pass hunts.

For every new concept, ask explicitly: *what is its closest counterpart in each other framework or paradigm the vault holds?* A counterpart that plays the same role is a parallel and earns a `Connections` link even if its mechanism is different; if it is close enough to be confused, also add a `Not This` to mark the difference. A new concept that ends up with links only to pages from its own source is the signature of a sweep that was not actually run across paradigms — go back and walk the other clusters.

## Reciprocity

Every `Connections`, `Not This`, and `Contradictions` edit is mirrored on the other page. One-sided links are a known lint/audit finding. The reciprocal edit on the existing page is part of the approved action for that relationship, not a separate later pass — this is the half that gets missed at ingest and only surfaces in audit.

## Worked Example

Continuing the optimization-corpus illustration from step 2: the new concept is `adaptive-moment-estimation` (Adam, from a new optimizer ingest). Role: update rule — how each step turns the gradient into a parameter update.

- Walk the update-rule role across frameworks. `rmsprop` plays the same role in a different optimizer → **parallel / cross-paradigm analogue**: add `Connections` on both naming the shared update-rule role, and a `Not This` on both (Adam keeps a bias-corrected running mean of the gradient — a momentum term — on top of the per-parameter variance scaling; RMSProp scales by the variance alone — different update rules for the same role).
- `gradient-descent` is the parent idea → **generalization-of**: `Connections` on both.
- `bias-correction` is the mechanism that removes the startup bias in Adam's moment estimates → **enables / mechanism-for**: `Connections` on both, with the reason.
- No related page in the attention cluster (`scaled-dot-product-attention` and its neighbours) or the pretraining-objective cluster (BERT's masked language modelling and its neighbours) → recorded as "none" in the map.

The parallel to `rmsprop` is the link the old approach missed; the role-walk is what surfaces it.
