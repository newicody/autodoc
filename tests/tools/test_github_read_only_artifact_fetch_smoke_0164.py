from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_read_only_artifact_fetch_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_github_read_only_artifact_fetch_smoke", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0164_repository_boundary_rejects_development_repo() -> None:
    module = _load_module()

    boundary = module.validate_repository_boundary(
        development_repository="newicody/autodoc",
        external_repository="newicody/autodoc",
    )

    assert boundary["allowed"] is False
    assert any(issue["code"] == "development_repo_ingestion" for issue in boundary["issues"])


def test_0164_operator_report_is_compatible_with_existing_probe_builder(tmp_path: Path) -> None:
    module = _load_module()
    report = module.build_operator_external_review_report(
        repository="newicody/autodoc-ideas",
        project_key="autodoc-ideas",
        allowed=True,
    )
    path = tmp_path / "operator_external_review_report.json"
    module._write_json(path, report)

    from context.source_candidate_read_only_external_probe import build_source_candidate_read_only_external_probe_request_from_file

    request = build_source_candidate_read_only_external_probe_request_from_file(path)

    assert request.repository == "newicody/autodoc-ideas"
    assert request.target_kind == "github_project_surface"
    assert request.dry_run is True
    assert "repository_visible" in request.requested_checks


def test_0164_cli_execute_writes_existing_builder_artifacts(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--output-dir",
            str(tmp_path / "out"),
            "--development-repository",
            "newicody/autodoc",
            "--external-repository",
            "newicody/autodoc-ideas",
            "--project-key",
            "autodoc-ideas",
            "--execute",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "ready" in completed.stdout

    result_path = tmp_path / "out" / "github_read_only_artifact_fetch_smoke_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))

    assert result["status"] == "ok"
    assert result["external_repository"] == "newicody/autodoc-ideas"
    assert result["read_only"] is True
    assert result["probe_allowed"] is True
    assert result["external_call_performed"] is False
    assert result["github_payload_dry_run"] is True
    assert result["github_payload_remote_mutation"] is False
    assert result["mutation_allowed"] is False
    assert result["performed_actions"] == {
        "external_network": False,
        "github_api_call": False,
        "github_mutation": False,
        "llm_execution": False,
        "openvino_execution": False,
        "qdrant_write": False,
        "scheduler_execution": False,
        "sql_write": False,
    }

    for path_key in [
        "operator_report_path",
        "probe_request_path",
        "probe_result_path",
        "bundle_manifest",
        "contract_path",
        "github_payload_path",
        "mutation_gate_path",
    ]:
        assert Path(result[path_key]).exists()

    assert "FakeSourceCandidateReadOnlyExternalProbeAdapter" in result["existing_builders_used"]
    assert "build_source_candidate_external_probe_bundle" in result["existing_builders_used"]
    assert "run_source_candidate_remote_mutation_gate" in result["existing_builders_used"]
