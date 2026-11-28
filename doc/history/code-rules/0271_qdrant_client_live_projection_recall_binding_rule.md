# Rule 0271 — qdrant-client live projection/recall binding

1. The live path must implement the existing QdrantProjectionExecutor boundary;
   it must not introduce a second Qdrant manager, worker or orchestrator.
2. Live Qdrant is an explicit live opt-in and is mutually exclusive with demo
   Qdrant.
3. Projection requires a write-only effect gate; recall requires a search-only
   effect gate. Both require a typed `policy_decision_id`.
4. SQL remains the durable authority. Qdrant hits must carry `sql_ref` and are
   rehydrated from the existing SQL context store.
5. OpenRC/OS/admin starts Qdrant. Scheduler and these CLIs never start or install
   services.
6. API-key values must not appear in command-line arguments, reports, manifests
   or logs. Only the environment-variable name may be serialized.
7. The live path does not read or write SHM and does not modify RouteProxy,
   ControlProxy or the Scheduler loop.
8. Collection creation and schema migration remain separate readiness/admin
   concerns.
