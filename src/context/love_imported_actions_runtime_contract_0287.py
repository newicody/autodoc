"""Real-runtime injection contract for imported Actions run previews.

This module creates no Scheduler, SQL store, embedding backend, Qdrant client or
retrieval executor.  It only validates a bundle supplied by an existing runtime
factory.  r15-r2 refuses to execute r14 unless that factory explicitly attests
that the injected E5/OpenVINO and Qdrant paths are real.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
import inspect
from threading import RLock
from typing import Any, Literal, Protocol, runtime_checkable

from contracts.scheduler import SchedulerContract

IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA = (
    "missipy.love.imported_actions_real_backend_attestation.v1"
)
IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA = (
    "missipy.love.imported_actions_runtime_ports.v1"
)
IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA = (
    "missipy.love.imported_actions_runtime_close_hook.v1"
)
IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA = (
    "missipy.love.imported_actions_runtime_lease.v1"
)
IMPORTED_ACTIONS_RUNTIME_LEASE_RECEIPT_SCHEMA = (
    "missipy.love.imported_actions_runtime_lease_receipt.v1"
)
ImportedActionsSchedulerLifecycle = Literal[
    "tool-bounded",
    "externally-managed",
]
ImportedActionsRuntimeLeaseAction = Literal["closed", "replay"]


class ImportedActionsRuntimeContractError(RuntimeError):
    """Raised when a runtime factory or its evidence fails closed."""


class ImportedActionsRuntimeLeaseCloseError(
    ImportedActionsRuntimeContractError
):
    """Raised after every close hook ran but at least one hook failed."""

    def __init__(
        self,
        message: str,
        *,
        receipt: "ImportedActionsRuntimeLeaseReceipt",
    ) -> None:
        super().__init__(message)
        self.receipt = receipt


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


@dataclass(frozen=True, slots=True)
class ImportedActionsRuntimeCloseHook:
    """One synchronous cleanup effect owned by a tool-bounded runtime."""

    schema: str
    hook_ref: str
    callback: Callable[[], object] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.schema != IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA:
            raise ImportedActionsRuntimeContractError(
                "unsupported imported Actions runtime close-hook schema"
            )
        if not _require_text("hook_ref", self.hook_ref).startswith(
            "runtime-close:"
        ):
            raise ImportedActionsRuntimeContractError(
                "runtime close hook_ref must start with runtime-close:"
            )
        if not callable(self.callback):
            raise ImportedActionsRuntimeContractError(
                "runtime close hook callback must be callable"
            )
        if inspect.iscoroutinefunction(self.callback):
            raise ImportedActionsRuntimeContractError(
                "runtime close hook callback must be synchronous"
            )


@dataclass(frozen=True, slots=True)
class ImportedActionsRuntimeLeaseReceipt:
    """Serializable exact-once evidence for one process-local lease close."""

    schema: str
    runtime_ref: str
    owner_ref: str
    action: ImportedActionsRuntimeLeaseAction
    process_id: int
    completed_hook_refs: tuple[str, ...]
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema != IMPORTED_ACTIONS_RUNTIME_LEASE_RECEIPT_SCHEMA:
            raise ImportedActionsRuntimeContractError(
                "unsupported imported Actions runtime lease-receipt schema"
            )
        if not _require_text("runtime_ref", self.runtime_ref).startswith(
            "runtime:"
        ):
            raise ImportedActionsRuntimeContractError(
                "runtime_ref must start with runtime:"
            )
        if not _require_text("owner_ref", self.owner_ref).startswith(
            "runtime-owner:"
        ):
            raise ImportedActionsRuntimeContractError(
                "owner_ref must start with runtime-owner:"
            )
        if self.action not in {"closed", "replay"}:
            raise ImportedActionsRuntimeContractError(
                "runtime lease receipt action must be closed or replay"
            )
        if self.process_id <= 0:
            raise ImportedActionsRuntimeContractError(
                "runtime lease receipt process_id must be positive"
            )

    @property
    def valid(self) -> bool:
        return not self.issues

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "runtime_ref": self.runtime_ref,
            "owner_ref": self.owner_ref,
            "action": self.action,
            "process_id": self.process_id,
            "completed_hook_refs": list(self.completed_hook_refs),
            "issues": list(self.issues),
            "valid": self.valid,
        }


@dataclass(slots=True)
class ImportedActionsRuntimeLease:
    """Process-local owner for ports and their tool-bounded cleanup effects."""

    schema: str
    ports: ImportedActionsRuntimePorts
    owner_ref: str
    process_id: int
    close_hooks: tuple[ImportedActionsRuntimeCloseHook, ...] = ()
    _closed: bool = field(default=False, init=False, repr=False)
    _receipt: ImportedActionsRuntimeLeaseReceipt | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _lock: RLock = field(
        default_factory=RLock,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if self.schema != IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA:
            raise ImportedActionsRuntimeContractError(
                "unsupported imported Actions runtime lease schema"
            )
        self.ports = validate_imported_actions_runtime_ports(self.ports)
        if not _require_text("owner_ref", self.owner_ref).startswith(
            "runtime-owner:"
        ):
            raise ImportedActionsRuntimeContractError(
                "owner_ref must start with runtime-owner:"
            )
        if self.process_id <= 0:
            raise ImportedActionsRuntimeContractError(
                "runtime lease process_id must be positive"
            )
        self.close_hooks = tuple(self.close_hooks)
        if not all(
            isinstance(hook, ImportedActionsRuntimeCloseHook)
            for hook in self.close_hooks
        ):
            raise ImportedActionsRuntimeContractError(
                "close_hooks must contain ImportedActionsRuntimeCloseHook"
            )
        if (
            self.close_hooks
            and self.ports.scheduler_lifecycle != "tool-bounded"
        ):
            raise ImportedActionsRuntimeContractError(
                "only a tool-bounded runtime may own close hooks"
            )
        hook_refs = tuple(hook.hook_ref for hook in self.close_hooks)
        if len(set(hook_refs)) != len(hook_refs):
            raise ImportedActionsRuntimeContractError(
                "runtime close hook references must be unique"
            )

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    @property
    def close_receipt(self) -> ImportedActionsRuntimeLeaseReceipt | None:
        with self._lock:
            return self._receipt

    def to_readback_mapping(self) -> dict[str, Any]:
        """Return lifecycle evidence without exposing executable callbacks."""

        with self._lock:
            receipt = self._receipt
            return {
                "schema": self.schema,
                "runtime_ref": self.ports.runtime_ref,
                "owner_ref": self.owner_ref,
                "process_id": self.process_id,
                "scheduler_lifecycle": self.ports.scheduler_lifecycle,
                "close_hook_refs": [
                    hook.hook_ref for hook in self.close_hooks
                ],
                "closed": self._closed,
                "close_receipt": (
                    receipt.to_mapping() if receipt is not None else None
                ),
            }

    def ensure_current_process(self, current_process_id: int) -> None:
        if current_process_id <= 0:
            raise ImportedActionsRuntimeContractError(
                "current_process_id must be positive"
            )
        if self.process_id != current_process_id:
            raise ImportedActionsRuntimeContractError(
                "runtime lease is process-local and cannot cross a process "
                f"boundary: owner pid {self.process_id}, current pid "
                f"{current_process_id}"
            )

    def close(
        self,
        *,
        current_process_id: int,
    ) -> ImportedActionsRuntimeLeaseReceipt:
        """Close all owned effects in reverse order, exactly once."""

        self.ensure_current_process(current_process_id)
        with self._lock:
            if self._closed:
                if self._receipt is None:
                    raise ImportedActionsRuntimeContractError(
                        "closed runtime lease has no close receipt"
                    )
                return replace(self._receipt, action="replay")

            completed: list[str] = []
            issues: list[str] = []
            for hook in reversed(self.close_hooks):
                try:
                    result = hook.callback()
                    if inspect.isawaitable(result):
                        close_awaitable = getattr(result, "close", None)
                        if callable(close_awaitable):
                            close_awaitable()
                        raise TypeError(
                            "runtime close hook returned an awaitable"
                        )
                    completed.append(hook.hook_ref)
                except Exception as exc:  # noqa: BLE001 - close all hooks
                    issues.append(
                        f"{hook.hook_ref}: {type(exc).__name__}: {exc}"
                    )

            receipt = ImportedActionsRuntimeLeaseReceipt(
                schema=IMPORTED_ACTIONS_RUNTIME_LEASE_RECEIPT_SCHEMA,
                runtime_ref=self.ports.runtime_ref,
                owner_ref=self.owner_ref,
                action="closed",
                process_id=self.process_id,
                completed_hook_refs=tuple(completed),
                issues=tuple(issues),
            )
            self._closed = True
            self._receipt = receipt
            if issues:
                raise ImportedActionsRuntimeLeaseCloseError(
                    "runtime lease close failed: " + "; ".join(issues),
                    receipt=receipt,
                )
            return receipt


def acquire_imported_actions_runtime_lease(
    value: object,
    *,
    current_process_id: int,
) -> ImportedActionsRuntimeLease:
    """Normalize a modern lease or legacy direct ports without side effects."""

    if isinstance(value, ImportedActionsRuntimeLease):
        value.ensure_current_process(current_process_id)
        return value
    if isinstance(value, ImportedActionsRuntimePorts):
        return ImportedActionsRuntimeLease(
            schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
            ports=value,
            owner_ref="runtime-owner:legacy-direct-ports",
            process_id=current_process_id,
        )
    raise ImportedActionsRuntimeContractError(
        "runtime factory must return ImportedActionsRuntimeLease or "
        "ImportedActionsRuntimePorts"
    )


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
    ) -> ImportedActionsRuntimeLease | ImportedActionsRuntimePorts:
        """Return initialized ports, preferably inside a process-local lease."""


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
    "IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA",
    "IMPORTED_ACTIONS_RUNTIME_LEASE_RECEIPT_SCHEMA",
    "IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA",
    "IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA",
    "ImportedActionsRealBackendAttestation",
    "ImportedActionsRuntimeCloseHook",
    "ImportedActionsRuntimeContractError",
    "ImportedActionsRuntimeFactory",
    "ImportedActionsRuntimeLease",
    "ImportedActionsRuntimeLeaseAction",
    "ImportedActionsRuntimeLeaseCloseError",
    "ImportedActionsRuntimeLeaseReceipt",
    "ImportedActionsSchedulerLifecycle",
    "ImportedActionsRuntimePorts",
    "acquire_imported_actions_runtime_lease",
    "validate_imported_actions_runtime_ports",
)
