"""Passive source audit for the first live love-runtime composer.

0287-r7-r15-r3-r5 records which installed-runtime surfaces already exist and
which leaf adapters are still missing before a tool-bounded live preview can be
truthfully composed.  The audit consumes source text supplied by tests or an IO
adapter.  It imports no PostgreSQL driver, OpenVINO runtime, Qdrant client,
Scheduler implementation or GitHub adapter and performs no side effect.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


AUDIT_SCHEMA = "missipy.love.live_runtime_composer_reuse_audit.v1"

REQUIRED_SURFACES: tuple[str, ...] = (
    "src/context/context_revision_sql_authority_0287.py",
    "src/context/sql_context_store.py",
    "src/inference/e5_pipeline.py",
    "src/inference/embedding_pipeline.py",
    "src/inference/qdrant_client_projection_executor.py",
    "src/context/qdrant_canonical_profile_0287.py",
    "src/context/hybrid_retrieval_sql_rehydration_0287.py",
    "src/context/love_memory_evidence_liaison_synthesis_0287.py",
    "src/context/love_full_deterministic_local_smoke_0287.py",
    "src/context/native_love_laboratory_scheduler_binding_0287.py",
    "src/context/native_love_laboratory_collaboration_scheduler_binding_0287.py",
    "src/context/love_installed_runtime_factory_0287.py",
    "src/context/love_manual_runtime_configuration_0287.py",
    "src/kernel/scheduler.py",
    "src/kernel/dispatcher.py",
)

IMPLEMENTATION_SEQUENCE: tuple[str, ...] = (
    "0287-r7-r15-r3-r6-postgresql-authority-live-binding",
    "0287-r7-r15-r3-r7-openvino-dense-query-adapter",
    "0287-r7-r15-r3-r8-qdrant-hybrid-projection-recall-adapters",
    "0287-r7-r15-r3-r9-tool-bounded-live-runtime-composer",
    "0287-r7-r15-r3-r10-first-live-imported-actions-preview",
)


@dataclass(frozen=True, slots=True)
class LoveLiveRuntimeComposerReuseAuditResult:
    """Immutable findings for the live runtime composition boundary."""

    valid: bool
    issues: tuple[str, ...]
    scanned_file_count: int
    required_surfaces_present: tuple[str, ...]
    missing_required_surfaces: tuple[str, ...]
    sql_authority_store_found: bool
    postgresql_target_descriptor_found: bool
    postgresql_connection_factory_found: bool
    e5_pipeline_factory_found: bool
    e5_embedding_is_async: bool
    dense_query_protocol_found: bool
    dense_query_adapter_found: bool
    qdrant_client_executor_found: bool
    qdrant_client_close_found: bool
    canonical_named_vector_profile_found: bool
    hybrid_query_protocol_found: bool
    hybrid_query_adapter_found: bool
    projection_protocol_found: bool
    projection_adapter_found: bool
    native_love_handler_registration_found: bool
    collaborative_love_handler_registration_found: bool
    base_revision_seed_found: bool
    existing_scheduler_reused: bool = True
    existing_dispatcher_reused: bool = True
    sql_remains_durable_authority: bool = True
    qdrant_remains_reference_projection_only: bool = True
    e5_dimension_locked_to_384: bool = True
    process_local_tool_bounded_composition_required: bool = True
    new_scheduler_allowed: bool = False
    runtime_manager_allowed: bool = False
    network_used: bool = False
    backend_loaded: bool = False
    write_performed: bool = False

    @property
    def postgresql_live_binding_needed(self) -> bool:
        return self.valid and not self.postgresql_connection_factory_found

    @property
    def dense_query_adapter_needed(self) -> bool:
        return self.valid and not self.dense_query_adapter_found

    @property
    def hybrid_qdrant_adapters_needed(self) -> bool:
        return self.valid and not self.hybrid_query_adapter_found

    @property
    def projection_adapter_needed(self) -> bool:
        return self.valid and not self.projection_adapter_found

    @property
    def base_revision_seed_needed(self) -> bool:
        return self.valid and not self.base_revision_seed_found

    @property
    def live_composer_ready(self) -> bool:
        return self.valid and not any(
            (
                self.postgresql_live_binding_needed,
                self.dense_query_adapter_needed,
                self.hybrid_qdrant_adapters_needed,
                self.projection_adapter_needed,
                self.base_revision_seed_needed,
            )
        )

    @property
    def next_recommended_patch(self) -> str:
        if self.live_composer_ready:
            return IMPLEMENTATION_SEQUENCE[3]
        return IMPLEMENTATION_SEQUENCE[0]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": AUDIT_SCHEMA,
            "love_live_runtime_composer_reuse_audit": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "scanned_file_count": self.scanned_file_count,
            "required_surfaces_present": list(self.required_surfaces_present),
            "missing_required_surfaces": list(self.missing_required_surfaces),
            "sql_authority_store_found": self.sql_authority_store_found,
            "postgresql_target_descriptor_found": (
                self.postgresql_target_descriptor_found
            ),
            "postgresql_connection_factory_found": (
                self.postgresql_connection_factory_found
            ),
            "e5_pipeline_factory_found": self.e5_pipeline_factory_found,
            "e5_embedding_is_async": self.e5_embedding_is_async,
            "dense_query_protocol_found": self.dense_query_protocol_found,
            "dense_query_adapter_found": self.dense_query_adapter_found,
            "qdrant_client_executor_found": self.qdrant_client_executor_found,
            "qdrant_client_close_found": self.qdrant_client_close_found,
            "canonical_named_vector_profile_found": (
                self.canonical_named_vector_profile_found
            ),
            "hybrid_query_protocol_found": self.hybrid_query_protocol_found,
            "hybrid_query_adapter_found": self.hybrid_query_adapter_found,
            "projection_protocol_found": self.projection_protocol_found,
            "projection_adapter_found": self.projection_adapter_found,
            "native_love_handler_registration_found": (
                self.native_love_handler_registration_found
            ),
            "collaborative_love_handler_registration_found": (
                self.collaborative_love_handler_registration_found
            ),
            "base_revision_seed_found": self.base_revision_seed_found,
            "postgresql_live_binding_needed": self.postgresql_live_binding_needed,
            "dense_query_adapter_needed": self.dense_query_adapter_needed,
            "hybrid_qdrant_adapters_needed": self.hybrid_qdrant_adapters_needed,
            "projection_adapter_needed": self.projection_adapter_needed,
            "base_revision_seed_needed": self.base_revision_seed_needed,
            "live_composer_ready": self.live_composer_ready,
            "implementation_sequence": list(IMPLEMENTATION_SEQUENCE),
            "next_recommended_patch": self.next_recommended_patch,
            "existing_scheduler_reused": self.existing_scheduler_reused,
            "existing_dispatcher_reused": self.existing_dispatcher_reused,
            "sql_remains_durable_authority": self.sql_remains_durable_authority,
            "qdrant_remains_reference_projection_only": (
                self.qdrant_remains_reference_projection_only
            ),
            "e5_dimension_locked_to_384": self.e5_dimension_locked_to_384,
            "process_local_tool_bounded_composition_required": (
                self.process_local_tool_bounded_composition_required
            ),
            "new_scheduler_allowed": self.new_scheduler_allowed,
            "runtime_manager_allowed": self.runtime_manager_allowed,
            "network_used": self.network_used,
            "backend_loaded": self.backend_loaded,
            "write_performed": self.write_performed,
        }


def audit_love_live_runtime_composer_reuse(
    sources: Mapping[str, str],
) -> LoveLiveRuntimeComposerReuseAuditResult:
    """Inspect supplied source text without importing or executing it."""

    normalized = {str(path): str(text) for path, text in sources.items()}
    present = tuple(path for path in REQUIRED_SURFACES if path in normalized)
    missing = tuple(path for path in REQUIRED_SURFACES if path not in normalized)
    issues = [f"missing required surface: {path}" for path in missing]

    authority = normalized.get(REQUIRED_SURFACES[0], "")
    sql_store = normalized.get(REQUIRED_SURFACES[1], "")
    e5_pipeline = normalized.get(REQUIRED_SURFACES[2], "")
    embedding_pipeline = normalized.get(REQUIRED_SURFACES[3], "")
    qdrant_executor = normalized.get(REQUIRED_SURFACES[4], "")
    qdrant_profile = normalized.get(REQUIRED_SURFACES[5], "")
    hybrid = normalized.get(REQUIRED_SURFACES[6], "")
    synthesis = normalized.get(REQUIRED_SURFACES[7], "")
    native_binding = normalized.get(REQUIRED_SURFACES[9], "")
    collaborative_binding = normalized.get(REQUIRED_SURFACES[10], "")

    sql_authority_store_found = (
        "class DbApiContextRevisionAuthorityStore" in authority
    )
    if not sql_authority_store_found:
        issues.append("DbApiContextRevisionAuthorityStore is missing")

    postgresql_target_descriptor_found = (
        "class PostgresSqlContextStoreTarget" in sql_store
    )
    if not postgresql_target_descriptor_found:
        issues.append("PostgresSqlContextStoreTarget descriptor is missing")

    postgresql_connection_factory_found = any(
        token in text
        for text in normalized.values()
        for token in ("psycopg.connect", "psycopg2.connect")
    )

    e5_pipeline_factory_found = (
        "def build_multilingual_e5_small_pipeline" in e5_pipeline
        and "class MultilingualE5SmallPipelineBundle" in e5_pipeline
    )
    if not e5_pipeline_factory_found:
        issues.append("multilingual E5 pipeline factory is incomplete")

    e5_embedding_is_async = "async def embed_text" in embedding_pipeline
    if not e5_embedding_is_async:
        issues.append("OpenVINO E5 embed_text must remain explicitly async")

    dense_query_protocol_found = (
        "class DenseQueryEmbedder(Protocol)" in hybrid
        and "def embed_query" in hybrid
    )
    if not dense_query_protocol_found:
        issues.append("DenseQueryEmbedder protocol is missing")
    dense_query_adapter_found = _method_implemented_outside(
        normalized,
        method="embed_query",
        excluded_paths=(REQUIRED_SURFACES[6],),
    )

    qdrant_client_executor_found = (
        "class QdrantClientProjectionExecutor" in qdrant_executor
    )
    if not qdrant_client_executor_found:
        issues.append("QdrantClientProjectionExecutor is missing")
    qdrant_client_close_found = "def close" in qdrant_executor
    if not qdrant_client_close_found:
        issues.append("Qdrant client executor close boundary is missing")

    canonical_named_vector_profile_found = (
        "class QdrantNamedVectorProfile" in qdrant_profile
        and "class QdrantCollectionProfile" in qdrant_profile
        and "named_vectors" in qdrant_profile
    )
    if not canonical_named_vector_profile_found:
        issues.append("canonical Qdrant named-vector profile is incomplete")

    hybrid_query_protocol_found = (
        "class QdrantHybridQueryExecutor(Protocol)" in hybrid
        and "def search_dense" in hybrid
        and "def search_sparse" in hybrid
    )
    if not hybrid_query_protocol_found:
        issues.append("QdrantHybridQueryExecutor protocol is missing")
    hybrid_query_adapter_found = _method_pair_implemented_outside(
        normalized,
        first="search_dense",
        second="search_sparse",
        excluded_paths=(REQUIRED_SURFACES[6],),
    )

    projection_protocol_found = (
        "class LoveAnalysisProjectionPort(Protocol)" in synthesis
        and "def project" in synthesis
    )
    if not projection_protocol_found:
        issues.append("LoveAnalysisProjectionPort protocol is missing")
    projection_adapter_found = _method_implemented_outside(
        normalized,
        method="project",
        excluded_paths=(REQUIRED_SURFACES[7],),
    )

    native_love_handler_registration_found = (
        "def register_native_love_laboratory_visit_handler" in native_binding
    )
    if not native_love_handler_registration_found:
        issues.append("native love handler registration is missing")
    collaborative_love_handler_registration_found = (
        "def register_native_love_collaboration_visit_handler"
        in collaborative_binding
    )
    if not collaborative_love_handler_registration_found:
        issues.append("collaborative love handler registration is missing")

    base_revision_seed_found = any(
        "context-revision:love-base" in text
        and any(
            token in text
            for token in (
                "put_revision(",
                "seed_revision",
                "bootstrap_revision",
            )
        )
        for text in normalized.values()
    )

    return LoveLiveRuntimeComposerReuseAuditResult(
        valid=not issues,
        issues=tuple(issues),
        scanned_file_count=len(normalized),
        required_surfaces_present=present,
        missing_required_surfaces=missing,
        sql_authority_store_found=sql_authority_store_found,
        postgresql_target_descriptor_found=postgresql_target_descriptor_found,
        postgresql_connection_factory_found=postgresql_connection_factory_found,
        e5_pipeline_factory_found=e5_pipeline_factory_found,
        e5_embedding_is_async=e5_embedding_is_async,
        dense_query_protocol_found=dense_query_protocol_found,
        dense_query_adapter_found=dense_query_adapter_found,
        qdrant_client_executor_found=qdrant_client_executor_found,
        qdrant_client_close_found=qdrant_client_close_found,
        canonical_named_vector_profile_found=canonical_named_vector_profile_found,
        hybrid_query_protocol_found=hybrid_query_protocol_found,
        hybrid_query_adapter_found=hybrid_query_adapter_found,
        projection_protocol_found=projection_protocol_found,
        projection_adapter_found=projection_adapter_found,
        native_love_handler_registration_found=(
            native_love_handler_registration_found
        ),
        collaborative_love_handler_registration_found=(
            collaborative_love_handler_registration_found
        ),
        base_revision_seed_found=base_revision_seed_found,
    )


def _method_implemented_outside(
    sources: Mapping[str, str],
    *,
    method: str,
    excluded_paths: tuple[str, ...],
) -> bool:
    marker = f"def {method}"
    return any(
        path not in excluded_paths and marker in text
        for path, text in sources.items()
    )


def _method_pair_implemented_outside(
    sources: Mapping[str, str],
    *,
    first: str,
    second: str,
    excluded_paths: tuple[str, ...],
) -> bool:
    return any(
        path not in excluded_paths
        and f"def {first}" in text
        and f"def {second}" in text
        for path, text in sources.items()
    )


__all__ = (
    "AUDIT_SCHEMA",
    "IMPLEMENTATION_SEQUENCE",
    "REQUIRED_SURFACES",
    "LoveLiveRuntimeComposerReuseAuditResult",
    "audit_love_live_runtime_composer_reuse",
)
