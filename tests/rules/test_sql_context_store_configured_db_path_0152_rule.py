from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_sql_context_store_controlled_write_smoke.py"
RULE = ROOT / "doc" / "code-rules" / "0152_sql_context_store_configured_db_path_rule.md"
DOC = ROOT / "doc" / "architecture" / "SQL_CONTEXT_STORE_CONFIGURED_DB_PATH_0152.md"


def test_0152_files_exist() -> None:
    for path in (TOOL, RULE, DOC):
        assert path.exists(), path


def test_0152_tool_exposes_configured_db_path_without_new_store() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "AUTODOC_SQL_CONTEXT_DB" in text
    assert ".var/local/sql_context_store.sqlite3" in text
    assert "resolve_configured_sql_context_db_path" in text
    assert "DbApiSqlContextStore(connection)" in text
    assert "store.upsert_record(record)" in text
    assert "db_path_source" in text


def test_0152_boundary_forbids_parallel_sql_runtime() -> None:
    combined = TOOL.read_text(encoding="utf-8") + "\n" + RULE.read_text(encoding="utf-8")
    forbidden = [
        "SQLPersistenceWorker(",
        "SQLOrchestrator(",
        "LocalArtifactOrchestrator(",
        "LocalVectorIndexingOrchestrator(",
        "qdrant_client",
        "openvino.runtime",
        "Scheduler.run(",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_0152_rule_locks_stable_db_path_precedence() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "--db-path" in text
    assert "AUTODOC_SQL_CONTEXT_DB" in text
    assert ".var/local/sql_context_store.sqlite3" in text
    assert "DbApiSqlContextStore.upsert_record" in text
    assert "SQL remains durable authority" in text
    assert "Qdrant remains projection/recall only" in text
