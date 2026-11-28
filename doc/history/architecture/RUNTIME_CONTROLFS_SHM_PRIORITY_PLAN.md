# Runtime ControlFS / SHM development priorities

Status: development priority plan.

This plan converts the locked graph into practical next tasks. It keeps the current work local-first and avoids implementing the distant cluster/hardware fabric too early.

## Priority 0: lock the vocabulary and graph

Goal: make the architecture readable and stable before changing runtime code.

Deliverables:

- Locked graph document.
- Glossary for SecurityFS, Scheduler, ControlFS, RouteProxy, SHM Runtime, DataHandle, Recorder, ZFS Store, NetworkBridge and Hardware Cluster Fabric.
- Explicit statement that RouteProxy is passive.
- Explicit statement that Scheduler writes desired state, not shm.
- Explicit statement that NetworkBridge and Hardware Cluster Fabric are future only.

Acceptance checks:

```text
docs mention ControlFS
docs mention RouteProxy passive reconciler
docs mention SHM Runtime
docs mention ZFS durable store
docs mention future NetworkBridge
docs mention distant future Hardware Cluster Fabric
```

## Priority 1: ControlFS schema, no runtime behavior change

Goal: define the filesystem shape without wiring the real Scheduler yet.

Target layout:

```text
/run/autodoc/controlfs/
  desired/
    routes/
  active/
    routes/
  leases/
  revoked/
  status/
```

Route manifest minimal fields:

```text
route_id
task_id
zone
scope
producer
consumer
ttl
mode
schema
created_by
created_at
```

Rules:

- Scheduler owns desired state.
- RouteProxy owns active/status state.
- Workers never write desired/ or active/.
- Writes should be atomic: write temp file then rename.
- Route identifiers must be normalized and must not contain path traversal.

Acceptance checks:

```text
manifest schema documented
desired/ vs active/ ownership documented
atomic write rule documented
```

## Priority 2: RouteProxy dry-run reconciler

Goal: introduce a testable passive reconciler without creating real shm yet.

Dry-run behavior:

```text
read desired/routes/*
read active/routes/*
plan create for desired route missing in active
plan delete for active route missing in desired
plan update when manifest changed
emit route.opened / route.closed plans as data structures
```

No real shm. No real semaphore. No scheduler integration yet.

Acceptance checks:

```text
route create plan from desired entry
route delete plan when desired removed
route update plan when manifest changes
invalid manifest ignored with error event
```

## Priority 3: SHM vocabulary and local fake transport

Goal: model the runtime transport shape before using low-level IPC.

Objects:

```text
event.bus
context.bus
data.index
routes/<route_id>
semaphore names
```

Implement as Python in-memory or files first if needed, but preserve the final naming.

Acceptance checks:

```text
event message schema exists
context message schema exists
data handle schema exists
route message schema exists
```

## Priority 4: Baby-fork integration with route vocabulary

Goal: keep the baby-fork smoke project as the validation path.

Current flow remains logical and local:

```text
TaskContext v1
-> retrieval worker
-> variant stub
-> context gate
-> TaskContext v2
-> recorder/cell lens snapshot
```

Next flow should use the new vocabulary:

```text
desired/routes/baby_fork.retrieval
active/routes/baby_fork.retrieval
event retrieval.completed
context patch proposed
context versioned
data handle for evidence set if payload grows
```

Acceptance checks:

```text
baby-fork emits route-like source classes or events
baby-fork report references route_id
baby-fork still rejects nasa-antenna evidence
baby-fork still selects variant-1
```

## Priority 5: Local shm/semaphore prototype

Goal: only after dry-run and smoke graph are stable, prototype the local fast layer.

Candidate Linux mechanisms:

```text
/dev/shm tmpfs
shm_open + mmap
memfd for anonymous sealed payloads
POSIX semaphore or eventfd for wakeups
ring buffer for compact messages
```

Rules:

- ControlFS remains the declarative state.
- SHM Runtime is the hot path.
- Semaphores wake readers/writers.
- Heavy payloads stay behind DataHandle.
- Scheduler never transports large payloads.

Acceptance checks:

```text
route can be materialized in /dev/shm
reader/writer can exchange compact message
semaphore wakeup works
data handle can point to a payload
```

## Priority 6: Recorder and replay

Goal: convert runtime facts into durable memory.

Recorder consumes:

```text
event.bus
route.opened
route.closed
context.patch.proposed
context.versioned
retrieval.completed
worker.started
worker.completed
```

Recorder writes:

```text
ZFS-backed journal
replay records
cell lens snapshots
```

Acceptance checks:

```text
events survive runtime restart through journal
cell lens can show route lifecycle
replay can reconstruct baby-fork context versions
```

## Priority 7: NetworkBridge design only

Goal: prepare remote extension without implementing it.

Document only:

```text
remote_handle
remote_route
remote_event
network bridge responsibility
non-responsibility of Scheduler for network payload transport
```

Acceptance checks:

```text
NetworkBridge future appears in graph
no code depends on network bridge
local smoke tests remain local-only
```

## Priority 8: Hardware Cluster Fabric design only

Goal: preserve the distant FPGA/ASIC PCIe/LVDS project without pulling it into the current implementation.

Document only:

```text
PCIe HardwareBridge
DMA-backed route buffers
BAR/MMIO control
MSI-X/eventfd notification
passive network observation/monitoring
LVDS or dedicated direct link between machines
cluster task dispatch future
```

Acceptance checks:

```text
Hardware Cluster Fabric future appears in graph
document says not implemented now
document says FPGA/ASIC does not share /dev/shm directly
document says hardware routes are DMA-backed shm-like routes
```

## Development order summary

```text
P0 docs vocabulary and graph
P1 ControlFS schema
P2 RouteProxy dry-run reconciler
P3 SHM message/handle schemas
P4 baby-fork route vocabulary integration
P5 local shm/semaphore prototype
P6 recorder/replay integration
P7 NetworkBridge design only
P8 Hardware Cluster Fabric design only
```

## Do not do yet

```text
Do not refactor Scheduler spawn.
Do not implement network routing.
Do not implement RDMA/DPDK/AF_XDP.
Do not implement FPGA/ASIC bridge.
Do not make Qdrant source of truth.
Do not put heavy payloads in event.bus.
Do not let RouteProxy decide security.
Do not let workers write ControlFS desired/active state.
```

## Next recommended patch after this one

The next patch should be Priority 1:

```text
Introduce a documented ControlFS manifest schema and a small parser/validator.
No real shm.
No real Scheduler integration.
No real RouteProxy daemon.
```
