from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.github_project_v2_theme_grouping_deployment_plan_0282 import (
    GitHubProjectV2ThemeAssignmentSpec,
    GitHubProjectV2ThemeFieldSnapshot,
    GitHubProjectV2ThemeGroupingDeploymentCommand,
    GitHubProjectV2ThemeGroupingDeploymentPolicy,
    GitHubProjectV2ThemeOptionSnapshot,
    GitHubProjectV2ThemeOptionSpec,
    GitHubProjectV2ViewGroupingSnapshot,
    plan_github_project_v2_theme_grouping_deployment,
)


PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"


def _options():
    return (
        GitHubProjectV2ThemeOptionSpec(
            name="Général",
            color="BLUE",
            description="Recherche générale",
        ),
        GitHubProjectV2ThemeOptionSpec(
            name="Chalouf",
            color="GREEN",
            description="Projet intégrateur",
        ),
    )


def _command(**overrides):
    values = {
        "owner_kind": "user",
        "owner_login": "newicody",
        "project_number": 3,
        "project_id": PROJECT_ID,
        "field_name": "Thème",
        "desired_options": _options(),
        "existing_fields": (),
        "assignments": (),
        "views": (),
        "target_view_number": 2,
    }
    values.update(overrides)
    return GitHubProjectV2ThemeGroupingDeploymentCommand(**values)


def _existing_field():
    return GitHubProjectV2ThemeFieldSnapshot(
        field_id="PVTF_theme",
        name="Thème",
        data_type="single_select",
        options=(
            GitHubProjectV2ThemeOptionSnapshot(
                option_id="theme-general",
                name="Général",
                color="BLUE",
                description="Recherche générale",
            ),
            GitHubProjectV2ThemeOptionSnapshot(
                option_id="theme-chalouf",
                name="Chalouf",
                color="GREEN",
                description="Projet intégrateur",
            ),
        ),
    )


def test_missing_field_plans_user_rest_creation_and_manual_grouping():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command()
    )

    assert result.valid is True
    assert result.action == "create_field"
    assert result.view_grouping_action == "manual_grouping_required"
    assert result.operations[0].transport_kind == "rest"
    assert result.operations[0].endpoint_or_mutation == (
        "POST /users/newicody/projectsV2/3/fields"
    )
    assert result.operations[0].execution_allowed is False
    assert result.operations[0].requires_response_resolution is True


def test_exact_existing_field_and_grouped_view_is_replay():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            existing_fields=(_existing_field(),),
            views=(
                GitHubProjectV2ViewGroupingSnapshot(
                    view_number=2,
                    view_name="Board",
                    grouped_field_id="PVTF_theme",
                ),
            ),
        )
    )

    assert result.valid is True
    assert result.action == "reuse_field"
    assert result.view_grouping_action == "replay"
    assert result.operations == ()
    assert result.field_id == "PVTF_theme"


def test_added_option_plans_graphql_update_and_preserves_ids():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            desired_options=_options()
            + (
                GitHubProjectV2ThemeOptionSpec(
                    name="Laboratoire",
                    color="PURPLE",
                ),
            ),
            existing_fields=(_existing_field(),),
        )
    )

    assert result.valid is True
    assert result.action == "update_field"
    operation = result.operations[0]
    assert operation.operation_name == "updateProjectV2Field"
    payload = dict(operation.payload)
    options = payload["singleSelectOptions"]
    assert options[0]["id"] == "theme-chalouf"
    assert options[1]["id"] == "theme-general"
    assert "id" not in options[2]


def test_removing_option_is_collision_by_default():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            desired_options=(_options()[0],),
            existing_fields=(_existing_field(),),
        )
    )

    assert result.valid is False
    assert result.action == "collision"
    assert (
        "desired options would remove existing options"
        in result.issues
    )
    assert result.operations == ()


def test_wrong_field_type_is_collision():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            existing_fields=(
                GitHubProjectV2ThemeFieldSnapshot(
                    field_id="PVTF_theme",
                    name="Thème",
                    data_type="text",
                ),
            ),
        )
    )

    assert result.valid is False
    assert "existing theme field is not single_select" in result.issues


def test_duplicate_matching_fields_are_collision():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            existing_fields=(
                _existing_field(),
                GitHubProjectV2ThemeFieldSnapshot(
                    field_id="PVTF_theme_2",
                    name="thème",
                    data_type="single_select",
                ),
            ),
        )
    )

    assert result.valid is False
    assert "multiple existing fields match field_name" in result.issues


def test_assignments_use_existing_option_ids():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            existing_fields=(_existing_field(),),
            assignments=(
                GitHubProjectV2ThemeAssignmentSpec(
                    project_item_ref=(
                        "github-project-v2-item:PVTI_15"
                    ),
                    theme_name="Général",
                ),
            ),
        )
    )

    assert result.valid is True
    operation = result.operations[0]
    assert operation.operation_name == "updateProjectV2ItemFieldValue"
    payload = dict(operation.payload)
    assert payload["fieldId"] == "PVTF_theme"
    assert payload["singleSelectOptionId"] == "theme-general"
    assert operation.requires_response_resolution is False


def test_new_field_assignment_is_staged_until_ids_are_resolved():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            assignments=(
                GitHubProjectV2ThemeAssignmentSpec(
                    project_item_ref=(
                        "github-project-v2-item:PVTI_15"
                    ),
                    theme_name="Général",
                ),
            ),
        )
    )

    assert result.valid is True
    assignment = result.operations[1]
    assert assignment.operation_kind == "item_theme_assignment"
    assert assignment.requires_response_resolution is True


def test_view_grouped_by_other_field_is_collision():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(
            existing_fields=(_existing_field(),),
            views=(
                GitHubProjectV2ViewGroupingSnapshot(
                    view_number=2,
                    view_name="Board",
                    grouped_field_id="PVTF_other",
                ),
            ),
        )
    )

    assert result.valid is False
    assert result.view_grouping_action == "view_collision"


def test_manual_grouping_can_be_forbidden_by_policy():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command(existing_fields=(_existing_field(),)),
        GitHubProjectV2ThemeGroupingDeploymentPolicy(
            allow_manual_view_grouping=False,
        ),
    )

    assert result.valid is False
    assert any("manual grouping is forbidden" in x for x in result.issues)


def test_plan_is_deterministic_across_input_order():
    options = _options()
    first = plan_github_project_v2_theme_grouping_deployment(
        _command(desired_options=options)
    )
    second = plan_github_project_v2_theme_grouping_deployment(
        _command(desired_options=tuple(reversed(options)))
    )

    assert first == second
    assert first.plan_ref.startswith(
        "github-project-v2-theme-grouping-plan:"
    )


def test_boundaries_are_locked():
    result = plan_github_project_v2_theme_grouping_deployment(
        _command()
    )
    assert dict(result.boundaries) == {
        "plan_only": True,
        "external_call_performed": False,
        "rest_mutation_allowed": False,
        "graphql_mutation_allowed": False,
        "github_mutation_performed": False,
        "view_mutation_automated": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


def test_contracts_are_frozen():
    option = _options()[0]
    with pytest.raises(FrozenInstanceError):
        option.name = "Changed"  # type: ignore[misc]
