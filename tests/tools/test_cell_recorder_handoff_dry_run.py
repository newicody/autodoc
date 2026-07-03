from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.cell_observation_event import CellObservationEvent


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "cell_recorder_handoff_dry_run.py"


def test_cell_recorder_handoff_dry_run_cli_outputs_json_result(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "cells.jsonl"
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
    input_path.write_text(event.to_json_line(), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(TOOL), "--input", str(input_path), "--output", str(output_path)],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    assert result["schema"] == "missipy.cell_recorder_handoff_dry_run.v1"
    assert result["ok"] is True
    assert result["event_count"] == 1
    assert output_path.exists()
