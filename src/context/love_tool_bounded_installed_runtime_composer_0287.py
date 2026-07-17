"""Tool-bounded installed PostgreSQL/OpenVINO/Qdrant runtime composition.

This is the concrete provider for one command invocation. It constructs exactly
one canonical Scheduler stack, opens the existing PostgreSQL authority binding,
builds the installed multilingual-E5 pipeline and opens one qdrant-client
executor. The returned process-local lease owns only the PostgreSQL and Qdrant
close effects.

The Scheduler remains the sole orchestrator. No laboratory manager, second
scheduler, service thread, event-loop runner, outbound mutation adapter or fallback
backend is introduced here.
"""

from __future__ import annotations

from collections.abc import Mapping
import os
from types import MappingProxyType
from typing import Any, TYPE_CHECKING

from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
    ImportedActionsRealBackendAttestation,
    ImportedActionsRuntimeCloseHook,
    ImportedActionsRuntimeLease,
    ImportedActionsRuntimePorts,
)
from context.love_manual_runtime_configuration_0287 import (
    ManualInstalledRuntimeSettings,
    load_manual_installed_runtime_settings,
)
from context.love_openvino_e5_async_query_adapter_0287 import (
    LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA,
    LoveOpenVinoE5AsyncQueryAdapterSettings,
    build_love_openvino_e5_async_query_embedder,
)
from context.love_postgresql_authority_binding_0287 import (
    LovePostgreSqlAuthorityBinding,
    open_love_postgresql_authority,
)
from context.love_qdrant_hybrid_query_adapter_0287 import (
    build_love_qdrant_hybrid_query_adapter,
)
from context.love_qdrant_live_analysis_projection_0287 import (
    LoveQdrantLiveAnalysisProjection,
    LoveQdrantLiveAnalysisProjectionSettings,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)
from inference.e5_pipeline import (
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from inference.e5_profile import MultilingualE5SmallLocalConfig
from inference.qdrant_client_projection_executor import (
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    QdrantClientProjectionExecutor,
    build_qdrant_client_projection_executor,
)
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler

if TYPE_CHECKING:
    from context.love_installed_runtime_factory_0287 import (
        InstalledRuntimeFactorySettings,
    )

TOOL_BOUNDED_INSTALLED_RUNTIME_COMPOSER_SCHEMA = (
    "missipy.love.tool_bounded_installed_runtime_composer.v1"
)
QDRANT_POINT_WRITE_GATE_ENV = "AUTODOC_QDRANT_POINT_WRITE_ALLOWED"
QDRANT_SEARCH_GATE_ENV = "AUTODOC_QDRANT_SEARCH_ALLOWED"


class ToolBoundedInstalledRuntimeComposerError(RuntimeError):
    """Raised when the concrete installed runtime cannot fail closed."""


def _flag(environment: Mapping[str, str], name: str) -> bool:
    return str(environment.get(name, "")).strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _required_policy_decision_id(runtime_context: Mapping[str, object]) -> str:
    value = str(runtime_context.get("policy_decision_id", "")).strip()
    if not value.startswith("policy:"):
        raise ToolBoundedInstalledRuntimeComposerError(
            "runtime_context policy_decision_id must be a typed policy reference"
        )
    return value


def _validate_alignment(
    factory_settings: "InstalledRuntimeFactorySettings",
    manual: ManualInstalledRuntimeSettings,
) -> None:
    expected = {
        "runtime_ref": factory_settings.runtime_ref,
        "scheduler_ref": factory_settings.scheduler_ref,
        "scheduler_lifecycle": factory_settings.scheduler_lifecycle,
        "sql_authority_ref": factory_settings.sql_authority_ref,
        "projection_backend_ref": factory_settings.projection_backend_ref,
        "embedding_backend_ref": factory_settings.embedding_backend_ref,
        "retrieval_backend_ref": factory_settings.retrieval_backend_ref,
        "model_ref": factory_settings.model_ref,
        "model_revision": factory_settings.model_revision,
        "base_revision_ref": factory_settings.base_revision_ref,
    }
    for name, value in expected.items():
        if getattr(manual, name) != value:
            raise ToolBoundedInstalledRuntimeComposerError(
                f"manual runtime {name} differs from factory attestation"
            )
    if factory_settings.scheduler_lifecycle != "tool-bounded":
        raise ToolBoundedInstalledRuntimeComposerError(
            "installed runtime composer requires scheduler lifecycle tool-bounded"
        )
    if not manual.qdrant.named_vectors_enabled:
        raise ToolBoundedInstalledRuntimeComposerError(
            "installed runtime composer requires named Qdrant vectors"
        )
    if manual.qdrant.physical_collection != factory_settings.qdrant_collection:
        raise ToolBoundedInstalledRuntimeComposerError(
            "physical Qdrant collection differs from factory attestation"
        )
    if manual.qdrant.dimension != 384 or manual.openvino.dimension != 384:
        raise ToolBoundedInstalledRuntimeComposerError(
            "installed E5/Qdrant composition must use dimension 384"
        )


def _build_collection(
    manual: ManualInstalledRuntimeSettings,
) -> QdrantCollectionProfile:
    dense = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=manual.qdrant.dense_vector_name,
        vector_kind="dense",
        embedding_profile_ref=(
            "embedding-profile:multilingual-e5-small-passage"
        ),
        model_ref=manual.model_ref,
        model_revision=manual.model_revision,
        dimension=384,
        distance="Cosine",
        normalized=True,
        hnsw_enabled=True,
        metadata={
            "backend_ref": manual.embedding_backend_ref,
            "role": "passage",
        },
    )
    sparse = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=manual.qdrant.sparse_vector_name,
        vector_kind="sparse",
        embedding_profile_ref="embedding-profile:sparse-lexical-v1",
        model_ref="model:sparse-lexical-v1",
        model_revision="v1",
        dimension=None,
        distance=None,
        normalized=None,
        hnsw_enabled=False,
        metadata={
            "backend_ref": "sparse:lexical-v1",
            "role": "passage",
        },
    )
    return QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref="qdrant-profile:love-hybrid-v1",
        collection_name=manual.qdrant.physical_collection,
        collection_alias=manual.qdrant.collection_alias,
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(dense, sparse),
        payload_indexes=build_canonical_payload_indexes(),
        metadata={
            "legacy_collection": manual.qdrant.collection,
            "composer_schema": TOOL_BOUNDED_INSTALLED_RUNTIME_COMPOSER_SCHEMA,
        },
    )


def _build_scheduler_stack() -> tuple[Scheduler, Dispatcher]:
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        event_bus,
        Registry(),
    )
    return scheduler, dispatcher


def _build_attestation(
    settings: "InstalledRuntimeFactorySettings",
) -> ImportedActionsRealBackendAttestation:
    return ImportedActionsRealBackendAttestation(
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
        embedding_dimension=384,
        scheduler_contract_reused=True,
        sql_authority_reused=True,
        openvino_e5_real=True,
        qdrant_write_real=True,
        qdrant_returns_references_only=True,
    )


def build_tool_bounded_installed_runtime(
    *,
    repository: str,
    run_id: str,
    request_payload: Mapping[str, object],
    runtime_context: Mapping[str, object],
    created_at: str,
    settings: "InstalledRuntimeFactorySettings",
    environment: Mapping[str, str] | None = None,
) -> ImportedActionsRuntimeLease:
    """Compose one process-local real runtime lease for the imported run."""

    del request_payload, created_at
    if "/" not in repository:
        raise ToolBoundedInstalledRuntimeComposerError(
            "repository must use owner/name"
        )
    if not str(run_id).strip():
        raise ToolBoundedInstalledRuntimeComposerError(
            "run_id must be non-empty"
        )

    env = os.environ if environment is None else environment
    manual = load_manual_installed_runtime_settings(settings.config_path)
    _validate_alignment(settings, manual)
    policy_decision_id = _required_policy_decision_id(runtime_context)

    allow_write = _flag(env, QDRANT_POINT_WRITE_GATE_ENV)
    allow_search = _flag(env, QDRANT_SEARCH_GATE_ENV)
    if not allow_write:
        raise ToolBoundedInstalledRuntimeComposerError(
            f"missing explicit Qdrant write gate {QDRANT_POINT_WRITE_GATE_ENV}"
        )
    if not allow_search:
        raise ToolBoundedInstalledRuntimeComposerError(
            f"missing explicit Qdrant search gate {QDRANT_SEARCH_GATE_ENV}"
        )

    scheduler, dispatcher = _build_scheduler_stack()
    postgres_binding: LovePostgreSqlAuthorityBinding | None = None
    qdrant_executor: QdrantClientProjectionExecutor | None = None
    try:
        postgres_binding = open_love_postgresql_authority(
            manual,
            environment=env,
        )
        local = MultilingualE5SmallLocalConfig(
            model_dir=manual.openvino.model_dir,
            device=manual.openvino.device,
        )
        pipeline_bundle = build_multilingual_e5_small_pipeline(
            MultilingualE5SmallPipelineConfig(
                local=local,
                require_model_exists=True,
                metadata=MappingProxyType(
                    {
                        "runtime_ref": manual.runtime_ref,
                        "composer_schema": (
                            TOOL_BOUNDED_INSTALLED_RUNTIME_COMPOSER_SCHEMA
                        ),
                    }
                ),
            )
        )
        api_key = (
            str(env.get(manual.qdrant.api_key_env, "")).strip()
            if manual.qdrant.api_key_env
            else ""
        )
        qdrant_executor = build_qdrant_client_projection_executor(
            QdrantClientConnectionConfig(
                url=manual.qdrant.url,
                timeout_seconds=manual.qdrant.timeout_seconds,
                prefer_grpc=False,
                grpc_port=manual.qdrant.grpc_port,
                wait_for_write=True,
                check_compatibility=True,
            ),
            QdrantClientEffectGate(
                policy_decision_id=policy_decision_id,
                allow_write=True,
                allow_search=True,
            ),
            api_key=api_key or None,
        )
        collection = _build_collection(manual)
        projection_port = LoveQdrantLiveAnalysisProjection(
            pipeline=pipeline_bundle.pipeline,
            writer=qdrant_executor,
            settings=LoveQdrantLiveAnalysisProjectionSettings(
                collection_name=manual.qdrant.physical_collection,
                dense_vector_name=manual.qdrant.dense_vector_name,
                sparse_vector_name=manual.qdrant.sparse_vector_name,
                model_ref=manual.model_ref,
                model_revision=manual.model_revision,
                backend_ref=manual.embedding_backend_ref,
                passage_prefix=manual.openvino.passage_prefix,
                dimension=384,
            ),
        )
        embedder = build_love_openvino_e5_async_query_embedder(
            pipeline=pipeline_bundle.pipeline,
            settings=LoveOpenVinoE5AsyncQueryAdapterSettings(
                schema=LOVE_OPENVINO_E5_ASYNC_QUERY_ADAPTER_SCHEMA,
                model_ref=manual.model_ref,
                model_revision=manual.model_revision,
                backend_ref=manual.embedding_backend_ref,
                query_prefix=manual.openvino.query_prefix,
                dimension=384,
            ),
        )
        executor = build_love_qdrant_hybrid_query_adapter(qdrant_executor)
        ports = ImportedActionsRuntimePorts(
            schema=IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
            runtime_ref=manual.runtime_ref,
            scheduler=scheduler,
            dispatcher=dispatcher,
            authority_store=postgres_binding.authority_store,
            projection_port=projection_port,
            collection=collection,
            embedder=embedder,
            executor=executor,
            base_revision_ref=manual.base_revision_ref,
            scheduler_lifecycle="tool-bounded",
            attestation=_build_attestation(settings),
        )
        return ImportedActionsRuntimeLease(
            schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
            ports=ports,
            owner_ref=f"runtime-owner:love-actions-run-{run_id}",
            process_id=os.getpid(),
            close_hooks=(
                ImportedActionsRuntimeCloseHook(
                    schema=IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA,
                    hook_ref="runtime-close:postgresql-authority",
                    callback=postgres_binding.close,
                ),
                ImportedActionsRuntimeCloseHook(
                    schema=IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA,
                    hook_ref="runtime-close:qdrant-client",
                    callback=qdrant_executor.close,
                ),
            ),
        )
    except Exception:
        if qdrant_executor is not None:
            try:
                qdrant_executor.close()
            except Exception:
                pass
        if postgres_binding is not None:
            try:
                postgres_binding.close()
            except Exception:
                pass
        raise


__all__ = (
    "QDRANT_POINT_WRITE_GATE_ENV",
    "QDRANT_SEARCH_GATE_ENV",
    "TOOL_BOUNDED_INSTALLED_RUNTIME_COMPOSER_SCHEMA",
    "ToolBoundedInstalledRuntimeComposerError",
    "build_tool_bounded_installed_runtime",
)
