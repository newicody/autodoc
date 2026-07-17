from __future__ import annotations

import pytest

from context.love_imported_actions_run_preview_0287 import (
    GitHubActionsArtifactIdentity,
    LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA,
    LoveImportedActionsRunPreviewCommand,
    LoveImportedActionsRunPreviewError,
    correlate_imported_actions_run_preview,
)
from context.love_imported_actions_runtime_contract_0287 import (
    IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
    ImportedActionsRealBackendAttestation,
)


def _artifacts():
    names = (
        (1, "autodoc-authoritative-request", "authoritative_request.json"),
        (2, "autodoc-copilot-advisory", "copilot_advisory.json"),
        (3, "autodoc-dual-artifact-manifest", "dual_artifact_manifest.json"),
    )
    return tuple(
        GitHubActionsArtifactIdentity(
            artifact_id=artifact_id,
            artifact_name=name,
            filename=filename,
            archive_size_in_bytes=100,
            content_size_in_bytes=80,
            content_digest=str(artifact_id) * 64,
            created_at="2026-07-17T20:00:00Z",
        )
        for artifact_id, name, filename in names
    )


def _attestation(**changes):
    values = {
        "schema": IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA,
        "runtime_ref": "runtime:autodoc-live-love",
        "scheduler_ref": "scheduler:main",
        "sql_authority_ref": "sql-authority:context-revision",
        "projection_backend_ref": "qdrant:local-live",
        "embedding_backend_ref": "openvino:embedding.e5-small",
        "retrieval_backend_ref": "hybrid-retrieval:qdrant-sql",
        "model_ref": "model:multilingual-e5-small",
        "model_revision": "local-openvino-ir-v1",
        "qdrant_collection": "autodoc_context",
        "evidence_refs": (
            "evidence:openvino-model-readback",
            "evidence:qdrant-write-readback",
        ),
        "scheduler_lifecycle": "tool-bounded",
    }
    values.update(changes)
    return ImportedActionsRealBackendAttestation(**values)


def _command(**changes):
    values = {
        "schema": LOVE_IMPORTED_ACTIONS_RUN_PREVIEW_COMMAND_SCHEMA,
        "repository": "newicody/projects",
        "run_id": "12345",
        "workflow_name": "autodoc-controlled-research",
        "workflow_conclusion": "success",
        "artifacts": _artifacts(),
        "runtime_attestation": _attestation(),
    }
    values.update(changes)
    return LoveImportedActionsRunPreviewCommand(**values)


def _r14(collection_name="autodoc_context"):
    receipt = {
        "openvino_e5_used": True,
        "qdrant_write_performed": True,
        "projection": {
            "dimension": 384,
            "normalized": True,
            "collection_name": collection_name,
        },
    }
    return {
        "schema": "missipy.love.full_deterministic_local_smoke_result.v1",
        "proof_digest": "a" * 64,
        "run_assembly": {
            "repository": "newicody/projects",
            "run_id": "12345",
            "valid": True,
        },
        "synthesis_result": {
            "projection_receipts": [receipt, dict(receipt)],
        },
        "publication_plan": {
            "plan_digest": "b" * 64,
            "valid": True,
        },
    }


def _preview(**changes):
    values = {
        "valid": True,
        "mode": "preview",
        "action": "preview",
        "plan_digest": "b" * 64,
        "remote_mutation_performed": False,
    }
    values.update(changes)
    return values


def test_correlation_keeps_r14_plan_directly_consumable_by_r15_r1() -> None:
    result = correlate_imported_actions_run_preview(
        _command(),
        r14_result=_r14(),
        publication_preview=_preview(),
    )

    mapping = result.to_mapping()
    assert result.valid is True
    assert mapping["publication_plan"]["plan_digest"] == "b" * 64
    assert mapping["_r15_import"]["artifact_ids"] == [1, 2, 3]
    assert mapping["_r15_import"]["preview_required"] is True
    assert mapping["_r15_import"]["live_path_status"] == "real-backend-preview"
    assert mapping["_r15_import"]["live_path_uses_real_backend"] is True
    assert mapping["_r15_import"]["runtime_attestation"]["openvino_e5_real"] is True
    assert mapping["remote_publication_preview"]["mode"] == "preview"


def test_correlation_rejects_digest_or_run_mismatch() -> None:
    r14 = _r14()
    r14["run_assembly"] = {
        "repository": "newicody/projects",
        "run_id": "different",
        "valid": True,
    }
    result = correlate_imported_actions_run_preview(
        _command(),
        r14_result=r14,
        publication_preview=_preview(plan_digest="c" * 64),
    )

    assert result.valid is False
    assert "r14 run_id differs" in " ".join(result.issues)
    assert "plan_digest differs" in " ".join(result.issues)


def test_preview_must_never_report_remote_mutation() -> None:
    result = correlate_imported_actions_run_preview(
        _command(),
        r14_result=_r14(),
        publication_preview=_preview(remote_mutation_performed=True),
    )

    assert result.valid is False
    assert "remote mutation" in " ".join(result.issues)


def test_projection_receipts_must_match_real_runtime_attestation() -> None:
    result = correlate_imported_actions_run_preview(
        _command(),
        r14_result=_r14(collection_name="wrong_collection"),
        publication_preview=_preview(),
    )
    assert result.valid is False
    assert "collection differs" in " ".join(result.issues)

    broken = _r14()
    broken["synthesis_result"]["projection_receipts"][0][
        "openvino_e5_used"
    ] = False
    result = correlate_imported_actions_run_preview(
        _command(),
        r14_result=broken,
        publication_preview=_preview(),
    )
    assert result.valid is False
    assert "OpenVINO/E5 proof" in " ".join(result.issues)


def test_exact_three_non_expired_artifacts_are_required() -> None:
    with pytest.raises(LoveImportedActionsRunPreviewError):
        _command(artifacts=_artifacts()[:2])
    with pytest.raises(LoveImportedActionsRunPreviewError):
        GitHubActionsArtifactIdentity(
            artifact_id=1,
            artifact_name="autodoc-authoritative-request",
            filename="authoritative_request.json",
            archive_size_in_bytes=10,
            content_size_in_bytes=8,
            content_digest="d" * 64,
            created_at="2026-07-17T20:00:00Z",
            expired=True,
        )


def test_artifact_digest_must_be_lowercase_sha256_hex() -> None:
    with pytest.raises(LoveImportedActionsRunPreviewError):
        GitHubActionsArtifactIdentity(
            artifact_id=9,
            artifact_name="autodoc-authoritative-request",
            filename="authoritative_request.json",
            archive_size_in_bytes=10,
            content_size_in_bytes=8,
            content_digest="z" * 64,
            created_at="2026-07-17T20:00:00Z",
        )
