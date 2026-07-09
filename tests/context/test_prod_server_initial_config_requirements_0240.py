from pathlib import Path

from context.prod_server_initial_config_requirements_0240 import (
    INITIAL_CONFIGURATION_BOUNDARY,
    configuration_to_dict,
    production_server_initial_configuration,
    validate_production_server_initial_configuration,
    write_production_server_initial_configuration,
)


def test_initial_configuration_is_requirements_only() -> None:
    assert INITIAL_CONFIGURATION_BOUNDARY["requirements_only"] is True
    assert INITIAL_CONFIGURATION_BOUNDARY["single_production_server_target"] is True
    assert INITIAL_CONFIGURATION_BOUNDARY["starts_openrc"] is False
    assert INITIAL_CONFIGURATION_BOUNDARY["writes_postgresql"] is False
    assert INITIAL_CONFIGURATION_BOUNDARY["writes_qdrant"] is False
    assert INITIAL_CONFIGURATION_BOUNDARY["calls_github_api"] is False
    assert INITIAL_CONFIGURATION_BOUNDARY["publishes_github"] is False


def test_initial_configuration_has_core_ini_sections() -> None:
    payload = configuration_to_dict()

    assert payload["version"] == "0240.r2"
    assert payload["target"] == "production_server"
    assert "server" in payload["ini_sections"]
    assert "component.scheduler" in payload["ini_sections"]
    assert "postgresql.table.context_records" in payload["ini_sections"]
    assert "qdrant.collection.autodoc_context_e5_small" in payload["ini_sections"]
    assert "github.repositories" in payload["ini_sections"]
    assert "eventbus.attributes" in payload["ini_sections"]


def test_initial_configuration_validates() -> None:
    assert validate_production_server_initial_configuration() == []


def test_scheduler_eventbus_and_github_boundaries() -> None:
    config = production_server_initial_configuration()
    components = {entry.component_id: entry for entry in config.component_requirements}

    assert components["scheduler"].command_path is True
    assert components["eventbus"].observation_path is True
    assert components["github_artifact_exchange"].command_path is True
    assert "scheduler" in components["github_artifact_exchange"].depends_on
    assert "sql_context_store" in components["github_artifact_exchange"].depends_on


def test_github_integration_is_artifact_exchange_only_by_default() -> None:
    github = production_server_initial_configuration().github_integration

    assert github.mode == "artifact_exchange"
    assert github.token_env == "GITHUB_TOKEN"
    assert github.repository_allowlist_required is True
    assert github.copilot_advisory_only is True
    assert github.publication_review_required is True
    assert github.publish_enabled_by_default is False
    assert github.sql_write_during_scan is False
    assert github.qdrant_write_during_scan is False


def test_event_attributes_include_github_refs_and_redaction() -> None:
    config = production_server_initial_configuration()
    attributes = {entry.name: entry for entry in config.event_attribute_requirements}

    assert attributes["schema_version"].required is True
    assert attributes["github_ref"].redact is False
    assert attributes["project_push_frame_ref"].redact is False
    assert attributes["secret"].redact is True


def test_qdrant_requirement_requires_sql_ref() -> None:
    collection = production_server_initial_configuration().qdrant_collection_requirements[0]

    assert collection.vector_dimension == 384
    assert collection.distance == "cosine"
    assert collection.normalized_vectors is True
    assert "sql_ref" in collection.required_payload


def test_write_initial_configuration(tmp_path: Path) -> None:
    output = tmp_path / "initial_configuration.json"
    payload = write_production_server_initial_configuration(output)

    assert payload["production_server_initial_configuration_written"] is True
    assert output.exists()
