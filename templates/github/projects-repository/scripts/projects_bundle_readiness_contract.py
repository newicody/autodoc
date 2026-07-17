"""Pure readiness comparison for the copied GitHub Projects bundle."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Any

_SCHEMA = "autodoc.github.projects_bundle_readiness.v1"


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_tuple(value: object, *, name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an array of strings")
    result = tuple(_text(item) for item in value)
    if any(not item for item in result):
        raise ValueError(f"{name} contains an empty value")
    return result


def _mapping_tuple(value: object, *, name: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an array")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{name} entries must be objects")
        result.append(dict(item))
    return tuple(result)


def _normalize_layout(value: object) -> str:
    text = _text(value).lower()
    return text.removesuffix("_layout")


def _normalize_data_type(value: object) -> str:
    text = _text(value).lower().replace("-", "_")
    aliases = {
        "single_select": "single_select",
        "singleselect": "single_select",
        "text": "text",
        "number": "number",
        "date": "date",
        "iteration": "iteration",
    }
    return aliases.get(text, text)


@dataclass(frozen=True, slots=True)
class DeclaredField:
    name: str
    data_type: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CurrentField:
    name: str
    data_type: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FieldReadiness:
    name: str
    exists: bool
    exact: bool
    expected_data_type: str
    actual_data_type: str
    missing_options: tuple[str, ...]
    unexpected_options: tuple[str, ...]
    drift: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "exists": self.exists,
            "exact": self.exact,
            "expected_data_type": self.expected_data_type,
            "actual_data_type": self.actual_data_type,
            "missing_options": list(self.missing_options),
            "unexpected_options": list(self.unexpected_options),
            "drift": list(self.drift),
        }


@dataclass(frozen=True, slots=True)
class DeclaredView:
    name: str
    layout: str
    filter: str
    visible_fields: tuple[str, ...]
    column_field: str = ""
    row_group_field: str = ""


@dataclass(frozen=True, slots=True)
class CurrentView:
    name: str
    layout: str
    filter: str
    visible_fields: tuple[str, ...]
    column_fields: tuple[str, ...] = ()
    row_group_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ViewReadiness:
    name: str
    exists: bool
    exact: bool
    expected_layout: str
    actual_layout: str
    expected_filter: str
    actual_filter: str
    expected_visible_fields: tuple[str, ...]
    actual_visible_fields: tuple[str, ...]
    expected_column_field: str
    actual_column_fields: tuple[str, ...]
    expected_row_group_field: str
    actual_row_group_fields: tuple[str, ...]
    drift: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "exists": self.exists,
            "exact": self.exact,
            "layout": {
                "expected": self.expected_layout,
                "actual": self.actual_layout,
            },
            "filter": {
                "expected": self.expected_filter,
                "actual": self.actual_filter,
            },
            "visible_fields": {
                "expected": list(self.expected_visible_fields),
                "actual": list(self.actual_visible_fields),
            },
            "column_field": {
                "expected": self.expected_column_field,
                "actual": list(self.actual_column_fields),
            },
            "row_group_field": {
                "expected": self.expected_row_group_field,
                "actual": list(self.actual_row_group_fields),
            },
            "drift": list(self.drift),
        }


@dataclass(frozen=True, slots=True)
class ActionsPolicy:
    enabled: bool
    allowed_actions: str
    github_owned_allowed: bool = False
    verified_allowed: bool = False
    patterns_allowed: tuple[str, ...] = ()
    sha_pinning_required: bool = False


@dataclass(frozen=True, slots=True)
class WorkflowReadiness:
    repository: str
    workflow_name: str
    workflow_path: str
    workflow_state: str
    workflow_dispatch_present: bool
    automatic_triggers: tuple[str, ...]
    required_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    unpinned_actions: tuple[str, ...]
    actions_policy: ActionsPolicy
    copilot_variable_present: bool
    copilot_enabled: bool
    copilot_permission_declared: bool
    obsolete_copilot_secret_reference: bool
    authoritative_ready: bool
    copilot_ready: bool
    issues: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "workflow": {
                "name": self.workflow_name,
                "path": self.workflow_path,
                "state": self.workflow_state,
                "workflow_dispatch_present": self.workflow_dispatch_present,
                "automatic_triggers": list(self.automatic_triggers),
                "manual_dispatch_only": (
                    self.workflow_dispatch_present and not self.automatic_triggers
                ),
            },
            "actions_policy": {
                "enabled": self.actions_policy.enabled,
                "allowed_actions": self.actions_policy.allowed_actions,
                "github_owned_allowed": self.actions_policy.github_owned_allowed,
                "verified_allowed": self.actions_policy.verified_allowed,
                "patterns_allowed": list(self.actions_policy.patterns_allowed),
                "sha_pinning_required": self.actions_policy.sha_pinning_required,
            },
            "required_actions": list(self.required_actions),
            "blocked_actions": list(self.blocked_actions),
            "unpinned_actions": list(self.unpinned_actions),
            "copilot": {
                "variable_present": self.copilot_variable_present,
                "enabled": self.copilot_enabled,
                "permission_declared": self.copilot_permission_declared,
                "obsolete_secret_reference": self.obsolete_copilot_secret_reference,
            },
            "authoritative_ready": self.authoritative_ready,
            "copilot_ready": self.copilot_ready,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class ProjectsBundleReadinessReport:
    project_owner: str
    project_number: int
    project_id: str
    project_title: str
    field_checks: tuple[FieldReadiness, ...]
    view_checks: tuple[ViewReadiness, ...]
    workflow: WorkflowReadiness
    projectv2_exact: bool
    authoritative_ready: bool
    copilot_ready: bool
    full_ready: bool
    issues: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA,
            "project": {
                "owner": self.project_owner,
                "number": self.project_number,
                "id": self.project_id,
                "title": self.project_title,
            },
            "projectv2_exact": self.projectv2_exact,
            "field_checks": [item.to_mapping() for item in self.field_checks],
            "view_checks": [item.to_mapping() for item in self.view_checks],
            "workflow_readiness": self.workflow.to_mapping(),
            "authoritative_ready": self.authoritative_ready,
            "copilot_ready": self.copilot_ready,
            "full_ready": self.full_ready,
            "issues": list(self.issues),
            "warnings": list(self.warnings),
            "remote_mutation_allowed": False,
            "mutation_performed": False,
        }


def declared_fields(configuration: Mapping[str, Any]) -> tuple[DeclaredField, ...]:
    result: list[DeclaredField] = []
    for item in _mapping_tuple(configuration.get("fields"), name="fields"):
        name = _text(item.get("name"))
        data_type = _normalize_data_type(item.get("data_type"))
        if not name or not data_type:
            raise ValueError("field name and data_type are required")
        options = tuple(
            _text(option.get("name"))
            for option in _mapping_tuple(item.get("options", ()), name=f"{name}.options")
        )
        if any(not option for option in options):
            raise ValueError(f"{name}.options contains an empty name")
        result.append(DeclaredField(name=name, data_type=data_type, options=options))
    return tuple(result)


def declared_views(configuration: Mapping[str, Any]) -> tuple[DeclaredView, ...]:
    result: list[DeclaredView] = []
    for item in _mapping_tuple(configuration.get("views"), name="views"):
        name = _text(item.get("name"))
        layout = _normalize_layout(item.get("layout"))
        if not name or not layout:
            raise ValueError("view name and layout are required")
        manual = item.get("manual_layout")
        if manual is not None and not isinstance(manual, Mapping):
            raise ValueError(f"{name}.manual_layout must be an object")
        manual_mapping = dict(manual or {})
        result.append(
            DeclaredView(
                name=name,
                layout=layout,
                filter=_text(item.get("filter")),
                visible_fields=_string_tuple(
                    item.get("visible_fields", ()), name=f"{name}.visible_fields"
                ),
                column_field=_text(manual_mapping.get("column_field")),
                row_group_field=_text(manual_mapping.get("group_by")),
            )
        )
    return tuple(result)


def compare_fields(
    expected: Sequence[DeclaredField],
    current: Sequence[CurrentField],
) -> tuple[FieldReadiness, ...]:
    by_name: dict[str, list[CurrentField]] = {}
    for item in current:
        by_name.setdefault(item.name, []).append(item)
    checks: list[FieldReadiness] = []
    for declaration in expected:
        matches = by_name.get(declaration.name, [])
        drift: list[str] = []
        if len(matches) != 1:
            drift.append(
                "field missing" if not matches else "field name is not unique"
            )
            checks.append(
                FieldReadiness(
                    name=declaration.name,
                    exists=bool(matches),
                    exact=False,
                    expected_data_type=declaration.data_type,
                    actual_data_type=(matches[0].data_type if matches else ""),
                    missing_options=declaration.options,
                    unexpected_options=(),
                    drift=tuple(drift),
                )
            )
            continue
        actual = matches[0]
        expected_type = _normalize_data_type(declaration.data_type)
        actual_type = _normalize_data_type(actual.data_type)
        if actual_type != expected_type:
            drift.append(f"data_type expected {expected_type}, got {actual_type}")
        missing_options = tuple(sorted(set(declaration.options) - set(actual.options)))
        unexpected_options = tuple(sorted(set(actual.options) - set(declaration.options)))
        if missing_options:
            drift.append("missing options: " + ", ".join(missing_options))
        if unexpected_options:
            drift.append("unexpected options: " + ", ".join(unexpected_options))
        checks.append(
            FieldReadiness(
                name=declaration.name,
                exists=True,
                exact=not drift,
                expected_data_type=expected_type,
                actual_data_type=actual_type,
                missing_options=missing_options,
                unexpected_options=unexpected_options,
                drift=tuple(drift),
            )
        )
    return tuple(checks)


def compare_views(
    expected: Sequence[DeclaredView],
    current: Sequence[CurrentView],
) -> tuple[ViewReadiness, ...]:
    by_name: dict[str, list[CurrentView]] = {}
    for item in current:
        by_name.setdefault(item.name, []).append(item)
    checks: list[ViewReadiness] = []
    for declaration in expected:
        matches = by_name.get(declaration.name, [])
        drift: list[str] = []
        if len(matches) != 1:
            drift.append("view missing" if not matches else "view name is not unique")
            actual = matches[0] if matches else CurrentView("", "", "", ())
        else:
            actual = matches[0]
            if _normalize_layout(actual.layout) != declaration.layout:
                drift.append(
                    f"layout expected {declaration.layout}, got {_normalize_layout(actual.layout)}"
                )
            if actual.filter.strip() != declaration.filter.strip():
                drift.append("filter differs")
            if actual.visible_fields != declaration.visible_fields:
                drift.append("visible fields or their order differ")
            expected_columns = (
                (declaration.column_field,) if declaration.column_field else ()
            )
            if actual.column_fields != expected_columns:
                drift.append("board column field differs")
            expected_rows = (
                (declaration.row_group_field,) if declaration.row_group_field else ()
            )
            if actual.row_group_fields != expected_rows:
                drift.append("vertical group field differs")
        checks.append(
            ViewReadiness(
                name=declaration.name,
                exists=bool(matches),
                exact=len(matches) == 1 and not drift,
                expected_layout=declaration.layout,
                actual_layout=_normalize_layout(actual.layout),
                expected_filter=declaration.filter,
                actual_filter=actual.filter,
                expected_visible_fields=declaration.visible_fields,
                actual_visible_fields=actual.visible_fields,
                expected_column_field=declaration.column_field,
                actual_column_fields=actual.column_fields,
                expected_row_group_field=declaration.row_group_field,
                actual_row_group_fields=actual.row_group_fields,
                drift=tuple(drift),
            )
        )
    return tuple(checks)


def _is_full_sha_reference(action: str) -> bool:
    if "@" not in action:
        return action.startswith("./") or action.startswith("docker://")
    reference = action.rsplit("@", 1)[1]
    return len(reference) == 40 and all(character in "0123456789abcdefABCDEF" for character in reference)


def _action_allowed(action: str, policy: ActionsPolicy) -> bool:
    if action.startswith("./") or action.startswith("docker://"):
        return True
    if not policy.enabled:
        return False
    if policy.allowed_actions == "all":
        return True
    if policy.allowed_actions == "local_only":
        return False
    if policy.allowed_actions != "selected":
        return False
    if action.startswith("actions/") and policy.github_owned_allowed:
        return True
    return any(fnmatchcase(action, pattern) for pattern in policy.patterns_allowed)


def evaluate_workflow(
    *,
    repository: str,
    workflow_name: str,
    workflow_path: str,
    workflow_state: str,
    workflow_dispatch_present: bool,
    automatic_triggers: Sequence[str],
    required_actions: Sequence[str],
    actions_policy: ActionsPolicy,
    copilot_variable_present: bool,
    copilot_enabled: bool,
    copilot_permission_declared: bool,
    obsolete_copilot_secret_reference: bool,
) -> WorkflowReadiness:
    required = tuple(dict.fromkeys(_text(item) for item in required_actions if _text(item)))
    blocked = tuple(item for item in required if not _action_allowed(item, actions_policy))
    unpinned = tuple(
        item
        for item in required
        if actions_policy.sha_pinning_required and not _is_full_sha_reference(item)
    )
    issues: list[str] = []
    warnings: list[str] = []
    if not actions_policy.enabled:
        issues.append("GitHub Actions are disabled for the repository")
    if workflow_state.lower() != "active":
        issues.append(f"workflow state is {workflow_state or 'missing'}")
    if not workflow_dispatch_present:
        issues.append("workflow_dispatch trigger is missing")
    if blocked:
        issues.append("blocked actions: " + ", ".join(blocked))
    if unpinned:
        issues.append("actions require full SHA pinning: " + ", ".join(unpinned))
    triggers = tuple(dict.fromkeys(_text(item) for item in automatic_triggers if _text(item)))
    if workflow_dispatch_present and not triggers:
        warnings.append("workflow is manual-dispatch only; the local transition dispatcher is required")
    if not copilot_variable_present:
        warnings.append("AUTODOC_COPILOT_ADVISORY_ENABLED is absent")
    elif not copilot_enabled:
        warnings.append("Copilot advisory is explicitly disabled")
    if obsolete_copilot_secret_reference:
        issues.append("workflow references obsolete AUTODOC_COPILOT_TOKEN")
    if copilot_enabled and not copilot_permission_declared:
        warnings.append("Copilot is enabled but copilot-requests: write is missing")
    authoritative_ready = not issues
    copilot_ready = (
        authoritative_ready and copilot_enabled and copilot_permission_declared
    )
    return WorkflowReadiness(
        repository=repository,
        workflow_name=workflow_name,
        workflow_path=workflow_path,
        workflow_state=workflow_state,
        workflow_dispatch_present=workflow_dispatch_present,
        automatic_triggers=triggers,
        required_actions=required,
        blocked_actions=blocked,
        unpinned_actions=unpinned,
        actions_policy=actions_policy,
        copilot_variable_present=copilot_variable_present,
        copilot_enabled=copilot_enabled,
        copilot_permission_declared=copilot_permission_declared,
        obsolete_copilot_secret_reference=obsolete_copilot_secret_reference,
        authoritative_ready=authoritative_ready,
        copilot_ready=copilot_ready,
        issues=tuple(issues),
        warnings=tuple(warnings),
    )


def build_readiness_report(
    *,
    project_owner: str,
    project_number: int,
    project_id: str,
    project_title: str,
    expected_fields: Sequence[DeclaredField],
    current_fields: Sequence[CurrentField],
    expected_views: Sequence[DeclaredView],
    current_views: Sequence[CurrentView],
    workflow: WorkflowReadiness,
) -> ProjectsBundleReadinessReport:
    field_checks = compare_fields(expected_fields, current_fields)
    view_checks = compare_views(expected_views, current_views)
    projectv2_exact = all(item.exact for item in (*field_checks, *view_checks))
    issues: list[str] = []
    warnings: list[str] = list(workflow.warnings)
    for item in field_checks:
        issues.extend(f"field {item.name}: {drift}" for drift in item.drift)
    for item in view_checks:
        issues.extend(f"view {item.name}: {drift}" for drift in item.drift)
    issues.extend(workflow.issues)
    authoritative_ready = projectv2_exact and workflow.authoritative_ready
    copilot_ready = authoritative_ready and workflow.copilot_ready
    return ProjectsBundleReadinessReport(
        project_owner=project_owner,
        project_number=project_number,
        project_id=project_id,
        project_title=project_title,
        field_checks=field_checks,
        view_checks=view_checks,
        workflow=workflow,
        projectv2_exact=projectv2_exact,
        authoritative_ready=authoritative_ready,
        copilot_ready=copilot_ready,
        full_ready=copilot_ready,
        issues=tuple(issues),
        warnings=tuple(dict.fromkeys(warnings)),
    )
