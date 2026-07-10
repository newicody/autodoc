# 0271-r1 — Controlled real Qdrant executor reuse audit

## Decision

The repository already owns the correct execution membrane:
`inference.qdrant_projection_adapter.QdrantProjectionExecutor`.
It defines both `upsert_points(...)` and `search_vector(...)` while keeping
projection contracts independent from a concrete client.

The current operational path does not contain a concrete non-demo executor:

- 0262 injects `DemoQdrantProjectionExecutor`;
- 0263 injects `DemoQdrantRecallExecutor`;
- 0269 requires the explicit `--demo-qdrant` gate;
- 0247/0248 are readiness-only and prohibit Qdrant API calls;
- 0210/0211/0212 audit, plan and accept contracts without writes.

Therefore 0271-r1 authorizes a later, narrow IO implementation of the existing
protocol. It does **not** authorize a Qdrant manager, Scheduler lifecycle owner,
new projection contract, or durable Qdrant authority.

## Required next shape

0271-r2 should implement the existing protocol in a small IO-edge module, use
an explicit endpoint/collection/policy decision, return existing immutable
write/recall results, preserve `payload.sql_ref`, and never start Qdrant.
The dependency choice must remain explicit; no third-party dependency is added
by this audit.
