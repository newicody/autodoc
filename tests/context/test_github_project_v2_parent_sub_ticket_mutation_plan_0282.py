from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryResult,
    GitHubProjectV2CycleHistoryEntry,
)
from context.github_project_v2_parent_sub_ticket_mutation_plan_0282 import (
    GitHubProjectV2IssueSnapshot,
    GitHubProjectV2ParentSubTicketMutationCommand,
    GitHubProjectV2ParentSubTicketMutationPolicy,
    plan_github_project_v2_parent_sub_ticket_mutation,
)


REPOSITORY = "newicody/projects"
ROOT_REF = "github-frame:newicody/projects/issues/15"
CHILD_REF = "github-frame:newicody/projects/issues/16"
OTHER_PARENT_REF = "github-frame:newicody/projects/issues/99"


def _entry() -> GitHubProjectV2CycleHistoryEntry:
    return GitHubProjectV2CycleHistoryEntry(
        entry_ref="github-project-v2-cycle-history-entry:entry1",
        entry_digest="a" * 64,
        cycle_ref="github-project-v2-cycle:cycle1",
        lineage_digest="b" * 64,
        cycle_ordinal=1,
        repository=REPOSITORY,
        project_id="PVT_kwHOA3ouXM4Ba3Ar",
        project_item_ref="github-project-v2-item:PVTI_15",
        issue_ref=ROOT_REF,
        root_issue_ref=ROOT_REF,
        parent_issue_ref="",
        previous_cycle_ref="",
        status_revision_ref="github-ticket-revision:revision1",
        status_name="Terminé",
        sub_issue_refs=(),
        theme_refs=("github-project-v2-theme:theme1",),
        theme_values=("Général",),
        result_issue_ref="github-frame:newicody/projects/issues/15",
        source_artifact_refs=("artifact:result:1",),
        decision_refs=("decision:operator:1",),
    )


def _history() -> GitHubProjectV2AppendOnlyCycleHistoryResult:
    return GitHubProjectV2AppendOnlyCycleHistoryResult(
        valid=True,
        action="append",
        issues=(),
        history_ref="github-project-v2-cycle-history:history1",
        history_digest="c" * 64,
        appended_entry_ref=_entry().entry_ref,
        root_issue_ref=ROOT_REF,
        entries=(_entry(),),
        boundaries=(
            ("append_only_projection", True),
            ("remote_mutation_allowed", False),
        ),
    )


def _root_snapshot(
    *,
    sub_issue_refs: tuple[str, ...] = (),
) -> GitHubProjectV2IssueSnapshot:
    return GitHubProjectV2IssueSnapshot(
        issue_ref=ROOT_REF,
        issue_number=15,
        title="Recherche racine",
        body="root",
        sub_issue_refs=sub_issue_refs,
    )


def _command(
    existing_issues: tuple[GitHubProjectV2IssueSnapshot, ...],
) -> GitHubProjectV2ParentSubTicketMutationCommand:
    return GitHubProjectV2ParentSubTicketMutationCommand(
        history=_history(),
        policy_decision_id="policy:0282:r5:test",
        operator_decision="approve",
        next_cycle_title="Cycle 2 — approfondissement",
        next_cycle_summary="Poursuivre la recherche validée.",
        existing_issues=existing_issues,
        source_artifact_refs=("artifact:closed-result:1",),
        decision_refs=("decision:operator:approve-cycle-2",),
    )


def test_no_marked_issue_plans_create_then_link() -> None:
    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )

    assert result.valid is True
    assert result.action == "create_and_link"
    assert result.next_cycle_ordinal == 2
    assert result.previous_cycle_ref == (
        "github-project-v2-cycle:cycle1"
    )
    assert result.marker.startswith(
        "autodoc:projectv2-cycle:"
    )
    assert result.planned_issue_ref.startswith(
        "github-planned-issue:"
    )
    assert tuple(op.kind for op in result.operations) == (
        "create_issue",
        "add_sub_issue",
    )
    assert result.operations[1].depends_on == (
        result.operations[0].operation_ref,
    )
    assert result.operations[1].parent_issue_ref == ROOT_REF
    assert result.operations[1].child_issue_ref == (
        result.planned_issue_ref
    )


def test_existing_identical_unlinked_issue_plans_link_only() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child))
    )

    assert result.valid is True
    assert result.action == "link_existing"
    assert result.existing_issue_ref == CHILD_REF
    assert len(result.operations) == 1
    assert result.operations[0].kind == "add_sub_issue"
    assert result.operations[0].child_issue_ref == CHILD_REF


def test_existing_identical_linked_issue_is_replay() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
        parent_issue_ref=ROOT_REF,
    )
    root = _root_snapshot(sub_issue_refs=(CHILD_REF,))

    replay = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((root, child))
    )

    assert replay.valid is True
    assert replay.action == "replay"
    assert replay.operations == ()
    assert replay.plan_digest


@pytest.mark.parametrize(
    ("title_suffix", "body_suffix", "expected"),
    (
        (" changed", "", "title differs"),
        ("", "\nchanged", "body"),
    ),
)
def test_existing_marked_issue_content_collision(
    title_suffix: str,
    body_suffix: str,
    expected: str,
) -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title + title_suffix,
        body=first.body + body_suffix,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child))
    )

    assert result.valid is False
    assert result.action == "collision"
    assert any(expected in issue for issue in result.issues)


def test_multiple_marker_matches_are_collision() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child1 = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
    )
    child2 = GitHubProjectV2IssueSnapshot(
        issue_ref="github-frame:newicody/projects/issues/17",
        issue_number=17,
        title=first.title,
        body=first.body,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child1, child2))
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.issues == (
        "multiple issues carry the same cycle marker",
    )


def test_other_parent_is_collision() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
        parent_issue_ref=OTHER_PARENT_REF,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child))
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.issues == (
        "existing marked issue belongs to another parent",
    )


def test_parent_and_root_snapshots_must_agree() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
        parent_issue_ref=ROOT_REF,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child))
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.issues == (
        "parent and sub-issue snapshots disagree",
    )


def test_closed_existing_issue_is_collision_by_default() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
        state="CLOSED",
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child))
    )

    assert result.valid is False
    assert result.action == "collision"
    assert result.issues == (
        "existing marked issue is not open",
    )


def test_missing_root_snapshot_is_blocked() -> None:
    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command(())
    )

    assert result.valid is False
    assert result.action == "blocked"
    assert result.issues == (
        "root issue snapshot is required",
    )


def test_invalid_history_is_blocked() -> None:
    command = _command((_root_snapshot(),))
    invalid_history = replace(
        command.history,
        valid=False,
        action="collision",
        issues=("history collision",),
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        replace(command, history=invalid_history)
    )

    assert result.valid is False
    assert result.action == "blocked"
    assert "cycle history must be valid" in result.issues
    assert (
        "cycle history action must be append or replay"
        in result.issues
    )


def test_replay_is_deterministic() -> None:
    command = _command((_root_snapshot(),))

    first = plan_github_project_v2_parent_sub_ticket_mutation(
        command
    )
    second = plan_github_project_v2_parent_sub_ticket_mutation(
        command
    )

    assert first == second
    assert first.plan_ref == second.plan_ref
    assert first.plan_digest == second.plan_digest


def test_all_boundaries_forbid_execution() -> None:
    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )

    assert dict(result.boundaries) == {
        "plan_only": True,
        "operator_authorization_required": True,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "github_mutation_allowed": False,
        "github_mutation_performed": False,
        "filesystem_write_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }
    for operation in result.to_json_dict()["operations"]:
        assert operation["github_mutation_allowed"] is False
        assert operation["github_mutation_performed"] is False


def test_policy_can_forbid_link_existing() -> None:
    first = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(),))
    )
    child = GitHubProjectV2IssueSnapshot(
        issue_ref=CHILD_REF,
        issue_number=16,
        title=first.title,
        body=first.body,
    )

    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((_root_snapshot(), child)),
        GitHubProjectV2ParentSubTicketMutationPolicy(
            allow_link_existing=False,
        ),
    )

    assert result.valid is False
    assert result.action == "blocked"
    assert result.issues == (
        "linking an existing issue is forbidden by policy",
    )


def test_contracts_are_frozen() -> None:
    snapshot = _root_snapshot()
    result = plan_github_project_v2_parent_sub_ticket_mutation(
        _command((snapshot,))
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.state = "CLOSED"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.valid = False  # type: ignore[misc]
