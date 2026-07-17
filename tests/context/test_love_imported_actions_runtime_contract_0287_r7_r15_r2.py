from __future__ import annotations

from dataclasses import dataclass

import pytest

from contracts.scheduler import SchedulerContract
from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
    ImportedActionsRealBackendAttestation,
    ImportedActionsRuntimeContractError,
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
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
    collection_name: str = "autodoc_context"


def _attestation(**changes):
    values = {
        "schema": IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
        "runtime_ref": "runtime:live",
        "scheduler_ref": "scheduler:main",
        "sql_authority_ref": "sql-authority:context-revision",
        "projection_backend_ref": "qdrant:local-live",
        "embedding_backend_ref": "openvino:e5-small",
        "retrieval_backend_ref": "hybrid:qdrant-sql",
        "model_ref": "model:multilingual-e5-small",
        "model_revision": "openvino-ir-v1",
        "qdrant_collection": "autodoc_context",
        "evidence_refs": ("evidence:runtime-readback",),
        "scheduler_lifecycle": "tool-bounded",
    }
    values.update(changes)
    return ImportedActionsRealBackendAttestation(**values)


def _ports(**changes):
    values = {
        "schema": IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA,
        "runtime_ref": "runtime:live",
        "scheduler": _Scheduler(),
        "dispatcher": _Dispatcher(),
        "authority_store": _Store(),
        "projection_port": _Projection(),
        "collection": _Collection(),
        "embedder": _Embedder(),
        "executor": _Executor(),
        "base_revision_ref": "context-revision:base",
        "scheduler_lifecycle": "tool-bounded",
        "attestation": _attestation(),
    }
    values.update(changes)
    return ImportedActionsRuntimePorts(**values)


def test_real_runtime_ports_are_structurally_validated() -> None:
    ports = _ports()
    assert validate_imported_actions_runtime_ports(ports) is ports
    assert ports.to_attestation_mapping()["embedding_dimension"] == 384


def test_attestation_rejects_dummy_or_non_384_backends() -> None:
    with pytest.raises(ImportedActionsRuntimeContractError):
        _attestation(openvino_e5_real=False)
    with pytest.raises(ImportedActionsRuntimeContractError):
        _attestation(qdrant_write_real=False)
    with pytest.raises(ImportedActionsRuntimeContractError):
        _attestation(embedding_dimension=385)
    with pytest.raises(ImportedActionsRuntimeContractError):
        _attestation(evidence_refs=())
    with pytest.raises(ImportedActionsRuntimeContractError):
        _attestation(scheduler_lifecycle="unknown")


def test_runtime_ports_reject_missing_required_methods() -> None:
    with pytest.raises(ImportedActionsRuntimeContractError):
        _ports(embedder=object())
    with pytest.raises(ImportedActionsRuntimeContractError):
        _ports(runtime_ref="runtime:other")
    with pytest.raises(ImportedActionsRuntimeContractError):
        _ports(scheduler_lifecycle="externally-managed")
