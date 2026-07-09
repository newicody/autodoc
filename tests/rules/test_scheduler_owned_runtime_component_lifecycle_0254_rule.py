from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0254_scheduler_ownership_rule_in_source() -> None:
    source = (ROOT / "src/context/scheduler_owned_runtime_component_lifecycle_0254.py").read_text(
        encoding="utf-8"
    )

    assert "scheduler_owns_runtime_components" in source
    assert "launcher_bootstrap_only" in source
    assert "no_cli_per_component_runtime_api" in source
    assert "eventbus_observation_only" in source
    assert "openvino_embedding_service" in source
    assert "qdrant_projection_store" in source
    assert "subprocess.run" not in source
    assert "Scheduler.run(" not in source
    assert ".upsert(" not in source


def test_0254_docs_lock_scheduler_owned_runtime_boundary() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_OWNED_RUNTIME_COMPONENT_LIFECYCLE_0254.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler owns runtime components" in doc
    assert "OpenRC -> launcher -> Scheduler" in doc
    assert "no CLI per component" in doc
    assert "execution phase is opened" in doc
    assert "EventBus remains observation-only" in doc
