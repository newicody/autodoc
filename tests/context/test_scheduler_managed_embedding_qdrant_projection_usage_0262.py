from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (
    DemoQdrantProjectionExecutor,
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    run_scheduler_managed_embedding_qdrant_projection_usage,
)


EMBEDDING_REPORT = {
    "embedding": {
        "embedding_ref": "embedding:passage:test",
        "source_ref": "ctx-fragment:sql:inference_context:test",
        "sql_ref": "sql:inference_context:test",
        "backend_ref": "openvino:model:multilingual-e5-small",
        "role": "passage",
        "dimension": 3,
        "normalized": True,
        "l2_norm": 1.0,
        "metadata": {
            "context_ref": "sql:inference_context:test",
            "device": "CPU",
            "model_path": "/tmp/model",
        },
        "vector": [1.0, 0.0, 0.0],
    }
}


def test_projection_dry_run_builds_qdrant_batch_with_sql_ref_payload_alias() -> None:
    result = run_scheduler_managed_embedding_qdrant_projection_usage(
        EMBEDDING_REPORT,
        SchedulerManagedEmbeddingQdrantProjectionRequest(vector_dimension=3),
    )
    payload = result.to_mapping()

    assert payload["valid"] is True
    assert payload["dry_run"] is True
    assert payload["sql_ref"] == "sql:inference_context:test"
    assert payload["batch"]["point_count"] == 1
    point = payload["batch"]["points"][0]
    assert point["sql_context_ref"] == "sql:inference_context:test"
    assert point["payload"]["sql_ref"] == "sql:inference_context:test"


def test_projection_execute_requires_policy_decision_id() -> None:
    result = run_scheduler_managed_embedding_qdrant_projection_usage(
        EMBEDDING_REPORT,
        SchedulerManagedEmbeddingQdrantProjectionRequest(vector_dimension=3),
        execute=True,
        executor=DemoQdrantProjectionExecutor(),
    )

    assert result.valid is False
    assert "execute requires policy_decision_id" in result.issues


def test_projection_execute_uses_injected_executor() -> None:
    result = run_scheduler_managed_embedding_qdrant_projection_usage(
        EMBEDDING_REPORT,
        SchedulerManagedEmbeddingQdrantProjectionRequest(
            policy_decision_id="policy:0262:test",
            vector_dimension=3,
        ),
        execute=True,
        executor=DemoQdrantProjectionExecutor(),
    )
    payload = result.to_mapping()

    assert payload["valid"] is True
    assert payload["execute"] is True
    assert payload["write_result"]["acknowledged"] is True
    assert payload["write_result"]["point_count"] == 1
