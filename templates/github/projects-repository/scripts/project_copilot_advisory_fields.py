#!/usr/bin/env python3
"""Project one operator-approved advisory preview into ProjectV2 card fields."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from datetime import date
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Protocol

_CONFIG_SCHEMA = "autodoc.github.projects_repository_configuration.v1"
_PREVIEW_SCHEMA = "missipy.github.copilot_advisory_publication_preview.v1"
_PLAN_SCHEMA = "autodoc.github.copilot_projectv2_projection_plan.v1"
_ALLOWED_OPERATOR_DECISIONS = frozenset({"approve"})


class GraphQLTransport(Protocol):
    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True, slots=True)
class CopilotFieldProjectionCommand:
    configuration_path: Path
    preview_path: Path
    repository: str
    issue_number: int
    policy_decision_id: str
    operator_decision: str
    updated_date: str
    execute: bool = False
    remote_mutation_allowed: bool = False
    project_projection_allowed: bool = False
    confirm_plan_digest: str = ""

    def __post_init__(self) -> None:
        if "/" not in self.repository:
            raise ValueError("repository must be owner/name")
        if self.issue_number <= 0:
            raise ValueError("issue_number must be > 0")
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")
        if self.operator_decision not in _ALLOWED_OPERATOR_DECISIONS:
            raise ValueError("operator_decision must be approve")
        try:
            date.fromisoformat(self.updated_date)
        except ValueError as exc:
            raise ValueError("updated_date must use YYYY-MM-DD") from exc


@dataclass(frozen=True, slots=True)
class FieldMutation:
    field_name: str
    field_id: str
    value_kind: str
    value: str | float
    option_id: str = ""

    def to_mapping(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "field_id": self.field_id,
            "value_kind": self.value_kind,
            "value": self.value,
            "option_id": self.option_id,
        }


@dataclass(frozen=True, slots=True)
class CopilotFieldProjectionPlan:
    valid: bool
    issues: tuple[str, ...]
    project_id: str
    item_id: str
    mutations: tuple[FieldMutation, ...]
    plan_digest: str
    remote_mutation_allowed: bool = False
    project_projection_allowed: bool = False
    mutation_performed: bool = False
    advisory_is_authority: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": _PLAN_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "project_id": self.project_id,
            "item_id": self.item_id,
            "mutations": [mutation.to_mapping() for mutation in self.mutations],
            "plan_digest": self.plan_digest,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "project_projection_allowed": self.project_projection_allowed,
            "mutation_performed": self.mutation_performed,
            "advisory_is_authority": False,
            "request_authoritative": True,
            "workflow_self_authorized": False,
        }


class GhGraphQLTransport:
    def __init__(self, *, token: str, command: str = "gh") -> None:
        if not token.strip():
            raise ValueError("AUTODOC_PROJECT_TOKEN is required")
        self._token = token
        self._command = command

    def graphql(self, query: str, variables: Mapping[str, Any]) -> Any:
        env = dict(os.environ)
        env["GH_TOKEN"] = self._token
        payload = json.dumps(
            {"query": query, "variables": dict(variables)},
            ensure_ascii=False,
        )
        completed = subprocess.run(
            [self._command, "api", "graphql", "--input", "-"],
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or "unknown gh failure"
            raise RuntimeError(f"GitHub CLI failed: {detail}")
        value = json.loads(completed.stdout)
        if isinstance(value, Mapping) and value.get("errors"):
            raise RuntimeError(f"GitHub GraphQL errors: {value['errors']}")
        return value


def _load_mapping(path: Path, *, schema: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or value.get("schema") != schema:
        raise ValueError(f"unexpected schema in {path}")
    return dict(value)


def _project(configuration: Mapping[str, Any]) -> tuple[str, int]:
    project = configuration.get("project")
    if not isinstance(project, Mapping) or project.get("owner_kind") != "user":
        raise ValueError("only a user-owned ProjectV2 is supported")
    owner = str(project.get("owner") or "").strip()
    number = int(project.get("number") or 0)
    if not owner or number <= 0:
        raise ValueError("project owner and number are required")
    return owner, number


def _required_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value.strip()


def _validate_preview(preview: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "source_candidate_ref",
        "advisory_artifact_ref",
        "summary",
        "suggested_route",
    ):
        if not isinstance(preview.get(name), str) or not str(preview.get(name)).strip():
            issues.append(f"{name} must be non-empty")
    try:
        confidence = float(preview.get("confidence"))
    except (TypeError, ValueError):
        issues.append("confidence must be numeric")
    else:
        if not 0.0 <= confidence <= 1.0:
            issues.append("confidence must be between 0 and 1")
    if preview.get("advisory_is_authority") is not False:
        issues.append("advisory_is_authority must remain false")
    if preview.get("operator_decision_required") is not True:
        issues.append("operator_decision_required must remain true")
    if preview.get("publication_gate_required") is not True:
        issues.append("publication_gate_required must remain true")
    if preview.get("github_mutation_performed") is not False:
        issues.append("preview must not claim a GitHub mutation")
    if preview.get("remote_mutation_allowed") not in (False, None):
        issues.append("preview must not pre-authorize remote mutation")
    return tuple(issues)


def _inventory_query() -> str:
    return """
query(
  $projectOwner:String!, $projectNumber:Int!,
  $repositoryOwner:String!, $repositoryName:String!, $issueNumber:Int!
) {
  user(login:$projectOwner) {
    projectV2(number:$projectNumber) {
      id
      fields(first:100) {
        nodes {
          __typename
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField { id name dataType options { id name } }
        }
      }
    }
  }
  repository(owner:$repositoryOwner, name:$repositoryName) {
    issue(number:$issueNumber) {
      projectItems(first:100) { nodes { id project { id number } } }
    }
  }
}
"""


def _extract_inventory(payload: object, *, project_number: int) -> tuple[str, str, dict[str, dict[str, Any]]]:
    if not isinstance(payload, Mapping):
        raise ValueError("GraphQL inventory must be an object")
    data = payload.get("data")
    user = data.get("user") if isinstance(data, Mapping) else None
    project = user.get("projectV2") if isinstance(user, Mapping) else None
    project_id = str(project.get("id") or "") if isinstance(project, Mapping) else ""
    field_connection = project.get("fields") if isinstance(project, Mapping) else None
    field_nodes = field_connection.get("nodes") if isinstance(field_connection, Mapping) else None
    if not project_id or not isinstance(field_nodes, list):
        raise ValueError("ProjectV2 inventory is incomplete")
    fields = {
        str(node.get("name")): dict(node)
        for node in field_nodes
        if isinstance(node, Mapping) and str(node.get("name") or "").strip()
    }
    repository = data.get("repository") if isinstance(data, Mapping) else None
    issue = repository.get("issue") if isinstance(repository, Mapping) else None
    items = issue.get("projectItems") if isinstance(issue, Mapping) else None
    nodes = items.get("nodes") if isinstance(items, Mapping) else None
    if not isinstance(nodes, list):
        raise ValueError("Issue ProjectV2 items are missing")
    item_id = ""
    for node in nodes:
        if not isinstance(node, Mapping):
            continue
        item_project = node.get("project")
        if (
            isinstance(item_project, Mapping)
            and int(item_project.get("number") or 0) == project_number
            and str(item_project.get("id") or "") == project_id
        ):
            item_id = str(node.get("id") or "")
            break
    if not item_id:
        raise ValueError("Issue is not present in the configured ProjectV2")
    return project_id, item_id, fields


def _field(configuration: Mapping[str, Any], key: str) -> str:
    projection = configuration.get("copilot_projection")
    if not isinstance(projection, Mapping):
        raise ValueError("copilot_projection configuration is required")
    return _required_text(key, projection.get(key))


def _single_select_option(field: Mapping[str, Any], name: str) -> str:
    options = field.get("options")
    if not isinstance(options, list):
        raise ValueError("single-select field options are missing")
    for option in options:
        if isinstance(option, Mapping) and option.get("name") == name:
            return _required_text("single-select option id", option.get("id"))
    raise ValueError(f"single-select option not found: {name}")


def _bounded(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _mutation(field_name: str, kind: str, value: str | float, fields: Mapping[str, Mapping[str, Any]], *, option_name: str = "") -> FieldMutation:
    field = fields.get(field_name)
    if not isinstance(field, Mapping):
        raise ValueError(f"ProjectV2 field not found: {field_name}")
    field_id = _required_text(f"{field_name}.id", field.get("id"))
    option_id = _single_select_option(field, option_name) if kind == "single_select" else ""
    return FieldMutation(field_name, field_id, kind, value, option_id)


def _plan_digest(command: CopilotFieldProjectionCommand, project_id: str, item_id: str, mutations: Sequence[FieldMutation]) -> str:
    payload = {
        "repository": command.repository,
        "issue_number": command.issue_number,
        "policy_decision_id": command.policy_decision_id,
        "project_id": project_id,
        "item_id": item_id,
        "mutations": [mutation.to_mapping() for mutation in mutations],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def plan_copilot_field_projection(
    command: CopilotFieldProjectionCommand,
    *,
    transport: GraphQLTransport,
) -> CopilotFieldProjectionPlan:
    configuration = _load_mapping(command.configuration_path, schema=_CONFIG_SCHEMA)
    preview = _load_mapping(command.preview_path, schema=_PREVIEW_SCHEMA)
    issues = list(_validate_preview(preview))
    project_owner, project_number = _project(configuration)
    repository_owner, repository_name = command.repository.split("/", 1)
    inventory = transport.graphql(
        _inventory_query(),
        {
            "projectOwner": project_owner,
            "projectNumber": project_number,
            "repositoryOwner": repository_owner,
            "repositoryName": repository_name,
            "issueNumber": command.issue_number,
        },
    )
    try:
        project_id, item_id, fields = _extract_inventory(inventory, project_number=project_number)
        status_field = _field(configuration, "status_field")
        status_value = _field(configuration, "status_value")
        mutations = (
            _mutation(status_field, "single_select", status_value, fields, option_name=status_value),
            _mutation(_field(configuration, "summary_field"), "text", _bounded(_required_text("summary", preview.get("summary")), 1024), fields),
            _mutation(_field(configuration, "route_field"), "text", _bounded(_required_text("suggested_route", preview.get("suggested_route")), 1024), fields),
            _mutation(_field(configuration, "confidence_field"), "number", float(preview.get("confidence")), fields),
            _mutation(_field(configuration, "updated_field"), "date", command.updated_date, fields),
            _mutation(_field(configuration, "artifact_field"), "text", _bounded(_required_text("advisory_artifact_ref", preview.get("advisory_artifact_ref")), 256), fields),
            _mutation(_field(configuration, "cycle_field"), "text", _bounded(_required_text("source_candidate_ref", preview.get("source_candidate_ref")), 256), fields),
        )
    except (TypeError, ValueError) as exc:
        issues.append(str(exc))
        project_id, item_id, mutations = "", "", ()
    digest = "" if issues else _plan_digest(command, project_id, item_id, mutations)
    return CopilotFieldProjectionPlan(
        valid=not issues,
        issues=tuple(dict.fromkeys(issues)),
        project_id=project_id,
        item_id=item_id,
        mutations=tuple(mutations),
        plan_digest=digest,
        remote_mutation_allowed=command.remote_mutation_allowed,
        project_projection_allowed=command.project_projection_allowed,
    )


def _value(mutation: FieldMutation) -> dict[str, Any]:
    if mutation.value_kind == "single_select":
        return {"singleSelectOptionId": mutation.option_id}
    if mutation.value_kind == "text":
        return {"text": str(mutation.value)}
    if mutation.value_kind == "number":
        return {"number": float(mutation.value)}
    if mutation.value_kind == "date":
        return {"date": str(mutation.value)}
    raise ValueError(f"unsupported field value kind: {mutation.value_kind}")


def execute_copilot_field_projection(
    command: CopilotFieldProjectionCommand,
    *,
    transport: GraphQLTransport,
) -> CopilotFieldProjectionPlan:
    plan = plan_copilot_field_projection(command, transport=transport)
    if not command.execute:
        return plan
    if not plan.valid:
        raise ValueError("invalid Copilot ProjectV2 projection plan")
    if not command.remote_mutation_allowed or not command.project_projection_allowed:
        raise ValueError("Copilot ProjectV2 projection is locked")
    if command.confirm_plan_digest != plan.plan_digest:
        raise ValueError("confirm-plan-digest mismatch")
    mutation_query = """
mutation($project:ID!, $item:ID!, $field:ID!, $value:ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(input:{
    projectId:$project, itemId:$item, fieldId:$field, value:$value
  }) { projectV2Item { id } }
}
"""
    for mutation in plan.mutations:
        transport.graphql(
            mutation_query,
            {
                "project": plan.project_id,
                "item": plan.item_id,
                "field": mutation.field_id,
                "value": _value(mutation),
            },
        )
    return CopilotFieldProjectionPlan(
        valid=True,
        issues=(),
        project_id=plan.project_id,
        item_id=plan.item_id,
        mutations=plan.mutations,
        plan_digest=plan.plan_digest,
        remote_mutation_allowed=True,
        project_projection_allowed=True,
        mutation_performed=True,
    )


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("projectv2_views.json"))
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--updated-date", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser


def _summary(plan: CopilotFieldProjectionPlan) -> str:
    lines = [
        f"valid: {str(plan.valid).lower()}",
        f"plan_digest: {plan.plan_digest}",
        f"mutations: {len(plan.mutations)}",
        f"mutation_performed: {str(plan.mutation_performed).lower()}",
        "advisory_is_authority: false",
    ]
    lines.extend(f"issue: {issue}" for issue in plan.issues)
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    command = CopilotFieldProjectionCommand(
        configuration_path=args.config,
        preview_path=args.preview,
        repository=args.repository,
        issue_number=args.issue_number,
        policy_decision_id=args.policy_decision_id,
        operator_decision=args.operator_decision,
        updated_date=args.updated_date,
        execute=args.execute,
        remote_mutation_allowed=_enabled("AUTODOC_REMOTE_MUTATION_ALLOWED"),
        project_projection_allowed=_enabled("AUTODOC_PROJECT_PROJECTION_ALLOWED"),
        confirm_plan_digest=args.confirm_plan_digest,
    )
    transport = GhGraphQLTransport(
        token=os.environ.get("AUTODOC_PROJECT_TOKEN", ""),
        command=args.gh_command,
    )
    plan = execute_copilot_field_projection(command, transport=transport)
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_summary(plan), end="")
    return 0 if plan.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
