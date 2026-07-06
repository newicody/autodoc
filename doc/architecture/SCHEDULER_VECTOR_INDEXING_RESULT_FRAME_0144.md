# 0144 — Scheduler vector indexing result frame

0144 writes a vector_indexing_result frame through the existing Scheduler route handler.

It extends the already-existing smoke tool instead of creating a new runtime. It reuses tools/run_scheduler_vector_indexing_smoke.py, reuses src/runtime/scheduler_route_handler_minimal.py
- extends src/runtime/scheduler_route_handler_minimal.py to accept vector_indexing_result, and reuses src/runtime/route_proxy_runtime_minimal.py.

## Boundary

- reuses tools/run_scheduler_vector_indexing_smoke.py
- reuses src/runtime/scheduler_route_handler_minimal.py
- reuses src/runtime/route_proxy_runtime_minimal.py
- reuses tools/run_local_vector_indexing_live_smoke.py for strict OpenVINO/Qdrant execution
- writes a vector_embedding_request frame first
- writes a vector_indexing_result frame after successful strict vector indexing
- includes sql_ref, point_id, qdrant_rest_id, vector_json, status, and machine_vector_handoff in the result frame
- OpenVINO and Qdrant stay behind existing operator tools and adapters
- does not create a result daemon or worker
- does not create VectorIndexingResultWorker
- does not create LocalVectorIndexingOrchestrator
- Do not modify Scheduler.run() in 0144

## Flow

```text
Scheduler-shaped command
-> existing scheduler route handler
-> existing RouteProxyRuntime request frame
-> existing local vector indexing smoke tool
-> OpenVINO/E5 full vector JSON
-> Qdrant projection/search
-> existing Scheduler route handler result frame
```

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: adds a result-frame rule so future vector indexing smoke work reuses the existing route handler/runtime instead of adding workers.
live_path_status: transition
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
