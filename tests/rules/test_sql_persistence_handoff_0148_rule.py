from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src" / "context" / "sql_persistence_handoff_contract.py"
TOOL = ROOT / "tools" / "run_sql_persistence_handoff_smoke.py"
RULE = ROOT / "doc" / "code-rules" / "0148_sql_persistence_handoff_rule.md"
DOC = ROOT / "doc" / "architecture" / "SQL_PERSISTENCE_HANDOFF_0148.md"


def test_0148_files_exist() -> None:
    for path in (CONTRACT, TOOL, RULE, DOC):
        assert path.exists(), path


def test_0148_contract_locks_sql_authority_and_qdrant_projection() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "SqlPersistenceHandoffContract",
        "durable_authority",
        "projection_recall_index",
        "handoff_only",
        "build_sql_persistence_handoff_contract",
    ]
    for phrase in required:
        assert phrase in text


def test_0148_tool_is_handoff_only_and_has_no_backend_imports() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "handoff-only",
        "sql_persistence_handoff.json",
        "sql_persistence_handoff_report.md",
        "does not write to SQL in 0148",
        "Qdrant remains projection/recall only; SQL remains durable authority",
    ]
    forbidden = [
        "SQLPersistenceWorker(",
        "SQLOrchestrator(",
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


def test_0148_rule_mentions_existing_sql_context_store_without_importing_it() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "SQLContextStore remains durable authority" in text
    assert "0148 is handoff-only" in text
    assert "must not create SQLPersistenceWorker" in text
