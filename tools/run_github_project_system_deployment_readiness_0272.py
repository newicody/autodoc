#!/usr/bin/env python3
"""Test an existing GitHub ProjectV2/Actions deployment without installing it."""
from __future__ import annotations

import argparse
import base64
import configparser
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence
from urllib.parse import quote
from urllib.request import Request, urlopen

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_push_frame_config import load_github_artifact_scan_config  # noqa: E402
from context.github_project_system_deployment_readiness_0272 import (  # noqa: E402
    PROJECT_QUERY,
    GitHubProjectSystemReadinessCommand,
    GitHubProjectSystemReadinessConfig,
    analyze_workflow,
    build_plan,
    close_result,
    sha256_bytes,
)
from context.github_project_v2_query_only_snapshot_0272 import validate_query_only_document  # noqa: E402

_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")
_DEFAULT_OUTPUT = Path(".var/reports/github_project_system_deployment_readiness_0272.json")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = _load_config(args.config)
    local_paths = {
        "config": args.config,
        "workflow_template": _repo_path(config.workflow_template_path),
        "builder_template": _repo_path(config.builder_template_path),
        "snapshot_tool": _repo_path(config.snapshot_tool_path),
        "change_detection_tool": _repo_path(config.change_detection_tool_path),
        "snapshot_dir_parent": _repo_path(config.snapshot_dir).parent,
        "report_dir_parent": _repo_path(config.report_dir).parent,
    }
    local_checks = {name: _local_check(name, path) for name, path in local_paths.items()}
    workflow_text = _read_text(local_paths["workflow_template"])
    local_analysis = analyze_workflow(workflow_text, expected_builder_path=config.builder_path)
    token_present = bool(os.environ.get(config.token_env, ""))
    command = GitHubProjectSystemReadinessCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        fixture_mode=args.fixture_json is not None,
    )
    plan = build_plan(
        config,
        command,
        local_checks=local_checks,
        local_workflow_analysis=local_analysis,
        token_present=token_present,
    )
    project_payload: Mapping[str, Any] | None = None
    workflow_payload: Mapping[str, Any] | None = None
    remote_analysis = None
    remote_builder_sha256 = ""
    external_call_performed = False
    errors: list[str] = []
    local_builder_sha256 = sha256_bytes(_read_bytes(local_paths["builder_template"]))
    if args.execute and plan.valid:
        try:
            if args.fixture_json is not None:
                fixture = _read_json(args.fixture_json)
                project_payload = _mapping(fixture.get("project"))
                workflow_payload = _mapping(fixture.get("workflow"))
                remote_workflow_text = str(fixture.get("workflow_content", ""))
                remote_builder = str(fixture.get("builder_content", "")).encode("utf-8")
            else:
                token = os.environ[config.token_env]
                external_call_performed = True
                project_payload = _query_project(config, token)
                workflow_payload = _get_json(
                    config.api_url,
                    token,
                    f"/repos/{config.workflow_repository}/actions/workflows/{quote(config.workflow_name, safe='')}",
                )
                remote_workflow_text = _get_repository_text(
                    config, token, config.workflow_path
                )
                remote_builder = _get_repository_bytes(config, token, config.builder_path)
            remote_analysis = analyze_workflow(
                remote_workflow_text, expected_builder_path=config.builder_path
            )
            remote_builder_sha256 = sha256_bytes(remote_builder)
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
    result = close_result(
        plan,
        project_payload=project_payload,
        workflow_payload=workflow_payload,
        remote_workflow_analysis=remote_analysis,
        local_builder_sha256=local_builder_sha256,
        remote_builder_sha256=remote_builder_sha256,
        external_call_performed=external_call_performed,
        errors=errors,
    )
    payload = result.to_json_dict()
    _write_json_atomic(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True) if args.format == "json" else result.to_summary())
    return 0 if result.valid else 2


def _load_config(path: Path) -> GitHubProjectSystemReadinessConfig:
    base = load_github_artifact_scan_config(path)
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path, encoding="utf-8"):
        raise ValueError(f"config not found: {path}")
    project = parser["project"]
    snapshot = parser["project_snapshot"]
    safety = parser["safety"]
    readiness = parser["deployment_readiness"]
    return GitHubProjectSystemReadinessConfig(
        config_path=str(path),
        token_env=base.token_env,
        api_url=base.api_url.rstrip("/"),
        graphql_url=snapshot.get("graphql_url", base.api_url.rstrip("/") + "/graphql"),
        project_owner=base.project_owner,
        project_number=base.project_number,
        project_id=project.get("id", "").strip(),
        project_url=base.project_url,
        workflow_repository=readiness.get("workflow_repository", base.external_repository).strip(),
        workflow_name=readiness.get("workflow_name", base.workflow_name).strip(),
        workflow_path=readiness.get("workflow_path", ".github/workflows/autodoc-ticket-artifact.yml").strip(),
        workflow_template_path=readiness.get("workflow_template_path", "templates/github/autodoc-ticket-artifact.yml").strip(),
        builder_path=readiness.get("builder_path", "scripts/build_autodoc_ticket_artifact.py").strip(),
        builder_template_path=readiness.get("builder_template_path", "templates/github/scripts/build_autodoc_ticket_artifact.py").strip(),
        snapshot_tool_path=readiness.get("snapshot_tool_path", "tools/run_github_project_v2_query_only_snapshot_0272.py").strip(),
        change_detection_tool_path=readiness.get("change_detection_tool_path", "tools/detect_github_project_v2_snapshot_changes_0272.py").strip(),
        snapshot_dir=snapshot.get("output_dir", ".var/github/project_v2/snapshots").strip(),
        report_dir=readiness.get("report_dir", ".var/reports").strip(),
        require_actions_deployment=readiness.getboolean("require_actions_deployment", fallback=True),
        query_only=safety.getboolean("query_only", fallback=True),
        graphql_mutation_allowed=safety.getboolean("graphql_mutation_allowed", fallback=False),
        remote_mutation_allowed=safety.getboolean("allow_remote_mutation", fallback=False),
    )


def _query_project(config: GitHubProjectSystemReadinessConfig, token: str) -> Mapping[str, Any]:
    validate_query_only_document(PROJECT_QUERY)
    payload = _post_json(
        config.graphql_url,
        token,
        {"query": PROJECT_QUERY, "variables": {"login": config.project_owner, "number": config.project_number}},
    )
    errors = payload.get("errors")
    if errors:
        raise RuntimeError(f"GraphQL errors: {errors}")
    user = _mapping(_mapping(payload.get("data")).get("user"))
    project = _mapping(user.get("projectV2"))
    if not project:
        raise RuntimeError("ProjectV2 not found")
    return project


def _get_repository_text(config: GitHubProjectSystemReadinessConfig, token: str, path: str) -> str:
    return _get_repository_bytes(config, token, path).decode("utf-8")


def _get_repository_bytes(config: GitHubProjectSystemReadinessConfig, token: str, path: str) -> bytes:
    payload = _get_json(
        config.api_url,
        token,
        f"/repos/{config.workflow_repository}/contents/{quote(path, safe='/')}",
    )
    content = str(payload.get("content", "")).replace("\n", "")
    if not content:
        raise RuntimeError(f"repository content missing: {path}")
    return base64.b64decode(content, validate=True)


def _post_json(url: str, token: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    request = Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    return _request_json(request, token)


def _get_json(api_url: str, token: str, path: str) -> Mapping[str, Any]:
    return _request_json(Request(api_url.rstrip("/") + path, method="GET"), token)


def _request_json(request: Request, token: str) -> Mapping[str, Any]:
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=30) as response:  # noqa: S310 - configured GitHub HTTPS boundary
        payload = json.loads(response.read().decode("utf-8"))
    return _mapping(payload)


def _repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else _REPO_ROOT / path


def _local_check(name: str, path: Path) -> bool:
    if name.endswith("_parent"):
        current = path
        while not current.exists() and current != current.parent:
            current = current.parent
        return current.exists() and current.is_dir()
    return path.is_file()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.is_file() else b""


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _read_json(path: Path) -> Mapping[str, Any]:
    return _mapping(json.loads(path.read_text(encoding="utf-8")))


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
