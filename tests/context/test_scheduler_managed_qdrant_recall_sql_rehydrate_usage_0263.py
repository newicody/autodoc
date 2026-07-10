from dataclasses import dataclass

from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (
    DemoQdrantRecallExecutor,
    SchedulerManagedQdrantRecallSqlRehydrateRequest,
    default_query_ref_from_embedding_report,
    run_scheduler_managed_qdrant_recall_sql_rehydrate_usage,
)


EMBEDDING_REPORT = {
    "embedding": {
        "embedding_ref": "embedding:passage:test",
        "dimension": 3,
        "vector": [1.0, 0.0, 0.0],
    }
}


@dataclass(frozen=True)
class Record:
    context_ref: str = "sql:inference_context:test"
    kind: str = "inference_context"
    title: str = "Recall title"
    body: str = "Recall body"
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()


class Store:
    def get_record(self, context_ref: str):
        if context_ref == "sql:inference_context:test":
            return Record()
        return None


def test_default_query_ref_uses_embedding_ref() -> None:
    assert default_query_ref_from_embedding_report(EMBEDDING_REPORT) == "qdrant-query:passage:test"


def test_recall_dry_run_plans_without_executor() -> None:
    result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
        EMBEDDING_REPORT,
        Store(),
        SchedulerManagedQdrantRecallSqlRehydrateRequest(
            query_ref="qdrant-query:test",
            vector_dimension=3,
        ),
    )
    payload = result.to_mapping()

    assert payload["valid"] is True
    assert payload["dry_run"] is True
    assert payload["recall"]["planned"] is True
    assert payload["starts_qdrant"] is False
    assert payload["runs_openvino"] is False


def test_recall_execute_rehydrates_sql_records_from_hits() -> None:
    result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
        EMBEDDING_REPORT,
        Store(),
        SchedulerManagedQdrantRecallSqlRehydrateRequest(
            query_ref="qdrant-query:test",
            policy_decision_id="policy:0263:test",
            vector_dimension=3,
        ),
        execute=True,
        executor=DemoQdrantRecallExecutor(sql_refs=("sql:inference_context:test",)),
    )
    payload = result.to_mapping()

    assert payload["valid"] is True
    assert payload["execute"] is True
    assert payload["sql_refs"] == ["sql:inference_context:test"]
    assert payload["hydrated_count"] == 1
    assert payload["missing_count"] == 0
    assert payload["hydrated_records"][0]["context_ref"] == "sql:inference_context:test"


def test_recall_execute_requires_policy_decision_id() -> None:
    result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
        EMBEDDING_REPORT,
        Store(),
        SchedulerManagedQdrantRecallSqlRehydrateRequest(
            query_ref="qdrant-query:test",
            vector_dimension=3,
        ),
        execute=True,
        executor=DemoQdrantRecallExecutor(sql_refs=("sql:inference_context:test",)),
    )

    assert result.valid is False
    assert "execute requires policy_decision_id" in result.issues
