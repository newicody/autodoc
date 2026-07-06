from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src" / "context" / "sql_context_store_controlled_write_contract.py"
TOOL = ROOT / "tools" / "run_sql_context_store_controlled_write_smoke.py"
RULE = ROOT / "doc" / "code-rules" / "0151_sql_context_store_controlled_write_rule.md"
DOC = ROOT / "doc" / "architecture" / "SQL_CONTEXT_STORE_CONTROLLED_WRITE_0151.md"


def test_0151_files_exist() -> None:
    for path in (CONTRACT, TOOL, RULE, DOC):
        assert path.exists(), path


def test_0151_uses_existing_dbapi_sql_context_store_surface() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    assert "DbApiSqlContextStore" in contract
    assert "SqlContextRecord" in contract
    assert "upsert_record" in contract
    assert "DbApiSqlContextStore(connection)" in tool
    assert "store.upsert_record(record)" in tool
    assert "store.get_record(record.context_ref)" in tool


def test_0151_boundary_forbids_parallel_sql_runtime() -> None:
    combined = CONTRACT.read_text(encoding="utf-8") + "\n" + TOOL.read_text(encoding="utf-8")
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


def test_0151_rule_doc_locks_sql_authority_and_qdrant_projection() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "DbApiSqlContextStore.upsert_record" in text
    assert "SQL remains durable authority" in text
    assert "Qdrant remains projection/recall only" in text
    assert "must not create SQLPersistenceWorker" in text
    assert "must not create SQLOrchestrator" in text
