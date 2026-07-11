#!/usr/bin/env python3
"""Bind the existing 0168 GitHub Actions artifact fetch into a gated scan-once."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_actions_artifact_scan_once_live_0272 import (  # noqa: E402
    GitHubActionsArtifactScanCommand,
    GitHubActionsArtifactScanSnapshot,
    build_github_actions_artifact_scan_plan,
    close_github_actions_artifact_scan_result,
)
from context.github_artifact_server_fetch_config import (  # noqa: E402
    load_github_artifact_server_fetch_config,
)
from context.github_project_push_frame_config import (  # noqa: E402
    load_github_artifact_scan_config,
)

_DEFAULT_PROJECT_CONFIG = Path("config/github_project_push_frame.example.ini")
_DEFAULT_FETCH_CONFIG = Path("config/github_artifact_server_fetch.example.ini")
_DEFAULT_FETCH_TOOL = Path("tools/run_github_actions_artifact_fetch_once.py")
_DEFAULT_OUTPUT = Path(".var/reports/github_actions_artifact_scan_once_live_0272.json")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one bounded GET/download scan of GitHub Actions artifacts using "
            "the existing 0168 fetch and 0167 dataset sync surfaces."
        )
    )
    parser.add_argument(
        "--project-config",
        "--config",
        dest="project_config",
        type=Path,
        default=_DEFAULT_PROJECT_CONFIG,
    )
    parser.add_argument("--fetch-config", type=Path, default=_DEFAULT_FETCH_CONFIG)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--max-runs", type=int, default=10)
    parser.add_argument("--max-artifacts", type=int, default=20)
    parser.add_argument("--fixture-root", type=Path, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    project = load_github_artifact_scan_config(args.project_config)
    fetch = load_github_artifact_server_fetch_config(args.fetch_config)
    project_payload = project.to_json_dict()
    fetch_payload = fetch.to_json_dict()

    snapshot = _build_snapshot(project, fetch, project_payload, fetch_payload)
    command = GitHubActionsArtifactScanCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        max_runs=args.max_runs,
        max_artifacts=args.max_artifacts,
        fixture_mode=args.fixture_root is not None,
        force=args.force,
    )
    plan = build_github_actions_artifact_scan_plan(snapshot, command)

    child_returncode: int | None = None
    child_report: Mapping[str, Any] | None = None
    token_present = False
    if args.execute and plan.valid:
        token_present = bool(os.environ.get(plan.token_env, ""))
        if args.fixture_root is None and not token_present:
            child_returncode = 2
            child_report = {
                "status": "blocked",
                "errors": [{"error": f"missing token environment variable: {plan.token_env}"}],
                "counts": {"error_count": 1},
                "external_call_performed": False,
            }
        else:
            child_returncode, child_report = _run_existing_fetch_tool(
                args=args,
                plan=plan,
            )

    result = close_github_actions_artifact_scan_result(
        plan,
        child_returncode=child_returncode,
        child_report=child_report,
        token_present=token_present,
    )
    payload = result.to_json_dict()
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.to_summary())
    return 0 if result.valid else 2


def _build_snapshot(
    project: object,
    fetch: object,
    project_payload: Mapping[str, Any],
    fetch_payload: Mapping[str, Any],
) -> GitHubActionsArtifactScanSnapshot:
    project_safety = _mapping(project_payload.get("safety"))
    fetch_safety = _mapping(fetch_payload.get("safety"))
    dataset = getattr(fetch, "dataset")
    return GitHubActionsArtifactScanSnapshot(
        project_config_path=str(getattr(project, "config_path")),
        fetch_config_path=str(getattr(fetch, "config_path")),
        repository=str(getattr(project, "external_repository")),
        fetch_repository=str(getattr(fetch, "external_repository")),
        development_repository=str(getattr(project, "development_repository")),
        fetch_development_repository=str(
            getattr(fetch, "development_repository")
        ),
        project_url=str(getattr(project, "project_url")),
        fetch_project_url=str(getattr(fetch, "project_url")),
        workflow_name=str(getattr(project, "workflow_name")),
        fetch_workflow_name=str(getattr(fetch, "workflow_name")),
        artifact_name_prefix=str(getattr(project, "artifact_name_prefix")),
        fetch_artifact_name_prefix=str(getattr(fetch, "artifact_name_prefix")),
        token_env=str(getattr(project, "token_env")),
        fetch_token_env=str(getattr(fetch, "token_env")),
        api_url=str(getattr(project, "api_url")),
        fetch_api_url=str(getattr(fetch, "api_url")),
        allowed_repositories=tuple(getattr(project, "allowed_repositories")),
        fetch_allowed_repositories=tuple(getattr(fetch, "allowed_repositories")),
        scan_command=str(getattr(project, "scan_command")),
        history_mode=str(getattr(project, "history_mode")),
        dataset_root=str(getattr(dataset, "root")),
        dataset_state_path=str(getattr(dataset, "state_path")),
        read_only_scan=bool(project_safety.get("read_only_scan", True)),
        read_only_fetch=bool(fetch_safety.get("read_only_fetch", True)),
        allow_workflow_dispatch=bool(project_safety.get("allow_workflow_dispatch", False)),
        allow_remote_mutation=bool(
            project_safety.get("allow_remote_mutation", False)
            or fetch_safety.get("allow_remote_mutation", False)
        ),
        allow_sql_write=bool(
            project_safety.get("allow_sql_write", False)
            or fetch_safety.get("allow_sql_write", False)
        ),
        allow_qdrant_write=bool(
            project_safety.get("allow_qdrant_write", False)
            or fetch_safety.get("allow_qdrant_write", False)
        ),
    )


def _run_existing_fetch_tool(
    *,
    args: argparse.Namespace,
    plan: object,
) -> tuple[int, Mapping[str, Any]]:
    fetch_tool = _REPO_ROOT / str(getattr(plan, "fetch_tool"))
    command = [
        sys.executable,
        str(fetch_tool),
        "--config",
        str(args.fetch_config),
        "--repository",
        str(getattr(plan, "repository")),
        "--workflow-name",
        str(getattr(plan, "workflow_name")),
        "--artifact-name-prefix",
        str(getattr(plan, "artifact_name_prefix")),
        "--max-runs",
        str(getattr(plan, "max_runs")),
        "--max-artifacts",
        str(getattr(plan, "max_artifacts")),
        "--format",
        "json",
    ]
    if args.fixture_root is not None:
        command.extend(("--fixture-root", str(args.fixture_root)))
    if args.force:
        command.append("--force")
    completed = subprocess.run(
        command,
        cwd=_REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {
            "status": "invalid_json",
            "errors": [
                {
                    "error": "fetch tool did not emit JSON",
                    "stderr": completed.stderr[-2000:],
                }
            ],
            "counts": {"error_count": 1},
            "external_call_performed": args.fixture_root is None,
        }
    return completed.returncode, payload if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
