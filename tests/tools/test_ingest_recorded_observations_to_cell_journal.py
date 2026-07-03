from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.cell_observation_event import CellObservationEvent


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ingest_recorded_observations_to_cell_journal.py"


def test_ingest_recorded_observations_cli_outputs_json_result(tmp_path: Path) -> None:
    source = tmp_path / "observations.jsonl"
    journal = tmp_path / "cells.jsonl"
    state = tmp_path / "state.json"
    event = CellObservationEvent(
        event_id="event-1",
        event_type="task.completed",
        source_task_id="task-1",
        source_class="scheduler.short_task",
        score=1.0,
        age=1.0,
        cost=0.5,
        observed_at="2026-07-03T10:00:00Z",
    )
    source.write_text(event.to_json_line(), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--source",
            str(source),
            "--journal",
            str(journal),
            "--state",
            str(state),
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["schema"] == "missipy.cell_recorded_observation_ingest.v1"
    assert result["ok"] is True
    assert result["written_count"] == 1
    assert journal.exists()
    assert state.exists()
