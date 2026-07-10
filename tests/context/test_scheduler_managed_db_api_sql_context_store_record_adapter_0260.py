from dataclasses import dataclass, field

from context.scheduler_managed_db_api_sql_context_store_record_adapter_0260 import (
    adapt_db_api_sql_context_store_for_scheduler_usage_0260,
)


@dataclass(frozen=True)
class SqlContextRecord:
    context_ref: str
    kind: str
    title: str
    body: str
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def build_sql_context_record(*, kind, identity, title, body, parent_ref=None, metadata=()):
    return SqlContextRecord(
        context_ref="sql:" + kind + ":" + identity,
        kind=kind,
        title=title,
        body=body,
        parent_ref=parent_ref,
        metadata=tuple(metadata),
    )


class UpsertOnlyStore:
    def upsert_record(self, record):
        assert record.context_ref.startswith("sql:")
        assert record.title
        assert record.body == "payload text"
        return record


class ControlledWriteStore:
    def controlled_write(self, payload):
        return {"sql_ref": "sql:controlled/" + payload["intent_id"]}


def test_record_adapter_builds_existing_sql_context_record() -> None:
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(UpsertOnlyStore())
    result = adapter.controlled_write(
        {
            "intent_id": "intent:0260:test",
            "text": "payload text",
            "text_kind": "passage",
            "metadata": {"title": "Custom title"},
        }
    )

    assert result["sql_ref"].startswith("sql:inference_context:")
    assert result["record"]["kind"] == "inference_context"
    assert result["record"]["title"] == "Custom title"
    assert result["record"]["body"] == "payload text"


def test_record_adapter_delegates_controlled_write_store() -> None:
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(ControlledWriteStore())
    result = adapter.controlled_write({"intent_id": "intent:0260:test", "text": "payload text"})

    assert result["sql_ref"] == "sql:controlled/intent:0260:test"


class SchemaBootstrapStore(UpsertOnlyStore):
    def __init__(self) -> None:
        self.schema_ready = False

    def initialize_schema(self) -> None:
        self.schema_ready = True

    def upsert_record(self, record):
        assert self.schema_ready is True
        return super().upsert_record(record)


def test_record_adapter_calls_existing_schema_bootstrap_hook() -> None:
    store = SchemaBootstrapStore()
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(store)

    assert adapter.schema_bootstrap_called is True
    result = adapter.controlled_write(
        {
            "intent_id": "intent:0260:schema",
            "text": "payload text",
            "metadata": {},
        }
    )
    assert result["sql_ref"].startswith("sql:inference_context:")
