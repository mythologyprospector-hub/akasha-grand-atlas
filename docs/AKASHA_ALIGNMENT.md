# Akasha Alignment

## Why Grand Atlas exists

Grand Atlas is the **outside-world scout** for Akasha.

It finds and ranks sources that may later become:

- implemented adapters in `akasha-apis`
- active context providers for `akasha-time-nexus`
- approved research, tool, or dataset references for other Akasha systems

## Boundary

Grand Atlas should remain:

- broad in discovery
- disciplined in canon
- explicit in Akasha adoption

It should not become:

- the API adapter layer
- the time/context nexus
- Akasha core

## Adoption flow

```text
Grand Atlas discovers source
→ human review or ranking blesses source
→ akasha-apis may implement adapter
→ akasha-time-nexus may consume adapter
```

## Canon and generated artifacts

Canonical data lives in `data/bookmarks.csv`.
Generated outputs and review artifacts should be rebuildable.

## Suggested future field

A future Atlas field such as `akasha_status` may track one of:

- `candidate`
- `approved`
- `adapter_exists`
- `in_use`
- `archived`

This is documented here first so the concept is preserved without forcing a script-breaking schema jump today.
