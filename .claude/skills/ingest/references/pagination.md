# ingest — register a raw's pagination (Step 2)

Before any locator is written for a PDF raw, record what each of its physical pages prints in `.claude/skills/multi-skill/pagination-map.md`. Step 2 states why; this file is the procedure.

The map is the per-raw record `lint`'s `locator_page_mismatch` checks every `p. M` against, and the record the anchor-only locator exemption keys on (`citation_locator_incomplete` / `source_locator_incomplete`). Without it a `p. M` cannot be checked at all.

## Propose, then confirm

```bash
python3 .claude/skills/multi-skill/scripts/pagination_map.py 0-raw/papers/{stem}.pdf                    # propose a map from the footers
python3 .claude/skills/multi-skill/scripts/pagination_map.py --verify 0-raw/papers/{stem}.pdf {outdir}  # render footer crops to eyeball
```

The generator proposes; **you confirm.** Eyeball every proposed line against its rendered footer crop before adding the `## 0-raw/papers/{stem}.pdf` section to the map. This is not ceremony: a wrong `none` licenses stripping a correct printed page out of a citation, and a wrong number sends a reader to a page the source does not carry — both pass every structural check afterwards, because the map is what those checks believe.

## When a raw is not registered

An unregistered raw still ingests. The locator-completeness checks fall back to the `app.`-anchor heuristic, `locator_page_mismatch` simply cannot run on it, and lint raises `pagination_map_unregistered` as an Info nudge. Register it rather than leaving the nudge standing — `audit` reads the map and does not maintain it, so an unregistered raw stays unverifiable on this axis for every later run.

In existing-source mode, register the raw if it is not already registered; a reingest is the natural moment to close that gap.
