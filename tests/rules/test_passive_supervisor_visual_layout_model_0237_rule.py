from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0237_visual_layout_model_has_no_renderer_dependency() -> None:
    source = (ROOT / "src/context/passive_supervisor_visual_layout_model.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "read_only_visual_layout" in source
    assert "uses_scheduler_run" in source
    assert "writes_sql" in source
    assert "writes_qdrant" in source
    assert "import vispy" not in lowered
    assert "scheduler.run(" not in lowered
    assert "qdrant.upsert" not in lowered
    assert "github" in lowered


def test_0237_docs_lock_layout_boundary() -> None:
    doc = (ROOT / "doc/architecture/PASSIVE_SUPERVISOR_VISUAL_LAYOUT_MODEL_0237.md").read_text(
        encoding="utf-8"
    )

    assert "snapshot/read-model -> visual layout model" in doc
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in doc
    assert "No renderer is introduced by this patch" in doc
