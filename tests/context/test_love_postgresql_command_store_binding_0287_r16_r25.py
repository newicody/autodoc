from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

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


def _settings() -> ManualInstalledRuntimeSettings:
    return ManualInstalledRuntimeSettings(
        schema=MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
        config_path="/tmp/love-installed-runtime.ini",
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle="externally-managed",
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
            schema_name="autodoc",
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


def test_installed_postgresql_binding_reuses_connection_for_command_store() -> None:
    connection = _Connection()
    binding = open_love_postgresql_authority(
        _settings(),
        connector=lambda **_kwargs: connection,
        environment={"AUTODOC_POSTGRES_PASSWORD": "secret"},
    )
    assert binding.scheduler_command_store is not None
    assert binding.receipt.boundaries["scheduler_command_store_bound"] is True
    assert (
        binding.receipt.boundaries["scheduler_command_json_storage_used"]
        is False
    )
    binding.close()
    assert connection.closed is True
