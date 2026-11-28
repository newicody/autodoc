# Passive supervisor visual pipeline smoke — 0238

## Intent

This patch adds a local read-only pipeline that generates the visual report
chain in the correct order.

```text
0234 -> 0236 -> 0237
```

It prevents local operator mistakes where the layout step is launched before
the read-model file exists.

No renderer is introduced by this patch.

## Canonical runtime path

```text
EventBus -> PassiveSupervisorSink -> CellularState
```

The pipeline remains downstream of the passive supervisor state.

## Local report chain

```text
all-surfaces smoke -> visual read-model -> visual layout model
```

Outputs are written under `.var/reports` by default. These files are runtime
artifacts and are not authoritative source files.

## Boundary

The pipeline executes existing CLI tools in order. It does not create a service,
own runtime authority, control proxy/SHM/policy, mutate SQL/Qdrant/GitHub, or
add non-stdlib dependencies.
