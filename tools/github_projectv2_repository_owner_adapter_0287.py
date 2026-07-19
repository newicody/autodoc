"""ProjectV2 owner-polymorphic extension of the existing GitHub adapter.

The base adapter remains the single transport implementation for Issue
comments, field reads and controlled mutations. This extension changes
only the read-only target query so a user or organization owner is
resolved through GitHub's ``repositoryOwner`` interface.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from context.love_actions_closed_loop_resolution_0287 import (
    LoveProjectV2TargetRequest,
    ResolvedLoveProjectV2Target,
    resolve_love_projectv2_target,
)
from tools.publish_love_final_deliverable_0287 import (
    GitHubCliFinalDeliverablePublicationAdapter,
)

PROJECT_TARGET_REPOSITORY_OWNER_QUERY = """
query(
    $repoOwner: String!,
    $repoName: String!,
    $issueNumber: Int!,
    $projectOwner: String!,
    $projectNumber: Int!
) {
    repository(owner: $repoOwner, name: $repoName) {
        issue(number: $issueNumber) {
            id
            projectItems(first: 100) {
                nodes {
                    id
                    project { id number title }
                }
            }
        }
    }
    owner: repositoryOwner(login: $projectOwner) {
        __typename
        ... on User {
            projectV2(number: $projectNumber) {
                id
                number
                title
                fields(first: 100) {
                    nodes {
                        ... on ProjectV2Field {
                            id
                            name
                            dataType
                        }
                        ... on ProjectV2SingleSelectField {
                            id
                            name
                        }
                        ... on ProjectV2IterationField {
                            id
                            name
                        }
                    }
                }
            }
        }
        ... on Organization {
            projectV2(number: $projectNumber) {
                id
                number
                title
                fields(first: 100) {
                    nodes {
                        ... on ProjectV2Field {
                            id
                            name
                            dataType
                        }
                        ... on ProjectV2SingleSelectField {
                            id
                            name
                        }
                        ... on ProjectV2IterationField {
                            id
                            name
                        }
                    }
                }
            }
        }
    }
}
""".strip()


class RepositoryOwnerGitHubCliFinalDeliverablePublicationAdapter(
    GitHubCliFinalDeliverablePublicationAdapter
):
    """Reuse the existing adapter with one owner-polymorphic read."""

    def resolve_project_target(
        self,
        request: LoveProjectV2TargetRequest,
    ) -> ResolvedLoveProjectV2Target:
        repository_owner, repository_name = request.repository.split(
            "/",
            1,
        )
        payload = self._graphql(
            PROJECT_TARGET_REPOSITORY_OWNER_QUERY,
            {
                "repoOwner": repository_owner,
                "repoName": repository_name,
                "issueNumber": request.issue_number,
                "projectOwner": request.project_owner,
                "projectNumber": request.project_number,
            },
        )
        normalized = normalize_repository_owner_payload(payload)
        return resolve_love_projectv2_target(
            request,
            normalized,
        )


def normalize_repository_owner_payload(
    payload: object,
) -> dict[str, Any]:
    root = _mapping(payload, "GraphQL response")
    data = _mapping(root.get("data"), "GraphQL data")
    owner = _mapping(data.get("owner"), "repository owner")
    owner_type = str(owner.get("__typename", "")).strip()
    if owner_type not in {"User", "Organization"}:
        raise RuntimeError(
            "repository owner must resolve to User or Organization"
        )

    normalized_data = dict(data)
    normalized_data.pop("owner", None)
    if owner_type == "User":
        normalized_data["user"] = dict(owner)
        normalized_data["organization"] = None
    else:
        normalized_data["user"] = None
        normalized_data["organization"] = dict(owner)
    return {
        "data": normalized_data,
    }


def _mapping(
    value: object,
    name: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{name} must be a JSON object")
    return value
