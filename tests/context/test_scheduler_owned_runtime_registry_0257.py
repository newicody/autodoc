from context.scheduler_owned_runtime_registry_0257 import (
    build_scheduler_owned_runtime_registry,
    validate_scheduler_owned_runtime_registry,
)


SOURCE_MAP = {
    "complete": True,
    "selections": [
        {
            "surface": "scheduler",
            "primary_paths": ["src/contracts/scheduler.py", "src/kernel/scheduler.py"],
            "hits": [],
        },
        {
            "surface": "eventbus",
            "primary_paths": ["src/kernel/event_bus.py"],
            "hits": [],
        },
        {
            "surface": "passive_supervisor",
            "primary_paths": ["src/context/passive_bus_supervisor_cellular_snapshot.py"],
            "hits": [],
        },
        {
            "surface": "sql_context_store",
            "primary_paths": ["tools/run_sql_context_store_controlled_write_smoke.py"],
            "hits": [],
        },
        {
            "surface": "openvino_embedding",
            "primary_paths": ["tools/run_openvino_e5_live_smoke.py"],
            "hits": [],
        },
        {
            "surface": "qdrant_projection",
            "primary_paths": [
                "tools/run_qdrant_projection_live_smoke.py",
                "tools/run_qdrant_live_recall_sql_rehydrate_smoke.py",
            ],
            "hits": [],
        },
        {
            "surface": "github_artifact_exchange",
            "primary_paths": [
                "src/context/github_artifact_scheduler_intake.py",
                "src/context/github_project_push_frame.py",
            ],
            "hits": [],
        },
    ],
}


def test_registry_is_scheduler_owned_and_valid() -> None:
    registry = build_scheduler_owned_runtime_registry(SOURCE_MAP)
    payload = registry.to_dict()

    assert payload["valid"] is True
    assert payload["owner"] == "scheduler"
    assert payload["launcher_bootstrap_only"] is True
    assert payload["eventbus_observation_only"] is True
    assert payload["no_cli_per_component"] is True
    assert payload["creates_runtime_manager"] is False
    assert payload["instantiates_components"] is False


def test_registry_reuses_existing_surfaces_for_core_components() -> None:
    registry = build_scheduler_owned_runtime_registry(SOURCE_MAP)
    registrations = {item.component_id: item for item in registry.registrations}

    assert "src/kernel/event_bus.py" in registrations["eventbus"].source_paths
    assert "sql.context.write" in registrations["sql_context_store"].capabilities
    assert "embedding.openvino.passage" in registrations["openvino_embedding_service"].capabilities
    assert registrations["qdrant_projection_store"].depends_on == (
        "sql_context_store",
        "openvino_embedding_service",
    )
    assert registrations["passive_supervisor_sink"].depends_on == ("eventbus",)


def test_registry_validation_passes() -> None:
    registry = build_scheduler_owned_runtime_registry(SOURCE_MAP)

    assert validate_scheduler_owned_runtime_registry(registry) == ()
