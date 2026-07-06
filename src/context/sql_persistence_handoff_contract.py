"""Pure SQL persistence handoff contract for vector indexing results.

0148 does not write to SQL and does not create a SQL worker.  It creates a
serializable handoff envelope that can be consumed by the existing SQL context
store in a later patch.  SQL remains the durable authority; Qdrant remains a
projection and recall index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

_DURABLE_AUTHORITY = "sql"
_QDRANT_ROLE = "projection_recall_index"
_DEFAULT_PERSISTENCE_MODE = "handoff_only"


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
class SqlPersistenceHandoffContract:
    """Serializable handoff from vector-indexing result to SQL persistence."""

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
    persistence_mode: str = _DEFAULT_PERSISTENCE_MODE
    durable_authority: str = _DURABLE_AUTHORITY
    qdrant_role: str = _QDRANT_ROLE
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
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
        if self.persistence_mode != _DEFAULT_PERSISTENCE_MODE:
            raise ValueError("0148 only supports handoff_only persistence_mode")
        if self.durable_authority != _DURABLE_AUTHORITY:
            raise ValueError("durable_authority must remain sql")
        if self.qdrant_role != _QDRANT_ROLE:
            raise ValueError("qdrant_role must remain projection_recall_index")

    def to_mapping(self) -> dict[str, Any]:
        return {
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
            "persistence_mode": self.persistence_mode,
            "durable_authority": self.durable_authority,
            "qdrant_role": self.qdrant_role,
            "payload": dict(self.payload),
        }


def build_sql_persistence_handoff_contract(
    *,
    handoff_ref: str,
    artifact_result: Mapping[str, Any],
    artifact_contract: Mapping[str, Any],
    result_frame_payload: Mapping[str, Any] | None = None,
) -> SqlPersistenceHandoffContract:
    """Build a SQL handoff contract from existing artifact/result outputs."""

    result_frame_payload = result_frame_payload or {}
    sql_ref = str(artifact_result.get("sql_ref") or artifact_contract.get("sql_ref") or result_frame_payload.get("sql_ref"))
    artifact_ref = str(artifact_contract.get("artifact_ref") or artifact_result.get("artifact_ref"))
    artifact_kind = str(artifact_contract.get("artifact_kind") or artifact_result.get("artifact_kind") or "local_markdown")
    artifact_path = str(artifact_contract.get("artifact_path") or artifact_result.get("artifact_input"))
    artifact_contract_path = str(artifact_result.get("artifact_contract_path") or artifact_contract.get("artifact_contract_path"))
    artifact_report = str(artifact_result.get("artifact_report"))
    artifact_json = str(artifact_result.get("artifact_json"))
    result_frame_path = str(artifact_result.get("result_frame_path") or result_frame_payload.get("result_frame_path"))
    point_id = str(artifact_result.get("point_id") or result_frame_payload.get("point_id"))
    qdrant_rest_id = str(artifact_result.get("qdrant_rest_id") or result_frame_payload.get("qdrant_rest_id"))
    vector_json = str(artifact_result.get("vector_json") or result_frame_payload.get("vector_json"))
    collection = str(artifact_contract.get("collection") or artifact_result.get("collection") or result_frame_payload.get("collection"))
    dimension = _normalize_dimension(artifact_contract.get("dimension") or artifact_result.get("dimension") or result_frame_payload.get("dimension") or 384)
    status = str(result_frame_payload.get("status") or artifact_result.get("status") or artifact_result.get("vector_indexing_result_frame") or "ok")
    return SqlPersistenceHandoffContract(
        handoff_ref=handoff_ref,
        sql_ref=sql_ref,
        artifact_ref=artifact_ref,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        artifact_contract_path=artifact_contract_path,
        artifact_report=artifact_report,
        artifact_json=artifact_json,
        result_frame_path=result_frame_path,
        point_id=point_id,
        qdrant_rest_id=qdrant_rest_id,
        vector_json=vector_json,
        collection=collection,
        dimension=dimension,
        status=status,
        machine_vector_handoff=_normalize_bool(
            artifact_result.get("machine_vector_handoff", result_frame_payload.get("machine_vector_handoff", False)),
            field_name="machine_vector_handoff",
        ),
        strict_vector_handoff=_normalize_bool(
            artifact_result.get("strict_vector_handoff", result_frame_payload.get("strict_vector_handoff", False)),
            field_name="strict_vector_handoff",
        ),
        payload={
            "artifact_result_keys": sorted(str(key) for key in artifact_result.keys()),
            "artifact_contract_keys": sorted(str(key) for key in artifact_contract.keys()),
            "result_frame_payload_keys": sorted(str(key) for key in result_frame_payload.keys()),
        },
    )


def default_handoff_ref(*, artifact_ref: str, sql_ref: str) -> str:
    """Derive a stable SQL handoff ref from artifact and SQL refs."""

    raw = f"{artifact_ref}/to/{sql_ref}"
    safe = "".join(ch if ch.isalnum() else "-" for ch in raw).strip("-").lower()
    while "--" in safe:
        safe = safe.replace("--", "-")
    return f"sql-handoff:{safe}"


def read_json_mapping(path: str | Path) -> dict[str, Any]:
    data = Path(path).read_text(encoding="utf-8")
    loaded = __import__("json").loads(data)
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object in {path}")
    return loaded
