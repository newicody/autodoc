# 0141 — Local vector indexing live smoke

0141 composes the already validated existing operator surfaces into one local vector indexing smoke command.

It does not add a Scheduler runner, a RouteProxy worker, an OpenVINO adapter, a Qdrant adapter, or a local vector indexing orchestrator.

## Existing surfaces

- tools/run_openvino_e5_live_smoke.py remains the OpenVINO/E5 execution surface.
- tools/run_qdrant_projection_live_smoke.py remains the Qdrant projection execution surface.
- src/inference/openvino_embedding_adapter.py remains the embedding membrane.
- src/inference/openvino_runtime.py remains the real OpenVINO import boundary.
- src/inference/qdrant_projection_adapter.py remains the Qdrant projection membrane.
- src/context/vector_indexing_job_plan.py remains the vector indexing job contract.
- SQLContextStore remains durable authority.

## Boundary

- Do not create LocalVectorIndexingOrchestrator.
- Do not create VectorOpenVINOEmbeddingAdapter.
- Do not create VectorQdrantProjectionAdapter.
- Scheduler remains outside OpenVINO and Qdrant.
- RouteProxy remains outside OpenVINO and Qdrant.
- SQLContextStore remains durable authority.
- Qdrant stores projection/recall only.

## Strict vector handoff

The existing `tools/embed_e5.py` operator has already proven real OpenVINO/E5 execution.  Its current operator output is human-oriented and includes vector preview and norm metadata.

0141 does not parse human-only previews as full vectors.  strict full-vector handoff requires machine-readable E5 vector output, such as a JSON list or an object with `vector`/`values`.

That keeps the system honest: if the existing OpenVINO path needs a machine-readable vector emission, the next patch must extend the existing embedding CLI/membrane instead of inventing another embedding implementation.

## Operator command

```bash
python tools/run_local_vector_indexing_live_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --execute
```

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
