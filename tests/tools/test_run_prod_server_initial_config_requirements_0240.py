import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_initial_configuration_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_initial_config_requirements_0240.py",
            "--check-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_initial_configuration_valid=True" in result.stdout
    assert "errors=0" in result.stdout


def test_initial_configuration_tool_writes_output(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_initial_config_requirements_0240.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_initial_config_requirements_0240.py",
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

    assert "production_server_initial_configuration_written=True" in result.stdout
    assert output.exists()
