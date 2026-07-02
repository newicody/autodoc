from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_projection_gate import (
    SourceCandidateProjectionGatePolicy,
    render_source_candidate_projection_gate,
    run_source_candidate_projection_gate,
)


def _write_bundle(path: Path, *, audit_present: bool = True) -> None:
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
                        "audit_present": audit_present,
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


def test_projection_gate_passes_valid_bundle(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)

    result = run_source_candidate_projection_gate(bundle)

    assert result.passed is True
    assert result.issue_count == 0
    assert result.item_count == 1
    assert result.to_json_dict()["schema"] == "missipy.source_candidate.projection_gate.v1"


def test_projection_gate_reports_missing_manifest(tmp_path: Path) -> None:
    result = run_source_candidate_projection_gate(tmp_path / "missing")

    assert result.passed is False
    assert any(issue.code == "manifest_missing" for issue in result.issues)


def test_projection_gate_can_require_audits(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    _write_bundle(bundle, audit_present=False)

    result = run_source_candidate_projection_gate(
        bundle,
        SourceCandidateProjectionGatePolicy(require_audit_present=True),
    )

    assert result.passed is False
    assert any(issue.code == "audit_required" for issue in result.issues)


def test_projection_gate_render_is_stable(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    _write_bundle(bundle)

    rendered = render_source_candidate_projection_gate(run_source_candidate_projection_gate(bundle))

    assert "projection gate: PASS" in rendered
    assert "items: 1" in rendered
