"""Live PostgreSQL authority binding for the installed love runtime.

This module is the explicit I/O boundary between the validated manual runtime
configuration and the existing ``DbApiContextRevisionAuthorityStore``.  It
imports no Scheduler, laboratory, OpenVINO or Qdrant implementation and creates
no parallel orchestrator.

The PostgreSQL driver is loaded lazily.  Tests inject a DB-API connector, while
an installed runtime uses psycopg v3 through the same narrow callable surface.
Secrets are read from the configured environment variable and are never
included in serializable receipts or exception messages.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import importlib
import os
import re
from threading import RLock
from types import MappingProxyType
from typing import Any, Protocol

from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextRevision,
    ContextSqlWriteResult,
    DbApiContextRevisionAuthorityStore,
)
from context.github_research_scheduler_command_sql_authority_0287 import (
    DbApiGitHubResearchSchedulerCommandStore,
)
from context.scheduler_task_launch_sql_authority_0287 import (
    DbApiSchedulerTaskLaunchTransaction,
)
from context.scheduler_handler_execution_sql_authority_0287 import (
    DbApiSchedulerHandlerExecutionTransaction,
)
from context.love_manual_runtime_configuration_0287 import (
    ManualInstalledRuntimeSettings,
    PostgreSqlRuntimeSettings,
)
from context.sql_context_store import SqlContextStorePolicy
from context.love_postgresql_shared_adapter_port_0287 import (
    LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
    LovePostgreSqlSharedAdapterPort,
)


LOVE_POSTGRESQL_AUTHORITY_BINDING_SCHEMA = (
    "missipy.love.postgresql_authority_binding.v1"
)
LOVE_POSTGRESQL_BASE_REVISION_SEED_SCHEMA = (
    "missipy.love.postgresql_base_revision_seed.v1"
)
LOVE_POSTGRESQL_APPLICATION_NAME = "autodoc-love-runtime"
LOVE_BASE_REVISION_CREATED_AT = "1970-01-01T00:00:00Z"
_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


class LovePostgreSqlAuthorityBindingError(RuntimeError):
    """Raised when the live PostgreSQL authority cannot fail closed safely."""


class DbApiConnector(Protocol):
    """Narrow injected PostgreSQL DB-API connection factory."""

    def __call__(self, **kwargs: object) -> object:
        """Open and return one DB-API compatible connection."""


@dataclass(frozen=True, slots=True)
class LovePostgreSqlBaseRevisionSeedReceipt:
    """Public idempotent evidence for the installed base revision seed."""

    schema: str
    revision_ref: str
    context_ref: str
    inserted: bool
    idempotent_replay: bool

    def __post_init__(self) -> None:
        if self.schema != LOVE_POSTGRESQL_BASE_REVISION_SEED_SCHEMA:
            raise LovePostgreSqlAuthorityBindingError(
                "unsupported PostgreSQL base revision seed schema"
            )
        if not self.revision_ref.startswith("context-revision:"):
            raise LovePostgreSqlAuthorityBindingError(
                "revision_ref must start with context-revision:"
            )
        if not self.context_ref.startswith("context:"):
            raise LovePostgreSqlAuthorityBindingError(
                "context_ref must start with context:"
            )
        if self.inserted == self.idempotent_replay:
            raise LovePostgreSqlAuthorityBindingError(
                "seed receipt must describe insertion or idempotent replay"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "revision_ref": self.revision_ref,
            "context_ref": self.context_ref,
            "inserted": self.inserted,
            "idempotent_replay": self.idempotent_replay,
        }


@dataclass(frozen=True, slots=True)
class LovePostgreSqlAuthorityBindingReceipt:
    """Serializable evidence for one live authority binding."""

    schema: str
    runtime_ref: str
    sql_authority_ref: str
    host: str
    port: int
    database: str
    user: str
    schema_name: str
    driver: str
    seed: LovePostgreSqlBaseRevisionSeedReceipt
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != LOVE_POSTGRESQL_AUTHORITY_BINDING_SCHEMA:
            raise LovePostgreSqlAuthorityBindingError(
                "unsupported PostgreSQL authority binding schema"
            )
        if not self.runtime_ref.startswith("runtime:"):
            raise LovePostgreSqlAuthorityBindingError(
                "runtime_ref must start with runtime:"
            )
        if not self.sql_authority_ref.startswith("sql-authority:"):
            raise LovePostgreSqlAuthorityBindingError(
                "sql_authority_ref must start with sql-authority:"
            )
        if self.port <= 0:
            raise LovePostgreSqlAuthorityBindingError(
                "PostgreSQL port must be positive"
            )
        object.__setattr__(
            self,
            "boundaries",
            MappingProxyType(dict(self.boundaries)),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "runtime_ref": self.runtime_ref,
            "sql_authority_ref": self.sql_authority_ref,
            "postgresql": {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "user": self.user,
                "schema": self.schema_name,
                "driver": self.driver,
                "secret_value_serialized": False,
            },
            "seed": self.seed.to_mapping(),
            "boundaries": dict(self.boundaries),
        }


@dataclass(slots=True)
class LovePostgreSqlAuthorityBinding:
    """Owned live authority store and its public binding evidence."""

    authority_store: DbApiContextRevisionAuthorityStore
    shared_adapter_port: LovePostgreSqlSharedAdapterPort
    receipt: LovePostgreSqlAuthorityBindingReceipt
    scheduler_command_store: (
        DbApiGitHubResearchSchedulerCommandStore | None
    ) = None
    scheduler_task_launch_transaction: (
        DbApiSchedulerTaskLaunchTransaction | None
    ) = None
    scheduler_handler_execution_transaction: (
        DbApiSchedulerHandlerExecutionTransaction | None
    ) = None
    _closed: bool = field(default=False, init=False, repr=False)
    _lock: RLock = field(
        default_factory=RLock,
        init=False,
        repr=False,
        compare=False,
    )

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def close(self) -> None:
        """Close the injected connection exactly once."""

        with self._lock:
            if self._closed:
                return
            try:
                self.authority_store.close()
            except Exception as exc:  # noqa: BLE001 - sanitize driver errors
                raise LovePostgreSqlAuthorityBindingError(
                    "PostgreSQL authority close failed "
                    f"({type(exc).__name__})"
                ) from None
            self._closed = True


def build_love_base_revision(
    settings: ManualInstalledRuntimeSettings,
) -> ContextRevision:
    """Build the deterministic empty root revision for the installed runtime."""

    revision_ref = settings.base_revision_ref
    prefix = "context-revision:"
    if not revision_ref.startswith(prefix) or not revision_ref[len(prefix):]:
        raise LovePostgreSqlAuthorityBindingError(
            "base_revision_ref must start with context-revision:"
        )
    suffix = revision_ref[len(prefix):]
    return ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=revision_ref,
        context_ref=f"context:{suffix}",
        parent_revision_refs=(),
        memberships=(),
        validation_status="accepted",
        significance="material",
        evidence_refs=("evidence:love-installed-runtime-configuration",),
        created_at=LOVE_BASE_REVISION_CREATED_AT,
        metadata={
            "bootstrap_seed": True,
            "runtime_ref": settings.runtime_ref,
            "sql_authority_ref": settings.sql_authority_ref,
            "postgresql_schema": settings.postgresql.schema_name,
        },
    )


def ensure_love_base_revision(
    authority_store: DbApiContextRevisionAuthorityStore,
    settings: ManualInstalledRuntimeSettings,
) -> LovePostgreSqlBaseRevisionSeedReceipt:
    """Initialize or idempotently replay the configured root revision."""

    revision = build_love_base_revision(settings)
    result: ContextSqlWriteResult = authority_store.put_revision(revision)
    return LovePostgreSqlBaseRevisionSeedReceipt(
        schema=LOVE_POSTGRESQL_BASE_REVISION_SEED_SCHEMA,
        revision_ref=revision.revision_ref,
        context_ref=revision.context_ref,
        inserted=result.inserted,
        idempotent_replay=result.idempotent_replay,
    )


def open_love_postgresql_authority(
    settings: ManualInstalledRuntimeSettings,
    *,
    connector: DbApiConnector | None = None,
    environment: Mapping[str, str] | None = None,
) -> LovePostgreSqlAuthorityBinding:
    """Open PostgreSQL, initialize the authority schema and seed the root.

    The caller owns the returned binding and should expose ``binding.close`` as
    one tool-bounded runtime lease hook.  This function performs no Qdrant
    write, no OpenVINO inference and no Scheduler construction.
    """

    postgres = settings.postgresql
    secret_source = os.environ if environment is None else environment
    password = str(secret_source.get(postgres.password_env, ""))
    if not password:
        raise LovePostgreSqlAuthorityBindingError(
            f"missing PostgreSQL password environment variable "
            f"{postgres.password_env}"
        )

    connection_factory = connector or _load_psycopg_connector()
    connection: object | None = None
    try:
        connection = connection_factory(
            host=postgres.host,
            port=postgres.port,
            dbname=postgres.database,
            user=postgres.user,
            password=password,
            sslmode=postgres.sslmode,
            connect_timeout=postgres.connect_timeout_seconds,
            application_name=LOVE_POSTGRESQL_APPLICATION_NAME,
        )
        _prepare_postgresql_schema(connection, postgres)
        authority_store = DbApiContextRevisionAuthorityStore(
            connection,  # type: ignore[arg-type]
            SqlContextStorePolicy(paramstyle="format", auto_commit=True),
        )
        authority_store.initialize_schema()
        scheduler_command_store = DbApiGitHubResearchSchedulerCommandStore(
            connection,  # type: ignore[arg-type]
            SqlContextStorePolicy(paramstyle="format", auto_commit=True),
        )
        scheduler_command_store.initialize_schema()
        scheduler_task_launch_transaction = DbApiSchedulerTaskLaunchTransaction(
            connection,  # type: ignore[arg-type]
            paramstyle="format",
        )
        scheduler_task_launch_transaction.initialize_schema()
        scheduler_handler_execution_transaction = (
            DbApiSchedulerHandlerExecutionTransaction(
                connection,  # type: ignore[arg-type]
                paramstyle="format",
            )
        )
        scheduler_handler_execution_transaction.initialize_schema()
        seed = ensure_love_base_revision(authority_store, settings)
    except LovePostgreSqlAuthorityBindingError:
        _close_connection_quietly(connection)
        raise
    except Exception as exc:  # noqa: BLE001 - never expose driver secrets
        _close_connection_quietly(connection)
        raise LovePostgreSqlAuthorityBindingError(
            "PostgreSQL authority binding failed "
            f"({type(exc).__name__})"
        ) from None

    receipt = LovePostgreSqlAuthorityBindingReceipt(
        schema=LOVE_POSTGRESQL_AUTHORITY_BINDING_SCHEMA,
        runtime_ref=settings.runtime_ref,
        sql_authority_ref=settings.sql_authority_ref,
        host=postgres.host,
        port=postgres.port,
        database=postgres.database,
        user=postgres.user,
        schema_name=postgres.schema_name,
        driver="psycopg",
        seed=seed,
        boundaries={
            "db_api_authority_reused": True,
            "postgresql_connection_owned": True,
            "schema_initialized_idempotently": True,
            "base_revision_seeded_idempotently": True,
            "scheduler_command_store_bound": True,
            "scheduler_command_storage_is_relational": True,
            "scheduler_command_json_storage_used": False,
            "scheduler_task_launch_transaction_bound": True,
            "scheduler_task_launch_schema_initialized": True,
            "scheduler_task_launch_uses_owned_connection": True,
            "scheduler_task_launch_handler_executed": False,
            "scheduler_handler_execution_transaction_bound": True,
            "scheduler_handler_execution_schema_initialized": True,
            "scheduler_handler_execution_uses_owned_connection": True,
            "scheduler_handler_execution_replayed": False,
            "shared_adapter_port_bound": True,
            "shared_adapter_port_uses_owned_connection": True,
            "secret_value_serialized": False,
            "scheduler_constructed": False,
            "openvino_inference_performed": False,
            "qdrant_write_performed": False,
        },
    )
    shared_adapter_port = LovePostgreSqlSharedAdapterPort(
        schema=LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
        sql_authority_ref=settings.sql_authority_ref,
        paramstyle="format",
        _connection=connection,
    )
    return LovePostgreSqlAuthorityBinding(
        authority_store=authority_store,
        shared_adapter_port=shared_adapter_port,
        scheduler_command_store=scheduler_command_store,
        scheduler_task_launch_transaction=(
            scheduler_task_launch_transaction
        ),
        scheduler_handler_execution_transaction=(
            scheduler_handler_execution_transaction
        ),
        receipt=receipt,
    )


def _load_psycopg_connector() -> Callable[..., object]:
    try:
        module = importlib.import_module("psycopg")
    except Exception as exc:  # noqa: BLE001 - optional runtime dependency
        raise LovePostgreSqlAuthorityBindingError(
            "psycopg is required for the installed PostgreSQL authority "
            f"({type(exc).__name__})"
        ) from None
    connect = getattr(module, "connect", None)
    if not callable(connect):
        raise LovePostgreSqlAuthorityBindingError(
            "psycopg.connect is not callable"
        )
    return connect


def _prepare_postgresql_schema(
    connection: object,
    settings: PostgreSqlRuntimeSettings,
) -> None:
    identifier = _quoted_identifier(settings.schema_name)
    cursor_factory = getattr(connection, "cursor", None)
    if not callable(cursor_factory):
        raise LovePostgreSqlAuthorityBindingError(
            "PostgreSQL connection must expose cursor()"
        )
    cursor = cursor_factory()
    try:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {identifier}")
        cursor.execute(f"SET search_path TO {identifier}")
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()
    commit = getattr(connection, "commit", None)
    if not callable(commit):
        raise LovePostgreSqlAuthorityBindingError(
            "PostgreSQL connection must expose commit()"
        )
    commit()


def _quoted_identifier(value: str) -> str:
    normalized = value.strip()
    if not _IDENTIFIER_RE.fullmatch(normalized):
        raise LovePostgreSqlAuthorityBindingError(
            "PostgreSQL schema must be a lowercase SQL identifier"
        )
    return f'"{normalized}"'


def _close_connection_quietly(connection: object | None) -> None:
    if connection is None:
        return
    close = getattr(connection, "close", None)
    if callable(close):
        try:
            close()
        except Exception:  # noqa: BLE001 - preserve original sanitized error
            pass


__all__ = (
    "LOVE_BASE_REVISION_CREATED_AT",
    "LOVE_POSTGRESQL_APPLICATION_NAME",
    "LOVE_POSTGRESQL_AUTHORITY_BINDING_SCHEMA",
    "LOVE_POSTGRESQL_BASE_REVISION_SEED_SCHEMA",
    "DbApiConnector",
    "LovePostgreSqlAuthorityBinding",
    "LovePostgreSqlAuthorityBindingError",
    "LovePostgreSqlAuthorityBindingReceipt",
    "LovePostgreSqlSharedAdapterPort",
    "LovePostgreSqlBaseRevisionSeedReceipt",
    "build_love_base_revision",
    "ensure_love_base_revision",
    "open_love_postgresql_authority",
)
