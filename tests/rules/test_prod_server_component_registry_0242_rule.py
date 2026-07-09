from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0242_registry_does_not_instantiate_or_start_runtime() -> None:
    source = (ROOT / "src/context/prod_server_component_registry_0242.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "registry_only" in source
    assert "imports_factory_modules" in source
    assert "calls_factories" in source
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


def test_0242_docs_lock_registry_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_COMPONENT_REGISTRY_0242.md").read_text(
        encoding="utf-8"
    )

    assert "declarative component registry" in doc
    assert "No component factory is imported or called" in doc
    assert "No __init__ side effects" in doc
    assert "0243" in doc
