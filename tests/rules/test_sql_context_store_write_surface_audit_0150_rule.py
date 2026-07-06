from __future__ import annotations

from pathlib import Path

CONTRACT = Path("src/context/sql_context_store_write_surface_contract.py")
TOOL = Path("tools/run_sql_context_store_write_surface_audit.py")
DOC = Path("doc/code-rules/0150_sql_context_store_write_surface_audit_rule.md")


def test_0150_files_exist() -> None:
    assert CONTRACT.exists()
    assert TOOL.exists()
    assert DOC.exists()


def test_0150_contract_contains_required_boundary_strings() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "SqlContextStoreWriteSurfaceAudit",
        "SqlContextStoreWriteSurfaceRecord",
        "inspect_sql_context_store_write_surface",
        "ready_for_controlled_write_patch",
        "blocked_no_explicit_sql_context_store_write_method",
        "Qdrant must remain projection/recall only",
    ]
    for phrase in required:
        assert phrase in text


def test_0150_tool_contains_required_boundary_strings() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "sql_context_store_persistence_record.json",
        "src/context/sql_context_store.py",
        "src/context/sql_context_store_write_surface_contract.py",
        "write_attempted",
        "selected_write_method",
        "ready_for_controlled_write_patch",
        "does not modify the Scheduler run loop",
    ]
    for phrase in required:
        assert phrase in text


def test_0150_forbidden_parallel_or_backend_strings_absent() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [CONTRACT, TOOL, DOC]
    )
    forbidden = [
        "SQLPersistenceWorker(",
        "SQLOrchestrator(",
        "LocalArtifactOrchestrator(",
        "LocalVectorIndexingOrchestrator(",
        "SchedulerOpenVINORunner(",
        "VectorOpenVINOEmbeddingAdapter(",
        "VectorQdrantProjectionAdapter(",
        "Scheduler.run(",
        "qdrant_client",
        "openvino.runtime",
        "psycopg.connect",
        "sqlalchemy.create_engine",
    ]
    for phrase in forbidden:
        assert phrase not in combined
