from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.github_project_v2_parent_theme_query_normalization_0282 import (
    GitHubProjectV2ParentThemeNormalizationCommand,
    GitHubProjectV2ParentThemeNormalizationPolicy,
    normalize_github_project_v2_parent_theme_snapshot,
)
from context.github_project_v2_query_only_snapshot_0272 import (
    ITEMS_QUERY,
    SNAPSHOT_SCHEMA,
    validate_query_only_document,
)


PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"
REPOSITORY = "newicody/projects"


def _field_value(
    *,
    field_id: str,
    field_name: str,
    name: str,
    option_id: str,
) -> dict[str, object]:
    return {
        "__typename": "ProjectV2ItemFieldSingleSelectValue",
        "name": name,
        "optionId": option_id,
        "field": {
            "id": field_id,
            "name": field_name,
            "dataType": "SINGLE_SELECT",
        },
    }


def _issue_item(
    *,
    item_id: str = "PVTI_item_15",
    number: int = 15,
    parent: dict[str, object] | None = None,
    sub_issues: list[dict[str, object]] | None = None,
    include_hierarchy: bool = True,
    repository: str = REPOSITORY,
) -> dict[str, object]:
    content: dict[str, object] = {
        "__typename": "Issue",
        "id": f"I_{number}",
        "number": number,
        "title": f"Issue {number}",
        "url": f"https://github.com/{repository}/issues/{number}",
        "repository": {"nameWithOwner": repository},
    }
    if include_hierarchy:
        content["parent"] = parent
        content["subIssues"] = {
            "totalCount": len(sub_issues or []),
            "pageInfo": {
                "hasNextPage": False,
                "endCursor": None,
            },
            "nodes": sub_issues or [],
        }

    return {
        "id": item_id,
        "type": "ISSUE",
        "content": content,
        "fieldValues": {
            "nodes": [
                _field_value(
                    field_id="PVTSSF_theme",
                    field_name="Thème",
                    name="Général",
                    option_id="theme-general",
                ),
                _field_value(
                    field_id="PVTSSF_status",
                    field_name="Étape Status",
                    name="En cours",
                    option_id="status-en-cours",
                ),
            ]
        },
    }


def _issue_node(number: int, repository: str = REPOSITORY):
    return {
        "id": f"I_{number}",
        "number": number,
        "title": f"Issue {number}",
        "url": f"https://github.com/{repository}/issues/{number}",
        "repository": {"nameWithOwner": repository},
    }


def _snapshot(items: list[dict[str, object]]):
    return {
        "schema": SNAPSHOT_SCHEMA,
        "kind": "github_project_v2_query_only_snapshot",
        "snapshot_ref": "github-project-v2-snapshot:fixture",
        "project": {
            "id": PROJECT_ID,
            "number": 3,
            "title": "Autodoc",
            "url": "https://github.com/users/newicody/projects/3",
        },
        "items": items,
        "boundaries": {
            "query_only": True,
            "graphql_mutation_allowed": False,
            "remote_mutation_allowed": False,
        },
    }


def _normalize(
    snapshot,
    policy=None,
):
    return normalize_github_project_v2_parent_theme_snapshot(
        GitHubProjectV2ParentThemeNormalizationCommand(
            snapshot=snapshot,
            repository=REPOSITORY,
            project_id=PROJECT_ID,
        ),
        policy,
    )


def test_existing_items_query_reads_parent_and_bounded_sub_issues() -> None:
    assert validate_query_only_document(ITEMS_QUERY) == ""
    assert "parent {" in ITEMS_QUERY
    assert "subIssues(first: 100)" in ITEMS_QUERY
    assert "mutation" not in ITEMS_QUERY.casefold()


def test_parent_sub_issues_theme_and_status_are_normalized() -> None:
    result = _normalize(
        _snapshot(
            [
                _issue_item(
                    parent=_issue_node(10),
                    sub_issues=[
                        _issue_node(16),
                        _issue_node(17),
                    ],
                )
            ]
        )
    )

    assert result.valid is True
    assert result.normalization_ref.startswith(
        "github-project-v2-parent-theme:"
    )
    item = result.items[0]
    assert item.project_item_ref == (
        "github-project-v2-item:PVTI_item_15"
    )
    assert item.issue_ref == (
        "github-frame:newicody/projects/issues/15"
    )
    assert item.parent_issue_ref == (
        "github-frame:newicody/projects/issues/10"
    )
    assert item.sub_issue_refs == (
        "github-frame:newicody/projects/issues/16",
        "github-frame:newicody/projects/issues/17",
    )
    assert item.theme_values == ("Général",)
    assert item.theme_refs[0].startswith(
        "github-project-v2-theme:"
    )
    assert item.status_name == "En cours"
    assert item.status_revision_ref.startswith(
        "github-ticket-revision:"
    )
    assert item.hierarchy_payload_present is True


def test_root_issue_without_parent_is_valid() -> None:
    result = _normalize(_snapshot([_issue_item(parent=None)]))

    assert result.valid is True
    assert result.items[0].parent_issue_ref == ""


def test_missing_hierarchy_payload_is_strict_by_default() -> None:
    result = _normalize(
        _snapshot([_issue_item(include_hierarchy=False)])
    )

    assert result.valid is False
    assert any(
        "Issue.parent and Issue.subIssues payload is required"
        in issue
        for issue in result.issues
    )


def test_missing_hierarchy_payload_can_be_allowed_explicitly() -> None:
    result = _normalize(
        _snapshot([_issue_item(include_hierarchy=False)]),
        GitHubProjectV2ParentThemeNormalizationPolicy(
            require_hierarchy_payload=False,
        ),
    )

    assert result.valid is True
    assert result.items[0].hierarchy_payload_present is False


def test_truncated_sub_issue_connection_is_rejected() -> None:
    item = _issue_item(sub_issues=[_issue_node(16)])
    item["content"]["subIssues"]["pageInfo"]["hasNextPage"] = True

    result = _normalize(_snapshot([item]))

    assert result.valid is False
    assert any(
        "subIssues payload is truncated" in issue
        for issue in result.issues
    )


def test_foreign_parent_and_sub_issue_are_rejected() -> None:
    result = _normalize(
        _snapshot(
            [
                _issue_item(
                    parent=_issue_node(10, "other/repository"),
                    sub_issues=[
                        _issue_node(16, "other/repository")
                    ],
                )
            ]
        )
    )

    assert result.valid is False
    assert any("parent repository mismatch" in x for x in result.issues)
    assert any(
        "sub-issue repository mismatch" in x
        for x in result.issues
    )


def test_duplicate_project_item_id_is_rejected() -> None:
    result = _normalize(
        _snapshot(
            [
                _issue_item(item_id="PVTI_duplicate"),
                _issue_item(
                    item_id="PVTI_duplicate",
                    number=16,
                ),
            ]
        )
    )

    assert result.valid is False
    assert any(
        "duplicate project item id" in issue
        for issue in result.issues
    )


def test_non_issue_items_are_ignored_by_default() -> None:
    draft = {
        "id": "PVTI_draft",
        "type": "DRAFT_ISSUE",
        "content": {
            "__typename": "DraftIssue",
            "id": "DI_1",
            "title": "Draft",
        },
        "fieldValues": {"nodes": []},
    }

    result = _normalize(
        _snapshot([draft, _issue_item()])
    )

    assert result.valid is True
    assert result.ignored_item_count == 1
    assert len(result.items) == 1


def test_non_issue_items_can_be_forbidden() -> None:
    draft = {
        "id": "PVTI_draft",
        "type": "DRAFT_ISSUE",
        "content": {"__typename": "DraftIssue"},
    }

    result = _normalize(
        _snapshot([draft]),
        GitHubProjectV2ParentThemeNormalizationPolicy(
            allow_non_issue_items=False,
        ),
    )

    assert result.valid is False
    assert any(
        "non-Issue item is forbidden" in issue
        for issue in result.issues
    )


def test_replay_and_input_order_are_deterministic() -> None:
    snapshot_a = _snapshot(
        [
            _issue_item(item_id="PVTI_b", number=16),
            _issue_item(item_id="PVTI_a", number=15),
        ]
    )
    snapshot_b = _snapshot(
        [
            _issue_item(item_id="PVTI_a", number=15),
            _issue_item(item_id="PVTI_b", number=16),
        ]
    )

    first = _normalize(snapshot_a)
    second = _normalize(snapshot_b)

    assert first.valid is True
    assert second.valid is True
    assert first.items == second.items
    assert first.normalization_ref == second.normalization_ref


def test_boundaries_remain_query_only_and_local() -> None:
    result = _normalize(_snapshot([_issue_item()]))
    assert dict(result.boundaries) == {
        "query_only_snapshot_consumed": True,
        "external_call_performed": False,
        "graphql_query_performed": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "projects_repository_change_required": False,
    }


def test_contracts_are_frozen_and_policy_is_bounded() -> None:
    policy = GitHubProjectV2ParentThemeNormalizationPolicy()

    with pytest.raises(FrozenInstanceError):
        policy.max_items = 1  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_items must be > 0"):
        GitHubProjectV2ParentThemeNormalizationPolicy(
            max_items=0
        )
