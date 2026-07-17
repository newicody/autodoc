# Tool-bounded runtime lease boundary

## Purpose

A live preview factory must be able to construct machine-local resources in the
same process as the CLI and prove that those resources were released.  A module
global registry cannot transfer Python objects between the server process and a
separate command process.

## Ownership model

```text
runtime factory
  ├─ validated ImportedActionsRuntimePorts
  └─ ImportedActionsRuntimeLease
       ├─ owner_ref
       ├─ creator process_id
       ├─ ordered synchronous close hooks
       └─ exact close receipt
```

The Scheduler lifecycle remains separate:

- `externally-managed`: the CLI borrows ports and performs no lifecycle effect;
- `tool-bounded`: the CLI starts and stops the injected canonical Scheduler and
  then closes the lease-owned backend resources.

## Close order

Resources are registered in acquisition order and closed in reverse order.  A
future composer may therefore acquire:

```text
PostgreSQL → Qdrant → OpenVINO
```

and obtain:

```text
OpenVINO → Qdrant → PostgreSQL
```

at shutdown.

All hooks run even if one fails.  A failure raises a typed close error carrying
the complete receipt.  A second `close()` is a replay and performs no effect.

## Serialization boundary

`to_readback_mapping()` includes only references and outcomes.  Executable
callback objects are never serialized into an artifact, SQL payload, ProjectV2
field or Issue comment.
