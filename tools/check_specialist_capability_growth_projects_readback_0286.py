#!/usr/bin/env python3
"""Verify capability-growth GitHub publication by query-only readback.

Without ``--execute``, snapshots are read from local JSON files. With
``--execute``, the tool performs only GitHub reads:

* REST GET for Issue comments;
* a GraphQL ``query`` for ProjectV2 item field values.

No GraphQL mutation or REST write endpoint exists in this tool.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_REPO_ROOT, _SRC_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from context.specialist_capability_growth_projects_operator_authorized_adapter_0286 import (  # noqa: E402
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA,
    SpecialistCapabilityGrowthProjectsOperatorExecutionResult,
)
from context.specialist_capability_growth_projects_readback_readiness_0286 import (  # noqa: E402
    SpecialistCapabilityGrowthIssueCommentReadback,
    SpecialistCapabilityGrowthProjectsReadbackCommand,
    verify_specialist_capability_growth_projects_readback,
)
from tools.apply_specialist_capability_growth_projects_projection_0286 import (  # noqa: E402
    load_publication_plan,
)

READBACK_CLI_SCHEMA = (
    "missipy.specialist.capability_growth.projects_readback_cli.v1"
)

_PROJECT_ITEM_READBACK_QUERY = """
query($itemId: ID!) {
  node(id: $itemId) {
    ... on ProjectV2Item {
      id
      fieldValues(first: 100) {
        nodes {
          ... on ProjectV2ItemFieldTextValue {
            text
            field {
              ... on ProjectV2Field { name }
            }
          }
          ... on ProjectV2ItemFieldSingleSelectValue {
            name
            field {
              ... on ProjectV2SingleSelectField { name }
            }
          }
        }
      }
    }
  }
}
""".strip()


class GhQueryOnlyProjectsReadback:
    """Thin query-only ``gh api`` boundary."""

    def __init__(self, command: str = "gh") -> None:
        if not command.strip():
            raise ValueError("gh command must be non-empty")
        self._command = command

    def read_issue_comments(
        self, *, repository: str, issue_number: int
    ) -> tuple[SpecialistCapabilityGrowthIssueCommentReadback, ...]:
        payload = self._gh_json(
            [
                "api",
                "--method",
                "GET",
                f"repos/{repository}/issues/{issue_number}/comments",
                "--paginate",
                "--slurp",
            ]
        )
        pages = _sequence(payload)
        comments: list[SpecialistCapabilityGrowthIssueCommentReadback] = []
        for page in pages:
            for raw in _sequence(page):
                item = _mapping(raw)
                comments.append(
                    SpecialistCapabilityGrowthIssueCommentReadback(
                        comment_id=_positive_int(
                            item.get("id"), "comment id"
                        ),
                        body=_required_string(
                            item.get("body"), "comment body"
                        ),
                        html_url=str(item.get("html_url", "")),
                    )
                )
        return tuple(comments)

    def read_projectv2_fields(
        self, *, project_item_id: str
    ) -> tuple[tuple[str, str], ...]:
        _assert_query_only_graphql(_PROJECT_ITEM_READBACK_QUERY)
        payload = self._gh_json(
            ["api", "graphql", "--input", "-"],
            input_payload={
                "query": _PROJECT_ITEM_READBACK_QUERY,
                "variables": {"itemId": project_item_id},
            },
        )
        response = _mapping(payload)
        errors = _sequence(response.get("errors"))
        if errors:
            raise RuntimeError(
                "GitHub GraphQL errors: "
                + json.dumps(errors, ensure_ascii=False)
            )
        node = _mapping(_mapping(response.get("data")).get("node"))
        connection = _mapping(node.get("fieldValues"))
        values: dict[str, str] = {}
        for raw in _sequence(connection.get("nodes")):
            item = _mapping(raw)
            field = _mapping(item.get("field"))
            field_name = str(field.get("name", "")).strip()
            if not field_name:
                continue
            value = item.get("text")
            if value is None:
                value = item.get("name")
            if value is not None:
                values[field_name] = str(value)
        return tuple(sorted(values.items()))

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
            "Verify the r5/r6 specialist capability-growth publication "
            "through local snapshots or live query-only GitHub readback."
        )
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--execution-result", type=Path, required=True)
    parser.add_argument("--issue-comments", type=Path)
    parser.add_argument("--projectv2-fields", type=Path)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform live query-only GitHub reads",
    )
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--format", choices=("json", "summary"), default="summary"
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = load_publication_plan(args.plan)
    execution = load_execution_result(args.execution_result)

    if args.execute:
        boundary = GhQueryOnlyProjectsReadback(args.gh_command)
        comments = boundary.read_issue_comments(
            repository=plan.repository,
            issue_number=plan.issue_number,
        )
        field_values = boundary.read_projectv2_fields(
            project_item_id=plan.project_item_id
        )
        source_mode = "live_query_only"
    else:
        if args.issue_comments is None or args.projectv2_fields is None:
            raise SystemExit(
                "--issue-comments and --projectv2-fields are required "
                "without --execute"
            )
        comments = load_issue_comments(args.issue_comments)
        field_values = load_projectv2_fields(args.projectv2_fields)
        source_mode = "provided_snapshots"

    evidence = verify_specialist_capability_growth_projects_readback(
        SpecialistCapabilityGrowthProjectsReadbackCommand(
            publication_plan=plan,
            execution_result=execution,
            issue_comments=comments,
            projectv2_field_values=field_values,
            source_mode=source_mode,
        )
    )
    report = {
        "schema": READBACK_CLI_SCHEMA,
        "evidence": evidence.to_mapping(),
        "boundaries": {
            "query_only": True,
            "remote_mutation_allowed": False,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
        },
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                report, ensure_ascii=False, indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
    _emit(report, args.format)
    return 0 if evidence.valid else 3


def load_execution_result(
    path: Path,
) -> SpecialistCapabilityGrowthProjectsOperatorExecutionResult:
    payload = _read_mapping(path)
    raw = _mapping(payload.get("result")) or payload
    if raw.get("schema") != (
        SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_ADAPTER_SCHEMA
    ):
        raise ValueError("unexpected r6 execution result schema")
    return SpecialistCapabilityGrowthProjectsOperatorExecutionResult(
        schema=str(raw["schema"]),
        valid=raw.get("valid") is True,
        mode=_required_text(raw.get("mode"), "mode"),
        action=_required_text(raw.get("action"), "action"),
        issues=tuple(str(item) for item in _sequence(raw.get("issues"))),
        plan_digest=_required_text(
            raw.get("plan_digest"), "plan_digest"
        ),
        repository=_required_text(raw.get("repository"), "repository"),
        issue_number=_positive_int(
            raw.get("issue_number"), "issue_number"
        ),
        project_id=_required_text(raw.get("project_id"), "project_id"),
        project_item_id=_required_text(
            raw.get("project_item_id"), "project_item_id"
        ),
        comment_action=_required_text(
            raw.get("comment_action"), "comment_action"
        ),
        comment_id=_optional_positive_int(raw.get("comment_id")),
        comment_url=str(raw.get("comment_url", "")),
        projectv2_action=_required_text(
            raw.get("projectv2_action"), "projectv2_action"
        ),
        changed_fields=tuple(
            str(item) for item in _sequence(raw.get("changed_fields"))
        ),
        operator_decision=_required_text(
            raw.get("operator_decision"), "operator_decision"
        ),
        confirmed_plan_digest=_required_text(
            raw.get("confirmed_plan_digest"),
            "confirmed_plan_digest",
        ),
        remote_mutation_allowed=(
            raw.get("remote_mutation_allowed") is True
        ),
        github_mutation_performed=(
            raw.get("github_mutation_performed") is True
        ),
        issue_comment_published=(
            raw.get("issue_comment_published") is True
        ),
        projectv2_mutation_performed=(
            raw.get("projectv2_mutation_performed") is True
        ),
    )


def load_issue_comments(
    path: Path,
) -> tuple[SpecialistCapabilityGrowthIssueCommentReadback, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_comments = (
        _sequence(payload.get("comments"))
        if isinstance(payload, Mapping)
        else _sequence(payload)
    )
    return tuple(
        SpecialistCapabilityGrowthIssueCommentReadback(
            comment_id=_positive_int(
                _mapping(item).get("id", _mapping(item).get("comment_id")),
                "comment id",
            ),
            body=_required_string(
                _mapping(item).get("body"), "comment body"
            ),
            html_url=str(
                _mapping(item).get(
                    "html_url", _mapping(item).get("comment_url", "")
                )
            ),
        )
        for item in raw_comments
    )


def load_projectv2_fields(path: Path) -> tuple[tuple[str, str], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        raw = payload.get("field_values", payload)
    else:
        raw = payload
    if isinstance(raw, Mapping):
        return tuple(sorted((str(k), str(v)) for k, v in raw.items()))
    values: list[tuple[str, str]] = []
    for item in _sequence(raw):
        pair = _sequence(item)
        if len(pair) != 2:
            raise ValueError(
                "ProjectV2 field snapshot entries must contain name/value"
            )
        values.append((str(pair[0]), str(pair[1])))
    return tuple(sorted(values))


def _assert_query_only_graphql(query: str) -> None:
    compact = " ".join(query.split()).lower()
    if not compact.startswith("query"):
        raise ValueError("GraphQL readback must start with query")
    if "mutation" in compact:
        raise ValueError("GraphQL readback cannot contain mutation")


def _read_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("JSON input must be an object")
    return dict(payload)


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
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    return value


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
    return _positive_int(value, "comment_id")


def _emit(report: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report, ensure_ascii=False, indent=2, sort_keys=True
            )
        )
        return
    evidence = _mapping(report.get("evidence"))
    print(f"valid: {evidence.get('valid', False)}")
    print(f"action: {evidence.get('action', '-')}")
    print(f"readback_ready: {evidence.get('readback_ready', False)}")
    print(
        "deployment_ready: "
        f"{evidence.get('deployment_ready', False)}"
    )
    print(f"plan_digest: {evidence.get('plan_digest', '-')}")
    print(f"readback_digest: {evidence.get('readback_digest', '-')}")
    for issue in _sequence(evidence.get("issues")):
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
