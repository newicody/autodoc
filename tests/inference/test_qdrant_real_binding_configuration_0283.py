from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
)
from inference.qdrant_real_binding_configuration_0283 import (
    QdrantRealBindingConfigurationCommand,
    QdrantRealBindingConfigurationPolicy,
    build_qdrant_real_binding_configuration,
)
from inference.qdrant_sql_authority_scope import (
    QdrantSqlAuthorityScope,
    QdrantStrictGrpcTransportPolicy,
)


def _command(
    *,
    operations=(),
    allow_write=False,
    allow_search=False,
    url="http://127.0.0.1:6333",
    rest_url="http://127.0.0.1:6333",
    prefer_grpc=True,
    strict_data_grpc=True,
    grpc_port=6334,
    collection_name="autodoc_context_embeddings",
    dimension=384,
    api_key_env_var="",
):
    return QdrantRealBindingConfigurationCommand(
        connection=QdrantClientConnectionConfig(
            url=url,
            timeout_seconds=10.0,
            prefer_grpc=prefer_grpc,
            grpc_port=grpc_port,
            wait_for_write=True,
            check_compatibility=True,
        ),
        effect_gate=QdrantClientEffectGate(
            policy_decision_id="policy:0283:r2",
            allow_write=allow_write,
            allow_search=allow_search,
        ),
        sql_authority_scope=QdrantSqlAuthorityScope(
            authority_ref="sql-authority:sqlite:fixture",
            store_kind="sqlite",
            namespace="autodoc-local",
        ),
        transport_policy=QdrantStrictGrpcTransportPolicy(
            rest_admin_url=rest_url,
            grpc_port=grpc_port,
            prefer_grpc=prefer_grpc,
            strict_data_grpc=strict_data_grpc,
        ),
        target=QdrantProjectionTarget(
            collection_name=collection_name,
            vector_dimension=dimension,
        ),
        projection_policy=QdrantProjectionPolicy(),
        requested_operations=operations,
        api_key_env_var=api_key_env_var,
        recall_oversample_factor=4,
    )


def test_preview_configuration_is_valid_and_effect_free() -> None:
    result = build_qdrant_real_binding_configuration(
        _command()
    )

    assert result.valid is True
    assert result.requested_operations == ()
    assert result.binding_ref.startswith("qdrant-real-binding:")
    assert result.remote_endpoint is False
    payload = result.to_json_dict()
    assert payload["api_key"] == {
        "source": "none",
        "env_var": "",
        "secret_value_serialized": False,
    }
    assert payload["boundaries"] == {
        "configuration_only": True,
        "existing_executor_reused": True,
        "existing_sql_scope_reused": True,
        "shared_collection_policy": True,
        "secret_value_serialized": False,
        "dependency_inspection_performed": False,
        "client_constructed": False,
        "external_call_performed": False,
        "qdrant_write_performed": False,
        "qdrant_search_performed": False,
        "sql_write_performed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


@pytest.mark.parametrize(
    ("operations", "allow_write", "allow_search"),
    (
        (("projection",), True, False),
        (("recall",), False, True),
        (("projection", "recall"), True, True),
    ),
)
def test_requested_operations_match_existing_effect_gate(
    operations,
    allow_write,
    allow_search,
) -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            operations=operations,
            allow_write=allow_write,
            allow_search=allow_search,
        )
    )
    assert result.valid is True
    assert result.requested_operations == tuple(sorted(operations))


def test_effect_gate_mismatch_is_rejected() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            operations=("projection",),
            allow_write=False,
        )
    )
    assert result.valid is False
    assert (
        "effect gate allow_write must exactly match projection"
        in result.issues
    )


def test_connection_and_transport_origins_must_match() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(rest_url="http://localhost:6333")
    )
    assert result.valid is False
    assert (
        "connection URL and REST administration URL must match"
        in result.issues
    )


def test_inline_credentials_are_rejected() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            url="http://user:secret@127.0.0.1:6333",
            rest_url="http://user:secret@127.0.0.1:6333",
        )
    )
    assert result.valid is False
    assert (
        "connection URL must not contain inline credentials"
        in result.issues
    )


def test_strict_grpc_is_required_by_default() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            prefer_grpc=False,
            strict_data_grpc=False,
        )
    )
    assert result.valid is False
    assert "strict data gRPC is required" in result.issues


def test_remote_endpoint_is_rejected_by_default() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            url="https://qdrant.example.test:6333",
            rest_url="https://qdrant.example.test:6333",
            api_key_env_var="QDRANT_API_KEY",
        )
    )
    assert result.valid is False
    assert "Qdrant endpoint must be loopback" in result.issues


def test_remote_endpoint_can_be_allowed_with_env_secret() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            url="https://qdrant.example.test:6333",
            rest_url="https://qdrant.example.test:6333",
            api_key_env_var="QDRANT_API_KEY",
        ),
        QdrantRealBindingConfigurationPolicy(
            require_loopback=False,
        ),
    )
    assert result.valid is True
    assert result.remote_endpoint is True
    assert result.to_json_dict()["api_key"]["source"] == (
        "environment"
    )


def test_remote_endpoint_requires_env_secret_name() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(
            url="https://qdrant.example.test:6333",
            rest_url="https://qdrant.example.test:6333",
        ),
        QdrantRealBindingConfigurationPolicy(
            require_loopback=False,
        ),
    )
    assert result.valid is False
    assert (
        "remote Qdrant endpoint requires api_key_env_var"
        in result.issues
    )


def test_collection_and_dimension_are_shared_policy_boundaries() -> None:
    wrong_collection = build_qdrant_real_binding_configuration(
        _command(collection_name="specialist_alpha")
    )
    wrong_dimension = build_qdrant_real_binding_configuration(
        _command(dimension=1024)
    )

    assert wrong_collection.valid is False
    assert any(
        "shared-collection policy" in issue
        for issue in wrong_collection.issues
    )
    assert wrong_dimension.valid is False
    assert (
        "target vector dimension is not allowed"
        in wrong_dimension.issues
    )


def test_operation_order_is_normalized_for_digest_replay() -> None:
    first = build_qdrant_real_binding_configuration(
        _command(
            operations=("recall", "projection"),
            allow_write=True,
            allow_search=True,
        )
    )
    second = build_qdrant_real_binding_configuration(
        _command(
            operations=("projection", "recall"),
            allow_write=True,
            allow_search=True,
        )
    )

    assert first == second
    assert first.binding_digest == second.binding_digest


def test_api_key_env_name_is_validated_without_reading_secret() -> None:
    result = build_qdrant_real_binding_configuration(
        _command(api_key_env_var="qdrant-api-key")
    )
    assert result.valid is False
    assert any(
        "uppercase environment name" in issue
        for issue in result.issues
    )


def test_contracts_are_frozen() -> None:
    command = _command()
    policy = QdrantRealBindingConfigurationPolicy()
    result = build_qdrant_real_binding_configuration(command)

    with pytest.raises(FrozenInstanceError):
        command.api_key_env_var = "X"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        policy.require_loopback = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.valid = False  # type: ignore[misc]
