# Rule 0271-r5 — SQL-authority scope live binding

1. SQL remains the durable authority; Qdrant stores reconstructible vectors and
   typed references only.
2. The 0262 and 0263 live tools must derive the same opaque
   `sql_authority_ref` from the same injected SQL store path and namespace.
3. Every live upsert must pass through `SqlAuthorityScopedQdrantExecutor`.
4. Every live recall must reject foreign and legacy unscoped hits before SQL
   rehydration.
5. Live data operations require strict gRPC intent; REST and gRPC ports must be
   distinct, with REST retained for administration only.
6. Existing 0262, 0263 and 0269 surfaces are extended; no new manager, worker or
   orchestrator is allowed.
7. OpenRC/OS/admin owns Qdrant startup and collection administration.
8. No API-key value, SQL database path, SHM content or remote mutation is added
   to the serialized authority proof.
