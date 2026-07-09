from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0258_bootstrap_attachment_keeps_scheduler_ownership() -> None:
    source = (ROOT / "src/context/scheduler_runtime_bootstrap_registry_attachment_0258.py").read_text(
        encoding="utf-8"
    )

    assert "OpenRC -> launcher -> Scheduler -> runtime registry -> runtime components" in source
    assert "Scheduler owns the registry attachment" in source
    assert "launcher remains bootstrap-only" in source
    assert "EventBus" in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source
    assert ".upsert(" not in source
    assert "requests." not in source


def test_0258_docs_lock_bootstrap_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_RUNTIME_BOOTSTRAP_REGISTRY_ATTACHMENT_0258.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler runtime bootstrap registry attachment" in doc
    assert "Scheduler owns the registry attachment" in doc
    assert "launcher remains bootstrap-only" in doc
    assert "no RuntimeManager" in doc
    assert "does not modify Scheduler.run" in doc
    assert "0259 can start adapting real SQL execution through Scheduler" in doc
