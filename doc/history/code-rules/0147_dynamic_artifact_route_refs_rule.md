# 0147 code rule — dynamic artifact route refs

Artifact vector indexing must derive command refs and RouteProxy route refs from typed artifact inputs instead of static smoke refs.

Rules:

- derive artifact route refs through src/context/artifact_route_refs.py
- src/context/artifact_route_refs.py must remain pure
- do not import Scheduler, RouteProxyRuntime, OpenVINO, Qdrant, or SQL clients from the route-ref contract
- artifact runner must pass --command-ref, --request-route-ref, --result-command-ref, --result-route-ref, --vector-indexing-job-ref, --route-namespace, and --result-route-namespace to the existing Scheduler smoke tool
- do not create LocalArtifactOrchestrator
- do not create LocalVectorIndexingOrchestrator
- do not create SchedulerOpenVINORunner
- do not modify Scheduler.run()
- Scheduler remains the orchestrator
- SQLContextStore remains durable authority
- Qdrant remains projection/recall only
