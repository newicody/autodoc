#!/usr/bin/env python3
"""Plan or apply fields and views owned by the copied Projects repository."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Protocol

_SCHEMA = "autodoc.github.projects_repository_configuration.v1"
_PLAN_SCHEMA = "autodoc.github.projectv2_configuration_plan.v1"
_ALLOWED_FIELD_TYPES = frozenset({"text", "number", "date", "single_select", "iteration"})
_ALLOWED_LAYOUTS = frozenset({"table", "board", "roadmap"})


class GitHubTransport(Protocol):
    def rest(self, method: str, endpoint: str, payload: Mapping[str, Any] | None = None) -> Any: ...
    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True, slots=True)
class ProjectConfigurationCommand:
    configuration_path: Path
    execute: bool = False
    remote_mutation_allowed: bool = False
    project_configuration_allowed: bool = False
    confirm_plan_digest: str = ""


@dataclass(frozen=True, slots=True)
class ProjectConfigurationPlan:
    valid: bool
    issues: tuple[str, ...]
    owner: str
    number: int
    user_id: int
    missing_fields: tuple[Mapping[str, Any], ...]
    existing_fields: tuple[str, ...]
    field_option_drift: tuple[str, ...]
    missing_views: tuple[Mapping[str, Any], ...]
    existing_views: tuple[str, ...]
    unresolved_visible_fields: tuple[str, ...]
    manual_layout_steps: tuple[str, ...]
    plan_digest: str
    remote_mutation_allowed: bool = False
    project_configuration_allowed: bool = False
    mutation_performed: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": _PLAN_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "project": {"owner": self.owner, "number": self.number, "user_id": self.user_id},
            "missing_fields": [dict(item) for item in self.missing_fields],
            "existing_fields": list(self.existing_fields),
            "field_option_drift": list(self.field_option_drift),
            "missing_views": [dict(item) for item in self.missing_views],
            "existing_views": list(self.existing_views),
            "unresolved_visible_fields": list(self.unresolved_visible_fields),
            "manual_layout_steps": list(self.manual_layout_steps),
            "plan_digest": self.plan_digest,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "project_configuration_allowed": self.project_configuration_allowed,
            "mutation_performed": self.mutation_performed,
            "workflow_mutation_allowed": False,
        }


class GhCliTransport:
    def __init__(self, *, token: str, command: str = "gh") -> None:
        if not token.strip():
            raise ValueError("AUTODOC_PROJECT_TOKEN is required")
        self._token = token
        self._command = command

    def rest(self, method: str, endpoint: str, payload: Mapping[str, Any] | None = None) -> Any:
        args = [
            "api",
            "--method",
            method,
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2026-03-10",
            endpoint,
        ]
        return self._run(args, payload)

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any:
        return self._run(
            ["api", "graphql"],
            {"query": query, "variables": dict(variables)},
        )

    def _run(self, arguments: Sequence[str], payload: Mapping[str, Any] | None) -> Any:
        env = dict(os.environ)
        env["GH_TOKEN"] = self._token
        completed = subprocess.run(
            [self._command, *arguments, *( ["--input", "-"] if payload is not None else [] )],
            input=(None if payload is None else json.dumps(payload, ensure_ascii=False)),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "unknown gh failure"
            raise RuntimeError(f"GitHub CLI failed: {detail}")
        if not completed.stdout.strip():
            return None
        return json.loads(completed.stdout)


def _load_configuration(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or value.get("schema") != _SCHEMA:
        raise ValueError("unexpected Projects repository configuration schema")
    return dict(value)


def _mapping_sequence(value: object, *, name: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be an array")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{name} entries must be objects")
        result.append(dict(item))
    return tuple(result)


def _project(configuration: Mapping[str, Any]) -> tuple[str, int]:
    project = configuration.get("project")
    if not isinstance(project, Mapping) or project.get("owner_kind") != "user":
        raise ValueError("only a user-owned ProjectV2 is supported")
    owner = str(project.get("owner") or "").strip()
    number = int(project.get("number") or 0)
    if not owner or number <= 0:
        raise ValueError("project owner and number are required")
    return owner, number


def _field_payload(declaration: Mapping[str, Any]) -> dict[str, Any]:
    name = str(declaration.get("name") or "").strip()
    data_type = str(declaration.get("data_type") or "").strip()
    if not name or data_type not in _ALLOWED_FIELD_TYPES:
        raise ValueError(f"invalid field declaration: {name or '<unnamed>'}")
    payload: dict[str, Any] = {"name": name, "data_type": data_type}
    if data_type == "single_select":
        options = _mapping_sequence(declaration.get("options"), name=f"{name}.options")
        if not options:
            raise ValueError(f"single-select field {name} requires options")
        payload["single_select_options"] = [
            {
                "name": str(option.get("name") or "").strip(),
                "color": str(option.get("color") or "GRAY").strip().upper(),
                "description": str(option.get("description") or "").strip(),
            }
            for option in options
        ]
        if any(not item["name"] for item in payload["single_select_options"]):
            raise ValueError(f"single-select field {name} contains an empty option")
    return payload


def _inventory(owner: str, number: int, transport: GitHubTransport) -> tuple[int, dict[str, dict[str, Any]], set[str]]:
    user = transport.rest("GET", f"users/{owner}")
    if not isinstance(user, Mapping) or int(user.get("id") or 0) <= 0:
        raise ValueError("GitHub user numeric id could not be resolved")
    fields_value = transport.rest("GET", f"users/{owner}/projectsV2/{number}/fields?per_page=100")
    if not isinstance(fields_value, list):
        raise ValueError("ProjectV2 fields response must be a JSON array")
    fields = {
        str(item.get("name")): dict(item)
        for item in fields_value
        if isinstance(item, Mapping) and str(item.get("name") or "").strip()
    }
    query = """
query($login:String!, $number:Int!) {
  user(login:$login) {
    projectV2(number:$number) {
      views(first:100) { nodes { name } }
    }
  }
}
"""
    payload = transport.graphql(query, {"login": owner, "number": number})
    data = payload.get("data") if isinstance(payload, Mapping) else None
    user_data = data.get("user") if isinstance(data, Mapping) else None
    project = user_data.get("projectV2") if isinstance(user_data, Mapping) else None
    views = project.get("views") if isinstance(project, Mapping) else None
    nodes = views.get("nodes") if isinstance(views, Mapping) else None
    if not isinstance(nodes, list):
        raise ValueError("ProjectV2 views response is missing")
    view_names = {
        str(node.get("name"))
        for node in nodes
        if isinstance(node, Mapping) and str(node.get("name") or "").strip()
    }
    return int(user["id"]), fields, view_names


def _field_id(value: Mapping[str, Any]) -> int | None:
    try:
        identifier = int(value.get("id"))
    except (TypeError, ValueError):
        return None
    return identifier if identifier > 0 else None


def _option_names(field: Mapping[str, Any]) -> set[str]:
    values = field.get("single_select_options", field.get("options", []))
    if not isinstance(values, list):
        return set()
    names: set[str] = set()
    for item in values:
        if not isinstance(item, Mapping):
            continue
        value = item.get("name")
        if isinstance(value, Mapping):
            value = value.get("raw", value.get("html", ""))
        text = str(value or "").strip()
        if text:
            names.add(text)
    return names


def _view_payload(view: Mapping[str, Any], field_ids: Mapping[str, int]) -> tuple[dict[str, Any], tuple[str, ...]]:
    name = str(view.get("name") or "").strip()
    layout = str(view.get("layout") or "").strip()
    if not name or layout not in _ALLOWED_LAYOUTS:
        raise ValueError(f"invalid view declaration: {name or '<unnamed>'}")
    visible = view.get("visible_fields", [])
    if not isinstance(visible, list) or not all(isinstance(item, str) for item in visible):
        raise ValueError(f"view {name} visible_fields must be strings")
    unresolved = tuple(item for item in visible if item not in field_ids)
    payload: dict[str, Any] = {
        "name": name,
        "layout": layout,
        "filter": str(view.get("filter") or "").strip(),
    }
    if layout != "roadmap":
        payload["visible_fields"] = [field_ids[item] for item in visible if item in field_ids]
    return payload, unresolved


def _digest_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan_projectv2_configuration(
    command: ProjectConfigurationCommand,
    *,
    transport: GitHubTransport,
) -> ProjectConfigurationPlan:
    configuration = _load_configuration(command.configuration_path)
    owner, number = _project(configuration)
    user_id, fields, view_names = _inventory(owner, number, transport)
    declarations = _mapping_sequence(configuration.get("fields"), name="fields")
    declared_names = {str(item.get("name") or "").strip() for item in declarations}
    missing_fields: list[Mapping[str, Any]] = []
    existing_fields: list[str] = []
    option_drift: list[str] = []
    for declaration in declarations:
        payload = _field_payload(declaration)
        name = str(payload["name"])
        current = fields.get(name)
        if current is None:
            missing_fields.append(payload)
            continue
        existing_fields.append(name)
        expected = {
            str(item["name"])
            for item in payload.get("single_select_options", [])
            if isinstance(item, Mapping)
        }
        missing_options = sorted(expected - _option_names(current))
        if missing_options:
            option_drift.append(f"{name}: options manquantes: {', '.join(missing_options)}")

    field_ids = {
        name: identifier
        for name, value in fields.items()
        if (identifier := _field_id(value)) is not None
    }
    missing_views: list[Mapping[str, Any]] = []
    existing_views: list[str] = []
    unresolved: set[str] = set()
    manual_steps: list[str] = []
    for view in _mapping_sequence(configuration.get("views"), name="views"):
        payload, missing = _view_payload(view, field_ids)
        unresolved.update(missing)
        name = str(payload["name"])
        if name in view_names:
            existing_views.append(name)
        else:
            missing_views.append(payload)
        manual = view.get("manual_layout")
        if isinstance(manual, Mapping) and manual:
            settings = ", ".join(f"{key}={value}" for key, value in manual.items())
            manual_steps.append(f"{name}: {settings}")

    issues: list[str] = []
    unresolved_external = sorted(unresolved - declared_names)
    if unresolved_external:
        issues.append(
            "visible fields are neither present nor declared: "
            + ", ".join(unresolved_external)
        )
    digest_basis = {
        "owner": owner,
        "number": number,
        "missing_fields": missing_fields,
        "missing_views": missing_views,
        "configured_views": _mapping_sequence(configuration.get("views"), name="views"),
        "unresolved_visible_fields": sorted(unresolved),
        "field_option_drift": option_drift,
        "manual_layout_steps": manual_steps,
    }
    return ProjectConfigurationPlan(
        valid=not issues,
        issues=tuple(issues),
        owner=owner,
        number=number,
        user_id=user_id,
        missing_fields=tuple(missing_fields),
        existing_fields=tuple(sorted(existing_fields)),
        field_option_drift=tuple(option_drift),
        missing_views=tuple(missing_views),
        existing_views=tuple(sorted(existing_views)),
        unresolved_visible_fields=tuple(sorted(unresolved)),
        manual_layout_steps=tuple(manual_steps),
        plan_digest=_digest_payload(digest_basis),
        remote_mutation_allowed=command.remote_mutation_allowed,
        project_configuration_allowed=command.project_configuration_allowed,
    )


def execute_projectv2_configuration(
    command: ProjectConfigurationCommand,
    *,
    transport: GitHubTransport,
) -> ProjectConfigurationPlan:
    plan = plan_projectv2_configuration(command, transport=transport)
    if not command.execute:
        return plan
    if not plan.valid:
        raise ValueError("invalid ProjectV2 configuration plan")
    if not command.remote_mutation_allowed or not command.project_configuration_allowed:
        raise ValueError("ProjectV2 configuration mutation is locked")
    if command.confirm_plan_digest != plan.plan_digest:
        raise ValueError("confirm-plan-digest mismatch")

    mutation_needed = bool(plan.missing_fields or plan.missing_views)
    fields_endpoint = f"users/{plan.owner}/projectsV2/{plan.number}/fields"
    for payload in plan.missing_fields:
        transport.rest("POST", fields_endpoint, payload)

    if plan.missing_fields:
        refreshed = ProjectConfigurationCommand(
            configuration_path=command.configuration_path,
            execute=False,
            remote_mutation_allowed=command.remote_mutation_allowed,
            project_configuration_allowed=command.project_configuration_allowed,
        )
        plan = plan_projectv2_configuration(refreshed, transport=transport)

    if plan.unresolved_visible_fields:
        raise ValueError("visible fields remain unresolved after field creation")
    views_endpoint = f"users/{plan.owner}/projectsV2/{plan.number}/views"
    for payload in plan.missing_views:
        transport.rest("POST", views_endpoint, payload)

    result = plan_projectv2_configuration(
        ProjectConfigurationCommand(configuration_path=command.configuration_path),
        transport=transport,
    )
    return replace(
        result,
        remote_mutation_allowed=True,
        project_configuration_allowed=True,
        mutation_performed=mutation_needed,
    )


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("projectv2_views.json"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def _summary(plan: ProjectConfigurationPlan) -> str:
    lines = [
        f"valid: {str(plan.valid).lower()}",
        f"project: {plan.owner}/{plan.number}",
        f"plan_digest: {plan.plan_digest}",
        f"missing_fields: {len(plan.missing_fields)}",
        f"missing_views: {len(plan.missing_views)}",
        f"mutation_performed: {str(plan.mutation_performed).lower()}",
    ]
    lines.extend(f"manual: {step}" for step in plan.manual_layout_steps)
    lines.extend(f"issue: {issue}" for issue in plan.issues)
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    command = ProjectConfigurationCommand(
        configuration_path=args.config,
        execute=args.execute,
        remote_mutation_allowed=_enabled("AUTODOC_REMOTE_MUTATION_ALLOWED"),
        project_configuration_allowed=_enabled("AUTODOC_PROJECT_CONFIGURATION_ALLOWED"),
        confirm_plan_digest=args.confirm_plan_digest,
    )
    transport = GhCliTransport(
        token=os.environ.get("AUTODOC_PROJECT_TOKEN", ""),
        command=args.gh_command,
    )
    plan = execute_projectv2_configuration(command, transport=transport)
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_summary(plan), end="")
    return 0 if plan.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
