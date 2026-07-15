from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = (
    ROOT
    / "tools/"
    "build_specialist_capability_growth_projects_readback_fixture_0286.py"
)
READBACK = (
    ROOT
    / "tools/check_specialist_capability_growth_projects_readback_0286.py"
)
SMOKE = (
    ROOT
    / "tools/run_specialist_capability_growth_projects_"
    "closed_loop_smoke_0286.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixture_readback_then_r8_smoke(tmp_path: Path) -> None:
    fixture = _load(FIXTURE, "fixture_for_r8")
    readback = _load(READBACK, "readback_for_r8")
    smoke = _load(SMOKE, "smoke_cli_r8")

    artifacts = tmp_path / "artifacts"
    assert fixture.main(["--output-dir", str(artifacts)]) == 0
    readback_path = artifacts / "readback.json"
    assert readback.main(
        [
            "--plan",
            str(artifacts / "capability-growth-plan.json"),
            "--execution-result",
            str(artifacts / "capability-growth-execution.json"),
            "--issue-comments",
            str(artifacts / "issue-comments.json"),
            "--projectv2-fields",
            str(artifacts / "projectv2-fields.json"),
            "--output",
            str(readback_path),
            "--format",
            "summary",
        ]
    ) == 0

    smoke_path = artifacts / "closed-loop-smoke.json"
    assert smoke.main(
        [
            "--plan",
            str(artifacts / "capability-growth-plan.json"),
            "--execution-result",
            str(artifacts / "capability-growth-execution.json"),
            "--readback",
            str(readback_path),
            "--output",
            str(smoke_path),
            "--format",
            "summary",
        ]
    ) == 0
    result = json.loads(smoke_path.read_text(encoding="utf-8"))["result"]
    assert result["phase_0286_closed"] is True
    assert result["local_contract_closed"] is True
    assert result["deployment_closed"] is False


def test_live_requirement_rejects_fixture_readback(tmp_path: Path) -> None:
    fixture = _load(FIXTURE, "fixture_for_r8_live")
    readback = _load(READBACK, "readback_for_r8_live")
    smoke = _load(SMOKE, "smoke_cli_r8_live")
    artifacts = tmp_path / "artifacts"
    fixture.main(["--output-dir", str(artifacts)])
    readback_path = artifacts / "readback.json"
    readback.main(
        [
            "--plan",
            str(artifacts / "capability-growth-plan.json"),
            "--execution-result",
            str(artifacts / "capability-growth-execution.json"),
            "--issue-comments",
            str(artifacts / "issue-comments.json"),
            "--projectv2-fields",
            str(artifacts / "projectv2-fields.json"),
            "--output",
            str(readback_path),
        ]
    )
    assert smoke.main(
        [
            "--plan",
            str(artifacts / "capability-growth-plan.json"),
            "--execution-result",
            str(artifacts / "capability-growth-execution.json"),
            "--readback",
            str(readback_path),
            "--require-live-readback",
        ]
    ) == 3
