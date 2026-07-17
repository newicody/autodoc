#!/usr/bin/env python3
"""Read-only ProjectV2, workflow and Actions readiness audit."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Protocol

from projects_bundle_readiness_contract import (
    ActionsPolicy,
    CurrentField,
    CurrentView,
    build_readiness_report,
    declared_fields,
    declared_views,
    evaluate_workflow,
)

_FIELD_FRAGMENTS = """
  __typename
  ... on ProjectV2Field { id name dataType }
  ... on ProjectV2SingleSelectField { id name options { id name } }
  ... on ProjectV2IterationField { id name }
"""

_PROJECT_QUERY = f"""
query($login:String!, $number:Int!) {{
  user(login:$login) {{
    projectV2(number:$number) {{
      id
      title
      number
      fields(first:100) {{
        nodes {{ {_FIELD_FRAGMENTS} }}
      }}
      views(first:100) {{
        nodes {{
          id
          name
          number
          layout
          filter
          fields(first:100) {{
            nodes {{ {_FIELD_FRAGMENTS} }}
          }}
          groupByFields(first:10) {{
            nodes {{ {_FIELD_FRAGMENTS} }}
          }}
          verticalGroupByFields(first:10) {{
            nodes {{ {_FIELD_FRAGMENTS} }}
          }}
        }}
      }}
    }}
  }}
}}
"""


class ReadTransport(Protocol):
    def rest(self, endpoint: str) -> Any: ...

    def rest_optional(self, endpoint: str) -> Any | None: ...

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any: ...


class GhCliReadTransport:
    def __init__(self, *, token: str = "", command: str = "gh") -> None:
        self._token = token.strip()
        self._command = command

    def _run(self, arguments: Sequence[str], payload: Mapping[str, Any] | None = None) -> Any:
        env = dict(os.environ)
        if self._token:
            env["GH_TOKEN"] = self._token
        completed = subprocess.run(
            [
                self._command,
                *arguments,
                *(["--input", "-"] if payload is not None else []),
            ],
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

    def rest(self, endpoint: str) -> Any:
        return self._run(
            [
                "api",
                "--method",
                "GET",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "X-GitHub-Api-Version: 2026-03-10",
                endpoint,
            ]
        )

    def rest_optional(self, endpoint: str) -> Any | None:
        try:
            return self.rest(endpoint)
        except RuntimeError as exc:
            if "HTTP 404" in str(exc) or "Not Found" in str(exc):
                return None
            raise

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any:
        return self._run(
            ["api", "graphql"],
            {"query": query, "variables": dict(variables)},
        )


def _mapping(value: object, *, name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return dict(value)


def _nodes(value: object, *, name: str) -> tuple[dict[str, Any], ...]:
    mapping = _mapping(value, name=name)
    nodes = mapping.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError(f"{name}.nodes must be an array")
    return tuple(dict(item) for item in nodes if isinstance(item, Mapping))


def _field_name(node: Mapping[str, Any]) -> str:
    return str(node.get("name") or "").strip()


def _current_field(node: Mapping[str, Any]) -> CurrentField | None:
    name = _field_name(node)
    if not name:
        return None
    typename = str(node.get("__typename") or "")
    if typename == "ProjectV2SingleSelectField":
        options_value = node.get("options")
        option_items = options_value if isinstance(options_value, list) else []
        options = tuple(
            str(item.get("name") or "").strip()
            for item in option_items
            if isinstance(item, Mapping)
        )
        return CurrentField(name=name, data_type="single_select", options=options)
    if typename == "ProjectV2IterationField":
        return CurrentField(name=name, data_type="iteration")
    data_type = str(node.get("dataType") or "").strip().lower()
    return CurrentField(name=name, data_type=data_type)


def _field_names(connection: object, *, name: str) -> tuple[str, ...]:
    return tuple(
        field_name
        for node in _nodes(connection, name=name)
        if (field_name := _field_name(node))
    )


def _load_configuration(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    configuration = _mapping(value, name="configuration")
    if configuration.get("schema") != "autodoc.github.projects_repository_configuration.v1":
        raise ValueError("unexpected Projects repository configuration schema")
    return configuration


def _project_target(configuration: Mapping[str, Any]) -> tuple[str, int]:
    project = _mapping(configuration.get("project"), name="project")
    if project.get("owner_kind") != "user":
        raise ValueError("only user-owned ProjectV2 is supported")
    owner = str(project.get("owner") or "").strip()
    number = int(project.get("number") or 0)
    if not owner or number <= 0:
        raise ValueError("project owner and number are required")
    return owner, number


def _project_inventory(
    *, owner: str, number: int, transport: ReadTransport
) -> tuple[str, str, tuple[CurrentField, ...], tuple[CurrentView, ...]]:
    payload = transport.graphql(_PROJECT_QUERY, {"login": owner, "number": number})
    data = _mapping(payload, name="graphql response").get("data")
    user = _mapping(_mapping(data, name="data").get("user"), name="data.user")
    project = _mapping(user.get("projectV2"), name="data.user.projectV2")
    fields = tuple(
        field
        for node in _nodes(project.get("fields"), name="project.fields")
        if (field := _current_field(node)) is not None
    )
    views: list[CurrentView] = []
    for node in _nodes(project.get("views"), name="project.views"):
        view_name = str(node.get("name") or "").strip()
        if not view_name:
            continue
        views.append(
            CurrentView(
                name=view_name,
                layout=str(node.get("layout") or "").strip(),
                filter=str(node.get("filter") or "").strip(),
                visible_fields=_field_names(
                    node.get("fields"), name=f"view {view_name}.fields"
                ),
                column_fields=_field_names(
                    node.get("groupByFields"),
                    name=f"view {view_name}.groupByFields",
                ),
                row_group_fields=_field_names(
                    node.get("verticalGroupByFields"),
                    name=f"view {view_name}.verticalGroupByFields",
                ),
            )
        )
    return (
        str(project.get("id") or "").strip(),
        str(project.get("title") or "").strip(),
        fields,
        tuple(views),
    )


def _workflow_source(path: Path) -> tuple[tuple[str, ...], bool, tuple[str, ...], bool, bool]:
    text = path.read_text(encoding="utf-8")
    actions = tuple(
        match.group(1).strip().strip("'\"")
        for match in re.finditer(r"^\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE)
    )
    dispatch_present = bool(re.search(r"^\s{2}workflow_dispatch:\s*$", text, flags=re.MULTILINE))
    triggers = tuple(
        trigger
        for trigger in ("issues", "project_v2_item", "schedule", "repository_dispatch")
        if re.search(rf"^\s{{2}}{re.escape(trigger)}:\s*$", text, flags=re.MULTILINE)
    )
    copilot_permission = bool(
        re.search(r"^\s{2}copilot-requests:\s*write\s*$", text, flags=re.MULTILINE)
    )
    obsolete_secret = "secrets.AUTODOC_COPILOT_TOKEN" in text
    return actions, dispatch_present, triggers, copilot_permission, obsolete_secret


def _actions_policy(repository: str, transport: ReadTransport) -> ActionsPolicy:
    payload = _mapping(
        transport.rest(f"repos/{repository}/actions/permissions"),
        name="actions permissions",
    )
    allowed_actions = str(payload.get("allowed_actions") or "").strip()
    selected: Mapping[str, Any] = {}
    if allowed_actions == "selected":
        selected_value = transport.rest(
            f"repos/{repository}/actions/permissions/selected-actions"
        )
        selected = _mapping(selected_value, name="selected actions permissions")
    patterns = selected.get("patterns_allowed", [])
    if not isinstance(patterns, list):
        patterns = []
    return ActionsPolicy(
        enabled=bool(payload.get("enabled")),
        allowed_actions=allowed_actions,
        github_owned_allowed=bool(selected.get("github_owned_allowed")),
        verified_allowed=bool(selected.get("verified_allowed")),
        patterns_allowed=tuple(str(item) for item in patterns),
        sha_pinning_required=bool(payload.get("sha_pinning_required")),
    )


def build_report(
    *,
    configuration_path: Path,
    workflow_path: Path,
    repository: str,
    transport: ReadTransport,
) -> Any:
    configuration = _load_configuration(configuration_path)
    owner, number = _project_target(configuration)
    project_id, project_title, current_fields, current_views = _project_inventory(
        owner=owner,
        number=number,
        transport=transport,
    )
    actions, dispatch_present, triggers, copilot_permission, obsolete_secret = (
        _workflow_source(workflow_path)
    )
    workflow_name = workflow_path.name
    workflow_value = transport.rest_optional(
        f"repos/{repository}/actions/workflows/{workflow_name}"
    )
    workflow_mapping = (
        _mapping(workflow_value, name="workflow") if workflow_value is not None else {}
    )
    variable_value = transport.rest_optional(
        f"repos/{repository}/actions/variables/AUTODOC_COPILOT_ADVISORY_ENABLED"
    )
    variable_mapping = (
        _mapping(variable_value, name="Copilot variable")
        if variable_value is not None
        else {}
    )
    copilot_value = str(variable_mapping.get("value") or "").strip().lower()
    workflow = evaluate_workflow(
        repository=repository,
        workflow_name=str(workflow_mapping.get("name") or workflow_name),
        workflow_path=str(workflow_mapping.get("path") or workflow_path),
        workflow_state=str(workflow_mapping.get("state") or "missing"),
        workflow_dispatch_present=dispatch_present,
        automatic_triggers=triggers,
        required_actions=actions,
        actions_policy=_actions_policy(repository, transport),
        copilot_variable_present=variable_value is not None,
        copilot_enabled=copilot_value in {"1", "true", "yes", "on"},
        copilot_permission_declared=copilot_permission,
        obsolete_copilot_secret_reference=obsolete_secret,
    )
    return build_readiness_report(
        project_owner=owner,
        project_number=number,
        project_id=project_id,
        project_title=project_title,
        expected_fields=declared_fields(configuration),
        current_fields=current_fields,
        expected_views=declared_views(configuration),
        current_views=current_views,
        workflow=workflow,
    )


def _summary(report: Any) -> str:
    lines = [
        f"project: {report.project_owner}/{report.project_number}",
        f"projectv2_exact: {str(report.projectv2_exact).lower()}",
        f"authoritative_ready: {str(report.authoritative_ready).lower()}",
        f"copilot_ready: {str(report.copilot_ready).lower()}",
        f"full_ready: {str(report.full_ready).lower()}",
        f"field_drift: {sum(not item.exact for item in report.field_checks)}",
        f"view_drift: {sum(not item.exact for item in report.view_checks)}",
        f"blocked_actions: {len(report.workflow.blocked_actions)}",
        f"manual_dispatch_only: {str(report.workflow.workflow_dispatch_present and not report.workflow.automatic_triggers).lower()}",
        "remote_mutation_allowed: false",
        "mutation_performed: false",
    ]
    lines.extend(f"warning: {item}" for item in report.warnings)
    lines.extend(f"issue: {item}" for item in report.issues)
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("projectv2_views.json"))
    parser.add_argument(
        "--workflow",
        type=Path,
        default=Path(".github/workflows/autodoc-controlled-research.yml"),
    )
    parser.add_argument("--repository", default="newicody/projects")
    parser.add_argument("--token-env", default="AUTODOC_PROJECT_TOKEN")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    try:
        report = build_report(
            configuration_path=args.config,
            workflow_path=args.workflow,
            repository=str(args.repository),
            transport=GhCliReadTransport(
                token=os.environ.get(str(args.token_env), ""),
                command=str(args.gh_command),
            ),
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_summary(report), end="")
    return 0 if report.authoritative_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
