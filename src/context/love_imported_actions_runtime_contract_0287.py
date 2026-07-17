"""Real-runtime injection contract for imported Actions run previews.

This module creates no Scheduler, SQL store, embedding backend, Qdrant client or
retrieval executor.  It only validates a bundle supplied by an existing runtime
factory.  r15-r2 refuses to execute r14 unless that factory explicitly attests
that the injected E5/OpenVINO and Qdrant paths are real.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from contracts.scheduler import SchedulerContract

IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA = (
    "missipy.love.imported_actions_real_backend_attestation.v1"
)
IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA = (
    "missipy.love.imported_actions_runtime_ports.v1"
)
ImportedActionsSchedulerLifecycle = Literal[
    "tool-bounded",
    "externally-managed",
]


class ImportedActionsRuntimeContractError(RuntimeError):
    """Raised when a runtime factory or its evidence fails closed."""


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ImportedActionsRuntimeContractError(
            f"{name} must be a non-empty string"
        )
    return value.strip()


def _require_callable(owner: object, attribute: str) -> None:
    if not callable(getattr(owner, attribute, None)):
        raise ImportedActionsRuntimeContractError(
            f"runtime port must expose callable {attribute}()"
        )


@dataclass(frozen=True, slots=True)
class ImportedActionsRealBackendAttestation:
    """Evidence declared by one concrete existing runtime factory."""

    schema: str
    runtime_ref: str
    scheduler_ref: str
    sql_authority_ref: str
    projection_backend_ref: str
    embedding_backend_ref: str
    retrieval_backend_ref: str
    model_ref: str
    model_revision: str
    qdrant_collection: str
    evidence_refs: tuple[str, ...]
    scheduler_lifecycle: ImportedActionsSchedulerLifecycle
    embedding_dimension: int = 384
    scheduler_contract_reused: bool = True
    sql_authority_reused: bool = True
    openvino_e5_real: bool = True
    qdrant_write_real: bool = True
    qdrant_returns_references_only: bool = True

    def __post_init__(self) -> None:
        if self.schema != IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA:
            raise ImportedActionsRuntimeContractError(
                "unsupported real-backend attestation schema"
            )
        for name in (
            "runtime_ref",
            "scheduler_ref",
            "sql_authority_ref",
            "projection_backend_ref",
            "embedding_backend_ref",
            "retrieval_backend_ref",
            "model_ref",
            "model_revision",
            "qdrant_collection",
        ):
            _require_text(name, getattr(self, name))
        if not self.runtime_ref.startswith("runtime:"):
            raise ImportedActionsRuntimeContractError(
                "runtime_ref must start with runtime:"
            )
        if not self.scheduler_ref.startswith("scheduler:"):
            raise ImportedActionsRuntimeContractError(
                "scheduler_ref must start with scheduler:"
            )
        if not self.sql_authority_ref.startswith("sql-authority:"):
            raise ImportedActionsRuntimeContractError(
                "sql_authority_ref must start with sql-authority:"
            )
        if self.scheduler_lifecycle not in {
            "tool-bounded",
            "externally-managed",
        }:
            raise ImportedActionsRuntimeContractError(
                "scheduler_lifecycle must be tool-bounded or externally-managed"
            )
        if self.embedding_dimension != 384:
            raise ImportedActionsRuntimeContractError(
                "imported Actions runtime must use E5 dimension 384"
            )
        required_truths = {
            "scheduler_contract_reused": self.scheduler_contract_reused,
            "sql_authority_reused": self.sql_authority_reused,
            "openvino_e5_real": self.openvino_e5_real,
            "qdrant_write_real": self.qdrant_write_real,
            "qdrant_returns_references_only": (
                self.qdrant_returns_references_only
            ),
        }
        disabled = tuple(name for name, value in required_truths.items() if not value)
        if disabled:
            raise ImportedActionsRuntimeContractError(
                "real runtime attestation is incomplete: " + ", ".join(disabled)
            )
        normalized_evidence = tuple(
            dict.fromkeys(
                str(value).strip()
                for value in self.evidence_refs
                if str(value).strip()
            )
        )
        if not normalized_evidence:
            raise ImportedActionsRuntimeContractError(
                "real runtime attestation requires evidence_refs"
            )
        object.__setattr__(self, "evidence_refs", normalized_evidence)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "runtime_ref": self.runtime_ref,
            "scheduler_ref": self.scheduler_ref,
            "sql_authority_ref": self.sql_authority_ref,
            "projection_backend_ref": self.projection_backend_ref,
            "embedding_backend_ref": self.embedding_backend_ref,
            "retrieval_backend_ref": self.retrieval_backend_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "embedding_dimension": self.embedding_dimension,
            "qdrant_collection": self.qdrant_collection,
            "evidence_refs": list(self.evidence_refs),
            "scheduler_lifecycle": self.scheduler_lifecycle,
            "scheduler_contract_reused": True,
            "sql_authority_reused": True,
            "openvino_e5_real": True,
            "qdrant_write_real": True,
            "qdrant_returns_references_only": True,
        }


@dataclass(frozen=True, slots=True)
class ImportedActionsRuntimePorts:
    """Existing runtime ports injected into the already-closed r14 function."""

    schema: str
    runtime_ref: str
    scheduler: Any
    dispatcher: Any
    authority_store: Any
    projection_port: Any
    collection: Any
    embedder: Any
    executor: Any
    base_revision_ref: str
    scheduler_lifecycle: ImportedActionsSchedulerLifecycle
    attestation: ImportedActionsRealBackendAttestation

    def __post_init__(self) -> None:
        if self.schema != IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA:
            raise ImportedActionsRuntimeContractError(
                "unsupported imported Actions runtime ports schema"
            )
        if not isinstance(
            self.attestation,
            ImportedActionsRealBackendAttestation,
        ):
            raise ImportedActionsRuntimeContractError(
                "attestation must be ImportedActionsRealBackendAttestation"
            )
        if (
            _require_text("runtime_ref", self.runtime_ref)
            != self.attestation.runtime_ref
        ):
            raise ImportedActionsRuntimeContractError(
                "runtime_ref differs from real-backend attestation"
            )
        if self.scheduler_lifecycle not in {
            "tool-bounded",
            "externally-managed",
        }:
            raise ImportedActionsRuntimeContractError(
                "scheduler_lifecycle must be tool-bounded or externally-managed"
            )
        if self.scheduler_lifecycle != self.attestation.scheduler_lifecycle:
            raise ImportedActionsRuntimeContractError(
                "scheduler_lifecycle differs from real-backend attestation"
            )
        if not _require_text(
            "base_revision_ref", self.base_revision_ref
        ).startswith("context-revision:"):
            raise ImportedActionsRuntimeContractError(
                "base_revision_ref must start with context-revision:"
            )
        if not isinstance(self.scheduler, SchedulerContract):
            raise ImportedActionsRuntimeContractError(
                "scheduler must implement the canonical SchedulerContract"
            )
        _require_callable(self.scheduler, "emit")
        _require_callable(self.scheduler, "run")
        _require_callable(self.scheduler, "shutdown")
        _require_callable(self.dispatcher, "register")
        for method in (
            "get_revision",
            "put_object",
            "put_artifact",
            "put_revision",
            "put_projection",
            "put_relation",
        ):
            _require_callable(self.authority_store, method)
        _require_callable(self.projection_port, "project")
        _require_callable(self.embedder, "embed_query")
        _require_callable(self.executor, "search_dense")
        _require_callable(self.executor, "search_sparse")
        collection_name = str(
            getattr(self.collection, "collection_name", "")
        ).strip()
        if not collection_name:
            raise ImportedActionsRuntimeContractError(
                "collection must expose a non-empty collection_name"
            )
        if collection_name != self.attestation.qdrant_collection:
            raise ImportedActionsRuntimeContractError(
                "collection_name differs from real-backend attestation"
            )

    def to_attestation_mapping(self) -> dict[str, Any]:
        return self.attestation.to_mapping()


@runtime_checkable
class ImportedActionsRuntimeFactory(Protocol):
    """Portable factory signature loaded by the thin r15-r2 CLI."""

    def __call__(
        self,
        *,
        repository: str,
        run_id: str,
        request_payload: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
        created_at: str,
    ) -> ImportedActionsRuntimePorts:
        """Return initialized real ports and their exact attestation."""


def validate_imported_actions_runtime_ports(
    value: object,
) -> ImportedActionsRuntimePorts:
    """Validate the factory result without creating or replacing any port."""

    if not isinstance(value, ImportedActionsRuntimePorts):
        raise ImportedActionsRuntimeContractError(
            "runtime factory must return ImportedActionsRuntimePorts"
        )
    return value


__all__ = (
    "IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA",
    "IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA",
    "ImportedActionsRealBackendAttestation",
    "ImportedActionsRuntimeContractError",
    "ImportedActionsRuntimeFactory",
    "ImportedActionsSchedulerLifecycle",
    "ImportedActionsRuntimePorts",
    "validate_imported_actions_runtime_ports",
)
