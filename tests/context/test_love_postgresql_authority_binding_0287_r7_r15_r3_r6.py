from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
    ManualInstalledRuntimeSettings,
    OpenVINORuntimeSettings,
    PostgreSqlRuntimeSettings,
    QdrantRuntimeSettings,
)
from context.love_postgresql_authority_binding_0287 import (  # noqa: E402
    LovePostgreSqlAuthorityBindingError,
    ensure_love_base_revision,
    open_love_postgresql_authority,
)


class _Cursor:
    def __init__(self, inner: sqlite3.Cursor) -> None:
        self._inner = inner

    def execute(self, sql: str, parameters=()):
        normalized = " ".join(sql.split()).upper()
        if normalized.startswith("CREATE SCHEMA IF NOT EXISTS"):
            return self
        if normalized.startswith("SET SEARCH_PATH TO"):
            return self
        self._inner.execute(sql.replace("%s", "?"), tuple(parameters))
        return self

    def fetchone(self):
        return self._inner.fetchone()

    def fetchall(self):
        return self._inner.fetchall()

    def close(self) -> None:
        self._inner.close()


class _Connection:
    def __init__(self) -> None:
        self._inner = sqlite3.connect(":memory:")
        self.closed = False

    def cursor(self) -> _Cursor:
        return _Cursor(self._inner.cursor())

    def commit(self) -> None:
        self._inner.commit()

    def rollback(self) -> None:
        self._inner.rollback()

    def close(self) -> None:
        if not self.closed:
            self._inner.close()
            self.closed = True


class _Connector:
    def __init__(self, connection: _Connection) -> None:
        self.connection = connection
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> _Connection:
        self.calls.append(dict(kwargs))
        return self.connection


def _settings(*, schema_name: str = "autodoc") -> ManualInstalledRuntimeSettings:
    return ManualInstalledRuntimeSettings(
        schema=MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
        config_path="/tmp/love-installed-runtime.ini",
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle="tool-bounded",
        sql_authority_ref="sql-authority:context-revisions",
        projection_backend_ref="projection:context-revision-sql-authority",
        embedding_backend_ref="openvino:multilingual-e5-small",
        retrieval_backend_ref="qdrant:local",
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
        base_revision_ref="context-revision:love-base",
        postgresql=PostgreSqlRuntimeSettings(
            host="127.0.0.1",
            port=5432,
            database="autodoc",
            user="autodoc",
            password_env="AUTODOC_POSTGRES_PASSWORD",
            sslmode="disable",
            schema_name=schema_name,
            connect_timeout_seconds=5,
        ),
        qdrant=QdrantRuntimeSettings(
            url="http://127.0.0.1:6333",
            grpc_port=6334,
            api_key_env="",
            collection="autodoc_context_current",
            vector_name="",
            dimension=384,
            distance="Cosine",
        ),
        openvino=OpenVINORuntimeSettings(
            model_dir="/models/e5",
            model_xml="/models/e5/openvino_model.xml",
            device="CPU",
            dimension=384,
            query_prefix="query:",
            passage_prefix="passage:",
        ),
    )


def test_opens_existing_db_api_authority_and_seeds_base_revision() -> None:
    connection = _Connection()
    connector = _Connector(connection)

    binding = open_love_postgresql_authority(
        _settings(),
        connector=connector,
        environment={"AUTODOC_POSTGRES_PASSWORD": "not-serialized"},
    )

    assert binding.authority_store.get_revision(
        "context-revision:love-base"
    ) is not None
    assert binding.receipt.seed.inserted is True
    assert binding.receipt.seed.idempotent_replay is False
    assert connector.calls == [
        {
            "host": "127.0.0.1",
            "port": 5432,
            "dbname": "autodoc",
            "user": "autodoc",
            "password": "not-serialized",
            "sslmode": "disable",
            "connect_timeout": 5,
            "application_name": "autodoc-love-runtime",
        }
    ]

    public = binding.receipt.to_mapping()
    assert "not-serialized" not in repr(public)
    assert public["postgresql"]["secret_value_serialized"] is False
    assert public["boundaries"]["qdrant_write_performed"] is False
    assert public["boundaries"]["openvino_inference_performed"] is False

    binding.close()
    binding.close()
    assert binding.closed is True
    assert connection.closed is True


def test_base_revision_seed_is_idempotent_on_same_authority() -> None:
    binding = open_love_postgresql_authority(
        _settings(),
        connector=_Connector(_Connection()),
        environment={"AUTODOC_POSTGRES_PASSWORD": "secret"},
    )

    replay = ensure_love_base_revision(binding.authority_store, _settings())

    assert replay.inserted is False
    assert replay.idempotent_replay is True
    binding.close()


def test_missing_password_fails_before_connector_is_called() -> None:
    connector = _Connector(_Connection())

    with pytest.raises(
        LovePostgreSqlAuthorityBindingError,
        match="AUTODOC_POSTGRES_PASSWORD",
    ):
        open_love_postgresql_authority(
            _settings(),
            connector=connector,
            environment={},
        )

    assert connector.calls == []


def test_driver_error_is_sanitized_and_connection_is_not_leaked() -> None:
    secret = "do-not-expose"

    def failing_connector(**kwargs: object) -> object:
        raise RuntimeError(f"password={kwargs['password']}")

    with pytest.raises(LovePostgreSqlAuthorityBindingError) as captured:
        open_love_postgresql_authority(
            _settings(),
            connector=failing_connector,
            environment={"AUTODOC_POSTGRES_PASSWORD": secret},
        )

    assert secret not in str(captured.value)
    assert secret not in repr(captured.value)


def test_postgresql_schema_identifier_fails_closed() -> None:
    connection = _Connection()

    with pytest.raises(
        LovePostgreSqlAuthorityBindingError,
        match="lowercase SQL identifier",
    ):
        open_love_postgresql_authority(
            _settings(schema_name="autodoc;drop"),
            connector=_Connector(connection),
            environment={"AUTODOC_POSTGRES_PASSWORD": "secret"},
        )

    assert connection.closed is True
