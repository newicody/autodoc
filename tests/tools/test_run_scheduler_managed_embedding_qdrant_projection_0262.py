import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


EMBEDDING_REPORT = {
    "embedding": {
        "embedding_ref": "embedding:passage:tool",
        "source_ref": "ctx-fragment:sql:inference_context:tool",
        "sql_ref": "sql:inference_context:tool",
        "backend_ref": "openvino:model:multilingual-e5-small",
        "role": "passage",
        "dimension": 3,
        "normalized": True,
        "l2_norm": 1.0,
        "metadata": {"context_ref": "sql:inference_context:tool", "model_path": "/tmp/model"},
        "vector": [1.0, 0.0, 0.0],
    }
}


def test_0262_tool_dry_run_and_demo_execute(tmp_path: Path) -> None:
    report = tmp_path / "embedding.json"
    output = tmp_path / "projection.json"
    report.write_text(json.dumps(EMBEDDING_REPORT), encoding="utf-8")

    dry = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py",
            "--embedding-report",
            str(report),
            "--output",
            str(output),
            "--dimension",
            "3",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "scheduler_managed_embedding_qdrant_projection_valid=True" in dry.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["batch"]["points"][0]["payload"]["sql_ref"] == "sql:inference_context:tool"

    execute = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_embedding_qdrant_projection_0262.py",
            "--embedding-report",
            str(report),
            "--execute",
            "--policy-decision-id",
            "policy:0262:test",
            "--demo-qdrant",
            "--dimension",
            "3",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "execute=True" in execute.stdout
    assert "acknowledged=True" in execute.stdout
