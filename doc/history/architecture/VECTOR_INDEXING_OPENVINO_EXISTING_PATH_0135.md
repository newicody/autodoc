# 0135 — Vector indexing jobs through the existing OpenVINO/E5 path

0135 connects VectorIndexingJobPlan to the existing OpenVINO/E5 embedding membrane by tests only.

The goal is to prove that the vector-indexing plan created in 0128 can already feed the OpenVINO/E5 embedding contracts introduced earlier without inventing another adapter.

## Decision

Do not create a new vector OpenVINO adapter.

Reuse these existing surfaces:

```text
context.vector_indexing_job_plan.VectorEmbeddingJob
context.vector_indexing_job_plan.VectorIndexableItem
inference.openvino_embedding_adapter.OpenVINOEmbeddingText
inference.openvino_embedding_adapter.build_embedding_vector
inference.openvino_embedding_adapter.OpenVINOEmbeddingRuntimeTarget
inference.openvino_embedding_adapter.OpenVINOEmbeddingPolicy
```

## Contract alignment

VectorEmbeddingJob.item.text_for_embedding is already E5-prefixed.

OpenVINOEmbeddingText is the existing text contract.

build_embedding_vector is the existing vector validation contract.

Scheduler remains the orchestrator and does not import OpenVINO. The Scheduler queues the vector indexing job and remains outside the OpenVINO runtime boundary.  The OpenVINO/E5 adapter executes later behind the existing membrane.

Qdrant projection remains a later adapter step.  SQLContextStore remains durable context authority.

## Flow

```text
VectorIndexingJobPlan
-> VectorEmbeddingJob.item.text_for_embedding
-> OpenVINOEmbeddingText
-> existing OpenVINO/E5 execution membrane
-> build_embedding_vector
-> VectorProjectionJob later
```

## Non-goals

```text
no new VectorOpenVINOEmbeddingAdapter
no Scheduler OpenVINO import
no Qdrant projection in this patch
no RouteProxy runtime mutation
no new worker daemon
```

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
live_path_status: transition
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
