import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_scheduler_owned_runtime_component_lifecycle_tool_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_owned_runtime_component_lifecycle_0254.py",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "scheduler_owned_runtime_component_lifecycle_valid=True" in result.stdout
    assert "openvino_embedding_service" in result.stdout
    assert "qdrant_projection_store" in result.stdout
