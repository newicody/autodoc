#!/usr/bin/env python3
"""Project a Copilot v2 preview into the existing ProjectV2 Copilot fields.

The v2 path deliberately does not write the historical route or confidence
fields. Its four analytical values are rendered into the existing generic
``Avis Copilot`` text field.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from build_copilot_advisory_v2_publication_preview import (
    render_projectv2_v2_summary,
)
from project_copilot_advisory_fields import (
    CopilotFieldProjectionCommand,
    FieldMutation,
    GhGraphQLTransport,
    GraphQLTransport,
    _bounded,
    _extract_inventory,
    _field,
    _inventory_query,
    _load_mapping,
    _mutation,
    _project,
    _required_text,
    _value,
)

_CONFIG_SCHEMA = "autodoc.github.projects_repository_configuration.v1"
_PREVIEW_SCHEMA = "missipy.github.copilot_advisory_publication_preview.v2"
_PLAN_SCHEMA = "autodoc.github.copilot_projectv2_projection_plan.v2"


@dataclass(frozen=True, slots=True)
class CopilotV2FieldProjectionPlan:
    valid: bool
    issues: tuple[str, ...]
    project_id: str
    item_id: str
    mutations: tuple[FieldMutation, ...]
    plan_digest: str
    remote_mutation_allowed: bool
    project_projection_allowed: bool
    mutation_performed: bool = False
    readback_verified: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": _PLAN_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "project_id": self.project_id,
            "item_id": self.item_id,
            "mutations": [item.to_mapping() for item in self.mutations],
            "plan_digest": self.plan_digest,
            "remote_mutation_allowed": self.remote_mutation_allowed,
            "project_projection_allowed": self.project_projection_allowed,
            "mutation_performed": self.mutation_performed,
            "readback_verified": self.readback_verified,
            "request_authoritative": True,
            "advisory_is_authority": False,
            "route_field_mutated": False,
            "confidence_field_mutated": False,
        }


def plan_copilot_v2_field_projection(
    command: CopilotFieldProjectionCommand,
    *,
    transport: GraphQLTransport,
) -> CopilotV2FieldProjectionPlan:
    configuration = _load_mapping(command.configuration_path, schema=_CONFIG_SCHEMA)
    preview = _load_mapping(command.preview_path, schema=_PREVIEW_SCHEMA)
    issues = list(_validate_preview(preview))
    if preview.get("repository") != command.repository:
        issues.append("publication preview repository mismatch")
    if preview.get("issue_number") != command.issue_number:
        issues.append("publication preview Issue mismatch")
    if issues:
        return CopilotV2FieldProjectionPlan(
            valid=False,
            issues=tuple(dict.fromkeys(issues)),
            project_id="",
            item_id="",
            mutations=(),
            plan_digest="",
            remote_mutation_allowed=command.remote_mutation_allowed,
            project_projection_allowed=command.project_projection_allowed,
        )
    owner, number = _project(configuration)
    repository_owner, repository_name = command.repository.split("/", 1)
    inventory = transport.graphql(
        _inventory_query(),
        {
            "projectOwner": owner,
            "projectNumber": number,
            "repositoryOwner": repository_owner,
            "repositoryName": repository_name,
            "issueNumber": command.issue_number,
        },
    )
    try:
        project_id, item_id, fields = _extract_inventory(inventory, project_number=number)
        status_field = _field(configuration, "status_field")
        status_value = _field(configuration, "status_value")
        mutations = (
            _mutation(
                status_field,
                "single_select",
                status_value,
                fields,
                option_name=status_value,
            ),
            _mutation(
                _field(configuration, "summary_field"),
                "text",
                _bounded(render_projectv2_v2_summary(preview), 1024),
                fields,
            ),
            _mutation(
                _field(configuration, "updated_field"),
                "date",
                command.updated_date,
                fields,
            ),
            _mutation(
                _field(configuration, "artifact_field"),
                "text",
                _bounded(
                    _required_text(
                        "advisory_artifact_ref",
                        preview.get("advisory_artifact_ref"),
                    ),
                    256,
                ),
                fields,
            ),
            _mutation(
                _field(configuration, "cycle_field"),
                "text",
                _bounded(
                    _required_text(
                        "source_candidate_ref",
                        preview.get("source_candidate_ref"),
                    ),
                    256,
                ),
                fields,
            ),
        )
    except (TypeError, ValueError) as exc:
        issues.append(str(exc))
        project_id, item_id, mutations = "", "", ()
    digest = "" if issues else _v2_plan_digest(command, project_id, item_id, mutations)
    return CopilotV2FieldProjectionPlan(
        valid=not issues,
        issues=tuple(dict.fromkeys(issues)),
        project_id=project_id,
        item_id=item_id,
        mutations=tuple(mutations),
        plan_digest=digest,
        remote_mutation_allowed=command.remote_mutation_allowed,
        project_projection_allowed=command.project_projection_allowed,
    )


def execute_copilot_v2_field_projection(
    command: CopilotFieldProjectionCommand,
    *,
    transport: GraphQLTransport,
) -> CopilotV2FieldProjectionPlan:
    plan = plan_copilot_v2_field_projection(command, transport=transport)
    if not command.execute:
        return plan
    if not plan.valid:
        raise ValueError("invalid Copilot v2 ProjectV2 projection plan")
    if not command.remote_mutation_allowed or not command.project_projection_allowed:
        raise ValueError("Copilot v2 ProjectV2 projection is locked")
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
    readback = transport.graphql(_readback_query(), {"item": plan.item_id})
    _verify_readback(readback, item_id=plan.item_id, mutations=plan.mutations)
    return CopilotV2FieldProjectionPlan(
        valid=True,
        issues=(),
        project_id=plan.project_id,
        item_id=plan.item_id,
        mutations=plan.mutations,
        plan_digest=plan.plan_digest,
        remote_mutation_allowed=True,
        project_projection_allowed=True,
        mutation_performed=True,
        readback_verified=True,
    )


def _v2_plan_digest(
    command: CopilotFieldProjectionCommand,
    project_id: str,
    item_id: str,
    mutations: Sequence[FieldMutation],
) -> str:
    payload = {
        "schema": _PLAN_SCHEMA,
        "repository": command.repository,
        "issue_number": command.issue_number,
        "policy_decision_id": command.policy_decision_id,
        "project_id": project_id,
        "item_id": item_id,
        "mutations": [mutation.to_mapping() for mutation in mutations],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _readback_query() -> str:
    return """
query($item:ID!) {
 node(id:$item) {
  ... on ProjectV2Item {
   id
   fieldValues(first:100) {
    nodes {
     __typename
     ... on ProjectV2ItemFieldTextValue {
      text
      field { ... on ProjectV2FieldCommon { id name } }
     }
     ... on ProjectV2ItemFieldDateValue {
      date
      field { ... on ProjectV2FieldCommon { id name } }
     }
     ... on ProjectV2ItemFieldNumberValue {
      number
      field { ... on ProjectV2FieldCommon { id name } }
     }
     ... on ProjectV2ItemFieldSingleSelectValue {
      name
      optionId
      field { ... on ProjectV2FieldCommon { id name } }
     }
    }
   }
  }
 }
}
"""


def _verify_readback(
    payload: object,
    *,
    item_id: str,
    mutations: Sequence[FieldMutation],
) -> None:
    if not isinstance(payload, Mapping):
        raise RuntimeError("ProjectV2 readback must be an object")
    data = payload.get("data")
    node = data.get("node") if isinstance(data, Mapping) else None
    if not isinstance(node, Mapping) or node.get("id") != item_id:
        raise RuntimeError("ProjectV2 readback item mismatch")
    connection = node.get("fieldValues")
    nodes = connection.get("nodes") if isinstance(connection, Mapping) else None
    if not isinstance(nodes, list):
        raise RuntimeError("ProjectV2 readback field values are missing")
    values: dict[str, Mapping[str, Any]] = {}
    for entry in nodes:
        if not isinstance(entry, Mapping):
            continue
        field = entry.get("field")
        field_name = field.get("name") if isinstance(field, Mapping) else None
        if isinstance(field_name, str) and field_name:
            if field_name in values:
                raise RuntimeError(
                    f"ProjectV2 readback contains duplicate field: {field_name}"
                )
            values[field_name] = entry
    mismatches: list[str] = []
    for mutation in mutations:
        entry = values.get(mutation.field_name)
        if entry is None or not _readback_matches(mutation, entry):
            mismatches.append(mutation.field_name)
    if mismatches:
        raise RuntimeError(
            "ProjectV2 readback mismatch: " + ", ".join(sorted(mismatches))
        )


def _readback_matches(
    mutation: FieldMutation,
    entry: Mapping[str, Any],
) -> bool:
    if mutation.value_kind == "single_select":
        return entry.get("optionId") == mutation.option_id
    if mutation.value_kind == "text":
        return entry.get("text") == str(mutation.value)
    if mutation.value_kind == "date":
        return entry.get("date") == str(mutation.value)
    if mutation.value_kind == "number":
        value = entry.get("number")
        if isinstance(value, bool):
            return False
        try:
            return float(value) == float(mutation.value)
        except (TypeError, ValueError):
            return False
    return False


def _validate_preview(preview: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "source_candidate_ref",
        "advisory_artifact_ref",
        "concrete_objective",
        "expected_result",
        "repository",
    ):
        if not isinstance(preview.get(name), str) or not str(preview.get(name)).strip():
            issues.append(f"{name} must be non-empty")
    issue_number = preview.get("issue_number")
    if isinstance(issue_number, bool) or not isinstance(issue_number, int) or issue_number <= 0:
        issues.append("issue_number must be a positive integer")
    if preview.get("advisory_schema") != "missipy.github.copilot_advisory.v2":
        issues.append("advisory_schema must identify Copilot advisory v2")
    for name in ("provided_constraints", "success_criteria"):
        value = preview.get(name)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            issues.append(f"{name} must be a JSON string array")
    if not preview.get("success_criteria"):
        issues.append("success_criteria must not be empty")
    if preview.get("request_authoritative") is not True:
        issues.append("request_authoritative must remain true")
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
    return tuple(dict.fromkeys(issues))


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
    plan = execute_copilot_v2_field_projection(command, transport=transport)
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"valid: {str(plan.valid).lower()}")
        print(f"plan_digest: {plan.plan_digest}")
        print(f"mutations: {len(plan.mutations)}")
        print(f"mutation_performed: {str(plan.mutation_performed).lower()}")
        print(f"readback_verified: {str(plan.readback_verified).lower()}")
        print("advisory_is_authority: false")
        for issue in plan.issues:
            print(f"issue: {issue}")
    return 0 if plan.valid else 2


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    raise SystemExit(main())
