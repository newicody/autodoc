from __future__ import annotations

from types import SimpleNamespace

import context.love_installed_runtime_factory_0287 as factory
from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
    ImportedActionsRealBackendAttestation,
    ImportedActionsRuntimeLease,
    ImportedActionsRuntimePorts,
)
from context.love_installed_runtime_factory_0287 import (
    INSTALLED_RUNTIME_FACTORY_SCHEMA,
    InstalledRuntimeFactorySettings,
)
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


class _Authority:
    def get_revision(self, ref): return None
    def put_object(self, value): return value
    def put_artifact(self, value): return value
    def put_revision(self, value): return value
    def put_projection(self, value): return value
    def put_relation(self, value): return value


class _Projection:
    async def project(self, *args, **kwargs): return None


class _Embedder:
    async def embed_query(self, *args, **kwargs): return None


class _Executor:
    def search_dense(self, *args, **kwargs): return ()
    def search_sparse(self, *args, **kwargs): return ()


def _settings() -> InstalledRuntimeFactorySettings:
    return InstalledRuntimeFactorySettings(
        schema=INSTALLED_RUNTIME_FACTORY_SCHEMA,
        config_path="/tmp/runtime.ini",
        provider_ref="provider:factory",
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
        evidence_refs=("evidence:runtime",),
    )


def _lease() -> ImportedActionsRuntimeLease:
    settings = _settings()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, Registry())
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
        scheduler_lifecycle="tool-bounded",
    )
    ports = ImportedActionsRuntimePorts(
        schema=IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
        runtime_ref=settings.runtime_ref,
        scheduler=scheduler,
        dispatcher=dispatcher,
        authority_store=_Authority(),
        projection_port=_Projection(),
        collection=SimpleNamespace(
            collection_name=settings.qdrant_collection
        ),
        embedder=_Embedder(),
        executor=_Executor(),
        base_revision_ref=settings.base_revision_ref,
        scheduler_lifecycle="tool-bounded",
        attestation=attestation,
    )
    return ImportedActionsRuntimeLease(
        schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
        ports=ports,
        owner_ref="runtime-owner:test",
        process_id=1,
    )


def test_factory_preserves_provider_owned_lease(monkeypatch) -> None:
    lease = _lease()
    monkeypatch.setattr(
        factory,
        "load_installed_runtime_factory_settings",
        lambda: _settings(),
    )
    monkeypatch.setattr(factory, "_load_provider", lambda ref: lambda **kw: lease)

    result = factory.build_runtime(
        repository="newicody/projects",
        run_id="1",
        request_payload={},
        runtime_context={},
        created_at="2026-07-17T00:00:00Z",
    )

    assert result is lease


def test_factory_loads_physical_collection_when_present(tmp_path) -> None:
    path = tmp_path / "runtime.ini"
    path.write_text(
        """
[runtime]
runtime_ref = runtime:love-installed

[scheduler]
scheduler_ref = scheduler:main
lifecycle = tool-bounded

[sql]
authority_ref = sql-authority:context-revisions
base_revision_ref = context-revision:love-base

[projection]
backend_ref = projection:qdrant-live

[embedding]
backend_ref = openvino:multilingual-e5-small
model_ref = model:multilingual-e5-small
model_revision = installed
dimension = 384

[qdrant]
backend_ref = qdrant:local
collection = autodoc_context_current
physical_collection = autodoc_context_e5_384_hybrid_v1

[evidence]
refs = evidence:runtime
""".strip()
        + "\n",
        encoding="utf-8",
    )

    settings = factory.load_installed_runtime_factory_settings(path)

    assert settings.qdrant_collection == "autodoc_context_e5_384_hybrid_v1"
