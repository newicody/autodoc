import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_source_map_tool_runs_on_repository() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_scheduler_owned_runtime_reuse_source_map_0256.py",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert "scheduler_owned_runtime_reuse_source_map_complete=" in result.stdout
    assert "scheduler:" in result.stdout
    assert result.returncode in (0, 2)
