# Snapshot / audit / replay supervision contract — 0226

## Decision

The passive supervisor is downstream of the EventBus. Its live state is the in-memory `CellularState` maintained by `PassiveSupervisorSink`.

The runtime path is:

```text
Scheduler / RouteProxy / ControlProxy / SHM / Policy / GitHub / SQL / Qdrant
  -> EventBus
  -> PassiveSupervisorSink
  -> CellularState
```

Snapshot, audit journal, replay files, and later VisPy views are outputs or test harnesses. They are not the primary transport and must not become a second runtime backbone.

## Snapshot boundary

A snapshot is a read-only projection of the current cellular state. It exists for:

```text
debug
inspection
operator review
tests
reports
VisPy bootstrap later
```

A snapshot may be exposed as:

```text
snapshot()
write_snapshot(path)
snapshot.json generated on demand or periodically
```

A snapshot must not be used as the normal upstream input for the supervisor.

Forbidden normal path:

```text
component -> status.json -> snapshot loader -> supervisor
```

Canonical path:

```text
component -> EventBus -> PassiveSupervisorSink -> CellularState -> optional snapshot
```

## Audit journal boundary

An audit journal such as `events.jsonl` is optional. It can be enabled to keep a durable trace of observed bus events.

It exists for:

```text
audit
run proof
post-mortem analysis
regression fixtures
replay in tests
debug of old components while they are being migrated to EventBus
```

It must not be mandatory in the runtime path.

Forbidden normal path:

```text
EventBus -> events.jsonl -> supervisor
```

Allowed optional output:

```text
EventBus -> PassiveSupervisorSink -> CellularState
                               -> optional events.jsonl audit
```

Allowed replay/test harness:

```text
events.jsonl fixture -> replay harness -> PassiveSupervisorSink
```

## Replay boundary

Replay is a development and verification surface. It may feed recorded events to the same passive sink to reproduce a state.

Replay must stay visibly separate from live runtime:

```text
live mode  = EventBus subscription
replay mode = file fixture / audit journal / regression test
```

Replay must not claim authority over Scheduler, proxy, SHM, policy, SQL, Qdrant, GitHub, or pushback.

## VisPy boundary

VisPy is a future view. It must read the current projection, not own it.

Allowed later paths:

```text
VisPy -> PassiveSupervisorSink.snapshot()
VisPy -> snapshot.json
```

Forbidden paths:

```text
VisPy -> Scheduler
VisPy -> EventBus mutation
VisPy -> RouteProxy control
VisPy -> SHM write
VisPy -> Policy decision
VisPy -> SQL/Qdrant/GitHub mutation
```

## Responsibility split

```text
EventBus                  = transport
PassiveSupervisorSink     = downstream observer
CellularState             = live projection
snapshot                  = optional readable projection
events.jsonl              = optional audit/replay trace
replay harness            = tests/debug only
VisPy                     = future human view
Scheduler                 = orchestration authority
Policy                    = decision authority
Proxy/control plane       = routing/control authority
SQL                       = durable authority
Qdrant                    = projection/recall only
GitHub                    = workflow/sync surface
```

## Rule

If a feature requires `events.jsonl`, `snapshot.json`, or VisPy to be present for normal runtime supervision, it is not compliant with this contract.

The supervisor may emit outputs. It must not be driven by those outputs in the normal path.
