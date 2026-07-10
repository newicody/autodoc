"""Adapter for existing DbApiSqlContextStore.upsert_record contracts.

0260 discovered the real ``context.sql_context_store.DbApiSqlContextStore``.
That existing store can expose ``upsert_record(record)`` and expects a
record-like object with ``context_ref`` instead of a raw payload dict.

This module does not create a SQL store and does not start PostgreSQL.  It wraps
an existing store object so the 0259 Scheduler-managed usage path can keep using
``controlled_write(payload)`` while the real store contract remains intact.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import inspect
from typing import Any, Mapping
import uuid


def _sql_typed_context_ref(value: object) -> str:
    """Return a SQL-typed context_ref required by DbApiSqlContextStore."""

    text = str(value or uuid.uuid4().hex)
    if text.startswith("sql:"):
        return text
    return "sql:" + text


def _record_values_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    metadata = dict(payload.get("metadata", {}))
    context_ref = _sql_typed_context_ref(
        metadata.get("context_ref")
        or payload.get("context_ref")
        or payload.get("intent_id")
        or uuid.uuid4().hex
    )
    text = str(payload.get("text", ""))
    text_kind = str(payload.get("text_kind", "passage"))
    return {
        "context_ref": context_ref,
        "record_ref": context_ref,
        "record_id": context_ref,
        "id": context_ref,
        "content": text,
        "text": text,
        "body": text,
        "text_kind": text_kind,
        "kind": text_kind,
        "source_ref": str(payload.get("source_ref", "")),
        "metadata": metadata,
        "payload": dict(payload),
    }


def _public_record_mapping(record: object) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if is_dataclass(record) and not isinstance(record, type):
        return dict(asdict(record))
    public: dict[str, Any] = {}
    for name in (
        "context_ref",
        "record_ref",
        "record_id",
        "id",
        "content",
        "text",
        "text_kind",
        "source_ref",
        "kind",
        "title",
        "body",
        "parent_ref",
        "metadata",
    ):
        if hasattr(record, name):
            value = getattr(record, name)
            if isinstance(value, Mapping):
                value = dict(value)
            public[name] = value
    return public


def _result_to_mapping(result: object, fallback_record: object | None = None) -> dict[str, Any]:
    if isinstance(result, Mapping):
        payload = dict(result)
    else:
        record = _public_record_mapping(result)
        payload = {"record": record} if record else {"result": result}

    sql_ref = (
        payload.get("sql_ref")
        or payload.get("record_ref")
        or payload.get("record_id")
        or payload.get("context_ref")
        or payload.get("id")
        or ""
    )
    record_payload = payload.get("record")
    if not sql_ref and isinstance(record_payload, Mapping):
        sql_ref = (
            record_payload.get("sql_ref")
            or record_payload.get("record_ref")
            or record_payload.get("record_id")
            or record_payload.get("context_ref")
            or record_payload.get("id")
            or ""
        )

    if not sql_ref and fallback_record is not None:
        fallback = _public_record_mapping(fallback_record)
        sql_ref = (
            fallback.get("sql_ref")
            or fallback.get("record_ref")
            or fallback.get("record_id")
            or fallback.get("context_ref")
            or fallback.get("id")
            or ""
        )
        if "record" not in payload and fallback:
            payload["record"] = fallback

    if sql_ref:
        payload["sql_ref"] = str(sql_ref)
    return payload


def _sql_record_kind(values: Mapping[str, Any]) -> str:
    """Map Scheduler text kinds to existing SqlContextRecord allowed kinds."""

    metadata = values.get("metadata")
    preferred = ""
    if isinstance(metadata, Mapping):
        preferred = str(metadata.get("sql_kind") or metadata.get("kind") or "")
    preferred = preferred or str(values.get("kind") or values.get("text_kind") or "")
    if preferred in {
        "source",
        "document",
        "chunk",
        "fact",
        "artifact",
        "objective",
        "axis",
        "trajectory",
        "inference_context",
        "specialist_output",
        "feedback",
        "github_artifact",
    }:
        return preferred
    return "inference_context"


def _sql_record_identity(values: Mapping[str, Any]) -> str:
    """Return a stable identity accepted by build_sql_context_record."""

    for key in ("context_ref", "record_ref", "record_id", "id"):
        value = values.get(key)
        if value:
            return str(value).removeprefix("sql:")
    return uuid.uuid4().hex


def _sql_record_title(values: Mapping[str, Any]) -> str:
    """Return a non-empty title for the existing SqlContextRecord."""

    metadata = values.get("metadata")
    if isinstance(metadata, Mapping):
        title = str(metadata.get("title") or "")
        if title.strip():
            return title
    source_ref = str(values.get("source_ref") or "")
    if source_ref.strip():
        return source_ref
    return str(values.get("context_ref") or "Scheduler-managed SQL context write")


def _sql_record_metadata_tuple(values: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """Return metadata in the tuple form expected by SqlContextRecord."""

    metadata = values.get("metadata")
    if not isinstance(metadata, Mapping):
        return ()
    normalized: list[tuple[str, str]] = []
    for key, value in sorted(metadata.items()):
        text_key = str(key)
        text_value = str(value)
        if text_key and text_value:
            normalized.append((text_key, text_value))
    return tuple(normalized)


def _build_existing_sql_context_record_with_module(store_module: object, values: Mapping[str, Any]) -> object | None:
    """Use the existing build_sql_context_record helper when available."""

    builder = getattr(store_module, "build_sql_context_record", None)
    if not callable(builder):
        return None
    return builder(
        kind=_sql_record_kind(values),
        identity=_sql_record_identity(values),
        title=_sql_record_title(values),
        body=str(values.get("body") or values.get("content") or values.get("text") or ""),
        parent_ref=values.get("parent_ref"),
        metadata=_sql_record_metadata_tuple(values),
    )


def _construct_existing_record_class(record_class: type[Any], values: Mapping[str, Any]) -> object:
    signature = inspect.signature(record_class)
    kwargs: dict[str, Any] = {}
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.kind in (parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL):
            continue
        if name in values:
            kwargs[name] = values[name]
        elif parameter.default is inspect.Signature.empty:
            if "ref" in name or name.endswith("_id"):
                kwargs[name] = values["context_ref"]
            elif "content" in name or name in {"text", "body"}:
                kwargs[name] = values["content"]
            elif "kind" in name:
                kwargs[name] = values["text_kind"]
            elif "metadata" in name:
                kwargs[name] = values["metadata"]
    return record_class(**kwargs)


def _build_record_for_existing_store(store: object, payload: Mapping[str, Any]) -> object:
    values = _record_values_from_payload(payload)
    store_module = inspect.getmodule(store.__class__)
    if store_module is not None:
        record = _build_existing_sql_context_record_with_module(store_module, values)
        if record is not None:
            return record
    for name in (
        "SqlContextRecord",
        "ContextRecord",
        "DbApiSqlContextRecord",
        "SQLContextRecord",
    ):
        record_class = getattr(store_module, name, None) if store_module is not None else None
        if inspect.isclass(record_class):
            try:
                return _construct_existing_record_class(record_class, values)
            except TypeError:
                continue
    raise TypeError("existing SQLContextStore record builder was not found")


def _call_existing_schema_bootstrap(store: object) -> bool:
    """Call an existing schema bootstrap hook when the store exposes one."""

    for name in (
        "ensure_schema",
        "initialize_schema",
        "init_schema",
        "create_schema",
        "setup_schema",
        "bootstrap_schema",
        "migrate",
    ):
        hook = getattr(store, name, None)
        if callable(hook):
            hook()
            return True
    return False


class SchedulerManagedDbApiSqlContextStoreRecordAdapter:
    """Expose ``controlled_write(payload)`` over an existing SQL store object."""

    def __init__(self, store: object) -> None:
        self.store = store
        self.schema_bootstrap_called = _call_existing_schema_bootstrap(store)

    def controlled_write(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        controlled_write = getattr(self.store, "controlled_write", None)
        if callable(controlled_write):
            return _result_to_mapping(controlled_write(payload))

        upsert_record = getattr(self.store, "upsert_record", None)
        if not callable(upsert_record):
            raise TypeError("existing SQLContextStore object must expose controlled_write or upsert_record")

        record = _build_record_for_existing_store(self.store, payload)
        return _result_to_mapping(upsert_record(record), fallback_record=record)


def adapt_db_api_sql_context_store_for_scheduler_usage_0260(store: object | None) -> object | None:
    """Wrap a real DbApiSqlContextStore for the 0259 controlled_write path."""

    if store is None:
        return None
    return SchedulerManagedDbApiSqlContextStoreRecordAdapter(store)
