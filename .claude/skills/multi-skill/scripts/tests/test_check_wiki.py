"""Tests for check_wiki.py — the CHECKS registry plus many individual checks
(embed isolation, both hyphenation checks and their data-file loader, source-locator
completeness, the verified-anchor diff-guard, wikilink-display caps, and chronology),
with the citation_bracket_style check and its auto-fix transform detailed below.

citation_bracket_style flags the superseded square-bracket Form 2 citation
(`[[[key]]; [[loc]]]`) on concept/entity/synthesis pages; CLAUDE.md ->
Source Support And Verification mandates the round-bracket form
(`([[key]]; [[loc]])`). The check is detection-only (the script prints
findings; the lint skill applies fixes), so these tests pin (a) what the check
detects and refuses to flag, and (b) that the documented auto-fix transform
`SQUARE_CITATION_RE.sub(r'(\\1)', body)` produces the canonical form, is
idempotent, and round-trips to a clean re-scan.

Run from anywhere:

    python3 -m unittest discover -s .claude/skills/multi-skill/scripts/tests

The module is loaded by path so the tests do not depend on cwd or packaging.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve()
SCRIPT = HERE.parents[1] / 'check_wiki.py'              # scripts/check_wiki.py
REPO = HERE.parents[5]                                  # repo root
WIKI = REPO / '1-wiki'

spec = importlib.util.spec_from_file_location('check_wiki', SCRIPT)
cw = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(cw)

BODY_HASH = HERE.parents[1] / 'body_hash.py'           # scripts/body_hash.py
bh_spec = importlib.util.spec_from_file_location('body_hash', BODY_HASH)
bh = importlib.util.module_from_spec(bh_spec)
assert bh_spec and bh_spec.loader
bh_spec.loader.exec_module(bh)


# --- builders ----------------------------------------------------------------

SRC = '[[1-wiki/sources/X.md|X]]'
LOC1 = '[[0-raw/papers/X.pdf#page=1|sec. 1, p. 1]]'
LOC2 = '[[0-raw/papers/X.pdf#page=2|fig. 1, p. 2]]'


def square(*locs):
    """The superseded square-bracket Form 2: outer literal [ ] wrap."""
    return '[' + SRC + ''.join('; ' + l for l in locs) + ']'


def roundc(*locs):
    """The canonical round-bracket Form 2."""
    return '(' + SRC + ''.join('; ' + l for l in locs) + ')'


def fix(body: str) -> str:
    """The documented auto-fix transform (mirrors the SKILL.md / fix_hint)."""
    return cw.SQUARE_CITATION_RE.sub(r'(\1)', body)


def bracket_findings(body: str, end: int = 0):
    return cw.check_citation_bracket_style(body=body, rel='1-wiki/concepts/x.md', end=end)


def lineno(find):
    """Pull the reported line number as an int. The check's message wording may
    drift; only the `line <N>` contract is asserted on, never the surrounding
    phrasing (this is a semantic/behavioural check, not a string match)."""
    m = re.search(r'line (\d+)', find['message'])
    assert m, f'finding has no line number: {find["message"]!r}'
    return int(m.group(1))


def _write_page(tmp_path, folder, name, frontmatter, body):
    d = tmp_path / '1-wiki' / folder
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(f'---\n{frontmatter}\n---\n\n{body}\n', encoding='utf-8')
    return p


CONCEPT_FM = ('type: concept\naliases: []\nsources:\n'
              '  - "[[1-wiki/sources/X.md|X]]"\nsource_count: 1\n'
              'tags: []\ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: draft')


_SRC_FM = ('type: paper\ntitle: "Adapters"\nauthors: []\nyear: 2019\n'
           'file: "[[0-raw/papers/Houlsby2019.pdf]]"\nattachments: []\ntags: []\n'
           'frames: []\ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: draft')
_CON_FM = ('type: concept\naliases: []\nsources:\n'
           '  - "[[1-wiki/sources/Houlsby2019.md|Houlsby2019]]"\nsource_count: 1\n'
           'tags: []\ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: draft')


EMB = '![[1-wiki/attachments/X/fig.png]]'


def embed_findings(body: str, end: int = 0):
    return cw.check_embed_isolated(body=body, rel='1-wiki/concepts/x.md', end=end)


def fix_embeds(body: str) -> str:
    """The documented auto-fix: insert a blank `>` line above and below each
    standalone embed line on whichever side is missing (mirrors the fix_hint)."""
    lines = body.split('\n')
    out: list[str] = []
    n = len(lines)
    for i, line in enumerate(lines):
        if cw.QUOTED_EMBED_LINE_RE.match(line):
            if not (out and cw.QUOTED_BLANK_RE.match(out[-1])):
                out.append('>')
            out.append(line)
            nxt = lines[i + 1] if i + 1 < n else None
            if nxt is None or not cw.QUOTED_BLANK_RE.match(nxt):
                out.append('>')
        else:
            out.append(line)
    return '\n'.join(out)


def fix_pipes(body: str) -> str:
    """The documented wikilink_pipe_spacing auto-fix: within each PIPE_SPACING_RE
    match, collapse the pipe-and-padding to a bare `|` (mirrors SKILL.md / the
    fix_hint). Only padding adjacent to the `|` inside the matched wikilink span is
    removed; a `|` outside `[[...]]` (a table cell) is never touched. This transform
    is on the verification-neutral re-stamp allowlist, so it is pinned here."""
    return cw.PIPE_SPACING_RE.sub(
        lambda m: re.sub(r'[^\S\n]*\|[^\S\n]*', '|', m.group(0)), body)


SOURCE_FM = ('type: paper\ntitle: "X"\nauthors: []\nyear: 2020\n'
             'file: "[[0-raw/papers/X.pdf]]"\nattachments: []\ntags: []\n'
             'frames: []\ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: draft')


def hyphen_findings(tmp_path, folder, name, fm, body):
    p = _write_page(tmp_path, folder, name, fm, body)
    wiki = tmp_path / '1-wiki'
    return [f for f in cw.check_page(path=p, wiki_root=wiki)
            if f['check_id'] == 'hyphenated_open_compound']


LOC_BOTH = '[[0-raw/papers/X.pdf#page=1|sec. 1, p. 1]]'      # anchor+page inside: OK
LOC_SPLIT = 'sec. 1, [[0-raw/papers/X.pdf#page=1|p. 1]]'     # anchor outside: drift
LOC_PAGE_ONLY = '[[0-raw/papers/X.pdf#page=1|p. 1]]'         # page only: drift
LOC_ANCHOR_ONLY = '[[0-raw/papers/X.pdf#page=1|sec. 1]]'     # anchor only: drift


def loc_findings(body: str, end: int = 0):
    return cw.check_source_locator_complete(body=body, rel='1-wiki/sources/X.md', end=end)


DG = '0-raw/papers/X.pdf'


def dg(cur, head, status='verified', head_status='verified'):
    return cw.anchor_change_findings(cur_text=cur, head_text=head,
                                     rel='1-wiki/sources/X.md', status=status,
                                     head_status=head_status)


def caps_findings(body: str, end: int = 0):
    return cw.check_wikilink_display_caps(body=body, rel='1-wiki/concepts/x.md', end=end)


SORT_SCRIPT = HERE.parents[5] / '.claude' / 'skills' / 'lint' / 'scripts' / 'sort_chronology.py'
_ss = importlib.util.spec_from_file_location('sort_chronology', SORT_SCRIPT)
sc = importlib.util.module_from_spec(_ss)
_ss.loader.exec_module(sc)


def _wiki(tmp_path, log=None, hot=None):
    d = tmp_path / '1-wiki'
    d.mkdir(parents=True, exist_ok=True)
    if log is not None:
        (d / 'log.md').write_text(log, encoding='utf-8')
    if hot is not None:
        (d / 'hot.md').write_text(hot, encoding='utf-8')
    return d


LOG_OK = ('# Log\n\nReverse-chronological event log. Newest entry on top.\n\n'
          '## [2026-06-08 18:00] audit | newer\n- a\n\n'
          '## [2026-06-08 09:00] fix | older\n- b\n')
LOG_DISORDER = ('# Log\n\nx\n\n'
                '## [2026-06-08 09:00] fix | older first (wrong)\n- a\n\n'
                '## [2026-06-08 18:00] audit | newer second (wrong)\n- b\n')
LOG_UNTIMED = ('# Log\n\nx\n\n'
               '## [2026-06-08 18:00] audit | timed\n- a\n\n'
               '## [2026-06-07] lint | no time\n- b\n')
HOT_OK = ('---\ntype: hot\n---\n\n# Hot\n\n## Recent activity\n\n'
          '- [2026-06-08 20:00] b | newer\n- [2026-06-08 08:00] a | older\n\n'
          '## Open threads\n\n- keep me\n')
HOT_DISORDER = ('---\ntype: hot\n---\n\n# Hot\n\n## Recent activity\n\n'
                '- [2026-06-08 08:00] a | older first (wrong)\n'
                '- [2026-06-08 20:00] b | newer second (wrong)\n\n'
                '## Open threads\n\n- keep me\n')
# Untimed entries whose time is recoverable from a linked report filename
# (`…-YYYY-MM-DD-HHMM-…`, matching date) — the determinate auto-recovery case.
LOG_UNTIMED_RECOVERABLE = (
    '# Log\n\nx\n\n'
    '## [2026-06-08 18:00] audit | timed\n- a\n\n'
    '## [2026-06-07] query | recoverable\n'
    '- Saved: [[2-outputs/query/query-2026-06-07-0915-topic.md|query]]\n')
HOT_UNTIMED_RECOVERABLE = (
    '---\ntype: hot\n---\n\n# Hot\n\n## Recent activity\n\n'
    '- [2026-06-08 20:00] b | newer\n'
    '- [2026-06-07] query | recoverable '
    '([[2-outputs/query/query-2026-06-07-0915-topic.md|query]])\n\n'
    '## Open threads\n\n- keep me\n')
# Non-entry lines inside Recent activity — a parked note before the first dated
# bullet, a sub-bullet under an entry — must survive the sort (sort_hot data-loss
# regression guard: the block must never be rebuilt from dated bullets alone).
HOT_WITH_STRAY = ('---\ntype: hot\n---\n\n# Hot\n\n## Recent activity\n\n'
                  'a parked note the user left here\n'
                  '- [2026-06-08 08:00] a | older first (wrong)\n'
                  '- [2026-06-08 20:00] b | newer second (wrong)\n'
                  '    - nested detail under b\n\n'
                  '## Open threads\n\n- keep me\n')


def _noun_findings(tmp_path, body):
    p = _write_page(tmp_path, 'concepts', 'c.md', CONCEPT_FM, body)
    return [f for f in cw.check_page(path=p, wiki_root=tmp_path / '1-wiki')
            if f['check_id'] == 'hyphenated_open_compound_noun']


class TestCheckWiki(unittest.TestCase):
    """CHECKS registry + individual check behaviour for check_wiki.py (one cohesive suite per script)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    # --- wiring invariants -------------------------------------------------------

    def test_check_is_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('citation_bracket_style') == 'warning'

    def test_finding_builder_accepts_the_new_id(self) -> None:
        # finding() raises on an unregistered check_id; this confirms registration.
        f = cw.finding(check='citation_bracket_style', file='x.md', message='m')
        assert f['check_id'] == 'citation_bracket_style'
        assert f['severity'] == 'warning'

    def test_list_checks_cli_exposes_it(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        listed = json.loads(r.stdout)
        assert listed.get('citation_bracket_style') == 'warning'

    # --- detection: positive cases ----------------------------------------------

    def test_basic_square_citation_is_flagged(self) -> None:
        f = bracket_findings(f'> - claim {square(LOC1)}.')
        assert len(f) == 1
        assert f[0]['check_id'] == 'citation_bracket_style'
        assert f[0]['severity'] == 'warning'

    def test_multi_locator_square_is_one_finding(self) -> None:
        f = bracket_findings(f'> - claim {square(LOC1, LOC2)}.')
        assert len(f) == 1

    def test_square_with_hyphen_and_digit_stems(self) -> None:
        body = ('> - a [the [[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]; '
                '[[0-raw/papers/Vaswani2017AttentionIA.pdf#page=1|sec. 1, p. 1]]] b\n'
                '> - c [[[1-wiki/sources/illustrated-transformer.md|illustrated-transformer]]; '
                '[[0-raw/articles/illustrated-transformer.md#page=1|sec. A, p. 1]]] d')
        # both lines carry a square citation
        assert len(bracket_findings(body)) == 2

    def test_two_squares_on_separate_lines_get_increasing_line_numbers(self) -> None:
        body = f'> - first {square(LOC1)}.\n> - second {square(LOC2)}.'
        f = bracket_findings(body)
        assert len(f) == 2
        assert lineno(f[1]) > lineno(f[0])

    def test_line_number_shifts_by_the_frontmatter_offset(self) -> None:
        body = f'\n\n> - claim {square(LOC1)}.'
        f0 = bracket_findings(body, end=0)
        f10 = bracket_findings(body, end=10)
        # the end (frontmatter close) offset shifts the reported line by its delta
        assert lineno(f10[0]) - lineno(f0[0]) == 10

    def test_square_mid_sentence_is_flagged(self) -> None:
        f = bracket_findings(f'> - text before {square(LOC1)} text after.')
        assert len(f) == 1

    # --- detection: negative cases (no false positives) -------------------------

    def test_round_form_not_flagged(self) -> None:
        assert bracket_findings(f'> - claim {roundc(LOC1)}.') == []

    def test_round_multi_locator_not_flagged(self) -> None:
        assert bracket_findings(f'> - claim {roundc(LOC1, LOC2)}.') == []

    def test_form1_attributive_not_flagged(self) -> None:
        body = f'> - {SRC} ({LOC1}) shows the thing.'
        assert bracket_findings(body) == []

    def test_plain_wikilink_not_flagged(self) -> None:
        assert bracket_findings('> - see [[1-wiki/concepts/y.md|y]] for detail.') == []

    def test_bare_source_link_not_flagged(self) -> None:
        # a source link with no deep-link is a different (citation_unpaired-ish) issue,
        # not the square-bracket form.
        assert bracket_findings(f'> - claim {SRC}.') == []

    def test_square_inside_inline_code_is_masked(self) -> None:
        body = f'> - example: `{square(LOC1)}` is the old form.'
        assert bracket_findings(body) == []

    def test_square_inside_sources_callout_is_masked(self) -> None:
        body = ('> [!sources] Sources\n'
                f'> - {square(LOC1)}\n'
                '> ^sources')
        assert bracket_findings(body) == []

    def test_square_inside_double_quote_is_masked(self) -> None:
        # A `[[[…]]]`-shaped literal inside a verbatim quote is an example, not a
        # citation; the auto-fix is on the re-stamp allowlist, so it must never
        # rewrite (and re-stamp) a quoted span. Mirrors the code/Sources masking.
        body = f'> - the old style read "{square(LOC1)}" before the fix.'
        assert bracket_findings(body) == []

    # --- fix transform -----------------------------------------------------------

    def test_fix_basic_square_to_round_exact(self) -> None:
        assert fix(square(LOC1)) == roundc(LOC1)

    def test_fix_multi_locator_to_round_exact(self) -> None:
        assert fix(square(LOC1, LOC2)) == roundc(LOC1, LOC2)

    def test_fix_is_idempotent_on_round_form(self) -> None:
        assert fix(roundc(LOC1)) == roundc(LOC1)
        assert fix(roundc(LOC1, LOC2)) == roundc(LOC1, LOC2)

    def test_fix_leaves_inner_wikilinks_byte_identical(self) -> None:
        before = square(LOC1, LOC2)
        after = fix(before)
        # every inner [[...]] wikilink survives unchanged; only the wrap changed
        assert SRC in after and LOC1 in after and LOC2 in after
        assert after.count('[[') == before.count('[[')
        assert after.count(']]') == before.count(']]')
        assert after.startswith('(') and after.endswith(')')

    def test_fix_then_rescan_is_clean_roundtrip(self) -> None:
        body = f'> - claim {square(LOC1, LOC2)}.'
        assert bracket_findings(body)                  # dirty before
        assert bracket_findings(fix(body)) == []       # clean after

    def test_fix_only_touches_square_citations_in_mixed_body(self) -> None:
        body = (f'> - good {roundc(LOC1)}.\n'
                f'> - bad {square(LOC2)}.\n'
                f'> - attributive {SRC} ({LOC1}) shows.')
        fixed = fix(body)
        assert bracket_findings(fixed) == []
        # the already-round and Form-1 lines are untouched
        assert f'good {roundc(LOC1)}.' in fixed
        assert f'attributive {SRC} ({LOC1}) shows.' in fixed

    # --- integration via check_page ---------------------------------------------

    def test_check_page_flags_square_on_concept(self) -> None:
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        f'> [!idea] Idea\n> - claim {square(LOC1)}.\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'citation_bracket_style' in ids

    def test_check_page_does_not_flag_round_on_concept(self) -> None:
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        f'> [!idea] Idea\n> - claim {roundc(LOC1)}.\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'citation_bracket_style' not in ids

    def test_check_page_exempts_source_pages(self) -> None:
        # Source pages use a different citation form and are out of scope for the
        # concept/entity/synthesis citation checks (detect_page_kind -> 'paper').
        src_fm = ('type: paper\ntitle: "X"\nauthors: []\nyear: 2020\n'
                  'file: "[[0-raw/papers/X.pdf]]"\nattachments: []\ntags: []\n'
                  'frames: []\ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: draft')
        p = _write_page(self.tmp, 'sources', 'X.md', src_fm,
                        f'> [!tldr] TL;DR\n> - claim {square(LOC1)}.\n> ^tldr')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'citation_bracket_style' not in ids

    # --- unlinked_page_mention scans source pages, own topic included -----------

    def test_unlinked_mention_scans_source_pages_including_own_topic(self) -> None:
        # A source page that names a concept in prose — even its own topic — must be
        # flagged: the concept page is a different file, so it is a genuine
        # cross-reference to link, not a self-link (CLAUDE.md -> Wikilink Format).
        _write_page(self.tmp, 'sources', 'Houlsby2019.md', _SRC_FM,
                    '> [!tldr] TL;DR\n> - Adapter tuning inserts small modules into a '
                    'frozen model.\n> ^tldr')
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert any(f['check_id'] == 'unlinked_page_mention'
                   and 'sources/Houlsby2019.md' in f['file']
                   and 'adapter-tuning' in f['message'] for f in finds)

    def test_unlinked_mention_source_page_not_flagged_for_own_stem(self) -> None:
        # The only exemption is a page linking to itself: a source page is never
        # flagged for a plain-text mention of its own stem/alias.
        _write_page(self.tmp, 'sources', 'adapter-survey.md',
                    _SRC_FM.replace('"[[0-raw/papers/Houlsby2019.pdf]]"',
                                    '"[[0-raw/papers/adapter-survey.pdf]]"'),
                    '> [!tldr] TL;DR\n> - This adapter survey reviews adapter survey '
                    'methods.\n> ^tldr')
        finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert not any(f['check_id'] == 'unlinked_page_mention'
                       and 'adapter-survey' in f['message'] for f in finds)

    def test_unlinked_mention_skips_h1_title_line(self) -> None:
        # A concept name appearing only in the source page's H1 paper title is not a
        # linkable reference (you never wikilink an H1) — must not be flagged.
        _write_page(self.tmp, 'sources', 'AdapterPaper.md',
                    _SRC_FM.replace('"X"', '"Adapter tuning for NLP"')
                           .replace('"[[0-raw/papers/Houlsby2019.pdf]]"',
                                    '"[[0-raw/papers/AdapterPaper.pdf]]"'),
                    '# Adapter tuning for NLP\n\n> [!tldr] TL;DR\n> - A frozen-backbone '
                    'method.\n> ^tldr')
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert not any(f['check_id'] == 'unlinked_page_mention'
                       and 'AdapterPaper' in f['file'] for f in finds)

    def test_unlinked_mention_still_flags_prose_when_title_also_matches(self) -> None:
        # The H1 skip removes only the title line: a genuine prose mention elsewhere
        # is still flagged.
        _write_page(self.tmp, 'sources', 'AdapterPaper2.md',
                    _SRC_FM.replace('"X"', '"Adapter tuning for NLP"')
                           .replace('"[[0-raw/papers/Houlsby2019.pdf]]"',
                                    '"[[0-raw/papers/AdapterPaper2.pdf]]"'),
                    '# Adapter tuning for NLP\n\n> [!tldr] TL;DR\n> - Adapter tuning '
                    'inserts small modules.\n> ^tldr')
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert any(f['check_id'] == 'unlinked_page_mention'
                   and 'AdapterPaper2' in f['file']
                   and 'adapter-tuning' in f['message'] for f in finds)

    def test_unlinked_mention_skips_version_continuation_but_keeps_bare(self) -> None:
        # A page-name form like the `GPT-3` alias must NOT match inside a version
        # suffix (`GPT-3.5`): the `.`-then-alphanumeric continuation is a different
        # model, not a reference to this page. A bare `GPT-3` mention still flags.
        gpt3_fm = ('type: entity\naliases:\n  - GPT-3\nsources:\n'
                   '  - "[[1-wiki/sources/Houlsby2019.md|Houlsby2019]]"\n'
                   'source_count: 1\ntags: []\ncreated: 2026-01-01\n'
                   'updated: 2026-01-01\nstatus: draft')
        _write_page(self.tmp, 'entities', 'gpt-3.md', gpt3_fm,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host-version.md', _CON_FM,
                    '> [!idea] Idea\n> - Built on GPT-3.5 and GPT-3.5-Turbo only.\n'
                    '> ^idea')
        _write_page(self.tmp, 'concepts', 'host-bare.md', _CON_FM,
                    '> [!idea] Idea\n> - Built on the GPT-3 model directly.\n> ^idea')
        finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        # No gpt-3 finding from the version-only page.
        assert not any(f['check_id'] == 'unlinked_page_mention'
                       and 'host-version' in f['file']
                       and 'gpt-3' in f['message'] for f in finds)
        # Bare GPT-3 reference still flags.
        assert any(f['check_id'] == 'unlinked_page_mention'
                   and 'host-bare' in f['file']
                   and 'gpt-3' in f['message'] for f in finds)

    # --- unlinked_page_mention verified-ignore list ------------------------------
    # Genuine-vs-generic is a judgement (CLAUDE.md -> Wikilink Format). audit makes
    # it per occurrence and records a confirmed-generic one in
    # .claude/skills/multi-skill/unlinked-mention-ignore.md so it is not re-litigated. An
    # entry is page-scoped (never suppresses elsewhere) and phrase-anchored (a
    # reword re-flags it — the safe fallback).

    def _ignore(self, *entries: str) -> list[dict[str, object]]:
        f = self.tmp / 'ignore.md'
        f.write_text('# x\n\n## verified-ignore\n'
                     + ''.join(f'- {e}\n' for e in entries), encoding='utf-8')
        return cw._load_unlinked_mention_ignore(f)

    def test_unlinked_mention_verified_ignore_suppresses_generic_occurrence(self) -> None:
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host.md', _CON_FM,
                    '> [!idea] Idea\n> - Loosely, any adapter tuning story counts.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert not any(f['check_id'] == 'unlinked_page_mention'
                       and 'host.md' in f['file'] for f in finds)

    def test_unlinked_mention_verified_ignore_leaves_other_occurrences(self) -> None:
        # An entry suppresses ONE occurrence context, not the whole page: a second,
        # genuine mention of the same target still flags.
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host2.md', _CON_FM,
                    '> [!idea] Idea\n> - Loosely, any adapter tuning story counts.\n'
                    '> - Adapter tuning inserts small modules into a frozen model.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host2.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        hits = [f for f in finds if f['check_id'] == 'unlinked_page_mention'
                and 'host2.md' in f['file']]
        assert len(hits) == 1
        assert '1×' in hits[0]['message']  # the generic one is gone, the genuine one stays

    def test_unlinked_mention_verified_ignore_is_page_scoped(self) -> None:
        # The same wording on a DIFFERENT page is judged again — an entry recorded
        # for one page never silently suppresses a genuine reference on another.
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'other.md', _CON_FM,
                    '> [!idea] Idea\n> - Loosely, any adapter tuning story counts.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert any(f['check_id'] == 'unlinked_page_mention'
                   and 'other.md' in f['file'] for f in finds)

    def test_unlinked_mention_verified_ignore_reflags_when_phrase_reworded(self) -> None:
        # Self-invalidating: the page's wording changed, so the entry no longer
        # matches and the mention flags again rather than riding on a stale judgement.
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host3.md', _CON_FM,
                    '> [!idea] Idea\n> - Concretely, this adapter tuning result holds.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host3.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert any(f['check_id'] == 'unlinked_page_mention'
                   and 'host3.md' in f['file'] for f in finds)

    def test_unlinked_mention_ignore_loader_parses_and_skips_malformed(self) -> None:
        ign = self._ignore('1-wiki/concepts/host.md :: adapter-tuning :: a b c',
                           'missing the target field',
                           '1-wiki/concepts/host.md ::  :: empty target')
        assert [(e['page'], e['target'], e['phrase']) for e in ign] == [
            ('1-wiki/concepts/host.md', 'adapter-tuning', 'a b c')]
        assert ign[0]['line'] == 4  # reported at its own line in the data file

    def test_unlinked_mention_ignore_loader_missing_file_is_empty_not_fatal(self) -> None:
        # A missing file leaves the check fully unsuppressed — the safe direction.
        assert cw._load_unlinked_mention_ignore(self.tmp / 'nope.md') == []

    def test_unlinked_mention_ignore_real_data_file_loads(self) -> None:
        # The shipped data file parses (it ships empty — only the example comment).
        assert cw._load_unlinked_mention_ignore() == []

    # --- stale_mention_ignore: an entry that suppresses nothing ------------------
    # A stale entry is inert (phrase-anchored: it can only fail to match), so this
    # is hygiene, not a correctness defect — but Warning-tier, because the tier says
    # who acts: Warning is audit's authored worklist (audit owns the data file) and
    # Info is explicitly not audit's to action. Without it, dead entries accumulate
    # silently as pages are reworded, renamed, or removed.

    def test_stale_mention_ignore_severity_registered(self) -> None:
        # Warning, not Info: audit owns the file, and Info findings are not audit's
        # to action — an Info-tier stale entry would be a finding nobody may clean up.
        assert cw.CHECKS.get('stale_mention_ignore') == 'warning'

    def test_stale_mention_ignore_flags_reworded_phrase(self) -> None:
        # The page still mentions the target, but not inside the recorded phrase:
        # the judgement no longer binds, so the entry is reported as dead.
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host4.md', _CON_FM,
                    '> [!idea] Idea\n> - Concretely, this adapter tuning result holds.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host4.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        stale = [f for f in finds if f['check_id'] == 'stale_mention_ignore']
        assert len(stale) == 1
        assert 'falls inside the recorded phrase' in stale[0]['message']

    def test_stale_mention_ignore_flags_missing_host_page(self) -> None:
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        ign = self._ignore('1-wiki/concepts/gone.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        stale = [f for f in finds if f['check_id'] == 'stale_mention_ignore']
        assert len(stale) == 1
        assert 'no longer exists' in stale[0]['message']

    def test_stale_mention_ignore_flags_missing_target_page(self) -> None:
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host5.md', _CON_FM,
                    '> [!idea] Idea\n> - Loosely, any adapter tuning story counts.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host5.md :: dropped-concept :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        stale = [f for f in finds if f['check_id'] == 'stale_mention_ignore']
        assert len(stale) == 1
        assert 'dropped-concept' in stale[0]['message']

    def test_stale_mention_ignore_silent_when_entry_still_suppresses(self) -> None:
        # A live entry — one doing real work — is never reported as stale.
        _write_page(self.tmp, 'concepts', 'adapter-tuning.md', _CON_FM,
                    '> [!idea] Idea\n> - x.\n> ^idea')
        _write_page(self.tmp, 'concepts', 'host6.md', _CON_FM,
                    '> [!idea] Idea\n> - Loosely, any adapter tuning story counts.\n'
                    '> ^idea')
        ign = self._ignore('1-wiki/concepts/host6.md :: adapter-tuning :: '
                           'any adapter tuning story')
        with mock.patch.object(cw, 'UNLINKED_MENTION_IGNORE', ign):
            finds = cw.check_unlinked_page_mentions(wiki_root=self.tmp / '1-wiki')
        assert not any(f['check_id'] == 'stale_mention_ignore' for f in finds)

    # --- callout block IDs (kebab-case of the callout title) ---------------------

    def test_expected_block_id_identity_for_matching_types(self) -> None:
        # Most callouts: block ID == type slug.
        assert cw.expected_block_id('idea') == 'idea'
        assert cw.expected_block_id('open-questions') == 'open-questions'
        assert cw.expected_block_id('tldr') == 'tldr'

    def test_expected_block_id_overrides_abbreviated_types(self) -> None:
        assert cw.expected_block_id('why') == 'why-it-matters'
        assert cw.expected_block_id('disconfirming') == 'disconfirming-evidence'
        assert (cw.expected_block_id('what-would-change-this')
                == 'what-would-change-this-answer')

    def test_correct_overridden_block_id_not_flagged(self) -> None:
        body = ('> [!idea] Idea\n> - x.\n> ^idea\n\n'
                '> [!why] Why It Matters\n> - x.\n> ^why-it-matters')
        ids = {f['check_id'] for f in cw.check_callout_block_ids(body=body, rel='c.md')}
        assert 'callout_block_id' not in ids

    def test_old_unexpanded_block_id_is_flagged(self) -> None:
        # `^why` on a `[!why]` callout is now wrong; expected `^why-it-matters`.
        body = '> [!why] Why It Matters\n> - x.\n> ^why'
        finds = cw.check_callout_block_ids(body=body, rel='c.md')
        assert [f['check_id'] for f in finds] == ['callout_block_id']
        assert 'why-it-matters' in finds[0]['fix_hint']

    # --- real-repo anchors -------------------------------------------------------

    def test_real_wiki_has_no_square_citations(self) -> None:
        findings = []
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            fp = WIKI / folder
            if not fp.exists():
                continue
            for page in sorted(fp.glob('*.md')):
                findings.extend(f for f in cw.check_page(path=page, wiki_root=WIKI)
                                if f['check_id'] == 'citation_bracket_style')
        assert findings == [], findings

    def test_full_run_output_is_deterministic(self) -> None:
        r1 = subprocess.run([sys.executable, str(SCRIPT), str(WIKI)],
                            capture_output=True, text=True)
        r2 = subprocess.run([sys.executable, str(SCRIPT), str(WIKI)],
                            capture_output=True, text=True)
        assert r1.stdout == r2.stdout
        # well-formed JSON, and no square-citation findings in the committed wiki
        data = json.loads(r1.stdout)
        assert not [f for f in data if f['check_id'] == 'citation_bracket_style']

    # --- embed isolation (embed_not_isolated) -----------------------------------
    #
    # CLAUDE.md -> Attachments / Source Pages: an image embed inside a callout must
    # sit in its own block — a blank quoted line (`>`) directly above AND below the
    # embed line — or Obsidian lazy-continues it into the adjacent bullet/line and
    # mis-renders. The check is detection-only (the script reports; the lint skill
    # applies the insertion), so these tests pin what is flagged, what is left alone,
    # and that the documented insertion produces a clean re-scan.

    # wiring invariants

    def test_embed_isolated_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('embed_not_isolated') == 'warning'

    def test_embed_finding_builder_accepts_the_id(self) -> None:
        f = cw.finding(check='embed_not_isolated', file='x.md', message='m')
        assert f['check_id'] == 'embed_not_isolated'
        assert f['severity'] == 'warning'

    def test_list_checks_cli_exposes_embed_not_isolated(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        assert json.loads(r.stdout).get('embed_not_isolated') == 'warning'

    # detection: positive cases

    def test_embed_with_no_blank_lines_flagged_both_sides(self) -> None:
        f = embed_findings(f'> [!idea] Idea\n> - claim.\n> {EMB}\n> ^idea')
        assert len(f) == 1
        assert f[0]['check_id'] == 'embed_not_isolated'
        assert 'above and below' in f[0]['message']

    def test_embed_missing_blank_below_only(self) -> None:
        f = embed_findings(f'> [!idea] Idea\n> - claim.\n>\n> {EMB}\n> ^idea')
        assert len(f) == 1
        assert 'below' in f[0]['message'] and 'above and below' not in f[0]['message']

    def test_embed_missing_blank_above_only(self) -> None:
        f = embed_findings(f'> [!idea] Idea\n> - claim.\n> {EMB}\n>\n> ^idea')
        assert len(f) == 1
        assert 'above' in f[0]['message'] and 'above and below' not in f[0]['message']

    def test_two_unisolated_embeds_get_increasing_line_numbers(self) -> None:
        body = (f'> [!evidence] Evidence\n> - a.\n> {EMB}\n> - b.\n> {EMB}\n'
                f'> ^evidence')
        f = embed_findings(body)
        assert len(f) == 2
        assert lineno(f[1]) > lineno(f[0])

    def test_embed_line_number_shifts_by_frontmatter_offset(self) -> None:
        body = f'> [!idea] Idea\n> - claim.\n> {EMB}\n> ^idea'
        assert lineno(embed_findings(body, end=10)[0]) - lineno(embed_findings(body, end=0)[0]) == 10

    # detection: negative cases

    def test_isolated_embed_not_flagged(self) -> None:
        body = f'> [!idea] Idea\n> - claim.\n>\n> {EMB}\n>\n> ^idea'
        assert embed_findings(body) == []

    def test_trailing_space_blank_lines_tolerated(self) -> None:
        # The blank quoted line may carry a trailing space (`> `) as well as bare `>`.
        body = f'> [!idea] Idea\n> - claim.\n> \n> {EMB}\n> \n> ^idea'
        assert embed_findings(body) == []

    def test_embed_mixed_with_prose_on_line_not_flagged(self) -> None:
        # An embed sharing its line with other content is not a standalone embed line.
        assert embed_findings(f'> [!idea] Idea\n> - see {EMB} here.\n> ^idea') == []

    # auto-fix round-trip

    def test_fix_isolates_embed_and_rescans_clean(self) -> None:
        body = f'> [!idea] Idea\n> - claim.\n> {EMB}\n> ^idea'
        fixed = fix_embeds(body)
        assert embed_findings(fixed) == []
        assert f'> - claim.\n>\n> {EMB}\n>\n> ^idea' in fixed

    def test_fix_is_idempotent_on_isolated_embed(self) -> None:
        body = f'> [!idea] Idea\n> - claim.\n>\n> {EMB}\n>\n> ^idea'
        assert fix_embeds(body) == body

    # integration via check_page

    def test_check_page_flags_unisolated_embed(self) -> None:
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        f'> [!idea] Idea\n> - claim.\n> {EMB}\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'embed_not_isolated' in ids

    def test_check_page_does_not_flag_isolated_embed(self) -> None:
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        f'> [!idea] Idea\n> - claim.\n>\n> {EMB}\n>\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'embed_not_isolated' not in ids

    # real-repo anchor

    def test_real_wiki_has_no_unisolated_embeds(self) -> None:
        findings = []
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            fp = WIKI / folder
            if not fp.exists():
                continue
            for page in sorted(fp.glob('*.md')):
                findings.extend(f for f in cw.check_page(path=page, wiki_root=WIKI)
                                if f['check_id'] == 'embed_not_isolated')
        assert findings == [], findings

    # --- hyphenated open compounds (hyphenated_open_compound) --------------------
    #
    # CLAUDE.md / field convention: established multi-word terms ("reinforcement
    # learning", "natural language", "language model") stay open even as attributive
    # modifiers (CMOS 7.89). A hyphenated form ("reinforcement-learning benchmark")
    # is drift. `multi-agent` (prefixed compound) and `foundation-model` (a project
    # convention) are deliberately NOT in the banned set; `natural-language-vs-code`
    # is left alone by the `(?!-)` longer-token guard.

    # wiring invariants

    def test_hyphen_check_is_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('hyphenated_open_compound') == 'warning'

    def test_hyphen_finding_builder_accepts_the_id(self) -> None:
        f = cw.finding(check='hyphenated_open_compound', file='x.md', message='m')
        assert f['severity'] == 'warning'

    def test_hyphen_list_checks_cli_exposes_it(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        assert json.loads(r.stdout).get('hyphenated_open_compound') == 'warning'

    # detection: positive cases (the regex, directly)

    def test_regex_flags_each_banned_compound(self) -> None:
        for tok in ('reinforcement-learning', 'deep-reinforcement-learning',
                    'machine-learning', 'deep-learning', 'imitation-learning',
                    'transfer-learning', 'supervised-learning',
                    'unsupervised-learning', 'self-supervised-learning',
                    'natural-language', 'language-model', 'language-models'):
            m = cw.HYPHENATED_OPEN_COMPOUND.search(f'a {tok} benchmark')
            assert m, f'{tok} should be flagged'

    def test_regex_longest_match_wins(self) -> None:
        # deep-reinforcement-learning matches as the whole token, not the
        # reinforcement-learning suffix, so the suggested fix keeps "deep".
        m = cw.HYPHENATED_OPEN_COMPOUND.search('a deep-reinforcement-learning agent')
        assert m.group(1).lower() == 'deep-reinforcement-learning'
        assert cw.OPEN_COMPOUND_SUGGEST[m.group(1).lower()] == 'deep reinforcement learning'
        # self-supervised-learning keeps its "self-" prefix hyphenated.
        m2 = cw.HYPHENATED_OPEN_COMPOUND.search('a self-supervised-learning method')
        assert m2.group(1).lower() == 'self-supervised-learning'
        assert cw.OPEN_COMPOUND_SUGGEST[m2.group(1).lower()] == 'self-supervised learning'

    # detection: negative cases (no false positives)

    def test_regex_leaves_open_forms_alone(self) -> None:
        for s in ('reinforcement learning benchmark', 'natural language description',
                  'language model agents'):
            assert not cw.HYPHENATED_OPEN_COMPOUND.search(s), s

    def test_regex_does_not_flag_multi_agent_or_foundation_model(self) -> None:
        for s in ('a multi-agent system', 'the multi-agent-debate page',
                  'foundation-model agents', 'foundation-model-specific claims'):
            assert not cw.HYPHENATED_OPEN_COMPOUND.search(s), s

    def test_regex_longer_token_guard_spares_natural_language_vs_code(self) -> None:
        # the (?!-) guard: natural-language followed by another hyphen is left alone.
        assert not cw.HYPHENATED_OPEN_COMPOUND.search('the natural-language-vs-code split')

    # integration via check_page

    def test_check_page_flags_hyphen_on_concept(self) -> None:
        f = hyphen_findings(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                            '> [!idea] Idea\n> - a reinforcement-learning method.\n> ^idea')
        assert len(f) == 1
        assert 'reinforcement learning' in f[0]['fix_hint']

    def test_check_page_flags_hyphen_on_source_page_too(self) -> None:
        # Unlike the citation checks, this one is NOT exempt for source pages —
        # the over-hyphenation appeared on source pages, so they are scanned.
        f = hyphen_findings(self.tmp, 'sources', 'X.md', SOURCE_FM,
                            '> [!tldr] TL;DR\n> - a deep-learning pipeline.\n> ^tldr')
        assert len(f) == 1
        assert 'deep learning' in f[0]['fix_hint']

    def test_check_page_masks_hyphen_inside_wikilink_and_code(self) -> None:
        # A hyphenated token inside a [[wikilink]] target/display or inline `code`
        # is masked, not flagged — only prose hyphenation is drift.
        body = ('> [!idea] Idea\n'
                '> - see [[1-wiki/concepts/reinforcement-learning.md|reinforcement-learning]] '
                'and `reinforcement-learning` literally.\n> ^idea')
        assert hyphen_findings(self.tmp, 'concepts', 'c.md', CONCEPT_FM, body) == []

    def test_check_page_does_not_flag_open_form(self) -> None:
        f = hyphen_findings(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                            '> [!idea] Idea\n> - a reinforcement learning method.\n> ^idea')
        assert f == []

    # real-repo anchor

    def test_real_wiki_has_no_hyphenated_open_compounds(self) -> None:
        findings = []
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            fp = WIKI / folder
            if not fp.exists():
                continue
            for page in sorted(fp.glob('*.md')):
                findings.extend(f for f in cw.check_page(path=page, wiki_root=WIKI)
                                if f['check_id'] == 'hyphenated_open_compound')
        assert findings == [], findings

    def test_real_wiki_has_no_hyphenated_open_compound_noun(self) -> None:
        findings = []
        for folder in ('sources', 'entities', 'concepts', 'syntheses'):
            fp = WIKI / folder
            if not fp.exists():
                continue
            for page in sorted(fp.glob('*.md')):
                findings.extend(f for f in cw.check_page(path=page, wiki_root=WIKI)
                                if f['check_id'] == 'hyphenated_open_compound_noun')
        assert findings == [], findings

    def test_unverified_marker_regex_identical_to_body_hash(self) -> None:
        assert cw.UNVERIFIED_MARKER_RE.pattern == bh._UNVERIFIED_RE.pattern, (
            'UNVERIFIED_MARKER_RE (check_wiki, counts markers) and _UNVERIFIED_RE '
            '(body_hash, masks them from the hash) must stay byte-identical, or '
            'claim-counting and hash-masking silently disagree.')

    # --- source-page locator completeness (source_locator_incomplete) ------------
    #
    # On source pages the `#page=N` deep-link display must list the structural anchor
    # (sec./fig./tab./eq./app./ch.) AND the page together INSIDE the link
    # (`[[…#page=1|sec. 1, p. 1]]`); a split form (anchor outside the link) or a
    # page-only / anchor-only display is drift. The source-page counterpart of
    # citation_locator_incomplete, and the inverse of the retired
    # source_locator_anchor_inlined. (CLAUDE.md -> Source Support And Verification.)

    # wiring invariants

    def test_source_locator_check_is_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('source_locator_incomplete') == 'warning'

    def test_source_locator_finding_builder_accepts_the_id(self) -> None:
        f = cw.finding(check='source_locator_incomplete', file='x.md', message='m')
        assert f['check_id'] == 'source_locator_incomplete'
        assert f['severity'] == 'warning'

    def test_source_locator_list_checks_cli_exposes_it(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        assert json.loads(r.stdout).get('source_locator_incomplete') == 'warning'

    # detection: positive cases (anchor and page NOT together inside the link)

    def test_source_locator_split_anchor_is_flagged(self) -> None:
        f = loc_findings(f'> - a claim ({LOC_SPLIT}).')
        assert len(f) == 1
        assert f[0]['check_id'] == 'source_locator_incomplete'

    def test_source_locator_page_only_is_flagged(self) -> None:
        assert len(loc_findings(f'> - a claim ({LOC_PAGE_ONLY}).')) == 1

    def test_source_locator_anchor_only_is_flagged(self) -> None:
        assert len(loc_findings(f'> - a claim ({LOC_ANCHOR_ONLY}).')) == 1

    def test_source_locator_line_number_shifts_by_offset(self) -> None:
        body = f'> - a claim ({LOC_PAGE_ONLY}).'
        assert lineno(loc_findings(body, end=10)[0]) - lineno(loc_findings(body, end=0)[0]) == 10

    # detection: negative cases

    def test_source_locator_both_inside_not_flagged(self) -> None:
        assert loc_findings(f'> - a claim ({LOC_BOTH}).') == []

    def test_source_locator_each_anchor_kind_inside_not_flagged(self) -> None:
        # Structural (sec./app./ch.), float (fig./tab./eq.), and theorem-environment
        # (def./thm./lem./prop./cor./alg.) anchors are all valid (CLAUDE.md -> Source
        # Support And Verification); a page paired with any of them is complete.
        for disp in ('sec. 4', 'app. C', 'ch. 2', 'fig. 4', 'tab. 8', 'eq. 3',
                     'def. 1', 'thm. 3.1', 'lem. 4.2', 'prop. 5', 'cor. 3.3', 'alg. 2'):
            link = f'[[0-raw/papers/X.pdf#page=5|{disp}, p. 5]]'
            assert loc_findings(f'> - claim ({link}).') == [], disp

    def test_source_locator_abstract_anchor_ok(self) -> None:
        # The front-matter `abstract` is a valid anchor (CLAUDE.md -> Source Support
        # And Verification). Abstract-drawn content is cited `abstract, p. 1`, never
        # relabelled `sec. 1` (on most papers sec. 1 is not on the abstract's page).
        assert loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=1|abstract, p. 1]]).') == []
        # case-insensitive, and only as the anchor token — `p. 1` alone still fails.
        assert loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=1|Abstract, p. 1]]).') == []
        assert len(loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=1|p. 1]]).')) == 1

    def test_source_locator_unpaginated_appendix_anchor_alone_ok(self) -> None:
        # The unpaginated-supplement exemption (CLAUDE.md -> Source Support And
        # Verification): a published appendix often carries no printed page, so an
        # `app.`-anchored display cites the anchor alone rather than fabricating a
        # `p. M`. The exemption is `app.`-only and does not widen the anchor set.
        assert loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=16|app. D.1, tab. 8]]).') == []
        assert loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=16|app. C]]).') == []
        # a paginated appendix keeps its page; the exemption does not require dropping it
        assert loc_findings('> - a claim ([[0-raw/papers/X.pdf#page=16|app. C, p. 4186]]).') == []
        # …and no other anchor kind may stand alone (theorem environments included)
        for disp in ('sec. 4', 'ch. 2', 'fig. 4', 'tab. 8', 'eq. 3', 'abstract',
                     'def. 1', 'thm. 3.1', 'lem. 4.2', 'prop. 5', 'cor. 3.3', 'alg. 2'):
            link = f'[[0-raw/papers/X.pdf#page=5|{disp}]]'
            assert len(loc_findings(f'> - claim ({link}).')) == 1, disp

    def test_citation_locator_unpaginated_appendix_anchor_alone_ok(self) -> None:
        # The concept/entity/synthesis counterpart: both checks share
        # locator_display_complete, so the exemption cannot drift between them.
        body = f'> - claim {SRC} ([[0-raw/papers/X.pdf#page=16|app. D.1, tab. 8]]).'
        f = cw.check_citation_form(body=body, rel='1-wiki/concepts/c.md', end=0)
        assert [x['check_id'] for x in f if x['check_id'] == 'citation_locator_incomplete'] == []
        bare = f'> - claim {SRC} ([[0-raw/papers/X.pdf#page=16|sec. 4]]).'
        f = cw.check_citation_form(body=bare, rel='1-wiki/concepts/c.md', end=0)
        assert 'citation_locator_incomplete' in {x['check_id'] for x in f}

    def test_source_locator_inside_inline_code_is_masked(self) -> None:
        assert loc_findings(f'> - literally `{LOC_PAGE_ONLY}` in code.') == []

    def test_source_locator_inside_sources_callout_is_masked(self) -> None:
        body = (f'> [!sources] Sources\n> - {LOC_PAGE_ONLY}\n> ^sources')
        assert loc_findings(body) == []

    # integration via check_page

    def test_check_page_flags_source_locator_on_source(self) -> None:
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        f'> [!tldr] TL;DR\n> - a claim ({LOC_PAGE_ONLY}).\n> ^tldr')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'source_locator_incomplete' in ids

    def test_check_page_does_not_flag_source_locator_on_concept(self) -> None:
        # Concept pages run citation_locator_incomplete instead; the source-page
        # check must not run on them.
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        f'> [!idea] Idea\n> - claim {SRC} ({LOC_PAGE_ONLY}).\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'source_locator_incomplete' not in ids

    # --- diff-guard: section change on a verified page (verified_anchor_unaudited) --
    #
    # A status:verified page must not keep `verified` after a locator's structural
    # anchor was ADDED or CHANGED vs HEAD (a "section change" is grounds for re-
    # verification; CLAUDE.md -> Page Status). A pure RELOCATION (same anchor + page,
    # repositioned) and a marked `*[unverified]*` bullet are exempt. Tested on the
    # pure core anchor_change_findings (no git working tree needed).

    def test_diffguard_abstract_to_sec_is_flagged(self) -> None:
        # The exact bug: abstract-drawn content relabelled `sec. 1` on a verified page.
        f = dg(f'> - c ([[{DG}#page=1|sec. 1, p. 1]]).',
               f'> - c ([[{DG}#page=1|abstract, p. 1]]).')
        assert len(f) == 1 and f[0]['check_id'] == 'verified_anchor_unaudited'

    def test_diffguard_page_only_to_anchor_is_flagged(self) -> None:
        assert len(dg(f'> - c ([[{DG}#page=13|sec. 4.2, p. 13]]).',
                      f'> - c ([[{DG}#page=13|p. 13]]).')) == 1

    def test_diffguard_anchor_changed_same_page_is_flagged(self) -> None:
        assert len(dg(f'> - c ([[{DG}#page=5|sec. 4, p. 5]]).',
                      f'> - c ([[{DG}#page=5|sec. 3, p. 5]]).')) == 1

    def test_diffguard_relocation_is_not_flagged(self) -> None:
        # `sec. 3.2` existed (outside the link) at HEAD — repositioning it inside is
        # claim-neutral, not a section change.
        assert dg(f'> - c ([[{DG}#page=9|sec. 3.2, p. 9]]).',
                  f'> - c (sec. 3.2, [[{DG}#page=9|p. 9]]).') == []

    def test_diffguard_unchanged_is_not_flagged(self) -> None:
        line = f'> - c ([[{DG}#page=5|sec. 3, p. 5]]).'
        assert dg(line, line) == []

    def test_diffguard_skips_non_verified_page(self) -> None:
        assert dg(f'> - c ([[{DG}#page=1|sec. 1, p. 1]]).',
                  f'> - c ([[{DG}#page=1|abstract, p. 1]]).', status='draft') == []

    def test_diffguard_promotion_from_draft_head_is_not_flagged(self) -> None:
        # A draft->verified promotion that adds a citation anchor is the verification
        # event, not a self-re-stamp: exempt when the page was NOT verified at HEAD.
        assert dg(f'> - c ([[{DG}#page=1|sec. 1, p. 1]]).',
                  f'> - c ([[{DG}#page=1|p. 1]]).', head_status='draft') == []

    def test_diffguard_anchor_change_still_flagged_when_verified_at_head(self) -> None:
        # The genuine abuse still fires: verified at HEAD, stayed verified, anchor changed.
        assert len(dg(f'> - c ([[{DG}#page=1|sec. 1, p. 1]]).',
                      f'> - c ([[{DG}#page=1|abstract, p. 1]]).',
                      head_status='verified')) == 1

    def test_diffguard_unverified_marker_is_exempt(self) -> None:
        assert dg(f'> - c ([[{DG}#page=1|sec. 1, p. 1]]). *[unverified]*',
                  f'> - c ([[{DG}#page=1|abstract, p. 1]]).') == []

    def test_diffguard_registered_and_exposed(self) -> None:
        assert cw.CHECKS.get('verified_anchor_unaudited') == 'error'

    # --- verified_hash_mismatch (committed-state backstop, Mechanism 2) -----------

    def test_verified_hash_match_is_not_flagged(self) -> None:
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!tldr] TL;DR\n> - a claim.\n> ^tldr')
        h = cw.body_hash(path=str(p))
        assert cw.check_verified_hash(
            path=p, fm={'status': 'verified', 'verified_hash': h},
            rel='1-wiki/sources/X.md') == []

    def test_verified_hash_mismatch_is_flagged(self) -> None:
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!tldr] TL;DR\n> - a claim.\n> ^tldr')
        f = cw.check_verified_hash(
            path=p, fm={'status': 'verified', 'verified_hash': 'deadbeef'},
            rel='1-wiki/sources/X.md')
        assert len(f) == 1 and f[0]['check_id'] == 'verified_hash_mismatch'

    def test_verified_without_stamp_is_flagged(self) -> None:
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!tldr] TL;DR\n> - a claim.\n> ^tldr')
        f = cw.check_verified_hash(
            path=p, fm={'status': 'verified'}, rel='1-wiki/sources/X.md')
        assert len(f) == 1 and f[0]['check_id'] == 'verified_hash_mismatch'

    def test_verified_hash_skips_draft(self) -> None:
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!tldr] TL;DR\n> - a claim.\n> ^tldr')
        assert cw.check_verified_hash(
            path=p, fm={'status': 'draft', 'verified_hash': 'x'},
            rel='1-wiki/sources/X.md') == []

    def test_verified_hash_masks_added_unverified_line(self) -> None:
        # Claim-level model through the new check: a verified page whose only change
        # since stamping is an added *[unverified]* line does not trip the hash.
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!tldr] TL;DR\n> - a claim.\n> ^tldr')
        h = cw.body_hash(path=str(p))
        p.write_text(p.read_text(encoding='utf-8') + '> - pending. *[unverified]*\n',
                     encoding='utf-8')
        assert cw.check_verified_hash(
            path=p, fm={'status': 'verified', 'verified_hash': h},
            rel='1-wiki/sources/X.md') == []

    def test_verified_hash_registered(self) -> None:
        assert cw.CHECKS.get('verified_hash_mismatch') == 'warning'
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert json.loads(r.stdout).get('verified_anchor_unaudited') == 'error'

    def test_verified_hash_malformed_delimiter_is_flagged(self) -> None:
        # A whitespace-padded closing `---` is accepted by parse_frontmatter
        # (strip-based) but rejected by body_hash (exact `\n---\n`), which raises
        # ValueError. check_verified_hash must SURFACE that as verified_hash_mismatch,
        # not swallow it — else a `verified` page silently escapes the hash backstop
        # (a self-concealing false green). Pins the ValueError-surfacing branch.
        d = self.tmp / '1-wiki' / 'sources'
        d.mkdir(parents=True, exist_ok=True)
        p = d / 'X.md'
        p.write_text('---\n' + SOURCE_FM + '\n--- \n\n'
                     '> [!tldr] TL;DR\n> - a claim.\n> ^tldr\n', encoding='utf-8')
        f = cw.check_verified_hash(
            path=p, fm={'status': 'verified', 'verified_hash': 'deadbeef'},
            rel='1-wiki/sources/X.md')
        assert len(f) == 1 and f[0]['check_id'] == 'verified_hash_mismatch'

    # --- wikilink_pipe_spacing transform (re-stamp-eligible, so pinned) ----------

    def test_pipe_spacing_detects_padded_pipe(self) -> None:
        _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                    '> [!idea] Idea\n> - see [[1-wiki/concepts/y.md | y]].\n> ^idea')
        finds = cw.check_wikilink_pipe_spacing(wiki_root=self.tmp / '1-wiki')
        assert [f['check_id'] for f in finds] == ['wikilink_pipe_spacing']

    def test_pipe_spacing_fix_collapses_all_padding_forms(self) -> None:
        assert fix_pipes('[[a | b]]') == '[[a|b]]'
        assert fix_pipes('[[a| b]]') == '[[a|b]]'
        assert fix_pipes('[[a |b]]') == '[[a|b]]'

    def test_pipe_spacing_fix_is_idempotent(self) -> None:
        assert fix_pipes('[[a|b]]') == '[[a|b]]'

    def test_pipe_spacing_fix_leaves_table_cells(self) -> None:
        # A `|` outside `[[...]]` (a Markdown table row) must not be touched.
        assert fix_pipes('| a | b |') == '| a | b |'

    def test_pipe_spacing_fix_roundtrips_to_clean(self) -> None:
        fixed = fix_pipes('x [[a | b]] and [[c|d]] y')
        assert not cw.PIPE_SPACING_RE.search(fixed)
        assert fixed == 'x [[a|b]] and [[c|d]] y'

    # --- bullet-initial wikilink capitalization (wikilink_display_uncapitalized) --
    #
    # A bullet that opens with a wikilink is sentence-initial, so its display takes a
    # leading capital (CLAUDE.md -> Wikilink Format). A common-noun display stays
    # lowercase mid-sentence but capitalizes when it opens the bullet. The Sources
    # callout is exempt (its displays are filename-derived source stems, kept
    # verbatim); a display whose first char is not a lowercase letter is left alone.

    # wiring invariants

    def test_caps_check_is_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('wikilink_display_uncapitalized') == 'warning'

    def test_caps_finding_builder_accepts_the_id(self) -> None:
        f = cw.finding(check='wikilink_display_uncapitalized', file='x.md', message='m')
        assert f['check_id'] == 'wikilink_display_uncapitalized'
        assert f['severity'] == 'warning'

    def test_caps_list_checks_cli_exposes_it(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        assert json.loads(r.stdout).get('wikilink_display_uncapitalized') == 'warning'

    # detection: positive cases

    def test_caps_lowercase_bullet_initial_flagged(self) -> None:
        f = caps_findings('> - [[1-wiki/concepts/c.md|collaboration channel]] — the unit.')
        assert len(f) == 1
        assert 'Collaboration channel' in f[0]['fix_hint']

    def test_caps_indented_sub_bullet_flagged(self) -> None:
        f = caps_findings('>   - [[1-wiki/concepts/c.md|collaboration channel]] — the unit.')
        assert len(f) == 1

    def test_caps_line_number_shifts_by_offset(self) -> None:
        body = '> - [[1-wiki/concepts/c.md|collaboration channel]] — x.'
        assert lineno(caps_findings(body, end=10)[0]) - lineno(caps_findings(body, end=0)[0]) == 10

    # detection: negative cases

    def test_caps_capitalized_display_not_flagged(self) -> None:
        assert caps_findings('> - [[1-wiki/entities/d.md|BERT]] is a system.') == []

    def test_caps_digit_initial_display_not_flagged(self) -> None:
        assert caps_findings('> - [[1-wiki/concepts/g.md|5G networks]] are fast.') == []

    def test_caps_mid_bullet_wikilink_not_flagged(self) -> None:
        # The leading-capital rule is sentence-initial only; a wikilink later in the
        # bullet keeps its lowercase common-noun display.
        assert caps_findings('> - It uses a [[1-wiki/concepts/c.md|collaboration channel]].') == []

    def test_caps_sources_callout_exempt(self) -> None:
        # Source-stem displays in the Sources callout are filename-derived, kept
        # verbatim, and must not be force-capitalized.
        body = ('> [!sources] Sources\n'
                '> - [[1-wiki/sources/illustrated-transformer.md|illustrated-transformer]]\n'
                '> ^sources')
        assert caps_findings(body) == []

    # integration via check_page

    def test_check_page_flags_caps_on_concept(self) -> None:
        p = _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        '> [!idea] Idea\n> - [[1-wiki/concepts/c.md|collaboration channel]] — x.\n> ^idea')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'wikilink_display_uncapitalized' in ids

    def test_check_page_flags_caps_on_source(self) -> None:
        # The rule is general — applies to source pages too.
        p = _write_page(self.tmp, 'sources', 'X.md', SOURCE_FM,
                        '> [!concepts-entities] Concepts and Entities\n'
                        '> - [[1-wiki/concepts/c.md|collaboration channel]] — x.\n> ^concepts-entities')
        wiki = self.tmp / '1-wiki'
        ids = {f['check_id'] for f in cw.check_page(path=p, wiki_root=wiki)}
        assert 'wikilink_display_uncapitalized' in ids

    # NB: no real-repo "no findings" invariant yet — several pages carry pre-existing
    # uncapitalized bullet-initial displays (Vaswani2017AttentionIA, Kingma2015AdamAM,
    # Devlin2019BERTPO, …). Add the standing assertion once that cleanup lands.

    def test_caps_locator_deeplink_not_flagged(self) -> None:
        # A bullet opening with a raw-file locator deep-link (`p. 5`, a page token,
        # not a page name) is NOT subject to the leading-capital rule — the check is
        # scoped to `1-wiki/` page targets.
        body = '> - [[0-raw/papers/X.pdf#page=5|p. 5]]: the gap chart.'
        assert caps_findings(body) == []

    # --- chronology: log/hot are timed and newest-first ---------------------------
    #
    # log.md (every `## [date time] …` entry) and hot.md Recent activity (each
    # `- [date time] …` bullet) must carry a 24-hour time and run newest-first, so
    # entries from separately-merged branches sort unambiguously (CLAUDE.md → Hot,
    # Index, And Log). check_chronology emits chronology_missing_time (no time) and
    # chronology_out_of_order (timed entries not descending); sort_chronology.py is
    # the determinate auto-fix.

    # wiring invariants

    def test_chronology_checks_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('chronology_missing_time') == 'warning'
        assert cw.CHECKS.get('chronology_out_of_order') == 'warning'

    def test_chronology_list_checks_cli_exposes_them(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        listed = json.loads(r.stdout)
        assert listed.get('chronology_missing_time') == 'warning'
        assert listed.get('chronology_out_of_order') == 'warning'

    # detection

    def test_chronology_inorder_log_not_flagged(self) -> None:
        w = _wiki(self.tmp, log=LOG_OK)
        ids = {f['check_id'] for f in cw.check_chronology(wiki_root=w)}
        assert 'chronology_out_of_order' not in ids
        assert 'chronology_missing_time' not in ids

    def test_chronology_disordered_log_flagged(self) -> None:
        w = _wiki(self.tmp, log=LOG_DISORDER)
        ids = {f['check_id'] for f in cw.check_chronology(wiki_root=w)}
        assert 'chronology_out_of_order' in ids

    def test_chronology_untimed_log_flagged(self) -> None:
        w = _wiki(self.tmp, log=LOG_UNTIMED)
        ids = {f['check_id'] for f in cw.check_chronology(wiki_root=w)}
        assert 'chronology_missing_time' in ids

    def test_chronology_hot_recent_activity_checked(self) -> None:
        w = _wiki(self.tmp, hot=HOT_DISORDER)
        fs = cw.check_chronology(wiki_root=w)
        assert any(f['check_id'] == 'chronology_out_of_order'
                   and f['file'].endswith('hot.md') for f in fs)

    def test_chronology_inorder_hot_not_flagged(self) -> None:
        w = _wiki(self.tmp, hot=HOT_OK)
        ids = {f['check_id'] for f in cw.check_chronology(wiki_root=w)}
        assert 'chronology_out_of_order' not in ids

    # sorter (sort_chronology.py)

    def test_sorter_orders_log_newest_first_with_bodies(self) -> None:
        w = _wiki(self.tmp, log=LOG_DISORDER)
        assert sc.main.__module__  # module loaded
        out = sc.sort_log(w / 'log.md')
        heads = re.findall(r'^## \[(.*?)\]', out, re.M)
        assert heads == ['2026-06-08 18:00', '2026-06-08 09:00']
        # body stays attached to its header
        assert re.search(r'18:00\] audit \| newer second \(wrong\)\n- b', out)

    def test_sorter_is_idempotent(self) -> None:
        w = _wiki(self.tmp, log=LOG_OK)
        once = sc.sort_log(w / 'log.md')
        (w / 'log.md').write_text(once, encoding='utf-8')
        assert sc.sort_log(w / 'log.md') == once

    def test_sorter_refuses_untimed_log(self) -> None:
        w = _wiki(self.tmp, log=LOG_UNTIMED)
        try:
            sc.sort_log(w / 'log.md')
            assert False, 'expected ValueError on untimed entry'
        except ValueError:
            pass

    def test_sorter_orders_hot_and_preserves_other_sections(self) -> None:
        w = _wiki(self.tmp, hot=HOT_DISORDER)
        out = sc.sort_hot(w / 'hot.md')
        ra = out.split('## Recent activity')[1].split('## Open threads')[0]
        bullets = re.findall(r'^- \[(.*?)\]', ra, re.M)
        assert bullets == ['2026-06-08 20:00', '2026-06-08 08:00']
        assert '## Open threads\n\n- keep me' in out

    def test_sorter_hot_preserves_non_entry_lines(self) -> None:
        # Regression: sort_hot must not rebuild the block from dated bullets alone
        # (that silently dropped placeholders, parked notes, and sub-bullets).
        w = _wiki(self.tmp, hot=HOT_WITH_STRAY)
        out = sc.sort_hot(w / 'hot.md')
        assert 'a parked note the user left here' in out       # preamble preserved
        assert 'nested detail under b' in out                  # entry body preserved
        ra = out.split('## Recent activity')[1].split('## Open threads')[0]
        bullets = re.findall(r'^- \[(.*?)\]', ra, re.M)
        assert bullets == ['2026-06-08 20:00', '2026-06-08 08:00']  # sorted newest-first
        # the sub-bullet moved with its entry (b), not stranded under a
        assert out.index('nested detail under b') < out.index('08:00] a')
        assert '## Open threads\n\n- keep me' in out           # other sections intact

    def test_sorter_hot_placeholder_only_preserved(self) -> None:
        # A Recent-activity section with only a `- None yet` placeholder (no dated
        # entry) is left untouched rather than emptied.
        hot = ('---\ntype: hot\n---\n\n# Hot\n\n## Recent activity\n\n'
               '- None yet\n\n## Open threads\n\n- keep me\n')
        w = _wiki(self.tmp, hot=hot)
        out = sc.sort_hot(w / 'hot.md')
        ra = out.split('## Recent activity')[1].split('## Open threads')[0]
        assert '- None yet' in ra

    def test_sorter_main_skips_untimed_returns_1(self) -> None:
        _wiki(self.tmp, log=LOG_UNTIMED, hot=HOT_OK)
        r = subprocess.run([sys.executable, str(SORT_SCRIPT), str(self.tmp / '1-wiki')],
                           capture_output=True, text=True)
        assert r.returncode == 1  # log skipped: no recoverable link, manual time needed

    # auto-recovery of a missing time from the linked report filename (determinate)

    def test_recover_time_single_matching_link(self) -> None:
        txt = '- Saved: [[2-outputs/query/query-2026-06-07-0915-topic.md|query]]'
        assert sc.recover_time(txt, '2026-06-07') == '09:15'

    def test_recover_time_date_mismatch_returns_none(self) -> None:
        # The link's date must match the entry's date, or it is not this entry's time.
        txt = '- Saved: [[2-outputs/query/query-2026-06-07-0915-topic.md|query]]'
        assert sc.recover_time(txt, '2026-06-08') is None

    def test_recover_time_conflicting_links_returns_none(self) -> None:
        # Two same-date links with different times → ambiguous → stays manual.
        txt = ('- a [[2-outputs/query/query-2026-06-07-0915-x.md|q]] '
               'and [[2-outputs/query/query-2026-06-07-1620-y.md|q]]')
        assert sc.recover_time(txt, '2026-06-07') is None

    def test_recover_time_no_link_returns_none(self) -> None:
        assert sc.recover_time('- just prose, no report link', '2026-06-07') is None

    def test_sorter_fills_recoverable_log_then_sorts(self) -> None:
        w = _wiki(self.tmp, log=LOG_UNTIMED_RECOVERABLE)
        out = sc.sort_log(w / 'log.md')
        heads = re.findall(r'^## \[(.*?)\]', out, re.M)
        assert heads == ['2026-06-08 18:00', '2026-06-07 09:15']

    def test_sorter_fills_recoverable_hot_then_sorts(self) -> None:
        w = _wiki(self.tmp, hot=HOT_UNTIMED_RECOVERABLE)
        out = sc.sort_hot(w / 'hot.md')
        ra = out.split('## Recent activity')[1].split('## Open threads')[0]
        bullets = re.findall(r'^- \[(.*?)\]', ra, re.M)
        assert bullets == ['2026-06-08 20:00', '2026-06-07 09:15']
        assert '## Open threads\n\n- keep me' in out

    # real-repo anchor: the committed log/hot are timed and sorted

    def test_real_wiki_log_hot_timed_and_sorted(self) -> None:
        findings = [f for f in cw.check_chronology(wiki_root=WIKI)
                    if f['check_id'].startswith('chronology')]
        assert findings == [], findings

    # --- hyphenated_open_compound_noun: bare-noun de-hyphenation, modifier-safe ----
    # A slug-derived open compound (tool-use, belief-state) is correct OPEN as a noun
    # but correct HYPHENATED as a modifier. The check flags ONLY the bare-noun
    # position, never a modifier, and never a wikilink display. Two curated lists
    # (OPEN_COMPOUND_NOUN_SUGGEST / HYPHENATED_COMPOUND_ALLOWED) drive it; these tests
    # pin the noun-vs-modifier behaviour so the lists can grow without regressing it.

    def test_open_compound_noun_flags_bare_noun_before_clause_end(self) -> None:
        f = _noun_findings(
            self.tmp, '> [!idea] Idea\n> - The lever is the belief-state.\n> ^idea')
        assert len(f) == 1
        assert 'belief state' in f[0]['fix_hint']

    def test_open_compound_noun_flags_before_copula(self) -> None:
        f = _noun_findings(
            self.tmp, '> [!idea] Idea\n> - The tool-use is costly here.\n> ^idea')
        assert any('tool use' in x['fix_hint'] for x in f)

    def test_open_compound_noun_flags_before_versus(self) -> None:
        f = _noun_findings(
            self.tmp,
            '> [!idea] Idea\n> - A test of belief-state versus other levers.\n> ^idea')
        assert len(f) == 1

    def test_open_compound_noun_does_not_flag_modifier(self) -> None:
        # "belief-state representation" — belief-state modifies a following noun, so
        # the hyphen is correct and must NOT be flagged (the no-overcorrection rule).
        f = _noun_findings(
            self.tmp,
            '> [!idea] Idea\n> - An explicit belief-state representation helps.\n> ^idea')
        assert f == []

    def test_open_compound_noun_does_not_flag_allowed_lookalike(self) -> None:
        # fine-tuning is on the ALLOWED keep-hyphenated list — never flagged, even as
        # a bare noun.
        f = _noun_findings(
            self.tmp, '> [!idea] Idea\n> - The main cost is the fine-tuning.\n> ^idea')
        assert f == []

    def test_open_compound_noun_does_not_flag_wikilink_display(self) -> None:
        # A compound inside a wikilink display is masked, so a hyphenated display is
        # never flagged — display text stays a manual call.
        f = _noun_findings(
            self.tmp,
            '> [!idea] Idea\n> - See [[1-wiki/concepts/tool-use.md|tool-use]].\n> ^idea')
        assert f == []

    def test_open_compound_noun_registered_as_warning(self) -> None:
        assert cw.CHECKS.get('hyphenated_open_compound_noun') == 'warning'

    def test_open_compound_noun_in_list_checks_cli(self) -> None:
        r = subprocess.run([sys.executable, str(SCRIPT), '--list-checks'],
                           capture_output=True, text=True)
        assert r.returncode == 0
        listed = json.loads(r.stdout)
        assert listed.get('hyphenated_open_compound_noun') == 'warning'

    def test_open_compound_noun_lists_are_disjoint(self) -> None:
        # A term must not sit on both lists by accident (the allowed list is also a
        # hard never-flag guard, but disjointness keeps intent clear).
        overlap = set(cw.OPEN_COMPOUND_NOUN_SUGGEST) & cw.HYPHENATED_COMPOUND_ALLOWED
        assert overlap == set(), overlap

    # --- hyphenated_open_compound_noun, direction 2: re-hyphenate an open modifier --
    # The inverse fix — an open compound directly before a curated HEAD NOUN was
    # overcorrected open and should be re-hyphenated. Head-noun-gated so a following
    # verb never triggers it (the "tool use reaches" false-positive class). A
    # verified-ignore phrase is skipped in both directions.

    def test_open_compound_noun_direction2_flags_open_modifier(self) -> None:
        f = _noun_findings(
            self.tmp,
            '> [!idea] Idea\n> - An explicit belief state representation helps.\n> ^idea')
        assert len(f) == 1
        assert 'belief-state representation' in f[0]['fix_hint']

    def test_open_compound_noun_direction2_ignores_following_verb(self) -> None:
        # "tool use reaches" — an open compound before a VERB is a noun, not a
        # modifier; must NOT be flagged (the 27-false-positive guard).
        f = _noun_findings(
            self.tmp,
            '> [!idea] Idea\n> - Here tool use reaches outside the model.\n> ^idea')
        assert f == []

    def test_open_compound_noun_direction2_ignores_nonhead_noun(self) -> None:
        # A noun not on COMPOUND_MODIFIER_HEADS is never treated as a head.
        f = _noun_findings(
            self.tmp, '> [!idea] Idea\n> - The tool use philosophy varies.\n> ^idea')
        assert f == []

    def test_open_compound_noun_verified_ignore_suppresses_both(self) -> None:
        # A phrase on the verified-ignore list is skipped (here, a direction-2 case).
        with mock.patch.object(cw, 'HYPHENATION_VERIFIED_IGNORE',
                               frozenset({'belief state representation'})):
            f = _noun_findings(
                self.tmp,
                '> [!idea] Idea\n> - An explicit belief state representation helps.\n> ^idea')
        assert f == []

    # --- hyphenation lists loaded from the agent-writable data file ----------------
    # The four lists live in .claude/skills/multi-skill/hyphenation-lists.md (audit grows
    # them autonomously). The loader must parse the sections and degrade safely.

    def test_hyphenation_lists_load_from_real_data_file(self) -> None:
        # The shipped data file populates all the lists the check depends on.
        assert 'belief-state' in cw.OPEN_COMPOUND_NOUN_SUGGEST
        assert cw.OPEN_COMPOUND_NOUN_SUGGEST['belief-state'] == 'belief state'
        assert 'gpt-3' in cw.HYPHENATED_COMPOUND_ALLOWED
        assert 'representation' in cw.COMPOUND_MODIFIER_HEADS

    def test_hyphenation_loader_parses_sections(self) -> None:
        f = self.tmp / 'h.md'
        f.write_text(
            '# x\n\n## disallowed\n- foo-bar = foo bar\n- bad line no equals\n\n'
            '## allowed\n- keep-this\n\n## heads\n- thing\n\n'
            '## verified-ignore\n- foo bar thing\n', encoding='utf-8')
        dis, allow, heads, ign = cw._load_hyphenation_lists(f)
        assert dis == {'foo-bar': 'foo bar'}          # malformed no-equals line skipped
        assert allow == frozenset({'keep-this'})
        assert heads == frozenset({'thing'})
        assert ign == frozenset({'foo bar thing'})

    def test_hyphenation_loader_missing_file_is_empty_not_fatal(self) -> None:
        dis, allow, heads, ign = cw._load_hyphenation_lists(self.tmp / 'nope.md')
        assert (dis, allow, heads, ign) == ({}, frozenset(), frozenset(), frozenset())

    def test_never_match_regex_matches_nothing(self) -> None:
        assert cw._never_match().search('belief state tool use anything') is None


class TestPaginationMap(unittest.TestCase):
    """The pagination map: the loader/`_parse_page_span`, `printed_page`, the
    map-aware locator exemption (`locator_display_complete`), and the two checks
    `locator_page_mismatch` / `pagination_map_unregistered`. Uses only the
    placeholder raw `0-raw/papers/X.pdf`; PAGINATION_MAP is a module global, so
    tests patch it with `mock.patch.object` rather than reloading."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def _mapfile(self, text: str) -> Path:
        p = self.tmp / 'pagination-map.md'
        p.write_text(text, encoding='utf-8')
        return p

    # --- loader + _parse_page_span ---
    def test_parse_page_span(self) -> None:
        assert cw._parse_page_span('5') == [5]
        assert cw._parse_page_span('1-3') == [1, 2, 3]
        assert cw._parse_page_span('x') is None
        assert cw._parse_page_span('3-1') is None   # reversed span rejected

    def test_load_map_arabic_span_none_and_comment(self) -> None:
        m = cw._load_pagination_map(self._mapfile(
            '## 0-raw/papers/X.pdf\n'
            '- 1 = 4171          # proceedings offset\n'
            '- 2-4 = 4172-4174\n'
            '- 5 = none\n'))
        assert m == {'0-raw/papers/X.pdf':
                     {1: 4171, 2: 4172, 3: 4173, 4: 4174, 5: None}}

    def test_load_map_skips_malformed(self) -> None:
        m = cw._load_pagination_map(self._mapfile(
            '## 0-raw/papers/X.pdf\n'
            '- 1 = 4171\n'
            '- 2-4 = 4172-4173\n'   # unequal span lengths -> skipped
            '- garbage line\n'      # no '=' -> skipped
            '- 9 = notanumber\n'))  # rhs not number/none/span -> skipped
        assert m == {'0-raw/papers/X.pdf': {1: 4171}}

    def test_load_map_missing_file_is_empty(self) -> None:
        assert cw._load_pagination_map(self.tmp / 'nope.md') == {}

    def test_load_map_ignores_non_raw_headings(self) -> None:
        # Prose H2 headings and fenced examples must not become entries.
        m = cw._load_pagination_map(self._mapfile(
            '## Why this file exists\n- 1 = 5\n'   # not a 0-raw heading -> skipped
            '## 0-raw/papers/X.pdf\n- 1 = 5\n'))
        assert m == {'0-raw/papers/X.pdf': {1: 5}}

    def test_shipped_template_parses_empty(self) -> None:
        # The real data file ships with no entries; its example fence/comment
        # must be inert to the parser.
        assert cw._load_pagination_map() == {}

    def test_printed_page_three_states(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP',
                               {'0-raw/papers/X.pdf': {5: 4175, 6: None}}):
            assert cw.printed_page('0-raw/papers/X.pdf', 5) == ('paginated', 4175)
            assert cw.printed_page('0-raw/papers/X.pdf', 6) == ('unpaginated', None)
            assert cw.printed_page('0-raw/papers/X.pdf', 7) == ('unregistered', None)
            assert cw.printed_page('0-raw/papers/Other.pdf', 1) == ('unregistered', None)

    # --- map-aware exemption ---
    def test_exemption_paginated_requires_page(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {5: 5}}):
            # page prints a number -> anchor alone (even `app.`) is incomplete
            assert not cw.locator_display_complete(
                display='sec. 3', raw='0-raw/papers/X.pdf', phys=5)
            assert not cw.locator_display_complete(
                display='app. A', raw='0-raw/papers/X.pdf', phys=5)
            assert cw.locator_display_complete(
                display='sec. 3, p. 5', raw='0-raw/papers/X.pdf', phys=5)

    def test_exemption_unpaginated_allows_any_anchor_only(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {20: None}}):
            assert cw.locator_display_complete(
                display='app. A', raw='0-raw/papers/X.pdf', phys=20)
            assert cw.locator_display_complete(   # any anchor, not only `app.`
                display='sec. 3', raw='0-raw/papers/X.pdf', phys=20)

    def test_exemption_unregistered_falls_back_to_app_heuristic(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {}):
            assert cw.locator_display_complete(     # `app.`-only OK (fallback)
                display='app. A', raw='0-raw/papers/X.pdf', phys=3)
            assert not cw.locator_display_complete(  # `sec.`-only still incomplete
                display='sec. 3', raw='0-raw/papers/X.pdf', phys=3)

    def test_exemption_no_keys_is_pure_display_heuristic(self) -> None:
        # Called without raw/phys (e.g. a caller with no deep-link keys): the
        # original app.-only behaviour.
        assert cw.locator_display_complete(display='app. A')
        assert not cw.locator_display_complete(display='sec. 3')

    # --- locator_page_mismatch ---
    def _match(self, body: str) -> list[str]:
        return [f['check_id'] for f in cw.check_locator_page_match(
            body=body, rel='1-wiki/concepts/c.md', end=0)]

    def test_mismatch_fires_on_wrong_printed_page(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {5: 4175}}):
            body = ('> - claim ([[1-wiki/sources/X.md|X]]; '
                    '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 99]]).')
            assert self._match(body) == ['locator_page_mismatch']

    def test_no_mismatch_when_page_matches(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {5: 4175}}):
            body = ('> - claim ([[1-wiki/sources/X.md|X]]; '
                    '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 4175]]).')
            assert self._match(body) == []

    def test_mismatch_fires_when_page_prints_nothing(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {20: None}}):
            body = ('> - claim ([[1-wiki/sources/X.md|X]]; '
                    '[[0-raw/papers/X.pdf#page=20|app. A, p. 4]]).')
            assert self._match(body) == ['locator_page_mismatch']

    def test_no_mismatch_on_unregistered_raw(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {}):
            body = ('> - claim ([[1-wiki/sources/X.md|X]]; '
                    '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 99]]).')
            assert self._match(body) == []

    def test_mismatch_ignores_pp_ranges(self) -> None:
        # Conservative for an error-severity check: `pp. M–N` ranges not matched.
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {5: 4175}}):
            body = ('> - claim ([[1-wiki/sources/X.md|X]]; '
                    '[[0-raw/papers/X.pdf#page=5|sec. 3, pp. 99-100]]).')
            assert self._match(body) == []

    def test_page_num_re_ignores_p_inside_app(self) -> None:
        # The classic bug: the `p.` inside `app.` must not read as a page token.
        assert cw.CITATION_PAGE_NUM_RE.search('app. D.1, tab. 8') is None
        assert cw.CITATION_PAGE_NUM_RE.search('sec. 3, p. 5').group(1) == '5'

    # --- pagination_map_unregistered ---
    def test_registration_flags_unregistered_raw(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {}):
            _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        '> - claim ([[1-wiki/sources/X.md|X]]; '
                        '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 5]]).')
            f = cw.check_pagination_registration(wiki_root=self.tmp / '1-wiki')
            assert [x['check_id'] for x in f] == ['pagination_map_unregistered']
            assert f[0]['file'] == '0-raw/papers/X.pdf'

    def test_registration_silent_when_registered(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {'0-raw/papers/X.pdf': {5: 5}}):
            _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        '> - claim ([[1-wiki/sources/X.md|X]]; '
                        '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 5]]).')
            assert cw.check_pagination_registration(wiki_root=self.tmp / '1-wiki') == []

    def test_registration_one_finding_per_raw(self) -> None:
        with mock.patch.object(cw, 'PAGINATION_MAP', {}):
            _write_page(self.tmp, 'concepts', 'c.md', CONCEPT_FM,
                        '> - a ([[1-wiki/sources/X.md|X]]; '
                        '[[0-raw/papers/X.pdf#page=5|sec. 3, p. 5]]).\n'
                        '> - b ([[1-wiki/sources/X.md|X]]; '
                        '[[0-raw/papers/X.pdf#page=6|sec. 4, p. 6]]).')
            f = cw.check_pagination_registration(wiki_root=self.tmp / '1-wiki')
            assert len(f) == 1   # one per raw, not per citation


if __name__ == '__main__':
    unittest.main()
