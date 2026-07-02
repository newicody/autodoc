from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_external_probe_bundle import (
    build_source_candidate_external_probe_bundle,
    read_source_candidate_external_probe_bundle_manifest,
    render_source_candidate_external_probe_bundle,
)


def _write_probe_inputs(path: Path, *, repository: str = "newicody/autodoc") -> tuple[Path, Path, Path]:
    path.mkdir(parents=True)

    operator_review = path / "operator_external_review_report.json"
    request = path / "read_only_external_probe_request.json"
    result = path / "read_only_external_probe_result.json"

    operator_review.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.operator_external_review_report.v1",
                "bundle_path": "/tmp/github_export_bundle",
                "repository": repository,
                "dry_run": True,
                "mutation_allowed": True,
                "operation_count": 1,
                "artifact_count": 5,
                "finding_count": 0,
                "recommended_action": "operator_review",
                "findings": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    request.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.read_only_external_probe_request.v1",
                "target_kind": "github_project_surface",
                "repository": repository,
                "dry_run": True,
                "requested_checks": [
                    "repository_visible",
                    "project_surface_visible",
                    "write_access_not_required",
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.read_only_external_probe_result.v1",
                "target_kind": "github_project_surface",
                "repository": repository,
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": True,
                "check_count": 3,
                "finding_count": 0,
                "findings": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return operator_review, request, result


def test_external_probe_bundle_copies_probe_artifacts_and_manifest(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    bundle = build_source_candidate_external_probe_bundle(
        output_dir=output,
        operator_review_report_path=operator_review,
        probe_request_path=request,
        probe_result_path=result,
    )

    assert bundle.repository == "newicody/autodoc"
    assert bundle.read_only is True
    assert bundle.external_call_performed is False
    assert bundle.probe_allowed is True
    assert bundle.artifact_count == 3
    assert (output / "manifest.json").exists()
    assert (output / "operator_external_review_report.json").exists()
    assert (output / "read_only_external_probe_request.json").exists()
    assert (output / "read_only_external_probe_result.json").exists()


def test_external_probe_bundle_manifest_uses_relative_artifact_paths(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    bundle = build_source_candidate_external_probe_bundle(
        output_dir=output,
        operator_review_report_path=operator_review,
        probe_request_path=request,
        probe_result_path=result,
    )
    payload = read_source_candidate_external_probe_bundle_manifest(bundle.manifest_path)

    assert payload["schema"] == "missipy.source_candidate.external_probe_bundle.v1"
    assert payload["artifact_count"] == 3
    assert payload["external_call_performed"] is False
    assert {artifact["path"] for artifact in payload["artifacts"]} == {
        "operator_external_review_report.json",
        "read_only_external_probe_request.json",
        "read_only_external_probe_result.json",
    }


def test_external_probe_bundle_rejects_repository_mismatch(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    payload = json.loads(result.read_text(encoding="utf-8"))
    payload["repository"] = "other/repo"
    result.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="repository mismatch"):
        build_source_candidate_external_probe_bundle(
            output_dir=output,
            operator_review_report_path=operator_review,
            probe_request_path=request,
            probe_result_path=result,
        )


def test_external_probe_bundle_rejects_schema_mismatch(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    payload = json.loads(request.read_text(encoding="utf-8"))
    payload["schema"] = "wrong.schema"
    request.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="schema mismatch"):
        build_source_candidate_external_probe_bundle(
            output_dir=output,
            operator_review_report_path=operator_review,
            probe_request_path=request,
            probe_result_path=result,
        )


def test_external_probe_bundle_render_is_stable(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    bundle = build_source_candidate_external_probe_bundle(
        output_dir=output,
        operator_review_report_path=operator_review,
        probe_request_path=request,
        probe_result_path=result,
    )
    text = render_source_candidate_external_probe_bundle(bundle)

    assert "external probe bundle: PASS" in text
    assert "repository: newicody/autodoc" in text
    assert "external_call_performed: False" in text
