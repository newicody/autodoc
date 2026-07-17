from __future__ import annotations

from dataclasses import replace
import os
from types import SimpleNamespace

import pytest

from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimeLease,
)
from context.love_installed_runtime_factory_0287 import (
    INSTALLED_RUNTIME_FACTORY_SCHEMA,
    InstalledRuntimeFactorySettings,
)
from context.love_manual_runtime_configuration_0287 import (
    MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
    ManualInstalledRuntimeSettings,
    OpenVINORuntimeSettings,
    PostgreSqlRuntimeSettings,
    QdrantRuntimeSettings,
)
import context.love_tool_bounded_installed_runtime_composer_0287 as composer


class _AuthorityStore:
    def get_revision(self, revision_ref): return None
    def put_object(self, value): return value
    def put_artifact(self, value): return value
    def put_revision(self, value): return value
    def put_projection(self, value): return value
    def put_relation(self, value): return value


class _PostgresBinding:
    def __init__(self, close_order):
        self.authority_store = _AuthorityStore()
        self._close_order = close_order

    def close(self):
        self._close_order.append("postgresql")


class _Pipeline:
    async def embed_text(self, text):
        return SimpleNamespace(
            values=(1.0,) + (0.0,) * 383,
            dimension=384,
            normalized=True,
        )


class _QdrantExecutor:
    def __init__(self, close_order):
        self._close_order = close_order

    def close(self):
        self._close_order.append("qdrant")

    def upsert_named_hybrid_point(self, **kwargs):
        return SimpleNamespace(acknowledged=True)

    def query_named_dense(self, *args, **kwargs):
        return ()

    def query_named_sparse(self, *args, **kwargs):
        return ()


def _factory_settings() -> InstalledRuntimeFactorySettings:
    return InstalledRuntimeFactorySettings(
        schema=INSTALLED_RUNTIME_FACTORY_SCHEMA,
        config_path="/tmp/love-installed-runtime.ini",
        provider_ref=(
            "context.love_tool_bounded_installed_runtime_composer_0287:"
            "build_tool_bounded_installed_runtime"
        ),
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle="tool-bounded",
        sql_authority_ref="sql-authority:context-revisions",
        projection_backend_ref="projection:qdrant-live",
        embedding_backend_ref="openvino:multilingual-e5-small",
        retrieval_backend_ref="qdrant:local",
        model_ref="model:multilingual-e5-small",
        model_revision="installed",
        qdrant_collection="autodoc_context_e5_384_hybrid_v1",
        base_revision_ref="context-revision:love-base",
        evidence_refs=("evidence:installed-runtime",),
        embedding_dimension=384,
    )


def _manual_settings() -> ManualInstalledRuntimeSettings:
    return ManualInstalledRuntimeSettings(
        schema=MANUAL_RUNTIME_CONFIGURATION_SCHEMA,
        config_path="/tmp/love-installed-runtime.ini",
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle="tool-bounded",
        sql_authority_ref="sql-authority:context-revisions",
        projection_backend_ref="projection:qdrant-live",
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
        ),
        qdrant=QdrantRuntimeSettings(
            url="http://127.0.0.1:6333",
            grpc_port=6334,
            api_key_env="",
            collection="autodoc_context_current",
            vector_name="",
            dimension=384,
            distance="Cosine",
            physical_collection="autodoc_context_e5_384_hybrid_v1",
            collection_alias="autodoc_context_hybrid_current",
            dense_vector_name="dense_e5_v1",
            sparse_vector_name="sparse_lexical_v1",
            named_vectors_enabled=True,
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


def test_composer_builds_one_tool_bounded_lease_and_closes_reverse(monkeypatch) -> None:
    close_order = []
    fake_qdrant = _QdrantExecutor(close_order)

    monkeypatch.setattr(
        composer,
        "load_manual_installed_runtime_settings",
        lambda path: _manual_settings(),
    )
    monkeypatch.setattr(
        composer,
        "open_love_postgresql_authority",
        lambda manual, environment: _PostgresBinding(close_order),
    )
    monkeypatch.setattr(
        composer,
        "build_multilingual_e5_small_pipeline",
        lambda config: SimpleNamespace(pipeline=_Pipeline()),
    )
    monkeypatch.setattr(
        composer,
        "build_qdrant_client_projection_executor",
        lambda config, gate, api_key=None: fake_qdrant,
    )

    lease = composer.build_tool_bounded_installed_runtime(
        repository="newicody/projects",
        run_id="29255262261",
        request_payload={},
        runtime_context={"policy_decision_id": "policy:live-runtime-test"},
        created_at="2026-07-17T00:00:00Z",
        settings=_factory_settings(),
        environment={
            "AUTODOC_POSTGRES_PASSWORD": "secret",
            composer.QDRANT_POINT_WRITE_GATE_ENV: "true",
            composer.QDRANT_SEARCH_GATE_ENV: "true",
        },
    )

    assert isinstance(lease, ImportedActionsRuntimeLease)
    assert lease.ports.scheduler_lifecycle == "tool-bounded"
    assert lease.ports.collection.collection_name == (
        "autodoc_context_e5_384_hybrid_v1"
    )
    assert lease.ports.collection.vector("dense_e5_v1").dimension == 384
    assert lease.ports.collection.vector("sparse_lexical_v1").dimension is None
    assert [hook.hook_ref for hook in lease.close_hooks] == [
        "runtime-close:postgresql-authority",
        "runtime-close:qdrant-client",
    ]

    receipt = lease.close(current_process_id=os.getpid())
    assert receipt.valid
    assert close_order == ["qdrant", "postgresql"]
    replay = lease.close(current_process_id=os.getpid())
    assert replay.action == "replay"
    assert close_order == ["qdrant", "postgresql"]


def test_composer_requires_separate_write_and_search_gates(monkeypatch) -> None:
    monkeypatch.setattr(
        composer,
        "load_manual_installed_runtime_settings",
        lambda path: _manual_settings(),
    )
    with pytest.raises(
        composer.ToolBoundedInstalledRuntimeComposerError,
        match="write gate",
    ):
        composer.build_tool_bounded_installed_runtime(
            repository="newicody/projects",
            run_id="1",
            request_payload={},
            runtime_context={"policy_decision_id": "policy:test"},
            created_at="2026-07-17T00:00:00Z",
            settings=_factory_settings(),
            environment={composer.QDRANT_SEARCH_GATE_ENV: "true"},
        )

    with pytest.raises(
        composer.ToolBoundedInstalledRuntimeComposerError,
        match="search gate",
    ):
        composer.build_tool_bounded_installed_runtime(
            repository="newicody/projects",
            run_id="1",
            request_payload={},
            runtime_context={"policy_decision_id": "policy:test"},
            created_at="2026-07-17T00:00:00Z",
            settings=_factory_settings(),
            environment={composer.QDRANT_POINT_WRITE_GATE_ENV: "true"},
        )


def test_composer_rejects_external_scheduler_lifecycle(monkeypatch) -> None:
    manual = replace(_manual_settings(), scheduler_lifecycle="externally-managed")
    monkeypatch.setattr(
        composer,
        "load_manual_installed_runtime_settings",
        lambda path: manual,
    )
    with pytest.raises(
        composer.ToolBoundedInstalledRuntimeComposerError,
        match="scheduler_lifecycle",
    ):
        composer.build_tool_bounded_installed_runtime(
            repository="newicody/projects",
            run_id="1",
            request_payload={},
            runtime_context={"policy_decision_id": "policy:test"},
            created_at="2026-07-17T00:00:00Z",
            settings=_factory_settings(),
            environment={
                composer.QDRANT_POINT_WRITE_GATE_ENV: "true",
                composer.QDRANT_SEARCH_GATE_ENV: "true",
            },
        )
