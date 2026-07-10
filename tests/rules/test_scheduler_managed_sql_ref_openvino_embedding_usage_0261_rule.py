from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0261_source_locks_openvino_embedding_boundary() -> None:
    source = (ROOT / "src/context/scheduler_managed_sql_ref_openvino_embedding_usage_0261.py").read_text(
        encoding="utf-8"
    )

    assert "Scheduler uses the existing OpenVINO/E5 pipeline surface" in source
    assert "Scheduler does not start OpenVINO" in source
    assert "Qdrant is not involved in 0261" in source
    assert "run_scheduler_managed_sql_ref_openvino_embedding_usage" in source
    assert "build_multilingual_e5_small_pipeline" in source
    assert '"calls_qdrant": self.calls_qdrant' in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0261_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_SQL_REF_OPENVINO_EMBEDDING_USAGE_0261.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed sql_ref to OpenVINO embedding usage" in doc
    assert "sql_ref -> SQL rehydrate -> OpenVINO/E5 passage embedding" in doc
    assert "Scheduler does not start OpenVINO" in doc
    assert "Qdrant is not involved in 0261" in doc
    assert "0262 can project the embedding toward Qdrant" in doc
