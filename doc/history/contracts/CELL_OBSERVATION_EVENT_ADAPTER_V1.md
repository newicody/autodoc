# Cell Observation Event Adapter v1

```text
schema: missipy.cell_observation_event.v1
output schema: missipy.cell.v1
```

This adapter converts recorded observation events into stable cell snapshots.

It is observation-only. It is not a command, not an action request, and not a
mutation surface.

## Purpose

```text
EventBus / recorder observation event
→ missipy.cell_observation_event.v1
→ missipy.cell.v1 snapshot
→ JSONL journal
→ replay/tail reader
→ VisPy or analysis
```

## Command boundary

The adapter must not command the system.

Any future operator action must use:

```text
typed command → Scheduler
```

It must not travel through the observation event adapter or the EventBus.

## Replacement rule

This is the handoff point for replacing synthetic journal production with real
recorded observations. The visualizer continues to read the same
`missipy.cell.v1` journal.
