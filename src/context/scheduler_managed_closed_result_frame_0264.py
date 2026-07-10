"""Scheduler-managed closed ResultFrame for the 0260-0263 path.

0264 does not execute SQL, OpenVINO, or Qdrant.  It reads the reports produced
by the already-controlled steps and composes a serialisable ResultFrame proving
that the same SQL authority reference flows through write, embedding,
projection, recall, and rehydration.

Boundary:
- SQL remains the durable authority.
- Qdrant remains projection/recall only.
- OpenVINO is not executed in 0264.
- Scheduler does not start PostgreSQL, OpenVINO, or Qdrant.
- No RuntimeManager and no Scheduler.run modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


RESULT_FRAME_SCHEMA = "missipy.scheduler_managed_closed_result_frame.v1"


@dataclass(frozen=True)
class ClosedResultFrameReportRefs:
    """Input report paths used to compose the closed frame."""

    sql_write_report: str
    embedding_report: str
    projection_report: str
    recall_rehydrate_report: str

    def to_mapping(self) -> dict[str, str]:
        return {
            "sql_write_report": self.sql_write_report,
            "embedding_report": self.embedding_report,
            "projection_report": self.projection_report,
            "recall_rehydrate_report": self.recall_rehydrate_report,
        }


@dataclass(frozen=True)
class SchedulerManagedClosedResultFrame:
    """Serializable closed frame for the current prototype loop."""

    valid: bool
    issues: tuple[str, ...]
    report_refs: ClosedResultFrameReportRefs
    sql_ref: str = ""
    embedding_ref: str = ""
    projection_point_count: int = 0
    recall_hit_count: int = 0
    hydrated_count: int = 0
    missing_count: int = 0
    hydrated_records: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    scheduler_owned: bool = True
    sql_remains_authority: bool = True
    qdrant_projection_recall_refs_only: bool = True
    openvino_already_executed_by_0261: bool = True
    executes_runtime: bool = False
    starts_postgresql: bool = False
    starts_openvino: bool = False
    starts_qdrant: bool = False
    creates_runtime_manager: bool = False
    modifies_scheduler_run: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": RESULT_FRAME_SCHEMA,
            "scheduler_managed_closed_result_frame": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "report_refs": self.report_refs.to_mapping(),
            "sql_ref": self.sql_ref,
            "embedding_ref": self.embedding_ref,
            "projection_point_count": self.projection_point_count,
            "recall_hit_count": self.recall_hit_count,
            "hydrated_count": self.hydrated_count,
            "missing_count": self.missing_count,
            "hydrated_records": [dict(record) for record in self.hydrated_records],
            "scheduler_owned": self.scheduler_owned,
            "sql_remains_authority": self.sql_remains_authority,
            "qdrant_projection_recall_refs_only": self.qdrant_projection_recall_refs_only,
            "openvino_already_executed_by_0261": self.openvino_already_executed_by_0261,
            "executes_runtime": self.executes_runtime,
            "starts_postgresql": self.starts_postgresql,
            "starts_openvino": self.starts_openvino,
            "starts_qdrant": self.starts_qdrant,
            "creates_runtime_manager": self.creates_runtime_manager,
            "modifies_scheduler_run": self.modifies_scheduler_run,
            "trace": {
                "0260": {
                    "kind": "sql_controlled_write",
                    "sql_ref": self.sql_ref,
                },
                "0261": {
                    "kind": "sql_rehydrate_openvino_embedding",
                    "sql_ref": self.sql_ref,
                    "embedding_ref": self.embedding_ref,
                },
                "0262": {
                    "kind": "embedding_qdrant_projection",
                    "sql_ref": self.sql_ref,
                    "embedding_ref": self.embedding_ref,
                    "point_count": self.projection_point_count,
                },
                "0263": {
                    "kind": "qdrant_recall_sql_rehydrate",
                    "sql_ref": self.sql_ref,
                    "hit_count": self.recall_hit_count,
                    "hydrated_count": self.hydrated_count,
                    "missing_count": self.missing_count,
                },
            },
        }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sql_ref_from_0260(report: Mapping[str, Any]) -> str:
    candidates: list[Any] = [
        report.get("sql_ref"),
        report.get("usage", {}).get("sql_ref") if isinstance(report.get("usage"), Mapping) else "",
        report.get("result", {}).get("sql_ref") if isinstance(report.get("result"), Mapping) else "",
    ]
    for value in candidates:
        if isinstance(value, str) and value.startswith("sql:"):
            return value
    return ""


def _embedding_from_0261(report: Mapping[str, Any]) -> Mapping[str, Any]:
    embedding = report.get("embedding", {})
    if isinstance(embedding, Mapping):
        return embedding
    return {}


def _projection_points_from_0262(report: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    batch = report.get("batch", {})
    if not isinstance(batch, Mapping):
        return ()
    points = batch.get("points", [])
    if not isinstance(points, list):
        return ()
    return tuple(point for point in points if isinstance(point, Mapping))


def _projection_sql_refs(points: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    refs: list[str] = []
    for point in points:
        payload = point.get("payload", {})
        ref = point.get("sql_context_ref")
        if not isinstance(ref, str) and isinstance(payload, Mapping):
            ref = payload.get("sql_ref") or payload.get("sql_context_ref")
        if isinstance(ref, str) and ref.startswith("sql:") and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _projection_embedding_refs(points: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    refs: list[str] = []
    for point in points:
        ref = point.get("embedding_ref")
        if isinstance(ref, str) and ref.startswith("embedding:") and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _recall_hit_count(report: Mapping[str, Any]) -> int:
    recall = report.get("recall", {})
    if not isinstance(recall, Mapping):
        return 0
    hit_count = recall.get("hit_count")
    if isinstance(hit_count, int):
        return hit_count
    hits = recall.get("hits", [])
    if isinstance(hits, list):
        return len(hits)
    return 0


def _recall_sql_refs(report: Mapping[str, Any]) -> tuple[str, ...]:
    refs = report.get("sql_refs", [])
    if not isinstance(refs, list):
        return ()
    return tuple(ref for ref in refs if isinstance(ref, str) and ref.startswith("sql:"))


def _hydrated_records(report: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    records = report.get("hydrated_records", [])
    if not isinstance(records, list):
        return ()
    return tuple(record for record in records if isinstance(record, Mapping))


def _hydrated_sql_refs(records: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    refs: list[str] = []
    for record in records:
        ref = record.get("context_ref")
        if isinstance(ref, str) and ref.startswith("sql:") and ref not in refs:
            refs.append(ref)
    return tuple(refs)


def _missing_count(report: Mapping[str, Any]) -> int:
    value = report.get("missing_count")
    if isinstance(value, int):
        return value
    missing = report.get("missing_sql_refs", [])
    if isinstance(missing, list):
        return len(missing)
    return 0


def compose_scheduler_managed_closed_result_frame(
    *,
    sql_write_report: Mapping[str, Any],
    embedding_report: Mapping[str, Any],
    projection_report: Mapping[str, Any],
    recall_rehydrate_report: Mapping[str, Any],
    report_refs: ClosedResultFrameReportRefs,
) -> SchedulerManagedClosedResultFrame:
    """Compose and validate the closed ResultFrame from existing reports."""

    issues: list[str] = []

    sql_ref = _sql_ref_from_0260(sql_write_report)
    embedding = _embedding_from_0261(embedding_report)
    embedding_sql_ref = str(embedding.get("sql_ref") or "")
    embedding_ref = str(embedding.get("embedding_ref") or "")
    projection_points = _projection_points_from_0262(projection_report)
    projection_sql_refs = _projection_sql_refs(projection_points)
    projection_embedding_refs = _projection_embedding_refs(projection_points)
    recall_sql_refs = _recall_sql_refs(recall_rehydrate_report)
    hydrated_records = _hydrated_records(recall_rehydrate_report)
    hydrated_sql_refs = _hydrated_sql_refs(hydrated_records)
    recall_hit_count = _recall_hit_count(recall_rehydrate_report)
    missing_count = _missing_count(recall_rehydrate_report)

    if not sql_ref:
        issues.append("0260 report must expose a typed sql_ref")
    if not embedding_sql_ref.startswith("sql:"):
        issues.append("0261 embedding must expose a typed sql_ref")
    if not embedding_ref.startswith("embedding:"):
        issues.append("0261 embedding must expose a typed embedding_ref")
    if sql_ref and embedding_sql_ref and sql_ref != embedding_sql_ref:
        issues.append("0260 sql_ref must match 0261 embedding.sql_ref")
    if sql_ref and projection_sql_refs and sql_ref not in projection_sql_refs:
        issues.append("0262 projection must carry payload.sql_ref matching 0260 sql_ref")
    if embedding_ref and projection_embedding_refs and embedding_ref not in projection_embedding_refs:
        issues.append("0262 projection must carry embedding_ref matching 0261")
    if sql_ref and recall_sql_refs and sql_ref not in recall_sql_refs:
        issues.append("0263 recall sql_refs must include the closed sql_ref")
    if sql_ref and hydrated_sql_refs and sql_ref not in hydrated_sql_refs:
        issues.append("0263 hydrated records must include the closed sql_ref")
    if not projection_points:
        issues.append("0262 projection must contain at least one point")
    if recall_hit_count <= 0:
        issues.append("0263 recall must contain at least one hit")
    if not hydrated_records:
        issues.append("0263 SQL rehydrate must return at least one record")
    if missing_count != 0:
        issues.append("0263 SQL rehydrate must have no missing refs")

    return SchedulerManagedClosedResultFrame(
        valid=not issues,
        issues=tuple(issues),
        report_refs=report_refs,
        sql_ref=sql_ref or embedding_sql_ref,
        embedding_ref=embedding_ref,
        projection_point_count=len(projection_points),
        recall_hit_count=recall_hit_count,
        hydrated_count=len(hydrated_records),
        missing_count=missing_count,
        hydrated_records=hydrated_records,
    )


def compose_scheduler_managed_closed_result_frame_from_paths(
    *,
    sql_write_report_path: Path,
    embedding_report_path: Path,
    projection_report_path: Path,
    recall_rehydrate_report_path: Path,
) -> SchedulerManagedClosedResultFrame:
    """Load reports from disk and compose the closed ResultFrame."""

    refs = ClosedResultFrameReportRefs(
        sql_write_report=str(sql_write_report_path),
        embedding_report=str(embedding_report_path),
        projection_report=str(projection_report_path),
        recall_rehydrate_report=str(recall_rehydrate_report_path),
    )
    return compose_scheduler_managed_closed_result_frame(
        sql_write_report=_load_json(sql_write_report_path),
        embedding_report=_load_json(embedding_report_path),
        projection_report=_load_json(projection_report_path),
        recall_rehydrate_report=_load_json(recall_rehydrate_report_path),
        report_refs=refs,
    )


def write_result_frame(output: Path, frame: SchedulerManagedClosedResultFrame) -> None:
    """Write a JSON ResultFrame report."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(frame.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
