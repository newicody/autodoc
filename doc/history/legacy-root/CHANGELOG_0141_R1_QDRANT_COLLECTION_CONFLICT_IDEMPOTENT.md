# Changelog 0141-r1 — Qdrant collection conflict idempotent

Fixed:

- `tools/run_qdrant_projection_live_smoke.py` now treats HTTP 409 on collection ensure as idempotent collection-already-exists.
- Added a unit test that simulates the Qdrant 409 response.

No new Qdrant adapter, Scheduler integration, RouteProxy worker, daemon, or qdrant_client dependency was added.
