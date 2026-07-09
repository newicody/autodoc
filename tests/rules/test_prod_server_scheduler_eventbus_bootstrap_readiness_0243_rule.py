from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0243_readiness_does_not_create_runtime() -> None:
    source = (
        ROOT / "src/context/prod_server_scheduler_eventbus_bootstrap_readiness_0243.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    assert "readiness_only" in source
    assert "imports_factory_modules" in source
    assert "calls_factories" in source
    assert "creates_scheduler" in source
    assert "creates_eventbus" in source
    assert "starts_threads" in source
    assert "calls_github_api" in source
    assert "writes_postgresql" in source
    assert "writes_qdrant" in source
    assert "importlib" not in lowered
    assert "subprocess.run" not in source
    assert "threading." not in lowered
    assert "scheduler.run(" not in lowered
    assert "requests." not in lowered
    assert "qdrant.upsert" not in lowered


def test_0243_docs_lock_bootstrap_readiness_boundary() -> None:
    doc = (
        ROOT / "doc/architecture/PROD_SERVER_SCHEDULER_EVENTBUS_BOOTSTRAP_READINESS_0243.md"
    ).read_text(encoding="utf-8")

    assert "Scheduler/EventBus bootstrap readiness" in doc
    assert "No factory is imported or called" in doc
    assert "Scheduler is command path" in doc
    assert "EventBus is observation path" in doc
    assert "0244" in doc
