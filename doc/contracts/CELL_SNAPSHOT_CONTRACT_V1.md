# Cell Snapshot Contract v1

```text
schema: missipy.cell.v1
```

The cell snapshot contract is the first stable observation contract for the
cell-population visualization track.

It is observation-only.

A cell snapshot is not a command, not an action request, not a live task handle,
and not a mutable runtime object.

## Purpose

The same immutable snapshot can be consumed by:

```text
VisPy desktop viewer
future mobile browser view
offline analysis scripts
replay/debug tools
```

The renderer changes. The contract does not silently change.

## Minimal fields

```text
schema
cell_id
source_task_id
source_component_id
source_class
score
age
cost
lifecycle_state
observed_at
```

## Lifecycle states

```text
created
queued
running
waiting
completed
failed
cancelled
dropped
```

## Versioning rule

Future enrichment requires a new schema version such as:

```text
missipy.cell.v2
```

Existing `missipy.cell.v1` fields must not be silently repurposed.

## Boundary rule

The contract module must not import VisPy, Scheduler, EventBus, recorder,
server, network, OpenVINO, or external API clients.

Producer and consumer modules may depend on this contract. This contract must
not depend on producers or consumers.

## Health rule

The contract stores primitive observation values. It does not define the final
fitness or optimization policy.

Health mapping belongs to later visualization/replay code and must compare the
observed lifecycle with the expected lifecycle for the source class.
