from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import tempfile

from .source_candidate_projection_gate import (
    SourceCandidateProjectionGatePolicy,
    SourceCandidateProjectionGateResult,
    render_source_candidate_projection_gate,
    run_source_candidate_projection_gate,
)


_REPORT_SCHEMA = "missipy.source_candidate.projection_gate_report.v1"


@dataclass(frozen=True)
class SourceCandidateProjectionGateReportPolicy:
    """Local report policy for projection gate results."""

    output_path: Path
    include_text: bool = True


@dataclass(frozen=True)
class SourceCandidateProjectionGateReport:
    output_path: Path
    byte_count: int
    passed: bool
    issue_count: int
    item_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPORT_SCHEMA,
            "output_path": str(self.output_path),
            "byte_count": self.byte_count,
            "passed": self.passed,
            "issue_count": self.issue_count,
            "item_count": self.item_count,
        }


def build_source_candidate_projection_gate_report_payload(
    result: SourceCandidateProjectionGateResult,
    *,
    include_text: bool = True,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": _REPORT_SCHEMA,
        "gate_result": result.to_json_dict(),
    }
    if include_text:
        payload["text"] = render_source_candidate_projection_gate(result)
    return payload


def write_source_candidate_projection_gate_report(
    result: SourceCandidateProjectionGateResult,
    policy: SourceCandidateProjectionGateReportPolicy,
) -> SourceCandidateProjectionGateReport:
    """Write a projection gate result report atomically."""

    if not str(policy.output_path).strip():
        raise ValueError("output_path must not be empty")

    payload = build_source_candidate_projection_gate_report_payload(
        result,
        include_text=policy.include_text,
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(policy.output_path, text)

    return SourceCandidateProjectionGateReport(
        output_path=policy.output_path,
        byte_count=policy.output_path.stat().st_size,
        passed=result.passed,
        issue_count=result.issue_count,
        item_count=result.item_count,
    )


def run_source_candidate_projection_gate_report(
    *,
    bundle_path: Path,
    report_policy: SourceCandidateProjectionGateReportPolicy,
    gate_policy: SourceCandidateProjectionGatePolicy | None = None,
) -> SourceCandidateProjectionGateReport:
    result = run_source_candidate_projection_gate(bundle_path, gate_policy)
    return write_source_candidate_projection_gate_report(result, report_policy)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(text)
    os.replace(tmp_name, path)
