from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src" / "context" / "sql_context_store_persistence_contract.py"
TOOL = ROOT / "tools" / "run_sql_context_store_persistence_smoke.py"
RULE = ROOT / "doc" / "code-rules" / "0149_sql_context_store_persistence_smoke_rule.md"
DOC = ROOT / "doc" / "architecture" / "SQL_CONTEXT_STORE_PERSISTENCE_SMOKE_0149.md"


def test_0149_files_exist() -> None:
    for path in (CONTRACT, TOOL, RULE, DOC):
        assert path.exists(), path


def test_0149_contract_locks_sql_context_store_record_boundary() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "SqlContextStorePersistenceRecord",
        "SqlContextStoreSurface",
        "inspect_sql_context_store_surface",
        "build_sql_context_store_persistence_record",
        "projection_recall_index",
        "sql_context_store_record",
    ]
    for phrase in required:
        assert phrase in text


def test_0149_tool_reuses_sql_context_store_and_avoids_parallel_workers() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "SQLContextStore persistence smoke",
        "sql_context_store_persistence_record.json",
        "src/context/sql_context_store.py",
        "Qdrant identifiers stay projection metadata; SQL remains durable authority",
        "record_only",
    ]
    forbidden = [
        "SQLPersistenceWorker(",
        "SQLOrchestrator(",
        "LocalArtifactOrchestrator(",
        "LocalVectorIndexingOrchestrator(",
        "qdrant_client",
        "openvino.runtime",
        "Scheduler.run(",
        "psycopg",
        "sqlite3.connect",
    ]
    for phrase in required:
        assert phrase in text
    for phrase in forbidden:
        assert phrase not in text


def test_0149_rule_mentions_existing_authority_surface() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "SQLContextStore remains durable authority" in text
    assert "must not create SQLPersistenceWorker" in text
    assert "must not use backend-specific SQL client calls" in text
