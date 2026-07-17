# LLM Knowledge Base Schema

This is a personal LLM knowledge base for academic research. It is browsed in Obsidian and maintained with local agent skills.

`MEMORY.md` at the repo root holds stable, transferable cross-machine context about the user, the project, and feedback rules — exported from auto-memory so it travels with the repo. Treat its contents as point-in-time observations and verify against the current state of files before asserting them as fact. See **Memory tiers** below for how `MEMORY.md` relates to the per-skill memory files (`.claude/skills/<skill>/<skill>-memory.md`), the multi-skill memory file (`.claude/skills/multi-skill/multi-skill-memory.md`), and this `CLAUDE.md` schema file, and **Workflow Rules → Session start order** for when each is read.

The design is a hybrid: it borrows the three-layer pattern (immutable raw sources, an LLM-maintained markdown knowledge base, and a schema file driving an agent) from Andrej Karpathy's LLM knowledge base sketch, and the atomic, source-grounded, interlinked note discipline from Sönke Ahrens' smart-note method. The layers:

- `0-raw/` is immutable source material and remains the source of truth.
- `1-wiki/sources/` holds source pages: source-shaped records with summary and evidence pointers.
- `1-wiki/concepts/` and `1-wiki/entities/` hold concept/entity pages. Each concept/entity page explains one reusable idea in very simple language.
- `1-wiki/syntheses/` holds cross-source argument pages that serve as entry points into developed topics.
- `1-wiki/attachments/` holds figures and other images extracted from raw sources for embedding in wiki pages.
- `2-outputs/` holds dated working artifacts. Outputs are not part of the durable wiki until the user explicitly promotes them. Every `2-outputs/` kind is uncapped and never auto-pruned — `lint`, `consistency`, `audit`, `skill-linter`, `query`, `brief`, `compare`, `reflect`, `ingest`, `cleanup`, `skill-llm-council`, `forget`, `supersede`, `synthesis`, and the `forget/quarantine`/`supersede/preserve` preservation subfolders all retain every report and artifact they accumulate. No skill auto-prunes them — the `cleanup` skill surfaces deletion candidates (OS junk, superseded check reports, subject-orphaned reports, and aged artifacts) and removes them only file by file on the user's approval, so reports are removed only by deliberate user action. Historical `log.md` / `hot.md` links pointing into `2-outputs/` at reports that no longer exist on disk (deleted under the former retention cap, now lifted, or otherwise removed by hand) remain expected danglers, not lint findings.

The wiki is source-grounded, but concept/entity pages are not citation wallpaper: obvious bullets stay uncited and the `Sources` callout lists support once at the bottom, while a non-obvious factual claim carries an inline citation to the specific source it draws from, next to a locator identifying where in the source (see Source Support And Verification). Source pages remain the fullest home for exact page, section, and figure locators (especially in the Evidence section), but inline claim citations on concept/entity/synthesis pages now carry their own locator too.

## Directory Structure

```text
llm-wiki/
├── CLAUDE.md
├── MEMORY.md
├── README.md
├── setup.sh
├── 0-raw/
│   ├── articles/
│   ├── books/
│   ├── media/
│   ├── other/
│   └── papers/
├── 1-wiki/
│   ├── hot.md
│   ├── index.md
│   ├── log.md
│   ├── attachments/
│   ├── concepts/
│   ├── entities/
│   ├── sources/
│   └── syntheses/
├── 2-outputs/
│   ├── audit/
│   ├── brief/
│   ├── cleanup/
│   ├── compare/
│   ├── consistency/
│   ├── forget/
│   │   └── quarantine/
│   ├── ingest/
│   ├── lint/
│   ├── query/
│   ├── reflect/
│   ├── skill-linter/
│   ├── skill-llm-council/
│   ├── supersede/
│   │   └── preserve/
│   └── synthesis/
├── a-archive/
│   ├── about-me/
│   ├── palettes/
│   ├── reference/
│   └── style/
├── docs/
│   └── examples/
└── .claude/skills/
```

Folder prefixes (`0-`, `1-`, `2-`, `a-`) keep Obsidian sorted in workflow order.

`setup.sh` provisions the `llm-wiki` conda env the skills run against — PyMuPDF, ImageMagick, and Poppler (the ingest figure-extraction toolchain; see [Attachments](#attachments)). Run once with `bash setup.sh`, then `conda activate llm-wiki`.

## Page Filenames

Concept pages, entity pages, synthesis pages, and attachment files in `1-wiki/` use kebab-case lowercase: ASCII letters, digits, and hyphens. No spaces, no underscores, no uppercase, no camel-case.

**Source pages are the one exception:** the source-page filename matches the raw source stem exactly (preserving the raw's case, digits, and any internal punctuation that the OS allows), so the source page and the raw file share a basename and are easy to associate by eye. This overrides the kebab-case rule for source pages only — other wiki file types stay kebab-case.

The `0-raw/` folder is curated by the user and may use any naming the user chose.

Examples:

- Source page (matches raw stem): `1-wiki/sources/Vaswani2017AttentionIA.md` (paired with `0-raw/papers/Vaswani2017AttentionIA.pdf`)
- Source page (raw uses kebab-case): `1-wiki/sources/illustrated-transformer.md` (paired with `0-raw/articles/illustrated-transformer.md`)
- Concept page: `1-wiki/concepts/scaled-dot-product-attention.md`
- Entity page: `1-wiki/entities/ashish-vaswani.md`
- Synthesis page: `1-wiki/syntheses/attention-vs-recurrence.md`
- Attachment: `1-wiki/attachments/Vaswani2017AttentionIA/architecture-diagram.png`

Wikilinks always include the `.md` extension and use a pipe-rendered display name where the display reads naturally in context (see [Wikilink Format](#wikilink-format) below).

## Raw Sources

Raw files are curated by the user and never edited by the agent. Raw filenames may use any convention the user chose (bibkeys, original filenames, etc.) — the kebab-case rule applies only to wiki files.

- `0-raw/papers/<bibkey>.<ext>` for papers.
- `0-raw/books/<bibkey>.<ext>` for books, textbooks, and monographs.
- `0-raw/articles/<slug>.md` for captured web articles.
- `0-raw/media/<slug>.<ext>` or `0-raw/media/<slug>/` for images, figures, transcripts, slide decks, and attachments.
- `0-raw/other/<slug>` for datasets, code, correspondence, and unusual source types.

Paper bibkeys follow the user's own citation-key convention (e.g., `Vaswani2017AttentionIA`); the agent matches the raw stem exactly and never normalizes, shortens, or "corrects" it.

The source page filename matches the raw source stem exactly (extension dropped, case and punctuation preserved). This makes the source page and the raw file trivially associable by eye. The raw file is also linked explicitly via the `file:` frontmatter.

- `0-raw/papers/Vaswani2017AttentionIA.pdf` -> `1-wiki/sources/Vaswani2017AttentionIA.md`
- `0-raw/papers/Kingma2015AdamAM.pdf` -> `1-wiki/sources/Kingma2015AdamAM.md`
- `0-raw/articles/illustrated-transformer.md` -> `1-wiki/sources/illustrated-transformer.md`

The attachments folder for a source uses the same stem: `1-wiki/attachments/{source-stem}/`.

Long sources may be split by chapter or major section (`Vaswani2017AttentionIA-ch01`, `Vaswani2017AttentionIA-ch02`) when one source page would become too large.

## Wikilink Format

Every wikilink in the wiki — frontmatter values, callout bullets, inline prose, hot/index/log references — is path-qualified from the repo root and uses this form:

```text
[[folder/path/file.md|display name]]
```

- No whitespace around the pipe. Write `[[path|display name]]`, never `[[path | display name]]`. Obsidian renders the alias text verbatim, so a space after the pipe shows up as a leading space in the rendered display name (" display name"). The pipe separates target from display with no padding on either side; whitespace inside the display name itself is preserved as written.
- The target is the full repo-root-relative path including the `.md` extension (or the real extension, for attachments and raw files). Path-qualified targets are unambiguous even when two files share a basename — for example a markdown raw `[[0-raw/articles/illustrated-transformer.md]]` and its source page `[[1-wiki/sources/illustrated-transformer.md]]`, which share both basename and extension. Bare-basename wikilinks are not used anywhere in the wiki.
- Targets by page type:
    - Source page: `[[1-wiki/sources/<stem>.md|display]]`
    - Concept page: `[[1-wiki/concepts/<slug>.md|display]]`
    - Entity page: `[[1-wiki/entities/<slug>.md|display]]`
    - Synthesis page: `[[1-wiki/syntheses/<slug>.md|display]]`
    - Attachment embed: `![[1-wiki/attachments/<stem>/<file>.png]]`
    - Raw file (source-page `file:` frontmatter): `[[0-raw/<category>/<file>.<ext>]]`
    - Raw-file page citation (a page/section/figure locator): `[[0-raw/papers/<stem>.pdf#page=N|<anchor>, p. M]]`, where `N` is the physical PDF page for the cited printed page `M`, and the display carries a structural anchor (sec./app./ch./fig./tab./eq./def./thm./lem./prop./cor./alg.) plus the page — e.g. `[[0-raw/papers/Devlin2019BERTPO.pdf#page=1|sec. 1, p. 4171]]`. This is the located raw-file deep-link that pairs with a source-page wikilink in the two canonical citation forms; see [Source Support And Verification](#source-support-and-verification) for the forms and for how to map printed → physical pages.
    - Output reference (hot/index/log): `[[2-outputs/<kind>/<file>.md|display]]`
    - Section link (to a specific callout): `[[1-wiki/sources/<stem>.md#^<block-id>|display]]` — appends `#^<block-id>` to the page target to point at one section, e.g. `[[1-wiki/sources/Devlin2019BERTPO.md#^appraisal|Appraisal]]`.
- Section links target callout block IDs, not callout titles. Obsidian does not resolve `[[page#Section Title]]` for a callout, so use the `#^<block-id>` the page carries on that callout (see [Callout Block IDs](#callout-block-ids)). The block ID is the kebab-case of the callout title, so the section link is predictable: Evidence is `#^evidence`, Open Questions is `#^open-questions`, Disconfirming Evidence is `#^disconfirming-evidence`. When a reference points at a section but a clickable anchor is not wanted, naming the section in prose after a plain page link is also fine.
- The display name is what the reader sees. It is the un-dashed form of the filename, in the case that reads naturally where the wikilink sits:
    - Proper nouns and named systems use title case: `[[1-wiki/concepts/adaptive-moment-estimation.md|Adaptive Moment Estimation]]`, `[[1-wiki/concepts/bleu.md|BLEU]]`.
    - Common-noun terms use sentence case mid-sentence: `[[1-wiki/concepts/feed-forward-network.md|feed-forward network]]`, `[[1-wiki/concepts/bias-correction.md|bias correction]]`.
    - Sentence-initial uses leading capital: `[[1-wiki/concepts/attention-weights.md|Attention weights]] are produced...`
- Authors use the same convention with the display in the human-readable form: `[[1-wiki/entities/ashish-vaswani.md|Ashish Vaswani]]`.
- The pipe-rendered display is required on every wikilink. A bare path-qualified target renders the whole path, which is unreadable; the pipe is no longer optional. Attachment embeds are the one exception (see below).
- **Link every genuine reference to a page that exists.** When another page's subject — a concept, entity, synthesis, or source — is genuinely referred to in a page's prose, wikilink it on every occurrence, in every callout, not only its first use, so a reader in any section can navigate and so the link graph is complete. An existing page is never left as a plain-text mention where it is genuinely referenced. Exceptions: the page's own subject/title (a page does not link to itself), generic wording that is not actually referencing that page (a judgement call), and text inside quote marks, verbatim, or inline code. A term whose page does not yet exist stays plain text — or a dangling link only on first use when it genuinely warrants a future page (see [Technical terminology](#technical-terminology)). `ingest` (draft) and `audit` (review) enforce this, and `lint`'s `unlinked_page_mention` check flags an existing page's title or alias appearing unlinked in another page's body.
- Attachment embeds are path-qualified and carry no pipe-rendered display: `![[1-wiki/attachments/<stem>/architecture-diagram.png]]`.
- File-reference wikilinks in source-page frontmatter point at the raw file, path-qualified into `0-raw/`: `file: "[[0-raw/papers/Vaswani2017AttentionIA.pdf]]"`, `file: "[[0-raw/articles/illustrated-transformer.md]]"`. The path prefix is what distinguishes a markdown raw from its same-named source page.

When a wikilink target page does not yet exist (a dangling link), the convention still applies — write the path as if the page already existed at its canonical location. Dangling links are acceptable when the term genuinely warrants a future page (see [Concepts and Entities](#concepts-and-entities)).

## Attachments

Figures, tables, and diagrams may be extracted from raw sources and embedded in wiki pages when they meaningfully clarify a claim, method, or result. Plain text usually suffices; reach for an image when a reader benefits from seeing it.

Storage and naming:

- One folder per source page at `1-wiki/attachments/{stem}/`, where `{stem}` matches the source-page filename.
- All attachment filenames are kebab-case lowercase (see Page Filenames).
- Embeds are path-qualified into the source's own `1-wiki/attachments/{stem}/` folder, so global basename uniqueness is no longer required for resolution. Descriptive names are still preferred for readability. Two acceptable styles:
  - Descriptive: `fig3-layouts.png`, `layout-cramped-room.png`, `architecture.png`.
  - Stem-prefixed: `architecture-diagram.png`, `attention-heads.png`.
- Bare `fig-1.png` / `fig-2.png` no longer collide across papers (the `{stem}/` folder in the path disambiguates), but descriptive names still read better in the link.
- PNG preferred. JPG acceptable for photographic content. SVG when the source provides native vector.
- Crops must contain the full figure and the full figure caption — including the figure/table label (the `Figure N` / `Table N` identifier line), which is part of the caption and is what ties the image back to its `fig. N` / `tab. N` locator — and nothing else. Trim out unrelated paragraph text, footnotes, or running headers that fall inside the crop window. Re-render with adjusted `pdftoppm -x -y -W -H` parameters until the crop is tight.

Embedding:

- Use path-qualified Obsidian embed syntax: `![[1-wiki/attachments/{stem}/fig3-layouts.png]]`, where `{stem}` is the source page's stem. The path makes the embed unambiguous regardless of basename reuse elsewhere in the vault.
- Source pages: any number of image embeds, placed inline in `Evidence` (for figures, tables, or charts that back a claim) or `Method` (for architecture diagrams or methodology figures that explain how the source works). Each embed sits on its own line, set off by a blank quoted line (`>`) both above and below it, so the embed is its own block and never lazy-continues the bullet above or the line below — Obsidian otherwise mis-renders an embed butted directly against surrounding callout content. The embed line is a single space after `>`, no indentation, no leading `- ` dash — neither a Markdown sub-bullet nor an indented code block (four or more spaces after `>` make the line a code block, which renders the raw `![[…]]` text instead of the image). The locator goes on the parent bullet directly above the upper blank line. Example:
  ```markdown
  > - fig. 4, p. 7: gap between baselines
  >
  > ![[1-wiki/attachments/{stem}/gap-chart.png]]
  >
  ```
  There is no separate Figures section — figures and evidence live together.
- Concept/entity pages: at most one defining image (e.g., the canonical architecture diagram for a method), placed inside `Idea`. Same no-leading-dash format as source pages. The image should illustrate the one reusable idea, not summarize a source. Do not place images in `Examples`.
- Synthesis pages: when comparing approaches visually, usually in `Evidence` or `Tensions`. Same no-leading-dash format.

Source-page frontmatter `attachments:` lists every extracted file as a path-qualified Obsidian wikilink:

```yaml
attachments:
  - "[[1-wiki/attachments/{stem}/fig3-layouts.png]]"
  - "[[1-wiki/attachments/{stem}/layout-cramped-room.png]]"
```

Extraction and cropping method:

Extraction uses PyMuPDF (`fitz`) and ImageMagick (`magick`), both installed in the `llm-wiki` conda env, plus Poppler's `pdftoppm` / `pdfimages`. Render and crop at 300 DPI (the older `pdftoppm -r 200` default is lower-resolution).

- Tools:
  - `pdftoppm -png -r 300 -f {page} -l {page} "{raw}" {outprefix}` renders a full page.
  - `pdfimages -png -f {page} -l {page} "{raw}" {outprefix}` pulls an embedded raster directly — best when the figure is a single embedded image needing no crop. It writes indexed names (`{outprefix}-000.png`) and may emit `.ppm`/`.pbm` for non-RGB images despite `-png`; convert with `magick in.ppm out.png` and rename to the approved filename before embedding.
  - `magick "{outprefix}-{page}.png" -crop {W}x{H}+{X}+{Y} +repage "{name}.png"` crops a pixel region (W×H is the box size; +X+Y the top-left offset). Preferred over `pdftoppm -x -y -W -H` for region crops; it also handles whole-image resize and format conversion.
  - PyMuPDF (`fitz`) crops by PDF coordinate: `page.get_pixmap(clip=rect, dpi=300)`, where `rect` is a `fitz.Rect` in PDF point-space. This is the most reliable path — point-space clips need no DPI-pixel arithmetic.
- Crop by coordinate, not by eye. Eyeballing a pixel box off a full-page raster and hand-scaling DPI is slow and error-prone (clipped captions, grabbed page headers, lost legends). Prefer the PyMuPDF point-space clip; when cropping a rendered raster with `magick`, pixel boxes scale with render DPI — a box read off a 200-DPI render is wrong against a 300-DPI render, so read and crop at the same DPI.
- Locating the figure box (PyMuPDF coordinate method):
  - Find the caption block by matching block text against `^\s*(Figure|Fig\.?)\s*N\b` (or `Table`). Merge its continuation blocks downward while the inter-block gap stays small (under ~18 pt) and they horizontally overlap (over ~0.4) — captions split across blocks, so one block's bbox clips the caption.
  - The caption is not always below the figure: for narrow two-column figures it sits beside the diagram. Include figure graphics that are either above the caption (within ~460 pt) or beside it (their y-range overlaps the caption's y-band), then union with the merged caption. Do not bound the figure by "graphics above the caption" alone — that drops a side-set figure's lower and left half.
  - Multi-panel figures are several disconnected graphics clusters with gaps between panels; a panel can sit far from the caption or behind another panel. Capture all panels, not just the nearest.
  - Exclude stray drawing rects before unioning: the page frame (height ≥ 700 pt), hairlines/rules (height < 3 pt), and any rect that extends beyond the page bounds or is larger than ~0.6 of the page — these are clip-path/background artifacts that otherwise balloon the figure bbox.
  - Pull in labels: text blocks that horizontally overlap the figure band (internal labels, any width), narrow blocks just above it within ~14 pt (subplot/figure titles), and narrow blocks just outside its left/right edge within ~14 pt (legends). Width-gate the title/legend inclusion (under ~120 pt) so full-width body lines and the running header never leak in.
  - Render the exact clip at 300 DPI with a small symmetric pad (~7 pt). Do not use a large top pad to chase a title — it grabs the header rule on a top-of-page figure; capture titles by content instead.
  - These point-space clips need no printed-vs-physical page math — that offset only matters for `#page=N` locators, not for extraction.
  - Packed grids (several small figures per row, or staggered single-figure rows) defeat the automatic clustering — a shared caption line or touching diagrams merge into one box. Fall back to the render→crop loop: render the page at 300 DPI and crop each figure with `magick` from element-bbox geometry and the caption-label positions, one figure at a time.
- The render→inspect→crop loop: render the page, read the figure's box, crop, then re-open the crop and check it. Adjust the box and re-crop until the crop holds the full figure (all panels, axes, legend), the full caption including the `Figure N` / `Table N` label, and nothing else (no page header or rule, no adjacent-column or body text).
- Double-check every crop before finalizing — by coordinates, not just a downscaled glance. Compute the figure's true graphics extent (the union of the stray-excluded figure-graphic bboxes, both above and beside the caption) and confirm the clip contains it on all four sides with a small margin; a downscaled visual glance misses a partial clip that the coordinate cross-check catches. Then confirm item by item: the whole figure (all panels, all axes, the full legend); the full caption (every line plus the `Figure N` / `Table N` label); and nothing extraneous (no page header or header rule, no adjacent-column text, no body paragraph above or below, no clipped title or legend). A plausible-looking crop that clips half a figure or grabs a header is a silent defect the later verification passes do not catch.
- On extraction failure (encrypted PDF, vector-only figure that rasterizes blank, a missing or permission-denied media file), report it rather than silently skipping — the embed can be dropped, replaced with a locator-only reference, re-rendered differently, or supplied as a manual screenshot placed in `1-wiki/attachments/{stem}/`.

Extraction is part of the `ingest` skill only (any mode — new or existing source, normal or deep). Other skills do not create new attachments. Attachments removed during `forget` or `supersede` follow the same quarantine rules as the source page they belong to.

## Body Sections As Callouts

Wiki page bodies use Obsidian callouts instead of H2 section headings:

```markdown
> [!idea] Idea
>
> - A short note body bullet.
> ^idea
```

The H1 (`# Page Title`) is a normal Markdown heading. Every required section appears even when empty. Empty placeholders:

- Source pages: `> - None noted`
- Concept/entity pages: `> - None yet`
- Synthesis pages: `> - None yet`

Empty placeholders are the correct content when a section has nothing genuine to say. Sections are not quotas. Do not invent content, paraphrase the same point across sections, or stretch a single bullet into multiple to avoid an empty placeholder. A page with several placeholders is fine; a page with padded sections is not.

### Callout Block IDs

Every callout carries a block ID, written as the last line inside the `>` block: `> ^idea`, `> ^key-claims`, `> ^open-questions`, and so on. This makes each section directly linkable. Obsidian does not anchor links to callout *titles* (`[[page#Idea]]` will not resolve), so the block ID is what enables section links — see [Wikilink Format](#wikilink-format).

- The block ID is the kebab-case of the callout's *display title* (the text after `[!type]`), not the callout type slug. For most callouts the two coincide (`[!idea]` Idea → `^idea`, `[!open-questions]` Open Questions → `^open-questions`), so the ID stays predictable from the section without opening the page, and is unique per page because each section appears once. Where the schema gave a callout an abbreviated *type*, the block ID still spells out the full title and the two diverge: `[!why]` Why It Matters → `^why-it-matters`, `[!disconfirming]` Disconfirming Evidence → `^disconfirming-evidence`, `[!what-would-change-this]` What Would Change This Answer → `^what-would-change-this-answer`. These three are the only divergences. The acronym title `[!tldr]` TL;DR keeps its compact `^tldr`. The callout *type* (the slug inside `[!...]`) is unchanged — it is what the Obsidian CSS keys on — and only the block ID expands to the title.
- Placement is the last line of the callout, still inside the blockquote, directly after the final content line (no blank `>` separator): see the `> ^idea` line in the example above. This placement attaches the ID to the whole callout box.
- The block ID does not render in reading view; it is invisible to the reader and exists only to anchor links.
- Every callout gets one, including empty-placeholder sections, so any section is linkable whether or not it currently has content.
- Adding or correcting a block ID is a mechanical edit that does not change a page's meaning. It is on the verification-neutral allowlist (see Page Status): a skill that adds or fixes a block ID on a `verified` page re-stamps `verified_hash:` in the same pass and the page stays `verified`. A block-ID edit made outside a skill that does not re-stamp still trips the body hash and resets the page to `draft` — the safe fallback.

### Required Callout Sections

Source pages:

1. `tldr` - TL;DR
2. `contribution` - Contribution
3. `key-claims` - Key Claims
4. `evidence` - Evidence
5. `method` - Method
6. `assumptions` - Assumptions
7. `limitations` - Limitations
8. `appraisal` - Appraisal
9. `concepts-entities` - Concepts and Entities
10. `contradictions` - Contradictions
11. `open-questions` - Open Questions
12. `connections` - Connections

Concept/entity pages:

1. `idea` - Idea
2. `why` - Why It Matters
3. `not-this` - Not This
4. `examples` - Examples
5. `contradictions` - Contradictions
6. `disconfirming` - Disconfirming Evidence
7. `open-questions` - Open Questions
8. `connections` - Connections
9. `sources` - Sources

Synthesis pages:

1. `question` - Question
2. `answer` - Answer
3. `scope` - Scope
4. `evidence` - Evidence
5. `tensions` - Tensions
6. `what-would-change-this` - What Would Change This Answer
7. `open-questions` - Open Questions
8. `connections` - Connections
9. `sources` - Sources

## Source Pages

Source pages summarize one source and preserve the audit trail needed to revisit it. They are allowed to be more detailed than concept/entity pages because they are evidence records.

Frontmatter:

```yaml
---
# identity
type: paper
title: "Attention Is All You Need"
authors:
  - "[[1-wiki/entities/ashish-vaswani.md|Ashish Vaswani]]"
venue: NeurIPS
year: 2017
# source location
file: "[[0-raw/papers/Vaswani2017AttentionIA.pdf]]"
attachments: []
# wiki metadata
tags: []
frames: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft
---
```

For non-paper sources, `type:` is `article`, `media`, or `other`. `url:` and `accessed:` may be added where useful. `venue:` is the venue or platform name only, never the year.

`frames:` is a list of lens texts. It is present on every source page and is empty (`frames: []`) when the page is unscoped — never omitted. When ingest is run with a frame (a short angle or lens scoping the summary), the exact frame text is appended here so a later ingest of the same source (existing-source mode) can recover and reuse it. A page may carry more than one frame: it is then scoped to the union of its frames, and faithfulness is judged against that union — content admitted by any listed frame is in scope, and items outside every frame are legitimately dropped, not gaps. The raw source is fully re-read on every ingest (see Workflow Rules), so reframing is additive: a reingest appends a new lens and the full re-read lets the body cover it, never deleting still-accurate content to swap a lens. Going fully unscoped (`frames: []`) widens the written scope to the whole source. Any scope-widening change — appending a lens or clearing to unscoped — obliges the reingest to write the newly in-scope content in the same pass (the full re-read makes it available) and resets the page to `status: draft`, because the body grows to match; a `frames:` value that claims more scope than the body actually covers is not allowed. A frame names what is in scope (a positive lens), not a hard exclusion: union is defined over positive scopes. Narrowing — dropping a lens while keeping its content — is not a reingest operation; use `forget` or `supersede`. The page body never references the frames — frontmatter only.

Source page rules:

- The whole page is scoped to its source, so bullets never self-cite (no wikilink to the page's own source page). But they are not citation-free: every non-obvious claim still carries its location — a raw-PDF `#page=N` deep-link whose display is the structural anchor and page (`[[0-raw/papers/<stem>.pdf#page=5|sec. 4, p. 5]]`), used as the sentence subject (`… indicates that …`) or as a trailing parenthetical. The source key is dropped because it would be a self-link; the locator alone is the citation. The author's own marked judgement (`Appraisal`, `Assumptions`, `Open Questions`) stays uncited.
- **Bullets paraphrase the source in plain language; verbatim text only inside quote marks paired with a locator.** Source pages are evidence records, not copy-paste from the raw file. A bullet that reads as a near-verbatim extract from the paper should be rewritten in the user's voice with the locator preserved.
- Use `Evidence` for precise pointers worth preserving. Image embeds (figures, tables, equation renderings) live inline in `Evidence` paired with their locator — there is no separate Figures section.
- Use `Method` for how the source arrived at its claims (empirical study, theoretical argument, case study, benchmark, historical analysis), implementation details (hardware, dataset, hyperparameters), and methodology or architecture diagrams that explain *how* the source works rather than backing a specific claim.
- Use `Assumptions` for premises the source's argument depends on, including ones the source doesn't state explicitly. Distinct from `Limitations` (the source's own acknowledged weaknesses) — assumptions are what gets taken for granted.
- Use `Limitations` for weaknesses the *source itself* acknowledges (e.g., "we did not test X", "results may not generalize beyond Y", "sample size was N=20"). Capture exactly what the authors flagged, in their voice (paraphrased), so future readers can separate the source's honesty from the user's judgement. Distinct from `Assumptions` (premises taken for granted, often unstated), `Appraisal` (your judgement), and `Contradictions` (cross-source disagreement).
- Use `Appraisal` for *your* judgement of trustworthiness: strength of evidence, possible bias, replication status, reasons to downgrade. Distinct from `Contradictions` (cross-source disagreement) and `Limitations` (the source's own admission).
- Keep direct quotes in the source page, not in concept/entity pages, unless the quote itself is the object of study.
- Link every concept/entity page the source supports in `Concepts and Entities`.
- Surface disagreements in `Contradictions`; do not blend them away. Contradictions records *active disagreement between independently-checkable sources* — what one source claims and another disputes. It is **not** for page provenance (how this page came to exist, what got split off from where), ingest or audit history ("this ingest split X off", "this reingest re-checked the distinction"), or status-transition reasons ("flagged needs-update to re-check"). Resolution notes, audit conclusions, and ingest commentary belong in the corresponding `2-outputs/audit/` or `2-outputs/ingest/` report, not on the wiki page. The page should read as the current state of the world, not its history.

Evidence pointer formats:

- Papers: `abstract, p. 1`, `p. 4`, `sec. 3.2, p. 5`, or `fig. 2, p. 6` (the front-matter `abstract` is a valid anchor — do not relabel abstract content as `sec. 1`, which on most papers is not even on the abstract's page)
- Articles: `sec. Heading`, `para. 12`
- Media: `slide 4`, `00:03:12`, `fig. 1`
- Other: stable row, section, label, or path

When an evidence bullet has an embedded image, put the locator on the parent bullet, then a blank quoted line (`>`), then the embed on its own line, then another blank quoted line (`>`) below it. The blank lines above and below set the embed off as its own block so Obsidian renders it correctly — an embed butted directly against the bullet above or the line below mis-renders. The embed line is a single space after `>`, no indentation, no leading `- ` dash, so it is neither a Markdown sub-bullet nor an indented code block (four or more spaces after `>` render the raw `![[…]]` instead of the image):

```markdown
> - fig. 4, p. 7: gap between baselines
>
> ![[1-wiki/attachments/{stem}/gap-chart.png]]
>
```

## Concepts and Entities

Concept and entity pages are reusable idea pages. They are not summaries of individual sources. Each page captures one reusable idea or named thing in simple language.

Concepts are abstractions: methods, ideas, hypotheses, metrics, phenomena.

Entities are proper-noun things: people, organizations, models, benchmarks, datasets, named systems. A named method may be either; prefer `concepts/` when the note is mostly about the idea, and `entities/` when it is mostly about the named artifact.

Frontmatter:

```yaml
---
# identity
type: concept
aliases: []
# source support
sources:
  - "[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]"
source_count: 1
# wiki metadata
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft
---
```

`aliases:` lists alternate names, acronyms, or older terminology for the same concept or entity. Obsidian uses it natively for search and `[[wikilink]]` autocomplete. Default empty; populate when the concept genuinely has alternate names ("Ashish Vaswani" / "Vaswani"; "Adam" / "Adaptive Moment Estimation"). No rendered Aliases section — frontmatter only.

Concept/entity page rules:

- One note, one idea. If a page needs two definitions, split it.
- Explain the idea in very simple terms, as if writing for a future tired version of the user.
- Use `Not This` to disambiguate against neighbouring concepts that get confused with this one ("similar concept X, but different because…"). Empty `> - None yet` placeholder is fine when the concept has no obvious neighbours.
- Use `Disconfirming Evidence` for observations, examples, or sources that cut against the concept as you've stated it — evidence you've noticed yourself that would push the concept toward needing revision. Distinct from `Contradictions` (which is cross-source disagreement *between* listed sources). This is the slot for actively-sought counterevidence: edge cases the concept doesn't handle, sources that disagree with the formulation, your own observations that don't fit. A bullet that draws on a source (a source that disagrees, a published counterexample, reported data) carries an inline citation to that source; a purely own observation with no source stays uncited. Empty `> - None yet` is fine.
- Do not cite obvious or definitional bullets, or the author's own judgement (`Appraisal`/`Open Questions`/`Assumptions`); the `sources:` frontmatter and `Sources` callout carry the page's overall support. But cite a non-obvious factual claim inline to the specific source it draws from (`[[1-wiki/sources/<stem>.md|<stem>]]`) — with several sources listed, the trail alone cannot show which one backs which claim. See Source Support And Verification.
- Avoid source-shaped sections like "What Source A Says." That belongs in source pages.
- Keep most concept/entity pages under 400 words.
- Use `Connections` to make the note useful in more than one context.
- If sources disagree, put the disagreement in `Contradictions` and set `status: needs-update` until resolved. Same scope rule as on source pages: Contradictions is for active cross-source disagreement, not page provenance, ingest/audit history, or status-transition reasons. Resolution notes live in the audit or reingest report, not on the page.
- **Author page creation policy.** On ingest, auto-link any author already in `1-wiki/entities/`. For an unlinked author, propose a new entity page only when the author is prominent in the area — recurring across the corpus, a well-known PI, or a named-system originator. One-off collaborators stay as dangling path-qualified wikilinks in `authors:` (e.g., `[[1-wiki/entities/noam-shazeer.md|Noam Shazeer]]` with no page yet); lint does not flag these danglers.

The `Sources` callout lists source pages only:

```markdown
> [!sources] Sources
>
> - [[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]
> - [[1-wiki/sources/Kingma2015AdamAM.md|Kingma2015AdamAM]]
```

## Synthesis Pages

Synthesis pages are durable cross-source argument pages and the main entry points into developed topics. They answer a reusable question, compare positions, preserve a debate map, or organize a cluster of concept/entity pages around a topic.

Frontmatter:

```yaml
---
# identity
type: synthesis
# source support
sources:
  - "[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]"
  - "[[1-wiki/sources/Kingma2015AdamAM.md|Kingma2015AdamAM]]"
source_count: 2
origin: "[[2-outputs/query/query-YYYY-MM-DD-HHMM-topic.md|query-YYYY-MM-DD-HHMM-topic]]" # or direct/query/brief/reflect/compare/synthesis-scan
# optional
single_source_stub: false  # optional; shown for reference — OMIT entirely on ≥2-source pages, present (as true) only for a deliberate single-source stub
# wiki metadata
tags: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft
---
```

`single_source_stub:` is optional and defaults to `false`. Lint warns when a synthesis page has exactly one source and this flag is not set to `true` — the schema requires synthesis pages to have at least two distinct sources (distinct underlying works; see the Synthesis rules below) unless the user explicitly creates a stub. Omit the field entirely on synthesis pages with ≥ 2 sources.

Synthesis rules:

- Must use at least two distinct sources, unless the user explicitly asks for a single-source synthesis stub. Distinct means distinct underlying works: chapter- or section-split source pages sharing a base stem (`X-ch01` / `X-ch02`), and two source pages whose `file:` resolves to the same raw, each count once — two chapters of one book do not clear the floor. `lint`'s `synthesis_under_supported` counts `len(sources)`, so a chapter-split pair passes the structural check; the distinct-works floor is enforced by `synthesis` at author/merge time.
- May be created from a focused topic request or from `/synthesis` discovery mode, which scans `hot.md`, `index.md`, and connected wiki pages for candidate topic entry points.
- Keep the answer clear and source-grounded.
- Use `Scope` to qualify *where* the answer applies — domains it covers, domains explicitly excluded, regimes the cross-source evidence does not yet reach. Synthesis pages aggregate sources and risk sounding more universal than they should; Scope keeps the answer honest.
- Use `Evidence` to name which source pages support which parts of the answer.
- Use `Tensions` for qualifications, counterevidence, and unresolved disagreements *that exist now* — both cross-source disagreement among the synthesis's listed sources *and* your own observations that cut against the answer as written. This is the synthesis-level home for actively-sought disconfirming evidence (concept/entity pages have a separate `Disconfirming Evidence` callout for the same purpose). A `Tensions` bullet that draws on a source carries an inline citation to that source, the same as any sourced counterevidence; a purely own observation stays uncited.
- Use `What Would Change This Answer` for *future* evidence that would invalidate or revise the answer — replication failures, counterexamples, simpler alternative explanations. Distinct from `Tensions` (present-tense pushback) and `Open Questions` (currently unanswered). Empty `> - None yet` placeholder is fine while the answer is still firming up.
- Do not create, update, or promote a synthesis without user approval. This binds the `synthesis` skill and user-initiated changes; `audit` is the standing exception — it fact-checks a synthesis page's content against its sources and applies the resulting fixes autonomously, preserving the prior version, exactly as on any other page (see Workflow Rules → the audit autonomy exception). Synthesis pages are left `status: draft` precisely for that later audit to validate.

## Source Support And Verification

The vault keeps provenance at the note level — the `sources:` frontmatter and `Sources` callout carry a page's overall support, and obvious or definitional bullets, plus the author's own marked judgement (`Appraisal`, `Open Questions`, `Assumptions`), need no inline citation. Sourced counterevidence in `Disconfirming Evidence` (concept/entity) or `Tensions` (synthesis) is cited like any non-obvious claim — it is left uncited only when it is a purely own observation with no source.

But on a multi-source page (concept/entity/synthesis), a **non-obvious factual claim carries an inline citation in one of two canonical forms**, chosen by the grammar of the sentence. Both pair the same two pieces: the source-page wikilink names *which* source (never the page itself; a page never cites or links to itself), and the located raw-source deep-link says *where* in it. Which form to use depends on whether the source is the grammatical subject of the sentence or the claim stands on its own:

- **Form 1 — attributive** (the source *does* something: it is the subject). The source-page wikilink is the subject, immediately followed by the locator in parentheses, then the verb:

  ```text
  [[1-wiki/sources/<stem>.md|<key>]] ([[0-raw/papers/<stem>.pdf#page=N|<anchor>, p. M]]) shows that …
  ```

  Renders as `<key> (<anchor>, p. M) shows that …`. The parenthetical holds only the locator deep-link (the key is already the subject). Worked: `[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]] ([[0-raw/papers/Vaswani2017AttentionIA.pdf#page=5|sec. 3.2, p. 5]]) shows attention scales quadratically with sequence length.`

- **Form 2 — parenthetical** (state the claim on its own terms, then cite). A trailing parenthetical reference closes the sentence: source-page wikilink, a semicolon, then the locator deep-link, all inside round brackets `(` `)`:

  ```text
  … attention scales quadratically with sequence length ([[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]; [[0-raw/papers/Vaswani2017AttentionIA.pdf#page=5|sec. 3.2, p. 5]]).
  ```

  Renders as `… sequence length (Vaswani2017AttentionIA; sec. 3.2, p. 5).`. The semicolon separates the key from the locator so the locator's own comma (`sec. 3.2, p. 5`) stays unambiguous. A claim drawn from more than one place in the same source lists each locator after the key, semicolon-separated, inside the one parenthetical: `(<key>; <locator 1>; <locator 2>)`.

Shared by both forms:

- **PDF source.** The locator is a `#page=N` raw-file deep-link whose display always carries **both** a structural anchor **and** a printed page. The anchor is a section/appendix (`sec. 3.2`, `app. C`), a figure/table/equation (`fig. 4`, `tab. 8`, `eq. 3`), a theorem-environment result (`def. 1`, `thm. 3.1`, `lem. 4.2`, `prop. 5`, `cor. 3.3`, `alg. 2`), or a named front-matter section (`abstract`); the page is `p. M`. `N` is the physical PDF page (see below), `M` the printed page. Cite abstract-drawn content as `abstract, p. 1` — never relabel it `sec. 1` (on most papers sec. 1 is not on the abstract's page).
- **Unpaginated region — keyed on the pagination map.** Many raws carry no printed page number over some region — most often a published supplement whose appendix prints no footer, sometimes a whole body that prints a number on only a page or two. There `p. M` cannot be stated honestly, so the locator **drops `p. M` and cites its structural anchor alone**: `[[0-raw/papers/<stem>.pdf#page=16|app. D.1, tab. 8]]` — the anchor is the locator, and `#page=N` still deep-links the physical page. This is a statement of fact about the raw, not a convenience: never resolve a missing `p. M` by writing the physical page as though it were printed, which fabricates a number no reader can find on the page (on a body-paginated paper it lands beside a genuine five-digit printed page from the same source). What each physical page actually prints is recorded per raw in the pagination map (`.claude/skills/lint/pagination-map.md`; see [Stay In Your Lane](#stay-in-your-lane)), and `lint` keys the exemption on it in both `citation_locator_incomplete` and `source_locator_incomplete`: a page the map says prints nothing may cite its structural anchor alone (any anchor, not only `app.`), a page the map says prints a number must give it, and `locator_page_mismatch` flags a `p. M` that contradicts what the page prints. A raw with no map entry falls back to the older heuristic — an `app.`-anchored display may omit the page, any other anchor still needs one — and raises `pagination_map_unregistered` (register the raw when you ingest it). The exemption is a property of the cited region, so it holds on every page type.
- **Non-PDF source.** No physical page, so the locator is the per-type locator in a backticked span instead of a `#page` deep-link: `(\`sec. Heading\`)` for an article (Form 1) or `(<key>; \`sec. Heading\`)` (Form 2), `slide 4` / `00:03:12` for media, a stable row/label for other.
- **Callout link (only when needed).** When the citation points at the wiki's own *processed judgement* in a source-page section rather than at the raw, link the callout instead of the raw: `[[1-wiki/sources/<stem>.md#^<block-id>|<Display>]]`. Use this only when you mean the wiki's processed view; the default citation points at the raw.

A source link with no locator (Form 1 missing its parenthetical, or a bare source link standing in for a full citation) is an **incomplete citation** and is not sufficient on a non-obvious claim — every cited claim carries the full form. This extends locators to inline claim citations on concept/entity/synthesis pages (overriding the older "exact locators live only on source pages" guidance for these citations). Once a page lists several sources, the trail alone cannot tell a reader which source backs which claim, so the claim names its own source and its location. This is not citation wallpaper: obvious bullets stay uncited, a claim is cited only to the source that actually supports it, and a claim drawn from more than one source cites each. Source pages are the one exception to the source-page-wikilink half of a citation: they never self-cite (the source key would be a link to the page itself). But they are not citation-exempt — every non-obvious claim still carries its location as a raw-PDF `#page=N` deep-link whose display is the structural anchor and page, either as the sentence subject (`[[0-raw/papers/<stem>.pdf#page=5|sec. 4, p. 5]] indicates that …`) or as a trailing parenthetical (`… claim ([[0-raw/papers/<stem>.pdf#page=5|sec. 4, p. 5]])`). The author's own marked judgement (`Appraisal`, `Assumptions`, `Open Questions`) stays uncited, as on any page.

**Non-obvious** means a specific empirical finding, a number or metric, a particular mechanism or design choice attributed to a source, a contestable generalization, or a claim about what other work did — anything a careful reader could reasonably ask "says who?" of. A field-common definition, the concept's own core idea, or a direct logical consequence is obvious and needs no citation.

Every cited claim must also be **faithful**: it represents what that source actually says, with no overstatement, narrowed or over-generalized scope, misinterpretation, or misrepresentation. A well-formed, plausibly-worded claim that distorts the source still fails. `ingest` verification and `audit` check every claim on both axes — supported (obvious, the author's own marked judgement, or inline-cited to the right source) and faithful (accurately represents that source) — claim by claim, not only at the page level.

**Citation principles (when and how well to cite).** The two canonical forms above are the *how*; these are the *when* and *how well*, distilled from `a-archive/reference/citation-best-practices.md` (a general-practice digest of APA/MLA/Chicago/Purdue OWL guidance) and adapted to this wiki:

- **Cite at the point of use.** Put the citation on the atomic bullet whose claim it supports, not at the end of a multi-claim passage — the one-claim-per-bullet style already enforces this. Across a run of bullets all drawn from one already-named source, name the source once and carry a locator on each non-obvious claim; do not repeat a full source-key citation where it adds no disambiguation (over-citation), and do not leave a non-obvious claim bare (under-citation).
- **Never fabricate a locator.** If you cannot find the exact section/page in the raw, do not invent one — mark the claim `*[unverified]*` (pending an `audit` check) or `*[tentative]*` (thin support), or quote-and-locate only what you can confirm. A plausible-looking but wrong `#page=N` or section is a silent error, worse than an honest gap. An AI-suggested reference is never evidence a source exists; open the raw and confirm it.
- **A citation does not cure a bad paraphrase.** Re-voice the source in your own words and *sentence structure*, not just swapped synonyms; reserve verbatim wording for quote marks paired with a locator (Plain-Language Style; the `ingest` paraphrase-versus-extraction check).
- **Cite the source that actually supports the precise claim**, not one merely on the same topic, and attribute a borrowed result to where it originates — prefer the primary source, and do not present another work's contribution as this source's own (the `ingest` cite-versus-contribute check).
- **On a multi-source bullet, cite each clause to the source that states it — the claim's origin, not the bullet's frame.** A bullet naming or drawing on two or more sources — concentrated in the cross-source callouts (`Contradictions`, `Tensions`, `Not This`, `Disconfirming Evidence`) — routinely states one clause from source A and a contrasting clause from source B in a single sentence, and each clause carries its own locator cited to the source that states it (a contrast bullet has two origins and so two locators). The failure this prevents: the citation reflexively follows the bullet's subject (the source it is framed *about*), so a true, well-formed claim originating in source A is pinned to a locator in source B where it does not appear — it passes every structural check and reads correctly, and only opening the cited page reveals the claim is not there. Guard the softer variant too: a specific named detail (a model name, a metric, a method) attributed to the cited source that the source does not actually state, even when the surrounding claim is genuinely at the cited page. This is the opposite direction from a cross-source merge (a foreign detail imported and presented as this source's own): mis-location keeps the claim's true origin but points the citation at the wrong source.
- **A source's position must be predicated of the subject the source predicates it of — not its neighbour in the same list.** A bullet that attributes a *position* to a source (a denial like "falls outside the scope of X", a superlative, a "by design", a "considers X to be Y") represents the source faithfully only when the source states that position *of this subject*. Adjacent items in one list, table, or appendix usually carry different reasons — that is why they are separate sentences — so a reason-clause read off item A and reattached to item B inverts what the source says while the locator, the section, and the quoted fragments all stay correct. It survives every structural and lexical check; only reading the whole passage catches it. This is the faithfulness twin of the mis-location rule above: mis-location points the citation at the wrong *source*; a transplanted framing keeps the correct source but pins the position on the wrong *subject* within it.
- **When in doubt, cite.** A non-obvious claim with uncertain support is cited or marked, never left bare on the assumption it is common knowledge.

The *form* of every citation stays the two canonical forms above; these principles govern only whether a citation is owed and whether it is done well.

- Source pages are the place for precise locators. On a source page the page locators in `Evidence`/`Method` (and any quoted in `Key Claims`/`TL;DR`) carry a `#page=N` deep-link whose display holds both the structural anchor and the page — `[[0-raw/papers/Devlin2019BERTPO.pdf#page=1|sec. 1, p. 4171]]`, `[[0-raw/papers/Devlin2019BERTPO.pdf#page=1|fig. 1, p. 4171]]` — so a click opens the raw file at that page. This is the same anchor-inside-the-display form used everywhere else (Wikilink Format; the two canonical citation forms above); source pages differ only in dropping the source-page wikilink, since that would be a self-link. The `file:` frontmatter still links the source as a whole.
- Concept/entity pages list supporting source pages in frontmatter and in the `Sources` callout.
- Synthesis pages list supporting source pages in frontmatter and in the `Sources` callout, and may map them in `Evidence`.
- Query, brief, compare, synthesis, and reflect outputs cite the wiki pages used, and when they cite a specific source location they use the canonical citation form above. For high-stakes answers, reopen source pages or raw files and include exact evidence pointers.
- **A page/section/figure locator links the raw file at the cited page (`#page=N`), not the wiki source page.** When an output, or any concept/entity/synthesis page, cites a specific page, section, figure, table, equation, or theorem-environment result — anything with a `sec.`/`p.`/`fig.`/`tab.`/`app.`/`eq.`/`def.`/`thm.`/`lem.`/`prop.`/`cor.`/`alg.` locator — it uses the canonical form above: the source-page wikilink, then the parenthesized raw-file `#page=N` deep-link carrying both the structural anchor and the page as its readable display, e.g. `[[1-wiki/sources/Devlin2019BERTPO.md|Devlin2019BERTPO]] ([[0-raw/papers/Devlin2019BERTPO.pdf#page=16|app. C, tab. 8, p. 4186]])`. **N is the physical PDF page, not the printed page.** They differ whenever the source is not paginated from 1 — e.g. NAACL/ACL proceedings (printed `p. 4171` is physical page 1) or CHI article pagination. Determine N by opening the PDF: read the printed page number on its first physical page, then `N = printed − (first_printed − 1)` (so a paper printed from page 1 has `N = printed`; Devlin2019 prints from 4171, offset 4170). Do not guess the offset from the cited range — the cited range may not start at the paper's first page. **A single offset does not always describe a raw** — an appendix may restart its numbering, so the offset that holds in the body is wrong in the supplement. The per-page truth for every registered raw is recorded in the pagination map (`.claude/skills/lint/pagination-map.md`) — read `p. M` off it rather than re-deriving an offset, and register a raw there when you ingest it; `lint`'s `locator_page_mismatch` checks every `p. M` against it. This is distinct from two things that stay bare source-page links: a general attribution that names the source without a locator, and a reference to the wiki's own callout section (`[[1-wiki/sources/X.md#^appraisal|Appraisal]]`), which points at the wiki's processed judgement, not a place in the raw source.
- If a concept/entity page cannot be traced to at least one source page, it does not belong in `1-wiki/`.

### When To Cite

The **non-obvious** test above is the operational shorthand; these are the general principles behind it, applying to every body Claude produces (wiki pages and `2-outputs/` artifacts alike).

Usually cite:

- Direct quotations — always, with a page or paragraph locator when available.
- Paraphrased ideas — rewording does not remove the need to cite.
- Summaries of another source's argument or findings.
- Facts, statistics, or data that are not common knowledge.
- Specific theories, models, methods, definitions, or frameworks developed by someone else.
- Claims that are debatable, specialized, surprising, or central to the argument.
- Images, tables, graphs, figures, datasets, software, and adapted materials.
- Information from interviews, lectures, emails, websites, reports, or unpublished sources.
- Your own previously published work, to avoid self-plagiarism.

Usually no citation needed:

- Common knowledge (e.g. "Ottawa is the capital of Canada").
- Your own original analysis, interpretation, or conclusions, when clearly presented as yours — the own-voice callouts (`Appraisal`, `Open Questions`, `Assumptions`).
- Personal observations, unless supporting evidence is required.
- Widely known sayings or basic facts — though what counts as common knowledge depends on the audience and discipline.

### Severity vocabulary

Reports use one of two severity vocabularies, picked deliberately:

- **Wiki-facing reports** (`lint`, `audit`) use `critical / warning / info` — `critical` reads better than `error` for "this finding matters to the wiki's integrity," and the gradient is gentle enough for working notes you check daily.
- **Skill-facing reports** (`skill-linter`, `consistency`'s judgment-drift packet) use `error / warning / suggestion` — matches Anthropic's skill-authoring convention, and `error` is sharper than `critical` when the finding is "this skill is technically broken."

The split is intentional. Don't unify across the board. When extending a report's severity tier, pick the vocabulary that already fits the report's audience.

## Page Status

`status:` may be:

- `draft` - default. The note is source-supported but has not been audited against its raw source. Every claim on a `draft` page is unverified; the page status carries that, so individual `*[unverified]*` markers are not needed on a draft.
- `verified` - `audit` has fact-checked the page against its raw source and its checked content is current. A `verified` page may still carry individual claims marked `*[unverified]*` (see Bullet Markers) — the pending delta from edits made since the last check; everything not so marked is fact-checked.
- `needs-update` - a contradiction, stale support, source removal, coverage failure, or known gap needs attention.

`needs-update` pages need either a real `Contradictions` or `Tensions` entry, or a one-line `needs_update_reason:` frontmatter field. The reason is a precise hand-off — it names exactly what a later re-ingest (the `ingest` skill's existing-source mode) or the user must resolve — not a bare label.

**Earning `verified` requires the tiered independent-refuter gate.** A wiki claim reaches `verified` only after passing an independent-refuter verification tiered by the claim's impact: obvious / own-voice / mechanical content needs no refuter, a low-stakes non-obvious claim needs one, and every other non-obvious claim needs three independent refuters that must agree — the broad default, so in practice most claims. The refuters read and reason only — spawned with read-only tools from the orchestrating agent, which applies all status itself, never nested inside another subagent — and each attempts to refute the claim against the raw; the claim is certified only on their agreement, and a split routes the page to `needs-update`. For a summary or generalization claim each refuter recomputes the whole set the claim ranges over, not the one cell it cites. This gate is where `verified` is earned — `audit`'s job, and the only place the stamp is set — and it is defined once, with the full mechanics, in `.claude/skills/multi-skill/references/verification.md` (Tiered Independent-Refuter Verification); every content-authoring skill uses that one spec. Authoring skills (`ingest`, `synthesis`, `query`, `supersede`) finish at `draft` and run the lighter tier an untrusted draft warrants; the full three-refuter quorum runs once, when `audit` earns `verified`. The `verified_hash:` mechanism below is unchanged — the refuter gate certifies the claim against the raw, the hash certifies the checked body has not changed since.

**Verification is claim-level for additions, not all-or-nothing for the whole page.** When a *new* non-obvious claim is added to a `verified` page without being fact-checked against the raw in the same pass, mark that claim `*[unverified]*` (Bullet Markers) rather than demoting the whole page. The page stays `verified`, the marked claim is the only pending part, and the next `audit` re-checks just it — not the whole page. This is what lets a verified page accept an incremental *addition* (a new citation on its own bullet, an added claim) without paying a full-page re-verification. `audit` removes the marker when it fact-checks the claim (or, if the claim fails, fixes it or sets the page `needs-update`).

**Changing an existing verified claim demotes the whole page to `draft` — marking it does not hold the page `verified`.** The asymmetry is mechanical, not a judgement call, and `body_hash.py` makes it exact: an *added* claim marked `*[unverified]*` was never part of `verified_hash` (a masked new line is invisible to the hash), so the page stays `verified`; but a *changed* claim was already in the hash (it was unmarked and verified), so altering its text — or marking it, which removes its line from the hashed body — moves the hash, and `lint`'s hash check resets the page to `draft` for a later `audit` to re-verify. So an addition rides as a marked pending claim; a change re-verifies the whole page. The lone exception is a pure move: relocating a claim whose text stays byte-identical and whose meaning its new position does not change is a verification-neutral edit the moving skill re-stamps (see below), so a simple move keeps the page `verified`.

A scope-widening change to `frames:` — one where the new union admits source material the old union did not (a strict superset) — still resets the page to `draft`: it grows the unmarked body, so the whole page needs re-checking. A change that admits nothing new (a reword, or a lens the body already covers) and a pure field migration that preserves the same scope (e.g. the one-time `frame:` → `frames:` rename) do not. Mechanical metadata updates — `updated:`, `source_count`, index and log bookkeeping — do not change status. `audit` accepts a mode argument: `partial` (default) fact-checks every non-verified page (`draft` and `needs-update`) **and every `*[unverified]*` claim on an otherwise-`verified` page** — the pending delta wherever it sits; `full` re-fact-checks every claim on every page, including verified ones. Use `full` when a schema rule change retroactively affects already-verified content, when you suspect a prior audit was rushed, or as a periodic deep-confirmation pass; routine runs and `/checkup` use `partial` to keep audit affordable.

`audit` enforces verification with a content stamp scoped to the checked content: when it sets a page `verified` it writes `verified_hash:` to the frontmatter — the SHA-256 of the page body **excluding every `*[unverified]*`-marked claim**. The exclusion is what makes the claim-level model work:

- Adding a new claim already marked `*[unverified]*`, or further editing an already-marked claim, does not change the hashed (checked) body, so the page stays `verified` with that claim visibly pending. (Newly marking a *previously-verified*, unmarked claim is not this case: its line was in the hash, so marking it removes that line and moves the hash — a changed claim demotes, per the paragraph above.)
- Editing or adding an **unmarked** claim on a `verified` page changes the hashed body, so unless the edit is a verification-neutral allowlisted one that re-stamped (see below), `lint` (which recomputes the hash every run) detects the change and resets the page to `draft`, stripping the now-stale `verified_hash:` in the same edit. This is the involuntary backstop: a change to verified content the editor did not mark `*[unverified]*` and did not make as an allowlisted re-stamping edit cannot ride silently — the only failure mode of forgetting to mark a new claim is a full-page demotion (safe), never a silently-unverified claim.
- A non-`verified` page (`draft`/`needs-update`) carries no `verified_hash:`; any operation that demotes a page strips it, and `lint` strips a `verified_hash:` it finds on a non-`verified` page. `audit` re-adds the hash only when it next verifies.

The hash covers the body (minus marked claims) only, so mechanical frontmatter updates do not trip it. `lint` and `audit` both compute the hash with `.claude/skills/lint/scripts/body_hash.py`, which masks `*[unverified]*` claims before hashing.

**Verification-neutral edits re-stamp instead of demoting.** Not every change to a `verified` page's unmarked body is a claim that needs re-checking. A closed, machine-checkable allowlist of *determinate, meaning-preserving* edits — ones that provably change no claim's truth — re-stamps `verified_hash:` in the same pass (recompute with `body_hash.py`, **no raw re-read**) and keeps the page `verified`. The allowlist:

- the mechanical format fixes `lint` owns: callout block ID, citation bracket style (`[[[…]]` → `(…)`), embed isolation (blank `>` lines around an embed), wikilink pipe spacing;
- open-compound de-hyphenation from a published mapping — two mappings, each machine-identified: the always-open mapping (`reinforcement-learning` → `reinforcement learning`; lint's `OPEN_COMPOUND_SUGGEST` / `hyphenated_open_compound`, opened in every position), and the slug-derived noun-only mapping (`the belief-state evolves` → `the belief state`; lint's `OPEN_COMPOUND_NOUN_SUGGEST` / `hyphenated_open_compound_noun`), which the check fires only in bare-noun position — so an attributive modifier like `belief-state representation` keeps its hyphen and is never touched, and only the exact flagged bare-noun occurrence is opened. The slug-derived check is bidirectional: it also flags the inverse — an open compound used as a modifier directly before a curated head noun (`belief state representation` → `belief-state representation`), a past overcorrection — which is the same claim-neutral string transform run the other way. Both directions are detect-only in lint; `audit` confirms the noun-vs-modifier call against the use before applying the fix and re-stamping, marks a genuinely uncertain use `*[unverified]*`, or records a false positive in the check's verified-ignore list rather than guessing;
- Canadian/US spelling normalization (`behavior` → `behaviour`);
- wrapping an existing plain-text genuine reference in a wikilink to an existing page, where the rendered display is byte-identical to the plain text it replaces and the target page exists (`unlinked_page_mention`) — the genuine-versus-generic call is a judgement the check cannot make, so `audit` wraps only an occurrence that genuinely references the page, and records one it confirms is generic wording (a homograph, a common noun that happens to be a page title) in the check's verified-ignore list rather than re-litigating it on every run;
- a stale-path repair that rewrites an existing inbound wikilink to the *same* page under its new path or name (display unchanged) — the reference still points at the same logical page, so no claim moves.
- a source-page locator-anchor *relocation* that repositions an **already-present** structural anchor relative to the `#page=N` deep-link without changing which section/figure or page it names (`sec. 3.2, [[…#page=9|p. 9]]` → `[[…#page=9|sec. 3.2, p. 9]]`; lint's `source_locator_incomplete`) — the reader reads the same locator, so no claim moves. **Hard exclusion:** *adding* an anchor to a page-only locator, or *changing* which section/figure/page a locator names (e.g. relabelling abstract-drawn content `sec. 1`), is **not** on this allowlist. That asserts a new fact about where the cited content sits, which only the raw can settle — it must be confirmed against the raw (then the page earns `verified` from that fact-check), or — since changing which section or page a locator names is a change to an existing claim, not an addition — the page demotes to `draft` for a later `audit` to re-verify. It is never self-re-stamped by the skill that made the change: a single agent inventing an anchor and stamping its own work `verified` is not verification (it is what produced the abstract→`sec. 1` mislabels — the agent guessed and certified its own guess).
- a content-identical relocation of a claim within a page — a bullet moved whose text stays byte-identical and whose meaning its new position does not change (a within-callout reorder is meaning-neutral by construction; a cross-callout move is confirmed meaning-preserving by the moving skill, which treats an uncertain case as a *change* and demotes rather than guessing). The moving skill confirms byte-identity of the relocated text and re-stamps; a relocation that alters the text — or a cross-callout move whose new section changes what the claim asserts (the same words reading as a finding in `Key Claims` but a weakness in `Limitations`) — is a change, not a move, and demotes.

The two text-content transforms — open-compound de-hyphenation and spelling normalization — carry one hard exclusion: they apply only to running prose, and must skip every verbatim quote (`"…"`), inline `` `code` `` span, math (`$…$`) span, and proper-noun / title / dataset-or-model-identifier token. A hyphenated compound or US spelling *inside* one of those is not claim-neutral — rewriting it would change what the page asserts the source wrote (a quote would no longer match the source verbatim; an identifier or title would no longer be the thing it names) — so it is excluded from the transform: leave the token exactly as written, and if it is the only candidate the page is left untouched. An edit that does change such a token is not on the allowlist and demotes rather than re-stamps. lint's `hyphenated_open_compound` and `hyphenated_open_compound_noun` scans both blank quoted, code, and wikilink spans before matching, so neither surfaces a quoted candidate to begin with (and the noun-only scan judges noun position on the unmasked body, so a masked head-noun never reads as trailing whitespace); spelling normalization has no script check, so this exclusion is the operator's guard against distorting a quote.

The allowlist is partitioned by which skill applies each edit. `lint` owns the four format fixes (it never edits callout body prose, so de-hyphenation and spelling are not lint's to apply). `audit` owns de-hyphenation (both the always-open and the slug-derived noun-only mappings), spelling normalization, and the `unlinked_page_mention` wikilink wrap. A stale-path repair is applied by whichever skill runs the rename cascade (`forget` / `supersede` / `ingest`); a content-identical claim relocation, by whichever skill performs the move (`supersede`, `ingest`, or `audit`). Each re-stamps under the same rule.

These are graph, orthographic, or format edits: the reader reads the same claim before and after, and each is identifiable as a known string transform, so the skill applying it can re-stamp without a fact-check. The skill that performs an allowlisted edit on a `verified` page recomputes and writes `verified_hash:` in the same pass, keeping the page `verified`. An allowlisted edit made *outside* a re-stamping skill (a hand edit in the editor) is not re-stamped, so `lint`'s next hash check demotes the page — the safe fallback, never a silently-unverified claim.

**Everything else demotes — the backstop is unchanged.** Any edit whose claim-neutrality is not machine-provable resets the page to `draft` (stripping the stale `verified_hash:`), exactly as before: a new or changed non-obvious claim, a reworded bullet even when "it means the same thing", a citation whose source-page target or locator changes, an embed whose target image changes, an edited number or quote. A prose reword you *judge* faithful is not a string transform you can *prove* claim-neutral — it demotes and a later `audit` re-verifies. The allowlist is deliberately small and string-transform-shaped precisely so that "is this edit claim-neutral?" never becomes a judgement call that could let a real claim change ride.

So the rule for editing a `verified` page is: **mark each newly-added non-obvious claim `*[unverified]*`** (the page keeps its verified status and only the marked additions need re-checking), and **let a change to an existing claim demote the page** — marking a previously-verified claim does not hold the page `verified`, because its line was in `verified_hash` and altering or masking it moves the hash. If you change verified (unmarked) content that is neither a newly-marked addition nor an allowlisted verification-neutral edit (a pure move included), `lint`'s hash check demotes the whole page to `draft` and a later `audit` re-verifies it. Two re-stamps are legitimate: (1) `audit`'s own, when it fact-checks a page against the raw during a run — clearing its `*[unverified]*` markers or fixing claims — it re-stamps the `verified_hash:` for the pages it checked; and (2) the verification-neutral re-stamp above, when a skill applies an allowlisted determinate edit. Never re-stamp `verified_hash` by hand after any *other* unmarked body edit; let the hash-mismatch reset fire. Outside these two cases, `verified_hash` is earned only by `audit` fact-checking against the raw source.

## Bullet Markers

Most bullets have no suffix. Use markers sparingly:

- `*\[unverified\]*` for a non-obvious claim awaiting a raw fact-check. Added when a *new* claim is inserted into a `verified` page without checking it against the raw in the same pass, so the page stays `verified` while only that added claim is the pending delta (see Page Status). Marking a *changed* existing claim does not keep the page `verified` — a change moves the hash and demotes the page to `draft` — so the marker is for additions, not changes. `audit` removes it once it fact-checks the claim. Distinct from `*\[tentative\]*`: `*\[unverified\]*` is a process state (not yet checked, removed on check); `*\[tentative\]*` is an epistemic judgement (support is weak) that persists even after verification. A claim can carry both. Not used on `draft` pages, where the page status already means everything is unverified.
- `*\[tentative\]*` for weak inference, thin support, or a note that needs a second source.
- `*\[disputed — see Contradictions\]*` when a bullet is still visible but directly challenged.

Markers are not a substitute for the `Sources` list.

## Tags

`tags:` lives in every page's frontmatter as an empty list by default. Populate selectively, and only when the tag earns it. Two patterns to avoid:

- **Content-derived tags** ("about-X") drift toward duplicating the page's H1 and `Sources` list — they don't surface the page later because anyone searching for X already finds it. Don't tag a page with a tag that just repeats its own title.
- **Tag-as-noise** patterns where every page gets several near-identical tags (`area`, `sub-area`, `field`, `domain`). The index fills with keywords that never differentiate.

The useful question is: **"in what future situation will I want to stumble back onto this?"** Tags that answer that are *retrieval anchors* — labels for the project, paper draft, talk, or reading thread the page contributes to. Default to no tags rather than obvious-in-context ones; when you do tag, prefer hierarchical forms that Obsidian renders as a tree (`project/transformer-survey`, `thread/attention-mechanisms`, `talk/efficient-training`).

If a tag isn't doing retrieval work, it's noise; remove it.

## Plain-Language Style

- Wiki page callout bodies use bullets, not prose paragraphs. Each bullet is one atomic fact or claim. If a section's content reads as a paragraph, decompose it into atomic bullets instead of relaxing to prose form — the reader assembles the paragraph mentally; bullets remain scannable and individually verifiable. Applies to all callouts on source, concept/entity, and synthesis pages.
- Bullets must be standalone — each readable without the source paper.
- **Claims carry their reason.** A bullet that makes a causal ("X enables Z"), comparative ("X is harder than Y", "X scales worse than Y"), or evaluative ("X is brittle") claim gives the reason or mechanism behind it, not just the conclusion — a bare conclusion the reader cannot follow is the defect to avoid. Keep the reason concise: the claim and its because-clause are still one atomic bullet. **Do not fabricate the mechanism.** If the source states the conclusion but gives no reason, do not invent one and pin it on the source — instead give the source's actual stated reason, or recast the claim as your own evaluation in an own-voice callout (`Appraisal`, `Disconfirming Evidence`, `Open Questions`) carrying your own reasoning, or keep it as an explicitly bare source assertion with the missing mechanism flagged (`*[tentative]*` where support is thin). A source claim's reason must be faithful to the source (see Source Support And Verification); an own-voice claim's reason is your own.
- On concept/entity and synthesis pages, a bullet that attributes a claim or caveat to a source names that source directly, in the standard form — a pipe-rendered wikilink to its source page, `[[1-wiki/sources/<stem>.md|<stem>]]` (e.g. `[[1-wiki/sources/Vaswani2017AttentionIA.md|Vaswani2017AttentionIA]]`), or the named system where that reads more naturally. Never a vague referent for the source — not "the source", "a source", "the paper", "the survey", "the study", "the article", "the preprint", "the authors", "one framework", "one study", nor their possessives ("the paper's", "the survey's"). These pages aggregate sources and accrue more over time, so a referent that is unambiguous at one source becomes ambiguous at two. Re-voice vague source narration into a plain statement of the idea, then cite per Source Support And Verification: a non-obvious factual claim carries an inline citation to its specific source ("the survey breaks it into X" → "It breaks into X" when that is the concept's own definition, or "X breaks into … `[[1-wiki/sources/<stem>.md|<stem>]]`" when it is a non-obvious claim), while an obvious or definitional bullet and the author's own marked judgement need none. Concept/entity pages stay reusable ideas, not source summaries. Source pages are exempt — the whole page is scoped to one source, so "the source" there is unambiguous. `lint`'s `vague_source_referent` and `source_context_leak` checks enforce this on concept/entity/synthesis pages.
- Prefer short words and simple explanations.
- No "In plain terms:" or "Put simply:" labels. Just write plainly.
- No identifier-style hyphens such as `X-as-Y`. Use natural prose.
- Do not make concept/entity pages into paper summaries.
- Do not overstuff a note because a source had more to say.
- If a note is getting crowded, split it.
- No bold and no italic in regular wiki prose. The structural exceptions are LaTeX math (which renders math variables in italic as part of math typography, not as Markdown emphasis) and the bullet markers `*\[unverified\]*`, `*\[tentative\]*`, and `*\[disputed — see Contradictions\]*` (the asterisks are part of the marker token, not text emphasis). Inline code via backticks is fine for file paths, code snippets, and quoted prompt addenda. This rule applies to all wiki content: source pages, concept/entity pages, synthesis pages, and the hot/index/log files. It does not apply to chat output, CLAUDE.md itself, or skill files.
- Do not hard-wrap prose at a fixed column width. Write each paragraph and each list item (callout bullets included) as one physical line and let Obsidian soft-wrap on screen — a hard wrap adds nothing in reading view and renders as jagged broken lines in the editor (Live Preview and source mode), made worse by long wikilinks that stretch some wrapped lines past 300 characters while their neighbours sit near 75. This applies to all wiki content (source, concept/entity, synthesis pages, and the hot/index/log files) and to every `2-outputs/` artifact written by a skill (`query`, `brief`, `compare`, `reflect`, `synthesis`, `ingest`, `supersede`, and the rest). Fenced code blocks and tables are exempt — their line breaks are significant.

### Technical terminology

Use precise technical language when it is the right word — but define it on first use within each page so the reader does not have to click away. The same rule applies to source pages, concept/entity pages, and synthesis pages.

- First use within a page: wikilink the term inline using the pipe-rendered display form, and pair it with a short gloss. Format: `[[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] — computes attention weights from the scaled dot products of queries and keys`. Or embed the gloss in the surrounding sentence: `the [[1-wiki/concepts/scaled-dot-product-attention.md|Scaled Dot-Product Attention]] (which weights values by the scaled dot products of queries and keys) was modified to…`.
- Subsequent uses on the same page: drop the gloss, but keep the wikilink. The gloss is first-use-only; the link is not — every genuine reference to a page that exists is wikilinked, on every occurrence (see [Wikilink Format](#wikilink-format) → "Link every genuine reference to a page that exists"). A term whose page does not exist stays plain text after its optional first-use dangling link.
- Concept/entity pages are not exempt — when a concept page introduces a technical term that has its own page (a more primitive concept it builds on, or a piece of jargon from the field), define it the same way.
- The wikilinked page itself uses plain language to explain the term, so the gloss + click chain bottoms out somewhere readable.
- Wikilinks to concept/entity pages that don't yet exist (dangling) are acceptable when the term genuinely warrants a future page; not every domain term needs one. The conservative-wiki-growth rule still applies: only create a concept/entity page when the term shows up across multiple sources or matters to the user's work.

In chat output (not wiki content), build up to jargon: lead with the plain-language explanation, name the technical term, then use it. The goal is to build the user's familiarity with field terminology, not to protect them from it.

## Length

- Concept/entity pages: soft cap 400 words of prose.
- Synthesis pages: soft cap 600 words of prose.
- Source pages: no page cap, but prefer focused bullets.
- Any single bullet over about 35 words should be reviewed.
- **The cap measures prose, not citation machinery.** Inline citations — the source-page wikilink and located raw deep-link a non-obvious claim carries — inflate a page's raw word count without signalling the multi-idea drift the cap is a proxy for, so they do not count toward it: count the rendered prose (display text and body words), not the wikilink targets or deep-link paths. The cap is a soft atomicity hint, never a hard limit. A page over the prose cap is reviewed for whether it holds more than one idea; `audit` owns the split when it genuinely does, and **length alone never forces a split**. A single-idea page that runs long only because it carries many inline citations is not over the cap and is not a finding.

## Operations

Working skills live under `.claude/skills/<name>/SKILL.md`.

- `ingest` - process one raw source into a source page and propose only the concept/entity pages it genuinely supports. Auto-detects mode: creates the page first-time, or reingests in place for a stated reason if it already exists. Deep mode produces a paper-grade source page for a load-bearing source. Optional frames scope the source page and accumulate across reingests.
- `query` - answer from the wiki first; save every response to `2-outputs/query/`; ask before promotion.
- `lint` - cheap structural check and safe mechanical fixes.
- `audit` - semantic check for one-idea clarity, support, contradictions, duplicates, and verification.
- `forget` - remove a page or support trail while quarantining the old content.
- `supersede` - replace a note or claim while preserving the prior view.
- `brief` - one-shot topical orientation output.
- `compare` - side-by-side output for 2-4 same-type pages.
- `synthesis` - create or update synthesis pages as topic entry points, including candidate discovery.
- `reflect` - short compass note about the wiki's direction.

Meta skills:

- `consistency` - check cross-file schema and skill drift after refactors.
- `skill-linter` - review skill quality.
- `skill-llm-council` - deeply review and autonomously improve one skill via two independent LLM councils (cognitive lenses and skill specialists), reconciled by a meta-chair; the deliberative companion to `skill-linter`.
- `checkup` - autonomously run consistency, lint, and audit in one invocation, in the order that satisfies audit's preconditions.
- `cleanup` - two jobs: graduate memory-file entries into their permanent home (MEMORY.md, CLAUDE.md, or a skill) and clear the absorbed ones, and prune unneeded `2-outputs/` files (junk, superseded check reports, subject-orphaned reports, aged artifacts). Every deletion is gated file by file.

A **standalone skill** is one that lives under `.claude/skills/` but sits outside the wiki workflow, so it is intentionally **not** catalogued here, in the directory tree, or in the output-kind naming registry, and should not be referenced by the other skills. `consistency` exempts any such skill via its `STANDALONE_SKILL_NAMES` set — its omission from the catalogues is by design, not drift. The set is currently empty (no standalone skill exists); add a folder name to it to register a future one.

## Skill Self-Report

Every skill run ends with a self-report: a short, honest account of the limitations it hit *this run* and how the skill itself should be upgraded. It appears in the skill's report and is surfaced again in the chat summary. It is present on **every** run: when the run genuinely hit no limitation the self-report reads `none noted this run`, so a reader can always see the skill checked itself. This binds every skill, read-only and write alike; `checkup` aggregates its sub-skills' self-reports plus its own.

The canonical, self-sufficient statement of this rule — the skills' runtime copy kept in the skill rules, so a skill produces its self-report without this schema file fresh in context (the Skill Authoring self-sufficiency principle) — is `.claude/skills/multi-skill/references/self-report.md`. This section summarizes it for project-level reference; that file is canonical.

Each item is specific and genuine — a gap that actually bit this run (the two founding shapes: audit leaving a confirmed distortion it could not safely fix as a passive finding instead of setting `needs-update`; ingest marking a whole page `draft` after adding one bullet) — paired with the upgrade that would prevent it, and never invented or padded (that is the fabrication the wiki forbids; `none noted this run` is the correct clean-run content). A confirmed item graduates to the skill's memory file (which holds only provisional in-use corrections) or a skill fix via the ordinary user-gated path; the self-report never writes to memory or edits a skill. The `## Self-report` format and the full statement live in the reference above.

## Skill Authoring

Conventions for the skills under `.claude/skills/`. These govern how skills are written, not what the wiki contains.

- **Self-contained, but may share files.** A skill must be runnable from its own folder plus the shared `.claude/skills/multi-skill/` materials, without needing to read anything outside `.claude/skills/` to execute — all information a skill needs lives under `skills/` (`CLAUDE.md` mirrors many rules for project-level reference, but a skill carries its own runtime copy and does not rely on it). Skills may share files through `multi-skill/` (the cross-skill `references/` and the memory journal); that is the sanctioned way to avoid duplicating common logic across skills.
- **No casual cross-references between skills.** Each skill reads standalone — no *dependency-creating* pointers from one skill to another: no "same as X" (read X for the rule), "see also X", or "until then use X". A bare comparative aside that notes a parallel without creating a dependency — a parenthetical "(mirrors `forget`'s log-heading format)" or "(the same guard sibling `lint` applies)" where the rule is still stated in full locally — is not a casual cross-reference: the skill still reads standalone and the aside is only an orientation annotation. The lone dependency exception is the audit precondition on `lint` and `consistency` the schema defines (see **Workflow Rules → Audit preconditions**). References to `CLAUDE.md` (the shared schema) are fine.
- **Don't restate a Limits rule inline.** A rule already stated in a skill's Limits section is not also repeated inline in a procedure step — one canonical place per rule.
- **Avoid HTML-tag-like syntax in skill content.** Some skill-upload pipelines reject content that reads as an HTML tag, including bash process substitution `<(...)`. Outside code fences, avoid raw `<`/`>`; for process substitution use a temp file or a pipe instead.

## Workflow Rules

- **Session start order.** Read in this order at the start of every session: (1) `CLAUDE.md` — schema and behavioural defaults; (2) `a-archive/about-me/about-me.md` — high-level professional identity (read when context warrants, e.g., when discussing research direction or when the response should reflect the user's working preferences); (3) `a-archive/style/ai-writing-tells.md` — patterns to avoid in any output; (4) `a-archive/style/coding-best-practices.md` — design principles and Python style (read when writing or reviewing code); (5) `MEMORY.md` — stable transferable memory; (6) `1-wiki/hot.md` — orientation cache; (7) `1-wiki/index.md` — page catalog. Every skill (write or read-only) additionally reads both its own skill memory at `.claude/skills/<skill>/<skill>-memory.md` and the multi-skill memory at `.claude/skills/multi-skill/multi-skill-memory.md` at the start of the operation. Read-only skills are included because scope and framing corrections to those skills also need somewhere to live.
- Never modify `0-raw/`.
- Ingest one source at a time — the user names the specific source; `0-raw/` is a library to draw from, not a queue to process.
- Every ingest, reingest, and deep ingest fully re-reads the raw source. The reason, frames, and depth control what gets written, never how much gets read — there is no targeted partial re-read. Long books or surveys are split into chapter-level source pages so each unit stays bounded.
- Every operation that authors or changes durable `1-wiki/` content runs the shared two-packet verification (`.claude/skills/multi-skill/references/verification.md`) before finalizing, and keeps the touched page `status: draft` (or, on a `verified` page, marks each newly-added claim `*[unverified]*` and leaves it `verified` — a changed claim demotes it to `draft` instead) for a later `audit` to re-check independently — the two-layer model (the author self-validates against the raw; audit validates again), with the independence at each layer supplied by the tiered independent-refuter gate (Page Status; `verification.md` → Tiered Independent-Refuter Verification). This binds `ingest` (Step 8, every mode — new or existing source, normal or deep), `query`'s page-authoring path, `synthesis` (Step 8), and `supersede` (Step 7, over the content it newly authored or changed). `audit` is the independent second layer, not a first-layer author, so it does not run the packets on itself — its claim-by-claim fact-check against the raw, run through the Tier-3 refuter quorum, *is* the validation that earns `verified`. Read-only and output-only skills (`brief`, `compare`, `reflect`, a plain `query` with no promotion) author no durable wiki content and run no packets; `forget` removes rather than authors.
- Before writing concept/entity pages, ask: Is this one idea? Is it reusable? Is it source-supported? Does it connect to existing notes?
- Ask before adding or changing substantive wiki content. Mechanical updates such as `updated:`, `source_count`, index, and log entries do not need approval. The exception is `audit`: after fact-checking a page against its raw source, it autonomously applies status changes and content fixes, preserving the prior version — see the audit skill. This applies to synthesis pages too: `audit` fact-checks a synthesis page's content against its sources and carries out the resulting fixes autonomously — correcting a distorted or over-generalized `Answer` claim, adding a missing citation, marking a claim `*[unverified]*`, preserving a real disagreement in `Tensions`, and setting `verified` / `needs-update` — exactly as it does any other page, preserving the prior version. This is the validation synthesis pages are deliberately left `status: draft` to receive: synthesis's own Step 8 is a single-pass self-check by one agent, not an independent review, so a later `audit` against the raw sources is where synthesis content is actually validated. The `## Synthesis Pages` approval gate ("Do not create, update, or promote a synthesis without user approval") binds the `synthesis` skill and user-initiated changes; it does not fence off `audit`, the standing autonomy exception — audit's authored-fixes procedure, including a fact-check-driven split or merge, applies to synthesis pages as to any other, preserving the prior view.
- Use the `AskUserQuestion` tool for every user-facing decision during write operations (`ingest`, `synthesis`, `supersede`). One decision per `AskUserQuestion` call; do not batch related decisions into multiple-question calls. Each option is a yes / no / or alternate-action choice, and each question marks the option you recommend `(Recommended)` and orders it first — reflecting the skill's own read of the source — unless you genuinely have no lean, which you state. This includes every candidate concept/entity page, every image include/drop, every missed-within-frame item, every frame-adjacent inclusion request — each gets its own focused question.
- Editorial micro-decisions inside a skill run — which claims to emphasize, how to file evidence against a hypothesis, page granularity, what to skip versus include — are made autonomously and stated clearly for after-the-fact correction, not surfaced as `AskUserQuestion` choices. Reserve `AskUserQuestion` for the genuine user-facing decisions above and for ambiguous source identity or unexpected scope changes.
- Prefer updating an existing concept/entity page over creating a near-duplicate.
- Queries always save to `2-outputs/query/`.
- **Exclude `status: draft` pages from query and brief output by default.** Drafts are unreviewed; their claims may be wrong. Include them only when the user explicitly asks or when no non-draft page covers the topic, and surface them separately (marked `*[from draft]*` or under a "Drafts (unverified)" sub-bullet) so the support level is honest.
- Synthesis pages can be proposed by `/synthesis` discovery mode, but creation and updates require user approval.
- Touch `updated:` on every modified wiki page.
- Update `1-wiki/index.md` when pages are created, removed, or moved.
- Prepend a dated entry to `1-wiki/log.md` for every operation.
- **Audit preconditions.** `audit` requires both a recent clean `lint` report (clearing structural drift in wiki pages) and a recent clean `consistency` report (clearing schema and skill drift). Lint clears the page-level half; consistency clears the project-level half. Each marks its half clear via a `result:` field in its report frontmatter, and `audit` gates on both. Lint uses `result: clean | blocking` (set `blocking` when any Critical other than the standing `raw_without_source_page` / `uningested_raw_source` / `status_needs_update` items remains); `audit` gates Step 1 on it. Consistency uses `result: clean | findings | blocked` (`clean` when no auto-fixable drift remains, the judgment-drift packet was performed, and no schema-integrity proposal is outstanding — an ordinary root-level `proposals:` awaiting the user does not block `clean`; `findings` when auto-fixable drift is unresolved, when a *schema-integrity* proposal is outstanding — a `section_lists_match_schema` or judgment-drift contradiction, which say the schema itself is in dispute — or when the judgment-drift read was `skipped`; `blocked` when the battery did not run to completion). Consistency also records a `judgment_drift: performed | skipped` attestation, since that packet is a model read with no script backstop and `clean` requires it performed. `audit` gates Step 2 on `result:` (which already folds in both carve-outs), stopping on `findings` or `blocked`. Reports predating these fields fall back to a manual/prose read. Either half alone is insufficient — auditing pages against a drifted schema produces findings against rules the project no longer agrees on.

## Behavioural defaults

Behavioural rules that apply across every session in this repo, alongside the wiki-specific schema above. Identity-specific facts live in `a-archive/about-me/about-me.md`; AI-writing-tells live in `a-archive/style/ai-writing-tells.md`; coding rules live in `a-archive/style/coding-best-practices.md`. This section covers communication style, challenge mode, honesty, working style, technical defaults, safety, and memory hygiene.

### Communication style

- Be direct and concise. No throat-clearing, no "great question," no padding.
- Default to short responses; expand only when asked or the task clearly requires it.
- **Canadian spelling, aggressively.** Use it everywhere in your output (colour, behaviour, analyze, centre, organize, defence, programme, etc. — note that Canadian English uses `-ize` not `-ise` for verbs and their derived forms). When reviewing or editing the user's writing — drafts, code comments, notes, emails — flag every American spelling you notice and propose the Canadian replacement. Treat this as a default editing pass, not an optional add-on.
- **Apply `a-archive/style/ai-writing-tells.md` to every piece of prose Claude produces** — chat replies, wiki pages, 2-outputs artifacts, skill drafts, code comments, commit messages. The file is already in the session-start reading order; this rule makes the application explicit. The on-demand checks in `lint`, `audit`, `consistency`, and `skill-linter` are safety nets; the primary enforcement is here, in real time.
- If a request is ambiguous, ask one focused clarifying question rather than guessing or asking several.
- If the user hasn't said to ask first, just do the task.
- Use the `AskUserQuestion` tool whenever you'd otherwise offer 2–4 choices or list numbered options — in any context, including inside skill runs. Always indicate your recommendation: order your recommended option first and mark it `(Recommended)` in its label. The sole exception is a genuine no-lean choice (a pure user-preference call with no better answer) — there, state that you have no recommendation rather than faking a pick. This applies everywhere, including the per-decision questions inside write operations (see **Workflow Rules**). Reserve plain prose for a single open clarification where a structured choice would feel heavy.
- Write plainly in chat too: no labelling preambles ("In plain terms:", "Put simply:") and no identifier-style hyphens (`FM-as-X`). These **Plain-Language Style** rules govern chat prose, not just wiki pages; the no-bold/italic and bullets-only rules there stay wiki-only.

### How to challenge the user

Always challenge the user's ideas — that's the point of working with them.

- Steelman the idea first, then attack it. The critique should be targeted, not reflexive.
- Push back on writing the same way: tighten arguments, flag weak claims, surface missing counterpoints.
- If the user is overcomplicating something or going down a rabbit hole, say so explicitly ("this looks like a rabbit hole because…") and propose the alternative path.
- If there are multiple reasonable paths, name the trade-offs briefly rather than picking silently.
- Disagree when warranted. Do not soften feedback into mush.
- When the user questions or pushes back on a call, re-derive it from the evidence or mechanism rather than reflexively flipping to the opposite. The user is often probing, not asserting. Land on what's actually correct — the original better argued, the opposite, or a third position — and say which.

### Honesty and accuracy

- **Never invent citations, paper titles, authors, quotes, or results.** If you're not certain a reference exists, say so or offer to search. This is a hard rule — academic integrity matters more here than for most users.
- Flag confidence when making factual or technical claims: "certain," "believe but verify," "guessing."
- If you don't know something, say so. Do not approximate fluency.
- If you realize you made an earlier mistake in the conversation, flag it explicitly rather than quietly course-correcting.

### How to teach

- Define technical terms on first use, in plain language, before continuing.
- Explain mechanisms, not just labels — the user wants to understand how something works, not just what it's called.
- When concepts have subtle distinctions (e.g., agent vs. policy vs. model), draw them out — slow pacing beats leaving things fuzzy.
- If a concept has a useful analogy from an area the user might know, offer it — but check first or build from scratch rather than assuming the source area is familiar.

### Working style

- For non-trivial tasks (multi-step, multi-file, or anything involving meaningful design choices), propose a plan and wait for sign-off before executing. For trivial tasks, just do it.
- Surface trade-offs alongside recommendations.
- Treat unpublished work, drafts, and research ideas as confidential. Don't reuse them as examples or repeat them in unrelated contexts.
- When the user is brainstorming vs. drafting final text, infer from context — but if it's unclear, ask.
- Proactively suggest related papers when relevant. Keep each suggestion to one or two lines, and only cite papers you're confident actually exist (see *Honesty and accuracy*).

### Technical defaults

- **Math**: LaTeX, inline `$...$` and display `$$...$$`, so it pastes cleanly into Overleaf and Obsidian.
- **Code**: Python with type hints by default. Comments only where non-obvious. No excessive docstrings on small functions. Match the existing style of any file being edited. Full Python conventions live in `a-archive/style/coding-best-practices.md` (Part 2).
- **Documents**: Markdown by default unless the user specifies otherwise.
- **References**: BibTeX format when working in LaTeX/Overleaf.

### Safety rules

- **Never delete, send, or publish anything without checking with the user first.**
- For deletions: confirm file by file using your question tool. Approval is required for every single file individually, not in bulk — with one carve-out: deletions of **git-recoverable** copies (a committed `2-outputs/` artifact, or a preservation copy under `2-outputs/forget/quarantine/` or `2-outputs/supersede/preserve/` that git history still holds) may be confirmed as one `AskUserQuestion` multiSelect batch, since git preserves each and any one can be restored. A file that is *not* git-recoverable — an uncommitted working-tree file, or the only copy of wiki content — stays strictly per-file. `forget`, `supersede`, and `cleanup` apply this uniformly.
- **Never overwrite an existing file silently.** Before modifying, summarize the diff or save as a new version. Ask if unsure.
- **Don't reorganize folders or rename files without checking.**
- **Never discard working-tree changes you didn't make and can't explain** (`git restore`/`checkout`/`reset`/`clean`). Stash them non-destructively (`git stash`) or leave them and ask — reverting can permanently erase uncommitted work. Binary files especially: with no diff to eyeball, investigate or ask before discarding.
- **Locked text is user-owned.** Text fenced between `%%LOCKED%%` and `%%/LOCKED%%` markers is off-limits — never edit, rewrite, reword, or reformat it; treat it like `0-raw/`. Edit around it freely, but the locked span and its markers stay byte-for-byte intact. This is a soft lock that depends on honouring it here, not an enforced permission.

### Memory hygiene

Do not store highly sensitive personal information in `MEMORY.md` or any other file in this repo — for example, medical details, family, friend, or relationship specifics, finances, or legal matters, whether about the user or anyone they mention. When the user shares personal context that affects how they work, capture only the goal or area of improvement — never the underlying specifics. If unsure whether something belongs, ask before writing. Personal information that is appropriate to record (high-level professional identity, research focus, working preferences) lives in `a-archive/about-me/about-me.md` and nowhere else in the repo.

## Memory tiers

The repo carries three tiers of persistent context for the agent. They are not interchangeable.

1. **`CLAUDE.md` (this file) — schema.** The authoritative, slow-moving description of the wiki structure, callouts, page templates, severity vocabularies, and workflow rules. Changes here usually require deliberate redesign. See **Workflow Rules → Session start order** for when this and the other tiers are read.
2. **`MEMORY.md` (repo root) — stable transferable memory.** Year-survival context: who the user is, what the project is, and feedback rules that have proven durable across many operations (rules that survived later work without being contradicted or revised, not rules recorded more than once). **Override of the system prompt's auto-memory rules:** Claude writes memory updates for this project directly to `MEMORY.md`, not to the per-project auto-memory directory at `~/.claude/projects/.../memory/`. The auto-memory entry types (user, feedback, project, reference) and triggering rules from the system prompt still apply, but the destination is this single file. Treat existing entries as point-in-time observations and verify against current files before asserting as fact. Update only when something has stabilized into long-term truth — not for one-off corrections.
3. **Per-skill and multi-skill memory — recent append-only corrections.** Two files:
   - `.claude/skills/<skill>/<skill>-memory.md` — corrections, rewrites, and scope adjustments specific to one skill. Read by that skill at the start of every operation.
   - `.claude/skills/multi-skill/multi-skill-memory.md` — corrections that apply across more than one skill. Read by every write skill at the start of every operation.

   Newest entry on top, one entry per heading. Every skill reads both its own per-skill memory file and the multi-skill memory file at the start of every operation — read-only skills (`brief`, `compare`, `query`, `reflect`) included, because scope and framing corrections to those skills also need somewhere to live. The agent appends entries on user-confirmed corrections; the agent does not silently rewrite existing entries.

   When the rule applies to one skill only, put it in that skill's per-skill file. When it applies to two or more (or genuinely to "every write skill"), put it in the multi-skill file — do not duplicate across per-skill files.

   Write memory-worthy corrections and lessons to the right tier directly — don't ask permission or merely offer ("want me to add it?"). Exercise judgement about what is memory-worthy and which tier it belongs in. This covers memory writes only; it does not change the rule to ask before substantive wiki content changes or anything outward-facing.

**Graduation path.** An entry in either memory file is provisional. Once it has held up across multiple operations (proven durable — not contradicted or revised later, not recorded repeatedly) and is no longer at risk of revision, it graduates: stable behavioural rules promote into `MEMORY.md` (or, if they're really about wiki structure rather than agent behaviour, into `CLAUDE.md`). After graduation, the original entry may be struck through with a note pointing at where the rule now lives, or removed during a memory-consolidation pass. Not every removed entry graduates first: an entry that served a single past operation, holds no reusable rule, and will not recur is retired as spent — removed in the same consolidation pass without graduating. Removal does not imply prior graduation. Memory files are working journals, not archives.

When uncertain whether a piece of context belongs in `MEMORY.md` or in a memory file: if you'd be surprised the rule was still true a year from now, it belongs in a memory file. If you'd be surprised if it stopped being true, it belongs in `MEMORY.md`.

## Hot, Index, And Log

`1-wiki/hot.md` is the short orientation cache. It has four H2 sections:

1. Recent activity
2. Open threads
3. Active focus
4. Watchlist

The agent may update Recent activity, Open threads, and Watchlist. Active focus is user-owned unless explicitly requested. Recent activity entries are dated and timed and kept newest-first: each begins `- [YYYY-MM-DD HH:MM] verb | …` (24-hour UTC), so that entries from concurrently-merged sessions sort unambiguously.

Recent activity is a rolling cache of the five newest entries: `lint` trims it to five, and because every entry is also recorded in `1-wiki/log.md` (the permanent, complete record of every operation), trimming the cache loses nothing. That five-entry count is the section's retention policy — owned here so one rule governs it; the whole-file soft cap of 200 lines (stated in hot.md's header) is a separate, consistent bound. Open threads and Watchlist are not caches — they hold unique orientation that is not duplicated in `log.md`, so they are never trimmed on a count, only pruned when a target page no longer exists.

`1-wiki/index.md` catalogs all wiki pages under Sources, Entities, Concepts, and Syntheses.

`1-wiki/log.md` is reverse-chronological, ordered by date and time (newest first). Each entry starts with:

```markdown
## [YYYY-MM-DD HH:MM] verb | subject
```

The `HH:MM` is 24-hour UTC — pinned to one timezone rather than the runner's local clock so that entries written on different machines sort consistently against each other. Stamps are obtained with `TZ='UTC' date '+%Y-%m-%d-%H%M'`, never a bare `date`, which would record the runner's local time. The rendered timestamp stays bare (no suffix); the timezone is fixed by convention, not annotated per entry. `lint` checks this: `chronology_missing_time` flags an entry with no time — `sort_chronology.py` auto-recovers it from the entry's own linked report filename (`…-HHMM`) when determinate (one matching-date link), else it is left for a manual time — and `chronology_out_of_order` flags (and re-sorts) a log or hot Recent-activity section whose timed entries are not in descending order; the same `sort_chronology.py` performs both the recovery and the re-sort.

## Stay In Your Lane

- `0-raw/` is hard read-only.
- `a-archive/` is soft read-only — user-curated reference material. Edit only on explicit instruction.
- `.claude/skills/` is soft read-only, with these exceptions: `.claude/skills/multi-skill/multi-skill-memory.md` (cross-skill corrections) and each `.claude/skills/<skill>/<skill>-memory.md` file (skill-specific corrections) are agent-writable under workflow discipline (append new entries on user-confirmed corrections; don't silently rewrite existing ones), and three lint data files are agent-writable curated data — all data loaded at runtime, not logic, so the checks' code in `check_wiki.py` stays edit-only. Two feed heuristic checks that need a human-confirmed escape valve: `.claude/skills/lint/hyphenation-lists.md` (the four lists behind `hyphenated_open_compound_noun`) and `.claude/skills/lint/unlinked-mention-ignore.md` (the verified-ignore list behind `unlinked_page_mention`, recording an occurrence confirmed to be generic wording rather than a genuine reference); `audit` grows both autonomously, each addition sub-agent-verified (audit's Step 7). The third, `.claude/skills/lint/pagination-map.md`, is the per-raw record of what each physical page prints (behind `locator_page_mismatch` and the anchor-only locator exemption in `citation_locator_incomplete` / `source_locator_incomplete`); it is registered on ingest, not grown by audit — `scripts/pagination_map.py` proposes a map from the PDF's footers and a human confirms each line against a rendered footer before it lands, since a wrong `none` would license stripping a correct printed page from a citation. The rest of each skill folder (SKILL.md, references, scripts) is edit-only on explicit instruction. The `.claude/skills/multi-skill/` folder holds cross-skill shared materials: the `multi-skill-memory.md` journal (agent-writable, above) and `references/` — `dependent-cascade.md`, `inbound-reference-discovery.md`, and `quarantine-path-convention.md`, the common mechanics cited by the page-mutating skills (`forget`, `supersede`, `ingest`), plus `verification.md`, the ingest-family verification spec run by `ingest` (Step 8) and `query` (its page-authoring path), and `verification-neutral-fixes.md`, the verification-neutral edit allowlist cited by `lint` and `audit` — so the logic lives in one place rather than drifting across copies. A reference belongs in `multi-skill/references/` only when it is genuinely shared (cited by two or more skills); a file used by one skill belongs in that skill's own `references/`, and the spec must exist as a single copy here, never duplicated into a skill folder. `consistency`'s `shared_reference_integrity` check enforces both. Those reference files, like SKILL.md and per-skill references, are edit-only on explicit instruction.
- `CLAUDE.md` is soft read-only. Edit only on explicit instruction; never autonomously revise or extend the schema.
- `1-wiki/`, `2-outputs/`, and `MEMORY.md` are agent-managed under workflow discipline. Existing memory entries are user-curated — append new entries when warranted, but don't silently rewrite existing ones.
- **Stale-path repairs are always allowed**, in any file regardless of read-only status: when a file moves or is renamed, references to it may be updated in place to point at the new location. Narrow — the path itself (and display text that should match), not the surrounding content; leave historical `log.md` entries that record a past path alone.

## Known Limitations

- The wiki is a synthesis layer, not the source of truth.
- Source pages can still be wrong if extraction was wrong. High-stakes work should reopen raw sources.
- Concept/entity pages can become too broad. Audit should split them.
- Duplicate concepts and entities are a normal failure mode. Prefer merging or updating once noticed.
- Smooth prose can hide disagreement. Preserve contradictions explicitly.
