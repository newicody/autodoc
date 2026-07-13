from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from context.github_project_push_frame import (
    build_origin_frame_id,
    build_ticket_revision_id,
)
from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryCommand,
    GitHubProjectV2AppendOnlyCycleHistoryPolicy,
    project_github_project_v2_append_only_cycle_history,
)
from context.github_project_v2_cycle_lineage_0282 import (
    GitHubProjectV2CycleLineageCommand,
    build_github_project_v2_cycle_lineage,
    build_github_project_v2_item_ref,
    build_github_project_v2_theme_ref,
)
from context.github_project_v2_parent_theme_query_normalization_0282 import (
    GitHubProjectV2NormalizedParentThemeItem,
)


REPOSITORY = "newicody/projects"
PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"
ROOT_REF = build_origin_frame_id(REPOSITORY, 15)
THEME_REF = build_github_project_v2_theme_ref(
    PROJECT_ID,
    "PVTSSF_theme",
    "theme-general",
)


def _cycle(
    ordinal: int,
    *,
    previous_cycle_ref: str = "",
):
    issue_number = 14 + ordinal
    issue_ref = build_origin_frame_id(REPOSITORY, issue_number)
    item_ref = build_github_project_v2_item_ref(
        f"PVTI_cycle_{issue_number}"
    )
    status_revision_ref = build_ticket_revision_id(
        issue_ref,
        "project_v2_snapshot_status",
        f"snapshot:{ordinal}:En cours",
    )
    parent_ref = ROOT_REF if ordinal > 1 else ""
    lineage = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=item_ref,
            root_issue_ref=ROOT_REF,
            parent_issue_ref=parent_ref,
            previous_cycle_ref=previous_cycle_ref,
            cycle_ordinal=ordinal,
            status_revision_ref=status_revision_ref,
            theme_refs=(THEME_REF,),
        )
    )
    item = GitHubProjectV2NormalizedParentThemeItem(
        project_item_ref=item_ref,
        issue_ref=issue_ref,
        parent_issue_ref=parent_ref,
        sub_issue_refs=(),
        theme_refs=(THEME_REF,),
        theme_values=("Général",),
        status_name="En cours",
        status_revision_ref=status_revision_ref,
        hierarchy_payload_present=True,
    )
    return lineage, item


def _append(lineage, item, existing=(), **kwargs):
    return project_github_project_v2_append_only_cycle_history(
        GitHubProjectV2AppendOnlyCycleHistoryCommand(
            lineage=lineage,
            normalized_item=item,
            existing_entries=existing,
            source_artifact_refs=kwargs.get(
                "source_artifact_refs",
                ("artifact:authoritative-request",),
            ),
            decision_refs=kwargs.get(
                "decision_refs",
                ("decision:operator-promote",),
            ),
        )
    )


def test_initial_cycle_appends_deterministically() -> None:
    lineage, item = _cycle(1)
    first = _append(lineage, item)
    replay_from_empty = _append(lineage, item)

    assert first.valid is True
    assert first.action == "append"
    assert len(first.entries) == 1
    assert first == replay_from_empty
    assert first.history_ref.startswith(
        "github-project-v2-cycle-history:"
    )
    assert first.entries[0].entry_ref.startswith(
        "github-project-v2-cycle-history-entry:"
    )
    assert dict(first.boundaries) == {
        "append_only_projection": True,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "filesystem_write_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


def test_second_cycle_appends_after_last_cycle() -> None:
    first_lineage, first_item = _cycle(1)
    first = _append(first_lineage, first_item)
    second_lineage, second_item = _cycle(
        2,
        previous_cycle_ref=first_lineage.cycle_ref,
    )
    second = _append(
        second_lineage,
        second_item,
        first.entries,
    )

    assert second.valid is True
    assert second.action == "append"
    assert [entry.cycle_ordinal for entry in second.entries] == [1, 2]
    assert second.entries[1].previous_cycle_ref == (
        second.entries[0].cycle_ref
    )
    assert second.root_issue_ref == ROOT_REF


def test_identical_existing_cycle_is_replay_not_append() -> None:
    lineage, item = _cycle(1)
    first = _append(lineage, item)
    replay = _append(lineage, item, first.entries)

    assert replay.valid is True
    assert replay.action == "replay"
    assert replay.entries == first.entries
    assert replay.history_ref == first.history_ref
    assert replay.history_digest == first.history_digest


def test_same_cycle_with_changed_artifact_refs_is_collision() -> None:
    lineage, item = _cycle(1)
    first = _append(lineage, item)
    collision = _append(
        lineage,
        item,
        first.entries,
        source_artifact_refs=("artifact:different",),
    )

    assert collision.valid is False
    assert collision.action == "collision"
    assert "cycle_ref collision" in " ".join(collision.issues)
    assert collision.entries == first.entries


def test_cycle_ordinal_gap_is_rejected() -> None:
    first_lineage, first_item = _cycle(1)
    first = _append(first_lineage, first_item)
    third_lineage, third_item = _cycle(
        3,
        previous_cycle_ref=first_lineage.cycle_ref,
    )
    result = _append(
        third_lineage,
        third_item,
        first.entries,
    )

    assert result.valid is False
    assert result.action == "reject"
    assert "cycle_ordinal is not contiguous" in " ".join(
        result.issues
    )


def test_previous_cycle_must_target_last_entry() -> None:
    first_lineage, first_item = _cycle(1)
    first = _append(first_lineage, first_item)
    second_lineage, second_item = _cycle(
        2,
        previous_cycle_ref="github-project-v2-cycle:wrong",
    )
    result = _append(
        second_lineage,
        second_item,
        first.entries,
    )

    assert result.valid is False
    assert "must target last cycle" in " ".join(result.issues)


def test_normalized_item_mismatches_are_rejected() -> None:
    lineage, item = _cycle(1)
    changed = replace(
        item,
        status_revision_ref="github-ticket-revision:different",
        theme_refs=("github-project-v2-theme:different",),
    )
    result = _append(lineage, changed)

    assert result.valid is False
    assert "status_revision_ref mismatch" in result.issues
    assert "theme_refs mismatch" in result.issues


def test_tampered_existing_entry_digest_is_rejected() -> None:
    lineage, item = _cycle(1)
    first = _append(lineage, item)
    tampered = replace(
        first.entries[0],
        entry_digest="0" * 64,
    )
    second_lineage, second_item = _cycle(
        2,
        previous_cycle_ref=lineage.cycle_ref,
    )
    result = _append(
        second_lineage,
        second_item,
        (tampered,),
    )

    assert result.valid is False
    assert "entry digest mismatch" in " ".join(result.issues)


def test_duplicate_and_empty_refs_are_rejected() -> None:
    lineage, item = _cycle(1)
    result = _append(
        lineage,
        item,
        source_artifact_refs=("artifact:a", "artifact:a", ""),
        decision_refs=("decision:a", "decision:a"),
    )

    assert result.valid is False
    text = " ".join(result.issues)
    assert "source_artifact_refs must not contain empty" in text
    assert "source_artifact_refs must be unique" in text
    assert "decision_refs must be unique" in text


def test_policy_limits_and_frozen_contracts() -> None:
    with pytest.raises(ValueError, match="max_entries must be > 0"):
        GitHubProjectV2AppendOnlyCycleHistoryPolicy(max_entries=0)

    lineage, item = _cycle(1)
    command = GitHubProjectV2AppendOnlyCycleHistoryCommand(
        lineage=lineage,
        normalized_item=item,
    )
    result = project_github_project_v2_append_only_cycle_history(
        command
    )

    with pytest.raises(FrozenInstanceError):
        command.existing_entries = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.valid = False  # type: ignore[misc]
