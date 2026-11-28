# Portable specialist real-memory closure — 0284-r6

## Purpose

Close the memory path of the portable specialist introduced by 0284-r2/r5
without creating another SQL, embedding, projection or recall implementation.

```text
PortableSpecialistDescriptor
→ existing Scheduler / fake laboratory path (0284-r5)
→ existing SQL specialist_output authority (0274-r3)
→ existing 0261 passage embedding through OpenVINO/E5
→ existing 0283 scoped projection executor
→ Qdrant point carrying payload.sql_ref
→ existing 0261 query embedding through OpenVINO/E5
→ existing 0283 scoped recall executor
→ Qdrant reference-only hits
→ existing 0263 SQL rehydration
→ portable identity and conversation verification
```

## Authority boundary

SQL remains the durable authority. Qdrant returns references only and cannot
supply authoritative specialist content. The passage and query vectors must be
normalized multilingual-E5-small vectors of exactly 384 dimensions.

The two Qdrant bindings reuse the existing 0283 factory:

```text
QdrantClientProjectionExecutor
→ SqlAuthorityScopedQdrantExecutor
```

The projection binding is write-only. The recall binding is search-only. They
share the same target, connection, transport, SQL-authority scope, projection
policy, API-key source and policy decision. Execute mode also requires the
existing concrete `DbApiSqlContextStore`; a protocol-only fake cannot prove the
real SQL path.

## Effects

Preview performs dependency/factory inspection only. Execute requires both:

```text
authorize_real_memory = true
authorize_persistent_qdrant_point = true
```

The point and SQL record are not removed automatically. The result reports
`persistent_qdrant_point_may_exist` and `persistent_sql_record_may_exist` even
when an exception interrupts the path after effects begin. The caller remains
responsible for reviewing the returned identifiers and deciding on cleanup.

## Preserved architecture

```text
Scheduler remains the only orchestrator
new Scheduler: none
new laboratory/provider: none
new Qdrant executor: none
new transport: none
EventBus: observation only
GitHub mutation: none
ControlProxy/SHM/MMIO integration: none
```
