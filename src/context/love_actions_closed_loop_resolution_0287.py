"""Pure ProjectV2 target resolution for the imported Actions closed loop.

The module selects one ProjectV2, one Issue item and one field from a GraphQL
readback.  It contains no transport, environment or configuration access.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class LoveActionsClosedLoopResolutionError(ValueError):
    """Raised when a remote ProjectV2 target cannot be resolved exactly."""


@dataclass(frozen=True, slots=True)
class LoveProjectV2TargetRequest:
    """Exact read-only target requested after the source Issue is known."""

    repository: str
    issue_number: int
    project_owner: str
    project_number: int
    field_name: str
    project_item_id_override: str = ""
    field_ref_override: str = ""

    def __post_init__(self) -> None:
        if "/" not in self.repository:
            raise LoveActionsClosedLoopResolutionError(
                "repository must use owner/name"
            )
        if self.issue_number <= 0:
            raise LoveActionsClosedLoopResolutionError(
                "issue_number must be positive"
            )
        if not self.project_owner.strip():
            raise LoveActionsClosedLoopResolutionError(
                "project_owner must be non-empty"
            )
        if self.project_number <= 0:
            raise LoveActionsClosedLoopResolutionError(
                "project_number must be positive"
            )
        if not self.field_name.strip():
            raise LoveActionsClosedLoopResolutionError(
                "field_name must be non-empty"
            )
        override_presence = (
            bool(self.project_item_id_override.strip()),
            bool(self.field_ref_override.strip()),
        )
        if override_presence.count(True) == 1:
            raise LoveActionsClosedLoopResolutionError(
                "project item and field overrides must be supplied together"
            )


@dataclass(frozen=True, slots=True)
class ResolvedLoveProjectV2Target:
    """One exact ProjectV2 item and field resolved without mutation."""

    project_id: str
    project_owner: str
    project_number: int
    project_item_id: str
    field_ref: str
    field_name: str
    resolution_source: str

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "project_owner",
            "project_item_id",
            "field_ref",
            "field_name",
            "resolution_source",
        ):
            if not str(getattr(self, name)).strip():
                raise LoveActionsClosedLoopResolutionError(
                    f"{name} must be non-empty"
                )
        if self.project_number <= 0:
            raise LoveActionsClosedLoopResolutionError(
                "project_number must be positive"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "project_owner": self.project_owner,
            "project_number": self.project_number,
            "project_item_id": self.project_item_id,
            "field_ref": self.field_ref,
            "field_name": self.field_name,
            "resolution_source": self.resolution_source,
        }


def resolve_love_projectv2_target(
    request: LoveProjectV2TargetRequest,
    payload: Mapping[str, Any],
) -> ResolvedLoveProjectV2Target:
    """Resolve one exact ProjectV2 target from a GraphQL response mapping."""

    data = _mapping(payload.get("data"), "GraphQL data")
    repository = _mapping(data.get("repository"), "repository")
    issue = _mapping(repository.get("issue"), "source Issue")

    project = _select_project(data, request)
    project_id = _required_text(project, "id", "ProjectV2 id")
    project_number = int(project.get("number", 0))
    if project_number != request.project_number:
        raise LoveActionsClosedLoopResolutionError(
            "resolved ProjectV2 number differs from requested project"
        )

    items = _nodes(issue.get("projectItems"), "Issue project items")
    item_matches = tuple(
        item
        for item in items
        if isinstance(item, Mapping)
        and isinstance(item.get("project"), Mapping)
        and str(item["project"].get("id", "")) == project_id
    )
    if request.project_item_id_override.strip():
        item_matches = tuple(
            item
            for item in item_matches
            if str(item.get("id", "")) == request.project_item_id_override
        )
    if len(item_matches) != 1:
        if not item_matches:
            raise LoveActionsClosedLoopResolutionError(
                "source Issue is not present exactly once in the configured "
                "ProjectV2"
            )
        raise LoveActionsClosedLoopResolutionError(
            "source Issue has multiple matching ProjectV2 items"
        )
    project_item_id = _required_text(
        item_matches[0], "id", "ProjectV2 item id"
    )

    fields = _nodes(project.get("fields"), "ProjectV2 fields")
    field_matches = tuple(
        field
        for field in fields
        if isinstance(field, Mapping)
        and str(field.get("name", "")) == request.field_name
    )
    if request.field_ref_override.strip():
        field_matches = tuple(
            field
            for field in field_matches
            if str(field.get("id", "")) == request.field_ref_override
        )
    if len(field_matches) != 1:
        if not field_matches:
            raise LoveActionsClosedLoopResolutionError(
                "configured ProjectV2 field cannot be resolved exactly"
            )
        raise LoveActionsClosedLoopResolutionError(
            "configured ProjectV2 field name is ambiguous"
        )
    field = field_matches[0]
    field_ref = _required_text(field, "id", "ProjectV2 field id")

    return ResolvedLoveProjectV2Target(
        project_id=project_id,
        project_owner=request.project_owner,
        project_number=request.project_number,
        project_item_id=project_item_id,
        field_ref=field_ref,
        field_name=request.field_name,
        resolution_source=(
            "explicit-overrides"
            if request.project_item_id_override.strip()
            else "authoritative-request-and-project-config"
        ),
    )


def _select_project(
    data: Mapping[str, Any],
    request: LoveProjectV2TargetRequest,
) -> Mapping[str, Any]:
    candidates: list[Mapping[str, Any]] = []
    for owner_key in ("user", "organization"):
        owner = data.get(owner_key)
        if not isinstance(owner, Mapping):
            continue
        project = owner.get("projectV2")
        if isinstance(project, Mapping):
            candidates.append(project)
    matches = tuple(
        project
        for project in candidates
        if int(project.get("number", 0)) == request.project_number
    )
    if len(matches) != 1:
        raise LoveActionsClosedLoopResolutionError(
            "configured ProjectV2 cannot be resolved exactly for its owner"
        )
    return matches[0]


def _nodes(value: object, name: str) -> Sequence[Any]:
    connection = _mapping(value, name)
    nodes = connection.get("nodes", ())
    if isinstance(nodes, Sequence) and not isinstance(
        nodes, (str, bytes, bytearray)
    ):
        return nodes
    raise LoveActionsClosedLoopResolutionError(f"{name} nodes must be an array")


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LoveActionsClosedLoopResolutionError(
            f"{name} must be a JSON object"
        )
    return value


def _required_text(
    value: Mapping[str, Any], key: str, name: str
) -> str:
    text = str(value.get(key, "")).strip()
    if not text:
        raise LoveActionsClosedLoopResolutionError(f"{name} is missing")
    return text
