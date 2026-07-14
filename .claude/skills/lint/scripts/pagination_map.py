#!/usr/bin/env python3
"""Propose a pagination-map section for a raw PDF: what printed page number each
physical page shows, read from the page footer.

The pagination map (`.claude/skills/lint/pagination-map.md`) records a fact the
locator checks depend on — what each physical page PRINTS — that is not
derivable by rule (proceedings offsets, appendices that restart, unpaginated
pages). This script PROPOSES that map from the PDF's footers; it does not write
the data file. A human confirms each line against the page before it lands,
because a wrong `none` would license stripping a correct printed page from a
citation and certifying the damage. The proposer is a starting point, never the
authority.

Usage:
    pagination_map.py <raw.pdf>                 # print a proposed `## <raw>` section
    pagination_map.py --verify <raw.pdf> <dir>  # render footer crops to <dir> for eyeballing

Requires PyMuPDF (`fitz`), which ships in the `llm-wiki` conda env. Prints an
error and exits 3 if it is missing, rather than guessing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write(
        'pagination_map.py needs PyMuPDF (fitz); activate the llm-wiki conda '
        'env (`conda activate llm-wiki`) or install it (`pip install pymupdf`).\n')
    raise SystemExit(3)

# Fraction of page height, measured up from the bottom edge, treated as the
# footer band where a page number sits.
FOOTER_BAND = 0.10
# A footer LINE that is nothing but a page number — the strongest signal, since
# a printed folio usually sits alone. A number embedded in a sentence (a
# footnote, a year) is deliberately not matched.
ARABIC_LINE_RE = re.compile(r'^\d{1,5}$')
ROMAN_LINE_RE = re.compile(r'^[ivxlcdm]{1,7}$', re.IGNORECASE)
_STRIP = ' \t.,:;-–—[]()'


def raw_key(pdf: Path) -> str:
    """The path as it appears in a `#page=N` deep-link (`0-raw/...`): the tail
    from the first `0-raw` component, else the path as given."""
    parts = pdf.parts
    if '0-raw' in parts:
        return '/'.join(parts[parts.index('0-raw'):])
    return str(pdf)


def footer_text(page: 'fitz.Page') -> str:
    r = page.rect
    band = fitz.Rect(r.x0, r.y1 - r.height * FOOTER_BAND, r.x1, r.y1)
    return page.get_text('text', clip=band)


def propose_printed(footer: str) -> str:
    """The most plausible printed page number in a footer, or `none`. Prefers a
    footer line that is a bare arabic number, then a bare roman numeral."""
    arabic: list[str] = []
    roman: list[str] = []
    for line in footer.splitlines():
        tok = line.strip().strip(_STRIP)
        if not tok:
            continue
        if ARABIC_LINE_RE.match(tok):
            arabic.append(tok)
        elif ROMAN_LINE_RE.match(tok):
            roman.append(tok.lower())
    if arabic:
        return arabic[0]
    if roman:
        return roman[0]
    return 'none'


def propose(pdf: Path) -> str:
    doc = fitz.open(pdf)
    try:
        lines = [f'## {raw_key(pdf=pdf)}']
        for i in range(doc.page_count):
            lines.append(f'- {i + 1} = {propose_printed(footer=footer_text(page=doc[i]))}')
    finally:
        doc.close()
    return '\n'.join(lines)


def verify(pdf: Path, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    try:
        count = doc.page_count
        for i in range(count):
            page = doc[i]
            r = page.rect
            band = fitz.Rect(r.x0, r.y1 - r.height * FOOTER_BAND, r.x1, r.y1)
            page.get_pixmap(clip=band, dpi=200).save(
                str(outdir / f'footer-{i + 1:03d}.png'))
    finally:
        doc.close()
    sys.stderr.write(f'Rendered {count} footer crops to {outdir}\n')


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == '--verify':
        verify(pdf=Path(args[1]), outdir=Path(args[2]))
        return 0
    if len(args) == 1 and not args[0].startswith('-'):
        print(propose(pdf=Path(args[0])))
        return 0
    sys.stderr.write(
        'usage: pagination_map.py <raw.pdf> | --verify <raw.pdf> <outdir>\n')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
