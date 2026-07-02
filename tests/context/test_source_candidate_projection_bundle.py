from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_projection_bundle import (
    SourceCandidateProjectionBundlePolicy,
    build_source_candidate_projection_bundle,
)


def _write_report(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.operator_report.v1",
                "items": [
                    {
                        "candidate_id": "candidate-a",
                        "title": "Review me",
                        "status": "new",
                        "decision_summary": {
                            "action": "inspect",
                            "reason": "needs review",
                        },
                        "audit_present": False,
                    },
                    {
                        "candidate_id": "candidate-b",
                        "title": "Archive done",
                        "status": "archived",
                        "decision_summary": {
                            "action": "archive",
                            "reason": "done",
                        },
                        "audit_present": True,
                    },
                ],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def test_projection_bundle_writes_manifest_and_preview(tmp_path: Path) -> None:
    report_path = tmp_path / "operator_report.json"
    bundle_dir = tmp_path / "projection_bundle"
    _write_report(report_path)

    bundle = build_source_candidate_projection_bundle(
        report_path,
        SourceCandidateProjectionBundlePolicy(path=bundle_dir),
    )

    assert bundle.path == bundle_dir
    assert bundle.item_count == 1
    assert bundle.artifact_count == 2
    assert bundle.byte_count > 0
    assert bundle.preview_path.exists()
    assert bundle.manifest_path.exists()

    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    preview = json.loads(bundle.preview_path.read_text(encoding="utf-8"))

    assert manifest["schema"] == "missipy.source_candidate.projection_bundle.v1"
    assert preview["schema"] == "missipy.source_candidate.projection_preview.v1"
    assert preview["item_count"] == 1
    assert preview["items"][0]["candidate_id"] == "candidate-a"


def test_projection_bundle_can_include_terminal_items(tmp_path: Path) -> None:
    report_path = tmp_path / "operator_report.json"
    bundle_dir = tmp_path / "projection_bundle"
    _write_report(report_path)

    bundle = build_source_candidate_projection_bundle(
        report_path,
        SourceCandidateProjectionBundlePolicy(path=bundle_dir, include_terminal=True),
    )

    preview = json.loads(bundle.preview_path.read_text(encoding="utf-8"))
    assert bundle.item_count == 2
    assert [item["candidate_id"] for item in preview["items"]] == [
        "candidate-a",
        "candidate-b",
    ]


def test_projection_bundle_rejects_conflicting_names(tmp_path: Path) -> None:
    report_path = tmp_path / "operator_report.json"
    _write_report(report_path)

    with pytest.raises(ValueError, match="distinct"):
        build_source_candidate_projection_bundle(
            report_path,
            SourceCandidateProjectionBundlePolicy(
                path=tmp_path / "bundle",
                preview_name="same.json",
                manifest_name="same.json",
            ),
        )
