import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_run_passive_supervisor_visual_layout_model_writes_json(tmp_path: Path) -> None:
    input_path = tmp_path / "visual_model.json"
    output_path = tmp_path / "layout.json"
    input_path.write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "scheduler:main", "kind": "SCHEDULER", "zone": "scheduler"},
                    {"id": "qdrant:projection", "kind": "QDRANT_PROJECTION", "zone": "qdrant"},
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_passive_supervisor_visual_layout_model_0237.py",
            "--input-json",
            str(input_path),
            "--output",
            str(output_path),
            "--generated-at",
            "2026-07-08T00:00:01Z",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "passive_supervisor_visual_layout_model_written=True" in result.stdout
    layout = json.loads(output_path.read_text(encoding="utf-8"))
    assert layout["node_count"] == 2
    assert layout["zone_count"] == 2
