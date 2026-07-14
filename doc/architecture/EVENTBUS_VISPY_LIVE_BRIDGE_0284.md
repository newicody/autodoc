# EventBus → VisPy live bridge — 0284-r1-r1

## Decision

Reuse the existing observation stack rather than introduce another bus, scheduler, viewer or snapshot schema.

```text
Scheduler and components
        │ observable Event
        ▼
existing EventBus
        │ subscribe(None)
        ▼
EventBusCellLensLiveBridge
        │ CellObservationEvent
        ▼
existing missipy.cell.v1 append-only journal
        │ tail, 0.25 s polling
        ▼
existing VisPy Cell Lens viewer
```

The bridge is composed only at the outer application boundary in `src/main.py`. The kernel and `Scheduler` are unchanged. It is disabled unless `MISSIPY_CELL_LENS_JOURNAL` names the journal to append.

## Reused wheels

```text
EventBus generic observation subscription
CellObservationEvent
CellSnapshot / missipy.cell.v1
CellSnapshotJournalWriter
visualize_cell_population_vispy.py --tail
cell_lens_all_view_launch_profiles.py
```

No new CLI is introduced. The existing VisPy launch profile now enables its existing `--tail` mode and documents that the producer and viewer must use the same journal path.

## Passive failure boundary

The EventBus publication path only queues the event. Journal conversion and filesystem append happen in the observer task. Filesystem work is sent through `asyncio.to_thread`; conversion or write failures are accumulated in immutable diagnostic stats and are not published back to the bus.

The bridge never:

```text
calls Scheduler.emit
publishes an Event
changes policy or priority
writes SQL
writes or searches Qdrant
loads OpenVINO or an LLM
calls GitHub
commands a component
```

## Identity projection

The existing metadata is reused when available, in this order:

```text
cell_id
specialist_ref
laboratory_ref
visit_ref
route_ref
sql_ref
qdrant_ref
correlation_id
source component
```

This keeps the bridge compatible with current components and lets phase 0284 specialist/laboratory references appear without changing the `missipy.cell.v1` schema.

## GitHub Copilot visibility boundary

Copilot advisory visibility in ProjectV2 is intentionally not coupled to this observer. It requires a separate controlled remote-publication patch because the current workflow stores the advisory as an Actions artifact but does not project it into an Issue comment or ProjectV2 custom field.
