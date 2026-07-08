from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0238_visual_pipeline_is_read_only_composition() -> None:
    source = (ROOT / "src/context/passive_supervisor_visual_pipeline_0238.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "read_only_visual_pipeline" in source
    assert "uses_scheduler_run" in source
    assert "writes_sql" in source
    assert "writes_qdrant" in source
    assert "subprocess.run" in source
    assert "import vispy" not in lowered
    assert "scheduler.run(" not in lowered
    assert "qdrant.upsert" not in lowered


def test_0238_docs_lock_pipeline_chain() -> None:
    doc = (ROOT / "doc/architecture/PASSIVE_SUPERVISOR_VISUAL_PIPELINE_SMOKE_0238.md").read_text(
        encoding="utf-8"
    )

    assert "0234 -> 0236 -> 0237" in doc
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in doc
    assert "No renderer is introduced by this patch" in doc
