# Qdrant real binding reuse audit — 0283-r1

## Purpose

Resume the controlled-real-Qdrant work without duplicating phase 0271.

The 0271 audit already established the protocol and implementation decision.
The repository now contains both:

```text
QdrantProjectionExecutor protocol
→ QdrantClientProjectionExecutor
→ SqlAuthorityScopedQdrantExecutor
```

Therefore phase 0283 must not add another Qdrant executor, Qdrant manager,
Scheduler, worker, queue or per-specialist Qdrant authority.

## Existing surfaces to reuse

| Surface | Reuse decision |
|---|---|
| `controlled_real_qdrant_executor_reuse_audit_0271.py` | retain as the historical executor reuse decision |
| `qdrant_projection_adapter.py` | retain the protocol, projection batch and reference-only recall contracts |
| `qdrant_client_projection_executor.py` | reuse as the sole concrete qdrant-client membrane |
| `qdrant_sql_authority_scope.py` | wrap the concrete executor before projection or recall |
| `scheduler_managed_embedding_qdrant_projection_usage_0262.py` | reuse as the Scheduler-owned projection use case |
| `scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py` | reuse as the Scheduler-owned recall and SQL rehydrate use case |
| `check_qdrant_client_projection_executor_0271.py` | reuse dependency and implementation checks |
| `check_qdrant_sql_authority_scope_0271.py` | reuse authority-scope and strict-gRPC checks |

## Audit conclusion

```text
previous_reuse_audit_reused: true
existing_real_executor_found: true
existing_sql_authority_scope_found: true
new_executor_module_justified: false
existing_executor_must_be_reused: true
sql_authority_scope_must_wrap_executor: true
scheduler_managed_projection_usage_reused: true
scheduler_managed_recall_usage_reused: true
binding_surface_missing: true
```

The missing capability is a controlled composition/binding surface that builds
the existing concrete executor, wraps it in the existing SQL-authority scope,
then injects it into the existing 0262/0263 use cases.

## Required binding order

```text
validated connection configuration
→ QdrantClientEffectGate
→ build_qdrant_client_projection_executor
→ SqlAuthorityScopedQdrantExecutor
→ inject into 0262 projection or 0263 recall
→ close injected executor
```

The binding must not:

- start or administer Qdrant;
- create collections implicitly;
- make Qdrant the durable content authority;
- serialize API keys;
- bypass the effect gate;
- bypass the SQL-authority scope;
- modify `Scheduler.run`;
- create one Qdrant database or authority per specialist.

## Planned 0283 sequence

```text
0283-r1  real binding reuse audit                         [this phase]
0283-r2  immutable binding configuration and policy
0283-r3  scoped executor factory composition
0283-r4  controlled Scheduler projection binding
0283-r5  controlled Scheduler recall/SQL-rehydrate binding
0283-r6  collection compatibility and effect readiness gate
0283-r7  preview-first real projection/recall CLI
0283-r8  local-Qdrant projection→recall→SQL smoke
```

## Locked boundaries

```text
runtime_source_modified: false
new_runtime_module_added: false
new_executor_added: false
new_scheduler_added: false
new_worker_added: false
new_qdrant_authority_added: false
qdrant_collection_creation_added: false
qdrant_write_performed: false
qdrant_search_performed: false
network_used: false
sql_write_performed: false
scheduler_modified: false
external_dependencies_added: false
projects_repository_change_required: false
```
