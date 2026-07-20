#!/usr/bin/env python3
"""Standalone backstop: is a cited numeric figure actually on the cited page?

A detect-only check for the cross-source mis-location defect (CLAUDE.md ->
Source Support And Verification, the multi-source-bullet rule): a true,
well-formed claim carrying a distinctive figure is cited to a raw `#page=N`
deep-link whose page does not carry that figure. The claim reads correctly and
passes every structural check in `check_wiki.py`; only opening the cited page
reveals the number is not there.

This lives OUTSIDE `check_wiki.py`'s battery on purpose. `check_wiki.py` never
opens a raw source (lint/SKILL.md Limits: "Lint does not read raw source
content"); this script does, so it is a separate, opt-in tool the agent runs
deliberately, not part of the structural lint pass. It requires PyMuPDF
(`fitz`), installed in the `llm-wiki` conda env by setup.sh.

Scope and policy:
- Detect-only, NEVER auto-fix. Like a mislabelled-locator finding, the check
  cannot tell which half is wrong — the figure, the page, or the source — so it
  flags for a human or `audit` to open the cited page and settle it.
- Numeric figures only, and only DECIMALS and PERCENTAGES (`37.2`, `37.2%`,
  `40%`). Bare integers are skipped: they recur everywhere and would flood the
  output with false positives. Locator machinery (`sec. 3.1`, `p. 4`,
  `#page=4`) sits inside a masked-out `[[...]]` span, so a section number is
  never read as a claim figure.
- A figure on a bullet is "off page" only when it appears on NONE of that
  bullet's cited raw pages, and only when every cited page was readable. A
  multi-source bullet citing two pages passes if the figure is on either; it
  flags only when the figure is on neither — the mis-location signature.
- The presence test is deliberately generous (whitespace-tolerant, matches the
  decimal core of a percentage), so the check errs toward "present": a false
  "present" quietly drops a finding, which is safer for a backstop than a false
  "absent" that cries wolf.
- It cannot catch a mislocated QUALITATIVE claim (no figure to match). That is
  ingest's and audit's job; this backstop settles only the numeric subset a
  script can settle.

Output: JSON list of findings ({check_id, severity, file, line, message}) to
stdout, mirroring `check_wiki.py`. `severity` is always `warning` (detect-only).
Exit code 0 normally; 2 on a usage error (bad wiki path); 3 if PyMuPDF is
missing (so a caller distinguishes "check could not run" from "found nothing").
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CHECK_ID = 'cited_figure_off_page'
SEVERITY = 'warning'

# Wiki page folders scanned (source, concept, entity, synthesis pages).
PAGE_DIRS = ('sources', 'concepts', 'entities', 'syntheses')

# A raw-source deep-link: group 1 = repo-relative raw path, group 2 = physical
# page N, group 3 = display text. Widens check_wiki.py's CITATION_DEEPLINK_RE to
# also capture the path and page so the raw can be opened at N.
DEEPLINK_RE = re.compile(r'\[\[(0-raw/[^\]|#]+)#page=(\d+)\|([^\]]*)\]\]')

# Inline-code and wikilink spans, blanked out of a bullet before figures are
# read, so a locator (`sec. 3.1`, `p. 4`), a link path/display, or a code
# snippet is never mistaken for a claim figure.
CODE_SPAN_RE = re.compile(r'`[^`]*`')
WIKILINK_RE = re.compile(r'\[\[[^\]]*\]\]')

# A distinctive numeric figure: a percentage (integer or decimal) or a bare
# decimal. The lookbehind for a word char, dot, or hyphen — plus the `(?!\.\d)`
# lookahead on the decimal arm — keeps a version or model id (`gpt-3.5`, `v2.0`,
# `3.1.4`) from reading as a figure, while `(?!\.\d)` still admits a
# sentence-final `37.2.` (a dot NOT followed by a digit). A bare integer (no
# dot, no `%`) is out of scope by construction.
FIGURE_RE = re.compile(
    r'(?<![\w.\-])\d+(?:\.\d+)?%'              # percentage: 40% or 37.2%
    r'|(?<![\w.\-])\d+\.\d+(?![\w%])(?!\.\d)'  # decimal 37.2, not 3.1.4
)


def mask_spans(*, line: str) -> str:
    """Blank inline-code and wikilink spans so their digits are not read as
    claim figures. Each span becomes spaces of equal length to keep offsets
    stable.
    """
    def blank(match: re.Match[str]) -> str:
        return ' ' * len(match.group(0))

    return WIKILINK_RE.sub(blank, CODE_SPAN_RE.sub(blank, line))


def extract_figures(*, line: str) -> list[str]:
    """Return the distinctive numeric figures in a bullet's prose, with locator
    machinery and code already masked out.
    """
    return FIGURE_RE.findall(mask_spans(line=line))


def extract_deeplinks(*, line: str) -> list[tuple[str, int]]:
    """Return (raw_relative_path, physical_page_n) for each raw deep-link on a
    bullet.
    """
    return [(m.group(1), int(m.group(2))) for m in DEEPLINK_RE.finditer(line)]


def figure_present(*, token: str, page_text: str) -> bool:
    """Whether a numeric figure appears in a page's extracted text.

    Generous by design (whitespace-tolerant; matches the decimal core of a
    percentage) so the check errs toward "present". A false "present" drops a
    finding — the safe direction for a detect-only backstop — whereas a false
    "absent" would cry wolf.
    """
    core = token.rstrip('%')
    stripped = re.sub(r'\s+', '', page_text)
    return any(c in page_text or c in stripped for c in {token, core})


class RawTextCache:
    """Lazily opens raw PDFs and caches extracted page text across a run.

    Attributes
    ----------
    repo_root : Path
        Repository root; raw deep-link paths resolve against it.
    """

    repo_root: Path

    def __init__(self, *, repo_root: Path) -> None:
        self.repo_root = repo_root
        self._docs: dict[str, Any] = {}
        self._pages: dict[tuple[str, int], str | None] = {}

    def page_text(self, *, raw_rel: str, page_n: int) -> str | None:
        """Return the text of physical page `page_n` (1-indexed) of a raw PDF,
        or None if the file is missing, is not a readable PDF, or has no such
        page. None means "cannot check", not "figure absent".
        """
        key = (raw_rel, page_n)
        if key not in self._pages:
            self._pages[key] = self._extract(raw_rel=raw_rel, page_n=page_n)
        return self._pages[key]

    def _extract(self, *, raw_rel: str, page_n: int) -> str | None:
        import fitz  # local import so --help works without PyMuPDF

        if not raw_rel.lower().endswith('.pdf'):
            return None
        doc = self._docs.get(raw_rel)
        if doc is None:
            raw_path = self.repo_root / raw_rel
            if not raw_path.exists():
                return None
            try:
                doc = fitz.open(raw_path)
            except (RuntimeError, OSError, ValueError):
                # A real open failure (encrypted, corrupt, not really a PDF —
                # fitz.FileDataError / EmptyFileError subclass RuntimeError) is
                # "cannot check", the safe direction — not a claimed absence. A code
                # bug (AttributeError/NameError/…) still propagates rather than
                # masquerading as cannot-check (mirrors the _git_show_head narrowing).
                return None
            self._docs[raw_rel] = doc
        if page_n < 1 or page_n > doc.page_count:
            return None
        try:
            return doc.load_page(page_n - 1).get_text()
        except (RuntimeError, OSError, ValueError):
            # Real page-load/parse failure is "cannot check"; a code bug propagates.
            return None


def check_page(
    *,
    path: Path,
    repo_root: Path,
    cache: RawTextCache,
) -> list[dict[str, Any]]:
    """Scan one wiki page for cited figures on none of a bullet's cited pages.

    Only flags a bullet whose cited pages were all readable, so an unreadable
    raw never produces a false "off page" finding.
    """
    findings: list[dict[str, Any]] = []
    rel = path.relative_to(repo_root).as_posix()
    for line_no, line in enumerate(path.read_text(encoding='utf-8').split('\n'),
                                   start=1):
        deeplinks = extract_deeplinks(line=line)
        figures = extract_figures(line=line)
        if not deeplinks or not figures:
            continue
        texts = [cache.page_text(raw_rel=r, page_n=n) for r, n in deeplinks]
        if any(text is None for text in texts):
            # A cited page is unreadable — cannot rule out presence there.
            continue
        cited = ', '.join(f'{r}#page={n}' for r, n in deeplinks)
        for token in dict.fromkeys(figures):
            if any(figure_present(token=token, page_text=t) for t in texts):
                continue
            findings.append({
                'check_id': CHECK_ID,
                'severity': SEVERITY,
                'file': rel,
                'line': line_no,
                'message': (
                    f'cited figure `{token}` appears on none of the cited '
                    f'pages for this bullet ({cited}); open the cited page and '
                    f'confirm the figure or the locator (detect-only, not '
                    f'auto-fixed — the check cannot tell which is wrong)'
                ),
            })
    return findings


def iter_pages(*, wiki_root: Path) -> list[Path]:
    """Return the wiki `.md` pages to scan, sorted, across the page folders."""
    pages: list[Path] = []
    for sub in PAGE_DIRS:
        folder = wiki_root / sub
        if folder.is_dir():
            pages.extend(sorted(folder.glob('*.md')))
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Detect cited numeric figures absent from their cited '
                    'raw page (cross-source mis-location backstop).')
    parser.add_argument(
        'wiki_root', nargs='?', default='1-wiki',
        help='path to the wiki root (default: 1-wiki)')
    args = parser.parse_args(argv)

    wiki_root = Path(args.wiki_root).resolve()
    if not wiki_root.is_dir():
        print(f'error: wiki root not found: {wiki_root}', file=sys.stderr)
        return 2
    repo_root = wiki_root.parent

    try:
        import fitz  # noqa: F401
    except ImportError:
        print(
            'error: PyMuPDF (fitz) is required and not installed. Run '
            '`conda activate llm-wiki` (setup.sh provisions it). The '
            'cited-figure check could not run.',
            file=sys.stderr)
        return 3

    cache = RawTextCache(repo_root=repo_root)
    findings: list[dict[str, Any]] = []
    for page in iter_pages(wiki_root=wiki_root):
        findings.extend(check_page(path=page, repo_root=repo_root, cache=cache))

    print(json.dumps(findings, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
