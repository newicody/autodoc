"""Pure SQLContextStore persistence record for SQL handoff outputs.

0149 consumes the 0148 SQL persistence handoff and prepares a durable context
record for the existing SQLContextStore authority boundary.  It does not create
SQL workers, does not import backend-specific database clients, and does not
turn Qdrant into durable truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import json

_DURABLE_AUTHORITY = "sql"
_QDRANT_ROLE = "projection_recall_index"
_PERSISTENCE_MODE = "sql_context_store_record"

_CANDIDATE_WRITE_METHODS = (
    "persist_context",
    "upsert_context",
    "save_context",
    "write_context",
    "store_context",
    "put_context",
    "record_context",
    "create_context",
)


def _require_non_empty(value: str, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_prefix(value: str, *, field_name: str, prefix: str) -> str:
    value = _require_non_empty(value, field_name=field_name)
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix!r}: {value!r}")
    return value


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


def _normalize_dimension(value: Any) -> int:
    try:
        dimension = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("dimension must be an integer") from exc
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    return dimension


@dataclass(frozen=True, slots=True)
class SqlContextStoreSurface:
    """Source-level description of the existing SQLContextStore surface."""

    path: str
    exists: bool
    has_sql_context_store: bool
    candidate_write_methods: tuple[str, ...]
    selected_write_method: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "exists": self.exists,
            "has_sql_context_store": self.has_sql_context_store,
            "candidate_write_methods": list(self.candidate_write_methods),
            "selected_write_method": self.selected_write_method,
            "ready_for_direct_sql_context_store_write": self.selected_write_method is not None,
        }


@dataclass(frozen=True, slots=True)
class SqlContextStorePersistenceRecord:
    """Serializable record prepared for SQLContextStore persistence."""

    persistence_ref: str
    handoff_ref: str
    sql_ref: str
    artifact_ref: str
    artifact_kind: str
    artifact_path: str
    artifact_contract_path: str
    artifact_report: str
    artifact_json: str
    result_frame_path: str
    point_id: str
    qdrant_rest_id: str
    vector_json: str
    collection: str
    dimension: int
    status: str
    machine_vector_handoff: bool
    strict_vector_handoff: bool
    sql_context_store_surface: Mapping[str, Any]
    persistence_mode: str = _PERSISTENCE_MODE
    durable_authority: str = _DURABLE_AUTHORITY
    qdrant_role: str = _QDRANT_ROLE
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_prefix(self.persistence_ref, field_name="persistence_ref", prefix="sql-context-persist:")
        _require_prefix(self.handoff_ref, field_name="handoff_ref", prefix="sql-handoff:")
        _require_prefix(self.sql_ref, field_name="sql_ref", prefix="sql:")
        _require_prefix(self.artifact_ref, field_name="artifact_ref", prefix="artifact:")
        _require_non_empty(self.artifact_kind, field_name="artifact_kind")
        _require_non_empty(self.artifact_path, field_name="artifact_path")
        _require_non_empty(self.artifact_contract_path, field_name="artifact_contract_path")
        _require_non_empty(self.artifact_report, field_name="artifact_report")
        _require_non_empty(self.artifact_json, field_name="artifact_json")
        _require_non_empty(self.result_frame_path, field_name="result_frame_path")
        _require_prefix(self.point_id, field_name="point_id", prefix="qdrant-point:")
        _require_non_empty(self.qdrant_rest_id, field_name="qdrant_rest_id")
        _require_non_empty(self.vector_json, field_name="vector_json")
        _require_non_empty(self.collection, field_name="collection")
        _normalize_dimension(self.dimension)
        _require_non_empty(self.status, field_name="status")
        _normalize_bool(self.machine_vector_handoff, field_name="machine_vector_handoff")
        _normalize_bool(self.strict_vector_handoff, field_name="strict_vector_handoff")
        if self.persistence_mode != _PERSISTENCE_MODE:
            raise ValueError("0149 only supports sql_context_store_record persistence_mode")
        if self.durable_authority != _DURABLE_AUTHORITY:
            raise ValueError("durable_authority must remain sql")
        if self.qdrant_role != _QDRANT_ROLE:
            raise ValueError("qdrant_role must remain projection_recall_index")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "persistence_ref": self.persistence_ref,
            "handoff_ref": self.handoff_ref,
            "sql_ref": self.sql_ref,
            "artifact_ref": self.artifact_ref,
            "artifact_kind": self.artifact_kind,
            "artifact_path": self.artifact_path,
            "artifact_contract_path": self.artifact_contract_path,
            "artifact_report": self.artifact_report,
            "artifact_json": self.artifact_json,
            "result_frame_path": self.result_frame_path,
            "point_id": self.point_id,
            "qdrant_rest_id": self.qdrant_rest_id,
            "vector_json": self.vector_json,
            "collection": self.collection,
            "dimension": self.dimension,
            "status": self.status,
            "machine_vector_handoff": self.machine_vector_handoff,
            "strict_vector_handoff": self.strict_vector_handoff,
            "sql_context_store_surface": dict(self.sql_context_store_surface),
            "persistence_mode": self.persistence_mode,
            "durable_authority": self.durable_authority,
            "qdrant_role": self.qdrant_role,
            "payload": dict(self.payload),
        }


def default_persistence_ref(*, handoff_ref: str, sql_ref: str) -> str:
    """Derive a stable SQLContextStore persistence ref from handoff and SQL refs."""

    raw = f"{handoff_ref}/record/{sql_ref}"
    safe = "".join(ch if ch.isalnum() else "-" for ch in raw).strip("-").lower()
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"sql-context-persist:{safe}"


def inspect_sql_context_store_surface(root: str | Path) -> SqlContextStoreSurface:
    """Inspect the existing SQLContextStore source without importing a backend."""

    path = Path(root) / "src" / "context" / "sql_context_store.py"
    if not path.exists():
        return SqlContextStoreSurface(
            path=str(path),
            exists=False,
            has_sql_context_store=False,
            candidate_write_methods=(),
            selected_write_method=None,
        )
    text = path.read_text(encoding="utf-8")
    candidates = tuple(method for method in _CANDIDATE_WRITE_METHODS if f"def {method}" in text)
    return SqlContextStoreSurface(
        path=str(path),
        exists=True,
        has_sql_context_store="SQLContextStore" in text,
        candidate_write_methods=candidates,
        selected_write_method=candidates[0] if candidates else None,
    )


def build_sql_context_store_persistence_record(
    *,
    handoff: Mapping[str, Any],
    sql_context_store_surface: SqlContextStoreSurface,
    persistence_ref: str | None = None,
) -> SqlContextStorePersistenceRecord:
    """Build a durable context record from a 0148 SQL handoff mapping."""

    handoff_ref = str(handoff.get("handoff_ref"))
    sql_ref = str(handoff.get("sql_ref"))
    persistence_ref = persistence_ref or default_persistence_ref(handoff_ref=handoff_ref, sql_ref=sql_ref)
    return SqlContextStorePersistenceRecord(
        persistence_ref=persistence_ref,
        handoff_ref=handoff_ref,
        sql_ref=sql_ref,
        artifact_ref=str(handoff.get("artifact_ref")),
        artifact_kind=str(handoff.get("artifact_kind")),
        artifact_path=str(handoff.get("artifact_path")),
        artifact_contract_path=str(handoff.get("artifact_contract_path")),
        artifact_report=str(handoff.get("artifact_report")),
        artifact_json=str(handoff.get("artifact_json")),
        result_frame_path=str(handoff.get("result_frame_path")),
        point_id=str(handoff.get("point_id")),
        qdrant_rest_id=str(handoff.get("qdrant_rest_id")),
        vector_json=str(handoff.get("vector_json")),
        collection=str(handoff.get("collection")),
        dimension=_normalize_dimension(handoff.get("dimension")),
        status=str(handoff.get("status")),
        machine_vector_handoff=_normalize_bool(handoff.get("machine_vector_handoff"), field_name="machine_vector_handoff"),
        strict_vector_handoff=_normalize_bool(handoff.get("strict_vector_handoff"), field_name="strict_vector_handoff"),
        sql_context_store_surface=sql_context_store_surface.to_mapping(),
        payload={
            "source_handoff_keys": sorted(str(key) for key in handoff.keys()),
            "write_attempted": False,
            "write_status": "record_only",
        },
    )


def read_json_mapping(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object in {path}")
    return loaded
