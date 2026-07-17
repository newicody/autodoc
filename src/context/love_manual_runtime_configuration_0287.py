"""Manual installed runtime configuration for the live r15 closed loop.

This module is a pure configuration boundary.  It resolves no network client,
opens no database and constructs no Scheduler.  Secrets are referenced by
environment-variable name and are never returned by public mappings.
"""
from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import urlparse

MANUAL_RUNTIME_CONFIGURATION_SCHEMA = (
    "missipy.love.manual_installed_runtime_configuration.v1"
)
DEFAULT_MANUAL_RUNTIME_CONFIG = Path(".var/config/love_installed_runtime.ini")
MANUAL_RUNTIME_CONFIG_ENV = "AUTODOC_LOVE_INSTALLED_RUNTIME_CONFIG"


class ManualRuntimeConfigurationError(ValueError):
    """Raised when the local runtime configuration is incomplete or unsafe."""


def _required(parser: ConfigParser, section: str, option: str) -> str:
    value = parser.get(section, option, fallback="").strip()
    if not value:
        raise ManualRuntimeConfigurationError(
            f"missing [{section}] {option} in manual runtime configuration"
        )
    return value


def _positive_int(
    parser: ConfigParser,
    section: str,
    option: str,
    *,
    fallback: int,
) -> int:
    try:
        value = parser.getint(section, option, fallback=fallback)
    except ValueError as exc:
        raise ManualRuntimeConfigurationError(
            f"[{section}] {option} must be an integer"
        ) from exc
    if value <= 0:
        raise ManualRuntimeConfigurationError(
            f"[{section}] {option} must be positive"
        )
    return value


def _positive_float(
    parser: ConfigParser,
    section: str,
    option: str,
    *,
    fallback: float,
) -> float:
    try:
        value = parser.getfloat(section, option, fallback=fallback)
    except ValueError as exc:
        raise ManualRuntimeConfigurationError(
            f"[{section}] {option} must be numeric"
        ) from exc
    if value <= 0:
        raise ManualRuntimeConfigurationError(
            f"[{section}] {option} must be positive"
        )
    return value


def _require_loopback_host(name: str, host: str) -> None:
    normalized = host.strip().casefold().strip("[]")
    if normalized not in {"127.0.0.1", "localhost", "::1"}:
        raise ManualRuntimeConfigurationError(
            f"{name} must remain loopback for this installed prototype"
        )


@dataclass(frozen=True, slots=True)
class PostgreSqlRuntimeSettings:
    host: str
    port: int
    database: str
    user: str
    password_env: str
    sslmode: str
    schema_name: str
    connect_timeout_seconds: int = 5

    def __post_init__(self) -> None:
        _require_loopback_host("postgresql host", self.host)
        for name, value in {
            "database": self.database,
            "user": self.user,
            "password_env": self.password_env,
            "sslmode": self.sslmode,
            "schema": self.schema_name,
        }.items():
            if not value.strip():
                raise ManualRuntimeConfigurationError(
                    f"postgresql {name} must be non-empty"
                )
        if self.port <= 0 or self.connect_timeout_seconds <= 0:
            raise ManualRuntimeConfigurationError(
                "postgresql port and timeout must be positive"
            )

    def to_public_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "user": self.user,
                "password_env": self.password_env,
                "password_loaded": bool(os.environ.get(self.password_env, "")),
                "secret_value_serialized": False,
                "sslmode": self.sslmode,
                "schema": self.schema_name,
                "connect_timeout_seconds": self.connect_timeout_seconds,
            }
        )


@dataclass(frozen=True, slots=True)
class QdrantRuntimeSettings:
    url: str
    grpc_port: int
    api_key_env: str
    collection: str
    vector_name: str
    dimension: int
    distance: str
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ManualRuntimeConfigurationError("qdrant url must be HTTP(S)")
        _require_loopback_host("qdrant host", parsed.hostname)
        if self.grpc_port <= 0 or self.timeout_seconds <= 0:
            raise ManualRuntimeConfigurationError(
                "qdrant grpc_port and timeout must be positive"
            )
        if not self.collection.strip():
            raise ManualRuntimeConfigurationError(
                "qdrant collection or alias must be non-empty"
            )
        if self.dimension != 384:
            raise ManualRuntimeConfigurationError(
                "qdrant collection must use E5 dimension 384"
            )
        if self.distance.casefold() != "cosine":
            raise ManualRuntimeConfigurationError(
                "qdrant collection must use Cosine distance"
            )

    def to_public_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "url": self.url.rstrip("/"),
                "grpc_port": self.grpc_port,
                "api_key_env": self.api_key_env,
                "api_key_loaded": bool(
                    self.api_key_env and os.environ.get(self.api_key_env, "")
                ),
                "secret_value_serialized": False,
                "collection": self.collection,
                "vector_name": self.vector_name,
                "dimension": self.dimension,
                "distance": "Cosine",
                "timeout_seconds": self.timeout_seconds,
            }
        )


@dataclass(frozen=True, slots=True)
class OpenVINORuntimeSettings:
    model_dir: str
    model_xml: str
    device: str
    dimension: int
    query_prefix: str
    passage_prefix: str

    def __post_init__(self) -> None:
        if self.dimension != 384:
            raise ManualRuntimeConfigurationError(
                "OpenVINO E5 configuration must use dimension 384"
            )
        for name, value in {
            "model_dir": self.model_dir,
            "model_xml": self.model_xml,
            "device": self.device,
            "query_prefix": self.query_prefix,
            "passage_prefix": self.passage_prefix,
        }.items():
            if not value.strip():
                raise ManualRuntimeConfigurationError(
                    f"openvino {name} must be non-empty"
                )
        if self.query_prefix.strip().casefold() != "query:":
            raise ManualRuntimeConfigurationError(
                "OpenVINO E5 query_prefix must be query:"
            )
        if self.passage_prefix.strip().casefold() != "passage:":
            raise ManualRuntimeConfigurationError(
                "OpenVINO E5 passage_prefix must be passage:"
            )

    def to_public_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "model_dir": self.model_dir,
                "model_xml": self.model_xml,
                "device": self.device,
                "dimension": self.dimension,
                "query_prefix": self.query_prefix,
                "passage_prefix": self.passage_prefix,
            }
        )


@dataclass(frozen=True, slots=True)
class ManualInstalledRuntimeSettings:
    schema: str
    config_path: str
    runtime_ref: str
    scheduler_ref: str
    scheduler_lifecycle: str
    sql_authority_ref: str
    projection_backend_ref: str
    embedding_backend_ref: str
    retrieval_backend_ref: str
    model_ref: str
    model_revision: str
    base_revision_ref: str
    postgresql: PostgreSqlRuntimeSettings
    qdrant: QdrantRuntimeSettings
    openvino: OpenVINORuntimeSettings

    def __post_init__(self) -> None:
        if self.schema != MANUAL_RUNTIME_CONFIGURATION_SCHEMA:
            raise ManualRuntimeConfigurationError(
                "unsupported manual installed runtime configuration schema"
            )
        if self.scheduler_lifecycle not in {
            "externally-managed",
            "tool-bounded",
        }:
            raise ManualRuntimeConfigurationError(
                "scheduler lifecycle must be externally-managed or tool-bounded"
            )
        required = {
            "runtime_ref": self.runtime_ref,
            "scheduler_ref": self.scheduler_ref,
            "sql_authority_ref": self.sql_authority_ref,
            "projection_backend_ref": self.projection_backend_ref,
            "embedding_backend_ref": self.embedding_backend_ref,
            "retrieval_backend_ref": self.retrieval_backend_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "base_revision_ref": self.base_revision_ref,
        }
        for name, value in required.items():
            if not value.strip():
                raise ManualRuntimeConfigurationError(f"{name} must be non-empty")

    def to_public_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "config_path": self.config_path,
                "runtime_ref": self.runtime_ref,
                "scheduler_ref": self.scheduler_ref,
                "scheduler_lifecycle": self.scheduler_lifecycle,
                "sql_authority_ref": self.sql_authority_ref,
                "projection_backend_ref": self.projection_backend_ref,
                "embedding_backend_ref": self.embedding_backend_ref,
                "retrieval_backend_ref": self.retrieval_backend_ref,
                "model_ref": self.model_ref,
                "model_revision": self.model_revision,
                "base_revision_ref": self.base_revision_ref,
                "postgresql": dict(self.postgresql.to_public_mapping()),
                "qdrant": dict(self.qdrant.to_public_mapping()),
                "openvino": dict(self.openvino.to_public_mapping()),
            }
        )


def resolve_manual_runtime_config_path(
    explicit_path: str | os.PathLike[str] | None = None,
) -> Path:
    if explicit_path is not None and str(explicit_path).strip():
        return Path(explicit_path).expanduser().resolve()
    from_env = os.environ.get(MANUAL_RUNTIME_CONFIG_ENV, "").strip()
    if from_env:
        return Path(from_env).expanduser().resolve()
    repository_root = Path(__file__).resolve().parents[2]
    return (repository_root / DEFAULT_MANUAL_RUNTIME_CONFIG).resolve()


def load_manual_installed_runtime_settings(
    explicit_path: str | os.PathLike[str] | None = None,
) -> ManualInstalledRuntimeSettings:
    path = resolve_manual_runtime_config_path(explicit_path)
    if not path.is_file():
        raise ManualRuntimeConfigurationError(
            f"manual installed runtime configuration not found: {path}"
        )
    parser = ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except OSError as exc:
        raise ManualRuntimeConfigurationError(
            f"cannot read manual runtime configuration: {path}"
        ) from exc

    postgresql = PostgreSqlRuntimeSettings(
        host=_required(parser, "postgresql", "host"),
        port=_positive_int(parser, "postgresql", "port", fallback=5432),
        database=_required(parser, "postgresql", "database"),
        user=_required(parser, "postgresql", "user"),
        password_env=_required(parser, "postgresql", "password_env"),
        sslmode=parser.get(
            "postgresql", "sslmode", fallback="disable"
        ).strip(),
        schema_name=_required(parser, "postgresql", "schema"),
        connect_timeout_seconds=_positive_int(
            parser,
            "postgresql",
            "connect_timeout_seconds",
            fallback=5,
        ),
    )
    qdrant = QdrantRuntimeSettings(
        url=_required(parser, "qdrant", "url").rstrip("/"),
        grpc_port=_positive_int(parser, "qdrant", "grpc_port", fallback=6334),
        api_key_env=parser.get("qdrant", "api_key_env", fallback="").strip(),
        collection=_required(parser, "qdrant", "collection"),
        vector_name=parser.get("qdrant", "vector_name", fallback="").strip(),
        dimension=_positive_int(parser, "qdrant", "dimension", fallback=384),
        distance=parser.get("qdrant", "distance", fallback="Cosine").strip(),
        timeout_seconds=_positive_float(
            parser, "qdrant", "timeout_seconds", fallback=5.0
        ),
    )
    openvino = OpenVINORuntimeSettings(
        model_dir=_required(parser, "openvino", "model_dir"),
        model_xml=_required(parser, "openvino", "model_xml"),
        device=parser.get("openvino", "device", fallback="CPU").strip(),
        dimension=_positive_int(parser, "openvino", "dimension", fallback=384),
        query_prefix=parser.get(
            "openvino", "query_prefix", fallback="query:"
        ).strip(),
        passage_prefix=parser.get(
            "openvino", "passage_prefix", fallback="passage:"
        ).strip(),
    )

    return ManualInstalledRuntimeSettings(
        schema=parser.get(
            "manual-runtime",
            "schema",
            fallback=MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
        ).strip(),
        config_path=str(path),
        runtime_ref=_required(parser, "runtime", "runtime_ref"),
        scheduler_ref=_required(parser, "scheduler", "scheduler_ref"),
        scheduler_lifecycle=parser.get(
            "scheduler", "lifecycle", fallback="externally-managed"
        ).strip(),
        sql_authority_ref=_required(parser, "sql", "authority_ref"),
        projection_backend_ref=_required(parser, "projection", "backend_ref"),
        embedding_backend_ref=_required(parser, "embedding", "backend_ref"),
        retrieval_backend_ref=_required(parser, "qdrant", "backend_ref"),
        model_ref=_required(parser, "embedding", "model_ref"),
        model_revision=_required(parser, "embedding", "model_revision"),
        base_revision_ref=_required(parser, "sql", "base_revision_ref"),
        postgresql=postgresql,
        qdrant=qdrant,
        openvino=openvino,
    )


__all__ = (
    "DEFAULT_MANUAL_RUNTIME_CONFIG",
    "MANUAL_RUNTIME_CONFIG_ENV",
    "MANUAL_RUNTIME_CONFIGURATION_SCHEMA",
    "ManualInstalledRuntimeSettings",
    "ManualRuntimeConfigurationError",
    "OpenVINORuntimeSettings",
    "PostgreSqlRuntimeSettings",
    "QdrantRuntimeSettings",
    "load_manual_installed_runtime_settings",
    "resolve_manual_runtime_config_path",
)
