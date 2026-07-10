# Rule 0271-r4 — SQL-authority scope and strict gRPC

1. SQL remains the durable authority; Qdrant stores reconstructible vectors and
   typed references only.
2. Every scoped Qdrant point carries `payload.sql_authority_ref` and
   `payload.sql_store_kind`.
3. Recall results from another authority, and legacy unscoped hits, are rejected
   before SQL rehydration.
4. The implementation wraps the existing `QdrantProjectionExecutor`; no second
   manager, worker or orchestrator is allowed.
5. REST administration and gRPC data operations use distinct ports. Strict data
   gRPC requires `prefer_grpc=True`.
6. The SQL database path is used only to derive an opaque reference and is not
   serialized in the scope report.
7. OpenRC/OS/admin owns Qdrant startup and collection administration.
8. SHM remains unchanged; RouteProxy, ControlProxy and the Scheduler loop are
   outside this patch.
