"""Controlled SQLContextStore write contract for persistence records.

0151 is the first real persistence step after the 0148/0149 handoff chain. It
converts the prepared persistence record into the existing SqlContextRecord
shape and is intentionally limited to the existing DbApiSqlContextStore boundary.
It does not create a SQL worker, does not call OpenVINO or Qdrant, and does not
turn Qdrant projection identifiers into durable truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, Mapping

from .sql_context_store import SqlContextRecord, SqlContextStoreWriteResult

_SCHEMA = "missipy.sql_context_store.controlled_write.v1"
_WRITE_MODE = "dbapi_sql_context_store_upsert_record"
_DURABLE_AUTHORITY = "sql"
_QDRANT_ROLE = "projection_recall_index"
_SELECTED_STORE_CLASS = "DbApiSqlContextStore"
_SELECTED_WRITE_METHOD = "upsert_record"


def _require_non_empty(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_prefix(value: Any, *, field_name: str, prefix: str) -> str:
    normalized = _require_non_empty(value, field_name=field_name)
    if not normalized.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix!r}: {normalized!r}")
    return normalized


def _normalize_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"{field_name} must be boolean-compatible")


def _metadata_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _metadata_items(mapping: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    keys = (
        "persistence_ref",
        "handoff_ref",
        "artifact_ref",
        "artifact_kind",
        "artifact_path",
        "artifact_contract_path",
        "artifact_report",
        "artifact_json",
        "result_frame_path",
        "point_id",
        "qdrant_rest_id",
        "vector_json",
        "collection",
        "dimension",
        "status",
        "machine_vector_handoff",
        "strict_vector_handoff",
        "durable_authority",
        "qdrant_role",
        "persistence_mode",
    )
    return tuple((key, _metadata_value(mapping.get(key))) for key in keys if key in mapping)


def _record_body(mapping: Mapping[str, Any]) -> str:
    payload = {
        "schema": _SCHEMA,
        "durable_authority": _DURABLE_AUTHORITY,
        "qdrant_role": _QDRANT_ROLE,
        "write_mode": _WRITE_MODE,
        "selected_store_class": _SELECTED_STORE_CLASS,
        "selected_write_method": _SELECTED_WRITE_METHOD,
        "sql_ref": mapping.get("sql_ref"),
        "artifact_ref": mapping.get("artifact_ref"),
        "artifact_kind": mapping.get("artifact_kind"),
        "artifact_path": mapping.get("artifact_path"),
        "artifact_contract_path": mapping.get("artifact_contract_path"),
        "artifact_report": mapping.get("artifact_report"),
        "artifact_json": mapping.get("artifact_json"),
        "result_frame_path": mapping.get("result_frame_path"),
        "point_id": mapping.get("point_id"),
        "qdrant_rest_id": mapping.get("qdrant_rest_id"),
        "vector_json": mapping.get("vector_json"),
        "collection": mapping.get("collection"),
        "dimension": mapping.get("dimension"),
        "status": mapping.get("status"),
        "machine_vector_handoff": mapping.get("machine_vector_handoff"),
        "strict_vector_handoff": mapping.get("strict_vector_handoff"),
        "source_persistence_ref": mapping.get("persistence_ref"),
        "source_handoff_ref": mapping.get("handoff_ref"),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_sql_context_record_from_persistence_mapping(mapping: Mapping[str, Any]) -> SqlContextRecord:
    """Convert a 0149 persistence mapping into the existing SQL record type."""

    sql_ref = _require_prefix(mapping.get("sql_ref"), field_name="sql_ref", prefix="sql:")
    artifact_ref = _require_prefix(mapping.get("artifact_ref"), field_name="artifact_ref", prefix="artifact:")
    _require_prefix(mapping.get("point_id"), field_name="point_id", prefix="qdrant-point:")
    _require_non_empty(mapping.get("qdrant_rest_id"), field_name="qdrant_rest_id")
    _normalize_bool(mapping.get("machine_vector_handoff"), field_name="machine_vector_handoff")
    _normalize_bool(mapping.get("strict_vector_handoff"), field_name="strict_vector_handoff")

    return SqlContextRecord(
        context_ref=sql_ref,
        kind="artifact",
        title=f"Artifact vector indexing result for {artifact_ref}",
        body=_record_body(mapping),
        parent_ref=artifact_ref,
        metadata=_metadata_items(mapping),
    )


@dataclass(frozen=True, slots=True)
class SqlContextStoreControlledWriteSummary:
    """Serializable summary for a controlled DbApiSqlContextStore write."""

    persistence_ref: str
    sql_ref: str
    artifact_ref: str
    db_path: str
    selected_store_class: str = _SELECTED_STORE_CLASS
    selected_write_method: str = _SELECTED_WRITE_METHOD
    write_mode: str = _WRITE_MODE
    durable_authority: str = _DURABLE_AUTHORITY
    qdrant_role: str = _QDRANT_ROLE
    write_status: str = "persisted"
    inserted: bool = False
    replaced: bool = False
    readback_ok: bool = False
    point_id: str = ""
    qdrant_rest_id: str = ""
    vector_json: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_prefix(self.persistence_ref, field_name="persistence_ref", prefix="sql-context-persist:")
        _require_prefix(self.sql_ref, field_name="sql_ref", prefix="sql:")
        _require_prefix(self.artifact_ref, field_name="artifact_ref", prefix="artifact:")
        _require_non_empty(self.db_path, field_name="db_path")
        if self.selected_store_class != _SELECTED_STORE_CLASS:
            raise ValueError("0151 must use DbApiSqlContextStore")
        if self.selected_write_method != _SELECTED_WRITE_METHOD:
            raise ValueError("0151 must use upsert_record")
        if self.durable_authority != _DURABLE_AUTHORITY:
            raise ValueError("durable_authority must remain sql")
        if self.qdrant_role != _QDRANT_ROLE:
            raise ValueError("qdrant_role must remain projection_recall_index")
        if self.write_mode != _WRITE_MODE:
            raise ValueError("invalid 0151 write_mode")

    @classmethod
    def from_write_result(
        cls,
        *,
        persistence_mapping: Mapping[str, Any],
        write_result: SqlContextStoreWriteResult,
        db_path: str,
        readback_ok: bool,
    ) -> "SqlContextStoreControlledWriteSummary":
        return cls(
            persistence_ref=_require_prefix(
                persistence_mapping.get("persistence_ref"),
                field_name="persistence_ref",
                prefix="sql-context-persist:",
            ),
            sql_ref=write_result.record.context_ref,
            artifact_ref=_require_prefix(
                persistence_mapping.get("artifact_ref"),
                field_name="artifact_ref",
                prefix="artifact:",
            ),
            db_path=db_path,
            inserted=write_result.inserted,
            replaced=write_result.replaced,
            readback_ok=readback_ok,
            point_id=str(persistence_mapping.get("point_id", "")),
            qdrant_rest_id=str(persistence_mapping.get("qdrant_rest_id", "")),
            vector_json=str(persistence_mapping.get("vector_json", "")),
            metadata={
                "source_handoff_ref": persistence_mapping.get("handoff_ref"),
                "source_persistence_mode": persistence_mapping.get("persistence_mode"),
                "machine_vector_handoff": persistence_mapping.get("machine_vector_handoff"),
                "strict_vector_handoff": persistence_mapping.get("strict_vector_handoff"),
                "collection": persistence_mapping.get("collection"),
                "dimension": persistence_mapping.get("dimension"),
            },
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA,
            "persistence_ref": self.persistence_ref,
            "sql_ref": self.sql_ref,
            "artifact_ref": self.artifact_ref,
            "db_path": self.db_path,
            "selected_store_class": self.selected_store_class,
            "selected_write_method": self.selected_write_method,
            "write_mode": self.write_mode,
            "durable_authority": self.durable_authority,
            "qdrant_role": self.qdrant_role,
            "write_status": self.write_status,
            "inserted": self.inserted,
            "replaced": self.replaced,
            "readback_ok": self.readback_ok,
            "point_id": self.point_id,
            "qdrant_rest_id": self.qdrant_rest_id,
            "vector_json": self.vector_json,
            "metadata": dict(self.metadata),
        }
