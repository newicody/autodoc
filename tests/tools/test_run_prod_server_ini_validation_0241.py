import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_ini_validation_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_ini_validation_0241.py",
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

    assert "production_server_ini_valid=True" in result.stdout
    assert "issues=0" in result.stdout


def test_ini_validation_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_ini_validation_0241.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_ini_validation_0241.py",
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

    assert "production_server_ini_validation_written=True" in result.stdout
    assert "valid=True" in result.stdout
    assert output.exists()
