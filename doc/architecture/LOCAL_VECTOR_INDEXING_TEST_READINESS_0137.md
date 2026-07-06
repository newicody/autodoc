# 0137 — Local vector-indexing test readiness

0137 is a readiness gate, not a runtime implementation.

The goal is to prepare the first local vector-indexing smoke test without creating a parallel wheel.  The test must reuse the existing Scheduler route handler, RouteProxy runtime, OpenVINO/E5 embedding membrane, Qdrant projection adapter, vector collection registry, and SQL context store.

## Steps before the first real local test

1. stabilize 0136-r1 before running the first local vector-indexing smoke test.
2. run `tools/plan_local_vector_indexing_smoke.py . --format markdown`.
3. confirm every expected existing surface is present.
4. run OpenVINO/E5 through the existing inference membrane.
5. run Qdrant through the existing projection adapter.
6. run a dry local vector-indexing path from text to embedding result to projection acknowledgement.
7. then wire Scheduler to enqueue the existing VectorIndexingJobPlan.

## Boundary lock

- Scheduler remains the orchestrator.
- SQLContextStore remains durable authority.
- RouteProxyRuntime remains data-plane runtime for local frame exchange.
- OpenVINO imports remain behind the existing OpenVINO runtime boundary.
- Qdrant remains a projection and recall adapter, not authority.
- Do not create VectorOpenVINOEmbeddingAdapter.
- Do not create VectorQdrantProjectionAdapter.
- Do not create a local vector indexing orchestrator.

## Readiness command

```bash
python tools/plan_local_vector_indexing_smoke.py . --format markdown
```

The command is read-only. It returns exit code `0` when expected existing surfaces are present and `2` when at least one surface is missing.

## Phase status

```text
code_rule_review: done
code_rule_update_required: true
code_rule_reason: add a smoke-test readiness rule before adding a local runner so existing wheels are reused first.
live_path_status: readiness
live_path_uses_real_backend: false
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
