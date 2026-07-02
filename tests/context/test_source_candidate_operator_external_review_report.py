from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_operator_external_review_report import (
    build_source_candidate_operator_external_review_report,
    read_source_candidate_operator_external_review_report,
    render_source_candidate_operator_external_review_report,
    write_source_candidate_operator_external_review_report,
)


def _write_bundle(path: Path, *, mutation_allowed: bool = False, include_adapter: bool = True) -> None:
    path.mkdir(parents=True)

    (path / "external_projection_contract.json").write_text(
        json.dumps({"schema": "missipy.source_candidate.external_projection_contract.v1"}) + "\n",
        encoding="utf-8",
    )
    (path / "github_projection_payload.json").write_text(
        json.dumps({"schema": "missipy.source_candidate.github_projection_payload.v1"}) + "\n",
        encoding="utf-8",
    )
    (path / "remote_mutation_gate.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.remote_mutation_gate.v1",
                "target_kind": "github_projection_payload",
                "repository": "newicody/autodoc",
                "mutation_allowed": mutation_allowed,
                "operation_count": 1,
                "issue_count": 0 if mutation_allowed else 1,
                "issues": []
                if mutation_allowed
                else [
                    {
                        "severity": "error",
                        "code": "operator_not_confirmed",
                        "message": "operator confirmation is required",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    if include_adapter:
        (path / "github_adapter_dry_run.json").write_text(
            json.dumps(
                {
                    "schema": "missipy.source_candidate.github_adapter_dry_run.v1",
                    "plan": {
                        "schema": "missipy.source_candidate.github_adapter_plan.v1",
                        "repository": "newicody/autodoc",
                        "project_key": None,
                        "dry_run": True,
                        "remote_mutation": False,
                        "operation_count": 1,
                        "operations": [],
                    },
                    "gate": {
                        "schema": "missipy.source_candidate.remote_mutation_gate.v1",
                        "mutation_allowed": mutation_allowed,
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

    artifacts = [
        {
            "role": "external_projection_contract",
            "path": str(path / "external_projection_contract.json"),
            "byte_count": 1,
            "schema": "missipy.source_candidate.external_projection_contract.v1",
        },
        {
            "role": "github_projection_payload",
            "path": str(path / "github_projection_payload.json"),
            "byte_count": 1,
            "schema": "missipy.source_candidate.github_projection_payload.v1",
        },
        {
            "role": "remote_mutation_gate",
            "path": str(path / "remote_mutation_gate.json"),
            "byte_count": 1,
            "schema": "missipy.source_candidate.remote_mutation_gate.v1",
        },
    ]
    if include_adapter:
        artifacts.append(
            {
                "role": "github_adapter_dry_run",
                "path": str(path / "github_adapter_dry_run.json"),
                "byte_count": 1,
                "schema": "missipy.source_candidate.github_adapter_dry_run.v1",
            }
        )

    (path / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.github_export_bundle.v1",
                "path": str(path),
                "manifest_path": str(path / "manifest.json"),
                "repository": "newicody/autodoc",
                "mutation_allowed": mutation_allowed,
                "dry_run": True,
                "operation_count": 1,
                "artifact_count": len(artifacts),
                "byte_count": 4,
                "artifacts": artifacts,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_operator_external_review_report_blocks_on_gate_errors(tmp_path: Path) -> None:
    bundle = tmp_path / "github_export_bundle"
    _write_bundle(bundle, mutation_allowed=False)

    report = build_source_candidate_operator_external_review_report(bundle)

    assert report.repository == "newicody/autodoc"
    assert report.dry_run is True
    assert report.mutation_allowed is False
    assert report.recommended_action == "fix_errors"
    assert any(finding.code == "operator_not_confirmed" for finding in report.findings)


def test_operator_external_review_report_ready_when_gate_passes(tmp_path: Path) -> None:
    bundle = tmp_path / "github_export_bundle"
    _write_bundle(bundle, mutation_allowed=True)

    report = build_source_candidate_operator_external_review_report(bundle)

    assert report.mutation_allowed is True
    assert report.recommended_action == "operator_review"
    assert report.finding_count == 0


def test_operator_external_review_report_finds_missing_adapter_artifact(tmp_path: Path) -> None:
    bundle = tmp_path / "github_export_bundle"
    _write_bundle(bundle, mutation_allowed=True, include_adapter=False)

    report = build_source_candidate_operator_external_review_report(bundle)

    assert report.recommended_action == "fix_errors"
    assert any(finding.code == "missing_artifact" for finding in report.findings)
    assert any(finding.code == "adapter_missing_or_unreadable" for finding in report.findings)


def test_operator_external_review_report_writes_and_reads_json(tmp_path: Path) -> None:
    bundle = tmp_path / "github_export_bundle"
    output = tmp_path / "operator_external_review_report.json"
    _write_bundle(bundle, mutation_allowed=True)
    report = build_source_candidate_operator_external_review_report(bundle)

    returned = write_source_candidate_operator_external_review_report(output, report)
    payload = read_source_candidate_operator_external_review_report(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.operator_external_review_report.v1"
    assert payload["recommended_action"] == "operator_review"


def test_operator_external_review_report_render_is_stable(tmp_path: Path) -> None:
    bundle = tmp_path / "github_export_bundle"
    _write_bundle(bundle, mutation_allowed=False)

    text = render_source_candidate_operator_external_review_report(
        build_source_candidate_operator_external_review_report(bundle)
    )

    assert "operator external review: BLOCKED" in text
    assert "repository: newicody/autodoc" in text
    assert "operator_not_confirmed" in text
