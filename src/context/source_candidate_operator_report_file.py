from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .source_candidate_operator_report import SourceCandidateOperatorReportResult

_FILE_SCHEMA = "missipy.source_candidate.operator_report_file.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorReportFilePolicy:
    """Politique d'écriture locale d'un rapport opérateur SourceCandidate."""

    path: Path | str
    output_format: str = "json"

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if self.output_format not in ("json", "text"):
            raise ValueError("output_format must be json or text")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "output_format": self.output_format,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorReportFileResult:
    """Résultat stable d'écriture d'un rapport opérateur local."""

    path: Path | str
    output_format: str
    byte_count: int
    report: SourceCandidateOperatorReportResult

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if self.byte_count < 0:
            raise ValueError("byte_count must be >= 0")
        if self.output_format not in ("json", "text"):
            raise ValueError("output_format must be json or text")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _FILE_SCHEMA,
            "path": str(self.path),
            "output_format": self.output_format,
            "byte_count": self.byte_count,
            "report_schema": "missipy.source_candidate.operator_report.v1",
            "returned_count": self.report.returned_count,
            "actionable_count": self.report.actionable_count,
            "audit_present_count": self.report.audit_present_count,
        }


def write_source_candidate_operator_report_file(
    report: SourceCandidateOperatorReportResult,
    policy: SourceCandidateOperatorReportFilePolicy,
) -> SourceCandidateOperatorReportFileResult:
    """Écrit un rapport opérateur local de façon atomique."""
    payload = _render_report(report, policy.output_format)
    path = Path(policy.path)
    _atomic_write_text(path, payload)
    return SourceCandidateOperatorReportFileResult(
        path=path,
        output_format=policy.output_format,
        byte_count=len(payload.encode("utf-8")),
        report=report,
    )


def _render_report(report: SourceCandidateOperatorReportResult, output_format: str) -> str:
    if output_format == "json":
        return json.dumps(report.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output_format == "text":
        return report.to_text() + "\n"
    raise ValueError("output_format must be json or text")


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    tmp_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
