from __future__ import annotations

import json
from pathlib import Path

from context.specialist_capability_growth_projects_operator_workflow_reuse_audit_0286 import (
    DEVELOPMENT_PHASES,
    REQUIRED_REUSE_SURFACES,
    audit_specialist_capability_growth_projects_operator_workflow_reuse,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "templates/github/projects-repository/projectv2_views.json"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"

EXPECTED_FIELDS = (
    "Spécialiste",
    "Révision spécialiste",
    "Capacité proposée",
    "Action capacité",
    "Décision capacité",
    "Statut révision",
    "Référence SQL",
    "Digest décision",
    "Laboratoire",
)


def _configuration() -> dict[str, object]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _field_map() -> dict[str, dict[str, object]]:
    configuration = _configuration()
    fields = configuration["fields"]
    assert isinstance(fields, list)
    return {str(item["name"]): item for item in fields}


def test_specialist_review_fields_are_declared_once() -> None:
    fields = _field_map()
    assert all(name in fields for name in EXPECTED_FIELDS)
    assert len(fields) == len(set(fields))
    assert fields["Spécialiste"]["data_type"] == "text"
    assert fields["Révision spécialiste"]["data_type"] == "text"
    assert fields["Référence SQL"]["data_type"] == "text"
    assert fields["Digest décision"]["data_type"] == "text"


def test_machine_values_match_the_local_projection_contract() -> None:
    fields = _field_map()

    def option_names(name: str) -> tuple[str, ...]:
        options = fields[name]["options"]
        assert isinstance(options, list)
        return tuple(str(option["name"]) for option in options)

    assert option_names("Action capacité") == (
        "add",
        "refine",
        "deprecate",
        "restore",
    )
    assert option_names("Décision capacité") == (
        "pending",
        "approve",
        "reject",
        "defer",
    )
    assert "approved_selected_observed" in option_names("Statut révision")
    assert "readback_verified" in option_names("Statut révision")


def test_projection_mapping_reuses_exact_field_names() -> None:
    configuration = _configuration()
    projection = configuration["specialist_capability_growth_projection"]
    assert isinstance(projection, dict)
    projected_fields = tuple(
        projection[key]
        for key in (
            "specialist_field",
            "revision_field",
            "capability_field",
            "action_field",
            "decision_field",
            "revision_status_field",
            "sql_ref_field",
            "decision_digest_field",
            "laboratory_field",
        )
    )
    assert projected_fields == EXPECTED_FIELDS
    assert projection["review_status_value"] == "approved_selected_observed"


def test_specialist_revision_review_view_is_table_only() -> None:
    configuration = _configuration()
    views = configuration["views"]
    assert isinstance(views, list)
    matching = [view for view in views if view.get("name") == "Révisions spécialistes"]
    assert len(matching) == 1
    view = matching[0]
    assert view["layout"] == "table"
    assert view["filter"] == "Action capacité:add,refine,deprecate,restore"
    for name in EXPECTED_FIELDS:
        assert name in view["visible_fields"]
    assert "manual_layout" not in view


def test_audit_advances_through_r4_to_publication_plan() -> None:
    sources: dict[str, str] = {
        requirement.path: "\n".join(requirement.markers)
        for requirement in REQUIRED_REUSE_SURFACES
    }
    workflow_path = (
        "templates/github/projects-repository/.github/workflows/"
        "autodoc-controlled-research.yml"
    )
    sources[workflow_path] += "\nissues: read\nactions: read\n"

    for phase in DEVELOPMENT_PHASES[:3]:
        for requirement in phase.requirements:
            if requirement.path.endswith("projectv2_views.json"):
                sources[requirement.path] = CONFIG.read_text(encoding="utf-8")
            elif requirement.path.endswith("INSTALLATION.md"):
                sources[requirement.path] = INSTALLATION.read_text(encoding="utf-8")
            else:
                sources[requirement.path] = "\n".join(requirement.markers)

    result = audit_specialist_capability_growth_projects_operator_workflow_reuse(
        sources
    )
    assert result.valid is True
    assert result.completed_phases[:3] == tuple(
        phase.patch_id for phase in DEVELOPMENT_PHASES[:3]
    )
    assert result.next_recommended_patch == DEVELOPMENT_PHASES[3].patch_id
    assert result.specialist_revision_fields_present is True
    assert result.operator_decision_view_present is True
