# 0153 — Architecture refresh and docs/surface audit

0153 is an audit-only architecture refresh after the P1 local vector/SQL path.

Current P1 chain:

```text
artifact local
-> ArtifactIntakeContract
-> dynamic ArtifactRouteRefs
-> Scheduler-shaped RouteProxy request frame
-> OpenVINO/E5 full-vector handoff
-> Qdrant projection/search
-> RouteProxy vector_indexing_result frame
-> SQL persistence handoff
-> SqlContextRecord
-> DbApiSqlContextStore.upsert_record
-> configured DB-API SQL database
-> readback
```

Boundary:

- E5 is the embedding model family and text convention (`query:` / `passage:`).
- OpenVINO is the local inference runtime boundary used to execute the exported E5 model.
- Qdrant is the vector projection/recall index.
- SQL remains durable authority through `DbApiSqlContextStore.upsert_record`.
- RouteProxy carries fast request/result frames and is not the durable authority.
- Scheduler remains the orchestrator boundary; operator tools are still smoke/CLI bridges until P3.

0153 adds `tools/audit_architecture_docs_and_surfaces.py` to inspect:

- reusable code surfaces so we do not redevelop existing components,
- documentation and DOT inventory,
- stale static route refs in historical docs,
- current SQL store AST surface,
- rough phase-completeness rollups.

0153 does not rewrite historical docs. The next docs patch should use the audit output to create current-state index pages and targeted fixes while preserving the existing hierarchy.
