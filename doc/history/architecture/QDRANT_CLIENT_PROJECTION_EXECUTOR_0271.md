# 0271-r2 — qdrant-client projection executor

## Decision

The 0271-r1 source audit found the existing
`QdrantProjectionExecutor` protocol but no concrete non-demo implementation.
The operator selected the official `qdrant-client` SDK instead of maintaining a
custom HTTP implementation.

0271-r2 therefore adds one narrow IO implementation:

```text
QdrantProjectionExecutor protocol
            |
            v
QdrantClientProjectionExecutor
            |
            v
qdrant_client.QdrantClient
            |
            v
Qdrant service started by OpenRC / OS / admin
```

## Durable authority and payload

SQL remains the durable authority. Every projected point carries both
`payload.sql_ref` and the historical `payload.sql_context_ref` alias. Recall
returns reference-only hits that must be rehydrated through SQL.

Autodoc point references such as `qdrant-point:...` are not valid native Qdrant
point IDs. The executor derives a deterministic UUID for Qdrant storage and
preserves the original typed reference in `payload.autodoc_point_ref`.

## Gates

Construction requires an immutable `QdrantClientEffectGate` with a typed
`policy_decision_id`. Writes and searches are separately authorized. The
executor fails before calling the SDK when the corresponding gate is false.

## Dependency

The official dependency is pinned in:

```text
config/requirements-qdrant-client-0271.txt
```

The SDK import is delayed until the executor factory is called. Repository tests
use an injected fake client and do not require a running Qdrant service.

## Boundaries

- no Qdrant service start or stop;
- no OpenRC or `rc-service` call;
- no collection creation in this phase;
- no Scheduler modification;
- no RuntimeManager or Orchestrator;
- no SQL write;
- no OpenVINO execution;
- no EventBus or PassiveSupervisor command;
- no SHM, mmap, RouteProxy or ControlProxy modification;
- no GitHub call.

The SHM data-plane remains responsible for fast local transient coordination.
The SDK executor is an external IO edge and must never run inside a SHM critical
section.

## Next

0271-r3 may inject this executor into the existing 0262 and 0263 CLIs and add a
separate opt-in live smoke. The 0269 composition must keep its demo gate until
that live path is validated against the operator's Qdrant service.
