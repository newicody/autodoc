# 0142 — Machine-readable E5 vector handoff

0142 reuses tools/embed_e5.py --format json --full-vector.
0142 reuses tools/run_qdrant_projection_live_smoke.py --vector-json.

The goal is to close the gap left by 0141: the operator chain worked, but Qdrant still received a deterministic smoke vector.  0142 makes the chain strict by producing a full 384-dimensional E5 vector through the existing E5 CLI JSON mode and passing that file into the existing Qdrant smoke tool.

## Locked path

```text
tools/embed_e5.py --format json --full-vector
-> .var/smoke/e5_vector_0142.json
-> tools/run_qdrant_projection_live_smoke.py --vector-json
-> existing qdrant projection contracts
-> Qdrant upsert/search
-> sql_ref remains the durable hydration pointer
```

## Boundaries

- Do not parse values_preview as a full vector.
- Do not create LocalVectorIndexingOrchestrator.
- Do not create VectorOpenVINOEmbeddingAdapter.
- Do not create VectorQdrantProjectionAdapter.
- Scheduler remains outside OpenVINO and Qdrant.
- RouteProxy remains outside OpenVINO and Qdrant.
- SQLContextStore remains durable authority.
- Qdrant stores projection and recall indexes only.

## Operator usage

```bash
python tools/run_local_vector_indexing_live_smoke.py . \
  --model-dir /home/eric/model/openvino/multilingual-e5-small \
  --qdrant-url http://127.0.0.1:6333 \
  --collection autodoc_smoke_e5_384 \
  --strict-vector-handoff \
  --execute
```

The tool generates `.var/smoke/e5_vector_0142.json` by default during execution and then feeds it to Qdrant through `--vector-json`.

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: add strict machine-vector handoff rule so future vector smoke code does not parse human previews or create parallel adapters.
live_path_status: live smoke
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
