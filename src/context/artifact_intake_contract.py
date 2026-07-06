"""Pure artifact intake contract for local vector indexing.

0146 defines a typed intake envelope for local artifacts before they are passed
through the existing Scheduler/RouteProxy/vector smoke.  This module is a pure
contract surface: it does not import Scheduler, RouteProxy, OpenVINO, Qdrant, or
SQL clients and it does not perform IO.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_ALLOWED_TEXT_KINDS = frozenset({"query", "passage"})
_ALLOWED_ARTIFACT_KINDS = frozenset({"local_markdown", "local_text", "local_json"})


@dataclass(frozen=True, slots=True)
class ArtifactIntakeContract:
    """Typed local artifact intake envelope.

    The contract carries metadata needed to derive Scheduler/RouteProxy/vector
    work later.  It is not an orchestrator and not a storage authority.
    """

    artifact_ref: str
    artifact_kind: str
    artifact_path: Path
    text_kind: str
    sql_ref: str
    collection: str
    dimension: int
    route_root: Path
    vector_indexing_job_ref: str
    text: str

    def normalized_text(self) -> str:
        prefix = f"{self.text_kind}: "
        if self.text.startswith(("query: ", "passage: ")):
            return self.text
        return prefix + self.text

    def to_mapping(self) -> dict[str, Any]:
        return {
            "artifact_ref": self.artifact_ref,
            "artifact_kind": self.artifact_kind,
            "artifact_path": str(self.artifact_path),
            "text_kind": self.text_kind,
            "sql_ref": self.sql_ref,
            "collection": self.collection,
            "dimension": self.dimension,
            "route_root": str(self.route_root),
            "vector_indexing_job_ref": self.vector_indexing_job_ref,
            "text": self.normalized_text(),
            "boundary": "pure artifact intake contract; Scheduler/RouteProxy/OpenVINO/Qdrant stay outside",
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ArtifactIntakeContract":
        return build_artifact_intake_contract(
            artifact_ref=str(data["artifact_ref"]),
            artifact_kind=str(data["artifact_kind"]),
            artifact_path=Path(str(data["artifact_path"])),
            text_kind=str(data["text_kind"]),
            sql_ref=str(data["sql_ref"]),
            collection=str(data["collection"]),
            dimension=int(data["dimension"]),
            route_root=Path(str(data["route_root"])),
            vector_indexing_job_ref=str(data["vector_indexing_job_ref"]),
            text=str(data["text"]),
        )


def build_artifact_intake_contract(
    *,
    artifact_ref: str,
    artifact_kind: str,
    artifact_path: Path,
    text_kind: str,
    sql_ref: str,
    collection: str,
    dimension: int,
    route_root: Path,
    vector_indexing_job_ref: str,
    text: str,
) -> ArtifactIntakeContract:
    artifact_ref = _require_prefix("artifact_ref", artifact_ref.strip(), "artifact:")
    artifact_kind = _require_member("artifact_kind", artifact_kind.strip(), _ALLOWED_ARTIFACT_KINDS)
    text_kind = _require_member("text_kind", text_kind.strip(), _ALLOWED_TEXT_KINDS)
    sql_ref = _require_prefix("sql_ref", sql_ref.strip(), "sql:")
    collection = _require_non_empty("collection", collection.strip())
    vector_indexing_job_ref = _require_prefix("vector_indexing_job_ref", vector_indexing_job_ref.strip(), "vector-indexing-job:")
    text = _require_non_empty("text", text.strip())
    if dimension <= 0:
        raise ValueError("dimension must be positive")
    return ArtifactIntakeContract(
        artifact_ref=artifact_ref,
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        text_kind=text_kind,
        sql_ref=sql_ref,
        collection=collection,
        dimension=dimension,
        route_root=route_root,
        vector_indexing_job_ref=vector_indexing_job_ref,
        text=text,
    )


def _require_non_empty(field: str, value: str) -> str:
    if not value:
        raise ValueError(f"{field} must be non-empty")
    return value


def _require_prefix(field: str, value: str, prefix: str) -> str:
    value = _require_non_empty(field, value)
    if not value.startswith(prefix):
        raise ValueError(f"{field} must start with {prefix!r}")
    return value


def _require_member(field: str, value: str, allowed: frozenset[str]) -> str:
    value = _require_non_empty(field, value)
    if value not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)!r}")
    return value
