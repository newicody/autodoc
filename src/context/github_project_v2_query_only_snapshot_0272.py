"""Pure contracts for the 0272-r3 GitHub ProjectV2 query-only snapshot.

The GraphQL transport lives in the CLI boundary.  This module carries only
immutable configuration, plans, normalized snapshot data and serializable
results.  It never carries a token value and never performs IO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

SNAPSHOT_SCHEMA = "missipy.github.project_v2_query_only_snapshot.v1"
REPORT_SCHEMA = "missipy.github.project_v2_query_only_snapshot_report.v1"
_SOURCE_MODE = "project_v2_query_only_snapshot"

FIELDS_QUERY = """
query AutodocProjectV2Fields(
  $login: String!
  $number: Int!
  $first: Int!
  $after: String
) {
  user(login: $login) {
    projectV2(number: $number) {
      id
      number
      title
      url
      closed
      fields(first: $first, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          __typename
          ... on ProjectV2FieldCommon {
            id
            name
            dataType
          }
        }
      }
    }
  }
}
""".strip()

ITEMS_QUERY = """
query AutodocProjectV2Items(
  $login: String!
  $number: Int!
  $first: Int!
  $after: String
) {
  user(login: $login) {
    projectV2(number: $number) {
      id
      number
      title
      url
      closed
      items(first: $first, after: $after) {
        totalCount
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          type
          content {
            __typename
            ... on DraftIssue {
              id
              title
              body
            }
            ... on Issue {
              id
              number
              title
              body
              url
              state
              createdAt
              updatedAt
              closedAt
              repository { nameWithOwner }
              parent {
                id
                number
                title
                url
                repository { nameWithOwner }
              }
              subIssues(first: 100) {
                totalCount
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  number
                  title
                  url
                  repository { nameWithOwner }
                }
              }
            }
            ... on PullRequest {
              id
              number
              title
              body
              url
              state
              createdAt
              updatedAt
              closedAt
              repository { nameWithOwner }
            }
          }
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                optionId
                field { ... on ProjectV2FieldCommon { id name dataType } }
              }
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { id name dataType } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { id name dataType } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { id name dataType } }
              }
            }
          }
        }
      }
    }
  }
}
""".strip()


@dataclass(frozen=True, slots=True)
class GitHubProjectV2QueryConfig:
    config_path: str
    token_env: str
    graphql_url: str
    owner: str
    project_number: int
    project_id: str
    project_url: str
    view_number_hint: int
    source_mode: str
    output_dir: str
    page_size: int
    max_items: int
    max_pages: int
    query_only: bool
    graphql_mutation_allowed: bool
    remote_mutation_allowed: bool
    allow_sql_write: bool
    allow_qdrant_write: bool


@dataclass(frozen=True, slots=True)
class GitHubProjectV2QueryCommand:
    execute: bool = False
    policy_decision_id: str = ""
    fixture_mode: bool = False


@dataclass(frozen=True, slots=True)
class GitHubProjectV2QueryPlan:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    fixture_mode: bool
    token_env: str
    graphql_url: str
    owner: str
    project_number: int
    project_id: str
    project_url: str
    view_number_hint: int
    output_dir: str
    page_size: int
    max_items: int
    max_pages: int
    fields_query_sha256: str
    items_query_sha256: str
    boundaries: Mapping[str, bool]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "kind": "plan",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "fixture_mode": self.fixture_mode,
            "token_env": self.token_env,
            "graphql_url": self.graphql_url,
            "owner": self.owner,
            "project_number": self.project_number,
            "project_id": self.project_id,
            "project_url": self.project_url,
            "view_number_hint": self.view_number_hint,
            "output_dir": self.output_dir,
            "page_size": self.page_size,
            "max_items": self.max_items,
            "max_pages": self.max_pages,
            "query_sha256": {
                "fields": self.fields_query_sha256,
                "items": self.items_query_sha256,
            },
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class GitHubProjectV2QueryResult:
    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    fixture_mode: bool
    token_env: str
    token_present: bool
    owner: str
    project_number: int
    project_id: str
    project_title: str
    project_url: str
    view_number_hint: int
    snapshot_ref: str
    snapshot_path: str
    field_count: int
    item_count: int
    fields_page_count: int
    items_page_count: int
    external_call_performed: bool
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": REPORT_SCHEMA,
            "kind": "result",
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "fixture_mode": self.fixture_mode,
            "token_env": self.token_env,
            "token_present": self.token_present,
            "project": {
                "owner": self.owner,
                "number": self.project_number,
                "id": self.project_id,
                "title": self.project_title,
                "url": self.project_url,
                "view_number_hint": self.view_number_hint,
            },
            "snapshot_ref": self.snapshot_ref,
            "snapshot_path": self.snapshot_path,
            "counts": {
                "field_count": self.field_count,
                "item_count": self.item_count,
                "fields_page_count": self.fields_page_count,
                "items_page_count": self.items_page_count,
            },
            "external_call_performed": self.external_call_performed,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"github_project_v2_query_only_snapshot_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"owner={self.owner or '-'}",
                f"project={self.project_number}",
                f"project_id={self.project_id or '-'}",
                f"fields={self.field_count}",
                f"items={self.item_count}",
                f"snapshot_ref={self.snapshot_ref or '-'}",
                f"external_call_performed={self.external_call_performed}",
                "graphql_mutation_allowed=False",
                "remote_mutation_allowed=False",
            )
        )


def build_github_project_v2_query_plan(
    config: GitHubProjectV2QueryConfig,
    command: GitHubProjectV2QueryCommand,
) -> GitHubProjectV2QueryPlan:
    issues = validate_github_project_v2_query_config(config)
    if command.execute and not command.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")
    for name, document in (("fields", FIELDS_QUERY), ("items", ITEMS_QUERY)):
        query_issue = validate_query_only_document(document)
        if query_issue:
            issues.append(f"{name} query rejected: {query_issue}")
    return GitHubProjectV2QueryPlan(
        valid=not issues,
        issues=tuple(issues),
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        fixture_mode=command.fixture_mode,
        token_env=config.token_env,
        graphql_url=config.graphql_url,
        owner=config.owner,
        project_number=config.project_number,
        project_id=config.project_id,
        project_url=config.project_url,
        view_number_hint=config.view_number_hint,
        output_dir=config.output_dir,
        page_size=config.page_size,
        max_items=config.max_items,
        max_pages=config.max_pages,
        fields_query_sha256=_sha256_text(FIELDS_QUERY),
        items_query_sha256=_sha256_text(ITEMS_QUERY),
        boundaries=_boundaries(command.execute, command.fixture_mode),
    )


def validate_github_project_v2_query_config(
    config: GitHubProjectV2QueryConfig,
) -> list[str]:
    issues: list[str] = []
    if not config.token_env or _looks_like_secret(config.token_env):
        issues.append("token_env must name an environment variable")
    split = urlsplit(config.graphql_url)
    if split.scheme != "https" or split.path.rstrip("/") != "/graphql":
        issues.append("graphql_url must be an HTTPS /graphql endpoint")
    if not config.owner.strip():
        issues.append("project owner is required")
    if config.project_number <= 0:
        issues.append("project number must be positive")
    if not config.project_id.startswith("PVT_"):
        issues.append("project_id must be a ProjectV2 node id")
    expected_path = f"/users/{config.owner}/projects/{config.project_number}"
    if expected_path not in urlsplit(config.project_url).path:
        issues.append("project_url does not match owner/project number")
    if config.view_number_hint <= 0:
        issues.append("view_number_hint must be positive")
    if config.source_mode != _SOURCE_MODE:
        issues.append(f"source_mode must be {_SOURCE_MODE}")
    if config.page_size <= 0 or config.page_size > 100:
        issues.append("page_size must be in 1..100")
    if config.max_items <= 0:
        issues.append("max_items must be positive")
    if config.max_pages <= 0:
        issues.append("max_pages must be positive")
    if not config.output_dir.strip():
        issues.append("output_dir is required")
    if not config.query_only:
        issues.append("query_only must remain enabled")
    if config.graphql_mutation_allowed:
        issues.append("GraphQL mutation must remain disabled")
    if config.remote_mutation_allowed:
        issues.append("remote mutation must remain disabled")
    if config.allow_sql_write:
        issues.append("Project snapshot must not write SQL")
    if config.allow_qdrant_write:
        issues.append("Project snapshot must not write Qdrant")
    return issues


def validate_query_only_document(document: str) -> str:
    stripped = re.sub(r"(?m)#.*$", "", document).strip()
    if not stripped:
        return "query document is empty"
    lowered = stripped.lower()
    if re.search(r"\bmutation\b", lowered):
        return "mutation operation is forbidden"
    if not re.match(r"^query\b", lowered):
        return "document must start with a query operation"
    return ""


def build_project_v2_snapshot_payload(
    plan: GitHubProjectV2QueryPlan,
    *,
    project: Mapping[str, Any],
    fields: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    normalized_project = {
        "owner": plan.owner,
        "number": int(project.get("number", plan.project_number)),
        "id": str(project.get("id", "")),
        "title": str(project.get("title", "")),
        "url": str(project.get("url", "")),
        "closed": bool(project.get("closed", False)),
        "view_number_hint": plan.view_number_hint,
    }
    payload: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "kind": "github_project_v2_query_only_snapshot",
        "project": normalized_project,
        "fields": [_json_safe_mapping(item) for item in fields],
        "items": [_json_safe_mapping(item) for item in items],
        "counts": {
            "field_count": len(fields),
            "item_count": len(items),
        },
        "boundaries": {
            "query_only": True,
            "graphql_mutation_allowed": False,
            "remote_mutation_allowed": False,
            "token_value_serialized": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
            "github_is_workflow_surface": True,
            "local_authority_preserved": True,
        },
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    payload["snapshot_ref"] = f"github-project-v2-snapshot:{digest}"
    return payload


def close_github_project_v2_query_result(
    plan: GitHubProjectV2QueryPlan,
    *,
    snapshot: Mapping[str, Any] | None,
    snapshot_path: str,
    token_present: bool,
    external_call_performed: bool,
    fields_page_count: int,
    items_page_count: int,
    errors: Sequence[str] = (),
) -> GitHubProjectV2QueryResult:
    issues = list(plan.issues)
    issues.extend(str(item) for item in errors if str(item))
    snapshot_payload = dict(snapshot or {})
    project = snapshot_payload.get("project")
    project_map = project if isinstance(project, Mapping) else {}
    counts = snapshot_payload.get("counts")
    count_map = counts if isinstance(counts, Mapping) else {}
    if plan.execute:
        if not snapshot_payload:
            issues.append("execute mode must produce a snapshot")
        if plan.fixture_mode and external_call_performed:
            issues.append("fixture mode must not perform an external call")
        if not plan.fixture_mode and not external_call_performed:
            issues.append("live mode must perform a GraphQL read call")
        if not plan.fixture_mode and not token_present:
            issues.append("live mode requires the configured token environment variable")
        if str(project_map.get("id", "")) != plan.project_id:
            issues.append("snapshot project id mismatch")
        if int(project_map.get("number", 0) or 0) != plan.project_number:
            issues.append("snapshot project number mismatch")
        if str(project_map.get("url", "")) != plan.project_url:
            issues.append("snapshot project URL mismatch")
        item_count = int(count_map.get("item_count", 0) or 0)
        if item_count > plan.max_items:
            issues.append("snapshot item count exceeds configured maximum")
        if fields_page_count <= 0 or items_page_count <= 0:
            issues.append("execute mode must report fields and items pages")
    elif snapshot_payload:
        issues.append("plan-only mode must not contain a snapshot")
    return GitHubProjectV2QueryResult(
        valid=not issues,
        issues=tuple(issues),
        execute=plan.execute,
        policy_decision_id=plan.policy_decision_id,
        fixture_mode=plan.fixture_mode,
        token_env=plan.token_env,
        token_present=token_present,
        owner=plan.owner,
        project_number=plan.project_number,
        project_id=str(project_map.get("id", plan.project_id)),
        project_title=str(project_map.get("title", "")),
        project_url=str(project_map.get("url", plan.project_url)),
        view_number_hint=plan.view_number_hint,
        snapshot_ref=str(snapshot_payload.get("snapshot_ref", "")),
        snapshot_path=snapshot_path,
        field_count=int(count_map.get("field_count", 0) or 0),
        item_count=int(count_map.get("item_count", 0) or 0),
        fields_page_count=fields_page_count,
        items_page_count=items_page_count,
        external_call_performed=external_call_performed,
        boundaries=_boundaries(plan.execute, plan.fixture_mode),
    )


def _boundaries(execute: bool, fixture_mode: bool) -> dict[str, bool]:
    return {
        "scan_once": True,
        "plan_only": not execute,
        "fixture_mode": fixture_mode,
        "project_v2_query_only": True,
        "direct_issue_rest_scan": False,
        "graphql_mutation_allowed": False,
        "remote_mutation_allowed": False,
        "workflow_dispatch_allowed": False,
        "token_value_serialized": False,
        "sql_write_allowed": False,
        "qdrant_write_allowed": False,
        "scheduler_modified": False,
        "polling_loop_added": False,
        "github_actions_artifact_path_secondary": True,
    }


def _json_safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    safe = _json_safe(value)
    return safe if isinstance(safe, dict) else {}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _looks_like_secret(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")):
        return True
    return len(stripped) >= 40 and stripped.upper() != stripped and "_" not in stripped
