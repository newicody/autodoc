"""Immutable real-Qdrant binding configuration for phase 0283-r2.

The contract composes existing connection, effect-gate, SQL-authority,
transport, target and projection-policy objects. It performs no dependency
inspection, client construction, secret lookup, network call, Qdrant effect,
SQL write, scheduling or service administration.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import ipaddress
import json
import re
from typing import Any
from urllib.parse import urlparse

from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
)
from inference.qdrant_sql_authority_scope import (
    QdrantSqlAuthorityScope,
    QdrantStrictGrpcTransportPolicy,
)


REAL_BINDING_CONFIGURATION_SCHEMA = (
    "missipy.qdrant.real_binding_configuration.v1"
)
REAL_BINDING_CONFIGURATION_RESULT_SCHEMA = (
    "missipy.qdrant.real_binding_configuration_result.v1"
)

_ALLOWED_OPERATIONS = frozenset({"projection", "recall"})
_ENV_VAR_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class QdrantRealBindingConfigurationCommand:
    connection: QdrantClientConnectionConfig
    effect_gate: QdrantClientEffectGate
    sql_authority_scope: QdrantSqlAuthorityScope
    transport_policy: QdrantStrictGrpcTransportPolicy
    target: QdrantProjectionTarget
    projection_policy: QdrantProjectionPolicy
    requested_operations: tuple[str, ...] = ()
    api_key_env_var: str = ""
    recall_oversample_factor: int = 4


@dataclass(frozen=True, slots=True)
class QdrantRealBindingConfigurationPolicy:
    require_loopback: bool = True
    require_https_for_remote: bool = True
    require_strict_data_grpc: bool = True
    require_connection_compatibility_check: bool = True
    require_exact_effect_gate: bool = True
    require_api_key_env_for_remote: bool = True
    allowed_collection_names: tuple[str, ...] = (
        "autodoc_context_embeddings",
    )
    allowed_vector_dimensions: tuple[int, ...] = (384,)
    max_timeout_seconds: float = 30.0
    max_recall_oversample_factor: int = 16

    def __post_init__(self) -> None:
        if not self.allowed_collection_names:
            raise ValueError(
                "allowed_collection_names must not be empty"
            )
        if any(
            not name or not name.strip()
            for name in self.allowed_collection_names
        ):
            raise ValueError(
                "allowed_collection_names must be non-empty"
            )
        if not self.allowed_vector_dimensions:
            raise ValueError(
                "allowed_vector_dimensions must not be empty"
            )
        if any(
            dimension <= 0
            for dimension in self.allowed_vector_dimensions
        ):
            raise ValueError(
                "allowed_vector_dimensions must be positive"
            )
        if self.max_timeout_seconds <= 0:
            raise ValueError("max_timeout_seconds must be > 0")
        if self.max_recall_oversample_factor <= 0:
            raise ValueError(
                "max_recall_oversample_factor must be > 0"
            )


@dataclass(frozen=True, slots=True)
class QdrantRealBindingConfigurationResult:
    valid: bool
    issues: tuple[str, ...]
    binding_ref: str
    binding_digest: str
    requested_operations: tuple[str, ...]
    connection: QdrantClientConnectionConfig
    effect_gate: QdrantClientEffectGate
    sql_authority_scope: QdrantSqlAuthorityScope
    transport_policy: QdrantStrictGrpcTransportPolicy
    target: QdrantProjectionTarget
    projection_policy: QdrantProjectionPolicy
    api_key_env_var: str
    recall_oversample_factor: int
    remote_endpoint: bool
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REAL_BINDING_CONFIGURATION_RESULT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "binding_ref": self.binding_ref,
            "binding_digest": self.binding_digest,
            "requested_operations": list(
                self.requested_operations
            ),
            "connection": self.connection.to_mapping(),
            "effect_gate": self.effect_gate.to_mapping(),
            "sql_authority_scope": (
                self.sql_authority_scope.to_mapping()
            ),
            "transport_policy": (
                self.transport_policy.to_mapping()
            ),
            "target": self.target.to_mapping(),
            "projection_policy": {
                "max_points": self.projection_policy.max_points,
                "max_recall_hits": (
                    self.projection_policy.max_recall_hits
                ),
                "require_sql_context_ref": (
                    self.projection_policy.require_sql_context_ref
                ),
                "require_normalized_vectors": (
                    self.projection_policy.require_normalized_vectors
                ),
                "normalization_tolerance": (
                    self.projection_policy.normalization_tolerance
                ),
            },
            "api_key": {
                "source": (
                    "environment"
                    if self.api_key_env_var
                    else "none"
                ),
                "env_var": self.api_key_env_var,
                "secret_value_serialized": False,
            },
            "recall_oversample_factor": (
                self.recall_oversample_factor
            ),
            "remote_endpoint": self.remote_endpoint,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        operations = ",".join(self.requested_operations) or "preview"
        return " ".join(
            (
                f"qdrant_real_binding_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"operations={operations}",
                f"collection={self.target.collection_name}",
                f"dimension={self.target.vector_dimension}",
                f"remote_endpoint={self.remote_endpoint}",
                "external_call_performed=False",
                "qdrant_write_performed=False",
                "qdrant_search_performed=False",
            )
        )


def build_qdrant_real_binding_configuration(
    command: QdrantRealBindingConfigurationCommand,
    policy: QdrantRealBindingConfigurationPolicy | None = None,
) -> QdrantRealBindingConfigurationResult:
    active_policy = (
        policy or QdrantRealBindingConfigurationPolicy()
    )
    operations = tuple(
        sorted(
            operation.strip().casefold()
            for operation in command.requested_operations
        )
    )
    api_key_env_var = command.api_key_env_var.strip()
    issues = _validate_configuration(
        command,
        operations,
        api_key_env_var,
        active_policy,
    )

    connection_url = urlparse(command.connection.url)
    remote_endpoint = not _is_loopback_host(
        connection_url.hostname or ""
    )

    canonical = {
        "schema": REAL_BINDING_CONFIGURATION_SCHEMA,
        "requested_operations": list(operations),
        "connection": command.connection.to_mapping(),
        "effect_gate": command.effect_gate.to_mapping(),
        "sql_authority_scope": (
            command.sql_authority_scope.to_mapping()
        ),
        "transport_policy": (
            command.transport_policy.to_mapping()
        ),
        "target": command.target.to_mapping(),
        "projection_policy": {
            "max_points": command.projection_policy.max_points,
            "max_recall_hits": (
                command.projection_policy.max_recall_hits
            ),
            "require_sql_context_ref": (
                command.projection_policy.require_sql_context_ref
            ),
            "require_normalized_vectors": (
                command.projection_policy.require_normalized_vectors
            ),
            "normalization_tolerance": (
                command.projection_policy.normalization_tolerance
            ),
        },
        "api_key_env_var": api_key_env_var,
        "recall_oversample_factor": (
            command.recall_oversample_factor
        ),
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return QdrantRealBindingConfigurationResult(
        valid=not issues,
        issues=tuple(issues),
        binding_ref=(
            f"qdrant-real-binding:{digest[:16]}"
            if not issues
            else ""
        ),
        binding_digest=digest,
        requested_operations=operations,
        connection=command.connection,
        effect_gate=command.effect_gate,
        sql_authority_scope=command.sql_authority_scope,
        transport_policy=command.transport_policy,
        target=command.target,
        projection_policy=command.projection_policy,
        api_key_env_var=api_key_env_var,
        recall_oversample_factor=(
            command.recall_oversample_factor
        ),
        remote_endpoint=remote_endpoint,
        boundaries=_boundaries(),
    )


def _validate_configuration(
    command: QdrantRealBindingConfigurationCommand,
    operations: tuple[str, ...],
    api_key_env_var: str,
    policy: QdrantRealBindingConfigurationPolicy,
) -> list[str]:
    issues: list[str] = []

    if len(operations) != len(set(operations)):
        issues.append("requested_operations must be unique")
    unsupported = sorted(set(operations) - _ALLOWED_OPERATIONS)
    if unsupported:
        issues.append(
            "requested_operations contains unsupported values"
        )

    wants_projection = "projection" in operations
    wants_recall = "recall" in operations
    if policy.require_exact_effect_gate:
        if command.effect_gate.allow_write != wants_projection:
            issues.append(
                "effect gate allow_write must exactly match projection"
            )
        if command.effect_gate.allow_search != wants_recall:
            issues.append(
                "effect gate allow_search must exactly match recall"
            )
    else:
        if wants_projection and not command.effect_gate.allow_write:
            issues.append(
                "projection requires effect gate allow_write"
            )
        if wants_recall and not command.effect_gate.allow_search:
            issues.append(
                "recall requires effect gate allow_search"
            )

    connection = urlparse(command.connection.url)
    transport = urlparse(
        command.transport_policy.rest_admin_url
    )
    if connection.username or connection.password:
        issues.append(
            "connection URL must not contain inline credentials"
        )
    if connection.query or connection.fragment:
        issues.append(
            "connection URL must not contain query or fragment"
        )
    if _origin(connection) != _origin(transport):
        issues.append(
            "connection URL and REST administration URL must match"
        )
    if (
        command.connection.prefer_grpc
        != command.transport_policy.prefer_grpc
    ):
        issues.append(
            "connection prefer_grpc must match transport policy"
        )
    if (
        command.connection.grpc_port
        != command.transport_policy.grpc_port
    ):
        issues.append(
            "connection grpc_port must match transport policy"
        )
    if (
        policy.require_strict_data_grpc
        and not command.transport_policy.strict_data_grpc
    ):
        issues.append("strict data gRPC is required")
    if (
        policy.require_connection_compatibility_check
        and not command.connection.check_compatibility
    ):
        issues.append(
            "connection compatibility check is required"
        )
    if (
        command.connection.timeout_seconds
        > policy.max_timeout_seconds
    ):
        issues.append("connection timeout exceeds policy maximum")

    hostname = connection.hostname or ""
    remote_endpoint = not _is_loopback_host(hostname)
    if policy.require_loopback and remote_endpoint:
        issues.append("Qdrant endpoint must be loopback")
    if (
        remote_endpoint
        and policy.require_https_for_remote
        and connection.scheme != "https"
    ):
        issues.append("remote Qdrant endpoint must use https")
    if (
        remote_endpoint
        and policy.require_api_key_env_for_remote
        and not api_key_env_var
    ):
        issues.append(
            "remote Qdrant endpoint requires api_key_env_var"
        )

    if api_key_env_var and not _ENV_VAR_RE.fullmatch(
        api_key_env_var
    ):
        issues.append(
            "api_key_env_var must be an uppercase environment name"
        )

    allowed_collections = {
        name.strip()
        for name in policy.allowed_collection_names
    }
    if command.target.collection_name not in allowed_collections:
        issues.append(
            "target collection is not allowed by shared-collection policy"
        )
    if (
        command.target.vector_dimension
        not in set(policy.allowed_vector_dimensions)
    ):
        issues.append(
            "target vector dimension is not allowed"
        )
    if not command.projection_policy.require_sql_context_ref:
        issues.append(
            "projection policy must require SQL context references"
        )
    if not command.projection_policy.require_normalized_vectors:
        issues.append(
            "projection policy must require normalized vectors"
        )
    if command.recall_oversample_factor <= 0:
        issues.append(
            "recall_oversample_factor must be > 0"
        )
    if (
        command.recall_oversample_factor
        > policy.max_recall_oversample_factor
    ):
        issues.append(
            "recall_oversample_factor exceeds policy maximum"
        )
    return issues


def _origin(parsed: Any) -> tuple[str, str, int]:
    scheme = str(parsed.scheme).casefold()
    host = str(parsed.hostname or "").casefold()
    port = parsed.port or (443 if scheme == "https" else 80)
    return scheme, host, port


def _is_loopback_host(hostname: str) -> bool:
    normalized = hostname.strip().casefold()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("configuration_only", True),
        ("existing_executor_reused", True),
        ("existing_sql_scope_reused", True),
        ("shared_collection_policy", True),
        ("secret_value_serialized", False),
        ("dependency_inspection_performed", False),
        ("client_constructed", False),
        ("external_call_performed", False),
        ("qdrant_write_performed", False),
        ("qdrant_search_performed", False),
        ("sql_write_performed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
