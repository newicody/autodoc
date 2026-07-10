from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0262_source_locks_qdrant_projection_boundary() -> None:
    source = (ROOT / "src/context/scheduler_managed_embedding_qdrant_projection_usage_0262.py").read_text(
        encoding="utf-8"
    )

    assert "Scheduler uses Qdrant; Scheduler does not start Qdrant" in source
    assert "SQL remains the durable authority" in source
    assert "build_qdrant_projection_batch" in source
    assert "payload.sql_ref alias" in source
    assert "OpenVINO is not executed in 0262" in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0262_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_EMBEDDING_QDRANT_PROJECTION_USAGE_0262.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed embedding to Qdrant projection usage" in doc
    assert "embedding -> Qdrant projection with payload.sql_ref" in doc
    assert "Scheduler does not start Qdrant" in doc
    assert "SQL remains the durable authority" in doc
    assert "0263 can recall from Qdrant and rehydrate from SQL" in doc
