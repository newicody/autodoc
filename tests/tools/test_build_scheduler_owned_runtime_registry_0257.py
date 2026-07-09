import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_registry_tool_uses_source_map_file(tmp_path: Path) -> None:
    source_map = tmp_path / "source_map.json"
    output = tmp_path / "registry.json"
    source_map.write_text(
        json.dumps(
            {
                "complete": True,
                "selections": [
                    {"surface": "eventbus", "primary_paths": ["src/kernel/event_bus.py"], "hits": []},
                    {"surface": "sql_context_store", "primary_paths": ["tools/run_sql_context_store_controlled_write_smoke.py"], "hits": []},
                    {"surface": "openvino_embedding", "primary_paths": ["tools/run_openvino_e5_live_smoke.py"], "hits": []},
                    {"surface": "qdrant_projection", "primary_paths": ["tools/run_qdrant_projection_live_smoke.py"], "hits": []},
                    {"surface": "passive_supervisor", "primary_paths": ["src/context/passive_bus_supervisor_cellular_snapshot.py"], "hits": []},
                    {"surface": "github_artifact_exchange", "primary_paths": ["src/context/github_project_push_frame.py"], "hits": []},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_scheduler_owned_runtime_registry_0257.py",
            "--source-map",
            str(source_map),
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

    assert "scheduler_owned_runtime_registry_valid=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["source_map_complete"] is True
