import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_qdrant_collection_readiness_tool_check_only_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_qdrant_collection_readiness_0247.py",
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

    assert "production_server_qdrant_collection_ready=True" in result.stdout
    assert "issues=0" in result.stdout
    assert "dimension=384" in result.stdout
    assert "distance=cosine" in result.stdout


def test_qdrant_collection_readiness_tool_writes_report(tmp_path: Path) -> None:
    output = tmp_path / "prod_server_qdrant_collection_readiness_0247.json"
    result = subprocess.run(
        [
            sys.executable,
            "tools/run_prod_server_qdrant_collection_readiness_0247.py",
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

    assert "production_server_qdrant_collection_readiness_written=True" in result.stdout
    assert "ready=True" in result.stdout
    assert output.exists()
