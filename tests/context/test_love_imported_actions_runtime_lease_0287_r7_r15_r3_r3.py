from __future__ import annotations

from dataclasses import dataclass
import os

import pytest

from contracts.scheduler import SchedulerContract
from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
    ImportedActionsRealBackendAttestation,
    ImportedActionsRuntimeCloseHook,
    ImportedActionsRuntimeContractError,
    ImportedActionsRuntimeLease,
    ImportedActionsRuntimeLeaseCloseError,
    ImportedActionsRuntimePorts,
    acquire_imported_actions_runtime_lease,
)


class _Scheduler(SchedulerContract):
    async def emit(self, event):
        return None

    async def run(self):
        return None

    async def shutdown(self):
        return None


class _Dispatcher:
    def register(self, event_type, handler):
        return None


class _Store:
    def get_revision(self, ref):
        return None

    def put_object(self, value):
        return None

    def put_artifact(self, value):
        return None

    def put_revision(self, value):
        return None

    def put_projection(self, value):
        return None

    def put_relation(self, value):
        return None


class _Projection:
    def project(self, value, **kwargs):
        return None


class _Embedder:
    def embed_query(self, value, **kwargs):
        return None


class _Executor:
    def search_dense(self, value, **kwargs):
        return ()

    def search_sparse(self, value, **kwargs):
        return ()


@dataclass
class _Collection:
    collection_name: str = "autodoc_context_current"


def _ports(*, lifecycle: str = "tool-bounded") -> ImportedActionsRuntimePorts:
    attestation = ImportedActionsRealBackendAttestation(
        schema=IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
        runtime_ref="runtime:live-preview",
        scheduler_ref="scheduler:canonical",
        sql_authority_ref="sql-authority:context-revision",
        projection_backend_ref="qdrant:autodoc-context-current",
        embedding_backend_ref="openvino:multilingual-e5-small",
        retrieval_backend_ref="hybrid:qdrant-sql",
        model_ref="model:multilingual-e5-small",
        model_revision="openvino-ir-v1",
        qdrant_collection="autodoc_context_current",
        evidence_refs=("evidence:manual-runtime-readiness",),
        scheduler_lifecycle=lifecycle,
    )
    return ImportedActionsRuntimePorts(
        schema=IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
        runtime_ref=attestation.runtime_ref,
        scheduler=_Scheduler(),
        dispatcher=_Dispatcher(),
        authority_store=_Store(),
        projection_port=_Projection(),
        collection=_Collection(),
        embedder=_Embedder(),
        executor=_Executor(),
        base_revision_ref="context-revision:base",
        scheduler_lifecycle=lifecycle,
        attestation=attestation,
    )


def _hook(reference: str, callback) -> ImportedActionsRuntimeCloseHook:
    return ImportedActionsRuntimeCloseHook(
        schema=IMPORTED_ACTIONS_RUNTIME_CLOSE_HOOK_SCHEMA,
        hook_ref=reference,
        callback=callback,
    )


def test_tool_bounded_lease_closes_in_reverse_order_exactly_once() -> None:
    effects: list[str] = []
    lease = ImportedActionsRuntimeLease(
        schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
        ports=_ports(),
        owner_ref="runtime-owner:actions-preview-123",
        process_id=os.getpid(),
        close_hooks=(
            _hook("runtime-close:postgresql", lambda: effects.append("sql")),
            _hook("runtime-close:qdrant", lambda: effects.append("qdrant")),
            _hook("runtime-close:openvino", lambda: effects.append("openvino")),
        ),
    )

    receipt = lease.close(
        current_process_id=os.getpid(),
    )
    replay = lease.close(
        current_process_id=os.getpid(),
    )

    assert effects == ["openvino", "qdrant", "sql"]
    assert receipt.action == "closed"
    assert receipt.valid is True
    assert receipt.completed_hook_refs == (
        "runtime-close:openvino",
        "runtime-close:qdrant",
        "runtime-close:postgresql",
    )
    assert replay.action == "replay"
    assert replay.completed_hook_refs == receipt.completed_hook_refs
    assert lease.closed is True
    readback = lease.to_readback_mapping()
    assert readback["closed"] is True
    assert readback["close_receipt"]["valid"] is True
    assert "callback" not in str(readback)


def test_close_runs_every_hook_before_reporting_failures() -> None:
    effects: list[str] = []

    def broken() -> None:
        effects.append("broken")
        raise RuntimeError("cannot close")

    lease = ImportedActionsRuntimeLease(
        schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
        ports=_ports(),
        owner_ref="runtime-owner:actions-preview-123",
        process_id=os.getpid(),
        close_hooks=(
            _hook("runtime-close:postgresql", lambda: effects.append("sql")),
            _hook("runtime-close:qdrant", broken),
            _hook("runtime-close:openvino", lambda: effects.append("openvino")),
        ),
    )

    with pytest.raises(ImportedActionsRuntimeLeaseCloseError) as raised:
        lease.close(
            current_process_id=os.getpid(),
        )

    assert effects == ["openvino", "broken", "sql"]
    assert raised.value.receipt.completed_hook_refs == (
        "runtime-close:openvino",
        "runtime-close:postgresql",
    )
    assert raised.value.receipt.issues
    assert lease.close(
        current_process_id=os.getpid(),
    ).action == "replay"


def test_legacy_direct_ports_are_wrapped_without_owned_close_hooks() -> None:
    ports = _ports()
    lease = acquire_imported_actions_runtime_lease(
        ports,
        current_process_id=os.getpid(),
    )

    assert lease.ports is ports
    assert lease.close_hooks == ()
    assert lease.close(
        current_process_id=os.getpid(),
    ).valid is True


def test_runtime_lease_rejects_cross_process_use() -> None:
    lease = ImportedActionsRuntimeLease(
        schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
        ports=_ports(),
        owner_ref="runtime-owner:other-process",
        process_id=os.getpid() + 1,
    )

    with pytest.raises(
        ImportedActionsRuntimeContractError,
        match="process-local",
    ):
        acquire_imported_actions_runtime_lease(
            lease,
            current_process_id=os.getpid(),
        )


def test_externally_managed_runtime_cannot_own_close_hooks() -> None:
    with pytest.raises(
        ImportedActionsRuntimeContractError,
        match="tool-bounded",
    ):
        ImportedActionsRuntimeLease(
            schema=IMPORTED_ACTIONS_RUNTIME_LEASE_SCHEMA,
            ports=_ports(lifecycle="externally-managed"),
            owner_ref="runtime-owner:external-server",
            process_id=os.getpid(),
            close_hooks=(
                _hook("runtime-close:postgresql", lambda: None),
            ),
        )
