import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_visual_pipeline_tool_can_print_plan(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_passive_supervisor_visual_pipeline_smoke_0238.py",
            "--report-dir",
            str(tmp_path),
            "--plan-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "passive_supervisor_visual_pipeline_plan=True" in result.stdout
    assert "steps=3" in result.stdout
