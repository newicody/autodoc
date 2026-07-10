import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"


def test_cli_plan_mode_writes_atomic_serialisable_report(tmp_path: Path) -> None:
    output = tmp_path / "reports/production_prototype_smoke_composition_0269.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--repo-root",
            str(tmp_path),
            "--bootstrap-report",
            str(tmp_path / "bootstrap.json"),
            "--db-path",
            str(tmp_path / "store.sqlite3"),
            "--reports-dir",
            str(tmp_path / "reports"),
            "--openrc-script-output",
            str(tmp_path / "autodoc-local-runtime.openrc"),
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "production_prototype_smoke_composition_valid=True" in completed.stdout
    assert "execute=False" in completed.stdout
    assert payload["schema"] == "autodoc.production_prototype_smoke_composition.v1"
    assert payload["planned_step_count"] == 9
    assert payload["executed_step_count"] == 0
    assert payload["valid"] is True




def test_cli_execute_composes_nine_existing_tools_with_explicit_demo_gates(
    tmp_path: Path, monkeypatch
) -> None:
    import importlib.util
    from types import SimpleNamespace

    spec = importlib.util.spec_from_file_location("production_prototype_cli_0269", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    repo = tmp_path / "repo"
    reports_dir = repo / ".var/reports"
    database = repo / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
    bootstrap = reports_dir / "scheduler_runtime_bootstrap_registry_attachment_0258.json"
    openrc_script = reports_dir / "autodoc-local-runtime.openrc"
    output = reports_dir / "production_prototype_smoke_composition_0269.json"
    reports_dir.mkdir(parents=True)
    bootstrap.write_text('{"valid": true}\n', encoding="utf-8")

    invoked_tools: list[str] = []

    def fake_run(argv, **_kwargs):
        values = list(argv)
        tool_name = Path(values[1]).name
        invoked_tools.append(tool_name)

        def option(name: str) -> str | None:
            try:
                return values[values.index(name) + 1]
            except (ValueError, IndexError):
                return None

        payload: dict[str, object] = {"valid": True, "tool": tool_name}
        if "0260" in tool_name:
            payload["sql_ref"] = "sql:inference_context:test"
            db_path = option("--db-path")
            assert db_path is not None
            db = Path(db_path)
            db.parent.mkdir(parents=True, exist_ok=True)
            db.write_bytes(b"SQLite format 3\\x00test")
        if "0261" in tool_name:
            payload["embedding_ref"] = "embedding:passage:test"
        if "0265" in tool_name:
            payload["eventbus_observation_only"] = True
            payload["events_are_facts_not_commands"] = True
            payload["starts_postgresql"] = False
            payload["starts_openvino"] = False
            payload["starts_qdrant"] = False
        if "0266" in tool_name:
            payload["passive_supervisor_observation_only"] = True
        if "0267" in tool_name:
            payload["handoff_ref"] = "github-scan-once-handoff:test"
            payload["remote_mutation_allowed"] = False
        if "0268" in tool_name:
            payload["readiness_ref"] = "openrc-launcher-readiness:test"
            payload["sqlite_database_present"] = True
            payload["readiness_only"] = True
            payload["scheduler_starts_external_services"] = False
            payload["calls_rc_service"] = False
            payload["starts_postgresql"] = False
            payload["starts_openvino"] = False
            payload["starts_qdrant"] = False

        report_path = option("--output")
        assert report_path is not None
        report = Path(report_path)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        script_path = option("--script-output")
        if script_path is not None:
            script = Path(script_path)
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text("#!/sbin/openrc-run\n", encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(TOOL),
            "--repo-root",
            str(repo),
            "--bootstrap-report",
            str(bootstrap),
            "--db-path",
            str(database),
            "--reports-dir",
            str(reports_dir),
            "--openrc-script-output",
            str(openrc_script),
            "--execute",
            "--policy-decision-id",
            "policy:test:0269",
            "--demo-embedding",
            "--demo-eventbus",
            "--demo-qdrant",
            "--output",
            str(output),
            "--format",
            "summary",
        ],
    )

    assert module.main() == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert invoked_tools == [
        "bind_scheduler_managed_db_api_sql_context_store_0260.py",
        "run_scheduler_managed_sql_ref_openvino_embedding_0261.py",
        "run_scheduler_managed_embedding_qdrant_projection_0262.py",
        "run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
        "compose_scheduler_managed_closed_result_frame_0264.py",
        "build_closed_result_frame_eventbus_observation_0265.py",
        "build_passive_supervisor_closed_result_frame_observation_0266.py",
        "build_github_scan_once_handoff_0267.py",
        "build_openrc_launcher_minimal_readiness_0268.py",
    ]
    assert payload["valid"] is True
    assert payload["executed_step_count"] == 9
    assert payload["valid_step_count"] == 9
    assert payload["references"] == {
        "embedding_ref": "embedding:passage:test",
        "handoff_ref": "github-scan-once-handoff:test",
        "readiness_ref": "openrc-launcher-readiness:test",
        "sql_ref": "sql:inference_context:test",
    }
    assert payload["checks"]["remote_mutation_allowed"] is False
    assert payload["boundaries"]["scheduler_starts_external_services"] is False
    assert database.is_file()
    assert openrc_script.is_file()
