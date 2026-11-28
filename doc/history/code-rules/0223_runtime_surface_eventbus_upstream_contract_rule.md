# 0223 Rule — Runtime Surface EventBus Upstream Contract

This rule locks passive supervision for RouteProxy, ControlProxy, SHM, and Policy.

## Required direction

Runtime/control surfaces are upstream of passive supervision:

```text
RouteProxy / ControlProxy / SHM / Policy
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
```

The Scheduler remains orchestration authority. The passive supervisor remains
downstream-only.

## Mandatory constraints

Future code MUST:

- reuse the existing EventBus contract/surface when available;
- reuse or extend the existing passive supervisor surface when available;
- keep EventBus as the canonical observation transport;
- keep snapshot and events.jsonl optional outputs only;
- preserve CellularState as a projection, not an owner;
- keep cell locality/movement as visualization/projection metadata only;
- treat RouteProxy, ControlProxy, SHM, and Policy as observed upstream surfaces;
- document any fallback/replay helper as non-canonical.

Future code MUST NOT:

- create a new EventBus implementation for this supervision path;
- make status JSON or events.jsonl the normal runtime transport;
- call, wrap, or modify `Scheduler.run()`;
- control RouteProxy or ControlProxy;
- claim or release proxy leases;
- write SHM or mutate SHM cursors/slots;
- use raw `/dev/shm` or mmap as the passive supervisor's required path;
- decide policy or become a policy engine;
- write SQL or Qdrant;
- mutate GitHub;
- introduce VisPy into the runtime path;
- add a non-stdlib dependency for this contract phase.

## Acceptance intent

A valid implementation phase can be accepted only if the passive supervisor is a
consumer of canonical EventBus events and remains downstream-only.
