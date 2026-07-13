"""ProjectV2 theme-grouping deployment plan for phase 0282-r6.

This module produces a deterministic, non-executing plan for:

* creating or updating a ProjectV2 single-select theme field;
* preserving existing option identities when updating that field;
* assigning theme values to project items;
* confirming or requesting manual view grouping by that field.

It performs no network request, GraphQL mutation, REST mutation, persistence
write, scheduling or laboratory execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from context.github_project_v2_cycle_lineage_0282 import (
    build_github_project_v2_theme_ref,
)


THEME_GROUPING_PLAN_SCHEMA = (
    "missipy.github.project_v2_theme_grouping_deployment_plan.v1"
)
THEME_GROUPING_OPERATION_SCHEMA = (
    "missipy.github.project_v2_theme_grouping_operation.v1"
)
GITHUB_REST_API_VERSION = "2026-03-10"

_ALLOWED_COLORS = frozenset(
    {
        "BLUE",
        "GRAY",
        "GREEN",
        "ORANGE",
        "PINK",
        "PURPLE",
        "RED",
        "YELLOW",
    }
)


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeOptionSpec:
    name: str
    color: str = "GRAY"
    description: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeOptionSnapshot:
    option_id: str
    name: str
    color: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeFieldSnapshot:
    field_id: str
    name: str
    data_type: str
    options: tuple[GitHubProjectV2ThemeOptionSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeAssignmentSpec:
    project_item_ref: str
    theme_name: str


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ViewGroupingSnapshot:
    view_number: int
    view_name: str
    grouped_field_id: str = ""


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeGroupingDeploymentCommand:
    owner_kind: str
    owner_login: str
    project_number: int
    project_id: str
    field_name: str
    desired_options: tuple[GitHubProjectV2ThemeOptionSpec, ...]
    existing_fields: tuple[GitHubProjectV2ThemeFieldSnapshot, ...] = ()
    assignments: tuple[GitHubProjectV2ThemeAssignmentSpec, ...] = ()
    views: tuple[GitHubProjectV2ViewGroupingSnapshot, ...] = ()
    target_view_number: int = 0


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeGroupingDeploymentPolicy:
    require_single_select: bool = True
    allow_option_extension: bool = True
    allow_option_rewrite: bool = False
    require_view_grouping: bool = True
    allow_manual_view_grouping: bool = True
    max_options: int = 32
    max_assignments: int = 1000

    def __post_init__(self) -> None:
        if self.max_options <= 0:
            raise ValueError("max_options must be > 0")
        if self.max_assignments < 0:
            raise ValueError("max_assignments must be >= 0")


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeGroupingOperation:
    operation_kind: str
    transport_kind: str
    operation_name: str
    endpoint_or_mutation: str
    payload: tuple[tuple[str, Any], ...]
    requires_operator_authorization: bool
    execution_allowed: bool
    requires_response_resolution: bool

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": THEME_GROUPING_OPERATION_SCHEMA,
            "operation_kind": self.operation_kind,
            "transport_kind": self.transport_kind,
            "operation_name": self.operation_name,
            "endpoint_or_mutation": self.endpoint_or_mutation,
            "payload": dict(self.payload),
            "requires_operator_authorization": (
                self.requires_operator_authorization
            ),
            "execution_allowed": self.execution_allowed,
            "requires_response_resolution": (
                self.requires_response_resolution
            ),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ThemeGroupingDeploymentResult:
    valid: bool
    issues: tuple[str, ...]
    action: str
    plan_ref: str
    plan_digest: str
    field_id: str
    field_name: str
    option_refs: tuple[tuple[str, str], ...]
    operations: tuple[GitHubProjectV2ThemeGroupingOperation, ...]
    view_grouping_action: str
    operator_steps: tuple[str, ...]
    boundaries: tuple[tuple[str, bool], ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": THEME_GROUPING_PLAN_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "action": self.action,
            "plan_ref": self.plan_ref,
            "plan_digest": self.plan_digest,
            "field_id": self.field_id,
            "field_name": self.field_name,
            "option_refs": dict(self.option_refs),
            "operations": [
                operation.to_json_dict()
                for operation in self.operations
            ],
            "view_grouping_action": self.view_grouping_action,
            "operator_steps": list(self.operator_steps),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"project_v2_theme_grouping_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"action={self.action}",
                f"operations={len(self.operations)}",
                f"view_grouping={self.view_grouping_action}",
                "execution_allowed=False",
                "github_mutation_performed=False",
            )
        )


def plan_github_project_v2_theme_grouping_deployment(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
    policy: GitHubProjectV2ThemeGroupingDeploymentPolicy | None = None,
) -> GitHubProjectV2ThemeGroupingDeploymentResult:
    active_policy = (
        policy or GitHubProjectV2ThemeGroupingDeploymentPolicy()
    )
    normalized = _normalize_command(command)
    issues = _validate_command(normalized, active_policy)

    matching_fields = tuple(
        field
        for field in normalized.existing_fields
        if field.name.casefold() == normalized.field_name.casefold()
    )
    if len(matching_fields) > 1:
        issues.append("multiple existing fields match field_name")

    action = "collision" if issues else ""
    field_id = ""
    operations: list[GitHubProjectV2ThemeGroupingOperation] = []
    operator_steps: list[str] = []
    option_ids_by_name: dict[str, str] = {}

    if not issues:
        if not matching_fields:
            action = "create_field"
            operations.append(
                _create_field_operation(normalized)
            )
            operator_steps.append(
                "Authorize creation of the single-select theme field."
            )
        else:
            existing = matching_fields[0]
            field_id = existing.field_id
            if (
                active_policy.require_single_select
                and existing.data_type.casefold() != "single_select"
            ):
                issues.append(
                    "existing theme field is not single_select"
                )
                action = "collision"
            else:
                option_ids_by_name = {
                    option.name.casefold(): option.option_id
                    for option in existing.options
                }
                existing_options = {
                    option.name.casefold(): option
                    for option in existing.options
                }
                desired_options = {
                    option.name.casefold(): option
                    for option in normalized.desired_options
                }

                removed = sorted(
                    set(existing_options) - set(desired_options)
                )
                added = sorted(
                    set(desired_options) - set(existing_options)
                )
                changed = sorted(
                    name
                    for name in (
                        set(existing_options) & set(desired_options)
                    )
                    if _option_signature(
                        existing_options[name]
                    )
                    != _option_signature(
                        desired_options[name]
                    )
                )

                if removed and not active_policy.allow_option_rewrite:
                    issues.append(
                        "desired options would remove existing options"
                    )
                    action = "collision"
                elif (
                    (added or changed)
                    and not active_policy.allow_option_extension
                ):
                    issues.append(
                        "existing options differ from desired options"
                    )
                    action = "collision"
                elif added or changed or removed:
                    action = "update_field"
                    operations.append(
                        _update_field_operation(
                            normalized,
                            existing,
                        )
                    )
                    operator_steps.append(
                        "Authorize updateProjectV2Field with all "
                        "existing option IDs preserved."
                    )
                else:
                    action = "reuse_field"

    option_refs: list[tuple[str, str]] = []
    if not issues:
        for option in normalized.desired_options:
            option_id = option_ids_by_name.get(
                option.name.casefold(),
                "",
            )
            option_ref_basis = option_id or option.name
            option_refs.append(
                (
                    option.name,
                    build_github_project_v2_theme_ref(
                        normalized.project_id,
                        field_id or f"pending:{normalized.field_name}",
                        option_ref_basis,
                    ),
                )
            )

        assignment_issues, assignment_operations = (
            _plan_assignment_operations(
                normalized,
                field_id,
                option_ids_by_name,
            )
        )
        issues.extend(assignment_issues)
        operations.extend(assignment_operations)
        if assignment_operations:
            operator_steps.append(
                "Authorize item theme assignments after field and "
                "option IDs are resolved."
            )

    view_grouping_action = "not_requested"
    if not issues and active_policy.require_view_grouping:
        view_grouping_action = _view_grouping_action(
            normalized,
            field_id,
        )
        if view_grouping_action == "manual_grouping_required":
            if not active_policy.allow_manual_view_grouping:
                issues.append(
                    "view grouping is not confirmed and manual grouping "
                    "is forbidden by policy"
                )
            else:
                operator_steps.append(
                    "Open the target Project view, choose Group by, "
                    "select the theme field, then save the view."
                )
        elif view_grouping_action == "view_collision":
            issues.append(
                "target view is grouped by a different field"
            )

    if issues:
        action = "collision"
        operations = []
        option_refs = []
        operator_steps = []

    canonical = {
        "owner_kind": normalized.owner_kind,
        "owner_login": normalized.owner_login,
        "project_number": normalized.project_number,
        "project_id": normalized.project_id,
        "field_name": normalized.field_name,
        "desired_options": [
            {
                "name": option.name,
                "color": option.color,
                "description": option.description,
            }
            for option in normalized.desired_options
        ],
        "assignments": [
            {
                "project_item_ref": assignment.project_item_ref,
                "theme_name": assignment.theme_name,
            }
            for assignment in normalized.assignments
        ],
        "target_view_number": normalized.target_view_number,
        "action": action,
        "view_grouping_action": view_grouping_action,
        "operations": [
            operation.to_json_dict()
            for operation in operations
        ],
    }
    digest = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return GitHubProjectV2ThemeGroupingDeploymentResult(
        valid=not issues,
        issues=tuple(issues),
        action=action,
        plan_ref=(
            f"github-project-v2-theme-grouping-plan:{digest[:16]}"
            if not issues
            else ""
        ),
        plan_digest=digest,
        field_id=field_id,
        field_name=normalized.field_name,
        option_refs=tuple(sorted(option_refs)),
        operations=tuple(operations),
        view_grouping_action=view_grouping_action,
        operator_steps=tuple(operator_steps),
        boundaries=_boundaries(),
    )


def _normalize_command(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
) -> GitHubProjectV2ThemeGroupingDeploymentCommand:
    return GitHubProjectV2ThemeGroupingDeploymentCommand(
        owner_kind=command.owner_kind.strip().casefold(),
        owner_login=command.owner_login.strip(),
        project_number=command.project_number,
        project_id=command.project_id.strip(),
        field_name=command.field_name.strip(),
        desired_options=tuple(
            sorted(
                (
                    GitHubProjectV2ThemeOptionSpec(
                        name=option.name.strip(),
                        color=option.color.strip().upper(),
                        description=option.description.strip(),
                    )
                    for option in command.desired_options
                ),
                key=lambda option: option.name.casefold(),
            )
        ),
        existing_fields=tuple(
            sorted(
                (
                    GitHubProjectV2ThemeFieldSnapshot(
                        field_id=field.field_id.strip(),
                        name=field.name.strip(),
                        data_type=field.data_type.strip(),
                        options=tuple(
                            sorted(
                                (
                                    GitHubProjectV2ThemeOptionSnapshot(
                                        option_id=option.option_id.strip(),
                                        name=option.name.strip(),
                                        color=option.color.strip().upper(),
                                        description=option.description.strip(),
                                    )
                                    for option in field.options
                                ),
                                key=lambda option: option.name.casefold(),
                            )
                        ),
                    )
                    for field in command.existing_fields
                ),
                key=lambda field: (
                    field.name.casefold(),
                    field.field_id,
                ),
            )
        ),
        assignments=tuple(
            sorted(
                (
                    GitHubProjectV2ThemeAssignmentSpec(
                        project_item_ref=assignment.project_item_ref.strip(),
                        theme_name=assignment.theme_name.strip(),
                    )
                    for assignment in command.assignments
                ),
                key=lambda assignment: assignment.project_item_ref,
            )
        ),
        views=tuple(
            sorted(
                (
                    GitHubProjectV2ViewGroupingSnapshot(
                        view_number=view.view_number,
                        view_name=view.view_name.strip(),
                        grouped_field_id=view.grouped_field_id.strip(),
                    )
                    for view in command.views
                ),
                key=lambda view: view.view_number,
            )
        ),
        target_view_number=command.target_view_number,
    )


def _validate_command(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
    policy: GitHubProjectV2ThemeGroupingDeploymentPolicy,
) -> list[str]:
    issues: list[str] = []
    if command.owner_kind not in {"user", "organization"}:
        issues.append("owner_kind must be user or organization")
    if not command.owner_login:
        issues.append("owner_login is required")
    if command.project_number <= 0:
        issues.append("project_number must be > 0")
    if not command.project_id.startswith("PVT_"):
        issues.append("project_id must start with PVT_")
    if not command.field_name:
        issues.append("field_name is required")
    if not command.desired_options:
        issues.append("at least one desired option is required")
    if len(command.desired_options) > policy.max_options:
        issues.append("desired options exceed policy maximum")
    if len(command.assignments) > policy.max_assignments:
        issues.append("assignments exceed policy maximum")

    option_names = tuple(
        option.name.casefold()
        for option in command.desired_options
    )
    if not all(option_names):
        issues.append("desired option names must be non-empty")
    if len(option_names) != len(set(option_names)):
        issues.append("desired option names must be unique")
    for option in command.desired_options:
        if option.color not in _ALLOWED_COLORS:
            issues.append(
                f"unsupported option color: {option.color}"
            )

    field_ids = tuple(
        field.field_id
        for field in command.existing_fields
    )
    if any(not field_id for field_id in field_ids):
        issues.append("existing field IDs must be non-empty")
    if len(field_ids) != len(set(field_ids)):
        issues.append("existing field IDs must be unique")

    assignment_items = tuple(
        assignment.project_item_ref
        for assignment in command.assignments
    )
    if any(
        not item_ref.startswith("github-project-v2-item:")
        for item_ref in assignment_items
    ):
        issues.append(
            "assignment project_item_ref must use "
            "github-project-v2-item prefix"
        )
    if len(assignment_items) != len(set(assignment_items)):
        issues.append("assignment project items must be unique")

    allowed_themes = set(option_names)
    for assignment in command.assignments:
        if assignment.theme_name.casefold() not in allowed_themes:
            issues.append(
                "assignment theme_name is not a desired option"
            )

    if command.target_view_number < 0:
        issues.append("target_view_number must be >= 0")
    view_numbers = tuple(view.view_number for view in command.views)
    if any(number <= 0 for number in view_numbers):
        issues.append("view numbers must be > 0")
    if len(view_numbers) != len(set(view_numbers)):
        issues.append("view numbers must be unique")
    return issues


def _create_field_operation(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
) -> GitHubProjectV2ThemeGroupingOperation:
    owner_segment = (
        "users"
        if command.owner_kind == "user"
        else "orgs"
    )
    endpoint = (
        f"/{owner_segment}/{command.owner_login}/projectsV2/"
        f"{command.project_number}/fields"
    )
    payload = {
        "name": command.field_name,
        "data_type": "single_select",
        "single_select_options": [
            {
                "name": option.name,
                "color": option.color,
                "description": option.description,
            }
            for option in command.desired_options
        ],
        "api_version": GITHUB_REST_API_VERSION,
    }
    return GitHubProjectV2ThemeGroupingOperation(
        operation_kind="field_create",
        transport_kind="rest",
        operation_name="add_project_v2_field",
        endpoint_or_mutation=f"POST {endpoint}",
        payload=tuple(sorted(payload.items())),
        requires_operator_authorization=True,
        execution_allowed=False,
        requires_response_resolution=True,
    )


def _update_field_operation(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
    existing: GitHubProjectV2ThemeFieldSnapshot,
) -> GitHubProjectV2ThemeGroupingOperation:
    existing_by_name = {
        option.name.casefold(): option
        for option in existing.options
    }
    options = []
    for desired in command.desired_options:
        existing_option = existing_by_name.get(
            desired.name.casefold()
        )
        option_payload = {
            "name": desired.name,
            "color": desired.color,
            "description": desired.description,
        }
        if existing_option is not None:
            option_payload["id"] = existing_option.option_id
        options.append(option_payload)

    payload = {
        "fieldId": existing.field_id,
        "name": command.field_name,
        "singleSelectOptions": options,
    }
    return GitHubProjectV2ThemeGroupingOperation(
        operation_kind="field_update",
        transport_kind="graphql",
        operation_name="updateProjectV2Field",
        endpoint_or_mutation="mutation updateProjectV2Field",
        payload=tuple(sorted(payload.items())),
        requires_operator_authorization=True,
        execution_allowed=False,
        requires_response_resolution=True,
    )


def _plan_assignment_operations(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
    field_id: str,
    option_ids_by_name: dict[str, str],
) -> tuple[list[str], list[GitHubProjectV2ThemeGroupingOperation]]:
    issues: list[str] = []
    operations: list[GitHubProjectV2ThemeGroupingOperation] = []

    for assignment in command.assignments:
        option_id = option_ids_by_name.get(
            assignment.theme_name.casefold(),
            "",
        )
        payload = {
            "projectId": command.project_id,
            "itemRef": assignment.project_item_ref,
            "fieldId": field_id,
            "themeName": assignment.theme_name,
            "singleSelectOptionId": option_id,
        }
        operations.append(
            GitHubProjectV2ThemeGroupingOperation(
                operation_kind="item_theme_assignment",
                transport_kind="graphql",
                operation_name="updateProjectV2ItemFieldValue",
                endpoint_or_mutation=(
                    "mutation updateProjectV2ItemFieldValue"
                ),
                payload=tuple(sorted(payload.items())),
                requires_operator_authorization=True,
                execution_allowed=False,
                requires_response_resolution=(
                    not field_id or not option_id
                ),
            )
        )

    return issues, operations


def _view_grouping_action(
    command: GitHubProjectV2ThemeGroupingDeploymentCommand,
    field_id: str,
) -> str:
    if command.target_view_number <= 0:
        return "manual_grouping_required"

    matches = tuple(
        view
        for view in command.views
        if view.view_number == command.target_view_number
    )
    if not matches:
        return "manual_grouping_required"

    view = matches[0]
    if field_id and view.grouped_field_id == field_id:
        return "replay"
    if view.grouped_field_id and view.grouped_field_id != field_id:
        return "view_collision"
    return "manual_grouping_required"


def _option_signature(option: Any) -> tuple[str, str, str]:
    return (
        option.name.casefold(),
        option.color.upper(),
        option.description,
    )


def _boundaries() -> tuple[tuple[str, bool], ...]:
    return (
        ("plan_only", True),
        ("external_call_performed", False),
        ("rest_mutation_allowed", False),
        ("graphql_mutation_allowed", False),
        ("github_mutation_performed", False),
        ("view_mutation_automated", False),
        ("sql_write_allowed", False),
        ("qdrant_write_allowed", False),
        ("scheduler_modified", False),
        ("projects_repository_change_required", False),
    )
