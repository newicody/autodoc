# 0138 — OpenVINO/E5 live smoke through existing path

0138 runs the first OpenVINO/E5 live smoke through existing surfaces only.

It does not add a new embedding adapter, scheduler runner, daemon, Qdrant client, or RouteProxy worker.  The smoke path is an operator command that plans by default and executes only when explicitly requested.

tools/embed_e5.py is the existing operator CLI.
src/inference/openvino_embedding_adapter.py is the existing embedding membrane.
src/inference/openvino_runtime.py is the only real OpenVINO import boundary.

## Command

dry-run is the default:

Dry-run is the default:

```bash
python tools/run_openvino_e5_live_smoke.py . --format markdown
```

Backend execution requires an explicit flag:

```bash
python tools/run_openvino_e5_live_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --execute
```

--execute is required for backend execution.

## Boundary lock

- Scheduler remains outside OpenVINO.
- Qdrant remains outside OpenVINO.
- RouteProxy remains outside OpenVINO.
- SQLContextStore remains durable context authority.
- The smoke command reuses `tools/embed_e5.py` instead of importing OpenVINO directly.
- Do not create SchedulerOpenVINORunner.
- Do not create VectorOpenVINOEmbeddingAdapter.

## Expected smoke

The command runs two texts through the existing E5 path:

```text
query: route proxy scheduler vector indexing smoke
passage: Scheduler queues vector indexing work while OpenVINO stays behind the existing inference membrane.
```

The next phase can consume this as proof that OpenVINO/E5 is alive before Qdrant projection is tested.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: add live smoke rule that executes E5/OpenVINO only through existing tools/embed_e5.py and existing inference membranes.
live_path_status: smoke-ready
live_path_uses_real_backend: optional-via---execute
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
