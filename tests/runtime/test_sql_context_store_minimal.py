from __future__ import annotations

from pathlib import Path

import pytest

from src.context.sql_context_store import (
    PostgresSqlContextStoreTarget,
    SQLiteSqlContextStore,
    SqlContextQuery,
    SqlContextRecord,
    allowed_sql_context_kinds,
    build_sql_context_record,
    build_sql_context_ref,
)


def test_sql_context_store_upserts_and_reads_from_sqlite_memory() -> None:
    store = SQLiteSqlContextStore()
    store.initialize_schema()
    record = build_sql_context_record(
        kind="document",
        identity="github:artifact:fork-001",
        title="Baby fork artifact",
        body="Initial artifact imported from project workflow.",
        parent_ref="github:project:item-001",
        metadata=(("origin", "github"), ("phase", "0116")),
    )

    first = store.upsert_record(record)
    second = store.upsert_record(record)
    fetched = store.get_record(record.context_ref)

    assert first.inserted is True
    assert first.replaced is False
    assert second.inserted is False
    assert second.replaced is True
    assert fetched == record
    assert fetched is not None
    assert fetched.to_mapping()["metadata"] == {"origin": "github", "phase": "0116"}


def test_sql_context_store_lists_by_kind_and_parent_ref() -> None:
    store = SQLiteSqlContextStore()
    store.initialize_schema()
    parent = "sql:document:parent"
    chunk = SqlContextRecord(
        context_ref="sql:chunk:001",
        kind="chunk",
        title="Chunk 1",
        body="Hydratable text chunk.",
        parent_ref=parent,
    )
    fact = SqlContextRecord(
        context_ref="sql:fact:001",
        kind="fact",
        title="Fact 1",
        body="Durable fact.",
        parent_ref=parent,
    )
    store.upsert_record(chunk)
    store.upsert_record(fact)

    chunks = store.list_records(SqlContextQuery(kind="chunk"))
    children = store.list_records(SqlContextQuery(parent_ref=parent))

    assert chunks.context_refs == ("sql:chunk:001",)
    assert children.record_count == 2
    assert children.context_refs == ("sql:chunk:001", "sql:fact:001")
    assert children.to_mapping()["record_count"] == 2


def test_sql_context_store_file_path_persists_records(tmp_path: Path) -> None:
    db_path = tmp_path / "autodoc-context.sqlite"
    record = build_sql_context_record(
        kind="objective",
        identity="plan-0116",
        title="Context objective",
        body="SQL authority should persist objective context.",
    )
    first_store = SQLiteSqlContextStore(db_path)
    first_store.initialize_schema()
    first_store.upsert_record(record)
    first_store.close()

    second_store = SQLiteSqlContextStore(db_path)
    second_store.initialize_schema()

    assert second_store.get_record(record.context_ref) == record


def test_sql_context_refs_are_deterministic_and_typed() -> None:
    one = build_sql_context_ref("artifact", "github:artifact:abc")
    two = build_sql_context_ref("artifact", "github:artifact:abc")
    other = build_sql_context_ref("artifact", "github:artifact:def")

    assert one == two
    assert one.startswith("sql:artifact:")
    assert one != other


def test_sql_context_record_rejects_embedded_or_untyped_refs() -> None:
    with pytest.raises(ValueError, match="context_ref must start with sql:"):
        SqlContextRecord(
            context_ref="ctx:not-authority",
            kind="document",
            title="Bad",
            body="Bad",
        )

    with pytest.raises(ValueError, match="parent_ref must be a typed reference"):
        SqlContextRecord(
            context_ref="sql:document:ok",
            kind="document",
            title="Bad parent",
            body="Bad parent",
            parent_ref="not typed",
        )


def test_postgres_target_documents_local_fast_pool_configuration() -> None:
    target = PostgresSqlContextStoreTarget()

    assert target.data_directory == "/srv/autodoc/postgres/data"
    assert target.active_pool == "fast_pool"
    assert target.backup_pool == "data_pool"
    assert target.to_mapping()["driver_import"] == "external"


def test_allowed_sql_context_kinds_include_context_variation_entities() -> None:
    kinds = allowed_sql_context_kinds()

    assert "objective" in kinds
    assert "axis" in kinds
    assert "trajectory" in kinds
    assert "inference_context" in kinds
    assert "github_artifact" in kinds
