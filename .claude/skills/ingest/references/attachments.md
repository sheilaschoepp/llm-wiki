# Attachment extraction and page-offset reference

Read this when Step 4 extracts an image or Step 5 writes a page locator. The load-bearing methods (the Step-2 pagination map for what each page prints, the Step-5 rename rule) live in the steps themselves; this file holds the worked examples and the crop-tuning loop, which are needed only when an extraction actually happens.

## Physical-Page Offset (for `#page=N` Deep-Links)

Every page locator on a source page deep-links the raw file at its physical PDF page, with the structural anchor and printed page together inside the display: `[[0-raw/papers/{stem}.pdf#page=14|sec. 5, p. 525]]`. `N` (here `14`) is the physical page (the Nth page of the file), not the printed page number; the display carries both an anchor (`sec.`/`fig.`/`app.`/…) and the printed page `p. M` — a page-only display (`|p. 525]]`) is what lint `source_locator_incomplete` flags.

- Printed page `p. M` comes off the Step-2 pagination map (`.claude/skills/multi-skill/pagination-map.md`), the per-physical-page record of what each page prints — not a re-derived offset, which a restarting appendix would defeat (`CLAUDE.md` → Source Support And Verification). Where the map says a page prints nothing, drop `p. M` and cite the structural anchor alone.
- Physical page `N`: open the PDF, read the printed number on its first physical page, then `N = printed − (first_printed − 1)` (a paper printed from page 1 has `N = printed`; a proceedings paper printed from p. 512 has offset 511, so printed p. 525 is physical `N = 14`). Do not infer the offset from the cited range — it need not start at the paper's first page. This offset is the fallback only for an unregistered raw with no pagination-map entry; the map is authoritative wherever it exists. The offset holds only where the PDF paginates linearly from its first numbered page — confirm that by reading the printed folio on the cited page itself. Where you cannot read one (a full-page figure, a part divider, a restarting appendix), do not compute a number: register the raw in Step 2, or cite the structural anchor alone.

## Crop-Tuning Loop (Figures, Tables, Equation Renders)

A crop must contain the full figure plus its full caption — including the figure/table label (the `Figure N` / `Table N` identifier line), which is part of the caption and ties the image back to its `fig. N` / `tab. N` locator — and nothing else: no body text, footnotes, or running headers in the crop window.

**Preferred — PyMuPDF point-space clip.** Crop by PDF coordinate, not by eye — a pixel box eyeballed off a full-page raster and hand-scaled by DPI clips captions and grabs headers. Open the page in PyMuPDF (`fitz`) and build the figure's bounding box in point-space: find the caption block by matching block text against `^\s*(Figure|Fig\.?|Table)\s*N\b`, merge its continuation blocks downward, then union it with the figure graphics above the caption or beside it (a narrow figure's caption sits to the side, not below). Exclude stray rects first — the page frame (height at least 700 pt), hairline rules (height under 3 pt), and anything larger than ~0.6 of the page — or they balloon the box; for a multi-panel figure capture every panel, not just the one nearest the caption. Render exactly that clip with a small pad: `page.get_pixmap(clip=rect, dpi=300)`, where `rect` is a `fitz.Rect` in points. A point-space clip needs no DPI-pixel arithmetic and no printed-vs-physical page math (that offset only matters for `#page=N` locators).

**Union both graphics sources — a vector-only box misses every raster-only figure.** A figure's graphics come from two independent PyMuPDF calls, and either can be empty: `page.get_drawings()` returns vector rects, `page.get_image_rects(xref)` (over `page.get_images(full=True)`) returns embedded-raster placements. A photographic or screenshot figure has raster panels and **no** vector drawings at all, so a box built from `get_drawings()` alone silently returns the caption and whatever vector rules sit near it — a crop that still looks plausible because the caption is intact. Union both sources before taking the extent.

**Apply the stray-rect exclusions to vector rects only.** Those three tests (page frame, hairline, larger than ~0.6 of the page) describe clip-path and background artifacts that `get_drawings()` produces; an embedded raster placement is not one. A full-page screenshot figure trips both the height and the area test, so running the exclusions over raster rects drops exactly the figure that has no vector rects to fall back on. Filter vector rects, keep every raster rect, then union.

**Confirm the crop by coordinate, never by glance** (`CLAUDE.md` → Attachments makes this mandatory, not optional). The check that matters is **independent of the box-building step**: re-collect the page's candidate rects fresh, then test the clip against them. Asserting that the clip contains the union it was *built from* is a tautology — it passes on every crop, including the caption-only crop a missed raster panel produces, which is the one failure this check exists to catch.

```python
MARGIN = 2.0    # pt; a flush edge shaves anti-aliased strokes at render
NEAR = 40.0     # pt; a figure panel this close to the clip probably belongs to it

vec = [d['rect'] for d in page.get_drawings()]
vec = [r for r in vec if r.height < 700 and r.height >= 3
       and r.get_area() <= 0.6 * page.rect.get_area()]
ras = [r for x in page.get_images(full=True) for r in page.get_image_rects(x[0])]

probe = clip + fitz.Rect(-MARGIN, -MARGIN, MARGIN, MARGIN)
near_probe = clip + fitz.Rect(-NEAR, -NEAR, NEAR, NEAR)

# A raster that covers the whole clip is the page substrate of a scan, not a panel.
substrate = [r for r in ras if r.contains(clip)]
candidates = [r for r in vec + ras if not any(r == s for s in substrate)]

if substrate and not candidates:
    raise ValueError(f'page {page.number}: the only graphics is a full-page raster — a scanned '
                     f'page carries no figure-level coordinates, so this check cannot run. Use '
                     f'the render-then-crop fallback and verify the crop visually.')
if not candidates:
    raise ValueError(f'page {page.number}: no figure graphics found — '
                     f'clip {clip} would be caption-only')

near = []
for r in candidates:
    if r.intersects(clip) and not probe.contains(r):
        raise ValueError(f'clip {clip} straddles rect {r} — panel cut')
    if not r.intersects(clip) and near_probe.intersects(r):
        near.append(r)

if near:
    print(f'page {page.number}: resolve {len(near)} near rect(s) '
          f'before rendering: {near}')

if not probe.contains(caption_rect):
    raise ValueError(f'clip {clip} does not contain caption {caption_rect}')
```

Each test names a distinct failure: no candidates at all means the box collapsed onto the caption; a rect crossing the boundary means a panel is cut in half; a rect just outside means a panel may have been left behind (the multi-panel and side-set-caption cases). `raise`, not bare `assert` — `assert` is stripped under `python -O`, and a narrow `ValueError` says which test failed (`a-archive/style/coding-best-practices.md` → Error handling).

**The substrate exemption is why a scan is a different job.** On a scanned page the entire page is one raster placement, so it covers every clip you could take and would trip the straddle test on every valid crop. It is also the honest signal that coordinate isolation has nothing to work with: there are no figure-level rects to find, only pixels. Take the render-then-crop fallback below and confirm the crop by eye against the caption, and say so in the Step 8 report — do not delete the substrate rect and let the remaining tests certify a crop they never examined.

**The near-miss list is resolved, not raised.** `candidates` holds every surviving vector rect, which on a text page includes table borders, boxed sidebars, and an unrelated adjacent diagram, so a hard failure here would fire on most multi-element pages and the only satisfiable move would be an over-crop. Instead every rect in `near` is resolved before rendering: widen the clip when it is genuinely part of the figure, or record in the Step 8 report the position reading against the caption band that shows it is unrelated. An unresolved `near` entry blocks the render as surely as a raised test. Do not silence it by shrinking `NEAR` to zero — that restores the tautology.

A straddle, caption, or no-candidates failure means the box is wrong — widen it and re-run the checks, at most three times. The substrate raise is not a box error and no widening clears it: take the render-then-crop fallback instead. Widening is not free: if containment is reachable only by a clip that also swallows body text, footnotes, or the running header, the figure cannot be isolated by coordinate. Stop and treat it as an extraction failure (On Extraction Failure, below; Step 4 puts the fallback to the user) rather than shipping an over-crop that passes. Only then render. One rendered view afterwards is a sanity check on the *content* (right figure, no adjacent-column text), not the containment test.

**Fallback — render then crop with `magick`** (packed grids or staggered single-figure rows that defeat the automatic clustering; crop one figure at a time):

1. Render the page first: `pdftoppm -png -r 300 -singlefile -f {page} -l {page} "{raw}" {outprefix}` — `-singlefile` writes exactly `{outprefix}.png` (plain `pdftoppm` zero-pads the page-number suffix to the document's digit width, so `{outprefix}-{page}.png` misnames the file on a 100+-page PDF).
2. Open the rendered page and read the figure's bounding box in pixels.
3. Crop with `magick "{outprefix}.png" -crop {W}x{H}+{X}+{Y} +repage "{name}.png"` (W×H is the box size; +X+Y is the top-left offset).
4. Re-open the crop. If it clips the caption or includes unrelated text, adjust the box and re-crop. Even on this path the containment test is by coordinate: convert the pixel box back to points (`pt = px × 72 / dpi`) and run the same assertion before accepting the crop — the visual re-open catches wrong-figure and stray-text errors, not a partial clip. The exception is a scanned page, which routed here precisely because the substrate raise fires on every clip: there the eye-check against the caption is the whole check, and the Step 8 report says so.

Notes:
- `magick` crop coordinates are in pixels and scale with `-r` DPI. A box read off one DPI render is wrong against a different-DPI render — read and crop at the same DPI. (The PyMuPDF point-space clip above sidesteps this — point coordinates are DPI-independent.)
- Use `magick` for both region crops (arbitrary `+X+Y` offset) and whole-image resize/convert — it targets an exact offset, unlike centred-crop tools.
- `pdfimages -png -f {page} -l {page} "{raw}" {outprefix}` pulls an embedded image directly (best when the figure is a single embedded raster, no crop needed). It writes indexed names (`{outprefix}-000.png`) and may emit `.ppm`/`.pbm` for non-RGB images despite `-png` — convert with `magick in.ppm out.png` and rename to the approved attachment filename before embedding (see Step 4).

## On Extraction Failure

If extraction fails (encrypted PDF, vector-only figure that rasterizes blank, copy fails on a missing/permission-denied media file), report it in Step 4 rather than silently skipping. The user can drop the embed, accept a locator-only reference, request a different render, or supply a manual screenshot placed in `1-wiki/attachments/{stem}/`.
