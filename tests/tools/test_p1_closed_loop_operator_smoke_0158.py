from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_p1_closed_loop_operator_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_p1_closed_loop_operator_smoke", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0158_plan_composes_existing_p1_tools_without_new_backend(tmp_path: Path) -> None:
    module = _load_module()

    plan = module.build_p1_closed_loop_plan(
        ROOT,
        output_dir=tmp_path / "artifacts",
        route_root=tmp_path / "routes",
        model_dir=Path("/tmp/model"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0158",
        handoff_ref="sql-handoff:sql-persistence/0158",
        db_path=tmp_path / "sql_context_store.sqlite3",
        text="P1 composition test",
        text_kind="passage",
        artifact_ref="artifact:local/0158/test",
        vector_indexing_job_ref="vector-indexing-job:artifact/0158-test",
        execute=False,
    )

    assert plan.ready
    roles = [command.role for command in plan.commands]
    assert roles == [
        "0145_local_artifact_vector_indexing",
        "0148_sql_persistence_handoff",
        "0149_sql_context_store_persistence_record",
        "0150_sql_context_store_write_surface_audit",
        "0151_0152_sql_context_store_controlled_write",
    ]

    preview = "\n".join(command.shell_preview() for command in plan.commands)
    assert "tools/run_local_artifact_vector_indexing_runner.py" in preview
    assert "tools/run_sql_persistence_handoff_smoke.py" in preview
    assert "tools/run_sql_context_store_persistence_smoke.py" in preview
    assert "tools/run_sql_context_store_write_surface_audit.py" in preview
    assert "tools/run_sql_context_store_controlled_write_smoke.py" in preview
    assert "--handoff-ref sql-handoff:sql-persistence/0158" in preview
    assert "--db-path" in preview

    mapping = plan.to_mapping()
    assert mapping["ready_for_p1_closed_loop_operator"] is True
    assert "does not create SQLPersistenceWorker" in mapping["boundary"]
    assert "does not create VectorQdrantProjectionAdapter" in mapping["boundary"]


def test_0158_result_summary_reads_existing_output_files(tmp_path: Path) -> None:
    module = _load_module()
    output_dir = tmp_path / "artifacts"
    output_dir.mkdir()

    (output_dir / "artifact_vector_indexing_report.json").write_text(
        json.dumps(
            {
                "sql_ref": "sql:artifact/vector-indexing/0158",
                "point_id": "qdrant-point:test",
                "qdrant_rest_id": "rest-test",
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "sql_persistence_handoff.json").write_text(
        json.dumps(
            {
                "handoff_ref": "sql-handoff:sql-persistence/0158",
                "sql_ref": "sql:artifact/vector-indexing/0158",
                "artifact_ref": "artifact:local/0158/test",
                "point_id": "qdrant-point:test",
                "qdrant_rest_id": "rest-test",
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "sql_context_store_persistence_record.json").write_text(
        json.dumps(
            {
                "persistence_ref": "sql-context-persist:test",
                "handoff_ref": "sql-handoff:sql-persistence/0158",
                "sql_ref": "sql:artifact/vector-indexing/0158",
                "artifact_ref": "artifact:local/0158/test",
                "point_id": "qdrant-point:test",
                "qdrant_rest_id": "rest-test",
            }
        ),
        encoding="utf-8",
    )
    (output_dir / "sql_context_store_controlled_write_result.json").write_text(
        json.dumps(
            {
                "sql_ref": "sql:artifact/vector-indexing/0158",
                "artifact_ref": "artifact:local/0158/test",
                "point_id": "qdrant-point:test",
                "qdrant_rest_id": "rest-test",
                "write_status": "persisted",
                "readback_ok": True,
                "selected_store_class": "DbApiSqlContextStore",
                "selected_write_method": "upsert_record",
                "db_path": str(tmp_path / "sql.sqlite3"),
            }
        ),
        encoding="utf-8",
    )

    plan = module.build_p1_closed_loop_plan(
        ROOT,
        output_dir=output_dir,
        route_root=tmp_path / "routes",
        model_dir=Path("/tmp/model"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0158",
        handoff_ref="sql-handoff:sql-persistence/0158",
        db_path=tmp_path / "sql.sqlite3",
        text="P1 composition test",
        text_kind="passage",
        artifact_ref="artifact:local/0158/test",
        vector_indexing_job_ref="vector-indexing-job:artifact/0158-test",
        execute=False,
    )

    result = module.build_p1_closed_loop_result(plan)
    assert result.status == "ok"
    assert result.write_status == "persisted"
    assert result.readback_ok is True
    assert result.selected_store_class == "DbApiSqlContextStore"
    assert result.selected_write_method == "upsert_record"


def test_0158_cli_json_dry_run_is_machine_readable(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--output-dir",
            str(tmp_path / "artifacts"),
            "--route-root",
            str(tmp_path / "routes"),
            "--db-path",
            str(tmp_path / "sql.sqlite3"),
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["ready_for_p1_closed_loop_operator"] is True
    assert payload["sql_ref"] == "sql:artifact/vector-indexing/0158"
    assert payload["handoff_ref"].startswith("sql-handoff:")
    assert payload["commands"]["0148_sql_persistence_handoff"]
