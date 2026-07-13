from __future__ import annotations

from context.github_project_push_frame import (
    build_origin_frame_id,
    build_ticket_revision_id,
)
from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryCommand,
    project_github_project_v2_append_only_cycle_history,
)
from context.github_project_v2_cycle_lineage_0282 import (
    GitHubProjectV2CycleLineageCommand,
    build_github_project_v2_cycle_lineage,
    build_github_project_v2_item_ref,
    build_github_project_v2_theme_ref,
)
from context.github_project_v2_parent_sub_ticket_mutation_plan_0282 import (
    GitHubProjectV2IssueSnapshot,
)
from context.github_project_v2_parent_theme_query_normalization_0282 import (
    GitHubProjectV2NormalizedParentThemeItem,
)
from context.github_project_v2_real_cycle_history_smoke_0282 import (
    GitHubProjectV2RealCycleHistorySmokeCommand,
    build_github_project_v2_real_cycle_history_smoke,
)
from context.github_project_v2_theme_grouping_deployment_plan_0282 import (
    GitHubProjectV2ThemeGroupingDeploymentCommand,
    GitHubProjectV2ThemeOptionSpec,
)


REPOSITORY = "newicody/projects"
PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"
ROOT_REF = build_origin_frame_id(REPOSITORY, 15)
ITEM_REF = build_github_project_v2_item_ref("PVTI_15")
THEME_REF = build_github_project_v2_theme_ref(
    PROJECT_ID,
    "PVTF_theme",
    "general",
)
STATUS_REF = build_ticket_revision_id(
    ROOT_REF,
    "project_v2_snapshot_status",
    "snapshot-1",
)


def _history():
    lineage = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=ITEM_REF,
            root_issue_ref=ROOT_REF,
            cycle_ordinal=1,
            status_revision_ref=STATUS_REF,
            theme_refs=(THEME_REF,),
        )
    )
    normalized = GitHubProjectV2NormalizedParentThemeItem(
        project_item_ref=ITEM_REF,
        issue_ref=ROOT_REF,
        parent_issue_ref="",
        sub_issue_refs=(),
        theme_refs=(THEME_REF,),
        theme_values=("Général",),
        status_name="En cours",
        status_revision_ref=STATUS_REF,
        hierarchy_payload_present=True,
    )
    return project_github_project_v2_append_only_cycle_history(
        GitHubProjectV2AppendOnlyCycleHistoryCommand(
            lineage=lineage,
            normalized_item=normalized,
            source_artifact_refs=("artifact:request:15",),
            decision_refs=("decision:approve:15",),
        )
    )


def _root_snapshot():
    return GitHubProjectV2IssueSnapshot(
        issue_ref=ROOT_REF,
        issue_number=15,
        title="Recherche racine",
        body="Besoin initial",
    )


def _theme_command():
    return GitHubProjectV2ThemeGroupingDeploymentCommand(
        owner_kind="user",
        owner_login="newicody",
        project_number=3,
        project_id=PROJECT_ID,
        field_name="Thème",
        desired_options=(
            GitHubProjectV2ThemeOptionSpec(
                name="Général",
                color="BLUE",
            ),
        ),
        target_view_number=2,
    )


def test_real_smoke_composes_r4_r5_and_r6_without_mutation():
    result = build_github_project_v2_real_cycle_history_smoke(
        GitHubProjectV2RealCycleHistorySmokeCommand(
            history=_history(),
            existing_issues=(_root_snapshot(),),
            next_cycle_title="Cycle 2",
            next_cycle_summary="Continuer la recherche.",
            policy_decision_id="policy:0282:r8",
            operator_decision="approve",
            theme_command=_theme_command(),
        )
    )

    assert result.valid is True
    assert result.action == (
        "ready_for_operator_authorized_execution"
    )
    assert result.parent_plan.action == "create_and_link"
    assert result.theme_plan is not None
    assert result.theme_plan.action == "create_field"
    assert result.smoke_ref.startswith(
        "github-project-v2-real-cycle-smoke:"
    )
    assert dict(result.boundaries) == {
        "composition_only": True,
        "adapter_reused": True,
        "preview_is_default": True,
        "exact_smoke_digest_required_for_execution": True,
        "external_call_performed": False,
        "github_mutation_allowed": False,
        "github_mutation_performed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


def test_real_smoke_digest_is_deterministic():
    command = GitHubProjectV2RealCycleHistorySmokeCommand(
        history=_history(),
        existing_issues=(_root_snapshot(),),
        next_cycle_title="Cycle 2",
        next_cycle_summary="Continuer la recherche.",
        policy_decision_id="policy:0282:r8",
        operator_decision="approve",
        theme_command=_theme_command(),
        source_artifact_refs=("artifact:b", "artifact:a"),
        decision_refs=("decision:b", "decision:a"),
    )
    replay = GitHubProjectV2RealCycleHistorySmokeCommand(
        history=command.history,
        existing_issues=command.existing_issues,
        next_cycle_title=command.next_cycle_title,
        next_cycle_summary=command.next_cycle_summary,
        policy_decision_id=command.policy_decision_id,
        operator_decision=command.operator_decision,
        theme_command=command.theme_command,
        source_artifact_refs=tuple(
            reversed(command.source_artifact_refs)
        ),
        decision_refs=tuple(reversed(command.decision_refs)),
    )

    first = build_github_project_v2_real_cycle_history_smoke(
        command
    )
    second = build_github_project_v2_real_cycle_history_smoke(
        replay
    )
    assert first.smoke_digest == second.smoke_digest
    assert first.smoke_ref == second.smoke_ref


def test_invalid_parent_plan_blocks_smoke():
    result = build_github_project_v2_real_cycle_history_smoke(
        GitHubProjectV2RealCycleHistorySmokeCommand(
            history=_history(),
            existing_issues=(),
            next_cycle_title="Cycle 2",
            next_cycle_summary="Continuer la recherche.",
            policy_decision_id="policy:0282:r8",
            operator_decision="approve",
            theme_command=None,
        )
    )

    assert result.valid is False
    assert result.action == "blocked"
    assert result.smoke_ref == ""
    assert (
        "parent/sub-ticket plan is not executable"
        in result.issues
    )
