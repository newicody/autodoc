from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0257_registry_reuses_surfaces_without_runtime_manager() -> None:
    source = (ROOT / "src/context/scheduler_owned_runtime_registry_0257.py").read_text(
        encoding="utf-8"
    )

    assert "Scheduler remains the owner of runtime components" in source
    assert "selected_from_existing_surfaces" in source
    assert "no_cli_per_component" in source
    assert "creates_runtime_manager" in source
    assert "instantiates_components" in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source
    assert ".upsert(" not in source
    assert "requests." not in source


def test_0257_docs_lock_registry_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_OWNED_RUNTIME_REGISTRY_0257.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-owned runtime registry" in doc
    assert "reuse source map from 0256" in doc
    assert "Scheduler owns runtime components" in doc
    assert "no CLI per component" in doc
    assert "no RuntimeManager" in doc
    assert "0258 will attach this registry to Scheduler bootstrap" in doc
