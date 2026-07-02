from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_phase7_closure_report_cli import main  # noqa: E402


def test_phase7_closure_report_cli_writes_report(tmp_path: Path, capsys) -> None:
    output = tmp_path / "closure.json"

    exit_code = main(["--root", str(ROOT), "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source candidate phase 7 closure report" in captured.out
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == (
        "missipy.source_candidate.phase7_closure_report.v1"
    )


def test_phase7_closure_report_cli_prints_json(tmp_path: Path, capsys) -> None:
    output = tmp_path / "closure.json"

    exit_code = main(["--root", str(ROOT), "--output", str(output), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.phase7_closure_report.v1"
    assert payload["phase"] == "7"
