# Phase 0287-r7-r15-r3-r11-r1 — Live Qdrant projection probe

## Result

A controlled command can now select one SQL-authoritative object and one active
context revision, preview the operation without constructing OpenVINO or Qdrant,
and execute the confirmed plan through the existing live ports.

The execution path:

1. reads the object and revision from PostgreSQL authority;
2. requires an exact plan digest, operator approval and environment gate;
3. invokes the r11 `LoveQdrantLiveAnalysisProjection` once;
4. persists reconstructible `VectorProjectionMetadata` in SQL;
5. reads the exact Qdrant point back with `with_vectors=False`;
6. verifies the reference-only payload and source digest;
7. rehydrates the original object and projection metadata from SQL.

## Reuse audit

- PostgreSQL: existing `open_love_postgresql_authority` and
  `DbApiContextRevisionAuthorityStore`.
- OpenVINO: existing `build_multilingual_e5_small_pipeline`.
- Projection: existing r11 `LoveQdrantLiveAnalysisProjection`.
- Qdrant write: existing `QdrantClientProjectionExecutor`.
- Qdrant readback: additive exact-point method on the same executor membrane.

No Scheduler, laboratory manager or alternate orchestrator is introduced.

## Boundaries

- exactly one object and one point per execution;
- no collection creation, deletion or alias mutation;
- Qdrant readback disables vectors;
- Qdrant payload remains references and scalar scope metadata only;
- SQL remains durable authority;
- no source body, vectors or secret values are serialized in the receipt.

## Validation

Isolated service, executor and architecture tests: **8 passed**.
