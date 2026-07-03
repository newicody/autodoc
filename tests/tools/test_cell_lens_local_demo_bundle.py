from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "cell_lens_local_demo_bundle.py"


def test_cell_lens_local_demo_bundle_cli_writes_demo_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo"

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--output-dir",
            str(output_dir),
            "--population-size",
            "8",
            "--tick-count",
            "8",
            "--seed",
            "3",
            "--sse-limit",
            "5",
        ],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )

    result = json.loads(completed.stdout)
    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))

    assert result["schema"] == "missipy.cell_lens_local_demo_bundle.v1"
    assert result["ok"] is True
    assert report["ok"] is True
    assert (output_dir / "cells.jsonl").exists()
    assert (output_dir / "cells.sse").exists()
    assert "missipy.cell.v1" in (output_dir / "cells.jsonl").read_text(encoding="utf-8")
    assert "missipy.cell_snapshot_sse.v1" in (output_dir / "cells.sse").read_text(encoding="utf-8")
