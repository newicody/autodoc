from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_external_probe_bundle_cli import (  # noqa: E402
    build_source_candidate_external_probe_bundle_cli_plan,
    main,
    render_source_candidate_external_probe_bundle_cli_plan,
)


def _write_probe_inputs(path: Path) -> tuple[Path, Path, Path]:
    path.mkdir(parents=True)

    operator_review = path / "operator_external_review_report.json"
    request = path / "read_only_external_probe_request.json"
    result = path / "read_only_external_probe_result.json"

    operator_review.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.operator_external_review_report.v1",
                "bundle_path": "/tmp/github_export_bundle",
                "repository": "newicody/autodoc",
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
                "repository": "newicody/autodoc",
                "dry_run": True,
                "requested_checks": ["repository_visible"],
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
                "repository": "newicody/autodoc",
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": True,
                "check_count": 1,
                "finding_count": 0,
                "findings": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return operator_review, request, result


def test_external_probe_bundle_cli_plan_is_dry_run_by_default(tmp_path: Path) -> None:
    plan = build_source_candidate_external_probe_bundle_cli_plan(
        output_dir=tmp_path / "bundle",
        operator_review_report_path=tmp_path / "operator.json",
        probe_request_path=tmp_path / "request.json",
        probe_result_path=tmp_path / "result.json",
    )

    assert plan.apply is False
    assert plan.to_json_dict()["writes_bundle"] is False


def test_external_probe_bundle_cli_plan_render_is_stable(tmp_path: Path) -> None:
    plan = build_source_candidate_external_probe_bundle_cli_plan(
        output_dir=tmp_path / "bundle",
        operator_review_report_path=tmp_path / "operator.json",
        probe_request_path=tmp_path / "request.json",
        probe_result_path=tmp_path / "result.json",
    )

    text = render_source_candidate_external_probe_bundle_cli_plan(plan)

    assert "external probe bundle cli: dry-run" in text
    assert "writes_bundle: False" in text


def test_external_probe_bundle_cli_dry_run_does_not_write_bundle(tmp_path: Path, capsys) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    exit_code = main(
        [
            "--output-dir",
            str(output),
            "--operator-review-report",
            str(operator_review),
            "--probe-request",
            str(request),
            "--probe-result",
            str(result),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "external probe bundle cli: dry-run" in captured.out
    assert not output.exists()


def test_external_probe_bundle_cli_apply_writes_bundle(tmp_path: Path, capsys) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    exit_code = main(
        [
            "--output-dir",
            str(output),
            "--operator-review-report",
            str(operator_review),
            "--probe-request",
            str(request),
            "--probe-result",
            str(result),
            "--apply",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "external probe bundle: PASS" in captured.out
    assert (output / "manifest.json").exists()
    assert (output / "read_only_external_probe_result.json").exists()


def test_external_probe_bundle_cli_json_dry_run(tmp_path: Path, capsys) -> None:
    inputs = tmp_path / "inputs"
    output = tmp_path / "bundle"
    operator_review, request, result = _write_probe_inputs(inputs)

    exit_code = main(
        [
            "--output-dir",
            str(output),
            "--operator-review-report",
            str(operator_review),
            "--probe-request",
            str(request),
            "--probe-result",
            str(result),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.external_probe_bundle_cli_plan.v1"
    assert payload["writes_bundle"] is False
