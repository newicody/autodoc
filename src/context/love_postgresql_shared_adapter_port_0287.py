"""Typed adapter construction port over one owned PostgreSQL connection.

The authority binding owns and closes the DB-API connection. Durable adapters
receive that same connection through this narrow port; callers cannot fetch or
close the raw connection and no second PostgreSQL backend is opened.

Connection capabilities are checked only when an adapter explicitly requires
them. Creating the port therefore remains compatible with lightweight injected
test doubles that validate connection sharing without exercising SQL I/O.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import inspect
from types import MappingProxyType

LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA = (
    "missipy.love.postgresql_shared_adapter_port.v1"
)


class LovePostgreSqlSharedAdapterPortError(RuntimeError):
    """Raised when a durable adapter cannot share the owned SQL connection."""


@dataclass(frozen=True, slots=True)
class LovePostgreSqlSharedAdapterPort:
    """Build validated adapters on the connection owned by the SQL binding."""

    schema: str
    sql_authority_ref: str
    paramstyle: str
    _connection: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.schema != LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA:
            raise LovePostgreSqlSharedAdapterPortError(
                "schéma du port PostgreSQL partagé non pris en charge"
            )
        if not self.sql_authority_ref.startswith("sql-authority:"):
            raise LovePostgreSqlSharedAdapterPortError(
                "sql_authority_ref doit commencer par sql-authority:"
            )
        if self.paramstyle not in {"format", "qmark"}:
            raise LovePostgreSqlSharedAdapterPortError(
                "paramstyle doit être format ou qmark"
            )

    def build_adapter(
        self,
        factory: Callable[..., object],
        *,
        required_methods: Sequence[str] = (),
        required_connection_methods: Sequence[str] = (),
        initialize_schema: bool = False,
        keyword_arguments: Mapping[str, object] | None = None,
    ) -> object:
        """Build one adapter on the shared connection and validate its surface."""

        if not callable(factory):
            raise TypeError("factory doit être callable")
        self._validate_connection_methods(required_connection_methods)
        keywords = dict(keyword_arguments or {})
        keywords.setdefault("paramstyle", self.paramstyle)
        adapter = factory(
            self._connection,
            **_supported_keywords(factory, keywords),
        )
        for method_name in required_methods:
            if not callable(getattr(adapter, method_name, None)):
                raise LovePostgreSqlSharedAdapterPortError(
                    f"l'adaptateur doit exposer {method_name}()"
                )
        if initialize_schema:
            initializer = getattr(adapter, "initialize_schema", None)
            if not callable(initializer):
                raise LovePostgreSqlSharedAdapterPortError(
                    "initialize_schema demandé mais absent de l'adaptateur"
                )
            initializer()
        return adapter

    def _validate_connection_methods(
        self,
        method_names: Sequence[str],
    ) -> None:
        for method_name in method_names:
            if not isinstance(method_name, str) or not method_name.strip():
                raise LovePostgreSqlSharedAdapterPortError(
                    "chaque capacité DB-API requise doit être nommée"
                )
            if not callable(getattr(self._connection, method_name, None)):
                raise LovePostgreSqlSharedAdapterPortError(
                    f"la connexion DB-API doit exposer {method_name}()"
                )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "sql_authority_ref": self.sql_authority_ref,
                "paramstyle": self.paramstyle,
                "connection_owned_by_binding": True,
                "connection_capabilities_checked_on_adapter_build": True,
                "raw_connection_exposed": False,
                "second_connection_opened": False,
                "secret_value_serialized": False,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def _supported_keywords(
    factory: Callable[..., object],
    values: Mapping[str, object],
) -> dict[str, object]:
    try:
        signature = inspect.signature(factory)
    except (TypeError, ValueError):
        return dict(values)
    parameters = signature.parameters
    if any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    ):
        return dict(values)
    return {name: value for name, value in values.items() if name in parameters}


__all__ = (
    "LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA",
    "LovePostgreSqlSharedAdapterPort",
    "LovePostgreSqlSharedAdapterPortError",
)
