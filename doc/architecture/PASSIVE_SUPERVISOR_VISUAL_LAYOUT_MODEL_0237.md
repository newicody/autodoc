# Passive supervisor visual layout model — 0237

## Intent

This patch prepares the future human visualization layer by deriving a stable
layout model from the existing passive supervisor snapshot or visual read-model.

No renderer is introduced by this patch.

## Canonical runtime path

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

The layout model is downstream-only.

## Visual layout path

```text
snapshot/read-model -> visual layout model
```

The output contains deterministic:

```text
zones
nodes
edges
positions
```

## Boundary

The layout model is read-only. It does not execute Scheduler logic, create an
EventBus, control proxy/SHM/policy, mutate SQL/Qdrant/GitHub, or push status
back to external systems.

## Future renderer

A future renderer may read the layout JSON. The renderer must remain a view and
must not own runtime authority.
