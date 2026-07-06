# Code rule 0153 — Architecture docs and surface audit

0153 may add a read-only audit tool for architecture docs, DOT files, and reusable runtime surfaces.

Required:

- the audit must be read-only against runtime state;
- the audit may write reports only under `.var/smoke/artifacts/0153` by default;
- it must preserve the existing documentation hierarchy;
- it must not rewrite historical phase docs automatically;
- it must distinguish E5, OpenVINO, Qdrant, SQL, RouteProxy, and Scheduler roles;
- it must keep SQL as durable authority and Qdrant as projection/recall only.

Forbidden:

- must not create SQLPersistenceWorker;
- must not create SQLOrchestrator;
- must not create LocalArtifactOrchestrator;
- must not create LocalVectorIndexingOrchestrator;
- must not create SchedulerOpenVINORunner;
- must not create VectorOpenVINOEmbeddingAdapter;
- must not create VectorQdrantProjectionAdapter;
- must not import OpenVINO backend clients;
- must not import Qdrant backend clients;
- must not modify the Scheduler run loop.
