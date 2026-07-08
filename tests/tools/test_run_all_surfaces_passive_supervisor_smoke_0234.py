from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_run_all_surfaces_passive_supervisor_smoke_writes_snapshot_and_audit(
    tmp_path: Path,
) -> None:
    output = tmp_path / "all_surfaces.json"
    audit = tmp_path / "audit" / "events.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_all_surfaces_passive_supervisor_smoke_0234.py",
            "--output",
            str(output),
            "--audit-jsonl",
            str(audit),
            "--observed-at",
            "2026-07-08T00:00:00Z",
            "--generated-at",
            "2026-07-08T00:00:01Z",
            "--format",
            "summary",
        ],
        check=True,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert "all_surfaces_passive_supervisor_smoke_passed=True" in result.stdout
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["all_surfaces_passive_supervisor_smoke_passed"] is True
    assert report["missing_cell_kinds"] == []
    assert set(report["expected_cell_kinds"]) == set(report["observed_cell_kinds"])
    assert report["event_count"] == 11
    assert report["authority_boundary"]["uses_scheduler_run"] is False
    assert report["authority_boundary"]["creates_eventbus"] is False
    assert report["authority_boundary"]["writes_sql"] is False
    assert report["authority_boundary"]["writes_qdrant"] is False
    assert audit.read_text(encoding="utf-8").count("\n") == 11
