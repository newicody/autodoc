#!/usr/bin/env python3
"""Preview or apply one capability-growth Projects publication plan.

The CLI is the concrete phase 0286-r6 adapter expected by the reuse audit.
Preview is the default and performs no GitHub call. Remote mutation requires:

* a valid immutable r5 plan whose digest recomputes exactly;
* ``--operator-decision approve``;
* ``--execute``;
* ``--confirm-plan-digest`` equal to the plan digest.

The implementation reuses the established ``gh api`` subprocess boundary.
It creates no HTTP client and gives no authority to GitHub Projects.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (  # noqa: E402
    SpecialistCapabilityGrowthCommentExecution,
    SpecialistCapabilityGrowthProjectV2Execution,
    SpecialistCapabilityGrowthProjectsOperatorExecutionCommand,
    execute_specialist_capability_growth_projects_publication,
)
from context.specialist_capability_growth_projects_publication_plan_0286 import (  # noqa: E402
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA,
    SpecialistCapabilityGrowthProjectV2FieldMutation,
    SpecialistCapabilityGrowthProjectsPublicationPlan,
)

ADAPTER_SCHEMA = (
    "missipy.specialist.capability_growth.projects_projection_cli.v1"
)

_PROJECT_FIELDS_QUERY = """
query($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
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
            dataType
            options {
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

_UPDATE_ITEM_FIELD_MUTATION = """
mutation($input: UpdateProjectV2ItemFieldValueInput!) {
  updateProjectV2ItemFieldValue(input: $input) {
    projectV2Item {
      id
    }
  }
}
""".strip()


class GhSpecialistCapabilityGrowthExecutionPort:
    """Existing ``gh api`` execution boundary used by the r6 contract."""

    def __init__(self, command: str = "gh") -> None:
        if not command.strip():
            raise ValueError("gh command must be non-empty")
        self._command = command
        self.performed_operations: list[dict[str, object]] = []

    def publish_issue_comment(
        self,
        *,
        repository: str,
        issue_number: int,
        body: str,
        marker: str,
    ) -> SpecialistCapabilityGrowthCommentExecution:
        response = self._gh_json(
            [
                "api",
                "--method",
                "POST",
                f"repos/{repository}/issues/{issue_number}/comments",
                "-f",
                f"body={body}",
            ]
        )
        payload = _require_mapping(response, "create comment response")
        comment_id = _positive_int(payload.get("id"), "comment id")
        comment_url = str(payload.get("html_url", ""))
        self.performed_operations.append(
            {
                "kind": "issue_comment",
                "comment_id": comment_id,
                "marker": marker,
                "html_url": comment_url,
            }
        )
        return SpecialistCapabilityGrowthCommentExecution(
            action="created",
            comment_id=comment_id,
            comment_url=comment_url,
        )

    def apply_projectv2_fields(
        self,
        *,
        project_id: str,
        project_item_id: str,
        field_values: tuple[tuple[str, str], ...],
    ) -> SpecialistCapabilityGrowthProjectV2Execution:
        if not field_values:
            return SpecialistCapabilityGrowthProjectV2Execution(
                action="replayed"
            )

        fields = self._load_project_fields(project_id)
        changed: list[str] = []
        for field_name, desired_value in field_values:
            field = fields.get(field_name)
            if field is None:
                raise RuntimeError(
                    f"ProjectV2 field is missing: {field_name}"
                )
            field_id = _required_text(field.get("id"), f"{field_name} id")
            data_type = str(field.get("data_type", "")).upper()
            if data_type == "TEXT":
                value: dict[str, object] = {"text": desired_value}
            elif data_type == "SINGLE_SELECT":
                options = _mapping(field.get("options"))
                option_id = str(options.get(desired_value, ""))
                if not option_id:
                    raise RuntimeError(
                        f"ProjectV2 option is missing: "
                        f"{field_name}={desired_value}"
                    )
                value = {"singleSelectOptionId": option_id}
            else:
                raise RuntimeError(
                    f"unsupported ProjectV2 field type for "
                    f"{field_name}: {data_type or '-'}"
                )

            self._gh_graphql(
                _UPDATE_ITEM_FIELD_MUTATION,
                {
                    "input": {
                        "projectId": project_id,
                        "itemId": project_item_id,
                        "fieldId": field_id,
                        "value": value,
                    }
                },
            )
            changed.append(field_name)
            self.performed_operations.append(
                {
                    "kind": "projectv2_field",
                    "field_name": field_name,
                    "desired_value": desired_value,
                }
            )

        return SpecialistCapabilityGrowthProjectV2Execution(
            action="updated",
            changed_fields=tuple(changed),
        )

    def _load_project_fields(
        self, project_id: str
    ) -> dict[str, dict[str, object]]:
        response = self._gh_graphql(
            _PROJECT_FIELDS_QUERY,
            {"projectId": project_id},
        )
        node = _mapping(_mapping(response.get("data")).get("node"))
        fields_connection = _mapping(node.get("fields"))
        result: dict[str, dict[str, object]] = {}
        for raw in _sequence(fields_connection.get("nodes")):
            item = _mapping(raw)
            name = str(item.get("name", "")).strip()
            field_id = str(item.get("id", "")).strip()
            if not name or not field_id:
                continue
            options: dict[str, str] = {}
            for raw_option in _sequence(item.get("options")):
                option = _mapping(raw_option)
                option_name = str(option.get("name", "")).strip()
                option_id = str(option.get("id", "")).strip()
                if option_name and option_id:
                    options[option_name] = option_id
            result[name] = {
                "id": field_id,
                "data_type": str(item.get("dataType", "")),
                "options": options,
            }
        return result

    def _gh_graphql(
        self, query: str, variables: Mapping[str, object]
    ) -> Mapping[str, object]:
        response = self._gh_json(
            ["api", "graphql", "--input", "-"],
            input_payload={
                "query": query,
                "variables": dict(variables),
            },
        )
        payload = _require_mapping(response, "GraphQL response")
        errors = _sequence(payload.get("errors"))
        if errors:
            raise RuntimeError(
                "GitHub GraphQL errors: "
                + json.dumps(errors, ensure_ascii=False)
            )
        return payload

    def _gh_json(
        self,
        arguments: Sequence[str],
        *,
        input_payload: Mapping[str, object] | None = None,
    ) -> object:
        completed = subprocess.run(
            [self._command, *arguments],
            cwd=_REPO_ROOT,
            text=True,
            input=(
                json.dumps(input_payload, ensure_ascii=False)
                if input_payload is not None
                else None
            ),
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
            raise RuntimeError(
                "GitHub CLI did not return valid JSON"
            ) from exc


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute one operator-authorized specialist "
            "capability-growth GitHub Projects publication."
        )
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument(
        "--operator-decision",
        choices=("approve",),
        required=True,
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument(
        "--output",
        type=Path,
        help="write the complete r6 execution report as JSON",
    )
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = load_publication_plan(args.plan)
    port = (
        GhSpecialistCapabilityGrowthExecutionPort(args.gh_command)
        if args.execute
        else None
    )
    command = SpecialistCapabilityGrowthProjectsOperatorExecutionCommand(
        plan=plan,
        operator_decision=args.operator_decision,
        execute=args.execute,
        confirmed_plan_digest=args.confirm_plan_digest,
    )

    try:
        result = execute_specialist_capability_growth_projects_publication(
            command,
            port=port,
        )
        report = {
            "schema": ADAPTER_SCHEMA,
            "result": result.to_mapping(),
            "performed_operations": (
                list(port.performed_operations) if port is not None else []
            ),
            "partial_execution": False,
            "boundaries": _boundaries(),
        }
    except Exception as exc:
        report = {
            "schema": ADAPTER_SCHEMA,
            "result": {
                "valid": False,
                "mode": "execute" if args.execute else "preview",
                "action": "failed",
                "plan_digest": plan.plan_digest,
                "issues": [str(exc)],
                "github_mutation_performed": bool(
                    port and port.performed_operations
                ),
            },
            "performed_operations": (
                list(port.performed_operations) if port is not None else []
            ),
            "partial_execution": bool(
                port and port.performed_operations
            ),
            "boundaries": _boundaries(),
        }
        _write_report(report, args.output)
        _emit(report, args.format)
        return 4

    _write_report(report, args.output)
    _emit(report, args.format)
    result_mapping = _mapping(report["result"])
    return 0 if result_mapping.get("valid") is True else 3


def load_publication_plan(
    path: Path,
) -> SpecialistCapabilityGrowthProjectsPublicationPlan:
    """Rehydrate and cryptographically verify one r5 plan JSON."""

    payload = _read_mapping(path)
    if (
        payload.get("schema")
        != SPECIALIST_CAPABILITY_GROWTH_PROJECTS_PUBLICATION_PLAN_SCHEMA
    ):
        raise ValueError("unexpected publication plan schema")

    raw_mutations = _sequence(payload.get("projectv2_field_mutations"))
    mutations = tuple(
        SpecialistCapabilityGrowthProjectV2FieldMutation(
            field_name=_required_text(
                _mapping(item).get("field_name"), "field_name"
            ),
            desired_value=_required_text(
                _mapping(item).get("desired_value"), "desired_value"
            ),
            current_value=_optional_text(
                _mapping(item).get("current_value")
            ),
            action=_required_text(
                _mapping(item).get("action"), "field action"
            ),
        )
        for item in raw_mutations
    )

    plan = SpecialistCapabilityGrowthProjectsPublicationPlan(
        schema=str(payload["schema"]),
        valid=payload.get("valid") is True,
        action=_required_text(payload.get("action"), "action"),
        issues=tuple(
            str(item) for item in _sequence(payload.get("issues"))
        ),
        repository=_required_text(
            payload.get("repository"), "repository"
        ),
        issue_number=_positive_int(
            payload.get("issue_number"), "issue_number"
        ),
        project_id=_required_text(
            payload.get("project_id"), "project_id"
        ),
        project_item_id=_required_text(
            payload.get("project_item_id"), "project_item_id"
        ),
        policy_decision_id=_required_text(
            payload.get("policy_decision_id"), "policy_decision_id"
        ),
        review_ref=_required_text(
            payload.get("review_ref"), "review_ref"
        ),
        revision_ref=_required_text(
            payload.get("revision_ref"), "revision_ref"
        ),
        sql_ref=_required_text(payload.get("sql_ref"), "sql_ref"),
        decision_ref=_required_text(
            payload.get("decision_ref"), "decision_ref"
        ),
        projection_digest_sha256=_required_text(
            payload.get("projection_digest_sha256"),
            "projection_digest_sha256",
        ),
        marker=_required_text(payload.get("marker"), "marker"),
        comment_action=_required_text(
            payload.get("comment_action"), "comment_action"
        ),
        comment_body=_required_string(
            payload.get("comment_body"), "comment_body"
        ),
        comment_body_sha256=_required_text(
            payload.get("comment_body_sha256"), "comment_body_sha256"
        ),
        existing_comment_id=_optional_positive_int(
            payload.get("existing_comment_id")
        ),
        existing_comment_url=str(
            payload.get("existing_comment_url", "")
        ),
        projectv2_action=_required_text(
            payload.get("projectv2_action"), "projectv2_action"
        ),
        projectv2_field_mutations=mutations,
        plan_digest=_required_text(
            payload.get("plan_digest"), "plan_digest"
        ),
    )

    actual_comment_digest = hashlib.sha256(
        plan.comment_body.encode("utf-8")
    ).hexdigest()
    if actual_comment_digest != plan.comment_body_sha256:
        raise ValueError("comment_body_sha256 mismatch")

    recomputed = recompute_plan_digest(plan)
    if recomputed != plan.plan_digest:
        raise ValueError("plan_digest mismatch")

    return plan


def recompute_plan_digest(
    plan: SpecialistCapabilityGrowthProjectsPublicationPlan,
) -> str:
    """Recompute the exact r5 deterministic digest."""

    payload = {
        "schema": plan.schema,
        "repository": plan.repository,
        "issue_number": plan.issue_number,
        "project_id": plan.project_id,
        "project_item_id": plan.project_item_id,
        "policy_decision_id": plan.policy_decision_id,
        "operator_decision": "approve",
        "review_ref": plan.review_ref,
        "revision_ref": plan.revision_ref,
        "sql_ref": plan.sql_ref,
        "projection_digest_sha256": plan.projection_digest_sha256,
        "marker": plan.marker,
        "comment_body_sha256": plan.comment_body_sha256,
        "field_mutations": [
            item.to_mapping() for item in plan.projectv2_field_mutations
        ],
        "action": plan.action,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _boundaries() -> dict[str, bool]:
    return {
        "preview_is_default": True,
        "explicit_operator_authorization_required": True,
        "exact_plan_digest_confirmation_required": True,
        "existing_gh_api_boundary_reused": True,
        "github_projects_authoritative": False,
        "sql_remains_durable_authority": True,
        "scheduler_remains_only_orchestrator": True,
        "qdrant_authoritative": False,
        "new_http_client_created": False,
    }


def _read_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("publication plan JSON must be an object")
    return dict(payload)


def _require_mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be an object")
    return value


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return value
    return ()


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _required_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} is required")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _positive_int(value: object, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{label} must be positive")
    return parsed


def _optional_positive_int(value: object) -> int | None:
    if value is None:
        return None
    return _positive_int(value, "existing_comment_id")


def _write_report(
    report: Mapping[str, object],
    output: Path | None,
) -> None:
    if output is None:
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _emit(report: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return

    result = _mapping(report.get("result"))
    print(f"mode: {result.get('mode', '-')}")
    print(f"valid: {result.get('valid', False)}")
    print(f"action: {result.get('action', '-')}")
    print(f"plan_digest: {result.get('plan_digest', '-')}")
    print(
        "github_mutation_performed: "
        f"{result.get('github_mutation_performed', False)}"
    )
    print(f"partial_execution: {report.get('partial_execution', False)}")
    for issue in _sequence(result.get("issues")):
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
