import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_recall_rehydrate_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_recall_rehydrate_readiness_0253.py",
            "--check-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_recall_rehydrate_ready=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "table=context_records" in result.stdout
    assert "lookup=id" in result.stdout
