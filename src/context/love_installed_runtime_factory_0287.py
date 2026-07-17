"""Canonical installed runtime factory for the live r14/r15 love closed loop.

This module is a composition boundary only.  It never constructs a Scheduler,
SQL backend, OpenVINO runtime, Qdrant client or laboratory manager.  Instead it
loads the single provider configured by the installed server composition,
builds the immutable real-backend attestation and validates the resulting ports
against :mod:`context.love_imported_actions_runtime_contract_0287`.
"""

from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from importlib import import_module
import inspect
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
    ImportedActionsRealBackendAttestation,
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)

INSTALLED_RUNTIME_FACTORY_SCHEMA = (
    "missipy.love.installed_runtime_factory_configuration.v1"
)
DEFAULT_INSTALLED_RUNTIME_CONFIG = Path(
    ".var/config/love_installed_runtime.ini"
)
INSTALLED_RUNTIME_CONFIG_ENV = "AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG"


class InstalledRuntimeFactoryError(ValueError):
    """Raised when the installed runtime composition cannot be trusted."""


@dataclass(frozen=True, slots=True)
class InstalledRuntimeFactorySettings:
    """Immutable settings used to attest one installed runtime composition."""

    schema: str
    config_path: str
    provider_ref: str
    runtime_ref: str
    scheduler_ref: str
    scheduler_lifecycle: str
    sql_authority_ref: str
    projection_backend_ref: str
    embedding_backend_ref: str
    retrieval_backend_ref: str
    model_ref: str
    model_revision: str
    qdrant_collection: str
    base_revision_ref: str
    evidence_refs: tuple[str, ...]
    embedding_dimension: int = 384

    def __post_init__(self) -> None:
        required = {
            "schema": self.schema,
            "config_path": self.config_path,
            "provider_ref": self.provider_ref,
            "runtime_ref": self.runtime_ref,
            "scheduler_ref": self.scheduler_ref,
            "scheduler_lifecycle": self.scheduler_lifecycle,
            "sql_authority_ref": self.sql_authority_ref,
            "projection_backend_ref": self.projection_backend_ref,
            "embedding_backend_ref": self.embedding_backend_ref,
            "retrieval_backend_ref": self.retrieval_backend_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "qdrant_collection": self.qdrant_collection,
            "base_revision_ref": self.base_revision_ref,
        }
        for name, value in required.items():
            if not str(value).strip():
                raise InstalledRuntimeFactoryError(f"{name} must be non-empty")
        if self.schema != INSTALLED_RUNTIME_FACTORY_SCHEMA:
            raise InstalledRuntimeFactoryError(
                "unsupported installed runtime configuration schema"
            )
        if self.scheduler_lifecycle not in {
            "tool-bounded",
            "externally-managed",
        }:
            raise InstalledRuntimeFactoryError(
                "scheduler_lifecycle must be tool-bounded or externally-managed"
            )
        if self.embedding_dimension != 384:
            raise InstalledRuntimeFactoryError(
                "installed love runtime must use E5 dimension 384"
            )
        if not self.evidence_refs:
            raise InstalledRuntimeFactoryError(
                "at least one installed runtime evidence ref is required"
            )
        _reject_non_real_markers(
            self.provider_ref,
            self.projection_backend_ref,
            self.embedding_backend_ref,
            self.retrieval_backend_ref,
            *self.evidence_refs,
        )

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "config_path": self.config_path,
                "provider_ref": self.provider_ref,
                "runtime_ref": self.runtime_ref,
                "scheduler_ref": self.scheduler_ref,
                "scheduler_lifecycle": self.scheduler_lifecycle,
                "sql_authority_ref": self.sql_authority_ref,
                "projection_backend_ref": self.projection_backend_ref,
                "embedding_backend_ref": self.embedding_backend_ref,
                "retrieval_backend_ref": self.retrieval_backend_ref,
                "model_ref": self.model_ref,
                "model_revision": self.model_revision,
                "qdrant_collection": self.qdrant_collection,
                "base_revision_ref": self.base_revision_ref,
                "evidence_refs": self.evidence_refs,
                "embedding_dimension": self.embedding_dimension,
            }
        )


def _reject_non_real_markers(*values: str) -> None:
    forbidden = ("dummy", "fake", "stub", "deterministic-test")
    for value in values:
        lowered = str(value).casefold()
        marker = next((item for item in forbidden if item in lowered), None)
        if marker is not None:
            raise InstalledRuntimeFactoryError(
                f"installed runtime cannot use non-real marker {marker!r}"
            )


def _split_refs(raw: str) -> tuple[str, ...]:
    values: list[str] = []
    for line in raw.replace(",", "\n").splitlines():
        value = line.strip()
        if value and value not in values:
            values.append(value)
    return tuple(values)


def _required(parser: ConfigParser, section: str, option: str) -> str:
    value = parser.get(section, option, fallback="").strip()
    if not value:
        raise InstalledRuntimeFactoryError(
            f"missing [{section}] {option} in installed runtime configuration"
        )
    return value


def resolve_installed_runtime_config_path(
    explicit_path: str | os.PathLike[str] | None = None,
) -> Path:
    """Resolve the one installed runtime configuration path."""

    if explicit_path is not None and str(explicit_path).strip():
        return Path(explicit_path).expanduser().resolve()
    from_env = os.environ.get(INSTALLED_RUNTIME_CONFIG_ENV, "").strip()
    if from_env:
        return Path(from_env).expanduser().resolve()
    repository_root = Path(__file__).resolve().parents[2]
    return (repository_root / DEFAULT_INSTALLED_RUNTIME_CONFIG).resolve()


def load_installed_runtime_factory_settings(
    explicit_path: str | os.PathLike[str] | None = None,
) -> InstalledRuntimeFactorySettings:
    """Load and validate the installed runtime composition configuration."""

    path = resolve_installed_runtime_config_path(explicit_path)
    if not path.is_file():
        raise InstalledRuntimeFactoryError(
            "installed runtime configuration not found: "
            f"{path}. Copy config/love_installed_runtime.example.ini to "
            ".var/config/love_installed_runtime.ini and configure the existing "
            "server composition provider."
        )
    parser = ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except OSError as exc:
        raise InstalledRuntimeFactoryError(
            f"cannot read installed runtime configuration: {path}"
        ) from exc

    try:
        embedding_dimension = parser.getint(
            "embedding", "dimension", fallback=384
        )
    except ValueError as exc:
        raise InstalledRuntimeFactoryError(
            "[embedding] dimension must be an integer"
        ) from exc

    return InstalledRuntimeFactorySettings(
        schema=parser.get(
            "runtime", "schema", fallback=INSTALLED_RUNTIME_FACTORY_SCHEMA
        ).strip(),
        config_path=str(path),
        provider_ref=_required(parser, "provider", "factory"),
        runtime_ref=_required(parser, "runtime", "runtime_ref"),
        scheduler_ref=_required(parser, "scheduler", "scheduler_ref"),
        scheduler_lifecycle=parser.get(
            "scheduler", "lifecycle", fallback="externally-managed"
        ).strip(),
        sql_authority_ref=_required(parser, "sql", "authority_ref"),
        projection_backend_ref=_required(
            parser, "projection", "backend_ref"
        ),
        embedding_backend_ref=_required(parser, "embedding", "backend_ref"),
        retrieval_backend_ref=_required(parser, "qdrant", "backend_ref"),
        model_ref=_required(parser, "embedding", "model_ref"),
        model_revision=_required(parser, "embedding", "model_revision"),
        qdrant_collection=_required(parser, "qdrant", "collection"),
        base_revision_ref=_required(parser, "sql", "base_revision_ref"),
        evidence_refs=_split_refs(_required(parser, "evidence", "refs")),
        embedding_dimension=embedding_dimension,
    )


def _load_provider(provider_ref: str) -> Callable[..., object]:
    module_name, separator, function_name = provider_ref.partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise InstalledRuntimeFactoryError(
            "[provider] factory must use module:function syntax"
        )
    try:
        module = import_module(module_name.strip())
    except Exception as exc:  # import boundary: preserve operator-facing error
        raise InstalledRuntimeFactoryError(
            f"cannot import installed runtime provider module {module_name!r}"
        ) from exc
    provider = getattr(module, function_name.strip(), None)
    if provider is None or not callable(provider):
        raise InstalledRuntimeFactoryError(
            f"installed runtime provider is not callable: {provider_ref}"
        )
    return provider


def _provider_keyword_arguments(
    provider: Callable[..., object],
    available: Mapping[str, object],
) -> Mapping[str, object]:
    """Pass only supported named arguments to an installed provider."""

    try:
        signature = inspect.signature(provider)
    except (TypeError, ValueError):
        return available
    if any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    ):
        return available
    supported = {
        name
        for name, parameter in signature.parameters.items()
        if parameter.kind
        in {
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        }
    }
    return MappingProxyType(
        {name: value for name, value in available.items() if name in supported}
    )


def _get_port(payload: object, name: str) -> object:
    if isinstance(payload, Mapping):
        value = payload.get(name)
    else:
        value = getattr(payload, name, None)
    if value is None:
        raise InstalledRuntimeFactoryError(
            f"installed runtime provider omitted required port {name}"
        )
    return value


def _validate_configured_ports(
    ports: ImportedActionsRuntimePorts,
    settings: InstalledRuntimeFactorySettings,
) -> ImportedActionsRuntimePorts:
    validated = validate_imported_actions_runtime_ports(ports)
    if validated.runtime_ref != settings.runtime_ref:
        raise InstalledRuntimeFactoryError(
            "provider runtime_ref differs from installed configuration"
        )
    if validated.base_revision_ref != settings.base_revision_ref:
        raise InstalledRuntimeFactoryError(
            "provider base_revision_ref differs from installed configuration"
        )
    if validated.scheduler_lifecycle != settings.scheduler_lifecycle:
        raise InstalledRuntimeFactoryError(
            "provider scheduler lifecycle differs from installed configuration"
        )
    attestation = validated.attestation
    expected = {
        "scheduler_ref": settings.scheduler_ref,
        "sql_authority_ref": settings.sql_authority_ref,
        "projection_backend_ref": settings.projection_backend_ref,
        "embedding_backend_ref": settings.embedding_backend_ref,
        "retrieval_backend_ref": settings.retrieval_backend_ref,
        "model_ref": settings.model_ref,
        "model_revision": settings.model_revision,
        "qdrant_collection": settings.qdrant_collection,
        "embedding_dimension": settings.embedding_dimension,
    }
    for name, value in expected.items():
        if getattr(attestation, name) != value:
            raise InstalledRuntimeFactoryError(
                f"provider attestation {name} differs from installed configuration"
            )
    return validated


def build_runtime(
    *,
    repository: str,
    run_id: str,
    request_payload: Mapping[str, object],
    runtime_context: Mapping[str, object],
    created_at: str,
) -> ImportedActionsRuntimePorts:
    """Build validated r14/r15 ports from the installed server composition.

    The configured provider owns only composition of components that already
    exist in the server process or its dedicated tool-bounded installation.  It
    must not create a second Scheduler authority or substitute fake SQL,
    OpenVINO/E5 or Qdrant backends.
    """

    settings = load_installed_runtime_factory_settings()
    provider = _load_provider(settings.provider_ref)
    available = MappingProxyType(
        {
            "repository": repository,
            "run_id": str(run_id),
            "request_payload": request_payload,
            "runtime_context": runtime_context,
            "created_at": created_at,
            "settings": settings,
        }
    )
    try:
        provided = provider(**_provider_keyword_arguments(provider, available))
    except InstalledRuntimeFactoryError:
        raise
    except Exception as exc:
        raise InstalledRuntimeFactoryError(
            "installed runtime provider failed while composing existing ports"
        ) from exc

    if isinstance(provided, ImportedActionsRuntimePorts):
        return _validate_configured_ports(provided, settings)

    attestation = ImportedActionsRealBackendAttestation(
        schema=IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
        runtime_ref=settings.runtime_ref,
        scheduler_ref=settings.scheduler_ref,
        sql_authority_ref=settings.sql_authority_ref,
        projection_backend_ref=settings.projection_backend_ref,
        embedding_backend_ref=settings.embedding_backend_ref,
        retrieval_backend_ref=settings.retrieval_backend_ref,
        model_ref=settings.model_ref,
        model_revision=settings.model_revision,
        qdrant_collection=settings.qdrant_collection,
        evidence_refs=settings.evidence_refs,
        scheduler_lifecycle=settings.scheduler_lifecycle,
        embedding_dimension=settings.embedding_dimension,
        scheduler_contract_reused=True,
        sql_authority_reused=True,
        openvino_e5_real=True,
        qdrant_write_real=True,
        qdrant_returns_references_only=True,
    )
    ports = ImportedActionsRuntimePorts(
        schema=IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
        runtime_ref=settings.runtime_ref,
        scheduler=_get_port(provided, "scheduler"),
        dispatcher=_get_port(provided, "dispatcher"),
        authority_store=_get_port(provided, "authority_store"),
        projection_port=_get_port(provided, "projection_port"),
        collection=_get_port(provided, "collection"),
        embedder=_get_port(provided, "embedder"),
        executor=_get_port(provided, "executor"),
        base_revision_ref=settings.base_revision_ref,
        scheduler_lifecycle=settings.scheduler_lifecycle,
        attestation=attestation,
    )
    return validate_imported_actions_runtime_ports(ports)


__all__ = [
    "DEFAULT_INSTALLED_RUNTIME_CONFIG",
    "INSTALLED_RUNTIME_CONFIG_ENV",
    "INSTALLED_RUNTIME_FACTORY_SCHEMA",
    "InstalledRuntimeFactoryError",
    "InstalledRuntimeFactorySettings",
    "build_runtime",
    "load_installed_runtime_factory_settings",
    "resolve_installed_runtime_config_path",
]
