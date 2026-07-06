from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from context.sql_context_store import DbApiSqlContextStore
from context.sql_context_store_controlled_write_contract import (
    SqlContextStoreControlledWriteSummary,
    build_sql_context_record_from_persistence_mapping,
)
ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_sql_context_store_controlled_write_smoke.py"


def _persistence_mapping() -> dict[str, object]:
    return {
        "persistence_ref": "sql-context-persist:demo",
        "handoff_ref": "sql-handoff:demo",
        "sql_ref": "sql:artifact/vector-indexing/test",
        "artifact_ref": "artifact:local/test/demo",
        "artifact_kind": "local_markdown",
        "artifact_path": ".var/smoke/artifacts/test/artifact_input.md",
        "artifact_contract_path": ".var/smoke/artifacts/test/artifact_intake_contract.json",
        "artifact_report": ".var/smoke/artifacts/test/artifact_vector_indexing_report.md",
        "artifact_json": ".var/smoke/artifacts/test/artifact_vector_indexing_report.json",
        "result_frame_path": ".var/smoke/routeproxy-test/routes/frames/result.json",
        "point_id": "qdrant-point:abc123",
        "qdrant_rest_id": "00000000-0000-0000-0000-000000000000",
        "vector_json": ".var/smoke/e5_vector_test.json",
        "collection": "autodoc_smoke_e5_384",
        "dimension": 384,
        "status": "ok",
        "machine_vector_handoff": True,
        "strict_vector_handoff": True,
        "persistence_mode": "sql_context_store_record",
        "durable_authority": "sql",
        "qdrant_role": "projection_recall_index",
    }


def test_build_sql_context_record_from_persistence_mapping() -> None:
    record = build_sql_context_record_from_persistence_mapping(_persistence_mapping())

    assert record.context_ref == "sql:artifact/vector-indexing/test"
    assert record.kind == "artifact"
    assert record.parent_ref == "artifact:local/test/demo"
    assert "qdrant-point:abc123" in record.body
    metadata = dict(record.metadata)
    assert metadata["qdrant_role"] == "projection_recall_index"
    assert metadata["point_id"] == "qdrant-point:abc123"


def test_dbapi_sql_context_store_upsert_record_roundtrip() -> None:
    record = build_sql_context_record_from_persistence_mapping(_persistence_mapping())
    connection = sqlite3.connect(":memory:")
    try:
        store = DbApiSqlContextStore(connection)
        store.initialize_schema()
        result = store.upsert_record(record)
        readback = store.get_record(record.context_ref)
    finally:
        connection.close()

    assert result.inserted is True
    assert result.replaced is False
    assert readback is not None
    assert readback.context_ref == record.context_ref


def test_controlled_write_summary_mapping() -> None:
    record = build_sql_context_record_from_persistence_mapping(_persistence_mapping())
    connection = sqlite3.connect(":memory:")
    try:
        store = DbApiSqlContextStore(connection)
        store.initialize_schema()
        result = store.upsert_record(record)
    finally:
        connection.close()

    summary = SqlContextStoreControlledWriteSummary.from_write_result(
        persistence_mapping=_persistence_mapping(),
        write_result=result,
        db_path=":memory:",
        readback_ok=True,
    )
    mapping = summary.to_mapping()

    assert mapping["write_status"] == "persisted"
    assert mapping["selected_store_class"] == "DbApiSqlContextStore"
    assert mapping["selected_write_method"] == "upsert_record"
    assert mapping["durable_authority"] == "sql"
    assert mapping["qdrant_role"] == "projection_recall_index"


def test_controlled_write_tool_execute(tmp_path: Path) -> None:
    persistence = tmp_path / "persistence.json"
    persistence.write_text(json.dumps(_persistence_mapping()), encoding="utf-8")
    output_dir = tmp_path / "out"
    db_path = output_dir / "store.sqlite3"

    dry = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--persistence-json",
            str(persistence),
            "--output-dir",
            str(output_dir),
            "--db-path",
            str(db_path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert dry.returncode == 0, dry.stdout
    assert "ready_for_sql_context_store_controlled_write: `true`" in dry.stdout

    live = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--persistence-json",
            str(persistence),
            "--output-dir",
            str(output_dir),
            "--db-path",
            str(db_path),
            "--execute",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert live.returncode == 0, live.stdout
    result = json.loads((output_dir / "sql_context_store_controlled_write_result.json").read_text(encoding="utf-8"))
    assert result["write_status"] == "persisted"
    assert result["readback_ok"] is True
    assert result["sql_ref"] == "sql:artifact/vector-indexing/test"
    assert db_path.exists()
