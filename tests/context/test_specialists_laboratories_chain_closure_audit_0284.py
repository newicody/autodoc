from context.specialists_laboratories_chain_closure_audit_0284 import (
    FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES,
    REQUIRED_CHAIN_SURFACES,
    REQUIRED_SUPPORT_SURFACES,
    Phase0284OperationalEvidence,
    audit_specialists_laboratories_chain_closure,
)


def _complete_sources() -> dict[str, str]:
    return {
        requirement.path: "\n".join(requirement.markers)
        for requirement in REQUIRED_CHAIN_SURFACES + REQUIRED_SUPPORT_SURFACES
    }


def _green_evidence() -> Phase0284OperationalEvidence:
    return Phase0284OperationalEvidence(
        fake_specialist_scheduler_closed=True,
        existing_scheduler_path_verified=True,
        real_sql_authority_used=True,
        real_openvino_e5_used=True,
        real_qdrant_projection_used=True,
        real_qdrant_recall_used=True,
        qdrant_returns_references_only=True,
        sql_rehydration_verified=True,
        portable_identity_preserved=True,
        artifact_correlation_verified=True,
        advisory_context_injected=True,
        source_candidate_injected=True,
        integrated_closed_loop_complete=True,
        publication_plan_ready=True,
        projects_projection_ready=True,
    )


def test_complete_implementation_without_live_evidence_remains_transition() -> None:
    result = audit_specialists_laboratories_chain_closure(_complete_sources())

    assert result.valid is True
    assert result.implementation_complete is True
    assert result.operational_evidence_supplied is False
    assert result.operationally_green is False
    assert result.phase_0284_closed is False
    assert result.live_path_status == "transition"
    assert result.next_recommended_patch.endswith("live-path-evidence")


def test_real_evidence_closes_phase_0284_green() -> None:
    result = audit_specialists_laboratories_chain_closure(
        _complete_sources(),
        _green_evidence(),
    )

    assert result.valid is True
    assert result.operationally_green is True
    assert result.phase_0284_closed is True
    assert result.live_path_status == "green"
    assert result.to_mapping()["live_path_uses_real_backend"] is True
    assert result.next_recommended_patch.startswith("0285-r1")


def test_missing_or_incomplete_surface_is_red() -> None:
    sources = _complete_sources()
    removed = REQUIRED_CHAIN_SURFACES[2].path
    sources.pop(removed)
    sources[REQUIRED_SUPPORT_SURFACES[1].path] = "wrong"

    result = audit_specialists_laboratories_chain_closure(
        sources,
        _green_evidence(),
    )

    assert result.valid is False
    assert result.phase_0284_closed is False
    assert result.live_path_status == "red"
    assert removed in result.missing_required_surfaces
    assert REQUIRED_SUPPORT_SURFACES[1].path in result.incomplete_required_surfaces


def test_active_project_workflow_in_autodoc_blocks_closure() -> None:
    sources = _complete_sources()
    forbidden = FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES[0]
    sources[forbidden] = "name: forbidden"

    result = audit_specialists_laboratories_chain_closure(
        sources,
        _green_evidence(),
    )

    assert result.valid is False
    assert result.forbidden_active_surfaces == (forbidden,)
    assert result.projects_configuration_owned_by == "newicody/projects"


def test_remote_mutation_cannot_be_used_as_smoke_evidence() -> None:
    evidence = _green_evidence()
    values = evidence.to_mapping()
    values.pop("green")
    values["github_mutation_performed"] = True
    mutated = Phase0284OperationalEvidence(**values)

    result = audit_specialists_laboratories_chain_closure(
        _complete_sources(),
        mutated,
    )

    assert result.valid is True
    assert result.operationally_green is False
    assert result.phase_0284_closed is False
