from context.multi_laboratory_evidence_aggregation_reuse_audit_0287 import (
    DEVELOPMENT_PHASES,
    REQUIRED_REUSE_SURFACES,
    audit_multi_laboratory_evidence_aggregation_reuse,
)


def _complete_sources() -> dict[str, str]:
    return {
        requirement.path: "\n".join(requirement.markers)
        for requirement in REQUIRED_REUSE_SURFACES
    }


def test_complete_reuse_surfaces_recommend_r2() -> None:
    result = audit_multi_laboratory_evidence_aggregation_reuse(
        _complete_sources()
    )
    assert result.valid is True
    assert result.completed_phases == ()
    assert result.next_recommended_patch == (
        "0287-r2-multi-laboratory-evidence-aggregation-contract"
    )
    assert result.visit_evidence_vocabulary_reusable is True
    assert result.transfer_continuity_reusable is True
    assert result.digest_bound_evidence_reusable is True


def test_missing_surface_is_reported() -> None:
    sources = _complete_sources()
    missing = REQUIRED_REUSE_SURFACES[0].path
    del sources[missing]
    result = audit_multi_laboratory_evidence_aggregation_reuse(sources)
    assert result.valid is False
    assert missing in result.missing_reuse_surfaces


def test_incomplete_surface_is_reported() -> None:
    sources = _complete_sources()
    requirement = REQUIRED_REUSE_SURFACES[2]
    sources[requirement.path] = requirement.markers[0]
    result = audit_multi_laboratory_evidence_aggregation_reuse(sources)
    assert result.valid is False
    assert requirement.path in result.incomplete_reuse_surfaces


def test_r2_surface_advances_to_r3() -> None:
    sources = _complete_sources()
    for requirement in DEVELOPMENT_PHASES[0].requirements:
        sources[requirement.path] = "\n".join(requirement.markers)
    result = audit_multi_laboratory_evidence_aggregation_reuse(sources)
    assert result.completed_phases == (
        "0287-r2-multi-laboratory-evidence-aggregation-contract",
    )
    assert result.next_recommended_patch == (
        "0287-r3-multi-laboratory-evidence-provenance-contract"
    )


def test_phase_progression_is_contiguous() -> None:
    sources = _complete_sources()
    for requirement in DEVELOPMENT_PHASES[1].requirements:
        sources[requirement.path] = "\n".join(requirement.markers)
    result = audit_multi_laboratory_evidence_aggregation_reuse(sources)
    assert result.completed_phases == ()
    assert result.next_recommended_patch == DEVELOPMENT_PHASES[0].patch_id


def test_authority_boundaries_are_locked() -> None:
    mapping = audit_multi_laboratory_evidence_aggregation_reuse(
        _complete_sources()
    ).to_mapping()
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["qdrant_remains_projection_and_recall"] is True
    assert mapping["eventbus_remains_observation_only"] is True
    assert mapping["laboratory_self_authorization_allowed"] is False
    assert mapping["new_scheduler_required"] is False
    assert mapping["new_laboratory_manager_required"] is False
    assert mapping["new_global_evidence_registry_required"] is False
