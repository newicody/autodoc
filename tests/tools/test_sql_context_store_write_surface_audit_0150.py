from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from context.sql_context_store_write_surface_contract import (
    build_sql_context_store_write_surface_record,
    inspect_sql_context_store_write_surface,
)


def _write_fake_persistence_record(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "persistence_ref": "sql-context-persist:demo",
                "handoff_ref": "sql-handoff:demo",
                "sql_ref": "sql:artifact/vector-indexing/demo",
                "artifact_ref": "artifact:local/demo",
            }
        ),
        encoding="utf-8",
    )


def _load_tool_module():
    path = Path("tools/run_sql_context_store_write_surface_audit.py")
    spec = importlib.util.spec_from_file_location("run_sql_context_store_write_surface_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0150_inspects_existing_sql_context_store_write_method(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context" / "sql_context_store.py"
    store.parent.mkdir(parents=True)
    store.write_text(
        "class SQLContextStore:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "    def upsert_context(self, record):\n"
        "        return record\n",
        encoding="utf-8",
    )

    audit = inspect_sql_context_store_write_surface(tmp_path)

    assert audit.exists is True
    assert audit.has_sql_context_store_class is True
    assert audit.selected_write_method == "upsert_context"
    assert audit.write_status == "ready_for_controlled_write_patch"
    assert audit.ready_for_controlled_write_patch is True


def test_0150_detects_dbapi_sql_context_store_upsert_record(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context" / "sql_context_store.py"
    store.parent.mkdir(parents=True)
    store.write_text(
        "class SqlContextRecord:\n"
        "    pass\n"
        "class DbApiSqlContextStore:\n"
        "    def initialize_schema(self):\n"
        "        pass\n"
        "    def upsert_record(self, record):\n"
        "        return record\n",
        encoding="utf-8",
    )

    audit = inspect_sql_context_store_write_surface(tmp_path)

    assert audit.exists is True
    assert audit.has_sql_context_store_class is True
    assert audit.selected_write_method == "upsert_record"
    assert audit.write_status == "ready_for_controlled_write_patch"
    assert audit.payload["selected_sql_context_store_class"] == "DbApiSqlContextStore"


def test_0150_reports_gap_when_no_explicit_write_method(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context" / "sql_context_store.py"
    store.parent.mkdir(parents=True)
    store.write_text("class SQLContextStore:\n    def connect(self):\n        pass\n", encoding="utf-8")

    audit = inspect_sql_context_store_write_surface(tmp_path)

    assert audit.selected_write_method is None
    assert audit.write_status == "blocked_no_explicit_sql_context_store_write_method"
    assert audit.ready_for_controlled_write_patch is False


def test_0150_builds_write_surface_record_without_write_attempt(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context" / "sql_context_store.py"
    store.parent.mkdir(parents=True)
    store.write_text("class SQLContextStore:\n    def save_context(self, record):\n        return record\n", encoding="utf-8")
    persistence_record = {
        "persistence_ref": "sql-context-persist:demo",
        "handoff_ref": "sql-handoff:demo",
        "sql_ref": "sql:artifact/vector-indexing/demo",
        "artifact_ref": "artifact:local/demo",
    }

    audit = inspect_sql_context_store_write_surface(tmp_path)
    record = build_sql_context_store_write_surface_record(
        persistence_record=persistence_record,
        surface_audit=audit,
    ).to_mapping()

    assert record["audit_ref"].startswith("sql-context-write-surface:")
    assert record["durable_authority"] == "sql"
    assert record["qdrant_role"] == "projection_recall_index"
    assert record["write_attempted"] is False
    assert record["selected_write_method"] == "save_context"


def test_0150_tool_writes_audit_artifacts(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context" / "sql_context_store.py"
    store.parent.mkdir(parents=True)
    store.write_text("class SQLContextStore:\n    def store_context(self, record):\n        return record\n", encoding="utf-8")
    (tmp_path / "src" / "context" / "sql_context_store_write_surface_contract.py").write_text("# test surface\n", encoding="utf-8")
    persistence_json = tmp_path / ".var" / "smoke" / "artifacts" / "0149" / "sql_context_store_persistence_record.json"
    _write_fake_persistence_record(persistence_json)
    module = _load_tool_module()

    plan = module.build_sql_context_store_write_surface_audit_plan(
        tmp_path,
        persistence_json=persistence_json,
        output_dir=Path(".var/smoke/artifacts/0150"),
        requested_write_method=None,
        execute=True,
    )
    rc = module.execute_sql_context_store_write_surface_audit_plan(plan)

    assert rc == 0
    assert plan.audit_json.exists()
    assert plan.audit_report.exists()
    written = json.loads(plan.audit_json.read_text(encoding="utf-8"))
    assert written["selected_write_method"] == "store_context"
    assert written["write_attempted"] is False
