from __future__ import annotations

from pathlib import Path

import pytest

from context.love_actions_closed_loop_resolution_0287 import (
    LoveProjectV2TargetRequest,
)
from tools.github_projectv2_repository_owner_adapter_0287 import (
    PROJECT_TARGET_REPOSITORY_OWNER_QUERY,
    RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter,
    normalize_repository_owner_payload,
)
from tools.publish_love_final_deliverable_0287 import (
    GitHubCliFinalDeliverablePublicationAdapter,
)


def _request() -> LoveProjectV2TargetRequest:
    return LoveProjectV2TargetRequest(
        repository="newicody/projects",
        issue_number=15,
        project_owner="newicody",
        project_number=3,
        field_name="Résumé",
    )


def _payload(owner_type: str) -> dict:
    return {
        "data": {
            "repository": {
                "issue": {
                    "id": "I_issue_15",
                    "projectItems": {
                        "nodes": [
                            {
                                "id": "PVTI_issue_15",
                                "project": {
                                    "id": "PVT_project_3",
                                    "number": 3,
                                    "title": "Autodoc",
                                },
                            }
                        ]
                    },
                }
            },
            "owner": {
                "__typename": owner_type,
                "projectV2": {
                    "id": "PVT_project_3",
                    "number": 3,
                    "title": "Autodoc",
                    "fields": {
                        "nodes": [
                            {
                                "id": "PVTF_resume",
                                "name": "Résumé",
                                "dataType": "TEXT",
                            }
                        ]
                    },
                },
            },
        }
    }


def test_adapter_reuses_existing_transport_and_mutation_surface() -> None:
    assert issubclass(
        RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter,
        GitHubCliFinalDeliverablePublicationAdapter,
    )
    assert (
        RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter
        .create_comment
        is GitHubCliFinalDeliverablePublicationAdapter.create_comment
    )
    assert (
        RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter
        .update_field
        is GitHubCliFinalDeliverablePublicationAdapter.update_field
    )


def test_query_has_one_polymorphic_owner_lookup() -> None:
    query = PROJECT_TARGET_REPOSITORY_OWNER_QUERY

    assert "owner: repositoryOwner(login: $projectOwner)" in query
    assert "... on User {" in query
    assert "... on Organization {" in query
    assert "user(login: $projectOwner)" not in query
    assert "organization(login: $projectOwner)" not in query


@pytest.mark.parametrize(
    ("owner_type", "legacy_key"),
    (
        ("User", "user"),
        ("Organization", "organization"),
    ),
)
def test_normalization_preserves_existing_domain_contract(
    owner_type: str,
    legacy_key: str,
) -> None:
    normalized = normalize_repository_owner_payload(
        _payload(owner_type)
    )

    data = normalized["data"]
    assert "owner" not in data
    assert data[legacy_key]["__typename"] == owner_type
    other = (
        "organization"
        if legacy_key == "user"
        else "user"
    )
    assert data[other] is None


@pytest.mark.parametrize("owner_type", ("User", "Organization"))
def test_resolve_target_uses_one_query_and_existing_resolver(
    owner_type: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = (
        RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter(
            gh_command="gh",
            token_env="AUTODOC_PROJECT_TOKEN",
        )
    )
    captured = {}

    def fake_graphql(query, variables):
        captured["query"] = query
        captured["variables"] = variables
        return _payload(owner_type)

    monkeypatch.setattr(adapter, "_graphql", fake_graphql)

    target = adapter.resolve_project_target(_request())

    assert target.project_id == "PVT_project_3"
    assert target.project_item_id == "PVTI_issue_15"
    assert target.field_ref == "PVTF_resume"
    assert captured["query"] == (
        PROJECT_TARGET_REPOSITORY_OWNER_QUERY
    )
    assert captured["variables"]["projectOwner"] == "newicody"


def test_unknown_repository_owner_type_fails_closed() -> None:
    with pytest.raises(
        RuntimeError,
        match="User or Organization",
    ):
        normalize_repository_owner_payload(_payload("Enterprise"))


def test_extension_adds_no_second_cli_or_mutation_implementation() -> None:
    source = Path(
        RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter
        .__module__
        .replace(".", "/")
    )
    root = Path(__file__).resolve().parents[2]
    text = (root / f"{source}.py").read_text(encoding="utf-8")

    assert "GitHubCliFinalDeliverablePublicationAdapter" in text
    assert "self._graphql(" in text
    assert "resolve_love_projectv2_target(" in text

    for forbidden in (
        "subprocess.run(",
        "create_comment(",
        "update_field(",
        "updateProjectV2ItemFieldValue",
        "requests.",
        "urlopen(",
        "Scheduler(",
        "QdrantClient(",
        "psycopg.connect(",
    ):
        assert forbidden not in text
