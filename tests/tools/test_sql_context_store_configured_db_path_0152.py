from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from tools.run_sql_context_store_controlled_write_smoke import (
    build_sql_context_store_controlled_write_plan,
    resolve_configured_sql_context_db_path,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_sql_context_store_controlled_write_smoke.py"


def _persistence_mapping() -> dict[str, object]:
    return {
        "persistence_ref": "sql-context-persist:configured-db-demo",
        "handoff_ref": "sql-handoff:configured-db-demo",
        "sql_ref": "sql:artifact/vector-indexing/configured-db-test",
        "artifact_ref": "artifact:local/0152/configured-db-demo",
        "artifact_kind": "local_markdown",
        "artifact_path": ".var/smoke/artifacts/0152/artifact_input.md",
        "artifact_contract_path": ".var/smoke/artifacts/0152/artifact_intake_contract.json",
        "artifact_report": ".var/smoke/artifacts/0152/artifact_vector_indexing_report.md",
        "artifact_json": ".var/smoke/artifacts/0152/artifact_vector_indexing_report.json",
        "result_frame_path": ".var/smoke/routeproxy-0152/routes/frames/result.json",
        "point_id": "qdrant-point:configureddb123",
        "qdrant_rest_id": "11111111-1111-1111-1111-111111111111",
        "vector_json": ".var/smoke/e5_vector_0152.json",
        "collection": "autodoc_smoke_e5_384",
        "dimension": 384,
        "status": "ok",
        "machine_vector_handoff": True,
        "strict_vector_handoff": True,
        "persistence_mode": "sql_context_store_record",
        "durable_authority": "sql",
        "qdrant_role": "projection_recall_index",
    }


def test_resolve_configured_db_path_precedence(tmp_path: Path) -> None:
    root = tmp_path
    explicit, explicit_source = resolve_configured_sql_context_db_path(root, "explicit.sqlite3", environ={})
    env_path, env_source = resolve_configured_sql_context_db_path(root, None, environ={"AUTODOC_SQL_CONTEXT_DB": "env.sqlite3"})
    default_path, default_source = resolve_configured_sql_context_db_path(root, None, environ={})

    assert explicit == (root / "explicit.sqlite3").resolve()
    assert explicit_source == "explicit"
    assert env_path == (root / "env.sqlite3").resolve()
    assert env_source == "env:AUTODOC_SQL_CONTEXT_DB"
    assert default_path == (root / ".var/local/sql_context_store.sqlite3").resolve()
    assert default_source == "default:.var/local/sql_context_store.sqlite3"


def test_controlled_write_plan_uses_stable_default_db_path(tmp_path: Path) -> None:
    persistence = tmp_path / "persistence.json"
    persistence.write_text(json.dumps(_persistence_mapping()), encoding="utf-8")

    plan = build_sql_context_store_controlled_write_plan(
        ROOT,
        persistence_json=persistence,
        output_dir=tmp_path / "out",
    )

    assert plan.db_path == (ROOT / ".var/local/sql_context_store.sqlite3").resolve()
    assert plan.db_path_source == "default:.var/local/sql_context_store.sqlite3"
    assert plan.output_dir == (tmp_path / "out").resolve()


def test_controlled_write_tool_uses_env_db_path(tmp_path: Path) -> None:
    persistence = tmp_path / "persistence.json"
    persistence.write_text(json.dumps(_persistence_mapping()), encoding="utf-8")
    output_dir = tmp_path / "out"
    env_db = tmp_path / "configured" / "sql_context_store.sqlite3"

    env = {"AUTODOC_SQL_CONTEXT_DB": str(env_db), "PYTHONPATH": f"{ROOT / 'src'}:{ROOT}"}
    dry = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--persistence-json",
            str(persistence),
            "--output-dir",
            str(output_dir),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=env,
    )
    assert dry.returncode == 0, dry.stdout
    assert f"db_path: `{env_db}`" in dry.stdout
    assert "db_path_source: `env:AUTODOC_SQL_CONTEXT_DB`" in dry.stdout

    live = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--persistence-json",
            str(persistence),
            "--output-dir",
            str(output_dir),
            "--execute",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=env,
    )
    assert live.returncode == 0, live.stdout
    assert env_db.exists()
    result = json.loads((output_dir / "sql_context_store_controlled_write_result.json").read_text(encoding="utf-8"))
    assert result["write_status"] == "persisted"
    assert result["readback_ok"] is True
    with sqlite3.connect(env_db) as connection:
        row = connection.execute(
            "SELECT context_ref FROM sql_context_records WHERE context_ref = ?",
            ("sql:artifact/vector-indexing/configured-db-test",),
        ).fetchone()
    assert row == ("sql:artifact/vector-indexing/configured-db-test",)
