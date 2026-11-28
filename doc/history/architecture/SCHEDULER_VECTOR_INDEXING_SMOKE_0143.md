# 0143 — Scheduler vector indexing smoke

0143 writes a vector indexing request frame through the existing Scheduler route handler, then hands execution to the already validated strict local vector indexing smoke tool.

## Locked path

```text
Scheduler-shaped command
-> src/runtime/scheduler_route_handler_minimal.py
-> src/runtime/route_proxy_runtime_minimal.py
-> vector_embedding_request frame under route root
-> tools/run_local_vector_indexing_live_smoke.py
-> tools/embed_e5.py --format json --full-vector
-> tools/run_qdrant_projection_live_smoke.py --vector-json
-> Qdrant projection/recall
-> sql_ref remains durable hydration pointer
```

## Reuse decisions

- reuses src/runtime/scheduler_route_handler_minimal.py.
- reuses src/runtime/route_proxy_runtime_minimal.py.
- reuses tools/run_local_vector_indexing_live_smoke.py.
- reuses existing OpenVINO/E5 and Qdrant operator tools through the local vector smoke tool.
- OpenVINO and Qdrant stay outside Scheduler and RouteProxy.

## Forbidden wheels

- Do not create SchedulerOpenVINORunner.
- Do not create LocalVectorIndexingOrchestrator.
- Do not create VectorOpenVINOEmbeddingAdapter.
- Do not create VectorQdrantProjectionAdapter.
- Do not modify Scheduler.run() in 0143.

## Operator usage

```bash
python tools/run_scheduler_vector_indexing_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --execute
```

Expected final status:

```text
scheduler_route_frame: ok
local_vector_indexing_smoke: ok
strict_vector_handoff: true
```

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: scheduler vector indexing smoke must reuse existing Scheduler route handler and local vector smoke tool, not add a parallel OpenVINO/Qdrant runner.
live_path_status: live smoke
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
