from context.scheduler_runtime_bootstrap_registry_attachment_0258 import (
    attach_scheduler_owned_runtime_registry,
    build_scheduler_runtime_bootstrap_attachment,
    scheduler_has_runtime_registry_attachment,
    validate_scheduler_runtime_bootstrap_attachment,
)


REGISTRY_PAYLOAD = {
    "scheduler_owned_runtime_registry": True,
    "valid": True,
    "issues": [],
    "owner": "scheduler",
    "source_map_complete": True,
    "launcher_bootstrap_only": True,
    "eventbus_observation_only": True,
    "no_cli_per_component": True,
    "creates_runtime_manager": False,
    "instantiates_components": False,
    "registrations": [
        {
            "component_id": "eventbus",
            "capabilities": ["eventbus.publish_fact", "eventbus.subscribe_fact"],
            "depends_on": [],
        },
        {
            "component_id": "passive_supervisor_sink",
            "capabilities": ["supervisor.observe", "supervisor.visual_read_model"],
            "depends_on": ["eventbus"],
        },
        {
            "component_id": "sql_context_store",
            "capabilities": ["sql.context.write", "sql.context.rehydrate"],
            "depends_on": [],
        },
        {
            "component_id": "openvino_embedding_service",
            "capabilities": ["embedding.openvino.passage", "embedding.openvino.query"],
            "depends_on": [],
        },
        {
            "component_id": "qdrant_projection_store",
            "capabilities": ["qdrant.collection.ensure", "qdrant.projection.upsert", "qdrant.recall"],
            "depends_on": ["sql_context_store", "openvino_embedding_service"],
        },
        {
            "component_id": "github_artifact_exchange",
            "capabilities": ["github.artifact.scan_once", "github.project_push_frame.build"],
            "depends_on": [],
        },
    ],
}


class FakeScheduler:
    pass


def test_bootstrap_attachment_plan_is_valid_and_dry_run() -> None:
    result = build_scheduler_runtime_bootstrap_attachment(REGISTRY_PAYLOAD)

    assert result.valid is True
    assert result.dry_run is True
    assert result.attached_to_scheduler_object is False
    assert result.attachment.owner == "scheduler"
    assert result.attachment.instantiates_components is False
    assert result.attachment.starts_components is False
    assert result.attachment.creates_runtime_manager is False
    assert result.attachment.capability_index["sql.context.write"] == "sql_context_store"
    assert result.attachment.capability_index["qdrant.recall"] == "qdrant_projection_store"


def test_attach_registry_to_existing_scheduler_object_without_runtime_manager() -> None:
    scheduler = FakeScheduler()

    result = attach_scheduler_owned_runtime_registry(scheduler, REGISTRY_PAYLOAD)

    assert result.valid is True
    assert result.dry_run is False
    assert result.attached_to_scheduler_object is True
    assert scheduler_has_runtime_registry_attachment(scheduler) is True


def test_validate_rejects_missing_runtime_component() -> None:
    invalid = dict(REGISTRY_PAYLOAD)
    invalid["registrations"] = REGISTRY_PAYLOAD["registrations"][:-1]

    issues = validate_scheduler_runtime_bootstrap_attachment(invalid)

    assert "missing registry component github_artifact_exchange" in issues
