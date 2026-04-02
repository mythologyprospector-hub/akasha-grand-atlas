# Grand Atlas

Grand Atlas is an **Akasha-adjacent source discovery and registry engine** for external tools, APIs, datasets, suppliers, archives, and web resources.

It began life as a bookmark atlas. It now serves a clearer role in the Akasha ecosystem:

- **discover** outside resources
- **rank** and filter candidates
- **review** likely additions with low human friction
- **track** which sources are merely interesting, which are approved, and which are adopted by Akasha systems

## Akasha role

Grand Atlas is **not** Akasha core.

It is the neighboring **registry/scout layer**.

Relationship to nearby repos:

```text
Grand Atlas        discovers and ranks sources
akasha-apis        implements chosen adapters to those sources
akasha-time-nexus  consumes adapters to build contextual event records
```

That means Grand Atlas should remain broad enough to scout the outside world, while still being disciplined enough to feed Akasha cleanly.

## Canonical rule

The canonical dataset is:

```text
data/bookmarks.csv
```

Everything else is derived, generated, or review-oriented.

## What this repo contains

- `data/` — canonical bookmark/source registry data and schema
- `scripts/` — harvesting, ranking, verification, promotion, and build tooling
- `site/` — static site source files and browser-side UI assets
- `.github/workflows/` — optional automation for harvesting, verification, and publishing
- `docs/` — alignment and architecture notes

## What this repo does

Grand Atlas can:

- harvest sources from curated lists and public endpoints
- rank sources into auto-promote / review / ignore bands
- build lightweight review dashboards
- generate a searchable static atlas
- export Chrome-compatible bookmarks
- support human-in-the-loop promotion into canon

## What this repo is not

Grand Atlas is **not**:

- the live adapter layer
- the time/context engine
- the meaning-making or interpretation layer
- Akasha core

Those roles belong elsewhere.

## Recommended workflow

```bash
python scripts/harvest_v3.py
python scripts/rank_candidates.py
python scripts/build_ranked_review_dashboard.py
```

Then, after review and approval:

```bash
python scripts/atlas_promote_ranked.py
python scripts/build_atlas.py
```

## Design principles

- CSV canon
- low-friction review
- broad discovery, narrow adoption
- generated artifacts should not become accidental canon
- Akasha-facing integration should stay explicit, not implied

## Near-term Akasha use

Grand Atlas is especially useful for scouting sources relevant to:

- weather context
- astronomy / moon / solar data
- timezone and geospatial context
- tides and hydrology
- geomagnetic / space weather
- ecology / forestry / biodiversity
- open datasets and research sources

## Status

This repo is ready to be pushed as an **Akasha-approved neighbor**.
It should remain a registry and discovery engine, while `akasha-apis` and `akasha-time-nexus` take on adapter and context responsibilities.

## Engine Role

TODO: fill this section.

## Why it exists

TODO: fill this section.

## Inputs

TODO: fill this section.

## Memory / Registry

TODO: fill this section.

## Relation Model

TODO: fill this section.

## Evaluator

TODO: fill this section.

## Outputs

TODO: fill this section.

## Position in Constellation

TODO: fill this section.

## Next Steps

TODO: fill this section.
