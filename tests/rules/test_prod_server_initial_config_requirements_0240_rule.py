from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0240_initial_configuration_does_not_start_or_mutate_runtime() -> None:
    source = (ROOT / "src/context/prod_server_initial_config_requirements_0240.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "requirements_only" in source
    assert "calls_github_api" in source
    assert "publishes_github" in source
    assert "writes_postgresql" in source
    assert "writes_qdrant" in source
    assert "subprocess.run" not in source
    assert "scheduler.run(" not in lowered
    assert "qdrant.upsert" not in lowered
    assert "create table" not in lowered
    assert "requests." not in lowered


def test_0240_docs_lock_production_server_wording_and_github_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_INITIAL_CONFIG_REQUIREMENTS_0240.md").read_text(
        encoding="utf-8"
    )

    assert "initial production server configuration" in doc
    assert "OpenRC -> launcher -> Scheduler" in doc
    assert "GitHub is an artifact exchange surface" in doc
    assert "Copilot output is advisory only" in doc
    assert "publication review is required" in doc
