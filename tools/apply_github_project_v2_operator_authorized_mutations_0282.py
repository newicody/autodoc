#!/usr/bin/env python3
"""Operator-authorized ProjectV2 mutation adapter for phase 0282-r7.

Preview is the default. Remote mutations require all of:

* an explicit ``approve`` operator decision;
* ``--execute``;
* the exact digest of every supplied r5/r6 plan;
* a valid non-collision plan whose own boundaries report no prior mutation.

The adapter reuses the existing ``gh api`` subprocess boundary. It does not
introduce an HTTP client, Scheduler path, queue, bus, registry or persistence
writer. Project view grouping remains a documented manual operator step.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping, Sequence


ADAPTER_SCHEMA = (
    "missipy.github.project_v2_operator_authorized_mutation_adapter.v1"
)
PARENT_PLAN_SCHEMA = (
    "missipy.github.project_v2_parent_sub_ticket_mutation_plan.v1"
)
THEME_PLAN_SCHEMA = (
    "missipy.github.project_v2_theme_grouping_deployment_plan.v1"
)
GITHUB_REST_API_VERSION = "2026-03-10"
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ISSUE_REF_RE = re.compile(
    r"^github-frame:(?P<repository>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    r"/issues/(?P<number>[1-9][0-9]*)$"
)
_ITEM_REF_PREFIX = "github-project-v2-item:"

_ADD_SUB_ISSUE_MUTATION = """
mutation($input: AddSubIssueInput!) {
  addSubIssue(input: $input) {
    issue { id number }
    subIssue { id number }
  }
}
""".strip()

_UPDATE_PROJECT_FIELD_MUTATION = """
mutation($input: UpdateProjectV2FieldInput!) {
  updateProjectV2Field(input: $input) {
    projectV2Field {
      ... on ProjectV2SingleSelectField {
        id
        name
        options { id name }
      }
    }
  }
}
""".strip()

_UPDATE_ITEM_FIELD_MUTATION = """
mutation($input: UpdateProjectV2ItemFieldValueInput!) {
  updateProjectV2ItemFieldValue(input: $input) {
    projectV2Item { id }
  }
}
""".strip()


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute operator-authorized ProjectV2 mutations "
            "from the deterministic 0282-r5/r6 plans."
        )
    )
    parser.add_argument("--parent-plan", type=Path)
    parser.add_argument("--theme-plan", type=Path)
    parser.add_argument(
        "--operator-decision",
        choices=("approve",),
        required=True,
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-parent-plan-digest", default="")
    parser.add_argument("--confirm-theme-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    if args.parent_plan is None and args.theme_plan is None:
        raise SystemExit(
            "at least one of --parent-plan or --theme-plan is required"
        )

    parent_plan = (
        _read_plan(args.parent_plan, PARENT_PLAN_SCHEMA)
        if args.parent_plan is not None
        else None
    )
    theme_plan = (
        _read_plan(args.theme_plan, THEME_PLAN_SCHEMA)
        if args.theme_plan is not None
        else None
    )

    report: dict[str, Any] = {
        "schema": ADAPTER_SCHEMA,
        "mode": "execute" if args.execute else "preview",
        "operator_decision": args.operator_decision,
        "parent_plan": parent_plan or {},
        "theme_plan": theme_plan or {},
        "operation_results": [],
        "manual_operator_steps": [],
        "github_mutation_performed": False,
        "partial_execution": False,
        "boundaries": {
            "local_adapter_only": True,
            "explicit_operator_authorization_required": True,
            "exact_plan_digest_confirmation_required": True,
            "preview_is_default": True,
            "view_grouping_automated": False,
            "scheduler_modified": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "projects_repository_change_required": False,
        },
    }

    validation_issues = []
    if parent_plan is not None:
        validation_issues.extend(_validate_parent_plan(parent_plan))
    if theme_plan is not None:
        validation_issues.extend(_validate_theme_plan(theme_plan))
        report["manual_operator_steps"] = list(
            theme_plan.get("operator_steps", [])
        )
    if validation_issues:
        report["validation_issues"] = validation_issues
        _emit(report, args.format)
        return 2

    if not args.execute:
        _emit(report, args.format)
        return 0

    confirmation_issues = _confirmation_issues(
        parent_plan=parent_plan,
        parent_digest=args.confirm_parent_plan_digest,
        theme_plan=theme_plan,
        theme_digest=args.confirm_theme_plan_digest,
    )
    if confirmation_issues:
        report["execution_error"] = "; ".join(confirmation_issues)
        _emit(report, args.format)
        return 3

    operation_results: list[dict[str, Any]] = []
    try:
        if parent_plan is not None:
            operation_results.extend(
                _execute_parent_plan(
                    args.gh_command,
                    parent_plan,
                )
            )
        if theme_plan is not None:
            operation_results.extend(
                _execute_theme_plan(
                    args.gh_command,
                    theme_plan,
                )
            )
    except Exception as exc:  # report partial remote execution honestly
        report["operation_results"] = operation_results
        report["github_mutation_performed"] = bool(operation_results)
        report["partial_execution"] = bool(operation_results)
        report["execution_error"] = str(exc)
        _emit(report, args.format)
        return 4

    report["operation_results"] = operation_results
    report["github_mutation_performed"] = bool(operation_results)
    _emit(report, args.format)
    return 0


def _validate_parent_plan(plan: Mapping[str, Any]) -> list[str]:
    issues = _validate_common_plan(plan, PARENT_PLAN_SCHEMA)
    action = str(plan.get("action", ""))
    allowed = {"create_and_link", "link_existing", "replay"}
    if action not in allowed:
        issues.append(f"unsupported parent plan action: {action or '-'}")
    operations = _sequence(plan.get("operations"))
    kinds = tuple(str(_mapping(op).get("kind", "")) for op in operations)
    expected = {
        "create_and_link": ("create_issue", "add_sub_issue"),
        "link_existing": ("add_sub_issue",),
        "replay": (),
    }.get(action, ())
    if kinds != expected:
        issues.append("parent plan operations do not match action")
    return issues


def _validate_theme_plan(plan: Mapping[str, Any]) -> list[str]:
    issues = _validate_common_plan(plan, THEME_PLAN_SCHEMA)
    action = str(plan.get("action", ""))
    if action not in {"create_field", "reuse_field", "update_field"}:
        issues.append(f"unsupported theme plan action: {action or '-'}")
    for raw_operation in _sequence(plan.get("operations")):
        operation = _mapping(raw_operation)
        if operation.get("execution_allowed") is not False:
            issues.append("theme operation must be non-executing in plan")
        if operation.get("requires_operator_authorization") is not True:
            issues.append("theme operation must require authorization")
        if str(operation.get("operation_kind", "")) not in {
            "field_create",
            "field_update",
            "item_theme_assignment",
        }:
            issues.append("unsupported theme operation kind")
    return issues


def _validate_common_plan(
    plan: Mapping[str, Any],
    expected_schema: str,
) -> list[str]:
    issues: list[str] = []
    if plan.get("schema") != expected_schema:
        issues.append("plan schema mismatch")
    if plan.get("valid") is not True:
        issues.append("plan must be valid")
    digest = str(plan.get("plan_digest", ""))
    if not _DIGEST_RE.fullmatch(digest):
        issues.append("plan_digest must be a SHA-256 digest")
    boundaries = _mapping(plan.get("boundaries"))
    if boundaries.get("github_mutation_performed") is not False:
        issues.append("plan already reports a GitHub mutation")
    if boundaries.get("scheduler_modified") is not False:
        issues.append("plan must not modify Scheduler")
    return issues


def _confirmation_issues(
    *,
    parent_plan: Mapping[str, Any] | None,
    parent_digest: str,
    theme_plan: Mapping[str, Any] | None,
    theme_digest: str,
) -> list[str]:
    issues: list[str] = []
    if parent_plan is not None and parent_digest != parent_plan["plan_digest"]:
        issues.append("confirm-parent-plan-digest mismatch")
    if theme_plan is not None and theme_digest != theme_plan["plan_digest"]:
        issues.append("confirm-theme-plan-digest mismatch")
    return issues


def _execute_parent_plan(
    gh_command: str,
    plan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if plan["action"] == "replay":
        return []

    created_nodes: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for raw_operation in _sequence(plan.get("operations")):
        operation = _mapping(raw_operation)
        kind = str(operation["kind"])
        if kind == "create_issue":
            repository = str(operation["repository"])
            target_ref = str(operation["target_ref"])
            response = _gh_json(
                gh_command,
                [
                    "api",
                    "--method",
                    "POST",
                    f"repos/{repository}/issues",
                    "--input",
                    "-",
                ],
                input_payload={
                    "title": str(operation["title"]),
                    "body": str(operation["body"]),
                },
            )
            created = _require_mapping(response, "create issue response")
            node_id = _required_text("created issue node_id", created.get("node_id"))
            number = _required_positive_int("created issue number", created.get("number"))
            created_nodes[target_ref] = {
                "node_id": node_id,
                "number": number,
                "repository": repository,
                "html_url": str(created.get("html_url", "")),
            }
            results.append(
                {
                    "operation_kind": kind,
                    "operation_ref": operation.get("operation_ref"),
                    "issue_number": number,
                    "node_id": node_id,
                    "html_url": created.get("html_url", ""),
                }
            )
            continue

        if kind == "add_sub_issue":
            parent_ref = str(operation["parent_issue_ref"])
            child_ref = str(operation["child_issue_ref"])
            parent_id = _resolve_issue_node_id(
                gh_command,
                parent_ref,
                created_nodes,
            )
            child_id = _resolve_issue_node_id(
                gh_command,
                child_ref,
                created_nodes,
            )
            response = _gh_graphql(
                gh_command,
                _ADD_SUB_ISSUE_MUTATION,
                {
                    "input": {
                        "issueId": parent_id,
                        "subIssueId": child_id,
                    }
                },
            )
            results.append(
                {
                    "operation_kind": kind,
                    "operation_ref": operation.get("operation_ref"),
                    "parent_node_id": parent_id,
                    "child_node_id": child_id,
                    "response": response,
                }
            )
            continue

        raise RuntimeError(f"unsupported parent operation: {kind}")
    return results


def _execute_theme_plan(
    gh_command: str,
    plan: Mapping[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    resolved_field_id = str(plan.get("field_id", ""))
    option_ids: dict[str, str] = {}

    for raw_operation in _sequence(plan.get("operations")):
        operation = _mapping(raw_operation)
        kind = str(operation["operation_kind"])
        payload = dict(_mapping(operation.get("payload")))

        if kind == "field_create":
            method, endpoint = _split_method_endpoint(
                str(operation["endpoint_or_mutation"])
            )
            if method != "POST":
                raise RuntimeError("field_create must use POST")
            api_version = str(
                payload.pop("api_version", GITHUB_REST_API_VERSION)
            )
            response = _gh_json(
                gh_command,
                [
                    "api",
                    "--method",
                    "POST",
                    "-H",
                    f"X-GitHub-Api-Version: {api_version}",
                    endpoint,
                    "--input",
                    "-",
                ],
                input_payload=payload,
            )
            field = _require_mapping(response, "create field response")
            resolved_field_id, option_ids = _field_identity(field)
            results.append(
                {
                    "operation_kind": kind,
                    "field_id": resolved_field_id,
                    "option_ids": option_ids,
                }
            )
            continue

        if kind == "field_update":
            response = _gh_graphql(
                gh_command,
                _UPDATE_PROJECT_FIELD_MUTATION,
                {"input": payload},
            )
            field = _mapping(
                _mapping(
                    _mapping(response.get("data")).get(
                        "updateProjectV2Field"
                    )
                ).get("projectV2Field")
            )
            resolved_field_id, option_ids = _field_identity(field)
            results.append(
                {
                    "operation_kind": kind,
                    "field_id": resolved_field_id,
                    "option_ids": option_ids,
                }
            )
            continue

        if kind == "item_theme_assignment":
            field_id = str(payload.get("fieldId", "")) or resolved_field_id
            theme_name = _required_text("themeName", payload.get("themeName"))
            option_id = (
                str(payload.get("singleSelectOptionId", ""))
                or option_ids.get(theme_name.casefold(), "")
            )
            item_ref = _required_text("itemRef", payload.get("itemRef"))
            if not item_ref.startswith(_ITEM_REF_PREFIX):
                raise RuntimeError("itemRef must use ProjectV2 item prefix")
            item_id = item_ref[len(_ITEM_REF_PREFIX):]
            if not field_id or not option_id:
                raise RuntimeError(
                    "theme assignment requires resolved field and option IDs"
                )
            mutation_input = {
                "projectId": _required_text(
                    "projectId", payload.get("projectId")
                ),
                "itemId": item_id,
                "fieldId": field_id,
                "value": {"singleSelectOptionId": option_id},
            }
            response = _gh_graphql(
                gh_command,
                _UPDATE_ITEM_FIELD_MUTATION,
                {"input": mutation_input},
            )
            results.append(
                {
                    "operation_kind": kind,
                    "item_id": item_id,
                    "field_id": field_id,
                    "single_select_option_id": option_id,
                    "response": response,
                }
            )
            continue

        raise RuntimeError(f"unsupported theme operation: {kind}")
    return results


def _resolve_issue_node_id(
    gh_command: str,
    issue_ref: str,
    created_nodes: Mapping[str, Mapping[str, Any]],
) -> str:
    created = created_nodes.get(issue_ref)
    if created is not None:
        return _required_text("created issue node_id", created.get("node_id"))
    match = _ISSUE_REF_RE.fullmatch(issue_ref)
    if match is None:
        raise RuntimeError(f"cannot resolve issue reference: {issue_ref}")
    response = _gh_json(
        gh_command,
        [
            "api",
            f"repos/{match.group('repository')}/issues/{match.group('number')}",
        ],
    )
    issue = _require_mapping(response, "issue lookup response")
    return _required_text("issue node_id", issue.get("node_id"))


def _field_identity(
    field: Mapping[str, Any],
) -> tuple[str, dict[str, str]]:
    field_id = str(field.get("node_id", "")) or str(field.get("id", ""))
    if not field_id:
        raise RuntimeError("field response is missing node id")
    options: dict[str, str] = {}
    for raw_option in _sequence(field.get("options")):
        option = _mapping(raw_option)
        option_id = str(option.get("id", ""))
        raw_name = option.get("name", "")
        if isinstance(raw_name, Mapping):
            name = str(raw_name.get("raw", ""))
        else:
            name = str(raw_name)
        if option_id and name:
            options[name.casefold()] = option_id
    return field_id, options


def _gh_graphql(
    command: str,
    query: str,
    variables: Mapping[str, Any],
) -> Mapping[str, Any]:
    response = _gh_json(
        command,
        ["api", "graphql", "--input", "-"],
        input_payload={"query": query, "variables": dict(variables)},
    )
    mapping = _require_mapping(response, "GraphQL response")
    errors = _sequence(mapping.get("errors"))
    if errors:
        raise RuntimeError(f"GitHub GraphQL errors: {json.dumps(errors)}")
    return mapping


def _gh_json(
    command: str,
    arguments: Sequence[str],
    *,
    input_payload: Mapping[str, Any] | None = None,
) -> object:
    input_text = (
        json.dumps(input_payload, ensure_ascii=False)
        if input_payload is not None
        else None
    )
    completed = subprocess.run(
        [command, *arguments],
        text=True,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "unknown gh failure"
        raise RuntimeError(f"GitHub CLI failed: {detail}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GitHub CLI did not return valid JSON") from exc


def _read_plan(path: Path, expected_schema: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise SystemExit(f"{path}: plan JSON must be an object")
    result = dict(payload)
    if result.get("schema") != expected_schema:
        raise SystemExit(f"{path}: unexpected plan schema")
    return result


def _split_method_endpoint(value: str) -> tuple[str, str]:
    parts = value.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise RuntimeError("endpoint_or_mutation must contain method and path")
    return parts[0].upper(), parts[1].lstrip("/")


def _required_text(label: str, value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise RuntimeError(f"{label} is required")
    return text


def _required_positive_int(label: str, value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{label} must be an integer") from exc
    if parsed <= 0:
        raise RuntimeError(f"{label} must be positive")
    return parsed


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be an object")
    return value


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return value
    return ()


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(f"mode: {report['mode']}")
    print(f"github_mutation_performed: {report['github_mutation_performed']}")
    print(f"operations: {len(report['operation_results'])}")
    if report.get("execution_error"):
        print(f"execution_error: {report['execution_error']}")
    for issue in report.get("validation_issues", []):
        print(f"validation_issue: {issue}")
    for step in report.get("manual_operator_steps", []):
        print(f"manual_step: {step}")


if __name__ == "__main__":
    raise SystemExit(main())
