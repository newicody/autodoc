"""Open the real installed backend foundation for the OpenRC Scheduler service.

This module owns one process-local Scheduler stack and one set of installed
PostgreSQL/OpenVINO/Qdrant resources for the lifetime of the future OpenRC
process.  It does not build the ten handler providers or the durable
continuation pipeline: those remain a distinct composition step.

PostgreSQL stays the durable authority.  Qdrant stays a projection/recall
backend.  OpenVINO E5 stays an injected embedding backend.  No internal JSON
store, JSONL queue, second Scheduler, thread or child process is introduced.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
import os
from types import MappingProxyType
from typing import Any, TYPE_CHECKING

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
from context.love_postgresql_shared_adapter_port_0287 import (
    LovePostgreSqlSharedAdapterPort,
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

EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA = (
    "missipy.love.externally_managed_installed_backend_foundation.v1"
)
QDRANT_POINT_WRITE_GATE_ENV = "AUTODOC_QDRANT_POINT_WRITE_ALLOWED"
QDRANT_SEARCH_GATE_ENV = "AUTODOC_QDRANT_SEARCH_ALLOWED"
SERVICE_POLICY_DECISION_ENV = "AUTODOC_GITHUB_RESEARCH_SERVICE_POLICY_DECISION_ID"
DEFAULT_SERVICE_POLICY_DECISION_ID = "policy:openrc-github-research-scheduler"


class LoveExternallyManagedInstalledBackendFoundationError(RuntimeError):
    """Raised when the long-lived installed backend foundation cannot open."""


CloseCallback = Callable[[], object]


@dataclass(slots=True)
class LoveExternallyManagedInstalledBackendFoundation:
    """Owned real resources shared by the externally-managed composition."""

    schema: str
    scheduler: Scheduler = field(repr=False, compare=False)
    dispatcher: Dispatcher = field(repr=False, compare=False)
    scheduler_ref: str
    authority_store: object = field(repr=False, compare=False)
    postgresql_adapter_port: LovePostgreSqlSharedAdapterPort = field(
        repr=False,
        compare=False,
    )
    command_store: object = field(repr=False, compare=False)
    task_launch_transaction: object = field(repr=False, compare=False)
    handler_execution_transaction: object = field(repr=False, compare=False)
    projection_port: object = field(repr=False, compare=False)
    collection: QdrantCollectionProfile = field(repr=False, compare=False)
    embedder: object = field(repr=False, compare=False)
    retrieval_executor: object = field(repr=False, compare=False)
    base_revision_ref: str
    close_callbacks: tuple[CloseCallback, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "schéma de fondation externally-managed non pris en charge"
            )
        if not isinstance(self.scheduler, Scheduler):
            raise TypeError("scheduler doit être le Scheduler canonique")
        if not isinstance(self.dispatcher, Dispatcher):
            raise TypeError("dispatcher doit être le Dispatcher canonique")
        _typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        _typed_ref("base_revision_ref", self.base_revision_ref, "context-revision:")
        if not isinstance(
            self.postgresql_adapter_port,
            LovePostgreSqlSharedAdapterPort,
        ):
            raise TypeError(
                "postgresql_adapter_port doit être le port PostgreSQL partagé"
            )
        _method(self.command_store, "claim_next_pending")
        if self.task_launch_transaction is None:
            raise TypeError("task_launch_transaction est requis")
        if self.handler_execution_transaction is None:
            raise TypeError("handler_execution_transaction est requis")
        if not isinstance(self.collection, QdrantCollectionProfile):
            raise TypeError("collection doit être un QdrantCollectionProfile")
        for callback in self.close_callbacks:
            if not callable(callback):
                raise TypeError("chaque close_callback doit être callable")
        if len(self.close_callbacks) < 2:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "la fondation doit posséder les fermetures PostgreSQL et Qdrant"
            )
        if not self.evidence_refs:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "la fondation doit exposer des preuves d'installation"
            )
        for value in self.evidence_refs:
            _typed_ref("evidence_ref", value)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "scheduler_ref": self.scheduler_ref,
                "base_revision_ref": self.base_revision_ref,
                "collection_name": self.collection.collection_name,
                "embedding_dimension": 384,
                "close_callback_count": len(self.close_callbacks),
                "evidence_refs": self.evidence_refs,
                "postgresql_durable_authority": True,
                "postgresql_shared_adapter_port": True,
                "qdrant_projection_and_recall": True,
                "openvino_e5_real": True,
                "scheduler_lifecycle": "externally-managed",
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def validate_love_externally_managed_backend_alignment(
    settings: "InstalledRuntimeFactorySettings",
    manual: ManualInstalledRuntimeSettings,
) -> None:
    """Fail closed when installed attestations and manual config diverge."""

    expected = {
        "runtime_ref": settings.runtime_ref,
        "scheduler_ref": settings.scheduler_ref,
        "scheduler_lifecycle": settings.scheduler_lifecycle,
        "sql_authority_ref": settings.sql_authority_ref,
        "projection_backend_ref": settings.projection_backend_ref,
        "embedding_backend_ref": settings.embedding_backend_ref,
        "retrieval_backend_ref": settings.retrieval_backend_ref,
        "model_ref": settings.model_ref,
        "model_revision": settings.model_revision,
        "base_revision_ref": settings.base_revision_ref,
    }
    for name, value in expected.items():
        if getattr(manual, name) != value:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                f"manual runtime {name} differs from factory attestation"
            )
    if settings.scheduler_lifecycle != "externally-managed":
        raise LoveExternallyManagedInstalledBackendFoundationError(
            "installed OpenRC backend foundation requires externally-managed"
        )
    if not manual.qdrant.named_vectors_enabled:
        raise LoveExternallyManagedInstalledBackendFoundationError(
            "installed Qdrant foundation requires named vectors"
        )
    if manual.qdrant.physical_collection != settings.qdrant_collection:
        raise LoveExternallyManagedInstalledBackendFoundationError(
            "physical Qdrant collection differs from factory attestation"
        )
    if manual.qdrant.dimension != 384 or manual.openvino.dimension != 384:
        raise LoveExternallyManagedInstalledBackendFoundationError(
            "installed E5/Qdrant foundation must use dimension 384"
        )


def build_love_externally_managed_installed_backend_foundation(
    *,
    settings: "InstalledRuntimeFactorySettings",
    config_path: str | os.PathLike[str] | None = None,
    environment: Mapping[str, str] | None = None,
) -> LoveExternallyManagedInstalledBackendFoundation:
    """Open one real process-owned backend foundation for the OpenRC service."""

    env = os.environ if environment is None else environment
    manual = load_manual_installed_runtime_settings(config_path or settings.config_path)
    validate_love_externally_managed_backend_alignment(settings, manual)
    _require_gate(env, QDRANT_POINT_WRITE_GATE_ENV)
    _require_gate(env, QDRANT_SEARCH_GATE_ENV)
    policy_decision_id = str(
        env.get(SERVICE_POLICY_DECISION_ENV, DEFAULT_SERVICE_POLICY_DECISION_ID)
    ).strip()
    if not policy_decision_id.startswith("policy:"):
        raise LoveExternallyManagedInstalledBackendFoundationError(
            f"{SERVICE_POLICY_DECISION_ENV} doit être une référence policy:"
        )

    scheduler, dispatcher = _build_scheduler_stack()
    postgres_binding: LovePostgreSqlAuthorityBinding | None = None
    qdrant_executor: QdrantClientProjectionExecutor | None = None
    try:
        postgres_binding = open_love_postgresql_authority(manual, environment=env)
        if postgres_binding.scheduler_command_store is None:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "PostgreSQL binding does not expose scheduler_command_store"
            )
        if postgres_binding.scheduler_task_launch_transaction is None:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "PostgreSQL binding does not expose task launch transaction"
            )
        if postgres_binding.scheduler_handler_execution_transaction is None:
            raise LoveExternallyManagedInstalledBackendFoundationError(
                "PostgreSQL binding does not expose handler execution transaction"
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
                        "foundation_schema": EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA,
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
        retrieval_executor = build_love_qdrant_hybrid_query_adapter(qdrant_executor)
        return LoveExternallyManagedInstalledBackendFoundation(
            schema=EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA,
            scheduler=scheduler,
            dispatcher=dispatcher,
            scheduler_ref=settings.scheduler_ref,
            authority_store=postgres_binding.authority_store,
            postgresql_adapter_port=postgres_binding.shared_adapter_port,
            command_store=postgres_binding.scheduler_command_store,
            task_launch_transaction=(
                postgres_binding.scheduler_task_launch_transaction
            ),
            handler_execution_transaction=(
                postgres_binding.scheduler_handler_execution_transaction
            ),
            projection_port=projection_port,
            collection=collection,
            embedder=embedder,
            retrieval_executor=retrieval_executor,
            base_revision_ref=manual.base_revision_ref,
            close_callbacks=(postgres_binding.close, qdrant_executor.close),
            evidence_refs=_unique_refs(
                settings.evidence_refs
                + (
                    "evidence:externally-managed-installed-backend-foundation",
                    "evidence:postgresql-authority-open",
                    "evidence:openvino-e5-dimension-384",
                    "evidence:qdrant-hybrid-live",
                )
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


def _build_scheduler_stack() -> tuple[Scheduler, Dispatcher]:
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    scheduler = Scheduler(PriorityQueue(), dispatcher, event_bus, Registry())
    return scheduler, dispatcher


def _build_collection(
    manual: ManualInstalledRuntimeSettings,
) -> QdrantCollectionProfile:
    dense = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=manual.qdrant.dense_vector_name,
        vector_kind="dense",
        embedding_profile_ref="embedding-profile:multilingual-e5-small-passage",
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
            "foundation_schema": EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA,
        },
    )


def _require_gate(environment: Mapping[str, str], name: str) -> None:
    enabled = str(environment.get(name, "")).strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not enabled:
        raise LoveExternallyManagedInstalledBackendFoundationError(
            f"missing explicit effect gate {name}"
        )


def _method(value: object, name: str) -> None:
    if not callable(getattr(value, name, None)):
        raise TypeError(f"{type(value).__name__} doit exposer {name}")


def _typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or ":" not in value or any(ch.isspace() for ch in value):
        raise LoveExternallyManagedInstalledBackendFoundationError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise LoveExternallyManagedInstalledBackendFoundationError(
            f"{name} doit commencer par {prefix}"
        )


def _unique_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        _typed_ref("evidence_ref", value)
        if value not in result:
            result.append(value)
    return tuple(result)


__all__ = (
    "DEFAULT_SERVICE_POLICY_DECISION_ID",
    "EXTERNALLY_MANAGED_BACKEND_FOUNDATION_SCHEMA",
    "LoveExternallyManagedInstalledBackendFoundation",
    "LoveExternallyManagedInstalledBackendFoundationError",
    "QDRANT_POINT_WRITE_GATE_ENV",
    "QDRANT_SEARCH_GATE_ENV",
    "SERVICE_POLICY_DECISION_ENV",
    "build_love_externally_managed_installed_backend_foundation",
    "validate_love_externally_managed_backend_alignment",
)
