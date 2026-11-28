# Rule 0271 — controlled real Qdrant executor reuse audit

1. 0271-r1 is source inspection only.
2. It must not import or execute audited modules.
3. It must not call Qdrant, SQL, OpenVINO, GitHub or OpenRC.
4. It must reuse `QdrantProjectionExecutor` as the future concrete executor contract.
5. Qdrant remains projection/recall only; SQL remains durable authority.
6. A new RuntimeManager, Orchestrator, Scheduler or service lifecycle owner is forbidden.
7. The audit report may justify one narrow concrete executor module only when no live implementation exists.
8. No non-stdlib dependency is introduced by 0271-r1.
