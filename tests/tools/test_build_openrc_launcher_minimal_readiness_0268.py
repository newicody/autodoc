import json
import subprocess
import sys
from pathlib import Path

from context.openrc_launcher_minimal_readiness_0268 import (
    EVENTBUS_OBSERVATION_SCHEMA,
    PASSIVE_SUPERVISOR_SCHEMA,
)


ROOT = Path(__file__).resolve().parents[2]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_0268_tool_builds_readiness_report_and_script(tmp_path: Path) -> None:
    closed = tmp_path / "closed.json"
    eventbus = tmp_path / "eventbus.json"
    passive = tmp_path / "passive.json"
    handoff = tmp_path / "handoff.json"
    sqlite_database = tmp_path / "scheduler.sqlite3"
    output = tmp_path / "readiness.json"
    script = tmp_path / "autodoc-local-runtime.openrc"

    _write_json(
        closed,
        {
            "valid": True,
            "sql_ref": "sql:inference_context:tool",
            "embedding_ref": "embedding:passage:tool",
            "hydrated_count": 1,
            "missing_count": 0,
            "executes_runtime": False,
        },
    )
    _write_json(
        eventbus,
        {
            "schema": EVENTBUS_OBSERVATION_SCHEMA,
            "valid": True,
            "frame_ref": "closed-result-frame:tool",
            "fact_count": 3,
            "published_count": 3,
            "observed_count": 3,
            "eventbus_observation_only": True,
            "events_are_facts_not_commands": True,
            "executes_runtime": False,
        },
    )
    _write_json(
        passive,
        {
            "schema": PASSIVE_SUPERVISOR_SCHEMA,
            "valid": True,
            "source_observation_ref": "eventbus-observation:tool",
            "fact_count": 3,
            "accepted_fact_count": 3,
            "rejected_fact_count": 0,
            "runtime_violation_count": 0,
            "passive_supervisor_observation_only": True,
            "executes_runtime": False,
        },
    )
    _write_json(
        handoff,
        {
            "valid": True,
            "handoff_ref": "github-scan-once-handoff:tool",
            "scan_once": True,
            "remote_mutation_allowed": False,
            "request": {"repository": "newicody/autodoc"},
        },
    )
    sqlite_database.write_bytes(b"SQLite format 3\x00phase-0260")

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_openrc_launcher_minimal_readiness_0268.py",
            "--closed-frame-report",
            str(closed),
            "--eventbus-observation",
            str(eventbus),
            "--passive-supervisor-observation",
            str(passive),
            "--github-handoff",
            str(handoff),
            "--sqlite-database",
            str(sqlite_database),
            "--output",
            str(output),
            "--script-output",
            str(script),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "openrc_launcher_minimal_readiness_valid=True" in result.stdout
    assert "reports=4/4" in result.stdout
    assert "sqlite_present=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.openrc_launcher_minimal_readiness.v1"
    assert payload["readiness_only"] is True
    assert payload["ready_report_count"] == 4
    assert payload["sqlite_database_summary"]["opened"] is False
    assert payload["sqlite_database_summary"]["written"] is False
    assert payload["uses_subprocess"] is False
    assert payload["calls_rc_service"] is False
    assert script.read_text(encoding="utf-8").startswith("#!/sbin/openrc-run")


def test_0268_tool_reports_missing_artifacts_without_starting_services(
    tmp_path: Path,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_openrc_launcher_minimal_readiness_0268.py",
            "--closed-frame-report",
            str(tmp_path / "0264.json"),
            "--eventbus-observation",
            str(tmp_path / "0265.json"),
            "--passive-supervisor-observation",
            str(tmp_path / "0266.json"),
            "--github-handoff",
            str(tmp_path / "0267.json"),
            "--sqlite-database",
            str(tmp_path / "0260.sqlite3"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["valid"] is False
    assert payload["ready_report_count"] == 0
    assert payload["starts_postgresql"] is False
    assert payload["starts_qdrant"] is False
    assert payload["starts_openvino"] is False
