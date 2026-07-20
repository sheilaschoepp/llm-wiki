#!/usr/bin/env python3
"""Mechanical wiki structural checks (subset of lint/SKILL.md's check battery).

The list below is a REPRESENTATIVE sample, not the full emitted set. The
canonical check_id -> severity map is the `CHECKS` registry near the top of this
module; run `check_wiki.py --list-checks` to print it as JSON (the machine-
readable target the consistency skill / docs diff the SKILL.md Checks section
against). Covers the deterministic subset Claude shouldn't have to do by hand:
- frontmatter completeness per page-type (check_id: `frontmatter_missing`)
- source_count vs len(sources) mismatch (input to lint's auto-fix)
- body section order via callout slugs (check_id: `section_order`)
- callout block IDs present, correct, and last-line (check_id: `callout_block_id`)
- page locators carry `#page=N` raw-file deep-links (check_id: `page_locator_unlinked`)
- source-page locators list the section anchor and page together inside the link (check_id: `source_locator_incomplete`)
- bullet-initial wikilink displays are capitalized (check_id: `wikilink_display_uncapitalized`)
- index.md vs filesystem drift (check_id: `index_missing_entry` / `index_stale_entry`)
- log.md / hot.md Recent activity are timed and newest-first (check_id: `chronology_missing_time` / `chronology_out_of_order`)
- zero-source pages (check_id: `zero_source_page`)
- status:draft inventory (check_id: `status_draft`)
- status:needs-update inventory (check_id: `status_needs_update`, standing)
- kebab-case filenames (check_id: `filename_not_kebab`)
- wikilink pipe spacing (check_id: `wikilink_pipe_spacing`, auto-fixable)
- hyphenated established open compounds (check_id: `hyphenated_open_compound`)
- bare-basename wikilinks (check_id: `bare_basename_link`)
- source-page stem vs raw stem (check_id: `source_stem_mismatch`)

Output: JSON list of findings (severity `error` -> report Critical, `warning` ->
Warning, `info` -> Info), printed to stdout.
Status-quo behaviour: read-only — no edits. Auto-fixes are described in lint/SKILL.md Step 3 prose; this script only surfaces findings.
Exit code: 1 if any `error`-severity finding remains except the STANDING_NONBLOCKING
set (expected repo states); 0 otherwise. Provided so a CI step or hook *could*
gate on blocking drift; the lint skill itself consumes the JSON findings, not the
exit code.

Plain-language, old citation-clutter, source-support, and note-atomicity checks
stay with the LLM because they need bullet-level reading and judgement.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

# Reuse the ONE shared body hasher (audit stamps with it; lint detects drift with
# it) rather than replicating its masking — see body_hash.py's docstring. Insert the
# script's own directory so the import resolves whether run as a script or imported.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from body_hash import body_hash  # noqa: E402

# Stale-draft threshold in days (D 11.5/6). Lint flags pages with
# status:draft and updated: older than this as Info-level. Audit's 60-day
# stale-draft check catches them later; this is the earlier nudge.
STALE_DRAFT_DAYS = 14

# Stale needs-update threshold in days (D 5.5b). The whole point of
# `needs-update` is that something demands attention; a page sitting at
# that status untouched for a month means the demand is being ignored.
# Lint flags as Warning (higher severity than stale_draft because the
# page is already known-broken).
STALE_NEEDS_UPDATE_DAYS = 30

# Empty-placeholder bullet strings. A callout whose only non-empty body
# bullet matches one of these is an empty placeholder (D X.4).
EMPTY_PLACEHOLDERS = (
    '> - None noted',
    '> - None yet',
)

# Jaccard threshold for near-duplicate concept/entity H1 detection
# (check_duplicate_concepts). 0.75 was picked empirically against the
# vault: 0.6 flagged unrelated pairs sharing common stopwords (two
# concepts that share a generic word but mean different things); 0.85
# missed real near-twins like a hyphenated short form versus its
# spelled-out long form, or a base concept versus the same concept with
# a trailing qualifier. 0.75 caught the latter without false positives
# while leaving genuinely distinct sibling concepts alone. Tune as the
# corpus grows — lower if real near-twins slip through, raise if
# legitimate sibling concepts get flagged.
JACCARD_THRESHOLD = 0.75

# Thresholds for intra_page_redundancy: two bullets on ONE concept/entity/
# synthesis page that make the same point across (or within) callouts — the
# CLAUDE.md "do not paraphrase the same point across sections" rule. This is the
# cheap lexical half; the semantic half (reworded repeats) lives in ingest's
# note-quality packet and audit's walk. Two arms, because redundancy shows up two
# ways:
#   - Jaccard arm catches near-twin bullets of similar length (a point copied
#     into two sections with light edits).
#   - Overlap-coefficient arm (|A∩B| / min(|A|,|B|)) catches CONTAINMENT — a
#     short bullet whose whole point is folded inside a longer bullet, where
#     Jaccard is dragged down by the longer bullet's extra tokens.
# Comparison is over content tokens only (wikilinks, citations, markers, and
# stopwords stripped), so two bullets that merely cite the same source or share
# function words do not collide. MIN floors keep short, low-content bullets from
# matching on a handful of shared words. Tune against the vault: raise if
# legitimate cross-section references get flagged, lower if real repeats slip by.
BULLET_JACCARD_THRESHOLD = 0.6
BULLET_OVERLAP_THRESHOLD = 0.8
MIN_BULLET_CONTENT_TOKENS = 5   # both bullets, Jaccard arm
MIN_OVERLAP_SHORTER_TOKENS = 6  # the shorter bullet, overlap arm (≥ a real point)

# Function words and wiki-generic terms stripped before redundancy comparison.
# Deliberately small — content words carry the signal; this just removes the
# high-frequency glue (and a few schema-ubiquitous words like "source"/"page")
# that would otherwise inflate overlap between unrelated bullets.
REDUNDANCY_STOPWORDS = frozenset({
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'because', 'been', 'both',
    'but', 'by', 'can', 'does', 'each', 'for', 'from', 'has', 'have', 'in',
    'into', 'is', 'it', 'its', 'not', 'of', 'on', 'one', 'only', 'or', 'over',
    'so', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these',
    'they', 'this', 'those', 'to', 'two', 'up', 'via', 'was', 'were', 'when',
    'where', 'which', 'while', 'who', 'whole', 'with', 'within',
    'page', 'source', 'sources',
})

# Per-type required frontmatter fields (CLAUDE.md source pages /
# concept/entity pages / synthesis pages).
REQUIRED_FIELDS: dict[str, list[str]] = {
    'paper': ['type', 'title', 'authors', 'venue', 'year', 'file', 'tags',
              'frames', 'created', 'updated', 'status'],
    'article': ['type', 'title', 'authors', 'venue', 'year', 'file', 'tags',
                'frames', 'created', 'updated', 'status'],
    'media': ['type', 'title', 'file', 'tags', 'frames', 'created', 'updated',
              'status'],
    'other': ['type', 'title', 'file', 'tags', 'frames', 'created', 'updated',
              'status'],
    'concept': ['type', 'aliases', 'sources', 'source_count', 'tags',
                'created', 'updated', 'status'],
    'entity': ['type', 'aliases', 'sources', 'source_count', 'tags',
               'created', 'updated', 'status'],
    'synthesis': ['type', 'sources', 'source_count', 'origin', 'tags',
                  'created', 'updated', 'status'],
}

# Required callout-slug sequence per page type (CLAUDE.md "Body sections as
# callouts"). Concepts and entities share the concept/entity page template.
REQUIRED_SECTIONS: dict[str, list[str]] = {
    'paper': ['tldr', 'contribution', 'key-claims', 'evidence', 'method',
              'assumptions', 'limitations', 'appraisal', 'concepts-entities',
              'contradictions', 'open-questions', 'connections'],
    'article': ['tldr', 'contribution', 'key-claims', 'evidence', 'method',
                'assumptions', 'limitations', 'appraisal',
                'concepts-entities', 'contradictions', 'open-questions',
                'connections'],
    'media': ['tldr', 'contribution', 'key-claims', 'evidence', 'method',
              'assumptions', 'limitations', 'appraisal', 'concepts-entities',
              'contradictions', 'open-questions', 'connections'],
    'other': ['tldr', 'contribution', 'key-claims', 'evidence', 'method',
              'assumptions', 'limitations', 'appraisal', 'concepts-entities',
              'contradictions', 'open-questions', 'connections'],
    'concept': ['idea', 'why', 'not-this', 'examples', 'contradictions',
                'disconfirming', 'open-questions', 'connections', 'sources'],
    'entity': ['idea', 'why', 'not-this', 'examples', 'contradictions',
               'disconfirming', 'open-questions', 'connections', 'sources'],
    'synthesis': ['question', 'answer', 'scope', 'evidence', 'tensions',
                  'what-would-change-this', 'open-questions', 'connections',
                  'sources'],
}

# Callout block ID = kebab-case of the callout's display title, which for most
# callouts equals the callout-type slug but diverges where the schema picked an
# abbreviated type. These are the only divergences (CLAUDE.md -> Callout Block
# IDs); every other callout's block ID is its type slug. `tldr` is an acronym
# title and deliberately keeps its compact `^tldr` (identity, so not listed).
BLOCK_ID_OVERRIDES = {
    'why': 'why-it-matters',
    'disconfirming': 'disconfirming-evidence',
    'what-would-change-this': 'what-would-change-this-answer',
}


def expected_block_id(slug: str) -> str:
    """The block ID a `[!{slug}]` callout must carry (CLAUDE.md -> Callout Block
    IDs): the type slug, unless the type is abbreviated below its display title."""
    return BLOCK_ID_OVERRIDES.get(slug, slug)


VALID_STATUSES = {'draft', 'verified', 'needs-update'}

# Source-page kinds (detect_page_kind returns the `type:` value for source
# pages: paper/article/media/other). Checks that apply only to source pages —
# whose locator/citation form differs from concept/entity/synthesis pages —
# gate on this set.
SOURCE_KINDS = {'paper', 'article', 'media', 'other'}

# Standing repo-state findings that lint emits at `error` (report Critical) but
# that are NOT audit-blocking and do NOT fail the script exit code: a
# `needs-update` page and an uningested raw are expected, ongoing repo states,
# not structural drift. CLAUDE.md -> Audit preconditions defines exactly this
# set as the standing exceptions the audit-blocking gate excludes; the script's
# exit code and lint's `result:` computation must use the same set so all three
# (exit code, `result:`, audit gate) agree. `uningested_raw_source` is
# CLAUDE.md's name for the same standing condition the script emits as
# `raw_without_source_page`; both are listed so the set matches CLAUDE.md
# verbatim and stays forward-compatible.
STANDING_NONBLOCKING = {
    'raw_without_source_page',
    'uningested_raw_source',
    'status_needs_update',
}

# Canonical check registry: check_id -> report severity ('error' renders
# as Critical, 'warning' as Warning, 'info' as Info). Single source of
# truth for severity — finding() derives each finding's severity from here,
# so a check's severity is set in exactly one place. `zero_source_page` is
# dual (error for synthesis pages, warning for concept/entity), so it maps
# to None and its severity is supplied at the call site. Run the script with
# `--list-checks` to print this registry as JSON (a machine-readable target
# the consistency skill / docs can diff the SKILL.md Checks section against).
CHECKS: dict[str, str | None] = {
    'alias_collision': 'warning',
    'alias_shadows_filename': 'warning',
    'attachment_duplicate_basename': 'info',
    'attachment_orphan': 'info',
    'attachments_file_unlisted': 'warning',
    'attachments_frontmatter_missing_file': 'warning',
    'bare_basename_link': 'info',
    'callout_block_id': 'warning',
    'chronology_missing_time': 'warning',
    'chronology_out_of_order': 'warning',
    'citation_bracket_style': 'warning',
    'citation_locator_incomplete': 'warning',
    'citation_unpaired': 'warning',
    'concept_duplicate_candidate': 'warning',
    'concept_multi_image': 'warning',
    'concept_source_asymmetry': 'warning',
    'embed_not_isolated': 'warning',
    'embed_unresolved': 'error',
    'file_field_unresolved': 'error',
    'filename_not_kebab': 'info',
    'frontmatter_missing': 'error',
    'frontmatter_missing_field': 'warning',
    'hyphenated_open_compound': 'warning',
    'hyphenated_open_compound_noun': 'warning',
    'index_missing_entry': 'warning',
    'index_stale_entry': 'warning',
    'intra_page_redundancy': 'warning',
    'locator_page_mismatch': 'error',
    'missing_index': 'error',
    'missing_reciprocal_contradiction': 'warning',
    'needs_update_without_reason': 'warning',
    'orphan_page': 'info',
    'page_locator_unlinked': 'warning',
    'pagination_map_unregistered': 'info',
    'placeholder_only_page': 'info',
    'raw_without_source_page': 'error',
    'recursive_wiki_citation': 'warning',
    'section_order': 'warning',
    'source_context_leak': 'warning',
    'source_count_mismatch': 'warning',
    'source_link_unresolved': 'warning',
    'source_locator_incomplete': 'warning',
    'source_stem_mismatch': 'info',
    'sources_callout_desync': 'warning',
    'stale_draft': 'info',
    'stale_mention_ignore': 'warning',
    'stale_needs_update': 'warning',
    'status_draft': 'info',
    'status_invalid': 'warning',
    'status_needs_update': 'error',
    'synthesis_under_supported': 'warning',
    'unlinked_page_mention': 'warning',
    'unverified_claim': 'info',
    'vague_source_referent': 'warning',
    'verified_anchor_unaudited': 'error',
    'verified_hash_mismatch': 'warning',
    'wikilink_display_uncapitalized': 'warning',
    'wikilink_pipe_spacing': 'warning',
    'zero_source_page': None,
}

# Callout markers that lint reads (the line under section headers).
CALLOUT_RE = re.compile(r'^> \[!([a-z-]+)\]', re.MULTILINE)

# Callout block-ID line — `> ^slug` as the last line inside a callout (see
# CLAUDE.md -> Callout Block IDs). It is an invisible link anchor, not body
# content, so placeholder/empty-section detection must skip it. Tolerates a
# leading-whitespace-stripped form (`> ^slug`) as well as the raw `> ^slug`.
# Group 1 captures the slug, used by the callout_block_id check.
BLOCK_ID_RE = re.compile(r'^>\s*\^([a-z0-9-]+)\s*$')

# A `p. N` / `pp. N–M` page locator that is NOT already a link alias (the
# negative lookbehind for `|` skips the display text of a `[[...#page=N|p. N]]`
# link). Per CLAUDE.md -> Source Support And Verification, every page locator on
# a wiki page carries a `#page=N` raw-file deep-link, so a bare match is drift.
PAGE_LOCATOR_RE = re.compile(r'(?<!\|)\bpp?\. ?\d+(?:[–-]\d+)?')

# Canonical inline citation form (CLAUDE.md -> Source Support And Verification):
# a source-page wikilink followed by a parenthesized raw deep-link whose display
# carries both a structural anchor and a printed page. These regexes drive the
# mechanical citation-form checks on concept/entity/synthesis pages.
# An inline raw-source deep-link used as a citation: group 1 is its display text.
CITATION_DEEPLINK_RE = re.compile(r'\[\[0-raw/[^\]]*#page=\d+\|([^\]]*)\]\]')
# The same deep-link, capturing the two keys the pagination map needs: group 1 is
# the raw path (`0-raw/papers/<stem>.pdf`), group 2 the physical page N. Kept
# separate from CITATION_DEEPLINK_RE so that regex's `group(1) == display` stays
# stable for its existing callers.
CITATION_DEEPLINK_KEY_RE = re.compile(r'\[\[(0-raw/[^\]#|]+)#page=(\d+)\|')
# The printed-page NUMBER cited in a display: `p. M` (single page only — `pp.`
# ranges are intentionally not matched, so locator_page_mismatch stays
# conservative). `\b`-guarded so the `p.` inside `app.` never matches.
CITATION_PAGE_NUM_RE = re.compile(r'\bp\.\s?(\d+)\b(?!\s*[–-]\s*\d)', re.IGNORECASE)
# A structural anchor inside a citation display: section/appendix/chapter,
# figure/table/equation, OR theorem-environment result — definition/theorem/lemma/
# proposition/corollary/algorithm (the CLAUDE.md anchor set), plus the front-matter
# sections that have no number — `abstract` (and `intro`/`introduction` when used as
# the named anchor). The abstract is a real, citable structural location; forcing
# abstract content into `sec. 1` mislabels it, since on most papers sec. 1 is not
# even on the abstract's page.
CITATION_ANCHOR_RE = re.compile(
    r'\b(?:sec|app|ch|chap|fig|tab|eq|def|thm|lem|prop|cor|alg)\.|§|\babstract\b',
    re.IGNORECASE)
# A printed-page token inside a citation display: `p. M` / `pp. M–N`.
CITATION_PAGE_RE = re.compile(r'\bpp?\.\s?\d', re.IGNORECASE)
# The unpaginated-supplement exemption (CLAUDE.md -> Source Support And
# Verification): a published appendix often carries no printed page number, so an
# `app.`-anchored display cites the anchor alone (`app. D.1, tab. 8`) rather than
# fabricating a `p. M` no reader can find on the page. Only `app.` earns the
# exemption — a `sec.`/`fig.`/`tab.`-only display is still incomplete. The cost is
# that a *paginated* appendix can now drop its `p. M` unflagged; that is audit's
# call to make against the raw, and the schema prefers a missing page to an
# invented one.
CITATION_APPENDIX_ANCHOR_RE = re.compile(r'\bapp\.', re.IGNORECASE)


def locator_display_complete(*, display: str,
                             raw: str | None = None,
                             phys: int | None = None) -> bool:
    """Whether a `#page=N` deep-link display carries a complete locator: a
    structural anchor AND a printed page, with the page requirement relaxed for a
    genuinely unpaginated region.

    When `raw` and `phys` are supplied and the pagination map covers that page,
    the map is authoritative: a page that PRINTS a number must carry `p. M`
    (`app.` earns no exemption there — a paginated appendix still needs its
    page), and a page that prints NOTHING may stand on its structural anchor
    alone. When the raw is unregistered (or the keys are not supplied), fall back
    to the display-only heuristic: an `app.`-anchored display may omit the page
    (the unpaginated-supplement exemption), any other anchor still needs one.
    Shared by citation_locator_incomplete and source_locator_incomplete so the
    two page types cannot drift apart on what "complete" means.
    """
    if not CITATION_ANCHOR_RE.search(display):
        return False
    has_page = bool(CITATION_PAGE_RE.search(display))
    if raw is not None and phys is not None:
        status, _ = printed_page(raw=raw, phys=phys)
        if status == 'paginated':
            return has_page          # the page prints a number — it must be cited
        if status == 'unpaginated':
            return True              # the page prints nothing — anchor alone is OK
        # 'unregistered' — fall through to the display-only heuristic below
    return has_page or bool(CITATION_APPENDIX_ANCHOR_RE.search(display))
# The leading structural-anchor TOKEN of a locator display (with its number, so
# `sec. 3.2` and `sec. 4` are distinct), used to tell an anchor CHANGE from a
# relocation: `sec. 3.2`, `app. C`, `fig. 4`, `tab. 8`, `eq. 3`, `ch. 2`,
# `thm. 3.1`, or the unnumbered `abstract`. En dash / hyphen allowed for ranges (`sec. 3.2-3.3`).
LOCATOR_ANCHOR_TOKEN_RE = re.compile(
    r'\b(?:sec|app|ch|chap|fig|tab|eq|def|thm|lem|prop|cor|alg)\.\s?[\w.–-]*'
    r'|\babstract\b', re.IGNORECASE)
# A source-page wikilink in citation form (no `#^callout` section anchor).
SOURCE_PAGE_LINK_RE = re.compile(r'\[\[1-wiki/sources/[^\]|#]+\.md\|[^\]]*\]\]')
# A callout body bullet that opens with a wiki-PAGE wikilink: `> - [[1-wiki/…|display]]…`.
# Group 1 is the display text. Tolerates indented sub-bullets (`>   - `). Only
# matches when the wikilink is the first content on the bullet (sentence-initial),
# which is what the leading-capital rule keys on (CLAUDE.md -> Wikilink Format).
# Scoped to `1-wiki/` targets so a bullet opening with a raw-file locator deep-link
# (`[[0-raw/…#page=5|p. 5]]`, a page token, not a page name) is not force-capitalized.
BULLET_INITIAL_WIKILINK_RE = re.compile(
    r'^>[ ]*-[ ]+\[\[1-wiki/[^\]|]+\|([^\]]*)\]\]', re.MULTILINE)
# The superseded square-bracket Form 2 citation: a source-page wikilink plus one
# or more raw deep-links wrapped in a literal outer `[ ]` (rendering `[key; loc]`),
# which surfaces as the triple-bracket `[[[` opener. CLAUDE.md -> Source Support
# And Verification now mandates the round-bracket form `(key; loc)`; this catches
# the old form. Group 1 is the inner content. The auto-fix is applied only within
# the code-/Sources-/quote-masked scan `check_citation_bracket_style` builds, and
# per flagged occurrence: swap the outer `[ ]` for `( )`, leaving the inner wikilinks
# untouched. Never a global `SQUARE_CITATION_RE.sub(r'(\1)', body)` over the unmasked
# body — that would rewrite a `[[[…]]]`-shaped literal inside a quote, the false green
# the mask exists to prevent.
SQUARE_CITATION_RE = re.compile(
    r'\['                                              # literal outer [
    r'(\[\[1-wiki/sources/[^\]|#]+\.md\|[^\]]*\]\]'    # source-page wikilink
    r'(?:;[ ]*\[\[0-raw/[^\]]*\]\])+'                  # ; + one or more raw deep-links
    r')\]'                                             # literal outer ]
)

# The claim-level "awaiting a raw fact-check" marker (CLAUDE.md -> Bullet Markers).
# Surfaced for visibility as the audit-pending delta on otherwise-verified pages.
# NOTE: this pattern is duplicated as `_UNVERIFIED_RE` in body_hash.py (there it
# masks marked lines from the hash; here it counts them). The two must stay
# identical, or counting (here) and masking (there) silently disagree — change both.
UNVERIFIED_MARKER_RE = re.compile(r'\*\[unverified\]\*')

# Source-context phrases — concept/entity pages must read as standalone ideas,
# not as summaries of a particular paper. These phrases tie the bullet's
# meaning back to the source rather than expressing the idea on its own
# terms. See D 3.11 in the design-decisions catalogue.
SOURCE_CONTEXT_PHRASES = re.compile(
    r'\b(as the (?:paper|authors?|source|study|work) (?:note[sd]?|state[sd]?|'
    r'shows?|argue[sd]?|find[s]?|claim[sd]?|suggest[sd]?)|'
    r'the (?:paper|authors?|study|work) (?:notes?|states?|shows?|argues?|'
    r'finds?|claims?|suggests?|propose[sd]?|introduce[sd]?|demonstrate[sd]?)|'
    r'according to (?:the (?:paper|authors?|source|study)|\[\[[^\]]+\]\])|'
    r'in this (?:paper|work|study|article)|'
    r'this (?:paper|work|study|article) (?:notes?|states?|shows?|argues?|'
    r'finds?|claims?|introduces?))\b',
    re.IGNORECASE,
)

# Vague source referents — when a concept/entity/synthesis bullet attributes a
# claim or caveat to a source, it must name that source (a pipe-rendered
# wikilink, or the named system where that reads naturally), never a bare "the
# source" / "a source" / "one framework" / "one study". These pages accrue more
# sources over time, so an unnamed referent that is unambiguous at one source
# becomes ambiguous at two. See CLAUDE.md -> Plain-Language Style.
# Distinct from source_context_leak (D 3.11): that flags source-FRAMING to be
# removed ("as the paper notes" -> state the idea standalone); this flags an
# UNNAMED source to be named. They can overlap on a definite-artifact line that
# also carries a framing verb ("the paper notes ..."), where both fixes apply
# (name it and/or re-voice it); that double flag is acceptable, not a bug.
_ATTRIB_VERB = (
    r'note[sd]?|argue[sd]?|state[sd]?|show(?:s|ed)?|find[s]?|found|'
    r'claim(?:s|ed)?|report(?:s|ed)?|suggest(?:s|ed)?|propose[sd]?|'
    r'demonstrate[sd]?|introduce[sd]?|observe[sd]?|describe[sd]?'
)
_VAGUE_NOUN = r'source|framework|study|paper|work|survey|article|preprint'
# Definite/demonstrative references to a source artifact ("the paper", "this
# survey", "the study", "the article", "the preprint", "the source", "the
# authors") are essentially always the unnamed source on a concept/entity/
# synthesis page, so they are flagged WITHOUT a verb gate — an enumerated verb
# list was too narrow and silently missed "the survey points to", "the paper
# does not measure", "the survey groups", etc. "framework/method/system/work"
# are deliberately NOT in this arm: a definite "the framework" usually names the
# page's OWN subject (e.g. an entity page for BERT), not the source. The
# negative lookahead `(?!\s*\[\[)` suppresses the named-appositive form
# "the survey [[1-wiki/sources/...]]", where the source IS named right after.
_SOURCE_ARTIFACT = r'paper|survey|study|article|preprint|source'
VAGUE_SOURCE_REFERENT = re.compile(
    # A vague referent as the subject of an attribution verb: "a source claims",
    # "one study found", "a paper shows".
    r'\b(?:the\s+source|(?:a|an|one)\s+(?:' + _VAGUE_NOUN + r'))\s+'
    r'(?:' + _ATTRIB_VERB + r')\b'
    # Enumerative possessive: "one framework's setup", "the source's claim".
    r"|\b(?:the\s+source|one\s+(?:" + _VAGUE_NOUN + r"))'s\b"
    # Definite/demonstrative reference to a source artifact, verb-free (covers
    # the trailing-possessive "the paper's" / "the survey's" too), unless the
    # source is named immediately after via a wikilink.
    r'|\b(?:the|this|that)\s+(?:' + _SOURCE_ARTIFACT + r')\b(?!\s*\[\[)'
    r'|\bthe\s+authors?\b(?!\s*\[\[)',
    re.IGNORECASE,
)

# Established open compounds that field convention leaves UNhyphenated even when
# used attributively (CMOS 7.89 drops the hyphen when the compound is familiar
# and reads unambiguously). The wiki writes these open ("reinforcement learning
# benchmark", not "reinforcement-learning benchmark"); a hyphenated form is
# drift. Mapping is banned-hyphenated -> open form (the fix the report suggests).
# Deliberately NOT listed, so they are never flagged:
#   - `multi-agent` (and `multi-agent-debate` etc.) — a prefixed compound,
#     universally hyphenated in the field; correct as written.
#   - `foundation-model` — hyphenated as an attributive modifier by convention;
#     left as written.
#   - `in-context` — conventionally hyphenated as a modifier.
# Keys are matched longest-first so `deep-reinforcement-learning` wins over
# `reinforcement-learning`, and `self-supervised-learning` over `supervised-
# learning` (whose `self-`/`deep-` prefix legitimately stays hyphenated).
OPEN_COMPOUND_SUGGEST: dict[str, str] = {
    'deep-reinforcement-learning': 'deep reinforcement learning',
    'self-supervised-learning': 'self-supervised learning',
    'reinforcement-learning': 'reinforcement learning',
    'unsupervised-learning': 'unsupervised learning',
    'supervised-learning': 'supervised learning',
    'imitation-learning': 'imitation learning',
    'transfer-learning': 'transfer learning',
    'machine-learning': 'machine learning',
    'deep-learning': 'deep learning',
    'natural-language': 'natural language',
    'language-models': 'language models',
    'language-model': 'language model',
}
# `\b`-anchored, case-insensitive, longest-first. The trailing `(?!-)` suppresses
# a match inside a longer hyphenated token the schema keeps joined — e.g.
# `natural-language-vs-code` (an "X vs Y" construct), where `natural-language` is
# followed by another hyphen and is left alone.
HYPHENATED_OPEN_COMPOUND = re.compile(
    r'\b(' + '|'.join(
        re.escape(k) for k in sorted(OPEN_COMPOUND_SUGGEST, key=len, reverse=True)
    ) + r')\b(?!-)',
    re.IGNORECASE,
)

# --- Slug-derived open compounds: bidirectional hyphenation check data ---------
# The four lists driving the bidirectional check_hyphenated_open_compound_noun
# check live in an AGENT-WRITABLE DATA FILE, not in this script (CLAUDE.md ->
# Stay In Your Lane). `audit` grows them autonomously — each addition verified by
# sub-agents before it is written — as it confirms hyphenation uses against the
# raw, without ever editing this code. This module only PARSES that file.
#
# The check enforces one rule both ways for a slug-derived compound (one whose
# kebab-case page slug, tool-use / belief-state, leaks into prose): correct OPEN
# as a noun ("tool use is costly"), correct HYPHENATED as an attributive modifier
# ("belief-state representation", CMOS 5.91). The four lists:
#   DISALLOWED (OPEN_COMPOUND_NOUN_SUGGEST): hyphenated -> open. Direction 1 opens
#     a hyphenated bare noun; direction 2 re-hyphenates an open compound before a
#     head noun (an overcorrection).
#   ALLOWED (HYPHENATED_COMPOUND_ALLOWED): keep-hyphenated look-alikes never
#     flagged (proper names like GPT-3, established fine-tuning, prefixed
#     multi-agent). A hard never-flag guard.
#   HEADS (COMPOUND_MODIFIER_HEADS): head nouns that mark a modifier — the
#     direction-2 gate, so a following verb never triggers a hyphen.
#   VERIFIED-IGNORE (HYPHENATION_VERIFIED_IGNORE): confirmed-correct phrases,
#     skipped both directions.
# Data file: .claude/skills/multi-skill/hyphenation-lists.md.
HYPHENATION_LISTS_FILE = Path(__file__).resolve().parent.parent / 'hyphenation-lists.md'


def _load_hyphenation_lists(
    path: Path = HYPHENATION_LISTS_FILE,
) -> tuple[dict[str, str], frozenset[str], frozenset[str], frozenset[str]]:
    """Parse the four `## section` lists from the hyphenation data file.

    Tolerant by design (audit edits this file autonomously): a missing/unreadable
    file returns empty lists (the check silently no-ops — recoverable from git),
    and a malformed line is skipped, never raised. Never crashes lint.
    """
    disallowed: dict[str, str] = {}
    allowed: set[str] = set()
    heads: set[str] = set()
    ignore: set[str] = set()
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return disallowed, frozenset(), frozenset(), frozenset()
    section: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('## '):
            section = line[3:].strip().lower()
            continue
        if section is None or not line.startswith('- '):
            continue
        item = line[2:].strip()
        if not item or item.startswith('<!--'):
            continue
        if section == 'disallowed' and '=' in item:
            hy, _, op = item.partition('=')
            hy, op = hy.strip().lower(), op.strip()
            if hy and op:
                disallowed[hy] = op
        elif section == 'allowed':
            allowed.add(item.lower())
        elif section == 'heads':
            heads.add(item.lower())
        elif section == 'verified-ignore':
            ignore.add(item.lower())
    return disallowed, frozenset(allowed), frozenset(heads), frozenset(ignore)


# --- Verified-ignore list for the unlinked_page_mention check ------------------
# `unlinked_page_mention` is heuristic in the same way the hyphenation check is:
# it matches a page's title/alias in another page's prose, but whether a given
# occurrence is a GENUINE reference or generic wording — a homograph, a common
# noun that happens to be a page title, a term inside a larger established phrase
# — is a judgement CLAUDE.md -> Wikilink Format explicitly leaves to a reader.
# `audit` makes that call per occurrence (audit Step 7) and records a
# confirmed-generic one here, so the next lint run does not re-flag it and the
# next audit does not re-litigate it. This is the escape valve
# HYPHENATION_VERIFIED_IGNORE gives the hyphenation check.
#
# An entry is `page-path :: target-stem :: phrase`. It is scoped to the PAGE the
# judgement was made on — genuine-vs-generic is a per-page call, so an entry
# never suppresses a mention on some other page — and anchored to the PHRASE the
# mention sits in. The phrase anchor makes an entry SELF-INVALIDATING: reword the
# sentence and the entry stops matching, so the mention re-flags. The failure
# mode of a stale entry is therefore a re-flag (safe), never a silently swallowed
# genuine reference. A stale entry suppresses nothing and is inert.
# Data file: .claude/skills/multi-skill/unlinked-mention-ignore.md.
UNLINKED_MENTION_IGNORE_FILE = (
    Path(__file__).resolve().parent.parent / 'unlinked-mention-ignore.md'
)


def _load_unlinked_mention_ignore(
    path: Path = UNLINKED_MENTION_IGNORE_FILE,
) -> list[dict[str, Any]]:
    """Parse the verified-ignore entries, one dict per line: page, target, phrase,
    the 1-based `line` in the data file (so a stale entry can be reported at its
    own line), and the compiled phrase `pattern`.

    Tolerant by design (audit edits this file autonomously): a missing or
    unreadable file returns no entries — the check then runs fully unsuppressed,
    which is the safe direction — and a malformed line is skipped, never raised.
    Never crashes lint.
    """
    entries: list[dict[str, Any]] = []
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return entries
    section: str | None = None
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line.startswith('## '):
            section = line[3:].strip().lower()
            continue
        if section != 'verified-ignore' or not line.startswith('- '):
            continue
        item = line[2:].strip()
        if not item or item.startswith('<!--'):
            continue
        parts = [p.strip() for p in item.split('::')]
        if len(parts) != 3 or not all(parts):
            continue
        page, target, phrase = parts
        entries.append({
            'page': page,
            'target': target,
            'phrase': phrase,
            'line': lineno,
            # Whitespace-flexible: a recorded phrase still matches after a reflow
            # of the line it sits on. Everything else is matched literally, so a
            # reword of the phrase itself correctly stops matching.
            'pattern': re.compile(r'\s+'.join(re.escape(w) for w in phrase.split()),
                                  re.IGNORECASE),
        })
    return entries


UNLINKED_MENTION_IGNORE = _load_unlinked_mention_ignore()


# What each physical page of each raw PDF actually PRINTS. A locator states two
# page facts: where the page sits in the file (`#page=N`, the physical page, for
# the deep-link) and what the page prints (`p. M`, the number a reader cites).
# These diverge whenever a PDF is not paginated 1, 2, 3… from its first physical
# page — proceedings that start at a high number, an appendix that restarts or
# continues, a page that prints no number at all — and the printed number is a
# fact about the raw, not derivable by rule. It is recorded once per raw in
# `.claude/skills/multi-skill/pagination-map.md`, whose header carries the rationale;
# `scripts/pagination_map.py` proposes entries from the PDF and a human confirms
# each against a rendered footer. check_wiki.py never opens a PDF — it reads only
# this map — so lint stays cheap and dependency-free. The map drives the
# anchor-only exemption in the two locator-completeness checks and the
# `locator_page_mismatch` check.
PAGINATION_MAP_FILE = Path(__file__).resolve().parent.parent / 'pagination-map.md'


def _parse_page_span(text: str) -> list[int] | None:
    """`5` -> [5]; `1-9` -> [1, 2, …, 9]. None when unparseable."""
    text = text.strip()
    if text.isdigit():
        return [int(text)]
    m = re.fullmatch(r'(\d+)\s*-\s*(\d+)', text)
    if not m:
        return None
    lo, hi = int(m.group(1)), int(m.group(2))
    return list(range(lo, hi + 1)) if lo <= hi else None


def _load_pagination_map(
    path: Path = PAGINATION_MAP_FILE,
) -> dict[str, dict[int, int | None]]:
    """Parse the `## <raw path>` sections of pagination-map.md into
    {raw path: {physical page: printed number | None}}.

    Each section body carries `- <physical> = <printed>` lines; either side may
    be a `lo-hi` span (spans on both sides must be equal length, mapped in
    order), and the right side may be `none` (the page prints no determinable
    number). A trailing `# comment` is ignored.

    Tolerant by design (audit edits this file autonomously): a missing or
    unreadable file returns {} — every raw then reads as unregistered and the
    locator checks fall back to the `app.`-anchor heuristic (the pre-map
    behaviour), so lint still runs (recoverable from git). A malformed line is
    skipped, never raised. Never crashes lint.
    """
    out: dict[str, dict[int, int | None]] = {}
    try:
        text = path.read_text(encoding='utf-8')
    except OSError:
        return out
    raw: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('## '):
            heading = stripped[3:].strip()
            raw = heading if heading.startswith('0-raw/') else None
            if raw:
                out.setdefault(raw, {})
            continue
        if raw is None or not stripped.startswith('- '):
            continue
        item = stripped[2:].split('#', 1)[0].strip()  # drop a trailing comment
        if '=' not in item:
            continue
        lhs, _, rhs = item.partition('=')
        physical = _parse_page_span(text=lhs)
        if not physical:
            continue
        rhs = rhs.strip().lower()
        if rhs == 'none':
            for phys in physical:
                out[raw][phys] = None
            continue
        printed = _parse_page_span(text=rhs)
        if not printed or len(printed) != len(physical):
            continue
        for phys, number in zip(physical, printed):
            out[raw][phys] = number
    return out


PAGINATION_MAP = _load_pagination_map()


def printed_page(raw: str, phys: int) -> tuple[str, int | None]:
    """What physical page `phys` of `raw` prints, per the pagination map:

      ('paginated', M)        the page prints M — a locator must cite `p. M`.
      ('unpaginated', None)   the page prints no number — a locator correctly
                              cites its structural anchor alone.
      ('unregistered', None)  no map entry covers this page; callers fall back
                              to the display heuristic rather than invent a fact.
    """
    pages = PAGINATION_MAP.get(raw)
    if pages is None or phys not in pages:
        return ('unregistered', None)
    number = pages[phys]
    return ('unpaginated', None) if number is None else ('paginated', number)


def _never_match() -> re.Pattern[str]:
    """A regex that matches nothing — used when a list is empty so an empty
    alternation never degenerates into matching the empty string everywhere."""
    return re.compile(r'(?!)')


(OPEN_COMPOUND_NOUN_SUGGEST, HYPHENATED_COMPOUND_ALLOWED,
 COMPOUND_MODIFIER_HEADS, HYPHENATION_VERIFIED_IGNORE) = _load_hyphenation_lists()
# NOTE: the two regexes below compile ONCE at import from the lists above.
# Rebinding a list global at runtime does not rebuild them — audit's data-file
# edits apply on the next process run, and a test adding a DISALLOWED term must
# reload the module, not monkeypatch OPEN_COMPOUND_NOUN_SUGGEST. The sets read
# live in the check body (HYPHENATED_COMPOUND_ALLOWED, COMPOUND_MODIFIER_HEADS,
# HYPHENATION_VERIFIED_IGNORE) are rebindable, so patching those works.
HYPHENATED_OPEN_COMPOUND_NOUN = (
    re.compile(r'\b(' + '|'.join(
        re.escape(k) for k in sorted(OPEN_COMPOUND_NOUN_SUGGEST, key=len, reverse=True)
    ) + r')\b(?!-)', re.IGNORECASE)
    if OPEN_COMPOUND_NOUN_SUGGEST else _never_match()
)
OPEN_COMPOUND_MODIFIER = (
    re.compile(r'\b(' + '|'.join(
        re.escape(v) for v in
        sorted(OPEN_COMPOUND_NOUN_SUGGEST.values(), key=len, reverse=True)
    ) + r')\b', re.IGNORECASE)
    if OPEN_COMPOUND_NOUN_SUGGEST else _never_match()
)
_OPEN_TO_HYPHEN: dict[str, str] = {v: k for k, v in OPEN_COMPOUND_NOUN_SUGGEST.items()}
# Noun-position signal: the compound is followed (after optional spaces) by a
# clause boundary or a copula/comparison word — never a noun it could modify.
# DELIBERATELY CONSERVATIVE: a following comma or word is ambiguous (a modifier
# list, or a modified noun) and is NOT treated as noun position, so the check
# errs toward silence rather than overcorrecting a modifier. Evaluated against
# the UNMASKED body so a masked wikilink head-noun is not mistaken for a space.
_NOUN_POSITION_AFTER = re.compile(
    r'\s*(?:[.;:?!]|$|(?:is|are|was|were|be|been|being|versus|vs\.?|than)\b)',
    re.IGNORECASE | re.MULTILINE,
)


# Embedded image: ![[basename.png]] or ![[basename.png|alt]]. Image extensions
# match Obsidian's defaults. Basename only — paths in embeds are unusual.
IMAGE_EXTS = ('png', 'jpg', 'jpeg', 'svg', 'webp', 'gif')
EMBED_RE = re.compile(
    r'!\[\[([^\]|]+?\.(?:' + '|'.join(IMAGE_EXTS) + r'))(?:\|[^\]]+)?\]\]',
    re.IGNORECASE,
)

# A blank quoted line inside a callout: `>` followed by only whitespace. The
# image-embed isolation rule (CLAUDE.md -> Attachments) requires one of these
# directly above and below every embed line. Tolerates the trailing-space form
# (`> `) as well as the bare `>`.
QUOTED_BLANK_RE = re.compile(r'^>[ \t]*$')

# A quoted line whose only content (after the `>` and surrounding whitespace) is
# a single image embed — the lines the isolation rule governs. A line that mixes
# an embed with prose is not a standalone embed line and is left alone.
QUOTED_EMBED_LINE_RE = re.compile(
    r'^>[ \t]*' + EMBED_RE.pattern + r'[ \t]*$', re.IGNORECASE,
)

# Frontmatter `attachments:`/`sources:`/`file:` entries are wikilinks like
# "[[1-wiki/sources/foo.md|foo]]". After parse_frontmatter strips the outer
# quotes, this re strips the [[ ]] and the optional `| display`.
WIKILINK_BASENAME_RE = re.compile(r'^\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]$')


def _link_stem(raw: str) -> str:
    """Normalize a wikilink target to its identity stem. Targets are
    path-qualified (`1-wiki/concepts/foo.md`), but older bare forms (`foo.md`,
    `foo`) normalize the same way. `Path(...).stem` drops the folder path and
    the final extension: `1-wiki/concepts/foo.md` -> `foo`, `foo` -> `foo`.

    A trailing anchor (`#^callout`, `#page=N`, or a dotted section locator like
    `#sec-3.2`) is stripped before `Path(...).stem`. Without this, `Path.stem`
    splits on the last dot, which on a dotted anchor lands *inside* the anchor
    (`X.md#sec-3.2` -> `X.md#sec-3`) and corrupts the page identity every graph
    check keys on. Strip the anchor first so the stem is always the page stem.

    This stays deliberately tolerant of bare targets: graph identity must
    survive a stray bare link so reciprocity/index/orphan still resolve. The
    bare-vs-path-qualified distinction is surfaced as its own finding
    (`bare_basename_link`), not enforced here.
    """
    return Path(raw.strip().split('#', 1)[0]).stem


def _link_name(raw: str) -> str:
    """Normalize a wikilink target to its basename WITH extension, for
    attachment and raw-file references. `1-wiki/attachments/s/fig.png` ->
    `fig.png`, `0-raw/papers/X.pdf` -> `X.pdf`.
    """
    return Path(raw.strip()).name


def _mask_code_spans(text: str) -> str:
    """Blank inline-code spans (length-preserving) so a prose-level scanner does
    not match inside `` `code` ``. Same-length spaces keep every offset stable,
    so match positions map back onto the original text unchanged. (Does not mask
    multi-line ``` fenced blocks — wiki page bodies use callouts, not fences, so
    no current page triggers that; revisit here if that changes.) Shared by the
    pipe-spacing and bare-basename scans, and by `_mask_noscan_spans`.
    """
    return re.sub(r'`[^`]*`', lambda m: ' ' * len(m.group(0)), text)


def _mask_noscan_spans(text: str) -> str:
    """Blank inline-code spans and wikilink spans (length-preserving) so a
    prose-level scanner does not match inside `` `code` `` or `[[links]]`.
    Used by the page-locator scan (a `p. N` inside a `[[…#page=N|p. N]]`
    deep-link or inside inline code is not a bare locator).
    """
    text = _mask_code_spans(text=text)
    return re.sub(r'\[\[[^\]]*\]\]', lambda m: ' ' * len(m.group(0)), text)


def _blank_sources_callout(text: str) -> str:
    """Blank the `> [!sources]` callout block (length-preserving) so its
    support-list source links are not read as inline citations. The block runs
    from the `> [!sources]` header line through its `> ^sources` block-id line.
    Same-length blanking keeps every offset stable for line-number mapping.
    """
    out = []
    in_sources = False
    for line in text.split('\n'):
        if re.match(r'^>\s*\[!sources\]', line):
            in_sources = True
        if in_sources:
            out.append(' ' * len(line))
            if re.match(r'^>\s*\^sources\s*$', line):
                in_sources = False
        else:
            out.append(line)
    return '\n'.join(out)


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, int]:
    """Return (frontmatter_dict, end_line_index) — minimal YAML-ish parser.

    Handles the wiki's frontmatter shape: `key: value`, `key: "quoted"`,
    `key: [list, items]`, multiline list `\n  - item`. Doesn't try to be a
    full YAML — pyyaml isn't always installed, and this covers our schema.
    """
    lines = text.split('\n')
    if not lines or lines[0].strip() != '---':
        return None, 0
    end = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end = i
            break
    if end == -1:
        return None, 0

    fm: dict[str, Any] = {}
    current_key: str | None = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.strip().startswith('#'):
            continue
        # Multi-line list continuation: `  - item`
        if raw.lstrip().startswith('- ') and current_key is not None:
            value = raw.lstrip()[2:].strip().strip('"').strip("'")
            existing = fm.get(current_key)
            if isinstance(existing, list):
                existing.append(value)
            else:
                fm[current_key] = [value]
            continue
        # `key: value` or `key:` (start of multi-line list). Key charset
        # tolerates digits and hyphens after the first char so a future
        # hyphenated/numbered frontmatter key is parsed, not silently dropped
        # (a dropped key reads as a missing field downstream).
        m = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', raw)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        current_key = key
        if not value:
            fm[key] = []  # empty list / multi-line list to follow
            continue
        # Inline list `[a, b]`. Quote-aware split so a comma inside a quoted
        # value (`["a, b", c]`) does not fragment the item.
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1].strip()
            parts = re.findall(r'"[^"]*"|\'[^\']*\'|[^,"\']+', inner)
            # Strip each part; drop empties (a bareword token can match the
            # inter-item whitespace between two quoted values, e.g. the ` ` in
            # `"a, b", "c"`, yielding a blank — discard it).
            stripped = [p.strip().strip('"').strip("'") for p in parts]
            fm[key] = [v for v in stripped if v] if inner else []
            continue
        # Stripped string
        fm[key] = value.strip('"').strip("'")
    return fm, end


def extract_section_slugs(body: str) -> list[str]:
    return [m.group(1) for m in CALLOUT_RE.finditer(body)]


def extract_embeds(body: str) -> list[str]:
    """Return the basename of every image embed in `body`."""
    out = []
    for m in EMBED_RE.finditer(body):
        # Embed may be `basename.png` or `subdir/basename.png` — keep just the
        # basename, since Obsidian resolves by basename across the vault.
        out.append(m.group(1).rsplit('/', 1)[-1])
    return out


def attachments_basenames(fm: dict[str, Any]) -> list[str]:
    """Pull basenames from a parsed `attachments:` list. Entries are wikilinks
    like `[[fig3-layouts.png]]`; if they aren't wikilinks, take the entry as-is.
    """
    raw = fm.get('attachments') if isinstance(fm.get('attachments'), list) else []
    out = []
    for entry in raw:
        if not isinstance(entry, str) or not entry.strip():
            continue
        m = WIKILINK_BASENAME_RE.match(entry.strip())
        target = m.group(1) if m else entry.strip()
        out.append(_link_name(raw=target))
    return out


def index_attachments_by_basename(wiki_root: Path) -> dict[str, list[Path]]:
    """Map basename -> list of files in `1-wiki/attachments/**`. List because
    duplicate basenames across stems are a real (and lint-flagged) failure mode.
    """
    out: dict[str, list[Path]] = {}
    attachments_root = wiki_root / 'attachments'
    if not attachments_root.exists():
        return out
    for path in attachments_root.rglob('*'):
        if path.is_file() and path.suffix.lower().lstrip('.') in IMAGE_EXTS:
            out.setdefault(path.name, []).append(path)
    return out


def detect_page_kind(path: Path, fm: dict[str, Any]) -> str:
    """Return the schema key for REQUIRED_FIELDS / REQUIRED_SECTIONS lookup."""
    parts = path.parts
    if 'sources' in parts:
        return str(fm.get('type', '')).lower()  # paper/article/media/other
    if 'entities' in parts:
        return 'entity'
    if 'concepts' in parts:
        return 'concept'
    if 'syntheses' in parts:
        return 'synthesis'
    return ''


def finding(check: str, file: str, message: str, fix_hint: str = '',
            severity: str | None = None) -> dict[str, Any]:
    """Build a finding. Severity comes from the CHECKS registry (the single
    source of truth); the `severity` argument is used only for a registry entry
    whose value is None (caller-determined, e.g. zero_source_page).
    """
    if check not in CHECKS:
        raise ValueError(f'unregistered check_id: {check!r} (add it to CHECKS)')
    canonical = CHECKS[check]
    if canonical is not None:
        severity = canonical
    elif severity is None:
        raise ValueError(f'check_id {check!r} needs a caller-supplied severity')
    return {
        'severity': severity,
        'check_id': check,
        'file': file,
        'message': message,
        'fix_hint': fix_hint,
    }


# Cap the best-effort `git show HEAD:` fetch so a hung git never stalls lint.
GIT_SHOW_TIMEOUT_S = 15


def _git_show_head(rel: str) -> str | None:
    """The file's content at git HEAD, or None if unavailable (not a git repo, a
    new/untracked file, or any git error). The diff-guard is best-effort: with no
    HEAD to compare against it is a silent no-op."""
    try:
        r = subprocess.run(['git', 'show', f'HEAD:{rel}'],
                           capture_output=True, text=True,
                           timeout=GIT_SHOW_TIMEOUT_S)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError):
        # OSError: git not installed (FileNotFoundError). SubprocessError:
        # the timeout fires (TimeoutExpired). UnicodeDecodeError: `text=True`
        # decodes stdout in the call, so a non-UTF-8 blob at HEAD raises here
        # (it is a ValueError, not an OSError). A genuine bug (NameError, etc.)
        # still surfaces rather than being silently swallowed.
        return None


def anchor_change_findings(cur_text: str, head_text: str, rel: str,
                           status: str | None,
                           head_status: str | None = None) -> list[dict[str, Any]]:
    """Mechanism 1 (the diff-guard), pure core: flag a `status: verified` page on
    which a raw-locator's structural anchor was ADDED or CHANGED relative to its
    HEAD version while the page stayed `verified`. A section change is a factual
    claim about where the cited content sits — excluded from the verification-
    neutral allowlist (CLAUDE.md -> Page Status) — so only a raw fact-check (audit)
    may keep the page verified. A pure RELOCATION (the same anchor + page,
    repositioned relative to the link) and any minor typo/format edit are neutral
    and not flagged; a bullet marked `*[unverified]*` is exempt (already pending).

    Detection works on the line diff so no bullet-matching is needed: for each
    added/changed line carrying a locator whose display now holds anchor A for
    `#page=N`, it is a relocation only if some removed line held BOTH `#page=N`
    and A (the anchor existed for that page at HEAD). Otherwise A is new or
    changed — a section change. Split out from check_verified_anchor_change so it
    is testable without a git working tree.

    Best-effort, with two known false-negative limits (the hash check is the real
    backstop): the line diff keys on whole-line identity, so a changed locator line
    that is byte-identical to another existing line is not seen as "added"; and the
    relocation exemption matches any removed line carrying the same `#page=N` and
    anchor, so a genuine change can be masked when one page is cited on two bullets.
    """
    if status != 'verified':
        return []
    # HEAD-status gate: a draft / needs-update -> verified promotion IS the
    # verification event, so a citation anchor added in that same change is not a
    # self-re-stamp of an already-verified page. Only fire when the page was ALSO
    # `verified` at HEAD (the genuine "re-stamp a section change without re-checking
    # the raw" case). head_status is None only for a direct caller that does not
    # supply it (assume verified-at-HEAD, preserve the flag). CLAUDE.md -> Page Status.
    if head_status is not None and head_status != 'verified':
        return []
    cur_lines = cur_text.splitlines()
    head_lines = head_text.splitlines()
    cur_set = set(cur_lines)
    head_set = set(head_lines)
    added = [ln for ln in cur_lines if ln not in head_set]
    removed = [ln for ln in head_lines if ln not in cur_set]
    findings: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str]] = set()
    for line in added:
        if '*[unverified]*' in line:
            continue
        for m in CITATION_DEEPLINK_RE.finditer(line):
            am = LOCATOR_ANCHOR_TOKEN_RE.search(m.group(1))
            if not am:
                continue  # page-only display — other checks own that
            anchor = am.group(0).rstrip(' .,').lower()
            pm = re.search(r'#page=(\d+)', m.group(0))
            pageN = pm.group(1) if pm else None
            key = (pageN, anchor)
            if key in seen:
                continue
            seen.add(key)
            # Relocation/unchanged: the same anchor for the same page existed at
            # HEAD (in a removed line). Compare on the same removed line so a
            # coincidental match elsewhere does not mask a real change.
            if pageN and any(f'#page={pageN}' in rl and anchor in rl.lower()
                             for rl in removed):
                continue
            findings.append(finding(
                check='verified_anchor_unaudited',
                file=rel,
                message=(f"`status: verified` page has a locator whose section/"
                         f"figure anchor `{am.group(0)}` (#page={pageN}) was added "
                         f"or changed since the last commit, yet the page is still "
                         f"`verified`. A section change is grounds for re-"
                         f"verification — only a raw fact-check (audit) may keep it "
                         f"verified; self-re-stamping a section change is not "
                         f"verification."),
                fix_hint=("Demote the page to `draft` (strip `verified_hash:`), or "
                          "mark the changed bullet `*[unverified]*`, and let `audit` "
                          "re-verify the anchor against the raw."),
            ))
    return findings


def check_verified_anchor_change(text: str, fm: dict[str, Any],
                                 rel: str) -> list[dict[str, Any]]:
    """Mechanism 1 (the diff-guard): git wrapper around anchor_change_findings.
    Fetches the page at HEAD and diffs the working tree. No-op without git."""
    if fm.get('status') != 'verified':
        return []
    head = _git_show_head(rel=rel)
    if head is None:
        return []
    head_fm, _ = parse_frontmatter(text=head)
    return anchor_change_findings(cur_text=text, head_text=head, rel=rel,
                                  status=fm.get('status'),
                                  head_status=(head_fm or {}).get('status'))


def check_verified_hash(path: Path, fm: dict[str, Any],
                        rel: str) -> list[dict[str, Any]]:
    """Mechanism 2 (the committed-state backstop): flag a `status: verified` page
    whose stored `verified_hash:` no longer matches the current masked body hash (its
    checked, unmarked content changed since `audit` stamped it), or that carries no
    stamp at all. Unlike the diff-guard (Mechanism 1), this needs no git working tree
    and survives a commit, so it is the durable backstop once a change is committed.

    Detection only: the re-stamp-vs-demote DECISION stays with the calling skill
    (lint SKILL.md), which has the run-state to tell an allowlisted verification-
    neutral re-stamp from a genuine demotion. The script only flags the mismatch.
    CLAUDE.md -> Page Status; hashes computed with the shared `body_hash` so lint and
    audit never disagree."""
    if fm.get('status') != 'verified':
        return []
    stored = fm.get('verified_hash')
    try:
        actual = body_hash(path=str(path))
    except OSError:
        return []  # unreadable mid-run (TOCTOU); check_page's own read already surfaces a real absence
    except ValueError:
        # body_hash refuses a frontmatter block it cannot cleanly close: it needs an
        # exact `---` delimiter line, but parse_frontmatter's strip-based match accepts
        # a whitespace-padded `---`. So `frontmatter_missing` does NOT fire and no other
        # check owns this case — surface it rather than silently exempting a `verified`
        # page from the hash check (a self-concealing false green).
        return [finding(
            check='verified_hash_mismatch',
            file=rel,
            message=('`status: verified` page has a malformed frontmatter `---` '
                     'delimiter (stray whitespace), so its checked content cannot be '
                     'hashed or confirmed current.'),
            fix_hint=('Repair the frontmatter `---` delimiter lines (exact `---`, no '
                      'surrounding whitespace), then re-run lint; demote to `draft` if unsure.'),
        )]
    if not stored:
        return [finding(
            check='verified_hash_mismatch',
            file=rel,
            message=('`status: verified` page carries no `verified_hash:` stamp, so '
                     'its checked content cannot be confirmed current.'),
            fix_hint=('Have `audit` fact-check and stamp the page, or reset it to '
                      '`draft` until it is verified.'),
        )]
    if stored != actual:
        return [finding(
            check='verified_hash_mismatch',
            file=rel,
            message=("`status: verified` page's body no longer matches its "
                     '`verified_hash:` — checked (unmarked) content changed since the '
                     'last fact-check.'),
            fix_hint=('If the change was a verification-neutral allowlisted edit, '
                      're-stamp `verified_hash:`; otherwise demote the page to '
                      '`draft` (strip `verified_hash:`) and let `audit` re-verify.'),
        )]
    return []


def check_page(path: Path, wiki_root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = path.read_text(encoding='utf-8')
    fm, end = parse_frontmatter(text=text)
    rel = str(path.relative_to(wiki_root.parent))

    if fm is None:
        findings.append(finding(
            check='frontmatter_missing',
            file=rel,
            message=('Page has no YAML frontmatter (missing opening or closing '
                     '`---`). Other structural checks were skipped for this page '
                     'until frontmatter exists; re-run lint after adding it.'),
            fix_hint='Add `---` markers around frontmatter at the top of the file.',
        ))
        return findings

    kind = detect_page_kind(path=path, fm=fm)
    if not kind:
        return findings  # hot/index/log/etc — out of scope here

    # Frontmatter completeness (check_id: frontmatter_missing_field).
    required = REQUIRED_FIELDS.get(kind, [])
    for field in required:
        if field not in fm:
            findings.append(finding(
                check='frontmatter_missing_field',
                file=rel,
                message=f'Required frontmatter field `{field}` missing for type `{kind}`.',
                fix_hint=f'Add `{field}:` to the frontmatter.',
            ))

    # Status validity (check_id: status_invalid).
    if 'status' in fm and fm['status'] not in VALID_STATUSES:
        findings.append(finding(
            check='status_invalid',
            file=rel,
            message=(f"`status:` is `{fm['status']}` but must be one of "
                     f'{sorted(VALID_STATUSES)}.'),
            fix_hint='Set status to `draft`, `verified`, or `needs-update`.',
        ))

    # Mechanism 1 (diff-guard): a verified page must not keep `verified` after a
    # locator section/figure anchor was added or changed vs HEAD without re-
    # verification (check_id: verified_anchor_unaudited). Git-aware, best-effort.
    findings.extend(check_verified_anchor_change(text=text, fm=fm, rel=rel))
    findings.extend(check_verified_hash(path=path, fm=fm, rel=rel))

    # source_count vs len(sources) (input to lint's auto-fix).
    if 'sources' in fm and 'source_count' in fm:
        sources = fm['sources'] if isinstance(fm['sources'], list) else []
        try:
            declared = int(str(fm['source_count']))
        except (TypeError, ValueError):
            declared = -1
        actual = len(sources)
        if declared != actual:
            findings.append(finding(
                check='source_count_mismatch',
                file=rel,
                message=f"`source_count: {declared}` doesn't match `len(sources) = {actual}`.",
                fix_hint=f'Set `source_count: {actual}` (lint auto-fix territory).',
            ))
        # Zero-source pages (check_id: zero_source_page).
        if actual == 0 and kind in {'entity', 'concept', 'synthesis'}:
            sev = 'error' if kind == 'synthesis' else 'warning'
            findings.append(finding(
                severity=sev,
                check='zero_source_page',
                file=rel,
                message=(f'{kind.capitalize()} page has no sources '
                         f"({'syntheses are structurally invalid without sources' if kind == 'synthesis' else 'fragile'})."),
                fix_hint='Add source support or quarantine the page via /forget.',
            ))
        # Single-source synthesis without explicit stub marker (D 3.3 / D X.3).
        # CLAUDE.md requires synthesis pages to have ≥ 2 sources unless the
        # user explicitly creates a single-source stub via the
        # `single_source_stub: true` frontmatter field.
        if kind == 'synthesis' and actual == 1:
            stub_flag = fm.get('single_source_stub')
            is_stub = (stub_flag is True or
                       (isinstance(stub_flag, str)
                        and stub_flag.strip().lower() == 'true'))
            if not is_stub:
                findings.append(finding(
                    check='synthesis_under_supported',
                    file=rel,
                    message=(
                        'Synthesis page has only 1 source; schema requires ≥ 2 '
                        'unless `single_source_stub: true` is set in frontmatter.'
                    ),
                    fix_hint=(
                        'Add a second supporting source page, mark the page as '
                        'a stub with `single_source_stub: true`, or convert to '
                        "a concept/entity page if cross-source synthesis isn't "
                        'the goal.'
                    ),
                ))

    # Body section order (check_id: section_order).
    body = '\n'.join(text.split('\n')[end + 1:])
    actual_slugs = extract_section_slugs(body=body)
    expected_slugs = REQUIRED_SECTIONS.get(kind, [])
    if expected_slugs and actual_slugs != expected_slugs:
        # Distinguish missing-section vs wrong-order for a more useful message.
        missing = set(expected_slugs) - set(actual_slugs)
        extra = set(actual_slugs) - set(expected_slugs)
        if missing:
            msg = f'Missing required sections: {sorted(missing)}.'
        elif extra:
            msg = f'Unknown extra sections present: {sorted(extra)}.'
        else:
            msg = (f"Section order doesn't match schema. "
                   f'Got {actual_slugs}; expected {expected_slugs}.')
        findings.append(finding(
            check='section_order',
            file=rel,
            message=msg,
            fix_hint='Reorder section callouts to match CLAUDE.md schema for this page type.',
        ))

    # Callout block IDs (check_id: callout_block_id).
    findings.extend(check_callout_block_ids(body=body, rel=rel))

    # Page-locator deep-links (check_id: page_locator_unlinked).
    findings.extend(check_page_locators_linked(body=body, rel=rel))

    # Status:draft inventory (check_id: status_draft, INFO).
    if fm.get('status') == 'draft':
        findings.append(finding(
            check='status_draft',
            file=rel,
            message='Page is `status: draft` — unreviewed.',
            fix_hint='Run /audit and consider promoting to `verified` after a re-read pass.',
        ))

    # Needs-update inventory (check_id: status_needs_update, error -> Critical).
    # Mirrors status_draft. CLAUDE.md lists this as a standing, audit-non-
    # blocking Critical (STANDING_NONBLOCKING): a needs-update page is an
    # expected, ongoing repo state, not structural drift, so it is excluded from
    # the audit-blocking gate and the script exit code. lint does not fix
    # needs-update pages — resolving one is content judgement (audit, or ingest's
    # existing-source mode). The companion `needs_update_without_reason` /
    # `stale_needs_update` checks add the quality nudges on top of this.
    if fm.get('status') == 'needs-update':
        reason = fm.get('needs_update_reason')
        reason_txt = (reason.strip()
                      if isinstance(reason, str) and reason.strip()
                      else 'see Contradictions/Tensions callout')
        findings.append(finding(
            check='status_needs_update',
            file=rel,
            message=f'Page is `status: needs-update` ({reason_txt}).',
            fix_hint=('Resolve via /audit or /ingest existing-source mode, or '
                      '/forget if no longer relevant. lint does not auto-fix '
                      'needs-update pages.'),
        ))

    # Concept/entity pages cap at one defining image embed (CLAUDE.md
    # Attachments rule). Source and synthesis pages may have multiple.
    embeds = extract_embeds(body=body)
    if kind in {'concept', 'entity'} and len(embeds) > 1:
        findings.append(finding(
            check='concept_multi_image',
            file=rel,
            message=(f'Page has {len(embeds)} image embeds; '
                     f'concept/entity pages allow at most one defining image.'),
            fix_hint='Move extra figures to the source page or split the concept.',
        ))

    # Every embed must sit in its own block — blank quoted line above and below
    # (check_id: embed_not_isolated). Applies to all page kinds with embeds.
    findings.extend(check_embed_isolated(body=body, rel=rel, end=end))

    # Concept/entity pages should read as standalone ideas, not as summaries
    # of a specific paper. Phrases like "as the paper notes" tie the bullet's
    # meaning back to the source rather than expressing the idea on its own
    # terms (D 3.11).
    if kind in {'concept', 'entity'}:
        for m in SOURCE_CONTEXT_PHRASES.finditer(body):
            line_no = body[:m.start()].count('\n') + 1
            # body starts after frontmatter; offset line numbers so the
            # finding points at the source file's actual line.
            actual_line = end + 1 + line_no
            findings.append(finding(
                check='source_context_leak',
                file=rel,
                message=(
                    f'Source-context phrase `{m.group(0)}` on concept/entity '
                    f'page (line {actual_line}). The page should read as a '
                    f'standalone idea, not as a summary of a particular source.'
                ),
                fix_hint=(
                    "Rewrite the bullet in the user's voice. State the idea on "
                    'its own terms; source support lives in `sources:` and the '
                    '`Sources` callout.'
                ),
            ))

    # When a concept/entity/synthesis bullet attributes a claim to a source, it
    # must name the source, not say "the source" / "a source" / "one framework"
    # (CLAUDE.md -> Plain-Language Style). Source pages are exempt: the whole
    # page is scoped to one source, so "the source" there is unambiguous.
    if kind in {'concept', 'entity', 'synthesis'}:
        for m in VAGUE_SOURCE_REFERENT.finditer(body):
            line_no = body[:m.start()].count('\n') + 1
            actual_line = end + 1 + line_no
            findings.append(finding(
                check='vague_source_referent',
                file=rel,
                message=(
                    f'Vague source referent `{m.group(0)}` on {kind} page '
                    f'(line {actual_line}). The bullet attributes a claim to a '
                    f'source without naming it; this becomes ambiguous once the '
                    f'page has more than one source.'
                ),
                fix_hint=(
                    'Name the source directly — a pipe-rendered wikilink to its '
                    'source page (or the named system) — or, if the attribution '
                    'is not load-bearing, restate the idea on its own terms.'
                ),
            ))

    # Canonical citation form: any inline raw deep-link must carry a structural
    # anchor + page in its display and be paired with its source-page link
    # (CLAUDE.md -> Source Support And Verification). Mechanical format only;
    # the "every non-obvious claim must be cited" rule is audit/ingest's.
    if kind in {'concept', 'entity', 'synthesis'}:
        findings.extend(check_citation_form(body=body, rel=rel, end=end))
        findings.extend(check_citation_bracket_style(body=body, rel=rel, end=end))

    # Source pages use the same anchor-inside-the-display locator form, minus the
    # paired source-page wikilink (which would self-link): the `#page=N` deep-link
    # display must list the structural anchor and the page together (check_id:
    # source_locator_incomplete). The source-page counterpart of
    # citation_locator_incomplete; inverse of the retired source_locator_anchor_inlined.
    if kind in SOURCE_KINDS:
        findings.extend(check_source_locator_complete(body=body, rel=rel, end=end))

    # Every #page=N locator's cited `p. M` must match what the pagination map
    # says that physical page prints (check_id: locator_page_mismatch). Applies
    # to every page kind that carries raw deep-links, so it is not kind-gated.
    findings.extend(check_locator_page_match(body=body, rel=rel, end=end))

    # Sentence-initial capitalization of bullet-initial wikilink displays
    # (check_id: wikilink_display_uncapitalized). Applies to every page kind —
    # the Wikilink Format rule is general.
    findings.extend(check_wikilink_display_caps(body=body, rel=rel, end=end))

    # Intra-page redundancy: the same point repeated across (or within) callouts
    # (CLAUDE.md -> Body Sections As Callouts). Scoped to concept/entity/synthesis
    # — source pages legitimately restate a Key Claim as a verbatim Evidence
    # anchor. Lexical half only; the semantic half is ingest/audit's.
    if kind in {'concept', 'entity', 'synthesis'}:
        findings.extend(check_intra_page_redundancy(body=body, rel=rel, end=end))

    # Established open compounds hyphenated as attributive modifiers
    # (check_id: hyphenated_open_compound). The wiki writes "reinforcement
    # learning", "natural language", "language model" open even before a noun;
    # the hyphenated form is drift. Applies to every page kind (source pages
    # carry these terms too). Scan the code- and wikilink-masked body so a slug
    # or path that contains a hyphenated token is not flagged; `_mask_noscan_spans`
    # is length-preserving, so match offsets map back to real line numbers. Also
    # blank double-quoted spans (verbatim quotes paired with a locator): a source
    # may hyphenate a term inside a quote, and de-hyphenating it would alter the
    # quote, so the term must read exactly as the source wrote it — never flagged,
    # never "fixed". Mirrors the quote mask in check_unlinked_page_mentions.
    masked = _mask_noscan_spans(text=body)
    masked = re.sub(r'"[^"\n]*"', lambda m: ' ' * len(m.group(0)), masked)
    for m in HYPHENATED_OPEN_COMPOUND.finditer(masked):
        line_no = masked[:m.start()].count('\n') + 1
        actual_line = end + 1 + line_no
        suggest = OPEN_COMPOUND_SUGGEST[m.group(1).lower()]
        findings.append(finding(
            check='hyphenated_open_compound',
            file=rel,
            message=(
                f'Hyphenated established compound `{m.group(1)}` used as a '
                f'modifier (line {actual_line}); field convention leaves this '
                f'term open.'
            ),
            fix_hint=f'Write `{suggest}` (drop the hyphen joining the open compound).',
        ))

    # Slug-derived open compounds used as a NOUN (check_id:
    # hyphenated_open_compound_noun). Distinct from the block above: these terms
    # are correct hyphenated as a modifier ("belief-state representation") and
    # wrong only as a bare noun ("the belief-state evolves" -> "belief state").
    # Flagged ONLY in noun position so a grammatical modifier is never touched.
    # Reuses the same code/quote/wikilink mask (so a slug, a quoted term, and a
    # wikilink-display compound are never flagged); noun position is judged on the
    # UNMASKED body so a masked head-noun is not read as trailing whitespace.
    # Direction 1 — a hyphenated open compound used as a bare NOUN -> open it.
    for m in HYPHENATED_OPEN_COMPOUND_NOUN.finditer(masked):
        token = m.group(1)
        if token.lower() in HYPHENATED_COMPOUND_ALLOWED:
            continue
        if not _NOUN_POSITION_AFTER.match(body, m.end()):
            continue
        nxt = re.match(r'\s+([A-Za-z][\w-]*)', body[m.end():])
        if (token + (' ' + nxt.group(1) if nxt else '')).lower() \
                in HYPHENATION_VERIFIED_IGNORE:
            continue
        line_no = masked[:m.start()].count('\n') + 1
        actual_line = end + 1 + line_no
        suggest = OPEN_COMPOUND_NOUN_SUGGEST[token.lower()]
        findings.append(finding(
            check='hyphenated_open_compound_noun',
            file=rel,
            message=(
                f'Hyphenated open compound `{token}` used as a noun '
                f'(line {actual_line}); the hyphenated form is correct only as a '
                f'modifier before a noun.'
            ),
            fix_hint=(
                f'Write `{suggest}` here (drop the hyphen); keep `{token}` '
                f'hyphenated where it directly modifies a following noun. '
                f'`audit` confirms the use against the raw before applying.'
            ),
        ))

    # Direction 2 — an OPEN compound used as a MODIFIER (directly before a curated
    # head noun) was overcorrected open -> re-hyphenate. Head-noun-gated, so a
    # following verb (the open-noun case "tool use reaches") never triggers it; a
    # word not on COMPOUND_MODIFIER_HEADS is never treated as a head.
    for m in OPEN_COMPOUND_MODIFIER.finditer(masked):
        open_form = m.group(1)
        nm = re.match(r'\s+([A-Za-z][\w-]*)', body[m.end():])
        if not nm or nm.group(1).lower() not in COMPOUND_MODIFIER_HEADS:
            continue
        head = nm.group(1)
        if f'{open_form} {head}'.lower() in HYPHENATION_VERIFIED_IGNORE:
            continue
        hyphenated = _OPEN_TO_HYPHEN[open_form.lower()]
        line_no = masked[:m.start()].count('\n') + 1
        actual_line = end + 1 + line_no
        findings.append(finding(
            check='hyphenated_open_compound_noun',
            file=rel,
            message=(
                f'Open compound `{open_form}` used as a modifier before '
                f'`{head}` (line {actual_line}); a compound modifier before a '
                f'noun takes a hyphen.'
            ),
            fix_hint=(
                f'Write `{hyphenated} {head}` (hyphenate the compound modifier); '
                f'`audit` confirms the use, or adds the phrase to '
                f'HYPHENATION_VERIFIED_IGNORE if it is correct open.'
            ),
        ))

    # Claim-level verification: surface `*[unverified]*` claims (the pending delta
    # audit re-checks). Info-level visibility — these are a normal transient state,
    # not drift; lint does not clear them (audit does, after a raw fact-check).
    n_unverified = len(UNVERIFIED_MARKER_RE.findall(_mask_code_spans(text=body)))
    if n_unverified:
        findings.append(finding(
            check='unverified_claim',
            file=rel,
            message=(f'{n_unverified} claim(s) marked `*[unverified]*` '
                     f'awaiting a raw fact-check; audit re-checks just these.'),
            fix_hint='Run /audit to fact-check the marked claims and clear them.',
        ))

    # Placeholder-only page check (D X.4): if every required callout is
    # filled with only the empty-placeholder bullet, the page is a stub.
    # Flag info-level so the user can fill it or quarantine it.
    if expected_slugs and _is_placeholder_only(body=body, expected_slugs=expected_slugs):
        findings.append(finding(
            check='placeholder_only_page',
            file=rel,
            message=('Every required section is the empty placeholder; page is a '
                     'stub with no genuine content yet.'),
            fix_hint='Fill the page with real content or quarantine via /forget.',
        ))

    # Stale-draft check (D 11.5/6): status:draft and updated: older than
    # STALE_DRAFT_DAYS. Info-level nudge before audit's 60-day stale-draft
    # threshold.
    # Stale needs-update check (D 5.5b): status:needs-update and updated:
    # older than STALE_NEEDS_UPDATE_DAYS. Warning-level — needs-update means
    # the page is known-broken, and ignored stale findings compound.
    status = fm.get('status')
    if status in ('draft', 'needs-update'):
        updated_raw = fm.get('updated')
        if isinstance(updated_raw, str):
            try:
                updated_date = datetime.strptime(
                    updated_raw.strip(), '%Y-%m-%d'
                ).date()
                age_days = (date.today() - updated_date).days
                if status == 'draft' and age_days > STALE_DRAFT_DAYS:
                    findings.append(finding(
                        check='stale_draft',
                        file=rel,
                        message=(
                            f'Page is `status: draft` and was last updated '
                            f'{age_days} days ago (>{STALE_DRAFT_DAYS} day '
                            f'threshold).'
                        ),
                        fix_hint=(
                            'Review the page and promote to `verified` if '
                            'ready, or update content if work is ongoing.'
                        ),
                    ))
                elif status == 'needs-update' and age_days > STALE_NEEDS_UPDATE_DAYS:
                    findings.append(finding(
                        check='stale_needs_update',
                        file=rel,
                        message=(
                            f'Page is `status: needs-update` and was last '
                            f'updated {age_days} days ago '
                            f'(>{STALE_NEEDS_UPDATE_DAYS} day threshold). '
                            f'Known-broken pages should not sit untouched.'
                        ),
                        fix_hint=(
                            'Resolve the open issue and promote, re-ingest '
                            'in existing-source mode or /supersede to fix, or '
                            '/forget if no longer relevant.'
                        ),
                    ))
            except ValueError:
                pass  # malformed date — covered by frontmatter checks

    return findings


def _is_placeholder_only(body: str, expected_slugs: list[str]) -> bool:
    """Return True if every required callout body is only an empty placeholder.

    Splits body into callout chunks by the callout-header line, then checks
    each chunk for a single placeholder bullet. Returns False if any required
    callout has substantive content (anything other than the empty placeholder
    bullet and blank quoted lines).
    """
    # Find all callout header positions.
    headers = list(CALLOUT_RE.finditer(body))
    if not headers:
        return False
    # Map each required slug to its chunk text.
    chunks: dict[str, str] = {}
    for i, m in enumerate(headers):
        slug = m.group(1)
        chunk_start = m.end()
        chunk_end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        chunks[slug] = body[chunk_start:chunk_end]
    # Every required slug must be present and placeholder-only.
    for slug in expected_slugs:
        if slug not in chunks:
            return False  # missing-section check handles this case
        # Strip the chunk to its non-blank *quoted* lines. CALLOUT_RE ends at
        # the `]` of the header, so the chunk's first line is the callout-title
        # remnant (` Idea`); it does not start with `>` and must be dropped, or
        # every titled callout reads as having >1 content line and the check
        # never fires. Mirror check_callout_block_ids' `startswith('>')` filter.
        lines = [line.rstrip() for line in chunks[slug].splitlines()
                 if line.strip() and line.startswith('>')]
        # A placeholder-only chunk has exactly one non-blank content line
        # (the `> - None ...` bullet) plus optional `>` blank quoted lines and
        # the callout's `> ^slug` block-ID line, which is not body content.
        content_lines = [line for line in lines
                         if line != '>' and not BLOCK_ID_RE.match(line)]
        if len(content_lines) != 1:
            return False
        if content_lines[0].strip() not in EMPTY_PLACEHOLDERS:
            return False
    return True


def check_callout_block_ids(body: str, rel: str) -> list[dict[str, Any]]:
    """Every callout carries its block ID `> ^<block-id>` as the last line
    inside the `>` block (CLAUDE.md -> Callout Block IDs), so each section is
    linkable via `[[path#^block-id|Display]]` (Obsidian does not anchor to
    callout titles). The block ID is the kebab-case of the callout's display
    title — the type slug for most callouts, but an expanded form where the type
    is abbreviated (`[!why]` -> `^why-it-matters`). Flag callouts whose block ID
    is missing, doesn't match the expected ID, is duplicated, or isn't the last
    quoted line. Each case has a deterministic fix, so lint applies it
    mechanically.
    """
    findings: list[dict[str, Any]] = []
    headers = list(CALLOUT_RE.finditer(body))
    for i, m in enumerate(headers):
        slug = m.group(1)
        bid = expected_block_id(slug=slug)
        start = m.end()
        end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        quoted = [ln for ln in body[start:end_pos].splitlines()
                  if ln.startswith('>')]
        if not quoted:
            continue  # malformed/empty callout — other checks own that
        id_hits = [(k, mm.group(1)) for k, ln in enumerate(quoted)
                   if (mm := BLOCK_ID_RE.match(ln))]
        if not id_hits:
            findings.append(finding(
                check='callout_block_id',
                file=rel,
                message=f'`[!{slug}]` callout has no block ID.',
                fix_hint=(f'Add `> ^{bid}` as the last line inside the '
                          f'`[!{slug}]` callout (CLAUDE.md -> Callout Block IDs).'),
            ))
            continue
        if len(id_hits) > 1:
            findings.append(finding(
                check='callout_block_id',
                file=rel,
                message=(f'`[!{slug}]` callout has {len(id_hits)} block IDs; '
                         f'expected exactly one (`^{bid}`).'),
                fix_hint=(f'Keep a single `> ^{bid}` as the last line inside '
                          f'the callout and remove the others.'),
            ))
            continue
        idx, value = id_hits[0]
        if value != bid:
            findings.append(finding(
                check='callout_block_id',
                file=rel,
                message=(f'`[!{slug}]` callout block ID is `^{value}`; expected '
                         f'`^{bid}` (the block ID is the kebab-case of the '
                         f'callout title).'),
                fix_hint=f'Change the block ID to `> ^{bid}`.',
            ))
        elif idx != len(quoted) - 1:
            findings.append(finding(
                check='callout_block_id',
                file=rel,
                message=(f'`[!{slug}]` block ID `^{bid}` is not the last line '
                         f'inside the callout.'),
                fix_hint=(f'Move `> ^{bid}` to the last line inside the '
                          f'`[!{slug}]` callout.'),
            ))
    return findings


# A callout bullet: a quoted line whose first non-`>` content is `- `. The
# `\s*` after `>` tolerates indented sub-bullets. Image embeds (`> ![[…]]`)
# carry no dash and so are excluded, which is what we want.
BULLET_RE = re.compile(r'^>\s*-\s+(.+?)\s*$')
# Empty-section placeholder bullets — never redundancy candidates.
PLACEHOLDER_BULLET_RE = re.compile(r'^none(?:\s+yet|\s+noted)?\.?$', re.IGNORECASE)


def _redundancy_tokens(bullet: str) -> set[str]:
    """Content-token set for intra-page redundancy comparison.

    Drops the parts that are navigational or formatting rather than the bullet's
    point — wikilinks and image embeds (target AND display, so two bullets citing
    the same source don't collide), `*[marker]*` tokens, and inline code (file
    paths, snippets) — then lowercases, splits on non-alphanumerics, and removes
    stopwords. What remains is the propositional content the comparison keys on.
    """
    t = re.sub(r'!?\[\[[^\]]*\]\]', ' ', bullet)   # wikilinks + image embeds
    t = re.sub(r'\*\[[^\]]*\]\*', ' ', t)           # *[unverified]* / *[tentative]*
    t = re.sub(r'`[^`]*`', ' ', t)                  # inline code spans
    t = re.sub(r'[^a-z0-9]+', ' ', t.lower())
    return {w for w in t.split()
            if len(w) >= 2 and w not in REDUNDANCY_STOPWORDS}


def check_intra_page_redundancy(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """Flag two bullets on ONE page that make the same point (CLAUDE.md -> Body
    Sections As Callouts: "do not paraphrase the same point across sections").

    Scoped by the caller to concept/entity/synthesis pages: source pages
    intentionally restate a Key Claim as a verbatim Evidence anchor, so the
    pattern is legitimate there. Lexical only — it compares content-token sets
    (see `_redundancy_tokens`) with two arms (Jaccard for similar-length twins,
    overlap coefficient for containment). The semantic variant, a point fully
    reworded, needs bullet-level reading and is ingest's note-quality packet and
    audit's job. Not auto-fixable: which bullet to drop or how to merge is
    editorial, so the finding is audit's worklist (like vague_source_referent).
    """
    bullets: list[tuple[str, set[str], str, int]] = []
    cur_slug: str | None = None
    for idx, ln in enumerate(body.splitlines()):  # idx: 0-based body line
        header = CALLOUT_RE.match(ln)
        if header:
            cur_slug = header.group(1)
            continue
        bm = BULLET_RE.match(ln)
        if not bm or cur_slug is None:
            continue
        raw = bm.group(1).strip()
        if PLACEHOLDER_BULLET_RE.match(raw):
            continue
        toks = _redundancy_tokens(bullet=raw)
        snippet = (raw[:60] + '…') if len(raw) > 60 else raw
        bullets.append((cur_slug, toks, snippet, idx + 1))  # 1-based body line

    findings: list[dict[str, Any]] = []
    for i, (slug_a, ta, snip_a, _line_a) in enumerate(bullets):
        if len(ta) < min(MIN_BULLET_CONTENT_TOKENS, MIN_OVERLAP_SHORTER_TOKENS):
            continue
        for slug_b, tb, snip_b, line_b in bullets[i + 1:]:
            inter = ta & tb
            if not inter:
                continue
            jaccard = len(inter) / len(ta | tb)
            shorter = min(len(ta), len(tb))
            overlap = len(inter) / shorter
            hit_jaccard = (jaccard >= BULLET_JACCARD_THRESHOLD
                           and len(ta) >= MIN_BULLET_CONTENT_TOKENS
                           and len(tb) >= MIN_BULLET_CONTENT_TOKENS)
            hit_overlap = (overlap >= BULLET_OVERLAP_THRESHOLD
                           and shorter >= MIN_OVERLAP_SHORTER_TOKENS)
            if not (hit_jaccard or hit_overlap):
                continue
            where = (f'within `{slug_a}`' if slug_a == slug_b
                     else f'across `{slug_a}` and `{slug_b}`')
            findings.append(finding(
                check='intra_page_redundancy',
                file=rel,
                message=(
                    f'Two bullets {where} overlap (Jaccard {jaccard:.2f}, '
                    f'containment {overlap:.2f}) at line {end + 1 + line_b}: '
                    f'"{snip_a}" / "{snip_b}". Possible repeated point.'
                ),
                fix_hint=(
                    'If the bullets make the same point, drop or merge one and '
                    'keep it in the section where it belongs (CLAUDE.md forbids '
                    'paraphrasing one point across sections). If they are '
                    'genuinely distinct, no change needed.'
                ),
            ))
    return findings


def check_page_locators_linked(body: str, rel: str) -> list[dict[str, Any]]:
    """Every page locator (`p. N`, `pp. N–M`) on a wiki page carries a `#page=N`
    raw-file deep-link (CLAUDE.md -> Source Support And Verification), so a click
    opens the source at that page. Flag bare locators. Not auto-fixable: N is the
    physical PDF page, which lint cannot derive without opening the PDF — the
    agent (or audit) computes it from the printed->physical offset. One finding
    per distinct bare token per page.
    """
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    # Scan with code and wikilink spans blanked, so a `p. N` already inside a
    # `[[…#page=N|p. N]]` deep-link or inside inline code is not re-flagged as
    # bare. Masking is length-preserving, so the matched token equals the
    # original text for the prose-level locators we want.
    scan = _mask_noscan_spans(text=body)
    for m in PAGE_LOCATOR_RE.finditer(scan):
        tok = m.group(0)
        if tok in seen:
            continue
        seen.add(tok)
        findings.append(finding(
            check='page_locator_unlinked',
            file=rel,
            message=f'Page locator `{tok}` is not a raw-file deep-link.',
            fix_hint=(f'Wrap it as `[[0-raw/papers/<stem>.pdf#page=N|{tok}]]`, where '
                      f'N is the physical PDF page (CLAUDE.md -> Source Support And '
                      f'Verification; determine the printed->physical offset from the PDF).'),
        ))
    return findings


def check_citation_form(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """Mechanical citation-form checks for concept/entity/synthesis pages
    (CLAUDE.md -> Source Support And Verification, canonical form). Lint owns the
    *format* of citations that carry a locator; the semantic rule that every
    non-obvious claim must carry the full form is audit/ingest's, since lint
    cannot judge whether a bullet is a non-obvious claim or an allowed bare
    general attribution. Source pages are exempt — their Evidence locators use a
    different (page-token-as-link) form.

    - citation_locator_incomplete: a raw `#page=N` deep-link whose display lacks
      a structural anchor (sec./app./ch./fig./tab./eq./def./thm./lem./prop./cor./alg.)
      or a page (`p. M`). An
      `app.`-anchored display may omit `p. M` (the unpaginated-supplement
      exemption; see locator_display_complete).
    - citation_unpaired: a raw deep-link not preceded on its bullet by a
      source-page wikilink (the canonical form pairs them).
    """
    findings: list[dict[str, Any]] = []
    # Blank inline code and the Sources callout (its support-list links are not
    # inline citations). Length-preserving, so offsets map back for line numbers.
    scan = _blank_sources_callout(text=_mask_code_spans(text=body))
    for m in CITATION_DEEPLINK_RE.finditer(scan):
        display = m.group(1)
        actual_line = end + 1 + scan[:m.start()].count('\n') + 1
        km = CITATION_DEEPLINK_KEY_RE.search(m.group(0))
        raw_path = km.group(1) if km else None
        phys = int(km.group(2)) if km else None
        if not locator_display_complete(display=display, raw=raw_path, phys=phys):
            findings.append(finding(
                check='citation_locator_incomplete',
                file=rel,
                message=(f'Citation deep-link display `{display}` (line '
                         f'{actual_line}) lacks a structural anchor '
                         f'(sec./app./ch./fig./tab./eq./def./thm./lem./prop./cor./alg.) '
                         f'and/or a page (`p. M`); '
                         f'the canonical citation form requires both.'),
                fix_hint=('Put both an anchor and the printed page inside the '
                          '`#page=N` display, e.g. '
                          '`[[0-raw/papers/X.pdf#page=5|sec. 3.2, p. 5]]`. An '
                          'appendix that carries no printed page cites the anchor '
                          'alone (`app. D.1, tab. 8`) — never invent a `p. M`.'),
            ))
        # Canonical form pairs the deep-link with a source-page link earlier in
        # the same bullet. Callout bullets are single physical lines, so scan
        # from the start of the deep-link's line — this allows the common
        # "Source notes X … (sec. Y, p. M)" form (source named at the bullet
        # start, location cited at the end) as well as the adjacent form.
        line_start = scan.rfind('\n', 0, m.start()) + 1
        window = scan[line_start:m.start()]
        if not SOURCE_PAGE_LINK_RE.search(window):
            findings.append(finding(
                check='citation_unpaired',
                file=rel,
                message=(f'Citation deep-link (line {actual_line}) is not '
                         f'preceded by a source-page wikilink; the canonical '
                         f'form pairs them.'),
                fix_hint=('Prefix the deep-link with its source-page wikilink: '
                          '`[[1-wiki/sources/X.md|X]] '
                          '([[0-raw/papers/X.pdf#page=N|sec. Y, p. M]])`.'),
            ))
    return findings


def check_citation_bracket_style(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """Flag the superseded square-bracket Form 2 citation on concept/entity/
    synthesis pages. CLAUDE.md -> Source Support And Verification mandates the
    round-bracket Form 2 `([[…|key]]; [[…|sec. X, p. M]])`; the old form wrapped
    the same wikilinks in a literal outer `[ ]` (rendering `[key; loc]`), which
    surfaces as the triple-bracket `[[[` opener. Auto-fixable: within the
    code-/Sources-/quote-masked scan built below, and per flagged occurrence only,
    swap the outer `[ ]` for `( )` (the inner wikilinks, which carry source identity
    and the locator, are unchanged) — never a global `.sub` over the unmasked body,
    which would rewrite a `[[[…]]]` literal inside a quote (a re-stamp-eligible false
    green; see the quote mask below).

    Scoped to concept/entity/synthesis pages, matching the other citation-form
    checks. Source pages use a different (page-token-as-link) form and are exempt.
    Inline code and the Sources callout are masked, as in check_citation_form.
    """
    findings: list[dict[str, Any]] = []
    scan = _blank_sources_callout(text=_mask_code_spans(text=body))
    # Blank double-quoted verbatim spans too (mirrors check_hyphenated_open_compound
    # / check_unlinked_page_mentions): a `[[[…]]]`-shaped literal inside a quote is
    # an example, not a citation, and must stay byte-identical. This fix is on the
    # verification-neutral re-stamp allowlist, so a swap reaching a quoted span would
    # ride through as a silent false green (CLAUDE.md -> Page Status text-content
    # exclusion). Length-preserving, so the line-count math below is unaffected.
    scan = re.sub(r'"[^"\n]*"', lambda m: ' ' * len(m.group(0)), scan)
    for m in SQUARE_CITATION_RE.finditer(scan):
        actual_line = end + 1 + scan[:m.start()].count('\n') + 1
        findings.append(finding(
            check='citation_bracket_style',
            file=rel,
            message=(f'Citation on line {actual_line} uses the superseded '
                     f'square-bracket Form 2 (outer literal `[ ]`, rendering '
                     f'`[key; loc]`); the canonical Form 2 wraps the citation in '
                     f'round brackets `( )`.'),
            fix_hint=('Swap the outer literal `[` `]` for `(` `)`, leaving the '
                      'inner wikilinks unchanged: '
                      '`[[[…|key]]; [[…|sec. X, p. M]]]` -> '
                      '`([[…|key]]; [[…|sec. X, p. M]])`. Swap only this flagged '
                      'occurrence, within the same code-/Sources-/quote-masked '
                      'scan the detector uses — never a `[[[…]]]` inside a verbatim '
                      'quote or code span, which is a literal, not a citation.'),
        ))
    return findings


def check_source_locator_complete(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """On a source page, a `#page=N` locator deep-link must list its structural
    anchor (sec./fig./tab./eq./app./ch./def./thm./lem./prop./cor./alg.) AND its
    page together INSIDE the link
    display — `[[…#page=1|sec. 1, p. 1]]` — never split with the anchor outside
    (`sec. 1, [[…#page=1|p. 1]]`) or page-only (`[[…#page=1|p. 1]]`). An
    `app.`-anchored display may stand on the anchor alone (the unpaginated-supplement
    exemption; see locator_display_complete).

    The source-page counterpart of citation_locator_incomplete (which enforces the
    same anchor-inside-the-display form on concept/entity/synthesis pages). Source
    pages use the identical form, just without the paired source-page wikilink
    (that would be a self-link), so this check shares the completeness test but not
    citation_unpaired. This is the inverse of the retired source_locator_anchor_inlined,
    which wrongly required the anchor OUTSIDE the link on source pages
    (CLAUDE.md -> Source Support And Verification).

    Inline code and the Sources callout are masked, length-preserving so match
    offsets map back to real line numbers.
    """
    findings: list[dict[str, Any]] = []
    scan = _blank_sources_callout(text=_mask_code_spans(text=body))
    for m in CITATION_DEEPLINK_RE.finditer(scan):
        display = m.group(1)
        km = CITATION_DEEPLINK_KEY_RE.search(m.group(0))
        raw_path = km.group(1) if km else None
        phys = int(km.group(2)) if km else None
        if not locator_display_complete(display=display, raw=raw_path, phys=phys):
            actual_line = end + 1 + scan[:m.start()].count('\n') + 1
            findings.append(finding(
                check='source_locator_incomplete',
                file=rel,
                message=(f'Source-page locator display `{display}` (line '
                         f'{actual_line}) does not carry a structural anchor '
                         f'(sec./app./ch./fig./tab./eq./def./thm./lem./prop./cor./alg.) '
                         f'and a page (`p. M`) '
                         f'together inside the `#page=N` link.'),
                fix_hint=('List the section/figure anchor and the page together '
                          'inside the link display — e.g. `sec. 1, '
                          '[[…#page=1|p. 1]]` becomes `[[…#page=1|sec. 1, p. 1]]`. '
                          'An appendix that carries no printed page cites the '
                          'anchor alone (`app. D.1, tab. 8`) — never invent a `p. M`.'),
            ))
    return findings


def check_locator_page_match(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """A `#page=N` deep-link whose display cites `p. M`, but the pagination map
    says physical page N of that raw prints a DIFFERENT number — or prints none
    at all. The one check that catches a confidently-wrong printed page: a
    locator that renders plausibly and passes every completeness check yet sends
    a reader to a page number the source does not carry (CLAUDE.md -> Source
    Support And Verification; lint Limits names this the worst failure mode).

    Keyed on the map, so an unregistered raw is silently skipped
    (check_pagination_registration nudges to register it). Deliberately
    conservative for an error-severity check: only a single `p. M` is matched
    (`pp. M–N` ranges are not), and `\\b`-guarding keeps the `p.` inside `app.`
    from matching. Runs on every wiki page kind that carries deep-links.

    Inline code and the Sources callout are masked (length-preserving) so match
    offsets map back to real line numbers.
    """
    findings: list[dict[str, Any]] = []
    scan = _blank_sources_callout(text=_mask_code_spans(text=body))
    for m in CITATION_DEEPLINK_RE.finditer(scan):
        display = m.group(1)
        pm = CITATION_PAGE_NUM_RE.search(display)
        if pm is None:
            continue  # no single `p. M` cited; completeness owns the missing-page case
        km = CITATION_DEEPLINK_KEY_RE.search(m.group(0))
        if km is None:
            continue
        raw_path, phys = km.group(1), int(km.group(2))
        status, printed = printed_page(raw=raw_path, phys=phys)
        if status == 'unregistered':
            continue
        cited = int(pm.group(1))
        if status == 'paginated' and cited == printed:
            continue
        actual_line = end + 1 + scan[:m.start()].count('\n') + 1
        if status == 'paginated':
            message = (f'Locator display `{display}` (line {actual_line}) cites '
                       f'`p. {cited}`, but the pagination map says physical page '
                       f'{phys} of `{raw_path}` prints `{printed}`.')
            fix_hint = (f'Cite the page the source prints (`p. {printed}`), or '
                        f'correct `#page={phys}` if the physical page is wrong.')
        else:  # unpaginated: the page prints no number
            message = (f'Locator display `{display}` (line {actual_line}) cites '
                       f'`p. {cited}`, but the pagination map says physical page '
                       f'{phys} of `{raw_path}` prints no number.')
            fix_hint = ('Drop `p. M` and cite the structural anchor alone (e.g. '
                        '`app. D.1, tab. 8`); never state a printed page the raw '
                        'does not carry.')
        findings.append(finding(
            check='locator_page_mismatch', file=rel,
            message=message, fix_hint=fix_hint))
    return findings


def check_wikilink_display_caps(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """A bullet that opens with a wikilink takes a leading capital on the link's
    display, because it is sentence-initial (CLAUDE.md -> Wikilink Format:
    "Sentence-initial uses leading capital"). A bullet-initial display whose first
    character is a lowercase letter is drift — a common-noun display stays
    lowercase mid-sentence but capitalizes when it opens the bullet.

    The Sources callout is exempt: its displays are filename-derived source stems
    (e.g. `illustrated-transformer`), not sentence text, and must stay verbatim, so
    it is blanked before scanning. A display whose first character is not a
    lowercase letter (a digit, an already-capitalized proper noun, a symbol) is
    left alone. Inline code is masked too; both masks are length-preserving so
    match offsets map back to real line numbers.

    Auto-fixable: upper-case the first character of the display. The agent applies
    the rewrite (the script reports; it does not edit files).
    """
    findings: list[dict[str, Any]] = []
    scan = _blank_sources_callout(text=_mask_code_spans(text=body))
    for m in BULLET_INITIAL_WIKILINK_RE.finditer(scan):
        display = m.group(1)
        if display[:1].islower():
            actual_line = end + 1 + scan[:m.start()].count('\n') + 1
            fixed = display[:1].upper() + display[1:]
            findings.append(finding(
                check='wikilink_display_uncapitalized',
                file=rel,
                message=(f'Bullet-initial wikilink display `{display}` (line '
                         f'{actual_line}) starts lowercase; a sentence-initial '
                         f'wikilink takes a leading capital.'),
                fix_hint=(f'Capitalize the first character of the display: '
                          f'`{display}` -> `{fixed}`.'),
            ))
    return findings


def check_embed_isolated(body: str, rel: str, end: int) -> list[dict[str, Any]]:
    """Flag a standalone image embed not set off by a blank quoted line both
    above and below it (CLAUDE.md -> Attachments / Source Pages).

    Inside an Obsidian callout an embed butted directly against the bullet above
    or the line below lazy-continues that content and mis-renders — the embed
    must be its own block, so the rule is: blank quoted line (`>`), embed, blank
    quoted line (`>`). Only quoted lines whose sole content is one embed are
    governed; an embed mixed with prose on a line is left alone.

    Auto-fixable: insert a blank `>` line directly above and/or below the embed
    line on whichever side is missing. The agent applies the insertion (the
    script reports; it does not rewrite files).
    """
    findings: list[dict[str, Any]] = []
    lines = body.split('\n')
    for i, line in enumerate(lines):
        if not QUOTED_EMBED_LINE_RE.match(line):
            continue
        prev_ok = i > 0 and QUOTED_BLANK_RE.match(lines[i - 1]) is not None
        next_ok = (i + 1 < len(lines)
                   and QUOTED_BLANK_RE.match(lines[i + 1]) is not None)
        if prev_ok and next_ok:
            continue
        if not prev_ok and not next_ok:
            where = 'above and below'
        elif not prev_ok:
            where = 'above'
        else:
            where = 'below'
        embed_m = EMBED_RE.search(line)
        embed = embed_m.group(0) if embed_m else line.strip()
        actual_line = end + 1 + i + 1
        findings.append(finding(
            check='embed_not_isolated',
            file=rel,
            message=(f'Image embed `{embed}` on line {actual_line} is not set '
                     f'off by a blank quoted line {where}; an embed butted '
                     f'against adjacent callout content mis-renders in Obsidian.'),
            fix_hint=(f'Insert a blank `>` line {where} the embed line so it '
                      f'sits in its own block (CLAUDE.md -> Attachments).'),
        ))
    return findings


def check_index_drift(wiki_root: Path) -> list[dict[str, Any]]:
    """Compare index.md entries to actual files in sources/entities/concepts/syntheses."""
    findings: list[dict[str, Any]] = []
    index_path = wiki_root / 'index.md'
    if not index_path.exists():
        return [finding(
            check='missing_index',
            file='1-wiki/index.md',
            message='index.md is absent.',
            fix_hint='Run /lint to scaffold or restore index.md.',
        )]

    text = index_path.read_text(encoding='utf-8')
    sections = {
        'Sources': (wiki_root / 'sources', '## Entities'),
        'Entities': (wiki_root / 'entities', '## Concepts'),
        'Concepts': (wiki_root / 'concepts', '## Syntheses'),
        'Syntheses': (wiki_root / 'syntheses', None),
    }
    wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    for section, (folder, next_section) in sections.items():
        # Files actually present.
        present = sorted(p.stem for p in folder.glob('*.md')) if folder.exists() else []
        # Index-listed stems for this section.
        start_marker = f'## {section}'
        end_marker = next_section
        m_start = re.search(rf"^{re.escape(start_marker)}\s*$", text, re.MULTILINE)
        if not m_start:
            continue
        body_start = m_start.end()
        if end_marker:
            m_end = re.search(rf"^{re.escape(end_marker)}\s*$",
                              text[body_start:], re.MULTILINE)
            section_body = text[body_start:body_start + m_end.start()] if m_end else text[body_start:]
        else:
            section_body = text[body_start:]
        # Index wikilinks are path-qualified; normalize each to its stem.
        listed = sorted({_link_stem(raw=x)
                         for x in wikilink_re.findall(section_body)})
        rel_folder = str(folder.relative_to(wiki_root.parent))

        in_files_not_index = sorted(set(present) - set(listed))
        in_index_not_files = sorted(set(listed) - set(present))

        for stem in in_files_not_index:
            findings.append(finding(
                check='index_missing_entry',
                file='1-wiki/index.md',
                message=f"{section}: file `{stem}.md` exists but isn't listed in index.md.",
                fix_hint=(f'Add `- [[{rel_folder}/{stem}.md|{stem}]]` to the '
                          f'{section} section of index.md.'),
            ))
        for stem in in_index_not_files:
            findings.append(finding(
                check='index_stale_entry',
                file='1-wiki/index.md',
                message=(f'{section}: index.md lists `{stem}.md` but no matching '
                         f'file exists.'),
                fix_hint=f'Remove the entry from index.md or restore the file.',
            ))
    return findings


def check_attachments(wiki_root: Path) -> list[dict[str, Any]]:
    """Cross-page attachment checks (CLAUDE.md Attachments section).

    1. Embedded image basenames resolve to a file under `1-wiki/attachments/`.
    2. Each source page's `attachments:` frontmatter entry resolves.
    3. Each file in `1-wiki/attachments/{stem}/` is listed in the `{stem}`
       source page's `attachments:` frontmatter.
    4. Duplicate basenames across stems (Obsidian wikilink ambiguity).
    5. Orphan attachment files: present on disk, embedded by no page.
    """
    findings: list[dict[str, Any]] = []
    attachments_root = wiki_root / 'attachments'
    if not attachments_root.exists():
        return findings

    by_basename = index_attachments_by_basename(wiki_root=wiki_root)

    # Check 4: duplicate basenames across stems. Embeds are now path-qualified
    # (`![[1-wiki/attachments/{stem}/fig.png]]`), so a shared basename no
    # longer breaks Obsidian resolution — this is a readability nudge only,
    # hence info-level.
    for basename, paths in by_basename.items():
        if len(paths) > 1:
            locations = sorted(str(p.relative_to(wiki_root.parent))
                               for p in paths)
            findings.append(finding(
                check='attachment_duplicate_basename',
                file=f'1-wiki/attachments/',
                message=(
                    f'Basename `{basename}` is reused across {len(paths)} '
                    f'attachment folders: {locations}. Path-qualified embeds '
                    f'resolve unambiguously, but distinct names read better.'
                ),
                fix_hint=('Optional: rename one (descriptive or stem-prefixed) for '
                          'clearer links.'),
            ))

    # Build set of basenames embedded anywhere (across all wiki pages).
    embedded_basenames: set[str] = set()
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            rel = str(page.relative_to(wiki_root.parent))
            for basename in extract_embeds(body=text):
                embedded_basenames.add(basename)
                # Check 1: embed basename must resolve.
                if basename not in by_basename:
                    findings.append(finding(
                        check='embed_unresolved',
                        file=rel,
                        message=(f'Embedded image `![[{basename}]]` does not resolve '
                                 f'to any file under `1-wiki/attachments/`.'),
                        fix_hint='Re-extract the figure or fix the basename.',
                    ))

    # Check 2 + 3: source-page `attachments:` frontmatter agrees with on-disk
    # files in `1-wiki/attachments/{stem}/`.
    sources_dir = wiki_root / 'sources'
    if sources_dir.exists():
        for page in sources_dir.glob('*.md'):
            stem = page.stem
            text = page.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            if fm is None:
                continue
            rel = str(page.relative_to(wiki_root.parent))
            declared = attachments_basenames(fm=fm)
            stem_dir = attachments_root / stem
            actual = (sorted(p.name for p in stem_dir.iterdir()
                             if p.is_file() and p.suffix.lower().lstrip('.') in IMAGE_EXTS)
                      if stem_dir.exists() else [])
            declared_set = set(declared)
            actual_set = set(actual)

            for entry in declared:
                if entry not in by_basename:
                    findings.append(finding(
                        check='attachments_frontmatter_missing_file',
                        file=rel,
                        message=(
                            f'`attachments:` lists `[[1-wiki/attachments/{stem}/'
                            f'{entry}]]` but no matching file exists under '
                            f'`1-wiki/attachments/`.'
                        ),
                        fix_hint='Re-extract the file or remove the entry.',
                    ))
            for name in sorted(actual_set - declared_set):
                findings.append(finding(
                    check='attachments_file_unlisted',
                    file=rel,
                    message=(
                        f"File `1-wiki/attachments/{stem}/{name}` exists but isn't "
                        f"listed in this source page's `attachments:` frontmatter."
                    ),
                    fix_hint=(f"Add `\"[[1-wiki/attachments/{stem}/{name}]]\"` to the "
                              f"page's `attachments:` list."),
                ))

    # Check 5: orphan files (present, never embedded).
    for basename, paths in by_basename.items():
        if basename in embedded_basenames:
            continue
        for path in paths:
            findings.append(finding(
                check='attachment_orphan',
                file=str(path.relative_to(wiki_root.parent)),
                message='Attachment file is not embedded by any wiki page.',
                fix_hint='Embed it where useful, or remove via /forget.',
            ))

    return findings


# Wikilink to a wiki page (basename, optional |alias). Distinguished from
# image embeds (`![[...]]`) by the negative lookbehind for `!`.
WIKILINK_PAGE_RE = re.compile(
    r'(?<!!)\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]'
)


def check_orphan_pages(wiki_root: Path) -> list[dict[str, Any]]:
    """Flag wiki pages not reachable from `index.md` via wikilinks (D 9.12).

    Walks the wikilink graph starting from `index.md`. Pages in
    `sources/`, `concepts/`, `entities/`, or `syntheses/` that the
    traversal never reaches are orphans (Info-level).

    Source pages are exempted from the orphan check: a source page is
    typically reached from the concept/entity pages it supports, not
    directly from index.md, but index.md does list every source page
    in its Sources section. So if a source page is missing from index
    that's a separate check (index drift, J). The orphan check is about
    concept/entity/synthesis pages that have no inbound link path from
    the index — usually a sign the page was never wired into the wiki.
    """
    findings: list[dict[str, Any]] = []
    index_path = wiki_root / 'index.md'
    if not index_path.exists():
        return findings

    # Map basename (stem) -> file path for every wiki page.
    pages_by_stem: dict[str, Path] = {}
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            pages_by_stem[page.stem] = page

    if not pages_by_stem:
        return findings

    # BFS from index.md.
    visited: set[str] = set()
    queue: list[Path] = [index_path]
    while queue:
        current = queue.pop(0)
        try:
            text = current.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for m in WIKILINK_PAGE_RE.finditer(text):
            # Targets are path-qualified; reduce to the page stem. Attachment
            # or raw links normalize to a stem that isn't in pages_by_stem,
            # so they're naturally skipped as non-page below.
            target_stem = _link_stem(raw=m.group(1))
            if not target_stem:
                continue
            if target_stem in visited:
                continue
            if target_stem not in pages_by_stem:
                # Dangling wikilink — separate check (broken link) handles it.
                continue
            visited.add(target_stem)
            queue.append(pages_by_stem[target_stem])

    # Anything in pages_by_stem but not visited is unreachable.
    for stem, page in sorted(pages_by_stem.items()):
        if stem in visited:
            continue
        # Source pages are listed in index.md directly (J check covers index
        # drift). If a source page is in pages_by_stem but unvisited, it
        # means it isn't listed in index.md or any reachable page — still a
        # genuine orphan signal. Surface it.
        rel = str(page.relative_to(wiki_root.parent))
        findings.append(finding(
            check='orphan_page',
            file=rel,
            message=(
                f'Page is not reachable from `1-wiki/index.md` via wikilinks. '
                f'Likely never wired into the wiki, or its only inbound links '
                f'were removed.'
            ),
            fix_hint=('Link the page from a relevant concept, entity, synthesis, or '
                      'index.md, or quarantine it via /forget if no longer wanted.'),
        ))
    return findings


def _extract_callout_body(body: str, slug: str) -> str | None:
    """Return the text between the `> [!{slug}]` header and the next callout
    header (or end of body). None if the callout isn't present.
    """
    headers = list(CALLOUT_RE.finditer(body))
    for i, m in enumerate(headers):
        if m.group(1) != slug:
            continue
        start = m.end()
        end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        return body[start:end_pos]
    return None


def _extract_wikilinks(text: str) -> list[str]:
    """Extract wikilink target stems from text (not image embeds).

    Targets are path-qualified (`[[1-wiki/concepts/foo.md|foo]]`); each is
    normalized to its bare stem so callers compare by page identity. Empty
    stems (malformed links) are dropped.
    """
    out = []
    for m in WIKILINK_PAGE_RE.finditer(text):
        stem = _link_stem(raw=m.group(1))
        if stem:
            out.append(stem)
    return out


def check_sources_callout_sync(wiki_root: Path) -> list[dict[str, Any]]:
    """Sources callout wikilinks must match `sources:` frontmatter (D X.3a).

    A page can drift between `sources: [[a]]` in frontmatter and a body
    `> [!sources]` callout listing `[[b]]` — the support trail and the
    reading trail then disagree silently.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    for folder in ('entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            fm, end = parse_frontmatter(text=text)
            if fm is None:
                continue
            body = '\n'.join(text.split('\n')[end + 1:])
            sources_body = _extract_callout_body(body=body, slug='sources')
            if sources_body is None:
                continue  # Missing-section check handles absence.
            frontmatter_sources = set()
            for entry in fm.get('sources', []) if isinstance(
                    fm.get('sources'), list) else []:
                if isinstance(entry, str):
                    m = WIKILINK_BASENAME_RE.match(entry.strip())
                    stem = _link_stem(raw=m.group(1) if m else entry.strip())
                    frontmatter_sources.add(stem)
            body_sources = set(_extract_wikilinks(text=sources_body))
            if frontmatter_sources == body_sources:
                continue
            missing_in_body = sorted(frontmatter_sources - body_sources)
            extra_in_body = sorted(body_sources - frontmatter_sources)
            rel = str(page.relative_to(repo_root))
            parts = []
            if missing_in_body:
                parts.append(f'in frontmatter but not in callout: '
                             f'{missing_in_body}')
            if extra_in_body:
                parts.append(f'in callout but not in frontmatter: '
                             f'{extra_in_body}')
            findings.append(finding(
                check='sources_callout_desync',
                file=rel,
                message=(f'`sources:` frontmatter and `> [!sources]` callout disagree. '
                         f"{'; '.join(parts)}."),
                fix_hint=('Reconcile so both list the same source pages; the '
                          'frontmatter is the machine-readable trail and the callout '
                          'is the reader-facing trail.'),
            ))
    return findings


def check_source_link_resolution(wiki_root: Path) -> list[dict[str, Any]]:
    """Every `sources:` frontmatter entry resolves to an existing source page.

    Source-support links must never dangle: a concept/entity/synthesis page
    cannot cite a source page that does not exist on disk (unlike concept or
    author wikilinks, which the schema allows to dangle). Catches a `sources:`
    entry left pointing at a deleted or renamed source page — the deterministic
    provenance check the manual lint walk used to do by eye.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    sources_dir = wiki_root / 'sources'
    for folder in ('entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            if fm is None:
                continue
            entries = fm.get('sources')
            if not isinstance(entries, list):
                continue
            rel = str(page.relative_to(repo_root))
            for entry in entries:
                if not isinstance(entry, str):
                    continue
                m = WIKILINK_BASENAME_RE.match(entry.strip())
                stem = _link_stem(raw=m.group(1) if m else entry.strip())
                if not stem:
                    continue
                if not (sources_dir / f'{stem}.md').exists():
                    findings.append(finding(
                        check='source_link_unresolved',
                        file=rel,
                        message=(f'`sources:` entry `{stem}` does not resolve to a '
                                 f'source page at `1-wiki/sources/{stem}.md`.'),
                        fix_hint=('Fix the link, or remove the stale entry and update '
                                  'source_count; source-support links must never '
                                  'dangle.'),
                    ))
    return findings


def check_concept_source_bidirectional(
        wiki_root: Path) -> list[dict[str, Any]]:
    """Source ↔ concept/entity/synthesis bidirectional support (D X.3b).

    For every wikilink in a source page's `concepts-entities` callout, the
    linked page must list the source in `sources:`. And for every source
    listed in a concept/entity page's `sources:`, the source page
    must list the page in `concepts-entities`. Asymmetry signals drift
    introduced by forget, supersede, or manual edits.

    Synthesis pages are exempt from the reverse direction: a source's
    `concepts-entities` callout lists the concepts/entities it supports, not the
    syntheses that cite it, so a synthesis citing a source does not oblige the
    source to back-link the synthesis. The forward direction still applies (a
    synthesis wrongly placed in a source's `concepts-entities` is flagged).
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent

    # Build: source-stem -> set of pages declared in its concepts-entities
    # callout.
    source_declares: dict[str, set[str]] = {}
    sources_dir = wiki_root / 'sources'
    if sources_dir.exists():
        for page in sorted(sources_dir.glob('*.md')):
            text = page.read_text(encoding='utf-8')
            _, end = parse_frontmatter(text=text)
            body = '\n'.join(text.split('\n')[end + 1:])
            ce_body = _extract_callout_body(body=body, slug='concepts-entities')
            declared = set(_extract_wikilinks(text=ce_body)) if ce_body else set()
            source_declares[page.stem] = declared

    # Build: page-stem -> (page path, set of sources in frontmatter).
    page_sources: dict[str, tuple[Path, set[str]]] = {}
    for folder in ('entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in sorted(folder_path.glob('*.md')):
            text = page.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            if fm is None:
                continue
            srcs = set()
            for entry in fm.get('sources', []) if isinstance(
                    fm.get('sources'), list) else []:
                if isinstance(entry, str):
                    m = WIKILINK_BASENAME_RE.match(entry.strip())
                    stem = _link_stem(raw=m.group(1) if m else entry.strip())
                    srcs.add(stem)
            page_sources[page.stem] = (page, srcs)

    # Forward: source's concepts-entities -> linked page must list source.
    # Sort every iteration (dict/set order varies per process under string hash
    # randomization) so the emitted findings — and thus the script's stdout — are
    # deterministic across runs.
    for source_stem, declared_pages in sorted(source_declares.items(),
                                              key=lambda kv: kv[0]):
        for page_stem in sorted(declared_pages):
            if page_stem not in page_sources:
                continue  # Broken-wikilink check handles it.
            page_path, page_srcs = page_sources[page_stem]
            if source_stem in page_srcs:
                continue
            rel = str(page_path.relative_to(repo_root))
            findings.append(finding(
                check='concept_source_asymmetry',
                file=rel,
                message=(
                    f'Source `[[{source_stem}]]` declares this page in its '
                    f"`concepts-entities` callout, but this page's `sources:` "
                    f"frontmatter doesn't list that source."
                ),
                fix_hint=(
                    f"Either add `[[{source_stem}]]` to this page's `sources:` "
                    f'frontmatter and `Sources` callout, or remove the wikilink '
                    f"from the source page's `concepts-entities`."
                ),
            ))

    # Reverse: page's sources -> source must list page in concepts-entities.
    # A source page's `concepts-entities` callout lists the concept/entity pages
    # it supports (CLAUDE.md -> Source Pages), not the synthesis pages that cite
    # it — a synthesis is a cross-source argument page, not a concept/entity the
    # source "supports". So a synthesis listing a source in `sources:` does not
    # oblige the source to back-link the synthesis; skip syntheses in the reverse
    # direction (the forward direction still flags a synthesis wrongly placed in a
    # source's concepts-entities callout).
    for page_stem, (page_path, srcs) in sorted(page_sources.items(),
                                              key=lambda kv: kv[0]):
        if page_path.parent.name == 'syntheses':
            continue
        for source_stem in sorted(srcs):
            if source_stem not in source_declares:
                continue  # Source page doesn't exist; other check handles.
            if page_stem in source_declares[source_stem]:
                continue
            rel = str(page_path.relative_to(repo_root))
            findings.append(finding(
                check='concept_source_asymmetry',
                file=rel,
                message=(
                    f'This page lists `[[{source_stem}]]` in `sources:`, but '
                    f"the source page's `concepts-entities` callout doesn't "
                    f'link back to this page.'
                ),
                fix_hint=(
                    f"Either add `[[{page_stem}]]` to the source page's "
                    f'`concepts-entities` callout, or remove `[[{source_stem}]]` '
                    f"from this page's `sources:`."
                ),
            ))
    return findings


def check_needs_update_reason(wiki_root: Path) -> list[dict[str, Any]]:
    """`needs-update` pages must provide a reason (D 5.5c).

    CLAUDE.md says a needs-update page needs either a real Contradictions or
    Tensions entry, OR a `needs_update_reason:` frontmatter field. Lint
    enforces that here.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            fm, end = parse_frontmatter(text=text)
            if fm is None or fm.get('status') != 'needs-update':
                continue
            reason = fm.get('needs_update_reason')
            has_reason = (isinstance(reason, str) and reason.strip()) or (
                isinstance(reason, list) and any(
                    isinstance(r, str) and r.strip() for r in reason))
            body = '\n'.join(text.split('\n')[end + 1:])
            # Sources use Contradictions; syntheses use Tensions.
            slug = 'tensions' if folder == 'syntheses' else 'contradictions'
            section_body = _extract_callout_body(body=body, slug=slug)
            has_real_section = False
            if section_body is not None:
                lines = [line.strip() for line in section_body.splitlines()
                         if line.strip() and line.strip() != '>'
                         and not BLOCK_ID_RE.match(line.strip())]
                # Real content if any non-blank quoted line isn't a placeholder.
                for line in lines:
                    if line in EMPTY_PLACEHOLDERS:
                        continue
                    if line.startswith('> -') or line.startswith('>'):
                        has_real_section = True
                        break
            if has_reason or has_real_section:
                continue
            rel = str(page.relative_to(repo_root))
            findings.append(finding(
                check='needs_update_without_reason',
                file=rel,
                message=(
                    f'Page is `status: needs-update` but provides no reason — '
                    f'`needs_update_reason:` frontmatter is empty/absent and '
                    f'the `{slug.capitalize()}` callout is the empty placeholder.'
                ),
                fix_hint=(
                    'Add a one-line `needs_update_reason:` to frontmatter, or '
                    f'populate the `{slug.capitalize()}` callout with the '
                    'actual contradiction/tension that needs resolving.'
                ),
            ))
    return findings


def check_alias_collisions(wiki_root: Path) -> list[dict[str, Any]]:
    """Flag duplicate aliases and aliases that shadow another page's filename
    (D 9.13).

    Obsidian uses `aliases:` for search and `[[wikilink]]` autocomplete.
    Uniqueness across the vault is required for unambiguous resolution.
    Two failure modes:

    - alias_collision: two pages claim the same alias. A wikilink-by-alias
      can't tell them apart; Obsidian picks one nondeterministically.
    - alias_shadows_filename: an alias matches another page's filename
      stem. The wikilink resolves to the file, not the aliased page —
      silent misdirection.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent

    # Build alias -> [page paths] and filename basename set.
    alias_to_pages: dict[str, list[Path]] = {}
    filename_stems: set[str] = set()
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            filename_stems.add(page.stem)
            text = page.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            if fm is None:
                continue
            aliases = fm.get('aliases')
            if not isinstance(aliases, list):
                continue
            for alias in aliases:
                if not isinstance(alias, str) or not alias.strip():
                    continue
                alias_to_pages.setdefault(alias.strip(), []).append(page)

    # Check: duplicate aliases across pages.
    for alias, pages in sorted(alias_to_pages.items()):
        if len(pages) > 1:
            rels = sorted(str(p.relative_to(repo_root)) for p in pages)
            findings.append(finding(
                check='alias_collision',
                file=rels[0],
                message=(f'Alias `{alias}` is claimed by {len(pages)} pages: '
                         f'{rels}. Obsidian wikilink resolution is ambiguous.'),
                fix_hint=('Drop the alias from all but one page, or rename one of the '
                          'aliases to be unique.'),
            ))

    # Check: alias shadows another page's filename.
    for alias, pages in sorted(alias_to_pages.items()):
        if alias not in filename_stems:
            continue
        # The alias matches some filename stem. Find which page owns it.
        owner_page = None
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            candidate = wiki_root / folder / f'{alias}.md'
            if candidate.exists():
                owner_page = candidate
                break
        for page in pages:
            if owner_page is not None and page.resolve() == owner_page.resolve():
                continue  # Page can alias its own filename harmlessly.
            rel = str(page.relative_to(repo_root))
            owner_rel = (str(owner_page.relative_to(repo_root))
                         if owner_page else '(unknown)')
            findings.append(finding(
                check='alias_shadows_filename',
                file=rel,
                message=(
                    f"Alias `{alias}` matches another page's filename "
                    f'(`{owner_rel}`). Wikilinks `[[{alias}]]` will resolve '
                    f'to the filename, not this page.'
                ),
                fix_hint=("Rename the alias so it doesn't collide with an existing "
                          'page filename.'),
            ))
    return findings


def check_raw_integrity(wiki_root: Path) -> list[dict[str, Any]]:
    """Critical checks for raw-vs-wiki integrity (D 8.17, lint checks 3 & 4).

    Check 3: every source page's `file:` frontmatter must resolve to a file
    that actually exists under `0-raw/`. A source page pointing at a deleted
    or renamed raw file silently breaks the audit trail back to evidence.

    Check 4: every raw file under `0-raw/{papers,articles,media,other}/`
    should have a matching source page that references it via `file:`. A
    raw file with no source page is uningested — flag at Critical so the
    user notices the gap.

    Note: 0-raw/ may be at `wiki_root.parent / "0-raw"` for the standard
    layout, or absent (e.g., for a vault under construction).
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    raw_root = repo_root / '0-raw'
    sources_dir = wiki_root / 'sources'

    # Build map: raw-file basename -> raw file path
    raw_files_by_basename: dict[str, Path] = {}
    if raw_root.exists():
        for sub in ('papers', 'articles', 'media', 'other'):
            sub_path = raw_root / sub
            if not sub_path.exists():
                continue
            for f in sub_path.rglob('*'):
                if f.is_file() and not f.name.startswith('.'):
                    raw_files_by_basename.setdefault(f.name, f)

    # Build set: basenames that source pages reference via file: frontmatter
    referenced_raw: set[str] = set()
    if sources_dir.exists():
        for page in sources_dir.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            fm, _ = parse_frontmatter(text=text)
            if fm is None:
                continue
            file_field = fm.get('file')
            if not isinstance(file_field, str) or not file_field.strip():
                # Frontmatter completeness check covers missing file: field.
                continue
            # file: is a path-qualified wikilink "[[0-raw/papers/X.pdf]]";
            # reduce to the raw file's basename for the on-disk lookup.
            m = WIKILINK_BASENAME_RE.match(file_field.strip())
            basename = _link_name(raw=m.group(1) if m else file_field.strip())
            referenced_raw.add(basename)
            rel = str(page.relative_to(repo_root))
            # G4: source-page stem must match the raw-file stem (CLAUDE.md ->
            # Page Filenames / Raw Sources — the two share a basename). A
            # chapter/section split is allowed: `<raw-stem>-chNN` / `-<section>`.
            raw_stem = Path(basename).stem
            if page.stem != raw_stem and not page.stem.startswith(raw_stem + '-'):
                findings.append(finding(
                    check='source_stem_mismatch',
                    file=rel,
                    message=(f'Source-page stem `{page.stem}` does not match its '
                             f'raw-file stem `{raw_stem}` (`file:` points at '
                             f'`{basename}`). A source page and its raw must '
                             f'share a basename.'),
                    fix_hint=('Rename the source page to the raw stem (or, for a '
                              'chapter split, `<raw-stem>-chNN`). User-owned: '
                              'renaming a file is a safety operation, not a lint '
                              'or audit auto-fix.'),
                ))
            # Check 3: the referenced raw file must exist.
            if basename not in raw_files_by_basename:
                findings.append(finding(
                    check='file_field_unresolved',
                    file=rel,
                    message=(
                        f"Source page's `file: \"[[{basename}]]\"` does not "
                        f'resolve to any file under `0-raw/`. Audit trail to '
                        f'raw evidence is broken.'
                    ),
                    fix_hint=(
                        'Restore the raw file at its expected `0-raw/` location, '
                        'fix the `file:` field to the correct basename, or '
                        'quarantine the source page via /forget if the raw '
                        'source is gone for good.'
                    ),
                ))

    # Check 4: every raw file should be referenced by some source page.
    for basename, raw_path in sorted(raw_files_by_basename.items()):
        if basename in referenced_raw:
            continue
        rel = str(raw_path.relative_to(repo_root))
        findings.append(finding(
            check='raw_without_source_page',
            file=rel,
            message=(f'Raw file `{rel}` has no source page that references it via '
                     f'`file:` frontmatter. The file is uningested.'),
            fix_hint=('Run /ingest on the file, or move it out of `0-raw/` if it '
                      "shouldn't become a source."),
        ))
    return findings


def check_recursive_citations(wiki_root: Path) -> list[dict[str, Any]]:
    """Flag concept/entity/synthesis pages that cite only other wiki pages
    instead of source pages (D 3.9 / D X.3).

    The "wiki cites itself as truth" failure (BP §13) shows up structurally
    when a derived page has empty `sources:` frontmatter but its body wikilinks
    only to other concept/entity/synthesis pages — there's no actual source
    grounding, just a closed loop of cross-references.

    The existing `zero_source_page` check catches the empty-sources part. This
    check adds the second condition: body wikilinks exist but none of them
    point at a source page.
    """
    findings: list[dict[str, Any]] = []

    # Build set of source-page stems for resolution.
    source_stems: set[str] = set()
    sources_dir = wiki_root / 'sources'
    if sources_dir.exists():
        source_stems = {p.stem for p in sources_dir.glob('*.md')}

    # Build set of all wiki page stems (for filtering out attachment / dangling links).
    all_stems: set[str] = set()
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            all_stems.add(page.stem)

    for folder in ('entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            fm, end = parse_frontmatter(text=text)
            if fm is None:
                continue
            sources = fm.get('sources') if isinstance(fm.get('sources'),
                                                     list) else []
            if sources:
                continue  # Has at least one source; not a recursion case.
            body = '\n'.join(text.split('\n')[end + 1:])
            wikilinks = [_link_stem(raw=m.group(1))
                         for m in WIKILINK_PAGE_RE.finditer(body)]
            # Keep only links that resolve to a real wiki page (drops
            # attachment links and danglings, which aren't page stems).
            body_page_links = [link for link in wikilinks
                               if link and link in all_stems]
            if not body_page_links:
                continue  # No body wikilinks at all; not a recursion case.
            cites_source = any(link in source_stems
                               for link in body_page_links)
            if cites_source:
                continue  # At least one wikilink hits a source page; OK.
            rel = str(page.relative_to(wiki_root.parent))
            findings.append(finding(
                check='recursive_wiki_citation',
                file=rel,
                message=(
                    f'Page has empty `sources:` but body wikilinks point only at '
                    f'non-source wiki pages ({sorted(set(body_page_links))[:3]}'
                    f"{'...' if len(set(body_page_links)) > 3 else ''}). The "
                    f'wiki risks citing itself as truth without any source '
                    f'grounding (D 3.9 / D X.3).'
                ),
                fix_hint=(
                    'Add at least one source page to `sources:` and the '
                    '`Sources` callout, or quarantine the page via /forget if '
                    "it's an unsupported draft."
                ),
            ))
    return findings


def check_duplicate_concepts(wiki_root: Path) -> list[dict[str, Any]]:
    """Flag pairs of concept/entity pages with very similar H1 titles.

    Cheap mechanical signal for the duplicate-detection breakage flagged in
    deep-research-report.md — a source refresh that creates a near-twin page
    instead of updating the existing one. Audit handles semantic duplicates
    (same idea, different titles); this catches the easy lexical variant.

    Heuristic: lowercase + tokenize the H1 (alphanumeric words only), then
    Jaccard-overlap each pair of word sets. Threshold lives at module scope
    as `JACCARD_THRESHOLD` with its tuning rationale.
    """
    pages: list[tuple[Path, str, set[str]]] = []
    for kind in ('concepts', 'entities'):
        folder = wiki_root / kind
        if not folder.exists():
            continue
        for path in sorted(folder.glob('*.md')):
            try:
                text = path.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            # Strip YAML frontmatter before the H1 regex; otherwise the
            # `^# (.+)$` pattern matches frontmatter section comments like
            # `# identity` and reports every page's title as `identity`,
            # producing N*(N-1)/2 false-positive duplicate-candidate
            # warnings on any vault with frontmatter comments.
            fm, end = parse_frontmatter(text=text)
            body = ('\n'.join(text.split('\n')[end + 1:])
                    if fm is not None else text)
            m = re.search(r'^# (.+)$', body, re.MULTILINE)
            title = m.group(1).strip() if m else path.stem
            words = set(re.sub(r'[^a-z0-9]+', ' ', title.lower()).split())
            if words:
                pages.append((path, title, words))

    findings: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for i, (p1, t1, w1) in enumerate(pages):
        for p2, t2, w2 in pages[i + 1:]:
            jaccard = len(w1 & w2) / len(w1 | w2)
            if jaccard < JACCARD_THRESHOLD:
                continue
            key = tuple(sorted([p1.name, p2.name]))
            if key in seen_pairs:
                continue
            seen_pairs.add(key)
            rel1 = str(p1.relative_to(wiki_root.parent))
            rel2 = str(p2.relative_to(wiki_root.parent))
            findings.append(finding(
                check='concept_duplicate_candidate',
                file=rel1,
                message=(f"Near-duplicate title with `{rel2}`: '{t1}' / '{t2}' "
                         f'(word-overlap {jaccard:.2f}).'),
                fix_hint=('Audit whether to merge with /supersede, or rename to make '
                          'the distinction explicit.'),
            ))
    return findings


def check_reciprocal_contradictions(
        wiki_root: Path) -> list[dict[str, Any]]:
    """Check missing_reciprocal_contradiction — reciprocal contradiction graph.

    If page A's Contradictions callout names `[[B]]`, page B's
    Contradictions (or Tensions, for syntheses) callout must mention A
    back. One-sided contradictions usually mean the second page hasn't
    absorbed the disagreement yet. Mirror of the existing
    connections-reciprocity logic, applied to the contradiction graph.

    Synthesis namers are exempt: a synthesis's Tensions callout cites its
    sources as evidence and counter-evidence, not as mutual-contradiction
    partners, so a synthesis naming `[[B]]` does not require B to reciprocate.
    A synthesis can still be a target B (a non-synthesis page genuinely
    contradicting a synthesis is flagged); only synthesis-originated links are
    skipped.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent

    # First pass: for every wiki page, parse its Contradictions/Tensions
    # callout body and collect the wikilink target stems.
    pages: dict[str, tuple[Path, set[str]]] = {}
    # Stem -> the source-page stems it lists in `sources:` frontmatter. A page
    # and one of its own sources are the same underlying work, so a contradiction
    # link between them is the page citing that source as evidence for a
    # disagreement with a *third* party, not a mutual contradiction the source
    # must reciprocate (the same reason synthesis namers are exempt below).
    page_sources: dict[str, set[str]] = {}
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        slug = 'tensions' if folder == 'syntheses' else 'contradictions'
        for page in folder_path.glob('*.md'):
            try:
                text = page.read_text(encoding='utf-8')
            except (UnicodeDecodeError, OSError):
                continue
            fm, end = parse_frontmatter(text=text)
            if fm is None:
                continue
            page_sources[page.stem] = {
                m.group(1)
                for s in (fm.get('sources') or [])
                if isinstance(s, str)
                for m in [re.search(r'/sources/([^./|\]]+)\.md', s)]
                if m
            }
            body = '\n'.join(text.split('\n')[end + 1:])
            callout_body = _extract_callout_body(body=body, slug=slug)
            if callout_body is None:
                # Missing callout is its own finding (check_id: section_order); record
                # an empty target set so reciprocity still fires for
                # incoming links.
                pages[page.stem] = (page, set())
                continue
            # Drop "see ..." / "see also ..." navigational links — they
            # point at parent or sibling pages for further reading, not at
            # the contradicting party. A bullet like "X disagrees with Y.
            # See [[parent]] for the full version." should treat `parent`
            # as a see-also link, not a contradiction party.
            # Excise navigational see-also clauses (including a chain of links
            # joined by and/or/commas) but NOT genuine contradiction links.
            # Two passes: (1) "see also" / "see:" are unambiguous navigational
            # cues anywhere; (2) a bare verb "see" is navigational only at a
            # clause boundary (line/bullet start — tolerating the `> ` quote
            # prefix — after sentence punctuation, or after `(`), so an ordinary
            # "we see [[X]]" does NOT drop [[X]] as a party. The boundary is
            # captured and restored via \1. Bare "see" mid-sentence is kept,
            # which was the false-negative the older bare-`see` excision caused.
            targets_body = re.sub(
                r'(?i)\bsee(?:\s+also\b|\s*:)\s*'
                r'(?:\[\[[^\]]*\]\]\s*(?:and|or|,|&)?\s*)+',
                '', callout_body)
            targets_body = re.sub(
                r'(?im)(^[>\s]*(?:[-*][ \t]+)?|[.;!?)]\s+|\()see\s+'
                r'(?:\[\[[^\]]*\]\]\s*(?:and|or|,|&)?\s*)+',
                r'\1', targets_body)
            targets = set(_extract_wikilinks(text=targets_body))
            targets.discard(page.stem)  # ignore self-links
            pages[page.stem] = (page, targets)

    # Second pass: for each A → B in the contradiction graph, B → A must
    # exist. Skip targets that aren't tracked wiki pages (raw files,
    # missing pages — those are other checks' territory). Dedupe pairs so
    # a missing reciprocal is reported once, not twice.
    seen_pairs: set[tuple[str, str]] = set()
    for a_stem, (a_path, a_targets) in pages.items():
        # A synthesis's Tensions callout cites its sources as evidence and
        # counter-evidence (CLAUDE.md -> Synthesis Pages: Tensions), not as
        # mutual-contradiction partners — so a synthesis naming `[[B]]` does not
        # oblige B to name the synthesis back. Any genuine cross-source
        # disagreement a synthesis records reciprocates between the disagreeing
        # sources, not between the synthesis and each page it cites. Skip
        # synthesis namers so the check stays a real mutual-contradiction graph
        # rather than demanding every page a synthesis cites declare a
        # contradiction with that synthesis.
        if a_path.parent.name == 'syntheses':
            continue
        for b_stem in sorted(a_targets):
            if b_stem not in pages:
                continue
            # Same underlying work: a page naming its own source (or a source
            # naming a page derived from it) in Contradictions cites it as
            # evidence, not as a mutual-contradiction party. No reciprocal owed.
            if (b_stem in page_sources.get(a_stem, set())
                    or a_stem in page_sources.get(b_stem, set())):
                continue
            if a_stem in pages[b_stem][1]:
                continue
            pair = tuple(sorted([a_stem, b_stem]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            b_path = pages[b_stem][0]
            a_rel = str(a_path.relative_to(repo_root))
            b_rel = str(b_path.relative_to(repo_root))
            findings.append(finding(
                check='missing_reciprocal_contradiction',
                file=b_rel,
                message=(
                    f"`{a_rel}`'s Contradictions/Tensions names "
                    f"`[[{b_stem}]]`, but this page's Contradictions/Tensions "
                    f'does not mention `{a_stem}`. One-sided contradictions '
                    f"usually mean the second page hasn't absorbed the "
                    f'disagreement yet.'
                ),
                fix_hint=(
                    f'Add a reciprocal bullet on `{b_rel}` referencing '
                    f'`{a_stem}` (or pointing at a shared concept page where '
                    f'the full disagreement is recorded).'
                ),
            ))
    return findings


# Kebab-case stem: ASCII lowercase letters/digits in hyphen-separated groups.
KEBAB_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

# A wikilink with whitespace adjacent to the pipe. `[^\]\n]` keeps the match
# from crossing a `]]` boundary into the next link AND from spanning a newline
# (a match across lines would let the auto-fix join two body lines); the
# adjacency uses `[^\S\n]` so only non-newline whitespace beside the pipe flags.
PIPE_SPACING_RE = re.compile(
    r'\[\[[^\]\n]*?(?:[^\S\n]\||\|[^\S\n])[^\]\n]*?\]\]')

# A wikilink (not an image embed — negative lookbehind for `!`). Group 1 is the
# raw target+display; the caller splits on `|` and `#`.
BARE_LINK_RE = re.compile(r'(?<!!)\[\[([^\]]+?)\]\]')


def check_filename_convention(wiki_root: Path) -> list[dict[str, Any]]:
    """Concept/entity/synthesis page filenames and attachment leaf filenames are
    kebab-case lowercase (CLAUDE.md -> Page Filenames). Source pages are exempt:
    their stem mirrors the raw stem, which preserves case/punctuation. The
    attachment `{stem}/` directory component is likewise exempt (it mirrors the
    source stem) — only leaf image filenames are checked. Not auto-fixable:
    renaming a page/file is a content/safety operation, not a mechanical edit.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    for folder in ('concepts', 'entities', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            if KEBAB_RE.match(page.stem):
                continue
            findings.append(finding(
                check='filename_not_kebab',
                file=str(page.relative_to(repo_root)),
                message=(f'Filename stem `{page.stem}` is not kebab-case '
                         f'lowercase (ASCII letters, digits, hyphens only).'),
                fix_hint=('Rename to kebab-case (lowercase; spaces/underscores '
                          '-> hyphens). User-owned: renaming a file is a safety '
                          'operation — neither lint nor audit does it '
                          'automatically.'),
            ))
    attach_root = wiki_root / 'attachments'
    if attach_root.exists():
        for f in attach_root.rglob('*'):
            if (not f.is_file() or f.name.startswith('.')
                    or f.suffix.lower().lstrip('.') not in IMAGE_EXTS):
                continue
            if KEBAB_RE.match(f.stem):
                continue
            findings.append(finding(
                check='filename_not_kebab',
                file=str(f.relative_to(repo_root)),
                message=(f'Attachment filename `{f.name}` has a non-kebab-case '
                         f'stem.'),
                fix_hint=('Rename the attachment file to kebab-case lowercase. '
                          'User-owned: renaming is a safety operation, not a '
                          'lint or audit auto-fix.'),
            ))
    return findings


def check_wikilink_pipe_spacing(wiki_root: Path) -> list[dict[str, Any]]:
    """Wikilinks carry no whitespace around the pipe (CLAUDE.md -> Wikilink
    Format): `[[path|display]]`, never `[[path | display]]` — a space after the
    pipe renders as a leading space in the display name. Auto-fixable (collapse
    the padding to a bare `|`). Inline-code spans are blanked first, so a
    documented `[[a | b]]` example inside backticks is not flagged. Operates on
    the whole page text (frontmatter wikilinks too).
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            scan = _mask_code_spans(text=text)
            seen: set[str] = set()
            for m in PIPE_SPACING_RE.finditer(scan):
                tok = text[m.start():m.end()]  # offsets align (length-preserving)
                if tok in seen:
                    continue
                seen.add(tok)
                findings.append(finding(
                    check='wikilink_pipe_spacing',
                    file=str(page.relative_to(repo_root)),
                    message=(f'Wikilink `{tok}` has whitespace around the pipe; '
                             f'use `[[path|display]]` with no padding.'),
                    fix_hint='Remove the space(s) adjacent to the `|`.',
                ))
    return findings


def check_bare_basename_links(wiki_root: Path) -> list[dict[str, Any]]:
    """Page wikilinks must be path-qualified (CLAUDE.md -> Wikilink Format):
    `[[folder/path/file.md|display]]`. A target with no `/` is a bare-basename
    link. Resolution still works (`_link_stem` stays tolerant so the graph
    checks keep resolving), but the schema forbids the bare form vault-wide.
    Not auto-fixable: the correct folder is not always mechanically recoverable.
    Excludes image embeds (`![[...]]`), pure-anchor self-links (`[[#^...]]`),
    and inline-code spans.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            scan = _mask_code_spans(text=text)
            seen: set[str] = set()
            for m in BARE_LINK_RE.finditer(scan):
                target = text[m.start(1):m.end(1)].split('|', 1)[0].strip()
                if not target or target.startswith('#'):
                    continue  # pure-anchor self-link
                base = target.split('#', 1)[0]  # drop anchor before the path test
                if '/' in base or base in seen:
                    continue
                # A real link target is a path stem (letters, digits, `._-`).
                # Literal `[[...]]` in verbatim quoted prose — e.g. an
                # output-format example `[[1, 5, 2, ...]]` — is not a wikilink;
                # commas/spaces/other prose chars mean it never names a page.
                if not re.match(r'^[A-Za-z0-9._-]+$', base):
                    continue
                seen.add(base)
                findings.append(finding(
                    check='bare_basename_link',
                    file=str(page.relative_to(repo_root)),
                    message=(f'Wikilink target `{target}` is a bare basename; '
                             f'schema requires a path-qualified target '
                             f'`[[folder/path/file.md|display]]` (the link still '
                             f'resolves — this is a convention fix, not a broken '
                             f'link).'),
                    fix_hint=('Rewrite the target as its repo-root-relative path '
                              'including the `.md` extension. User-owned: the '
                              'correct folder is not always mechanically '
                              'recoverable, so neither lint nor audit auto-fixes '
                              'it.'),
                ))
    return findings


# Minimum length of a page-display form the unlinked_page_mention check will
# match, to avoid flagging short common words. Every current page title clears
# this; tune up if a short generic title starts producing false positives.
UNLINKED_MENTION_MIN_LEN = 5


def _display_forms_for(stem: str, fm: dict[str, Any]) -> set[str]:
    """Plain-prose forms a page is referred to by: its un-dashed stem plus any
    `aliases:`. Lowercased for case-insensitive matching; forms shorter than
    UNLINKED_MENTION_MIN_LEN are dropped (too common to match safely).
    """
    forms = {stem.replace('-', ' ').strip().lower()}
    aliases = fm.get('aliases')
    if isinstance(aliases, list):
        for a in aliases:
            if isinstance(a, str) and a.strip():
                forms.add(a.strip().lower())
    return {f for f in forms if len(f) >= UNLINKED_MENTION_MIN_LEN}


def check_unlinked_page_mentions(wiki_root: Path) -> list[dict[str, Any]]:
    """Flag an existing page's title/alias appearing as plain text in another
    page's body where it should be a wikilink (CLAUDE.md -> Wikilink Format:
    "Link every genuine reference to a page that exists"). Emits one finding per
    (page, target) with the unlinked-occurrence count; audit/ingest apply the
    judgement of which occurrences are genuine references vs generic wording.
    Code spans, existing `[[wikilinks]]`, and double-quoted spans are masked
    (the quote exception); a page's own stem/aliases are excluded so it is not
    asked to link to itself. An occurrence audit has confirmed generic is
    suppressed via UNLINKED_MENTION_IGNORE, the check's verified-ignore list —
    scoped to the page and anchored to the phrase, so it re-flags if reworded.
    """
    findings: list[dict[str, Any]] = []
    repo_root = wiki_root.parent

    # Index the verified-ignore entries by (page, target), and track which ones
    # actually suppress an occurrence this run. An entry that suppresses nothing
    # is stale (see the stale_mention_ignore pass at the end).
    ignore_by_key: dict[tuple[str, str], list[int]] = {}
    for idx, e in enumerate(UNLINKED_MENTION_IGNORE):
        ignore_by_key.setdefault((e['page'], e['target']), []).append(idx)
    used_entries: set[int] = set()

    form_to_stem: dict[str, str] = {}
    own_forms: dict[str, set[str]] = {}
    page_paths: dict[str, Path] = {}
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            fm, _ = parse_frontmatter(text=page.read_text(encoding='utf-8'))
            forms = _display_forms_for(stem=page.stem, fm=fm or {})
            own_forms[page.stem] = forms
            page_paths[page.stem] = page
            for f in forms:
                # On an alias collision (a separate check), keep the first seen
                # and leave the ambiguous form to that check, not this one.
                form_to_stem.setdefault(f, page.stem)

    if not form_to_stem:
        findings.extend(_stale_mention_ignore_findings(
            used=used_entries, page_paths=page_paths, repo_root=repo_root))
        return findings

    # Longest-first so a multi-word form wins over a contained shorter one
    # ("centralized topology" before "topology"); re.finditer is non-overlapping.
    alt = '|'.join(re.escape(f) for f in sorted(form_to_stem, key=len, reverse=True))
    # `(?!\.\w)` guards a `.`-then-alphanumeric continuation (a version/decimal
    # suffix): a form like `gpt-3` must not match inside `GPT-3.5` / `GPT-3.5-Turbo`
    # (the `.` is neither a word char nor a hyphen, so `(?![\w-])` alone treats it
    # as a boundary and over-matches). A `.` followed by space or end-of-line is a
    # real sentence period ("the model is GPT-3.") and still matches as a genuine
    # reference.
    mention_re = re.compile(r'(?<![\w-])(' + alt + r')(?![\w-])(?!\.\w)', re.IGNORECASE)

    # Scan every page type, source pages included. The CLAUDE.md rule ("link
    # every genuine reference to a page that exists, on every occurrence") applies
    # to source pages too, and its only exemption is a page linking to *itself*
    # (its own file) — handled by `self_forms` below (a page's own stem/aliases).
    # A source page's own topic is a *different* page (the
    # `scaled-dot-product-attention` concept is not the `Vaswani2017AttentionIA`
    # source page), so it is a genuine cross-reference to link,
    # not a self-link: source pages link their own topics like any other.
    # Targets stay all page types (a concept may reference a source bibkey too).
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in folder_path.glob('*.md'):
            text = page.read_text(encoding='utf-8')
            _, end = parse_frontmatter(text=text)
            body = '\n'.join(text.split('\n')[end + 1:])
            scan = _mask_noscan_spans(text=body)  # code + [[...]] spans blanked
            scan = re.sub(r'"[^"\n]*"', lambda m: ' ' * len(m.group(0)), scan)
            # Blank the H1 title line: a markdown heading is never wikilinked, and
            # on a source page the H1 is the paper title, which routinely contains
            # another page's name (a system or concept the paper is about) — not a
            # linkable prose reference. (Callout sections use `> [!type]`, not `#`,
            # so this only removes the one title line.)
            scan = re.sub(r'(?m)^#[ ].*$', lambda m: ' ' * len(m.group(0)), scan)
            self_forms = own_forms.get(page.stem, set())
            rel = str(page.relative_to(repo_root))

            # Spans of the confirmed-generic phrases audit recorded for this page
            # (UNLINKED_MENTION_IGNORE): an occurrence sitting inside one was
            # judged generic wording, not a genuine reference, and is not
            # re-flagged. Matched against the same masked body the mentions are,
            # so a recorded phrase can never reach into a code span or wikilink.
            # Each span carries the index of the entry that recorded it, so an
            # entry that never actually suppresses an occurrence can be reported
            # as stale below.
            ignored_spans: dict[str, list[tuple[int, int, int]]] = {}
            for (ig_page, ig_target), idxs in ignore_by_key.items():
                if ig_page != rel:
                    continue
                spans = ignored_spans.setdefault(ig_target, [])
                for idx in idxs:
                    spans.extend((pm.start(), pm.end(), idx)
                                 for pm in UNLINKED_MENTION_IGNORE[idx]['pattern']
                                 .finditer(scan))

            counts: dict[str, int] = {}
            for m in mention_re.finditer(scan):
                form = m.group(1).lower()
                target = form_to_stem.get(form)
                if target is None or target == page.stem or form in self_forms:
                    continue
                covering = [idx for s, e, idx in ignored_spans.get(target, ())
                            if s <= m.start() and m.end() <= e]
                if covering:
                    used_entries.update(covering)
                    continue
                counts[target] = counts.get(target, 0) + 1
            for target, n in sorted(counts.items()):
                tgt_rel = str(page_paths[target].relative_to(repo_root))
                findings.append(finding(
                    check='unlinked_page_mention',
                    file=rel,
                    message=(f'Existing page `{target}` is mentioned unlinked '
                             f'{n}× in this page but has a wiki page '
                             f'(`{tgt_rel}`); genuine references should be '
                             f'wikilinked.'),
                    fix_hint=(f'Wikilink each genuine reference as '
                              f'`[[{tgt_rel}|{target.replace("-", " ")}]]`; '
                              f'skip generic non-reference usage and quoted text. '
                              f'Record an occurrence confirmed generic in '
                              f'`.claude/skills/multi-skill/unlinked-mention-ignore.md` '
                              f'(`{rel} :: {target} :: <phrase>`) so it is not '
                              f're-flagged.'),
                ))

    findings.extend(_stale_mention_ignore_findings(
        used=used_entries, page_paths=page_paths, repo_root=repo_root))
    return findings


def _stale_mention_ignore_findings(
    used: set[int],
    page_paths: dict[str, Path],
    repo_root: Path,
) -> list[dict[str, Any]]:
    """Report every verified-ignore entry that suppressed nothing this run.

    A stale entry is INERT, not dangerous — the phrase anchor means it can only
    fail to match, never wrongly suppress (check_unlinked_page_mentions) — so this
    is hygiene, not a correctness defect: dead entries otherwise accumulate
    silently as pages are reworded, renamed, or removed, and nothing would ever
    prompt their removal. It is Warning-tier all the same, because in this repo the
    tier says WHO ACTS: Warning is lint's authored worklist that `audit` carries
    out (audit owns this data file), while Info is explicitly not audit's to action
    — an Info-tier stale entry would be a finding no skill is allowed to clean up.
    Warnings never block audit, so the gate is unaffected.
    An entry goes stale three ways, and the message names which: the page it was
    recorded on is gone, the target page is gone, or no unlinked mention of the
    target falls inside the recorded phrase any more (the wording changed, or the
    mention has since been wikilinked — either way the judgement no longer binds).
    """
    findings: list[dict[str, Any]] = []
    ignore_rel = '.claude/skills/multi-skill/unlinked-mention-ignore.md'
    for idx, e in enumerate(UNLINKED_MENTION_IGNORE):
        if idx in used:
            continue
        page, target = e['page'], e['target']
        if not (repo_root / page).exists():
            why = f'the page it was recorded on (`{page}`) no longer exists'
        elif target not in page_paths:
            why = f'its target page `{target}` no longer exists'
        else:
            why = (f'no unlinked mention of `{target}` falls inside the recorded '
                   f'phrase in `{page}` any more (the wording changed, or the '
                   f'mention is now wikilinked)')
        findings.append(finding(
            check='stale_mention_ignore',
            file=ignore_rel,
            message=(f'Verified-ignore entry on line {e["line"]} suppresses '
                     f'nothing: {why}. The entry is inert (a phrase-anchored entry '
                     f'can only fail to match, never wrongly suppress), so this is '
                     f'hygiene, not a defect.'),
            fix_hint=(f'Delete the entry (`{page} :: {target} :: {e["phrase"]}`) '
                      f'from `{ignore_rel}`. If the occurrence still exists but was '
                      f'reworded, re-record it against the current phrase — do not '
                      f'edit the phrase to match without re-confirming the '
                      f'occurrence is still generic wording.'),
        ))
    return findings


# Dated-entry headers in the two reverse-chronological files. The time group is
# optional so an undated (old-format) entry is detected and flagged rather than
# silently skipped. log.md uses an H2 header; hot.md Recent activity uses a bullet.
CHRONO_LOG_RE = re.compile(r'^## \[(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?\]')
CHRONO_HOT_RE = re.compile(r'^- \[(\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))?\]')


def _chronology_findings(rel: str, entries: list[tuple]) -> list[dict[str, Any]]:
    """Shared check for one reverse-chronological section: every entry carries a
    `[YYYY-MM-DD HH:MM]` time, and the timed entries run newest-first (CLAUDE.md →
    Hot, Index, And Log). `entries` is a list of (date, time_or_None, label) in
    file order.
    """
    findings: list[dict[str, Any]] = []
    if not entries:
        return findings
    missing = [e for e in entries if e[1] is None]
    if missing:
        findings.append(finding(
            check='chronology_missing_time',
            file=rel,
            message=(f'{len(missing)} entr{"y" if len(missing) == 1 else "ies"} in '
                     f'{rel} {"lacks" if len(missing) == 1 else "lack"} a '
                     f'`[YYYY-MM-DD HH:MM]` time (first: '
                     f'"{missing[0][2][:60]}"); ordering cannot be verified or '
                     f'auto-sorted until every entry is timed.'),
            fix_hint=('Run `python3 .claude/skills/lint/scripts/sort_chronology.py`: '
                      'it auto-recovers a missing `HH:MM` from the entry\'s linked '
                      'report filename (`…-HHMM`) when determinate, then sorts. An '
                      'entry with no recoverable link needs the 24-hour `HH:MM` '
                      'added by hand (from the report, or git) first.'),
        ))
    timed = [(d, t) for d, t, _ in entries if t is not None]
    if timed and timed != sorted(timed, key=lambda x: (x[0], x[1]), reverse=True):
        findings.append(finding(
            check='chronology_out_of_order',
            file=rel,
            message=(f'{rel} entries are not in descending (date, time) order '
                     f'(newest first); concurrently-merged sessions interleaved.'),
            fix_hint=('Run `python3 .claude/skills/lint/scripts/sort_chronology.py` '
                      'to stable-sort entries by their `[date time]` header '
                      '(only once no `chronology_missing_time` remains).'),
        ))
    return findings


def check_chronology(wiki_root: Path) -> list[dict[str, Any]]:
    """log.md (every entry) and hot.md Recent activity must be timed and ordered
    newest-first (CLAUDE.md → Hot, Index, And Log). The time disambiguates order
    when work from separately-merged branches interleaves in one file.
    """
    findings: list[dict[str, Any]] = []
    log = wiki_root / 'log.md'
    if log.exists():
        entries = []
        for ln in log.read_text(encoding='utf-8').split('\n'):
            m = CHRONO_LOG_RE.match(ln)
            if m:
                entries.append((m.group(1), m.group(2), ln[3:].strip()))
        findings.extend(_chronology_findings(
            rel=str(log.relative_to(wiki_root.parent)), entries=entries))
    hot = wiki_root / 'hot.md'
    if hot.exists():
        entries = []
        in_block = False
        for ln in hot.read_text(encoding='utf-8').split('\n'):
            if ln.strip() == '## Recent activity':
                in_block = True
                continue
            if in_block and ln.startswith('## '):
                break
            if in_block:
                m = CHRONO_HOT_RE.match(ln)
                if m:
                    entries.append((m.group(1), m.group(2), ln[2:].strip()))
        findings.extend(_chronology_findings(
            rel=str(hot.relative_to(wiki_root.parent)), entries=entries))
    return findings


def check_pagination_registration(wiki_root: Path) -> list[dict[str, Any]]:
    """A raw cited somewhere with a `#page=N` deep-link but absent from the
    pagination map. The citation still lints — the locator-completeness checks
    fall back to the `app.`-anchor heuristic, and locator_page_mismatch simply
    cannot run on the raw — so this is an INFO nudge, not a blocker: register the
    raw so its `p. M` locators can be verified. One finding per unregistered raw,
    reported against the raw path.
    """
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in sorted(folder_path.glob('*.md')):
            text = page.read_text(encoding='utf-8')
            for km in CITATION_DEEPLINK_KEY_RE.finditer(text):
                raw_path = km.group(1)
                if raw_path in PAGINATION_MAP or raw_path in seen:
                    continue
                seen.add(raw_path)
                findings.append(finding(
                    check='pagination_map_unregistered',
                    file=raw_path,
                    message=(f'`{raw_path}` is cited with a `#page=N` deep-link '
                             f'but has no section in the pagination map, so its '
                             f'`p. M` locators cannot be verified against what '
                             f'each physical page prints.'),
                    fix_hint=('Propose entries with `python3 '
                              '.claude/skills/multi-skill/scripts/pagination_map.py '
                              f'{raw_path}`, confirm each against a rendered '
                              f'footer, then add the `## {raw_path}` section to '
                              '`.claude/skills/multi-skill/pagination-map.md`.'),
                ))
    return findings


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == '--list-checks':
        print(json.dumps(
            {cid: (sev if sev is not None else 'caller-determined')
             for cid, sev in sorted(CHECKS.items())}, indent=2))
        return 0
    if len(sys.argv) < 2:
        sys.stderr.write('usage: check_wiki.py <wiki-path> | --list-checks\n')
        return 2

    wiki_root = Path(sys.argv[1]).resolve()
    if not wiki_root.exists():
        sys.stderr.write(f"path not found: {wiki_root}\n")
        return 2

    findings: list[dict[str, Any]] = []

    for folder in ('sources', 'entities', 'concepts', 'syntheses'):
        folder_path = wiki_root / folder
        if not folder_path.exists():
            continue
        for page in sorted(folder_path.glob('*.md')):
            findings.extend(check_page(path=page, wiki_root=wiki_root))

    findings.extend(check_index_drift(wiki_root=wiki_root))
    findings.extend(check_chronology(wiki_root=wiki_root))
    findings.extend(check_attachments(wiki_root=wiki_root))
    findings.extend(check_raw_integrity(wiki_root=wiki_root))
    findings.extend(check_orphan_pages(wiki_root=wiki_root))
    findings.extend(check_recursive_citations(wiki_root=wiki_root))
    findings.extend(check_sources_callout_sync(wiki_root=wiki_root))
    findings.extend(check_source_link_resolution(wiki_root=wiki_root))
    findings.extend(check_concept_source_bidirectional(wiki_root=wiki_root))
    findings.extend(check_needs_update_reason(wiki_root=wiki_root))
    findings.extend(check_alias_collisions(wiki_root=wiki_root))
    findings.extend(check_duplicate_concepts(wiki_root=wiki_root))
    findings.extend(check_reciprocal_contradictions(wiki_root=wiki_root))
    findings.extend(check_filename_convention(wiki_root=wiki_root))
    findings.extend(check_wikilink_pipe_spacing(wiki_root=wiki_root))
    findings.extend(check_bare_basename_links(wiki_root=wiki_root))
    findings.extend(check_unlinked_page_mentions(wiki_root=wiki_root))
    findings.extend(check_pagination_registration(wiki_root=wiki_root))

    print(json.dumps(findings, indent=2))
    # Exit non-zero only on blocking errors so CI / hooks can gate. Standing
    # repo-state findings (STANDING_NONBLOCKING) are expected, ongoing states,
    # not failures, so they do not flip the exit code — matching the
    # audit-blocking gate's carve-out.
    return 1 if any(
        f['severity'] == 'error' and f['check_id'] not in STANDING_NONBLOCKING
        for f in findings
    ) else 0


if __name__ == '__main__':
    sys.exit(main())
