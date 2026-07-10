from dataclasses import dataclass

from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    build_openvino_passage_text_from_sql_record,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
)


@dataclass(frozen=True)
class Record:
    context_ref: str = "sql:inference_context:test"
    kind: str = "inference_context"
    title: str = "Test title"
    body: str = "Test body"
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = (("k", "v"),)


class Store:
    def get_record(self, context_ref: str):
        if context_ref == "sql:inference_context:test":
            return Record()
        return None


def fake_embedder(text: str, sql_ref: str, model_dir: str | None, device: str):
    return {
        "embedding_ref": "embedding:passage:test",
        "source_ref": "ctx-fragment:" + sql_ref,
        "sql_ref": sql_ref,
        "role": "passage",
        "dimension": 3,
        "normalized": True,
        "l2_norm": 1.0,
        "vector": [1.0, 0.0, 0.0],
        "metadata": {"device": device, "model_path": model_dir or ""},
    }


def test_builds_explicit_passage_text_from_sql_record() -> None:
    text = build_openvino_passage_text_from_sql_record(
        {"context_ref": "sql:x", "title": "Title", "body": "Body"}
    )
    assert text == "passage: Title\nBody"


def test_sql_ref_embedding_dry_run_rehydrates_record() -> None:
    result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        Store(),
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest(sql_ref="sql:inference_context:test"),
    )
    payload = result.to_mapping()
    assert payload["valid"] is True
    assert payload["dry_run"] is True
    assert payload["record"]["context_ref"] == "sql:inference_context:test"
    assert payload["embedding_text"] == "passage: Test title\nTest body"
    assert payload["calls_qdrant"] is False
    assert payload["starts_openvino"] is False


def test_sql_ref_embedding_execute_uses_injected_embedder() -> None:
    result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        Store(),
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
            sql_ref="sql:inference_context:test",
            policy_decision_id="policy:0261:test",
        ),
        execute=True,
        embedder=fake_embedder,
    )
    payload = result.to_mapping()
    assert payload["valid"] is True
    assert payload["execute"] is True
    assert payload["embedding"]["source_ref"] == "ctx-fragment:sql:inference_context:test"
    assert payload["embedding"]["dimension"] == 3


def test_sql_ref_embedding_execute_requires_policy_decision_id() -> None:
    result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        Store(),
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest(sql_ref="sql:inference_context:test"),
        execute=True,
        embedder=fake_embedder,
    )
    assert result.valid is False
    assert "execute requires policy_decision_id" in result.issues
