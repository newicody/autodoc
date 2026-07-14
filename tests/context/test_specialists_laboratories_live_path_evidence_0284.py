from copy import deepcopy

from context.specialists_laboratories_chain_closure_audit_0284 import (
    REQUIRED_CHAIN_SURFACES,
    REQUIRED_SUPPORT_SURFACES,
)
from context.specialists_laboratories_live_path_evidence_0284 import (
    SpecialistsLaboratoriesLivePathEvidenceCommand,
    build_specialists_laboratories_live_path_evidence,
)


def _sources() -> dict[str, str]:
    return {
        requirement.path: "\n".join(requirement.markers)
        for requirement in REQUIRED_CHAIN_SURFACES + REQUIRED_SUPPORT_SURFACES
    }


def _command() -> SpecialistsLaboratoriesLivePathEvidenceCommand:
    return SpecialistsLaboratoriesLivePathEvidenceCommand(
        evidence_ref="evidence:0284-r9:run-123",
        repository="newicody/projects",
        run_id="123",
        source_revision="d31290d",
    )


def _integrated_result() -> dict[str, object]:
    policy = "policy:0284:r9:real-path"
    sql_ref = "sql:context:portable-specialist-123"
    return {
        "schema": "missipy.github.projects_copilot_specialist_smoke_result.v1",
        "valid": True,
        "issues": [],
        "command": {
            "repository": "newicody/projects",
            "run_id": "123",
            "policy_decision_id": policy,
            "memory": {
                "execute": True,
                "authorize_real_memory": True,
                "authorize_persistent_qdrant_point": True,
                "projection_configuration": {
                    "target": {"vector_dimension": 384},
                    "effect_gate": {"policy_decision_id": policy},
                },
                "recall_configuration": {
                    "target": {"vector_dimension": 384},
                    "effect_gate": {"policy_decision_id": policy},
                },
                "specialist_smoke": {
                    "smoke": {
                        "handoff": {"policy_decision_id": policy},
                        "recall": {"policy_decision_id": policy},
                    }
                },
            },
        },
        "assembly": {
            "intake": {
                "source_candidate": {"candidate_id": "candidate:123"},
            }
        },
        "memory": {
            "valid": True,
            "issues": [],
            "preview_only": False,
            "real_sql_authority_used": True,
            "real_openvino_e5_used": True,
            "real_qdrant_projection_used": True,
            "real_qdrant_recall_used": True,
            "qdrant_returns_references_only": True,
            "sql_rehydration_verified": True,
            "portable_identity_preserved": True,
            "memory_closed": True,
            "persistent_qdrant_point_created": True,
            "existing_scheduler_used": True,
            "automatic_cleanup_performed": False,
            "scheduler_created": False,
            "scheduler_modified": False,
            "new_qdrant_executor_added": False,
            "new_transport_added": False,
            "github_mutation_performed": False,
            "embedding_runtime_injected": False,
            "sql_ref": sql_ref,
            "passage_embedding_ref": "embedding:passage:123",
            "query_embedding_ref": "embedding:query:123",
            "specialist_smoke": {
                "existing_scheduler_path_verified": True,
                "portable_identity_preserved": True,
            },
        },
        "publication_preview": {"laboratory_source_sql_ref": sql_ref},
        "artifact_correlation_verified": True,
        "advisory_context_injected": True,
        "source_candidate_injected": True,
        "request_authoritative": True,
        "advisory_used_as_hint_only": True,
        "real_memory_closed": True,
        "publication_plan_ready": True,
        "projects_projection_ready": True,
        "integrated_closed_loop_complete": True,
        "existing_scheduler_used": True,
        "scheduler_created": False,
        "scheduler_modified": False,
        "parallel_orchestrator_created": False,
        "github_mutation_performed": False,
        "projectv2_mutation_performed": False,
    }


def test_correlated_real_result_closes_phase_0284() -> None:
    result = build_specialists_laboratories_live_path_evidence(
        _command(), _integrated_result(), _sources()
    )

    assert result.valid is True
    assert result.phase_0284_closed is True
    assert result.live_path_status == "green"
    assert result.vector_dimensions == (384, 384)
    assert result.sql_ref.startswith("sql:")
    assert result.operational_evidence.green is True
    assert result.closure_audit.next_recommended_patch.startswith("0285-r1")
    assert result.to_mapping()["new_scheduler_added"] is False


def test_evidence_digest_is_deterministic() -> None:
    first = build_specialists_laboratories_live_path_evidence(
        _command(), _integrated_result(), _sources()
    )
    second = build_specialists_laboratories_live_path_evidence(
        _command(), _integrated_result(), _sources()
    )

    assert first.integrated_result_digest == second.integrated_result_digest
    assert first.evidence_digest == second.evidence_digest


def test_dimension_385_is_rejected_and_never_closes() -> None:
    integrated = _integrated_result()
    integrated["command"]["memory"]["projection_configuration"]["target"][
        "vector_dimension"
    ] = 385

    result = build_specialists_laboratories_live_path_evidence(
        _command(), integrated, _sources()
    )

    assert result.valid is False
    assert result.phase_0284_closed is False
    assert "all Qdrant vector dimensions must be exactly 384" in result.issues


def test_remote_mutation_cannot_be_live_path_evidence() -> None:
    integrated = _integrated_result()
    integrated["github_mutation_performed"] = True

    result = build_specialists_laboratories_live_path_evidence(
        _command(), integrated, _sources()
    )

    assert result.valid is False
    assert result.operational_evidence.green is False
    assert any("github_mutation_performed=false" in issue for issue in result.issues)


def test_repository_source_gap_keeps_phase_open() -> None:
    sources = _sources()
    sources.pop(REQUIRED_CHAIN_SURFACES[0].path)

    result = build_specialists_laboratories_live_path_evidence(
        _command(), _integrated_result(), sources
    )

    assert result.valid is False
    assert result.closure_audit.valid is False
    assert result.live_path_status == "red"


def test_result_is_a_deep_json_snapshot() -> None:
    integrated = _integrated_result()
    result = build_specialists_laboratories_live_path_evidence(
        _command(), integrated, _sources()
    )
    before = deepcopy(result.to_mapping()["integrated_result"])
    integrated["memory"]["sql_ref"] = "sql:changed"

    assert result.to_mapping()["integrated_result"] == before
