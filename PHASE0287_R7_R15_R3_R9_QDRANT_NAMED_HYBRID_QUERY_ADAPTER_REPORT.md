# Phase 0287-r7-r15-r3-r9 — Qdrant named hybrid-query adapter

## Result

The existing `QdrantClientProjectionExecutor` now exposes bounded named-vector
query operations for dense E5 vectors and sparse lexical vectors.

A context-layer adapter implements the already-existing hybrid-query executor
shape without importing the Qdrant SDK.

## Authority boundary

Every returned hit is reference-only:

- `point_id`;
- `sql_ref`;
- `source_ref`;
- canonical scalar scope/provenance payload;
- score.

Raw vectors and authoritative text fields fail closed. SQL remains the sole
durable content authority.

## Effect boundary

- the existing Qdrant search gate remains mandatory;
- no write operation is added;
- no collection is created or migrated;
- no Scheduler, SQL store, OpenVINO runtime or event loop is constructed.

## Validation

Isolated adapter and membrane tests: **6 passed**.

## Next unit

Provision and validate the canonical named-vector collection profile
(`dense_e5_v1` and `sparse_lexical_v1`) before projection is enabled.
