import json
import subprocess
import sys
from pathlib import Path


def test_run_passive_bus_supervisor_cellular_snapshot_writes_snapshot(
    tmp_path: Path,
) -> None:
    events_jsonl = tmp_path / "events.jsonl"
    output = tmp_path / "snapshot.json"
    events_jsonl.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "event_id": "evt-1",
                        "event_kind": "artifact_seen",
                        "cell_id": "artifact",
                        "cell_kind": "GITHUB_ARTIFACT",
                        "state": "queued",
                        "observed_at": "2026-07-08T00:00:00Z",
                        "artifact_ref": "artifact-1",
                    }
                ),
                json.dumps(
                    {
                        "event_id": "evt-2",
                        "event_kind": "artifact_imported",
                        "cell_id": "artifact",
                        "cell_kind": "GITHUB_ARTIFACT",
                        "state": "success",
                        "observed_at": "2026-07-08T00:00:01Z",
                        "artifact_ref": "artifact-1",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_passive_bus_supervisor_cellular_snapshot_0220.py",
            "--events-jsonl",
            str(events_jsonl),
            "--output",
            str(output),
            "--generated-at",
            "2026-07-08T00:00:02Z",
            "--format",
            "json",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )

    stdout_payload = json.loads(result.stdout)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_payload == payload
    assert payload["cellular_snapshot_written"] is True
    assert payload["supervision_authority_violation"] is False
    assert payload["event_count"] == 2
    assert payload["cell_count"] == 1
    assert payload["cells"][0]["cell_id"] == "artifact"
    assert payload["cells"][0]["state"] == "success"
    assert payload["cells"][0]["refs"]["artifact_ref"] == "artifact-1"
