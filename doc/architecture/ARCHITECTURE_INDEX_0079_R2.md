# Architecture index - 0079-r2

## Foundation

```text
0063 ControlFS manifest schema validator
0064 RouteProxy dry-run reconciler
0065 SHM runtime message schemas
0066 baby-fork runtime projection
0067 projection compatibility correction
0068 fake local route transport
0069 fake runtime recorder ingestion
```

## ControlFS / route boundary

```text
0071 ControlFS desired manifests for baby-fork
0072 RouteProxy dry-run plan for baby-fork
0073 SHM ring buffer boundary design
0074 baby-fork runtime flow CLI
0075 fake runtime replace semantics
```

## Ring / frame layer

```text
0076 in-process ring buffer model
0077 RouteMessage frame codec
0078 in-process frame ring integration
```

## ControlProxy protocol layer

```text
0079-r2 ControlProxy sizing + prepare handshake + bus visibility
```

## Locked architecture

```text
EventBus carries facts.
Recorder persists facts.
ContextBus carries compact state.
ControlProxy = ControlFS + RouteProxy.
ControlProxy prepares/materializes routes.
Scheduler authorizes and leases route usage.
Workers send full frames only after route ready.
ControlProxy state is visible on bus for VisPy.
```

## Next

```text
0080 file-backed fixed-slot mmap route prototype
```
