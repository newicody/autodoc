# Qdrant controlled Scheduler projection binding — 0283-r4

## Purpose

Bind the existing real scoped Qdrant executor to the existing Scheduler-owned
0262 projection use case without changing the working architecture.

```text
architecture_preserved: true
existing_0262_usage_reused: true
existing_r3_factory_reused: true
```

## Current path retained

```text
Scheduler-owned command/use case
→ scheduler_managed_embedding_qdrant_projection_usage_0262
→ injected QdrantProjectionExecutor
→ SqlAuthorityScopedQdrantExecutor
→ QdrantClientProjectionExecutor
→ existing qdrant-client gRPC path
```

This phase does not modify `Scheduler.run`. It supplies the controlled binding
needed by the already-existing 0262 injection point.

## Preview

```text
command.execute=false
→ validate r2 configuration
→ build the 0262 projection request from the configured target
→ run 0262 with execute=false
→ build the deterministic projection batch
→ do not build a client
→ do not write Qdrant
```

```text
preview_constructs_client: false
```

## Execute

```text
command.execute=true
→ validate projection-only configuration
→ build the existing r3 scoped binding
→ inject binding.executor into 0262
→ perform the single controlled projection
→ close the scoped binding
```

The result reports separately whether the binding was constructed, closed and
whether an acknowledged Qdrant write was performed.

## Policy coherence

The current 0262 implementation constructs `QdrantProjectionPolicy()` itself.
This phase therefore accepts only that exact default policy. A non-default r2
policy is rejected rather than silently ignored.

A projection binding is also projection-only by default:

```text
requested_operations = ("projection",)
allow_write = true
allow_search = false
```

Recall receives its own controlled binding in r5.

## Architecture explicitly unchanged

```text
new_scheduler_added: false
scheduler_modified: false
new_qdrant_executor_added: false
new_transport_added: false
control_proxy_integrated: false
event_bus_integrated: false
shm_or_mmio_integrated: false
projects_repository_change_required: false
external_dependencies_added: false
```

The ControlProxy remains lateral control infrastructure. EventBus remains
observation. SHM/MMIO remain future orientations and are not inserted into the
Qdrant path.
