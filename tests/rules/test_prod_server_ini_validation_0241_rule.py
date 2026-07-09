from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0241_validation_is_read_only_and_stdlib_only() -> None:
    source = (ROOT / "src/context/prod_server_ini_validation_0241.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "validation_only" in source
    assert "configobj_compatible_layout" in source
    assert "imports_configobj" in source
    assert "calls_github_api" in source
    assert "publishes_github" in source
    assert "writes_postgresql" in source
    assert "writes_qdrant" in source
    assert "import configparser" in source
    assert "import configobj" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert "qdrant.upsert" not in lowered
    assert "create table" not in lowered


def test_0241_example_locks_github_and_qdrant_requirements() -> None:
    example = (ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini").read_text(
        encoding="utf-8"
    )

    assert "token_env = GITHUB_TOKEN" in example
    assert "mode = artifact_exchange" in example
    assert "publish_enabled_by_default = false" in example
    assert "publication_review_required = true" in example
    assert "required_payload = sql_ref" in example
    assert "vector_dimension = 384" in example


def test_0241_docs_state_initial_server_validation() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_INI_VALIDATION_0241.md").read_text(
        encoding="utf-8"
    )

    assert "production server INI validation" in doc
    assert "ConfigObj-compatible" in doc
    assert "No runtime service is started" in doc
    assert "GitHub remains artifact exchange" in doc
