from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0263_source_locks_recall_rehydrate_boundary() -> None:
    source = (ROOT / "src/context/scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py").read_text(
        encoding="utf-8"
    )

    assert "Qdrant is recall only and carries refs" in source
    assert "SQL remains the durable authority" in source
    assert "Scheduler does not start Qdrant" in source
    assert "unique_sql_context_refs_from_recall" in source
    assert "rehydrate_sql_refs" in source
    assert "OpenVINO is not executed in 0263" in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0263_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_QDRANT_RECALL_SQL_REHYDRATE_USAGE_0263.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed Qdrant recall to SQL rehydrate usage" in doc
    assert "Qdrant recall -> sql_ref -> SQL rehydrate" in doc
    assert "Qdrant is recall only and carries refs" in doc
    assert "SQL remains the durable authority" in doc
    assert "0264 can compose the closed ResultFrame" in doc
