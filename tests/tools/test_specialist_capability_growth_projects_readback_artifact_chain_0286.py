from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_TOOL = (
    ROOT
    / "tools/"
    "build_specialist_capability_growth_projects_readback_fixture_0286.py"
)
READBACK_TOOL = (
    ROOT
    / "tools/check_specialist_capability_growth_projects_readback_0286.py"
)
APPLY_TOOL = (
    ROOT
    / "tools/apply_specialist_capability_growth_projects_projection_0286.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_builder_and_local_readback(tmp_path: Path) -> None:
    fixture = _load(FIXTURE_TOOL, "fixture_builder_0286")
    readback = _load(READBACK_TOOL, "readback_artifact_chain_0286")
    output_dir = tmp_path / "fixture"
    assert fixture.main(["--output-dir", str(output_dir)]) == 0

    report_path = tmp_path / "readback.json"
    status = readback.main(
        [
            "--plan",
            str(output_dir / "capability-growth-plan.json"),
            "--execution-result",
            str(output_dir / "capability-growth-execution.json"),
            "--issue-comments",
            str(output_dir / "issue-comments.json"),
            "--projectv2-fields",
            str(output_dir / "projectv2-fields.json"),
            "--output",
            str(report_path),
            "--format",
            "summary",
        ]
    )
    assert status == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    evidence = report["evidence"]
    assert evidence["valid"] is True
    assert evidence["action"] == "snapshot_ready"
    assert evidence["deployment_ready"] is False
    assert evidence["remote_query_performed"] is False


def test_r6_preview_can_write_a_json_report(tmp_path: Path) -> None:
    fixture = _load(FIXTURE_TOOL, "fixture_builder_for_r6_0286")
    apply_tool = _load(APPLY_TOOL, "apply_output_0286")
    output_dir = tmp_path / "fixture"
    fixture.main(["--output-dir", str(output_dir)])
    report_path = tmp_path / "r6-preview.json"

    status = apply_tool.main(
        [
            "--plan",
            str(output_dir / "capability-growth-plan.json"),
            "--operator-decision",
            "approve",
            "--output",
            str(report_path),
            "--format",
            "summary",
        ]
    )
    assert status == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["result"]["mode"] == "preview"
    assert report["result"]["github_mutation_performed"] is False


def test_readback_preflight_explains_missing_plan(
    tmp_path: Path,
) -> None:
    readback = _load(READBACK_TOOL, "readback_preflight_0286")
    try:
        readback.main(
            [
                "--plan",
                str(tmp_path / "missing-plan.json"),
                "--execution-result",
                str(tmp_path / "missing-execution.json"),
                "--execute",
            ]
        )
    except SystemExit as exc:
        message = str(exc)
        assert "r5 publication plan not found" in message
        assert "fixture" in message
        assert "does not create or publish" in message
    else:
        raise AssertionError("missing plan must be rejected before GitHub")
