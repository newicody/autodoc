import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONFIG = "doc/examples/autodoc_prod_server_initial_0241.ini"
INITD = "doc/examples/openrc_autodoc_0244.initd"


def test_openrc_surface_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_openrc_launcher_surface_0244.py",
            "--config",
            CONFIG,
            "--initd",
            INITD,
            "--check-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_openrc_launcher_surface_valid=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "configtest,start,stop,status" in result.stdout


def test_openrc_surface_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_openrc_launcher_surface_0244.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_openrc_launcher_surface_0244.py",
            "--config",
            CONFIG,
            "--initd",
            INITD,
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

    assert "production_server_openrc_launcher_surface_written=True" in result.stdout
    assert "valid=True" in result.stdout
    assert output.exists()
