#!/usr/bin/env python3
"""Preview or execute the exact r13 final-deliverable publication plan.

Preview is the default.  Remote mutation requires the three environment locks,
``--execute`` and an exact ``--confirm-plan-digest``.  The domain executor lives
under ``src/context``; this file only adapts GitHub CLI REST/GraphQL transport.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from context.github_controlled_advisory_issue_publication_0281 import (  # noqa: E402
    GitHubIssueCommentSnapshot,
)
from context.love_final_deliverable_publication_plan_0287 import (  # noqa: E402
    FinalDeliverableProjectV2Projection,
    ProjectV2FieldSnapshot,
)
from context.love_final_deliverable_remote_publication_0287 import (  # noqa: E402
    LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
    LoveFinalDeliverableRemotePublicationCommand,
    execute_love_final_deliverable_remote_publication,
    parse_love_final_deliverable_publication_plan,
)

_REMOTE_MUTATION_ENV = "AUTODOC_REMOTE_MUTATION_ALLOWED"
_ISSUE_PUBLICATION_ENV = "AUTODOC_ISSUE_PUBLICATION_ALLOWED"
_PROJECT_PROJECTION_ENV = "AUTODOC_PROJECT_PROJECTION_ALLOWED"

_PROJECT_ITEM_QUERY = """
query($itemId: ID!) {
  node(id: $itemId) {
    ... on ProjectV2Item {
      id
      project {
        id
        fields(first: 100) {
          nodes {
            ... on ProjectV2Field { id name dataType }
            ... on ProjectV2SingleSelectField {
              id
              name
              options { id name }
            }
          }
        }
      }
      fieldValues(first: 100) {
        nodes {
          ... on ProjectV2ItemFieldTextValue {
            text
            field { ... on ProjectV2FieldCommon { id name } }
          }
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
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
        }
      }
    }
  }
}
""".strip()

_UPDATE_PROJECT_FIELD_MUTATION = """
mutation(
  $projectId: ID!,
  $itemId: ID!,
  $fieldId: ID!,
  $value: ProjectV2FieldValue!
) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId,
      itemId: $itemId,
      fieldId: $fieldId,
      value: $value
    }
  ) {
    projectV2Item { id }
  }
}
""".strip()


class GitHubCliFinalDeliverablePublicationAdapter:
    """GitHub CLI adapter for Issue comments and one ProjectV2 field."""

    def __init__(
        self,
        *,
        gh_command: str,
        token_env: str,
    ) -> None:
        if not gh_command.strip():
            raise ValueError("gh_command must be non-empty")
        if not token_env.strip():
            raise ValueError("token_env must be non-empty")
        self._gh_command = gh_command
        self._env = os.environ.copy()
        token = self._env.get(token_env, "").strip()
        if token:
            self._env["GH_TOKEN"] = token
        self._field_cache: dict[tuple[str, str, str], dict[str, Any]] = {}

    def list_comments(
        self,
        repository: str,
        issue_number: int,
    ) -> tuple[GitHubIssueCommentSnapshot, ...]:
        payload = self._run_json(
            [
                "api",
                "--paginate",
                "--slurp",
                f"repos/{repository}/issues/{issue_number}/comments?per_page=100",
            ]
        )
        comments: list[GitHubIssueCommentSnapshot] = []
        for item in _flatten_pages(payload):
            if not isinstance(item, Mapping):
                continue
            comment_id = item.get("id")
            body = item.get("body")
            if not isinstance(comment_id, int) or not isinstance(body, str):
                continue
            comments.append(
                GitHubIssueCommentSnapshot(
                    comment_id=comment_id,
                    body=body,
                    html_url=str(item.get("html_url", "")),
                )
            )
        return tuple(comments)

    def create_comment(
        self,
        repository: str,
        issue_number: int,
        body: str,
    ) -> GitHubIssueCommentSnapshot:
        payload = self._run_json(
            [
                "api",
                "--method",
                "POST",
                f"repos/{repository}/issues/{issue_number}/comments",
                "--input",
                "-",
            ],
            input_payload={"body": body},
        )
        item = _mapping(payload, "created Issue comment")
        return GitHubIssueCommentSnapshot(
            comment_id=int(item["id"]),
            body=str(item.get("body", "")),
            html_url=str(item.get("html_url", "")),
        )

    def read_field(
        self,
        *,
        project_item_id: str,
        field_ref: str,
        field_name: str,
    ) -> ProjectV2FieldSnapshot:
        payload = self._graphql(
            _PROJECT_ITEM_QUERY,
            {"itemId": project_item_id},
        )
        node = _mapping(
            _mapping(payload, "GraphQL response").get("data"),
            "GraphQL data",
        ).get("node")
        item = _mapping(node, "ProjectV2 item")
        if str(item.get("id", "")) != project_item_id:
            raise RuntimeError("ProjectV2 item readback identity mismatch")
        project = _mapping(item.get("project"), "ProjectV2 project")
        project_id = str(project.get("id", ""))
        if not project_id:
            raise RuntimeError("ProjectV2 project id is missing")

        fields_connection = _mapping(
            project.get("fields"),
            "ProjectV2 fields",
        )
        field_nodes = _sequence(
            fields_connection.get("nodes", ()),
            "ProjectV2 field nodes",
        )
        field = _resolve_field(field_nodes, field_ref, field_name)
        field_id = str(field.get("id", ""))
        resolved_name = str(field.get("name", ""))
        field_type = _field_type(field)
        if not field_id or not resolved_name:
            raise RuntimeError("ProjectV2 field metadata is incomplete")

        value = ""
        values_connection = _mapping(
            item.get("fieldValues"),
            "ProjectV2 field values",
        )
        for raw_value in _sequence(
            values_connection.get("nodes", ()),
            "ProjectV2 field value nodes",
        ):
            if not isinstance(raw_value, Mapping):
                continue
            value_field = raw_value.get("field")
            if not isinstance(value_field, Mapping):
                continue
            if str(value_field.get("id", "")) != field_id:
                continue
            value = _project_value_as_text(raw_value)
            break

        self._field_cache[(project_item_id, field_ref, field_name)] = {
            "project_id": project_id,
            "field_id": field_id,
            "field_name": resolved_name,
            "field_type": field_type,
            "options": tuple(
                option
                for option in field.get("options", ())
                if isinstance(option, Mapping)
            ),
        }
        return ProjectV2FieldSnapshot(
            project_item_id=project_item_id,
            field_ref=field_ref,
            field_name=field_name,
            value=value,
        )

    def update_field(
        self,
        projection: FinalDeliverableProjectV2Projection,
    ) -> None:
        cache_key = (
            projection.project_item_id,
            projection.field_ref,
            projection.field_name,
        )
        metadata = self._field_cache.get(cache_key)
        if metadata is None:
            self.read_field(
                project_item_id=projection.project_item_id,
                field_ref=projection.field_ref,
                field_name=projection.field_name,
            )
            metadata = self._field_cache[cache_key]

        value = _graphql_field_value(metadata, projection.value)
        payload = self._graphql(
            _UPDATE_PROJECT_FIELD_MUTATION,
            {
                "projectId": metadata["project_id"],
                "itemId": projection.project_item_id,
                "fieldId": metadata["field_id"],
                "value": value,
            },
        )
        data = _mapping(
            _mapping(payload, "GraphQL response").get("data"),
            "GraphQL data",
        )
        mutation = _mapping(
            data.get("updateProjectV2ItemFieldValue"),
            "ProjectV2 mutation result",
        )
        updated_item = _mapping(
            mutation.get("projectV2Item"),
            "updated ProjectV2 item",
        )
        if str(updated_item.get("id", "")) != projection.project_item_id:
            raise RuntimeError("ProjectV2 mutation returned an unexpected item")

    def _graphql(
        self,
        query: str,
        variables: Mapping[str, Any],
    ) -> Any:
        return self._run_json(
            ["api", "graphql", "--input", "-"],
            input_payload={"query": query, "variables": dict(variables)},
        )

    def _run_json(
        self,
        arguments: Sequence[str],
        *,
        input_payload: Mapping[str, Any] | None = None,
    ) -> Any:
        completed = subprocess.run(
            [self._gh_command, *arguments],
            input=(
                None
                if input_payload is None
                else json.dumps(input_payload, ensure_ascii=False)
            ),
            text=True,
            capture_output=True,
            check=False,
            env=self._env,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(
                f"GitHub CLI command failed ({completed.returncode}): {detail}"
            )
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GitHub CLI returned invalid JSON") from exc


def _resolve_field(
    fields: Sequence[Any],
    field_ref: str,
    field_name: str,
) -> Mapping[str, Any]:
    by_ref = tuple(
        field
        for field in fields
        if isinstance(field, Mapping)
        and str(field.get("id", "")) == field_ref
    )
    if len(by_ref) == 1:
        field = by_ref[0]
        if str(field.get("name", "")) != field_name:
            raise RuntimeError("ProjectV2 field name differs from the plan")
        return field
    by_name = tuple(
        field
        for field in fields
        if isinstance(field, Mapping)
        and str(field.get("name", "")) == field_name
    )
    if len(by_name) != 1:
        raise RuntimeError("ProjectV2 field cannot be resolved unambiguously")
    field = by_name[0]
    if field_ref and str(field.get("id", "")) != field_ref:
        raise RuntimeError("ProjectV2 field id differs from the plan")
    return field


def _field_type(field: Mapping[str, Any]) -> str:
    if "options" in field:
        return "SINGLE_SELECT"
    return str(field.get("dataType", "")).upper()


def _project_value_as_text(value: Mapping[str, Any]) -> str:
    for key in ("text", "name", "date"):
        raw = value.get(key)
        if isinstance(raw, str):
            return raw
    number = value.get("number")
    if isinstance(number, (int, float)) and not isinstance(number, bool):
        return str(number)
    return ""


def _graphql_field_value(
    metadata: Mapping[str, Any],
    value: str,
) -> dict[str, Any]:
    field_type = str(metadata.get("field_type", "")).upper()
    if field_type == "SINGLE_SELECT":
        matches = tuple(
            option
            for option in metadata.get("options", ())
            if isinstance(option, Mapping)
            and str(option.get("name", "")) == value
        )
        if len(matches) != 1:
            raise RuntimeError(
                "ProjectV2 single-select value does not match one exact option"
            )
        return {"singleSelectOptionId": str(matches[0]["id"])}
    if field_type == "TEXT":
        return {"text": value}
    if field_type == "DATE":
        return {"date": value}
    if field_type == "NUMBER":
        try:
            return {"number": float(value)}
        except ValueError as exc:
            raise RuntimeError("ProjectV2 number value is invalid") from exc
    raise RuntimeError(f"unsupported ProjectV2 field type: {field_type}")


def _flatten_pages(value: Any) -> tuple[Any, ...]:
    if not isinstance(value, list):
        raise RuntimeError("GitHub Issue comments response must be an array")
    if value and all(isinstance(page, list) for page in value):
        return tuple(item for page in value for item in page)
    return tuple(value)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{name} must be a JSON object")
    return value


def _sequence(value: object, name: str) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return value
    raise RuntimeError(f"{name} must be a JSON array")


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        required=True,
        help="r13 plan JSON or r14 result JSON containing publication_plan",
    )
    parser.add_argument(
        "--operator-decision",
        required=True,
        choices=("approve",),
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--token-env", default="AUTODOC_PROJECT_TOKEN")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    payload = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("plan file must contain a JSON object")
    plan = parse_love_final_deliverable_publication_plan(payload)
    command = LoveFinalDeliverableRemotePublicationCommand(
        schema=LOVE_FINAL_DELIVERABLE_REMOTE_PUBLICATION_COMMAND_SCHEMA,
        plan=plan,
        operator_decision=args.operator_decision,
        execute=bool(args.execute),
        confirm_plan_digest=str(args.confirm_plan_digest),
        remote_mutation_allowed=_env_flag(_REMOTE_MUTATION_ENV),
        issue_publication_allowed=_env_flag(_ISSUE_PUBLICATION_ENV),
        project_projection_allowed=_env_flag(_PROJECT_PROJECTION_ENV),
    )
    adapter = GitHubCliFinalDeliverablePublicationAdapter(
        gh_command=args.gh_command,
        token_env=args.token_env,
    )
    result = execute_love_final_deliverable_remote_publication(
        command,
        issue_port=adapter,
        project_port=adapter,
    )
    if args.format == "json":
        print(json.dumps(result.to_mapping(), indent=2, ensure_ascii=False))
    else:
        print(
            f"mode={result.mode} action={result.action} "
            f"valid={str(result.valid).lower()} "
            f"plan_digest={result.plan_digest}"
        )
        for issue in result.issues:
            print(f"issue: {issue}")
        if result.execution_error:
            print(f"error: {result.execution_error}")
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
