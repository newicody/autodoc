from __future__ import annotations

from pathlib import Path
import subprocess
import sys

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import CellSnapshotJournalWriter


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "cell_snapshot_sse_dry_run.py"


def test_cell_snapshot_sse_dry_run_cli_writes_sse_file(tmp_path: Path) -> None:
    journal = tmp_path / "cells.jsonl"
    output = tmp_path / "cells.sse"
    snapshot = CellSnapshot(
        cell_id="cell-1",
        source_class="scheduler.short_task",
        score=1.0,
        age=1.0,
        cost=0.5,
        lifecycle_state="completed",
        observed_at="2026-07-03T10:00:00Z",
    )
    CellSnapshotJournalWriter(journal).append(snapshot)

    subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--journal",
            str(journal),
            "--output",
            str(output),
            "--start-sequence",
            "5",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )

    text = output.read_text(encoding="utf-8")
    assert text.startswith("id: 5\nevent: cell_snapshot\ndata: ")
    assert "missipy.cell_snapshot_sse.v1" in text
    assert "missipy.cell.v1" in text
