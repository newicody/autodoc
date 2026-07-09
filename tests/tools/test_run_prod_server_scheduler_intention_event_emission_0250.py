import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_scheduler_intention_event_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_scheduler_intention_event_emission_0250.py",
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

    assert "production_server_scheduler_intention_event_emission_valid=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "event_id=event:" in result.stdout


def test_scheduler_intention_event_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_scheduler_intention_event_emission_0250.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_scheduler_intention_event_emission_0250.py",
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

    assert "production_server_scheduler_intention_event_emission_written=True" in result.stdout
    assert "valid=True" in result.stdout
    assert output.exists()
