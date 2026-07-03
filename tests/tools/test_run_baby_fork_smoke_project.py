from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_baby_fork_smoke_project.py"


def test_run_baby_fork_smoke_project_cli_outputs_report(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--output-dir", str(tmp_path)],
        cwd=ROOT,
        env={"PYTHONPATH": "src:."},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["schema"] == "missipy.baby_fork_smoke_project.v1"
    assert payload["ok"] is True
    assert payload["retrieval"]["retrieved_ids"] == ["baby-silicone-fork", "rounded-stainless-soft-handle"]
    assert payload["patch"]["selected_variant"] == "variant-1"
    assert Path(payload["journal_path"]).exists()
