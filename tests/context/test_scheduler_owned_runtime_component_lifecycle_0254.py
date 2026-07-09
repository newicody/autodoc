from context.scheduler_owned_runtime_component_lifecycle_0254 import (
    build_scheduler_owned_runtime_lifecycle,
    validate_scheduler_owned_lifecycle,
)


def test_scheduler_owns_runtime_components() -> None:
    lifecycle = build_scheduler_owned_runtime_lifecycle()
    payload = lifecycle.to_dict()

    assert payload["bootstrap_path"] == ["OpenRC", "launcher", "Scheduler"]
    assert payload["authority"]["scheduler_owns_runtime_components"] is True
    assert payload["authority"]["launcher_bootstrap_only"] is True
    assert payload["authority"]["no_cli_per_component_runtime_api"] is True
    assert payload["execution_phase_opened"] is True


def test_scheduler_lifecycle_includes_sql_openvino_qdrant() -> None:
    lifecycle = build_scheduler_owned_runtime_lifecycle()
    components = {component.component_id: component for component in lifecycle.components}

    assert "sql_context_store" in components
    assert "openvino_embedding_service" in components
    assert "qdrant_projection_store" in components
    assert "qdrant.recall" in components["qdrant_projection_store"].capabilities
    assert components["qdrant_projection_store"].depends_on == (
        "sql_context_store",
        "openvino_embedding_service",
    )


def test_scheduler_lifecycle_validation_passes() -> None:
    lifecycle = build_scheduler_owned_runtime_lifecycle()

    assert validate_scheduler_owned_lifecycle(lifecycle) == ()
