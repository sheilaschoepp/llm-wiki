#!/usr/bin/env python3
"""Propose a pagination-map section for a raw PDF: what printed page number each
physical page shows, read from the page header and footer.

The pagination map (`.claude/skills/multi-skill/pagination-map.md`) records a fact the
locator checks depend on — what each physical page PRINTS — that is not
derivable by rule (proceedings offsets, appendices that restart, unpaginated
pages). This script PROPOSES that map from the PDF's headers and footers; it does not write
the data file. A human confirms each line against the page before it lands,
because a wrong `none` would license stripping a correct printed page from a
citation and certifying the damage. The proposer is a starting point, never the
authority.

Usage:
    pagination_map.py <raw.pdf>                 # print a proposed `## <raw>` section
    pagination_map.py --verify <raw.pdf> <dir>  # render header/footer crops for eyeballing

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
        'env (`conda activate llm-wiki`) or install it (`pip install pymupdf`).\n'
    )
    raise SystemExit(3)

# Fraction of page height at each vertical edge treated as the page-margin band
# where a printed folio may sit.
MARGIN_BAND = 0.10
# A margin LINE that is nothing but a page number — the strongest signal, since
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
        return '/'.join(parts[parts.index('0-raw') :])
    return str(pdf)


def margin_text(page: 'fitz.Page', *, position: str) -> str:
    r = page.rect
    if position == 'header':
        band = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * MARGIN_BAND)
    elif position == 'footer':
        band = fitz.Rect(r.x0, r.y1 - r.height * MARGIN_BAND, r.x1, r.y1)
    else:
        raise ValueError(f'unknown margin position: {position}')
    return page.get_text('text', clip=band)


def propose_candidates(margin: str) -> list[str]:
    """Return distinct bare-number candidates from one page margin.

    Prefer arabic-number lines; use roman-numeral lines only when no arabic
    candidate exists. Preserve every distinct candidate so an equation number
    or reference year cannot silently beat the real folio by appearing first.
    """
    arabic: list[str] = []
    roman: list[str] = []
    for line in margin.splitlines():
        tok = line.strip().strip(_STRIP)
        if not tok:
            continue
        if ARABIC_LINE_RE.match(tok):
            arabic.append(tok)
        elif ROMAN_LINE_RE.match(tok):
            roman.append(tok.lower())
    candidates = arabic or roman
    return list(dict.fromkeys(candidates))


def reconcile_candidates(*, header: list[str], footer: list[str]) -> str:
    """Combine header/footer proposals without silently resolving a conflict.

    `review(...)` is intentionally not a valid pagination-map value. If a user
    pastes an unresolved proposal, the map parser skips that line rather than
    certifying either candidate.
    """
    # A bare roman-numeral-looking token may be an isolated diagram/section
    # label (`i`, `v`, `c`, `d`, ...). When either margin contains an arabic
    # candidate, ignore roman candidates across both margins. Roman candidates
    # remain available for genuinely roman-paginated front matter where no
    # arabic number is present.
    if any(candidate.isdigit() for candidate in [*header, *footer]):
        header = [candidate for candidate in header if candidate.isdigit()]
        footer = [candidate for candidate in footer if candidate.isdigit()]

    distinct = list(dict.fromkeys([*header, *footer]))
    if not distinct:
        return 'none'
    if len(distinct) == 1:
        return distinct[0]
    header_display = '|'.join(header) if header else 'none'
    footer_display = '|'.join(footer) if footer else 'none'
    return f'review(header={header_display},footer={footer_display})'


def propose(pdf: Path) -> str:
    doc = fitz.open(pdf)
    try:
        lines = [f'## {raw_key(pdf=pdf)}']
        for i in range(doc.page_count):
            page = doc[i]
            header = propose_candidates(
                margin=margin_text(page=page, position='header')
            )
            footer = propose_candidates(
                margin=margin_text(page=page, position='footer')
            )
            lines.append(
                f'- {i + 1} = '
                f'{reconcile_candidates(header=header, footer=footer)}'
            )
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
            header_band = fitz.Rect(
                r.x0, r.y0, r.x1, r.y0 + r.height * MARGIN_BAND
            )
            footer_band = fitz.Rect(
                r.x0, r.y1 - r.height * MARGIN_BAND, r.x1, r.y1
            )
            page.get_pixmap(clip=header_band, dpi=200).save(
                str(outdir / f'header-{i + 1:03d}.png')
            )
            page.get_pixmap(clip=footer_band, dpi=200).save(
                str(outdir / f'footer-{i + 1:03d}.png')
            )
    finally:
        doc.close()
    sys.stderr.write(
        f'Rendered {count} header/footer crop pairs to {outdir}\n'
    )


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == '--verify':
        verify(pdf=Path(args[1]), outdir=Path(args[2]))
        return 0
    if len(args) == 1 and not args[0].startswith('-'):
        print(propose(pdf=Path(args[0])))
        return 0
    sys.stderr.write(
        'usage: pagination_map.py <raw.pdf> | --verify <raw.pdf> <outdir>\n'
    )
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
