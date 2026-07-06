# Current architecture state — 0154

This page is the current-state index after the 0153 documentation and surface audit. Historical phase documents remain useful as implementation history, but this page is the canonical high-level map for the active architecture.

## Current boundary model

The active system is organized around four durable roles and two execution roles:

| Role | Current surface | Responsibility | Must not become |
| --- | --- | --- | --- |
| SQL durable authority | `src/context/sql_context_store.py` | Stores typed context records, provenance, metadata, and readback state. | Vector index, inference runtime, scheduler. |
| Qdrant projection index | `src/inference/qdrant_projection_adapter.py` plus `tools/run_qdrant_projection_live_smoke.py` | Stores recall projections with `sql_ref` payloads. | Durable truth. |
| OpenVINO/E5 embedding path | `tools/embed_e5.py`, `src/inference/openvino_embedding_adapter.py`, `src/inference/openvino_runtime.py` | Produces normalized E5 vectors. | Database or scheduler. |
| RouteProxy runtime | `src/runtime/route_proxy_runtime_minimal.py` | Fast request/result frames and readback. | Policy authority or durable store. |
| Scheduler-shaped boundary | `src/runtime/scheduler_route_handler_minimal.py` | Writes route frames and carries command-shaped intent. | Embedding runner or Qdrant client. |
| Artifact surface | `tools/run_local_artifact_vector_indexing_runner.py`, `src/context/artifact_intake_contract.py`, `src/context/artifact_route_refs.py` | Human/replayable artifact input, reports, and dynamic refs. | Hidden bus. |

## Current validated P1 chain

The validated local path is:

```text
artifact local
-> ArtifactIntakeContract
-> dynamic artifact route refs
-> Scheduler-shaped vector request frame
-> RouteProxyRuntime readback
-> OpenVINO/E5 full-vector JSON
-> Qdrant projection/search with sql_ref
-> RouteProxyRuntime result frame
-> SQL persistence handoff
-> SQLContextStore persistence record
-> DbApiSqlContextStore.upsert_record
-> SQL readback OK
```

The stable local SQL database is resolved by the controlled write smoke in this order:

```text
1. --db-path
2. AUTODOC_SQL_CONTEXT_DB
3. .var/local/sql_context_store.sqlite3
```

## Meaning of E5, OpenVINO, Qdrant, and SQL

- E5 is the embedding model. It converts text into vectors.
- OpenVINO is the local Intel inference runtime used to execute E5.
- Qdrant is the vector recall index. It stores projections and metadata such as `sql_ref`.
- SQL is the durable authority. It stores context records and makes Qdrant rebuildable.

The current invariant is:

```text
SQL owns durable context. Qdrant owns recall projections. OpenVINO/E5 owns vector generation. RouteProxy owns fast frames.
```

## Current completeness snapshot from the 0153 audit

The 0153 audit reported P1 near complete, P2 not started, P3 partially prepared, and VisPy/GitHub/distribution missing. The reported OpenVINO/E5 partial status is a static audit warning, not a live failure: the strict machine-vector handoff has been validated by the 0142/0143/0147/0151 smoke chain.

## Reuse-first rule

Before adding new runtime, handler, adapter, or worker surfaces, inspect existing code and prefer extension of the current surfaces above. New surfaces are allowed only when an explicit gap is documented.

## Current non-goals

- No separate SQL worker or SQL orchestrator.
- No new vector adapter parallel to the existing Qdrant projection adapter.
- No new OpenVINO embedding adapter parallel to the existing embedding membrane.
- No direct Qdrant or OpenVINO backend imports from Scheduler, RouteProxy, or context contracts.
- No deletion of historical phase docs during current-state refresh.
