import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_run_passive_supervisor_visual_read_model_writes_json(tmp_path: Path) -> None:
    snapshot = tmp_path / "snapshot.json"
    output = tmp_path / "visual.json"
    snapshot.write_text(
        json.dumps(
            {
                "generated_at": "2026-07-08T00:00:00Z",
                "event_count": 1,
                "cells": [
                    {
                        "cell_id": "github_artifact:artifact-1",
                        "cell_kind": "GITHUB_ARTIFACT",
                        "state": "queued",
                        "health": "active",
                        "artifact_ref": "artifact-1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_passive_supervisor_visual_read_model_0236.py",
            "--snapshot-json",
            str(snapshot),
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

    assert "passive_supervisor_visual_read_model_written=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["node_count"] == 1
    assert payload["nodes"][0]["zone"] == "data"
    assert payload["edges"][0]["edge_kind"] == "artifact_ref"
