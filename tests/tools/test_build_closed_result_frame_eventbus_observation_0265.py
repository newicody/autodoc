import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0265_tool_builds_and_publishes_observation_facts(tmp_path: Path) -> None:
    frame = tmp_path / "frame.json"
    output = tmp_path / "observation.json"
    frame.write_text(
        json.dumps(
            {
                "schema": "missipy.scheduler_managed_closed_result_frame.v1",
                "valid": True,
                "sql_ref": "sql:inference_context:tool",
                "embedding_ref": "embedding:passage:tool",
                "projection_point_count": 1,
                "recall_hit_count": 1,
                "hydrated_count": 1,
                "missing_count": 0,
                "sql_remains_authority": True,
                "qdrant_projection_recall_refs_only": True,
                "openvino_already_executed_by_0261": True,
                "executes_runtime": False,
                "starts_postgresql": False,
                "starts_openvino": False,
                "starts_qdrant": False,
                "modifies_scheduler_run": False,
                "trace": {"0260": {}, "0261": {}, "0262": {}, "0263": {}},
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_closed_result_frame_eventbus_observation_0265.py",
            "--frame-report",
            str(frame),
            "--output",
            str(output),
            "--publish-demo",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "closed_result_frame_eventbus_observation_valid=True" in result.stdout
    assert "published=3" in result.stdout
    assert "observed=3" in result.stdout

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["facts"][0]["command"] is False
    assert payload["eventbus_observation_only"] is True
