from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_phase6_closure_audit import (
    build_source_candidate_phase6_closure_audit,
    render_source_candidate_phase6_closure_audit,
    write_source_candidate_phase6_closure_audit,
)


def _write_handoff(path: Path, *, passed: bool = True, item_count: int = 1) -> None:
    path.mkdir(parents=True)
    (path / "projection_preview.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_preview.v1",
                "target_name": "operator_project_surface",
                "source_report_schema": "missipy.source_candidate.operator_report.v1",
                "item_count": item_count,
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
                ][:item_count],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "projection_gate_report.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_gate_report.v1",
                "gate_result": {
                    "schema": "missipy.source_candidate.projection_gate.v1",
                    "bundle_path": str(path),
                    "manifest_path": str(path / "manifest.json"),
                    "preview_path": str(path / "projection_preview.json"),
                    "passed": passed,
                    "item_count": item_count,
                    "issue_count": 0 if passed else 1,
                    "issues": [],
                },
                "text": "projection gate: PASS" if passed else "projection gate: FAIL",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (path / "handoff_manifest.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.projection_handoff_dry_run.v1",
                "path": str(path),
                "manifest_path": str(path / "handoff_manifest.json"),
                "projection_bundle_path": str(path / "projection_bundle"),
                "passed": passed,
                "item_count": item_count,
                "artifacts": [
                    {"role": "handoff_manifest", "path": str(path / "handoff_manifest.json")},
                    {"role": "projection_preview", "path": str(path / "projection_preview.json")},
                    {
                        "role": "projection_gate_report",
                        "path": str(path / "projection_gate_report.json"),
                    },
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_phase6_closure_audit_passes_valid_handoff(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff)

    audit = build_source_candidate_phase6_closure_audit(handoff)

    assert audit.passed is True
    assert audit.handoff_passed is True
    assert audit.item_count == 1
    assert audit.artifact_count == 3
    assert audit.issue_count == 0
    assert audit.to_json_dict()["schema"] == "missipy.source_candidate.phase6_closure_audit.v1"


def test_phase6_closure_audit_fails_when_gate_failed(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff, passed=False)

    audit = build_source_candidate_phase6_closure_audit(handoff)

    assert audit.passed is False
    assert audit.handoff_passed is False


def test_phase6_closure_audit_reports_missing_files(tmp_path: Path) -> None:
    audit = build_source_candidate_phase6_closure_audit(tmp_path / "missing")

    assert audit.passed is False
    assert any(issue.code == "handoff_manifest_missing" for issue in audit.issues)


def test_phase6_closure_audit_writes_json(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    output = tmp_path / "phase6_closure_audit.json"
    _write_handoff(handoff)

    audit = write_source_candidate_phase6_closure_audit(handoff, output)
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert audit.output_path == output
    assert payload["schema"] == "missipy.source_candidate.phase6_closure_audit.v1"
    assert payload["passed"] is True


def test_phase6_closure_audit_render_is_stable(tmp_path: Path) -> None:
    handoff = tmp_path / "handoff"
    _write_handoff(handoff)

    rendered = render_source_candidate_phase6_closure_audit(
        build_source_candidate_phase6_closure_audit(handoff)
    )

    assert "phase 6 closure audit: PASS" in rendered
    assert "artifacts: 3" in rendered
