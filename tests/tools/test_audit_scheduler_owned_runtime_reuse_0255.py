import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_reuse_audit_tool_runs_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audit_scheduler_owned_runtime_reuse_0255.py",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "scheduler_owned_runtime_reuse_audit_passed=" in result.stdout
    assert "scheduler=" in result.stdout
    assert "eventbus=" in result.stdout
    assert "openvino_embedding=" in result.stdout


def test_reuse_audit_can_write_json(tmp_path: Path) -> None:
    output = tmp_path / "reuse_audit.json"
    subprocess.run(
        [
            sys.executable,
            "tools/audit_scheduler_owned_runtime_reuse_0255.py",
            "--output",
            str(output),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["scheduler_owned_runtime_reuse_audit"] is True
    assert payload["read_only"] is True
    assert payload["imports_target_modules"] is False
    assert "surface_counts" in payload["summary"]
