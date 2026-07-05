# Attachment extraction and page-offset reference

Read this when Step 4 extracts an image or Step 5 writes a page locator. The load-bearing one-liners (the offset formula, the rename rule) live in the steps themselves; this file holds the worked examples and the crop-tuning loop, which are needed only when an extraction actually happens.

## Physical-Page Offset (for `#page=N` Deep-Links)

Every page locator on a source page deep-links the raw file at its physical PDF page: `[[0-raw/papers/{stem}.pdf#page=N|p. 525]]`. `N` is the physical page (the Nth page of the file), not the printed page number on the paper.

- Compute it: open the PDF, read the printed page number on its first physical page, then `N = printed − (first_printed − 1)`.
- A paper printed from page 1 has `N = printed`. A proceedings paper printed from p. 512 has offset 511, so printed p. 525 is physical `N = 14`.
- Do not infer the offset from the cited range — the cited range need not start at the paper's first page.

## Crop-Tuning Loop (Figures, Tables, Equation Renders)

A crop must contain the full figure plus its full caption — including the figure/table label (the `Figure N` / `Table N` identifier line), which is part of the caption and ties the image back to its `fig. N` / `tab. N` locator — and nothing else: no body text, footnotes, or running headers in the crop window.

**Preferred — PyMuPDF point-space clip.** Crop by PDF coordinate, not by eye — a pixel box eyeballed off a full-page raster and hand-scaled by DPI clips captions and grabs headers. Open the page in PyMuPDF (`fitz`) and build the figure's bounding box in point-space: find the caption block by matching block text against `^\s*(Figure|Fig\.?|Table)\s*N\b`, merge its continuation blocks downward, then union it with the figure graphics above the caption or beside it (a narrow figure's caption sits to the side, not below). Exclude stray rects first — the page frame (height ≥ 700 pt), hairline rules (height < 3 pt), and anything larger than ~0.6 of the page — or they balloon the box; for a multi-panel figure capture every panel, not just the one nearest the caption. Render exactly that clip with a small pad: `page.get_pixmap(clip=rect, dpi=300)`, where `rect` is a `fitz.Rect` in points. A point-space clip needs no DPI-pixel arithmetic and no printed-vs-physical page math (that offset only matters for `#page=N` locators).

**Fallback — render then crop with `magick`** (packed grids or staggered single-figure rows that defeat the automatic clustering; crop one figure at a time):

1. Render the page first: `pdftoppm -png -r 300 -singlefile -f {page} -l {page} "{raw}" {outprefix}` — `-singlefile` writes exactly `{outprefix}.png` (plain `pdftoppm` zero-pads the page-number suffix to the document's digit width, so `{outprefix}-{page}.png` misnames the file on a 100+-page PDF).
2. Open the rendered page and read the figure's bounding box in pixels.
3. Crop with `magick "{outprefix}.png" -crop {W}x{H}+{X}+{Y} +repage "{name}.png"` (W×H is the box size; +X+Y is the top-left offset).
4. Re-open the crop. If it clips the caption or includes unrelated text, adjust the box and re-crop.

Notes:
- `magick` crop coordinates are in pixels and scale with `-r` DPI. A box read off one DPI render is wrong against a different-DPI render — read and crop at the same DPI. (The PyMuPDF point-space clip above sidesteps this — point coordinates are DPI-independent.)
- Use `magick` for both region crops (arbitrary `+X+Y` offset) and whole-image resize/convert — it targets an exact offset, unlike centred-crop tools.
- `pdfimages -png -f {page} -l {page} "{raw}" {outprefix}` pulls an embedded image directly (best when the figure is a single embedded raster, no crop needed). It writes indexed names (`{outprefix}-000.png`) and may emit `.ppm`/`.pbm` for non-RGB images despite `-png` — convert with `magick in.ppm out.png` and rename to the approved attachment filename before embedding (see Step 4).

## On Extraction Failure

If extraction fails (encrypted PDF, vector-only figure that rasterizes blank, copy fails on a missing/permission-denied media file), report it in Step 4 rather than silently skipping. The user can drop the embed, accept a locator-only reference, request a different render, or supply a manual screenshot placed in `1-wiki/attachments/{stem}/`.
