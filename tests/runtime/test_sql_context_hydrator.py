from __future__ import annotations

from context.sql_context_hydrator import (
    SQLContextHydrator,
    SqlContextHydrationPolicy,
    build_sql_context_hydration_request,
    fragment_from_sql_record,
)
from context.sql_context_store import SQLiteSqlContextStore, SqlContextRecord


def _store_with_context() -> SQLiteSqlContextStore:
    store = SQLiteSqlContextStore()
    store.initialize_schema()
    store.upsert_record(
        SqlContextRecord(
            context_ref="sql:document:root",
            kind="document",
            title="Root artifact",
            body="Root body from SQL authority.",
            parent_ref="github:artifact:root",
            metadata=(("origin", "github"),),
        )
    )
    store.upsert_record(
        SqlContextRecord(
            context_ref="sql:chunk:001",
            kind="chunk",
            title="Chunk A",
            body="Hydrated chunk A.",
            parent_ref="sql:document:root",
        )
    )
    store.upsert_record(
        SqlContextRecord(
            context_ref="sql:fact:001",
            kind="fact",
            title="Fact A",
            body="Hydrated fact A.",
            parent_ref="sql:document:root",
        )
    )
    return store


def test_sql_context_hydrator_hydrates_requested_record() -> None:
    store = _store_with_context()
    hydrator = SQLContextHydrator(store)

    bundle = hydrator.hydrate(build_sql_context_hydration_request("sql:document:root"))

    assert bundle.fragment_count == 1
    assert bundle.context_refs == ("sql:document:root",)
    assert bundle.fragments[0].relation == "requested"
    assert bundle.fragments[0].projection_ref == "ctx-fragment:sql:document:root"
    assert bundle.to_mapping()["missing_context_refs"] == []


def test_sql_context_hydrator_can_include_children_by_kind() -> None:
    store = _store_with_context()
    hydrator = SQLContextHydrator(store)

    bundle = hydrator.hydrate(
        build_sql_context_hydration_request(
            "sql:document:root",
            include_children=True,
            child_kinds=("chunk",),
        )
    )

    assert bundle.context_refs == ("sql:document:root", "sql:chunk:001")
    assert [fragment.relation for fragment in bundle.fragments] == ["requested", "child"]


def test_sql_context_hydrator_records_missing_refs_and_deduplicates_requests() -> None:
    store = _store_with_context()
    hydrator = SQLContextHydrator(store)

    bundle = hydrator.hydrate(
        build_sql_context_hydration_request(
            "sql:document:root",
            "sql:document:root",
            "sql:document:missing",
        )
    )

    assert bundle.context_refs == ("sql:document:root",)
    assert bundle.missing_context_refs == ("sql:document:missing",)


def test_sql_context_hydrator_policy_bounds_records_and_body_size() -> None:
    store = _store_with_context()
    hydrator = SQLContextHydrator(
        store,
        SqlContextHydrationPolicy(max_records=1, max_body_chars=4, max_children_per_parent=4),
    )

    bundle = hydrator.hydrate(
        build_sql_context_hydration_request("sql:document:root", include_children=True)
    )

    assert bundle.capped is True
    assert bundle.fragment_count == 1
    assert bundle.fragments[0].body == "Root"
    assert bundle.fragments[0].truncated is True


def test_fragment_from_sql_record_is_mapping_serializable() -> None:
    record = SqlContextRecord(
        context_ref="sql:fact:serializable",
        kind="fact",
        title="Serializable fact",
        body="Body",
        metadata=(("z", "last"), ("a", "first")),
    )

    fragment = fragment_from_sql_record(record)

    assert fragment.to_mapping()["schema"] == "missipy.sql_context_hydrator.fragment.v1"
    assert fragment.metadata == (("a", "first"), ("z", "last"))
