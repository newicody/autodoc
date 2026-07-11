from context.github_project_v2_query_only_snapshot_0272 import (
    FIELDS_QUERY,
    ITEMS_QUERY,
    GitHubProjectV2QueryCommand,
    GitHubProjectV2QueryConfig,
    build_github_project_v2_query_plan,
    build_project_v2_snapshot_payload,
    close_github_project_v2_query_result,
    validate_query_only_document,
)


def _config() -> GitHubProjectV2QueryConfig:
    return GitHubProjectV2QueryConfig(
        config_path="config/github_project_v2_query_only.example.ini",
        token_env="GITHUB_TOKEN",
        graphql_url="https://api.github.com/graphql",
        owner="newicody",
        project_number=2,
        project_id="PVT_kwHOA3ouXM4Ba3Ar",
        project_url="https://github.com/users/newicody/projects/2",
        view_number_hint=2,
        source_mode="project_v2_query_only_snapshot",
        output_dir=".var/github/project_v2/snapshots",
        page_size=50,
        max_items=500,
        max_pages=20,
        query_only=True,
        graphql_mutation_allowed=False,
        remote_mutation_allowed=False,
        allow_sql_write=False,
        allow_qdrant_write=False,
    )


def test_0272_r3_queries_are_query_only() -> None:
    assert validate_query_only_document(FIELDS_QUERY) == ""
    assert validate_query_only_document(ITEMS_QUERY) == ""
    assert validate_query_only_document("mutation Bad { deleteProjectV2(input: {}) { clientMutationId } }")


def test_0272_r3_execute_requires_decision() -> None:
    plan = build_github_project_v2_query_plan(
        _config(), GitHubProjectV2QueryCommand(execute=True)
    )
    assert not plan.valid
    assert "policy_decision_id is required for execute mode" in plan.issues


def test_0272_r3_snapshot_is_deterministic_and_keeps_status() -> None:
    plan = build_github_project_v2_query_plan(
        _config(),
        GitHubProjectV2QueryCommand(
            execute=True,
            policy_decision_id="policy:0272:test",
            fixture_mode=True,
        ),
    )
    project = {
        "id": "PVT_kwHOA3ouXM4Ba3Ar",
        "number": 2,
        "title": "idea",
        "url": "https://github.com/users/newicody/projects/2",
        "closed": False,
    }
    fields = [
        {"id": "PVTSSF_status", "name": "Status", "dataType": "SINGLE_SELECT"}
    ]
    items = [
        {
            "id": "PVTI_item",
            "type": "DRAFT_ISSUE",
            "content": {"id": "DI_item", "title": "Idea", "body": "Body"},
            "fieldValues": {
                "nodes": [
                    {
                        "__typename": "ProjectV2ItemFieldSingleSelectValue",
                        "name": "Todo",
                        "optionId": "option-1",
                        "field": {
                            "id": "PVTSSF_status",
                            "name": "Status",
                            "dataType": "SINGLE_SELECT",
                        },
                    }
                ]
            },
        }
    ]
    first = build_project_v2_snapshot_payload(
        plan, project=project, fields=fields, items=items
    )
    second = build_project_v2_snapshot_payload(
        plan, project=project, fields=fields, items=items
    )
    assert first == second
    assert first["snapshot_ref"].startswith("github-project-v2-snapshot:")
    assert first["items"][0]["fieldValues"]["nodes"][0]["name"] == "Todo"
    assert first["boundaries"]["graphql_mutation_allowed"] is False


def test_0272_r3_fixture_result_closes_without_network() -> None:
    plan = build_github_project_v2_query_plan(
        _config(),
        GitHubProjectV2QueryCommand(
            execute=True,
            policy_decision_id="policy:0272:test",
            fixture_mode=True,
        ),
    )
    snapshot = build_project_v2_snapshot_payload(
        plan,
        project={
            "id": "PVT_kwHOA3ouXM4Ba3Ar",
            "number": 2,
            "title": "idea",
            "url": "https://github.com/users/newicody/projects/2",
            "closed": False,
        },
        fields=[],
        items=[],
    )
    result = close_github_project_v2_query_result(
        plan,
        snapshot=snapshot,
        snapshot_path="snapshot.json",
        token_present=False,
        external_call_performed=False,
        fields_page_count=1,
        items_page_count=1,
    )
    assert result.valid
    assert result.external_call_performed is False
    assert result.snapshot_ref == snapshot["snapshot_ref"]
