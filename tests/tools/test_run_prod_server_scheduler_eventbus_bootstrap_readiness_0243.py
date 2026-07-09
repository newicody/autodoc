import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_bootstrap_readiness_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_scheduler_eventbus_bootstrap_readiness_0243.py",
            "--config",
            EXAMPLE,
            "--check-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_scheduler_eventbus_bootstrap_ready=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "eventbus,scheduler" in result.stdout


def test_bootstrap_readiness_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_scheduler_eventbus_bootstrap_readiness_0243.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_scheduler_eventbus_bootstrap_readiness_0243.py",
            "--config",
            EXAMPLE,
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_scheduler_eventbus_bootstrap_readiness_written=True" in result.stdout
    assert "ready=True" in result.stdout
    assert output.exists()
