# Changelog 0140 — Qdrant projection operator REST smoke

Changed:

- `tools/run_qdrant_projection_live_smoke.py` now executes an opt-in local REST smoke when no adapter smoke entrypoint exists.

Added:

- tool tests for deterministic vector and REST payload generation
- rule tests for Qdrant/Scheduler/RouteProxy boundaries
- architecture docs, code-rule addendum, DOT graph, manifest, and phase report

No new Qdrant adapter, Scheduler runner, RouteProxy worker, daemon, or durable authority was added.
