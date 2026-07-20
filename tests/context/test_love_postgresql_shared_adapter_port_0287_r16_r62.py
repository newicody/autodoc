from __future__ import annotations

import pytest

from context.love_postgresql_shared_adapter_port_0287 import (
    LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
    LovePostgreSqlSharedAdapterPort,
    LovePostgreSqlSharedAdapterPortError,
)


class Connection:
    def cursor(self):
        return object()

    def commit(self) -> None:
        pass

    def close(self) -> None:
        pass


class MinimalConnection:
    autocommit = False


class Adapter:
    def __init__(self, connection: object, *, paramstyle: str) -> None:
        self.connection = connection
        self.paramstyle = paramstyle
        self.initialized = 0

    def initialize_schema(self) -> None:
        self.initialized += 1

    def append_many(self, values: object) -> None:
        del values


def _port(connection: object) -> LovePostgreSqlSharedAdapterPort:
    return LovePostgreSqlSharedAdapterPort(
        schema=LOVE_POSTGRESQL_SHARED_ADAPTER_PORT_SCHEMA,
        sql_authority_ref="sql-authority:test",
        paramstyle="format",
        _connection=connection,
    )


def test_shared_port_accepts_lightweight_connection_until_adapter_use() -> None:
    port = _port(MinimalConnection())
    assert port.to_mapping()[
        "connection_capabilities_checked_on_adapter_build"
    ] is True


def test_shared_port_fails_when_requested_connection_capability_is_absent() -> None:
    port = _port(MinimalConnection())
    with pytest.raises(
        LovePostgreSqlSharedAdapterPortError,
        match=r"cursor\(\)",
    ):
        port.build_adapter(
            Adapter,
            required_connection_methods=("cursor", "commit"),
        )


def test_shared_port_reuses_exact_connection_and_initializes_once() -> None:
    connection = Connection()
    port = _port(connection)
    adapter = port.build_adapter(
        Adapter,
        required_methods=("initialize_schema", "append_many"),
        required_connection_methods=("cursor", "commit"),
        initialize_schema=True,
    )
    assert isinstance(adapter, Adapter)
    assert adapter.connection is connection
    assert adapter.paramstyle == "format"
    assert adapter.initialized == 1
    assert port.to_mapping()["raw_connection_exposed"] is False
    assert port.to_mapping()["second_connection_opened"] is False
