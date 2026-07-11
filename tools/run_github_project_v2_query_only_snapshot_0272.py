#!/usr/bin/env python3
"""Read one GitHub user ProjectV2 through GraphQL queries and write a local snapshot."""

from __future__ import annotations

import argparse
import configparser
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_push_frame_config import (  # noqa: E402
    load_github_artifact_scan_config,
)
from context.github_project_v2_query_only_snapshot_0272 import (  # noqa: E402
    FIELDS_QUERY,
    ITEMS_QUERY,
    GitHubProjectV2QueryCommand,
    GitHubProjectV2QueryConfig,
    build_github_project_v2_query_plan,
    build_project_v2_snapshot_payload,
    close_github_project_v2_query_result,
)

_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")
_DEFAULT_REPORT = Path(".var/reports/github_project_v2_query_only_snapshot_0272.json")


class GitHubProjectV2QueryError(RuntimeError):
    """Typed operator-facing failure at the GraphQL IO boundary."""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one immutable local snapshot from a user ProjectV2 using GraphQL query operations only."
    )
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=_DEFAULT_REPORT)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = _load_config(args.config)
    command = GitHubProjectV2QueryCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        fixture_mode=args.fixture_json is not None,
    )
    plan = build_github_project_v2_query_plan(config, command)
    token_present = False
    external_call_performed = False
    fields_page_count = 0
    items_page_count = 0
    snapshot: Mapping[str, Any] | None = None
    snapshot_path = ""
    errors: list[str] = []

    if args.execute and plan.valid:
        try:
            if args.fixture_json is not None:
                project, fields, items, fields_page_count, items_page_count = _read_fixture(
                    args.fixture_json,
                    plan.max_items,
                )
            else:
                token = os.environ.get(plan.token_env, "")
                token_present = bool(token)
                if not token_present:
                    raise GitHubProjectV2QueryError(
                        f"missing token environment variable: {plan.token_env}"
                    )
                external_call_performed = True
                project, fields, items, fields_page_count, items_page_count = _read_live(
                    plan=plan,
                    token=token,
                )
            snapshot = build_project_v2_snapshot_payload(
                plan,
                project=project,
                fields=fields,
                items=items,
            )
            snapshot_path = str(_write_immutable_snapshot(Path(plan.output_dir), snapshot))
        except (GitHubProjectV2QueryError, OSError, ValueError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")

    result = close_github_project_v2_query_result(
        plan,
        snapshot=snapshot,
        snapshot_path=snapshot_path,
        token_present=token_present,
        external_call_performed=external_call_performed,
        fields_page_count=fields_page_count,
        items_page_count=items_page_count,
        errors=errors,
    )
    payload = result.to_json_dict()
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.to_summary())
    return 0 if result.valid else 2


def _load_config(path: Path) -> GitHubProjectV2QueryConfig:
    base = load_github_artifact_scan_config(path)
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path, encoding="utf-8"):
        raise ValueError(f"config not found: {path}")
    project = parser["project"]
    snapshot = parser["project_snapshot"]
    safety = parser["safety"]
    graphql_url = snapshot.get(
        "graphql_url",
        str(base.api_url).rstrip("/") + "/graphql",
    ).strip()
    return GitHubProjectV2QueryConfig(
        config_path=str(path),
        token_env=base.token_env,
        graphql_url=graphql_url,
        owner=base.project_owner,
        project_number=base.project_number,
        project_id=project.get("id", "").strip(),
        project_url=base.project_url,
        view_number_hint=project.getint("view_number_hint", fallback=2),
        source_mode=project.get("source_mode", "").strip(),
        output_dir=snapshot.get("output_dir", ".var/github/project_v2/snapshots").strip(),
        page_size=snapshot.getint("page_size", fallback=50),
        max_items=snapshot.getint("max_items", fallback=500),
        max_pages=snapshot.getint("max_pages", fallback=20),
        query_only=safety.getboolean("query_only", fallback=True),
        graphql_mutation_allowed=safety.getboolean(
            "graphql_mutation_allowed", fallback=False
        ),
        remote_mutation_allowed=safety.getboolean(
            "allow_remote_mutation", fallback=False
        ),
        allow_sql_write=safety.getboolean("allow_sql_write", fallback=False),
        allow_qdrant_write=safety.getboolean("allow_qdrant_write", fallback=False),
    )


def _read_live(
    *,
    plan: object,
    token: str,
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], list[Mapping[str, Any]], int, int]:
    project: Mapping[str, Any] | None = None
    fields: list[Mapping[str, Any]] = []
    items: list[Mapping[str, Any]] = []
    fields_cursor: str | None = None
    items_cursor: str | None = None
    fields_pages = 0
    items_pages = 0

    for _ in range(int(getattr(plan, "max_pages"))):
        payload = _graphql_request(
            url=str(getattr(plan, "graphql_url")),
            token=token,
            query=FIELDS_QUERY,
            variables={
                "login": str(getattr(plan, "owner")),
                "number": int(getattr(plan, "project_number")),
                "first": int(getattr(plan, "page_size")),
                "after": fields_cursor,
            },
        )
        current = _extract_project(payload)
        project = project or _project_metadata(current)
        connection = _mapping(current.get("fields"))
        fields.extend(_mapping_list(connection.get("nodes")))
        fields_pages += 1
        page = _mapping(connection.get("pageInfo"))
        if not bool(page.get("hasNextPage", False)):
            break
        fields_cursor = str(page.get("endCursor") or "") or None
        if fields_cursor is None:
            raise GitHubProjectV2QueryError("fields pagination cursor missing")
    else:
        raise GitHubProjectV2QueryError("fields pagination exceeded max_pages")

    total_count: int | None = None
    for _ in range(int(getattr(plan, "max_pages"))):
        payload = _graphql_request(
            url=str(getattr(plan, "graphql_url")),
            token=token,
            query=ITEMS_QUERY,
            variables={
                "login": str(getattr(plan, "owner")),
                "number": int(getattr(plan, "project_number")),
                "first": int(getattr(plan, "page_size")),
                "after": items_cursor,
            },
        )
        current = _extract_project(payload)
        project = project or _project_metadata(current)
        connection = _mapping(current.get("items"))
        if total_count is None:
            total_count = int(connection.get("totalCount", 0) or 0)
            if total_count > int(getattr(plan, "max_items")):
                raise GitHubProjectV2QueryError(
                    f"project contains {total_count} items; max_items is {getattr(plan, 'max_items')}"
                )
        items.extend(_mapping_list(connection.get("nodes")))
        items_pages += 1
        page = _mapping(connection.get("pageInfo"))
        if not bool(page.get("hasNextPage", False)):
            break
        items_cursor = str(page.get("endCursor") or "") or None
        if items_cursor is None:
            raise GitHubProjectV2QueryError("items pagination cursor missing")
    else:
        raise GitHubProjectV2QueryError("items pagination exceeded max_pages")

    if project is None:
        raise GitHubProjectV2QueryError("ProjectV2 metadata missing")
    return project, fields, items, fields_pages, items_pages


def _graphql_request(
    *,
    url: str,
    token: str,
    query: str,
    variables: Mapping[str, Any],
) -> Mapping[str, Any]:
    body = json.dumps({"query": query, "variables": dict(variables)}).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "autodoc-project-v2-query-only-0272",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310 - validated HTTPS GraphQL URL
            payload = json.load(response)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise GitHubProjectV2QueryError(
            f"GitHub GraphQL HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise GitHubProjectV2QueryError(f"GitHub GraphQL transport: {exc.reason}") from exc
    if not isinstance(payload, Mapping):
        raise GitHubProjectV2QueryError("GitHub GraphQL response is not an object")
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        messages = [str(_mapping(item).get("message", "GraphQL error")) for item in errors]
        raise GitHubProjectV2QueryError("; ".join(messages))
    return payload


def _extract_project(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    data = _mapping(payload.get("data"))
    user = _mapping(data.get("user"))
    project = _mapping(user.get("projectV2"))
    if not project:
        raise GitHubProjectV2QueryError("user ProjectV2 not found or not readable")
    return project


def _project_metadata(project: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(project.get("id", "")),
        "number": int(project.get("number", 0) or 0),
        "title": str(project.get("title", "")),
        "url": str(project.get("url", "")),
        "closed": bool(project.get("closed", False)),
    }


def _read_fixture(
    path: Path,
    max_items: int,
) -> tuple[Mapping[str, Any], list[Mapping[str, Any]], list[Mapping[str, Any]], int, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("fixture must be an object")
    project = _mapping(payload.get("project"))
    fields = _mapping_list(payload.get("fields"))
    items = _mapping_list(payload.get("items"))
    if len(items) > max_items:
        raise ValueError("fixture exceeds max_items")
    return project, fields, items, 1, 1


def _write_immutable_snapshot(output_dir: Path, payload: Mapping[str, Any]) -> Path:
    snapshot_ref = str(payload.get("snapshot_ref", ""))
    digest = snapshot_ref.rsplit(":", 1)[-1]
    if not digest:
        raise ValueError("snapshot_ref missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"project-v2-{digest}.json"
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"immutable snapshot collision: {path}")
        return path
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    return path


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
