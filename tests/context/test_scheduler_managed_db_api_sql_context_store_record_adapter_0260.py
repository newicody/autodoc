from context.scheduler_managed_db_api_sql_context_store_record_adapter_0260 import (
    adapt_db_api_sql_context_store_for_scheduler_usage_0260,
)


class UpsertOnlyStore:
    def upsert_record(self, record):
        assert record.context_ref.startswith("sql:")
        assert record.content == "payload text"
        return record


class ControlledWriteStore:
    def controlled_write(self, payload):
        return {"sql_ref": "sql:controlled/" + payload["intent_id"]}


def test_record_adapter_builds_record_for_upsert_only_store() -> None:
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(UpsertOnlyStore())
    result = adapter.controlled_write(
        {
            "intent_id": "intent:0260:test",
            "text": "payload text",
            "text_kind": "passage",
            "metadata": {},
        }
    )

    assert result["sql_ref"] == "sql:intent:0260:test"
    assert result["record"]["context_ref"] == "sql:intent:0260:test"


def test_record_adapter_delegates_controlled_write_store() -> None:
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(ControlledWriteStore())
    result = adapter.controlled_write({"intent_id": "intent:0260:test", "text": "payload text"})

    assert result["sql_ref"] == "sql:controlled/intent:0260:test"


def test_record_adapter_keeps_existing_sql_typed_context_ref() -> None:
    adapter = adapt_db_api_sql_context_store_for_scheduler_usage_0260(UpsertOnlyStore())
    result = adapter.controlled_write(
        {
            "intent_id": "intent:ignored",
            "text": "payload text",
            "metadata": {"context_ref": "sql:already-typed"},
        }
    )

    assert result["sql_ref"] == "sql:already-typed"


class SchemaBootstrapStore(UpsertOnlyStore):
    def __init__(self) -> None:
        self.schema_ready = False

    def ensure_schema(self) -> None:
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
    assert result["sql_ref"] == "sql:intent:0260:schema"
