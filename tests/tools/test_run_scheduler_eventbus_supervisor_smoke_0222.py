import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_run_scheduler_eventbus_supervisor_smoke_writes_snapshot(tmp_path: Path) -> None:
    output = tmp_path / "snapshot.json"
    audit = tmp_path / "audit" / "events.jsonl"

    result = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_eventbus_supervisor_smoke_0222.py",
            "--event-id",
            "evt-scheduler-1",
            "--event-kind",
            "scheduler_handler_completed",
            "--scheduler-ref",
            "main",
            "--handler-ref",
            "route-handler",
            "--state",
            "success",
            "--observed-at",
            "2026-07-08T00:00:00Z",
            "--generated-at",
            "2026-07-08T00:00:01Z",
            "--route-ref",
            "route-1",
            "--policy-decision-id",
            "policy-1",
            "--payload",
            "cycle=1",
            "--output",
            str(output),
            "--audit-jsonl",
            str(audit),
            "--format",
            "json",
        ],
        check=True,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    payload = json.loads(result.stdout)
    saved = json.loads(output.read_text(encoding="utf-8"))
    audit_text = audit.read_text(encoding="utf-8")

    assert payload["scheduler_eventbus_source_smoke"] is True
    assert payload["cellular_snapshot_written"] is True
    assert payload["audit_journal_enabled"] is True
    assert payload["accepted_event"]["cell_kind"] == "SCHEDULER"
    assert payload["accepted_event"]["cell_id"] == "scheduler:main"
    assert payload["accepted_event"]["payload"]["handler_ref"] == "route-handler"
    assert payload["accepted_event"]["payload"]["cycle"] == "1"
    assert saved["cells"][0]["refs"]["route_ref"] == "route-1"
    assert saved["cells"][0]["refs"]["policy_decision_id"] == "policy-1"
    assert "scheduler_handler_completed" in audit_text
