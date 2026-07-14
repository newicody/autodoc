from __future__ import annotations

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    DEVELOPMENT_PHASES,
    REQUIRED_REUSE_SURFACES,
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
)


def _base_sources() -> dict[str, str]:
    sources: dict[str, str] = {}
    for requirement in REQUIRED_REUSE_SURFACES:
        sources[requirement.path] = "\n".join(requirement.markers)
    workflow_path = (
        "templates/github/projects-repository/.github/workflows/"
        "autodoc-controlled-research.yml"
    )
    sources[workflow_path] += "\nissues: read\nactions: read\n"
    return sources


def test_current_reuse_surfaces_are_valid_and_r2_is_next() -> None:
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        _base_sources()
    )
    assert result.valid is True
    assert result.next_recommended_patch.startswith("0286-r2-")
    assert result.completed_phases == ()
    assert result.dedicated_growth_issue_form_present is False
    assert result.specialist_revision_fields_present is False
    assert result.operator_decision_view_present is False
    assert result.workflow_is_read_only_for_issues is True
    assert result.installation_reviewed is True
    assert result.installation_update_required is False


def test_missing_reuse_surface_invalidates_audit() -> None:
    sources = _base_sources()
    missing = REQUIRED_REUSE_SURFACES[0].path
    del sources[missing]
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(sources)
    assert result.valid is False
    assert result.missing_reuse_surfaces == (missing,)


def test_incomplete_surface_is_reported_without_execution() -> None:
    sources = _base_sources()
    target = REQUIRED_REUSE_SURFACES[1]
    sources[target.path] = target.markers[0]
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(sources)
    assert result.valid is False
    assert result.incomplete_reuse_surfaces == (target.path,)


def test_phase_detection_is_sequential_and_supports_non_python_bundle_markers() -> None:
    sources = _base_sources()
    first = DEVELOPMENT_PHASES[0]
    for requirement in first.requirements:
        sources[requirement.path] = "\n".join(requirement.markers)
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(sources)
    assert result.completed_phases == (first.patch_id,)
    assert result.next_recommended_patch == DEVELOPMENT_PHASES[1].patch_id


def test_all_planned_phases_close_0286() -> None:
    sources = _base_sources()
    for phase in DEVELOPMENT_PHASES:
        for requirement in phase.requirements:
            existing = sources.get(requirement.path, "")
            sources[requirement.path] = existing + "\n" + "\n".join(requirement.markers)
    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(sources)
    assert result.valid is True
    assert result.completed_phases == tuple(phase.patch_id for phase in DEVELOPMENT_PHASES)
    assert result.next_recommended_patch == "0286-complete"
    assert result.dedicated_growth_issue_form_present is True
    assert result.specialist_revision_fields_present is True
    assert result.operator_decision_view_present is True


def test_digest_is_deterministic_and_sensitive_to_source_change() -> None:
    first = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        _base_sources()
    )
    second_sources = _base_sources()
    second = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        dict(reversed(tuple(second_sources.items())))
    )
    assert first.source_digest == second.source_digest
    changed = _base_sources()
    changed[REQUIRED_REUSE_SURFACES[0].path] += "\nchanged"
    third = audit_specialist_capability_growth_projects_operator_workflow_reuse(changed)
    assert third.source_digest != first.source_digest


def test_mapping_locks_authority_boundaries() -> None:
    mapping = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        _base_sources()
    ).to_mapping()
    assert mapping["github_projects_authoritative"] is False
    assert mapping["operator_gate_reused"] is True
    assert mapping["sql_remains_durable_authority"] is True
    assert mapping["scheduler_remains_only_orchestrator"] is True
    assert mapping["qdrant_remains_projection_and_recall_only"] is True
    assert mapping["copilot_remains_advisory"] is True
    assert mapping["new_scheduler_required"] is False
    assert mapping["new_global_specialist_registry_required"] is False
    assert mapping["new_http_client_required"] is False
