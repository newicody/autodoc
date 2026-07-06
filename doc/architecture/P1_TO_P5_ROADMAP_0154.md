# P1 to P5 roadmap — 0154

This page records the active roadmap after the 0153 audit and the 0151/0152 SQL controlled-write work.

## P1 — Local artifact pipeline

Goal: one local artifact can be indexed, projected, persisted, and read back.

Status: mostly complete.

Completed capabilities:

- OpenVINO/E5 live vector generation.
- Qdrant REST projection/search.
- Strict machine-vector handoff.
- Scheduler-shaped request frames through RouteProxyRuntime.
- Dynamic artifact/job route refs.
- Result frames.
- Artifact reports.
- SQL handoff and persistence records.
- Real DB-API write through `DbApiSqlContextStore.upsert_record`.
- Stable configured local DB path.

Remaining P1 closure work:

1. Add one P1 runner that executes artifact intake, vector projection, SQL write, Qdrant search, and SQL readback in a single command.
2. Add Qdrant-to-SQL rehydration verification: search Qdrant, recover `sql_ref`, read SQL.
3. Separate `.var/smoke`, `.var/local`, and future `.var/prod` conventions.
4. Normalize collection names and model metadata through the existing registry.

## P2 — Local knowledge base ingestion

Goal: process folders/repos/documents, not just one demo artifact.

Required capabilities:

1. Filesystem intake contract.
2. Content hashing and stable source refs.
3. Chunking contract for Markdown, code, JSON, logs, and future PDF-derived text.
4. SQL document/chunk/fact records.
5. Batch embedding and batch Qdrant projection.
6. Deduplication by content hash.
7. Rebuild Qdrant projections from SQL records.
8. Collection lifecycle: smoke, local, dev, prod, archive.

## P3 — Operational Scheduler

Goal: move from smoke tools to real job lifecycle while keeping the Scheduler as orchestrator.

Required capabilities:

1. Job contracts for vector indexing, retrieval, validation, and persistence.
2. Dispatcher binding to existing handlers.
3. Status lifecycle: pending, running, done, failed, stale, cancelled.
4. Retry and timeout policies.
5. RouteProxy leases and stale-frame handling.
6. Operator CLI: run, status, list, retry, cancel.
7. EventBus observation only.
8. Optional local daemon only after tools are stable.

## P4 — Context specialists and synthesis

Goal: allow specialist outputs while preserving traceability.

Required capabilities:

1. Specialist input/output contracts.
2. Context pack builder from Qdrant recall plus SQL rehydration.
3. Validation pass with evidence refs.
4. Synthesis pass with provenance.
5. Contradiction handling.
6. Feedback records.
7. Context generations and stale record management.
8. GitHub artifact exchange design may begin here, but GitHub remains an exchange surface rather than an internal bus.

## P5 — Distributed and future hardware seam

Goal: prepare multi-node execution and later hardware acceleration without changing the core authority model.

Required capabilities:

1. Node identity contracts.
2. Distributed RouteProxy frame exchange.
3. Shard-aware SQL/Qdrant metadata.
4. Task dispatch across nodes.
5. Failure domains and replay.
6. Rebuild projections from SQL across nodes.
7. Observability and replay tooling.
8. Future PCIe/LVDS/FPGA observer only after the software protocol is stable.

## After P5

P6: observability and replay, including VisPy if the audit confirms or adds a usable surface.

P7: GitHub artifact exchange and project workflow integration.

P8: knowledge operations: rebuilds, migrations, quality checks, and benchmarks.

P9: stable multi-node operations.

P10: hardware acceleration seam.

P11: declarative job DSL and state-machine layer.

P12: packaging, services, backup/restore, and operational hardening.
