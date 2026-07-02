from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "generate_synthetic_cell_journal.py"


def test_generate_synthetic_cell_journal_cli_writes_jsonl(tmp_path: Path) -> None:
    output = tmp_path / "cells.jsonl"

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--output",
            str(output),
            "--population-size",
            "4",
            "--tick-count",
            "4",
            "--seed",
            "11",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout.replace("'", '"'))
    lines = output.read_text(encoding="utf-8").splitlines()

    assert result["written_count"] == len(lines)
    assert lines
    assert json.loads(lines[0])["schema"] == "missipy.cell.v1"
