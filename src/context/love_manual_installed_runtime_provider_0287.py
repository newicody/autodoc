"""Canonical provider binding for an already-composed installed runtime.

The provider never creates a Scheduler, SQL authority, OpenVINO executor,
Qdrant client or laboratory.  The live server registers its already-composed
``ImportedActionsRuntimePorts`` once.  Each imported run then validates the
manual backend configuration and returns those exact ports.
"""
from __future__ import annotations

from collections.abc import Mapping
from threading import RLock
from typing import Any

from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from context.love_manual_runtime_configuration_0287 import (
    load_manual_installed_runtime_settings,
)
from context.love_manual_runtime_readiness_0287 import (
    inspect_manual_runtime_readiness,
)

CANONICAL_MANUAL_PROVIDER_REF = (
    "context.love_manual_installed_runtime_provider_0287:"
    "build_installed_runtime_ports"
)


class ManualInstalledRuntimeProviderError(RuntimeError):
    """Raised when live ports are absent or differ from manual configuration."""


_LOCK = RLock()
_REGISTERED_PORTS: ImportedActionsRuntimePorts | None = None


def register_installed_runtime_ports(
    ports: ImportedActionsRuntimePorts,
) -> ImportedActionsRuntimePorts:
    """Register the one live server composition without replacing its authority."""
    validated = validate_imported_actions_runtime_ports(ports)
    global _REGISTERED_PORTS
    with _LOCK:
        if _REGISTERED_PORTS is not None and _REGISTERED_PORTS is not validated:
            raise ManualInstalledRuntimeProviderError(
                "installed runtime ports are already registered"
            )
        _REGISTERED_PORTS = validated
    return validated


def clear_installed_runtime_ports_for_shutdown(
    ports: ImportedActionsRuntimePorts,
) -> None:
    """Remove only the exact composition being shut down by its owner."""
    global _REGISTERED_PORTS
    with _LOCK:
        if _REGISTERED_PORTS is not ports:
            raise ManualInstalledRuntimeProviderError(
                "cannot clear a different installed runtime composition"
            )
        _REGISTERED_PORTS = None


def get_registered_installed_runtime_ports() -> ImportedActionsRuntimePorts:
    with _LOCK:
        ports = _REGISTERED_PORTS
    if ports is None:
        raise ManualInstalledRuntimeProviderError(
            "no installed runtime ports are registered; start the canonical "
            "server bootstrap before importing an Actions run"
        )
    return validate_imported_actions_runtime_ports(ports)


def _validate_manual_identity(
    ports: ImportedActionsRuntimePorts,
    settings: Any,
) -> ImportedActionsRuntimePorts:
    attestation = ports.attestation
    expected = {
        "runtime_ref": settings.runtime_ref,
        "scheduler_ref": settings.scheduler_ref,
        "sql_authority_ref": settings.sql_authority_ref,
        "projection_backend_ref": settings.projection_backend_ref,
        "embedding_backend_ref": settings.embedding_backend_ref,
        "retrieval_backend_ref": settings.retrieval_backend_ref,
        "model_ref": settings.model_ref,
        "model_revision": settings.model_revision,
        "qdrant_collection": settings.qdrant.collection,
        "embedding_dimension": settings.openvino.dimension,
    }
    for name, value in expected.items():
        if getattr(attestation, name) != value:
            raise ManualInstalledRuntimeProviderError(
                f"registered runtime attestation {name} differs from manual configuration"
            )
    if ports.base_revision_ref != settings.base_revision_ref:
        raise ManualInstalledRuntimeProviderError(
            "registered runtime base revision differs from manual configuration"
        )
    if ports.scheduler_lifecycle != settings.scheduler_lifecycle:
        raise ManualInstalledRuntimeProviderError(
            "registered scheduler lifecycle differs from manual configuration"
        )
    return ports


def build_installed_runtime_ports(
    *,
    repository: str,
    run_id: str,
    request_payload: Mapping[str, object],
    runtime_context: Mapping[str, object],
    created_at: str,
    settings: object | None = None,
) -> ImportedActionsRuntimePorts:
    """Return validated live ports after read-only backend readiness.

    The run metadata is accepted for the canonical provider signature but does
    not influence backend identities.  No live object is reconstructed from
    serialized runtime_context data.
    """
    del repository, run_id, request_payload, runtime_context, created_at, settings
    manual = load_manual_installed_runtime_settings()
    readiness = inspect_manual_runtime_readiness(manual)
    if not readiness.valid:
        raise ManualInstalledRuntimeProviderError(
            "manual installed runtime readiness failed: "
            + "; ".join(readiness.issues)
        )
    ports = get_registered_installed_runtime_ports()
    return _validate_manual_identity(ports, manual)


__all__ = (
    "CANONICAL_MANUAL_PROVIDER_REF",
    "ManualInstalledRuntimeProviderError",
    "build_installed_runtime_ports",
    "clear_installed_runtime_ports_for_shutdown",
    "get_registered_installed_runtime_ports",
    "register_installed_runtime_ports",
)
