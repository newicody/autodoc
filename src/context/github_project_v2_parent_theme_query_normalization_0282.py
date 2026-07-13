"""Query-only ProjectV2 parent/theme normalization for phase 0282-r3.

The module consumes an already-built 0272 query-only snapshot. It does not
perform GraphQL transport, GitHub mutation, persistence, scheduling or
laboratory execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from context.github_project_push_frame import build_ticket_revision_id
from context.github_project_v2_cycle_lineage_0282 import (
    build_github_project_v2_issue_ref,
    build_github_project_v2_item_ref,
    build_github_project_v2_theme_ref,
)
from context.github_project_v2_query_only_snapshot_0272 import (
    SNAPSHOT_SCHEMA,
)


PARENT_THEME_NORMALIZATION_SCHEMA = (
    "missipy.github.project_v2_parent_theme_normalization.v1"
)
PARENT_THEME_ITEM_SCHEMA = (
    "missipy.github.project_v2_parent_theme_item.v1"
)
PARENT_THEME_RESULT_SCHEMA = (
    "missipy.github.project_v2_parent_theme_normalization_result.v1"
)


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentThemeNormalizationCommand:
    snapshot: Mapping[str, Any]
    repository: str
    project_id: str


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentThemeNormalizationPolicy:
    theme_field_names: tuple[str, ...] = ("Theme", "Thème")
    theme_field_ids: tuple[str, ...] = ()
    status_field_names: tuple[str, ...] = (
        "Status",
        "Étape Status",
    )
    status_field_ids: tuple[str, ...] = ()
    require_hierarchy_payload: bool = True
    require_status: bool = True
    allow_non_issue_items: bool = True
    max_items: int = 500
    max_sub_issue_refs: int = 64
    max_theme_refs: int = 16

    def __post_init__(self) -> None:
        if self.max_items <= 0:
            raise ValueError("max_items must be > 0")
        if self.max_sub_issue_refs < 0:
            raise ValueError("max_sub_issue_refs must be >= 0")
        if self.max_theme_refs < 0:
            raise ValueError("max_theme_refs must be >= 0")
        if not self.theme_field_names and not self.theme_field_ids:
            raise ValueError(
                "at least one theme field name or id is required"
            )
        if not self.status_field_names and not self.status_field_ids:
            raise ValueError(
                "at least one status field name or id is required"
            )


@dataclass(frozen=True, slots=True)
class GitHubProjectV2NormalizedParentThemeItem:
    project_item_ref: str
    issue_ref: str
    parent_issue_ref: str
    sub_issue_refs: tuple[str, ...]
    theme_refs: tuple[str, ...]
    theme_values: tuple[str, ...]
    status_name: str
    status_revision_ref: str
    hierarchy_payload_present: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": PARENT_THEME_ITEM_SCHEMA,
            "project_item_ref": self.project_item_ref,
            "issue_ref": self.issue_ref,
            "parent_issue_ref": self.parent_issue_ref,
            "sub_issue_refs": list(self.sub_issue_refs),
            "theme_refs": list(self.theme_refs),
            "theme_values": list(self.theme_values),
            "status_name": self.status_name,
            "status_revision_ref": self.status_revision_ref,
            "hierarchy_payload_present": (
                self.hierarchy_payload_present
            ),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ParentThemeNormalizationResult:
    valid: bool
    issues: tuple[str, ...]
    normalization_ref: str
    snapshot_ref: str
    repository: str
    project_id: str
    items: tuple[GitHubProjectV2NormalizedParentThemeItem, ...]
    ignored_item_count: int
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": PARENT_THEME_RESULT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "normalization_ref": self.normalization_ref,
            "snapshot_ref": self.snapshot_ref,
            "repository": self.repository,
            "project_id": self.project_id,
            "items": [item.to_json_dict() for item in self.items],
            "counts": {
                "normalized_item_count": len(self.items),
                "ignored_item_count": self.ignored_item_count,
            },
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"project_v2_parent_theme_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"items={len(self.items)}",
                f"ignored={self.ignored_item_count}",
                f"snapshot_ref={self.snapshot_ref or '-'}",
                "external_call_performed=False",
                "graphql_mutation_allowed=False",
                "remote_mutation_allowed=False",
            )
        )


def normalize_github_project_v2_parent_theme_snapshot(
    command: GitHubProjectV2ParentThemeNormalizationCommand,
    policy: GitHubProjectV2ParentThemeNormalizationPolicy | None = None,
) -> GitHubProjectV2ParentThemeNormalizationResult:
    active_policy = (
        policy or GitHubProjectV2ParentThemeNormalizationPolicy()
    )
    snapshot = command.snapshot
    repository = command.repository.strip()
    project_id = command.project_id.strip()
    issues: list[str] = []

    if str(snapshot.get("schema", "")) != SNAPSHOT_SCHEMA:
        issues.append("snapshot schema mismatch")

    project = _mapping(snapshot.get("project"))
    if str(project.get("id", "")).strip() != project_id:
        issues.append("snapshot project id mismatch")

    boundaries = _mapping(snapshot.get("boundaries"))
    if boundaries.get("query_only") is not True:
        issues.append("snapshot must remain query-only")
    if boundaries.get("graphql_mutation_allowed") is not False:
        issues.append("snapshot must disable GraphQL mutation")
    if boundaries.get("remote_mutation_allowed") is not False:
        issues.append("snapshot must disable remote mutation")

    snapshot_ref = str(snapshot.get("snapshot_ref", "")).strip()
    if not snapshot_ref.startswith("github-project-v2-snapshot:"):
        issues.append("snapshot_ref is required")

    raw_items = _sequence(snapshot.get("items"))
    if len(raw_items) > active_policy.max_items:
        issues.append("snapshot item count exceeds policy maximum")

    normalized_items: list[
        GitHubProjectV2NormalizedParentThemeItem
    ] = []
    ignored_item_count = 0
    seen_project_item_ids: set[str] = set()

    for position, raw_item in enumerate(raw_items):
        item = _mapping(raw_item)
        item_id = str(item.get("id", "")).strip()
        item_label = item_id or f"position:{position}"

        if not item_id:
            issues.append(f"{item_label}: project item id is required")
            continue
        if item_id in seen_project_item_ids:
            issues.append(f"{item_label}: duplicate project item id")
            continue
        seen_project_item_ids.add(item_id)

        content = _mapping(item.get("content"))
        item_type = str(item.get("type", "")).strip()
        content_type = str(content.get("__typename", "")).strip()
        if item_type != "ISSUE" or content_type != "Issue":
            if active_policy.allow_non_issue_items:
                ignored_item_count += 1
                continue
            issues.append(f"{item_label}: non-Issue item is forbidden")
            continue

        item_issues: list[str] = []
        content_repository = str(
            _mapping(content.get("repository")).get(
                "nameWithOwner",
                "",
            )
        ).strip()
        issue_number = _positive_int(content.get("number"))

        if content_repository != repository:
            item_issues.append(
                "issue repository does not match normalization repository"
            )
        if issue_number <= 0:
            item_issues.append("issue number must be positive")

        issue_ref = ""
        if not item_issues:
            issue_ref = build_github_project_v2_issue_ref(
                repository,
                issue_number,
            )

        hierarchy_payload_present = (
            "parent" in content and "subIssues" in content
        )
        if (
            active_policy.require_hierarchy_payload
            and not hierarchy_payload_present
        ):
            item_issues.append(
                "Issue.parent and Issue.subIssues payload is required"
            )

        parent_issue_ref = _normalize_optional_issue(
            content.get("parent"),
            repository,
            f"{item_label}: parent",
            item_issues,
        )
        sub_issue_refs = _normalize_sub_issues(
            content.get("subIssues"),
            repository,
            item_label,
            active_policy,
            item_issues,
        )

        if issue_ref and issue_ref in sub_issue_refs:
            item_issues.append(
                "issue must not appear in its own sub_issue_refs"
            )
        if (
            parent_issue_ref
            and parent_issue_ref in sub_issue_refs
        ):
            item_issues.append(
                "parent_issue_ref must not be a sub_issue_ref"
            )

        field_values = _field_value_nodes(item)
        theme_refs, theme_values = _normalize_themes(
            field_values,
            project_id,
            active_policy,
            item_label,
            item_issues,
        )
        status_name, status_field_ref = _normalize_status(
            field_values,
            active_policy,
            item_label,
            item_issues,
        )

        status_revision_ref = ""
        if issue_ref and status_name:
            status_revision_ref = build_ticket_revision_id(
                issue_ref,
                "project_v2_snapshot_status",
                "\0".join(
                    (
                        snapshot_ref,
                        item_id,
                        status_field_ref,
                        status_name,
                    )
                ),
            )

        if item_issues:
            issues.extend(
                f"{item_label}: {message}"
                for message in item_issues
            )
            continue

        normalized_items.append(
            GitHubProjectV2NormalizedParentThemeItem(
                project_item_ref=build_github_project_v2_item_ref(
                    item_id
                ),
                issue_ref=issue_ref,
                parent_issue_ref=parent_issue_ref,
                sub_issue_refs=sub_issue_refs,
                theme_refs=theme_refs,
                theme_values=theme_values,
                status_name=status_name,
                status_revision_ref=status_revision_ref,
                hierarchy_payload_present=hierarchy_payload_present,
            )
        )

    normalized_items.sort(key=lambda item: item.project_item_ref)
    digest = _normalization_digest(
        snapshot_ref,
        repository,
        project_id,
        normalized_items,
    )
    normalization_ref = (
        f"github-project-v2-parent-theme:{digest[:16]}"
        if not issues
        else ""
    )

    return GitHubProjectV2ParentThemeNormalizationResult(
        valid=not issues,
        issues=tuple(issues),
        normalization_ref=normalization_ref,
        snapshot_ref=snapshot_ref,
        repository=repository,
        project_id=project_id,
        items=tuple(normalized_items),
        ignored_item_count=ignored_item_count,
        boundaries=_boundaries(),
    )


def _normalize_optional_issue(
    value: Any,
    repository: str,
    label: str,
    issues: list[str],
) -> str:
    if value is None:
        return ""
    issue = _mapping(value)
    if not issue:
        issues.append(f"{label} must be an issue mapping or null")
        return ""

    issue_repository = str(
        _mapping(issue.get("repository")).get(
            "nameWithOwner",
            "",
        )
    ).strip()
    issue_number = _positive_int(issue.get("number"))
    if issue_repository != repository:
        issues.append(f"{label} repository mismatch")
        return ""
    if issue_number <= 0:
        issues.append(f"{label} number must be positive")
        return ""
    return build_github_project_v2_issue_ref(
        repository,
        issue_number,
    )


def _normalize_sub_issues(
    value: Any,
    repository: str,
    item_label: str,
    policy: GitHubProjectV2ParentThemeNormalizationPolicy,
    issues: list[str],
) -> tuple[str, ...]:
    if value is None:
        return ()

    connection = _mapping(value)
    page_info = _mapping(connection.get("pageInfo"))
    if page_info.get("hasNextPage") is True:
        issues.append(
            f"{item_label}: subIssues payload is truncated"
        )

    refs: list[str] = []
    for raw_node in _sequence(connection.get("nodes")):
        node = _mapping(raw_node)
        node_repository = str(
            _mapping(node.get("repository")).get(
                "nameWithOwner",
                "",
            )
        ).strip()
        node_number = _positive_int(node.get("number"))
        if node_repository != repository:
            issues.append(
                f"{item_label}: sub-issue repository mismatch"
            )
            continue
        if node_number <= 0:
            issues.append(
                f"{item_label}: sub-issue number must be positive"
            )
            continue
        refs.append(
            build_github_project_v2_issue_ref(
                repository,
                node_number,
            )
        )

    if len(refs) != len(set(refs)):
        issues.append(f"{item_label}: duplicate sub-issue")
    if len(refs) > policy.max_sub_issue_refs:
        issues.append(
            f"{item_label}: sub-issues exceed policy maximum"
        )
    return tuple(sorted(set(refs)))


def _normalize_themes(
    nodes: Sequence[Any],
    project_id: str,
    policy: GitHubProjectV2ParentThemeNormalizationPolicy,
    item_label: str,
    issues: list[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    refs: list[str] = []
    values: list[str] = []

    for node_value in nodes:
        node = _mapping(node_value)
        field = _mapping(node.get("field"))
        field_id = str(field.get("id", "")).strip()
        field_name = str(field.get("name", "")).strip()
        if not _matches_field(
            field_id,
            field_name,
            policy.theme_field_ids,
            policy.theme_field_names,
        ):
            continue

        value_ref, display_value = _field_value(node)
        if not field_id:
            issues.append(
                f"{item_label}: theme field id is required"
            )
            continue
        if not value_ref:
            continue

        refs.append(
            build_github_project_v2_theme_ref(
                project_id,
                field_id,
                value_ref,
            )
        )
        values.append(display_value or value_ref)

    if len(refs) != len(set(refs)):
        issues.append(f"{item_label}: duplicate theme value")
    if len(refs) > policy.max_theme_refs:
        issues.append(
            f"{item_label}: theme refs exceed policy maximum"
        )

    paired = sorted(set(zip(refs, values)))
    return (
        tuple(ref for ref, _ in paired),
        tuple(value for _, value in paired),
    )


def _normalize_status(
    nodes: Sequence[Any],
    policy: GitHubProjectV2ParentThemeNormalizationPolicy,
    item_label: str,
    issues: list[str],
) -> tuple[str, str]:
    matches: list[tuple[str, str]] = []

    for node_value in nodes:
        node = _mapping(node_value)
        field = _mapping(node.get("field"))
        field_id = str(field.get("id", "")).strip()
        field_name = str(field.get("name", "")).strip()
        if not _matches_field(
            field_id,
            field_name,
            policy.status_field_ids,
            policy.status_field_names,
        ):
            continue

        value_ref, display_value = _field_value(node)
        if value_ref:
            matches.append(
                (field_id or field_name, display_value or value_ref)
            )

    if len(matches) > 1:
        issues.append(f"{item_label}: multiple status values")
        return "", ""
    if not matches:
        if policy.require_status:
            issues.append(f"{item_label}: status value is required")
        return "", ""
    return matches[0][1], matches[0][0]


def _field_value_nodes(item: Mapping[str, Any]) -> Sequence[Any]:
    field_values = _mapping(item.get("fieldValues"))
    return _sequence(field_values.get("nodes"))


def _field_value(node: Mapping[str, Any]) -> tuple[str, str]:
    for key in ("optionId", "name", "text", "date", "number"):
        value = node.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            if key == "optionId":
                display = str(node.get("name", "")).strip()
                return text, display
            return text, text
    return "", ""


def _matches_field(
    field_id: str,
    field_name: str,
    configured_ids: Sequence[str],
    configured_names: Sequence[str],
) -> bool:
    if field_id and field_id in {
        value.strip()
        for value in configured_ids
        if value.strip()
    }:
        return True
    normalized_name = field_name.casefold()
    return normalized_name in {
        value.strip().casefold()
        for value in configured_names
        if value.strip()
    }


def _normalization_digest(
    snapshot_ref: str,
    repository: str,
    project_id: str,
    items: Sequence[
        GitHubProjectV2NormalizedParentThemeItem
    ],
) -> str:
    payload = {
        "schema": PARENT_THEME_NORMALIZATION_SCHEMA,
        "snapshot_ref": snapshot_ref,
        "repository": repository,
        "project_id": project_id,
        "items": [item.to_json_dict() for item in items],
    }
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return value
    return ()


def _positive_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("query_only_snapshot_consumed", True),
        ("external_call_performed", False),
        ("graphql_query_performed", False),
        ("graphql_mutation_allowed", False),
        ("remote_mutation_allowed", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
