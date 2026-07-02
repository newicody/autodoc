from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from source_candidate_phase7_handoff_contract_cli import main  # noqa: E402


def _write_closure(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.phase7_closure_report.v1",
                "root": "/tmp/repo",
                "phase": "7",
                "status": "closed",
                "artifact_count": 1,
                "missing_count": 0,
                "local_only": True,
                "remote_mutation_enabled": False,
                "scheduler_modified": False,
                "network_enabled": False,
                "next_phase": "8",
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_phase7_handoff_contract_cli_writes_contract(tmp_path: Path, capsys) -> None:
    closure = tmp_path / "closure.json"
    output = tmp_path / "handoff.json"
    _write_closure(closure)

    exit_code = main(["--closure-report", str(closure), "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "source candidate phase 7 handoff contract" in captured.out
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "frozen"


def test_phase7_handoff_contract_cli_prints_json(tmp_path: Path, capsys) -> None:
    output = tmp_path / "handoff.json"

    exit_code = main(["--output", str(output), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.phase7_handoff_contract.v1"
    assert payload["phase"] == "7"
