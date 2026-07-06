# 0134 — Existing OpenVINO/E5 embedding path

0134 extends the existing OpenVINO/E5 embedding path by tests and integration documentation.

It deliberately does **not** create a new adapter. The audit shows the OpenVINO/E5 stack already exists, including:

```text
src/inference/openvino_embedding_adapter.py
src/inference/openvino_runtime.py
src/inference/openvino_backend.py
src/inference/e5_pipeline.py
src/inference/embedding_pipeline.py
src/inference/registry.py
src/inference/handlers.py
```

## Locked decision

Do not create a parallel E5OpenVINOEmbeddingAdapter.

`src/inference/openvino_embedding_adapter.py` is the existing embedding membrane. It already has:

```text
OpenVINOEmbeddingRuntimeTarget
OpenVINOEmbeddingPolicy
OpenVINOEmbeddingText
OpenVINOEmbeddingVector
OpenVINOEmbeddingBatch
OpenVINOEmbeddingAdapter
build_embedding_vector
build_embedding_texts_from_hydrated_bundle
local_multilingual_e5_openvino_target
```

`src/inference/openvino_runtime.py` is the only real OpenVINO import boundary. Scheduler remains outside OpenVINO. Qdrant remains outside OpenVINO.

## E5 roles

```text
query: text is for retrieval
passage: text is for corpus, contracts, outputs, and synthesis candidates
```

This is enough for the next vector indexing path:

```text
VectorIndexableItem
-> OpenVINOEmbeddingText(role=query|passage)
-> OpenVINOEmbeddingAdapter / existing E5 pipeline
-> OpenVINOEmbeddingVector
-> Qdrant projection adapter later
```

## Code rule review

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: 0134 locks the anti-duplication rule for OpenVINO/E5 adapters. New OpenVINO/E5 capabilities must reuse/extend existing src/inference surfaces unless a documented gap proves otherwise.
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

src/inference/openvino_embedding_adapter.py is the existing embedding membrane
src/inference/openvino_runtime.py is the only real OpenVINO import boundary
