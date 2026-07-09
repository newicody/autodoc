import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_sql_controlled_write_handler_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_sql_controlled_write_handler_readiness_0251.py",
            "--server-config",
            SERVER_CONFIG,
            "--openvino-config",
            OPENVINO_CONFIG,
            "--check-only",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "production_server_sql_controlled_write_handler_ready=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "table=context_records" in result.stdout


def test_sql_controlled_write_handler_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_sql_controlled_write_handler_readiness_0251.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_sql_controlled_write_handler_readiness_0251.py",
            "--server-config",
            SERVER_CONFIG,
            "--openvino-config",
            OPENVINO_CONFIG,
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

    assert "production_server_sql_controlled_write_handler_readiness_written=True" in result.stdout
    assert "ready=True" in result.stdout
    assert output.exists()
