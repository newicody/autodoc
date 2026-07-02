from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_projection_gate import run_source_candidate_projection_gate
from context.source_candidate_projection_gate_report import (
    SourceCandidateProjectionGateReportPolicy,
    build_source_candidate_projection_gate_report_payload,
    run_source_candidate_projection_gate_report,
    write_source_candidate_projection_gate_report,
)


def _write_bundle(path: Path) -> None:
    path.mkdir(parents=True)
    preview_path = path / "projection_preview.json"
    manifest_path = path / "manifest.json"
    preview_path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_preview.v1",
                "target_name": "operator_project_surface",
                "source_report_schema": "missipy.source_candidate.operator_report.v1",
                "item_count": 1,
                "items": [
                    {
                        "candidate_id": "candidate-a",
                        "title": "Ready",
                        "status": "new",
                        "decision_action": "inspect",
                        "decision_reason": "check",
                        "target_context_id": None,
                        "audit_present": True,
                        "recommended_action": "inspect",
                        "labels": ["status:new"],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_bundle.v1",
                "path": str(path),
                "manifest_path": str(manifest_path),
                "preview_path": str(preview_path),
                "item_count": 1,
                "target_name": "operator_project_surface",
                "source_report_schema": "missipy.source_candidate.operator_report.v1",
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_gate_report_payload_can_include_text(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)
    result = run_source_candidate_projection_gate(bundle)

    payload = build_source_candidate_projection_gate_report_payload(result)

    assert payload["schema"] == "missipy.source_candidate.projection_gate_report.v1"
    assert payload["gate_result"]["passed"] is True
    assert "projection gate: PASS" in payload["text"]


def test_gate_report_writes_json_atomically(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    output = tmp_path / "reports" / "gate_report.json"
    _write_bundle(bundle)
    result = run_source_candidate_projection_gate(bundle)

    report = write_source_candidate_projection_gate_report(
        result,
        SourceCandidateProjectionGateReportPolicy(output_path=output),
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert report.output_path == output
    assert report.byte_count > 0
    assert report.passed is True
    assert payload["schema"] == "missipy.source_candidate.projection_gate_report.v1"


def test_gate_report_can_be_run_from_bundle_path(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    output = tmp_path / "gate_report.json"
    _write_bundle(bundle)

    report = run_source_candidate_projection_gate_report(
        bundle_path=bundle,
        report_policy=SourceCandidateProjectionGateReportPolicy(output_path=output),
    )

    assert report.passed is True
    assert report.item_count == 1
    assert output.exists()
