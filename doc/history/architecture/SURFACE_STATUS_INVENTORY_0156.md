# Surface status inventory — 0156

## Purpose

The repository already contains surfaces for P1 to P5 and beyond. Some are
validated, some are partial, some are future-facing, and some are historical.

0156 classifies them before further implementation.

The rule is:

```text
Do not delete.
Do not recreate in parallel.
Classify first.
Reuse or extend existing surfaces when possible.
Deprecate only with proof.
```

## Status definitions

| Status | Meaning |
| --- | --- |
| `current` | Active development axis. |
| `validated` | Smoke-tested or readback-tested path. |
| `partial` | Contract/surface exists but the full loop is incomplete. |
| `planned` | Future direction; no runtime authority yet. |
| `historical` | Kept for traceability and design history. |
| `superseded` | Replaced by a newer preferred surface, but retained. |
| `deprecated` | Should not be extended; retained until safe removal. |
| `blocked` | Cannot progress without a missing dependency or decision. |

## Current / validated P1 axis

| Phase | Surface | Status | Decision |
| --- | --- | --- | --- |
| 0138 | OpenVINO/E5 live smoke existing path | `validated` | Reuse. |
| 0139 | Qdrant projection live smoke existing path | `validated` | Reuse. |
| 0140 | Qdrant REST projection smoke | `validated` | Reuse for local/operator smoke only. |
| 0141 | Local vector indexing live smoke | `validated` | Reuse as proof of chain. |
| 0142 | Machine vector handoff | `validated` | Reuse handoff format. |
| 0143 | Scheduler vector indexing smoke | `validated` / `partial` | Reuse Scheduler-shaped boundary. |
| 0144 | Scheduler vector indexing result frame | `validated` / `partial` | Reuse result-frame shape. |
| 0145 | Local artifact vector indexing runner | `validated` / `operator` | Candidate base for P1 single runner; not an orchestrator. |
| 0146 | Artifact intake contract | `validated` | Reuse. |
| 0147 | Dynamic artifact route refs | `validated` | Reuse; no static route refs. |
| 0148 | SQL persistence handoff | `validated` | Reuse. |
| 0149 | SQL context store persistence record | `validated` | Reuse. |
| 0150 | SQL write surface audit | `validated` / `audit` | Reuse audit discipline. |
| 0151 | SQL controlled write | `validated` | Reuse `DbApiSqlContextStore.upsert_record`. |
| 0152 | Configured SQL context DB path | `validated` | Reuse DB path precedence. |
| 0153 | Architecture docs and surface audit | `validated` / `audit` | Reuse before new surfaces. |
| 0154 | Current-state docs refresh | `validated` / `doc` | Reuse roadmap. |
| 0155 | Canonical global graph refresh | `validated` / `doc` | Continue, do not replace. |

## Reusable / partial surfaces

| Family | Status | Reuse direction |
| --- | --- | --- |
| ControlFS / RouteProxy / frame codec / ring buffer | `partial` / `historical` | Inspect before reuse; do not create a new data-plane path first. |
| RouteProxy runtime minimal | `validated` / `partial` | Reuse for P1 smoke chain; not business authority. |
| Scheduler route handler minimal | `validated` / `partial` | Reuse as Scheduler-shaped boundary until real jobs exist. |
| SQL context store / hydrator | `validated` / `partial` | Reuse for durable authority and future Qdrant -> SQL rehydration. |
| OpenVINO embedding pipeline / E5 CLI | `validated` | Reuse for embeddings only. |
| Qdrant projection adapter / collection registry | `validated` / `partial` | Reuse for projection and recall only. |
| Vector indexing job plan | `partial` | Candidate for P3 Scheduler jobs after P1 closes. |
| Replay reader/writer/exporter | `partial` | Keep for observability/replay; not a live VisPy claim. |
| Cell lens / VisPy tools | `partial` | Inspect before claiming live observer support. |

## Planned / future surfaces

| Family | Status | Boundary |
| --- | --- | --- |
| GitHub project/artifact exchange | `planned` / `partial` | Projection surface only; not internal bus. |
| SourceCandidate external projection | `planned` / `partial` | Keep as future GitHub/operator exchange path. |
| Specialist liaison / synthesis | `planned` | After P1/P2/P3. |
| Server-oriented deliberation | `planned` | After local knowledge and Scheduler loops stabilize. |
| Distributed RouteProxy / cluster | `planned` | After local loop stability. |
| Hardware acceleration / PCIe/LVDS/FPGA/ASIC | `planned` | Long-term, not current P1/P2 path. |

## Deprecated / superseded candidates

0156 does not mark any Python runtime code as abandoned.

A future deprecation must prove:

```text
- no current tests depend on it;
- no current docs/changelogs mark it as active;
- it duplicates a validated newer surface;
- it violates current code rules or architecture boundaries;
- a replacement path is named explicitly.
```

Until then, use `historical`, `partial`, or `superseded`, not `abandoned`.

## Immediate next development axis

```text
0157 — P1 single runner surface audit
0158 — Qdrant recall -> sql_ref -> SQL rehydration
0159 — P1 closed-loop smoke
```

0157 must begin by inspecting existing 0145, 0146, 0147, 0148, 0149, 0151,
0152 surfaces. It must not create `SQLPersistenceWorker`,
`SQLOrchestrator`, `LocalArtifactOrchestrator`,
`LocalVectorIndexingOrchestrator`, `SchedulerOpenVINORunner`,
`VectorOpenVINOEmbeddingAdapter`, or `VectorQdrantProjectionAdapter`.
