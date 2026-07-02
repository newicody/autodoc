from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_projection_handoff_dry_run import (
    SourceCandidateProjectionHandoffDryRunPolicy,
    build_source_candidate_projection_handoff_dry_run,
)


def _write_projection_bundle(path: Path, *, audit_present: bool = True) -> None:
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
            },
            ensure_ascii=False,
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
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_handoff_dry_run_writes_local_bundle(tmp_path: Path) -> None:
    source_bundle = tmp_path / "projection_bundle"
    handoff_dir = tmp_path / "handoff"
    _write_projection_bundle(source_bundle)

    result = build_source_candidate_projection_handoff_dry_run(
        source_bundle,
        SourceCandidateProjectionHandoffDryRunPolicy(path=handoff_dir),
    )

    assert result.passed is True
    assert result.item_count == 1
    assert result.artifact_count == 3
    assert result.byte_count > 0
    assert (handoff_dir / "handoff_manifest.json").exists()
    assert (handoff_dir / "projection_preview.json").exists()
    assert (handoff_dir / "projection_gate_report.json").exists()

    manifest = json.loads((handoff_dir / "handoff_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "missipy.source_candidate.projection_handoff_dry_run.v1"
    assert manifest["passed"] is True


def test_handoff_dry_run_can_fail_gate_without_external_effects(tmp_path: Path) -> None:
    source_bundle = tmp_path / "projection_bundle"
    handoff_dir = tmp_path / "handoff"
    _write_projection_bundle(source_bundle, audit_present=False)

    result = build_source_candidate_projection_handoff_dry_run(
        source_bundle,
        SourceCandidateProjectionHandoffDryRunPolicy(
            path=handoff_dir,
            require_audit_present=True,
        ),
    )

    assert result.passed is False
    report = json.loads((handoff_dir / "projection_gate_report.json").read_text(encoding="utf-8"))
    assert report["gate_result"]["passed"] is False


def test_handoff_dry_run_rejects_conflicting_names(tmp_path: Path) -> None:
    source_bundle = tmp_path / "projection_bundle"
    _write_projection_bundle(source_bundle)

    with pytest.raises(ValueError, match="distinct"):
        build_source_candidate_projection_handoff_dry_run(
            source_bundle,
            SourceCandidateProjectionHandoffDryRunPolicy(
                path=tmp_path / "handoff",
                manifest_name="same.json",
                preview_name="same.json",
            ),
        )
