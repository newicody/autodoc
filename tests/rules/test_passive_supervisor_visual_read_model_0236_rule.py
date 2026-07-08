from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0236_visual_read_model_is_read_only_and_no_vispy_dependency() -> None:
    source = (ROOT / "src/context/passive_supervisor_visual_read_model.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "read_only_visual_model" in source
    assert "uses_scheduler_run" in source
    assert "writes_sql" in source
    assert "writes_qdrant" in source
    assert "import vispy" not in lowered
    assert "scheduler.run(" not in lowered
    assert "upsert" not in lowered
    assert "mutate_github" not in lowered


def test_0236_docs_lock_visual_read_model_boundary() -> None:
    doc = (ROOT / "doc/architecture/PASSIVE_SUPERVISOR_VISUAL_READ_MODEL_0236.md").read_text(
        encoding="utf-8"
    )

    assert "VisPy is not introduced by this patch" in doc
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in doc
    assert "snapshot -> visual read-model" in doc
