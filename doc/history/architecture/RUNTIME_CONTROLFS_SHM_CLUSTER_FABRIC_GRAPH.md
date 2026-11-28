# Runtime ControlFS / SHM / RouteProxy / Cluster Fabric architecture

Status: locked architecture note for the next development tasks.

This document updates the runtime graph after the Gateway/Proxy concept was corrected into a passive RouteProxy model.

## Locked vocabulary

Use these terms consistently:

- **SecurityFS**: persistent rule surface, usually `/etc/autodoc/security`.
- **Scheduler**: decision authority. It reads security snapshots and active context, then writes desired state.
- **ControlFS**: Unix filesystem state surface, usually `/run/autodoc/controlfs`.
- **RouteProxy**: passive reconciler. It watches ControlFS and materializes routes.
- **SHM Runtime**: local fast runtime surface in `/dev/shm/autodoc`.
- **DataHandle**: compact reference to a payload stored outside the hot bus.
- **Recorder**: durable journal writer.
- **ZFS Store**: persistent journal, contracts, artifacts, replay and snapshots.
- **NetworkBridge**: future software extension for remote routes and handles.
- **Hardware Cluster Fabric**: distant future FPGA/ASIC PCIe/LVDS extension for passive network observation, acceleration and cluster routing.

Avoid the old wording:

- `Gateway calls Scheduler`
- `RuntimeProxy commands Scheduler`
- `Proxy decides access`
- `FPGA shares /dev/shm directly`

Correct wording:

- `Scheduler writes desired route state into ControlFS.`
- `RouteProxy passively watches ControlFS.`
- `RouteProxy creates/deletes shm routes and semaphores.`
- `Workers use only materialized routes.`
- `FPGA/ASIC exposes DMA-backed route buffers through a HardwareBridge, not direct /dev/shm sharing.`

## Core invariant

```text
SecurityFS decides the rules.
Scheduler compiles and writes desired state.
ControlFS carries declarative state.
RouteProxy materializes routes.
SHM Runtime carries fast local runtime traffic.
DataHandle references heavy payloads.
Recorder persists facts.
ZFS Store keeps durable memory.
NetworkBridge and Hardware Cluster Fabric are future extensions.
```

## Current local graph

```text
                         +--------------------------------+
                         | SecurityFS                     |
                         | /etc/autodoc/security          |
                         | subsystem rules / zones/scopes |
                         +---------------+----------------+
                                         |
                                         | read + compile
                                         v
                         +--------------------------------+
                         | Scheduler                      |
                         | decision authority             |
                         | security snapshot in RAM       |
                         | active context / budget/order  |
                         | writes desired route state     |
                         | does not create shm            |
                         +---------------+----------------+
                                         |
                                         | mkdir/write/rename desired state
                                         v
+--------------------------------------------------------------------------------+
| ControlFS Unix                                                                 |
| /run/autodoc/controlfs                                                         |
| desired/routes/  leases/  revoked/  status/  active/routes/                    |
| This is the runtime access surface formerly confused with Gateway/Proxy.        |
+-------------------------------+------------------------------------------------+
                                |
                                | passive watch / reconcile
                                v
                         +--------------------------------+
                         | RouteProxy                     |
                         | external passive reconciler    |
                         | does not call Scheduler        |
                         | does not decide policy         |
                         | creates/deletes shm routes     |
                         | creates/deletes semaphores     |
                         | writes active/status           |
                         +---------------+----------------+
                                         |
                                         | materialize
                                         v
+--------------------------------------------------------------------------------+
| SHM Runtime local                                                              |
| /dev/shm/autodoc                                                              |
| event.bus  context.bus  data.index  routes/<route_id>/  semaphores             |
| Fast path: mmap/shm/memfd/ring buffers + semaphore/eventfd/futex wakeups.      |
+-------------------------------+------------------------------------------------+
                                |
                                | route access
                                v
                         +--------------------------------+
                         | Workers / Experts              |
                         | RetrievalWorker                |
                         | VariantGeneratorStub now       |
                         | future MVTC / Qdrant workers   |
                         | use materialized routes only   |
                         +---------------+----------------+
                                         |
                                         | events / context patches / data handles
                                         v
+-------------------------+       +--------------------------------+
| event.bus / context.bus |------>| Recorder                       |
| lightweight facts       |       | journal / replay writer        |
+-------------------------+       +---------------+----------------+
                                                 |
                                                 | durable write
                                                 v
                                      +----------------------------+
                                      | ZFS Store                  |
                                      | journal / contracts        |
                                      | artifacts / replay         |
                                      | snapshots / ARC            |
                                      +-------------+--------------+
                                                    |
                                                    v
                                      +----------------------------+
                                      | Cell Lens                  |
                                      | observation, not hot path  |
                                      +----------------------------+
```

## ControlFS is not the hot bus

ControlFS is a Unix filesystem state surface. It is used when a route or lease changes.

Examples:

```text
desired/routes/baby_fork.retrieval/
desired/routes/baby_fork.variant_stub/
desired/routes/baby_fork.context_gate/
leases/<lease_id>/
revoked/<route_id>/
status/<component_id>/
active/routes/<route_id>/
```

The hot path is not repeated filesystem mutation. The hot path is:

```text
route exists
-> shm ring buffer exists
-> semaphore/eventfd wakes readers
-> worker reads/writes compact messages
-> heavy payloads are referenced by DataHandle
```

## SHM Runtime layout

Recommended local runtime layout:

```text
/dev/shm/autodoc/
  event.bus
  context.bus
  data.index

  routes/
    baby_fork.retrieval/
      ring
      index
      state

    baby_fork.variant_stub/
      ring
      index
      state

    baby_fork.context_gate/
      ring
      index
      state
```

Recommended semaphore namespace:

```text
/autodoc_event_bus
/autodoc_context_bus
/autodoc_data_index
/autodoc_route_<route_id>_read
/autodoc_route_<route_id>_write
/autodoc_route_<route_id>_control
```

A semaphore does not carry a message. It only wakes a reader/writer. The message is in shm.

## Bus count

For the current architecture, lock this shape:

```text
1. ControlFS        declarative route state, not a fast bus
2. event.bus        lightweight facts
3. context.bus      compact active context and patch proposals
4. data.index       handles to heavy payloads
5. routes/*         dynamic shm channels created by RouteProxy
```

Do not add more buses until the smoke path proves a real bottleneck.

## Scheduler reachable surface

The Scheduler should not become a throughput pipe. Its reachable surface is extended by shared local surfaces:

```text
SecurityFS    rules
ControlFS     desired route state
context.bus   compact context
event.bus     facts that affect scheduling
data.index    handles and payload metadata
```

The Scheduler sees compact identifiers:

```text
route_id
lease_id
context_id
data_handle
schema
hash
size
zone
budget
status
```

The Scheduler should not transport:

```text
large PDFs
large embeddings
large blobs
network streams
video/audio payloads
full datasets
```

## Local performance model

```text
very hot:
  CPU cache + RAM + shm + mmap + ring buffers + semaphores

hot durable:
  ZFS ARC + NVMe datasets

cold durable:
  ZFS datasets + HDD + snapshots
```

`/dev/shm` does not use ZFS ARC directly. ZFS ARC helps the durable side: journals, contracts, artifacts, replay, documents and persistent stores.

## Current baby-fork target flow

```text
ProjectRequest
-> context.bus or initial task surface
-> Scheduler reads active context/security snapshot
-> Scheduler writes desired/routes/baby_fork.retrieval
-> RouteProxy materializes /dev/shm/autodoc/routes/baby_fork.retrieval
-> RetrievalWorker uses route and emits retrieval.completed
-> Scheduler allows baby_fork.variant_stub route
-> VariantGeneratorStub produces variants
-> ContextGate validates ContextPatchProposal
-> context.versioned event is recorded
-> Recorder persists to ZFS
-> Cell Lens observes durable journal
```

## Future software network extension

NetworkBridge is future, not V0.

```text
SHM Runtime local
  event.bus / context.bus / data.index / routes/*
        |
        v
NetworkBridge future
  replicate selected facts
  translate local handle -> remote handle
  expose remote route status
  never replace Scheduler authority
        |
        v
remote server SHM Runtime future
```

NetworkBridge must not turn the Scheduler into a network payload pipe. It only extends reachable surfaces through compact events, remote handles and route metadata.

## Distant future hardware extension

Hardware Cluster Fabric is future lointain and must not be implemented now.

It keeps together two linked ideas:

1. A PCIe FPGA/ASIC network-oriented passive observer/accelerator.
2. A distributed server cluster where tasks are dispatched across machines while contexts and data can be recovered through a fast route.

Conceptual shape:

```text
Server A SHM Runtime
  routes/*  context.bus  data.index
        |
        v
PCIe HardwareBridge
  DMA-backed route buffers
  BAR/MMIO control
  MSI-X/eventfd notifications
        |
        v
FPGA/ASIC passive network fabric
  observe / monitor / anticipate flows
  accelerate routing decisions
  bridge machines through LVDS or a dedicated direct link
        |
        v
FPGA/ASIC passive network fabric
        |
        v
PCIe HardwareBridge
        |
        v
Server B SHM Runtime
```

Correct hardware wording:

```text
FPGA/ASIC does not share /dev/shm directly.
FPGA/ASIC exposes DMA-backed route buffers and hardware notifications.
HardwareBridge presents them as shm-like routes to the runtime.
```

This is deliberately not part of the current implementation. It only conditions the architecture so that local routes, remote routes and hardware routes remain compatible concepts.

## Architecture lock

The current implementation should only document and prepare this model.

Do not implement now:

```text
NetworkBridge
HardwareBridge
RDMA/DPDK/AF_XDP
FPGA/ASIC control
cluster scheduling
remote context replication
```

Implement first:

```text
ControlFS schema
RouteProxy dry-run model
local shm route vocabulary
event/context/data handle rules
baby-fork smoke project integration
documentation and rule tests
```
