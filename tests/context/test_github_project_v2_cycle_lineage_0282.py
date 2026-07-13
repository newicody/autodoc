from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.github_project_push_frame import (
    build_origin_frame_id,
    build_ticket_revision_id,
)
from context.github_project_v2_cycle_lineage_0282 import (
    CYCLE_LINEAGE_RESULT_SCHEMA,
    GitHubProjectV2CycleLineageCommand,
    GitHubProjectV2CycleLineagePolicy,
    build_github_project_v2_cycle_lineage,
    build_github_project_v2_issue_ref,
    build_github_project_v2_item_ref,
    build_github_project_v2_theme_ref,
)


REPOSITORY = "newicody/projects"
PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"
ROOT_REF = build_origin_frame_id(REPOSITORY, 15)
STATUS_REVISION = build_ticket_revision_id(
    ROOT_REF,
    "status_changed",
    "en-cours",
)
ITEM_REF = build_github_project_v2_item_ref("PVTI_cycle_15")
THEME_REF = build_github_project_v2_theme_ref(
    PROJECT_ID,
    "PVTF_theme",
    "general",
)


def _initial_command() -> GitHubProjectV2CycleLineageCommand:
    return GitHubProjectV2CycleLineageCommand(
        repository=REPOSITORY,
        project_id=PROJECT_ID,
        project_item_ref=ITEM_REF,
        root_issue_ref=ROOT_REF,
        cycle_ordinal=1,
        status_revision_ref=STATUS_REVISION,
        theme_refs=(THEME_REF,),
        metadata=(("source", "project_v2"),),
    )


def test_initial_cycle_is_valid_deterministic_and_local_only() -> None:
    first = build_github_project_v2_cycle_lineage(
        _initial_command()
    )
    replay = build_github_project_v2_cycle_lineage(
        _initial_command()
    )

    assert first.valid is True
    assert first.issues == ()
    assert first.cycle_ref.startswith(
        "github-project-v2-cycle:"
    )
    assert first == replay

    payload = first.to_json_dict()
    assert payload["schema"] == CYCLE_LINEAGE_RESULT_SCHEMA
    assert payload["root_issue_ref"] == ROOT_REF
    assert payload["theme_refs"] == [THEME_REF]
    assert payload["metadata"] == {"source": "project_v2"}
    assert payload["boundaries"] == {
        "contract_only": True,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


def test_following_cycle_requires_parent_and_previous_cycle() -> None:
    first = build_github_project_v2_cycle_lineage(
        _initial_command()
    )
    child_ref = build_github_project_v2_issue_ref(
        REPOSITORY,
        16,
    )
    second = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=build_github_project_v2_item_ref(
                "PVTI_cycle_16"
            ),
            root_issue_ref=ROOT_REF,
            parent_issue_ref=ROOT_REF,
            previous_cycle_ref=first.cycle_ref,
            cycle_ordinal=2,
            status_revision_ref=build_ticket_revision_id(
                child_ref,
                "status_changed",
                "en-cours",
            ),
            sub_issue_refs=(child_ref,),
            theme_refs=(THEME_REF,),
        )
    )

    assert second.valid is True
    assert second.previous_cycle_ref == first.cycle_ref
    assert second.parent_issue_ref == ROOT_REF


@pytest.mark.parametrize(
    ("parent_ref", "previous_ref", "expected"),
    (
        (
            "",
            "github-project-v2-cycle:previous",
            "parent_issue_ref is required after initial cycle",
        ),
        (
            ROOT_REF,
            "",
            "previous_cycle_ref is required after initial cycle",
        ),
    ),
)
def test_following_cycle_policy_rejects_missing_lineage_link(
    parent_ref: str,
    previous_ref: str,
    expected: str,
) -> None:
    result = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=ITEM_REF,
            root_issue_ref=ROOT_REF,
            parent_issue_ref=parent_ref,
            previous_cycle_ref=previous_ref,
            cycle_ordinal=2,
            status_revision_ref=STATUS_REVISION,
        )
    )

    assert result.valid is False
    assert expected in result.issues
    assert result.cycle_ref == ""


def test_initial_cycle_rejects_parent_and_previous_cycle() -> None:
    result = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=ITEM_REF,
            root_issue_ref=ROOT_REF,
            parent_issue_ref=ROOT_REF,
            previous_cycle_ref=(
                "github-project-v2-cycle:previous"
            ),
            cycle_ordinal=1,
            status_revision_ref=STATUS_REVISION,
        )
    )

    assert result.valid is False
    assert (
        "initial cycle must not reference previous_cycle_ref"
        in result.issues
    )
    assert (
        "initial cycle must not reference parent_issue_ref"
        in result.issues
    )


def test_duplicate_and_foreign_references_are_rejected() -> None:
    local_child = build_github_project_v2_issue_ref(
        REPOSITORY,
        16,
    )
    foreign_child = build_github_project_v2_issue_ref(
        "other/repository",
        17,
    )
    result = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=ITEM_REF,
            root_issue_ref=ROOT_REF,
            cycle_ordinal=1,
            status_revision_ref=STATUS_REVISION,
            sub_issue_refs=(
                local_child,
                local_child,
                foreign_child,
            ),
            theme_refs=(THEME_REF, THEME_REF),
        )
    )

    assert result.valid is False
    assert (
        "sub_issue_refs must reference issues in repository"
        in result.issues
    )
    assert "sub_issue_refs must be unique" in result.issues
    assert "theme_refs must be unique" in result.issues


def test_policy_limits_are_validated_and_enforced() -> None:
    with pytest.raises(
        ValueError,
        match="max_cycle_ordinal must be > 0",
    ):
        GitHubProjectV2CycleLineagePolicy(
            max_cycle_ordinal=0
        )

    result = build_github_project_v2_cycle_lineage(
        _initial_command(),
        GitHubProjectV2CycleLineagePolicy(
            max_theme_refs=0
        ),
    )
    assert result.valid is False
    assert "theme_refs exceed policy maximum" in result.issues


def test_contracts_are_frozen() -> None:
    command = _initial_command()
    result = build_github_project_v2_cycle_lineage(command)

    with pytest.raises(FrozenInstanceError):
        command.cycle_ordinal = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.valid = False  # type: ignore[misc]


def test_reference_builders_are_strict_and_reuse_origin_frame() -> None:
    assert build_github_project_v2_issue_ref(
        REPOSITORY,
        15,
    ) == build_origin_frame_id(REPOSITORY, 15)

    with pytest.raises(ValueError, match="owner/name"):
        build_github_project_v2_issue_ref(
            "invalid",
            15,
        )
    with pytest.raises(ValueError, match="issue_number"):
        build_github_project_v2_issue_ref(
            REPOSITORY,
            0,
        )
