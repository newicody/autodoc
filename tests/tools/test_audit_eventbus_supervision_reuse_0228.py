from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.audit_eventbus_supervision_reuse_0228 import build_report


def test_audit_detects_existing_surfaces_without_runtime_imports(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "event_bus.py").write_text(
        "class EventBus:\n"
        "    def publish(self, event):\n"
        "        pass\n"
        "    def subscribe(self, sink):\n"
        "        pass\n",
        encoding="utf-8",
    )
    (src / "scheduler.py").write_text(
        "class Scheduler:\n"
        "    def run(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    (src / "passive_bus_supervisor_cellular_snapshot.py").write_text(
        "class CellularState: pass\n"
        "def build_cellular_snapshot(events):\n"
        "    return {}\n",
        encoding="utf-8",
    )

    report = build_report(tmp_path, ("src",))

    assert report["read_only"] is True
    assert report["runtime_side_effects"] is False
    assert report["scheduler_run_called"] is False
    summary = report["surface_summary"]
    assert summary["eventbus"]["found"] is True
    assert summary["scheduler"]["found"] is True
    assert summary["passive_supervisor"]["found"] is True
    assert "reuse_or_extend_existing_eventbus_surface_before_adding_any_bus" in report["reuse_recommendations"]
    assert "extend_existing_passive_supervisor_cellular_state_instead_of_parallel_bridge" in report["reuse_recommendations"]


def test_audit_cli_writes_json_report(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    src = root / "src"
    src.mkdir(parents=True)
    output = tmp_path / "report.json"
    (src / "bus.py").write_text("class EventBus: pass\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/audit_eventbus_supervision_reuse_0228.py",
            "--root",
            str(root),
            "--scan-dir",
            "src",
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
    )

    assert "eventbus: found=True" in result.stdout
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["phase"] == "0228"
    assert data["authority_boundary"]["allows_scheduler_run"] is False
    assert data["functional_resumption_gate"]["reuse_decision_required_before_runtime_patch"] is True
