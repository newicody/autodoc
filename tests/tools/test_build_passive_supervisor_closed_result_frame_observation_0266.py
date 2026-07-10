import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0266_tool_builds_passive_supervisor_report(tmp_path: Path) -> None:
    observation = tmp_path / "observation.json"
    output = tmp_path / "passive-supervisor.json"
    observation.write_text(
        json.dumps(
            {
                "valid": True,
                "eventbus_observation_only": True,
                "events_are_facts_not_commands": True,
                "executes_runtime": False,
                "starts_postgresql": False,
                "starts_openvino": False,
                "starts_qdrant": False,
                "modifies_scheduler_run": False,
                "facts": [
                    {
                        "fact_ref": "event-fact:0265:sql:tool:closed",
                        "fact_kind": "closed_result_frame.validated",
                        "observation_only": True,
                        "command": False,
                        "payload": {
                            "sql_ref": "sql:tool",
                            "frame_ref": "frame:0264",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_passive_supervisor_closed_result_frame_observation_0266.py",
            "--observation-report",
            str(observation),
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

    assert "passive_supervisor_closed_result_frame_observation_valid=True" in result.stdout
    assert "accepted=1" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["passive_supervisor_observation_only"] is True
    assert payload["publishes_events"] is False
