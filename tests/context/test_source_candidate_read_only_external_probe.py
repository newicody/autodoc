from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_read_only_external_probe import (
    FakeSourceCandidateReadOnlyExternalProbeAdapter,
    build_source_candidate_read_only_external_probe_request_from_file,
    build_source_candidate_read_only_external_probe_request_from_operator_report,
    read_source_candidate_read_only_external_probe_result,
    render_source_candidate_read_only_external_probe_result,
    write_source_candidate_read_only_external_probe_request,
    write_source_candidate_read_only_external_probe_result,
)


def _operator_report(*, recommended_action: str = "operator_review", dry_run: bool = True) -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.operator_external_review_report.v1",
        "bundle_path": "/tmp/github_export_bundle",
        "repository": "newicody/autodoc",
        "dry_run": dry_run,
        "mutation_allowed": True,
        "operation_count": 1,
        "artifact_count": 5,
        "finding_count": 0,
        "recommended_action": recommended_action,
        "findings": [],
    }


def test_read_only_probe_request_builds_from_operator_review() -> None:
    request = build_source_candidate_read_only_external_probe_request_from_operator_report(
        _operator_report()
    )

    assert request.target_kind == "github_project_surface"
    assert request.repository == "newicody/autodoc"
    assert request.dry_run is True
    assert "repository_visible" in request.requested_checks


def test_read_only_probe_request_rejects_not_ready_report() -> None:
    with pytest.raises(ValueError, match="not ready"):
        build_source_candidate_read_only_external_probe_request_from_operator_report(
            _operator_report(recommended_action="fix_errors")
        )


def test_fake_read_only_probe_never_performs_external_call() -> None:
    request = build_source_candidate_read_only_external_probe_request_from_operator_report(
        _operator_report()
    )
    adapter = FakeSourceCandidateReadOnlyExternalProbeAdapter(
        available_repositories=("newicody/autodoc",)
    )

    result = adapter.probe(request)

    assert result.read_only is True
    assert result.external_call_performed is False
    assert result.probe_allowed is True
    assert result.finding_count == 0


def test_fake_read_only_probe_warns_when_repository_not_confirmed() -> None:
    request = build_source_candidate_read_only_external_probe_request_from_operator_report(
        _operator_report()
    )
    adapter = FakeSourceCandidateReadOnlyExternalProbeAdapter()

    result = adapter.probe(request)

    assert result.probe_allowed is True
    assert any(finding.code == "repository_not_confirmed" for finding in result.findings)


def test_fake_read_only_probe_blocks_not_dry_run_request() -> None:
    request = build_source_candidate_read_only_external_probe_request_from_operator_report(
        _operator_report(dry_run=False)
    )
    adapter = FakeSourceCandidateReadOnlyExternalProbeAdapter(
        available_repositories=("newicody/autodoc",)
    )

    result = adapter.probe(request)

    assert result.probe_allowed is False
    assert any(finding.code == "not_dry_run" for finding in result.findings)


def test_read_only_probe_json_io(tmp_path: Path) -> None:
    report_path = tmp_path / "operator_external_review_report.json"
    request_path = tmp_path / "read_only_probe_request.json"
    result_path = tmp_path / "read_only_probe_result.json"
    report_path.write_text(json.dumps(_operator_report()) + "\n", encoding="utf-8")

    request = build_source_candidate_read_only_external_probe_request_from_file(report_path)
    adapter = FakeSourceCandidateReadOnlyExternalProbeAdapter(
        available_repositories=("newicody/autodoc",)
    )
    result = adapter.probe(request)

    assert write_source_candidate_read_only_external_probe_request(request_path, request) == request_path
    assert write_source_candidate_read_only_external_probe_result(result_path, result) == result_path

    payload = read_source_candidate_read_only_external_probe_result(result_path)
    assert payload["schema"] == "missipy.source_candidate.read_only_external_probe_result.v1"
    assert payload["external_call_performed"] is False


def test_read_only_probe_render_is_stable() -> None:
    request = build_source_candidate_read_only_external_probe_request_from_operator_report(
        _operator_report()
    )
    result = FakeSourceCandidateReadOnlyExternalProbeAdapter().probe(request)

    text = render_source_candidate_read_only_external_probe_result(result)

    assert "read-only external probe: PASS" in text
    assert "external_call_performed: False" in text
