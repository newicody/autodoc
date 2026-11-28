# Runtime pipeline retrospective changelog — 0129 to 0154

This retrospective changelog summarizes the major runtime/vector/SQL/documentation evolution that led to the current P1 pipeline.

## 0129 — RouteProxy flow-control contract

Introduced the typed RouteProxy/ControlProxy flow-control boundary: leases, writer permits, stale frames, priority hints, context generation fences and observation facts.

Boundary: RouteProxy is a fast data-plane seam, not Scheduler, not SQL authority.

## 0130 — RouteProxy runtime minimal

Introduced the minimal `/dev/shm`-oriented runtime path with permit request, frame write/read, stale marking and observation facts.

Boundary: no mount scanning and no Scheduler ownership.

## 0131 — Scheduler route handler minimal

Introduced a Scheduler-shaped handler that writes request frames through the existing RouteProxy runtime.

Boundary: Scheduler remains the orchestration authority; RouteProxy only carries fast frames.

## 0132 — Existing runtime integration audit

Added the audit rule that new runtime/adapter surfaces must not be created when existing ones can be reused or extended.

## 0133 — Existing scheduler route handler integration

Extended the existing scheduler route handler with readback and integration decision reporting instead of creating a parallel runtime.

## 0134 — Existing OpenVINO embedding path

Locked OpenVINO/E5 behind the existing embedding path and runtime boundary.

Boundary: no parallel E5 adapter.

## 0135 — Vector indexing through existing OpenVINO path

Connected VectorIndexingJobPlan to the existing OpenVINO/E5 embedding membrane.

## 0136 — Vector indexing through existing Qdrant projection path

Connected vector indexing plans to the existing Qdrant projection adapter and collection registry.

Boundary: Qdrant remains projection/recall, not durable truth.

## 0137 — Local vector indexing readiness

Added the readiness audit for local vector indexing surfaces.

## 0138 — OpenVINO/E5 live smoke

Validated local OpenVINO/E5 embedding with normalized 384-dimensional vectors.

## 0139 — Qdrant projection live smoke inventory

Audited the existing Qdrant adapter and confirmed that live execution should extend the existing tool/surface, not create a new adapter.

## 0140 — Qdrant REST projection smoke

Added opt-in Qdrant REST projection using stdlib HTTP while preserving existing adapter contracts.

## 0141 — Local vector indexing live smoke

Chained OpenVINO/E5 smoke and Qdrant projection smoke.

## 0142 — Machine vector handoff

Enabled strict handoff of a real E5 full vector JSON into Qdrant projection.

## 0143 — Scheduler vector indexing smoke

Introduced a Scheduler-shaped route request frame feeding the local vector indexing smoke.

## 0144 — Scheduler vector indexing result frame

Added vector indexing result frames containing SQL refs, Qdrant point ids, strict handoff state and request frame refs.

## 0145 — Local artifact vector indexing runner

Connected a local artifact to intake, Scheduler-shaped route frame, OpenVINO/E5, Qdrant, result frame and artifact report.

## 0146 — Artifact intake contract

Added a typed artifact intake contract for artifact refs, SQL refs, collection, dimension, route root and text kind.

## 0147 — Dynamic artifact route refs

Replaced static smoke refs with dynamic refs derived from artifact_ref and vector_indexing_job_ref.

## 0148 — SQL persistence handoff

Added a handoff record from artifact/vector indexing result to SQL persistence intent.

Boundary: handoff only; no SQL worker.

## 0149 — SQL context store persistence smoke

Mapped SQL persistence handoff to a persistence record targeting the existing SQL context store surface.

## 0150 — SQL context store write surface audit

Audited `src/context/sql_context_store.py` and selected `DbApiSqlContextStore.upsert_record` as the existing write surface.

## 0151 — SQL context store controlled write

Performed a real DB-API SQL write with readback using the existing `DbApiSqlContextStore.upsert_record`.

## 0152 — Configured SQL context DB path

Resolved the SQL context DB from CLI path, environment variable, then stable local default.

## 0153 — Architecture docs and surface audit

Audited architecture docs, DOT files, runtime surfaces and phase completeness.

## 0154 — Current-state docs refresh

Added current-state documentation, but this was not sufficient as a canonical graph refresh. The canonical source remains `00_global.dot`.

## 0155 direction

The architecture refresh must now proceed from `doc/docs/architecture/00_global.dot` and then update subordinate graph families progressively.
