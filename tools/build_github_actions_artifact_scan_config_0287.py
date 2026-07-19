#!/usr/bin/env python3
"""Build a dedicated GitHub Actions artifact-scan configuration.

The ProjectV2 query-only snapshot configuration and the GitHub Actions
artifact-scan configuration are different operational surfaces.  This tool
reads the existing ProjectV2 and server-fetch INI files, keeps their common
GitHub/project/artifact identity aligned, replaces only the scan surface with
the accepted one-shot Actions scanner, validates the resulting configuration
through the existing 0165/0272 contracts and optionally writes it atomically.

It never reads a token value and performs no GitHub, SQL, Qdrant, Scheduler or
laboratory operation.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_actions_artifact_scan_once_live_0272 import (  # noqa: E402
    GitHubActionsArtifactScanCommand,
    GitHubActionsArtifactScanSnapshot,
    build_github_actions_artifact_scan_plan,
)
from context.github_artifact_server_fetch_config import (  # noqa: E402
    GitHubArtifactServerFetchConfig,
    load_github_artifact_server_fetch_config,
)
from context.github_project_push_frame_config import (  # noqa: E402
    GithubArtifactScanConfig,
    build_github_artifact_scan_config,
    load_github_artifact_scan_config,
)

SCHEMA = "missipy.github_actions.artifact_scan_config_builder.v1"
_CANONICAL_SCAN_COMMAND = (
    "tools/run_github_actions_artifact_scan_once_live_0272.py"
)
_DEFAULT_OUTPUT = Path(".var/config/github_actions_artifact_scan.ini")


class GitHubActionsArtifactScanConfigBuildError(RuntimeError):
    """Raised when source configs cannot form one aligned scan surface."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-config", type=Path, required=True)
    parser.add_argument("--fetch-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument(
        "--working-directory",
        type=Path,
        default=_REPO_ROOT,
    )
    parser.add_argument(
        "--python-executable",
        default=sys.executable,
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--format",
        choices=("json", "summary", "ini"),
        default="summary",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    try:
        payload = build_artifact_scan_config_report(
            project_config=_absolute_input(args.project_config),
            fetch_config=_absolute_input(args.fetch_config),
            output=_absolute_output(args.output),
            working_directory=_absolute_working_directory(
                args.working_directory
            ),
            python_executable=str(args.python_executable),
            execute=bool(args.execute),
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": SCHEMA,
            "valid": False,
            "mode": "execute" if args.execute else "plan",
            "status": "failed",
            "issues": [f"{type(exc).__name__}: {exc}"],
            "output": str(_absolute_output(args.output)),
            "boundaries": _boundaries(written=False),
        }

    _emit(payload, args.format)
    return 0 if payload.get("valid") is True else 2


def build_artifact_scan_config_report(
    *,
    project_config: Path,
    fetch_config: Path,
    output: Path,
    working_directory: Path,
    python_executable: str,
    execute: bool,
) -> dict[str, Any]:
    project = load_github_artifact_scan_config(project_config)
    fetch = load_github_artifact_server_fetch_config(fetch_config)
    issues = _alignment_issues(project, fetch)

    payload_mapping = _generated_mapping(
        project=project,
        fetch=fetch,
        working_directory=working_directory,
        python_executable=python_executable,
    )
    generated = build_github_artifact_scan_config(
        output,
        payload_mapping,
    )
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(generated, fetch),
        GitHubActionsArtifactScanCommand(execute=False),
    )
    issues.extend(plan.issues)

    rendered = _render_ini(payload_mapping)
    valid = not issues
    written = False
    status = "plan-complete" if valid else "blocked"

    if execute and valid:
        _write_text_atomic(output, rendered)
        readback = load_github_artifact_scan_config(output)
        if readback.to_json_dict() != generated.to_json_dict():
            raise GitHubActionsArtifactScanConfigBuildError(
                "generated configuration readback mismatch"
            )
        written = True
        status = "written"

    return {
        "schema": SCHEMA,
        "valid": valid,
        "mode": "execute" if execute else "plan",
        "status": status,
        "issues": list(dict.fromkeys(issues)),
        "project_config": str(project_config),
        "fetch_config": str(fetch_config),
        "output": str(output),
        "scan_command": generated.scan_command,
        "repository": generated.external_repository,
        "workflow_name": generated.workflow_name,
        "artifact_name_prefix": generated.artifact_name_prefix,
        "token_env": generated.token_env,
        "api_url": generated.api_url,
        "project_url": generated.project_url,
        "working_directory": str(generated.working_directory),
        "python_executable": generated.python_executable,
        "content": rendered,
        "boundaries": _boundaries(written=written),
    }


def _alignment_issues(
    project: GithubArtifactScanConfig,
    fetch: GitHubArtifactServerFetchConfig,
) -> list[str]:
    pairs = (
        ("repository", project.external_repository, fetch.external_repository),
        (
            "development_repository",
            project.development_repository,
            fetch.development_repository,
        ),
        ("project_url", project.project_url, fetch.project_url),
        ("workflow_name", project.workflow_name, fetch.workflow_name),
        (
            "artifact_name_prefix",
            project.artifact_name_prefix,
            fetch.artifact_name_prefix,
        ),
        ("token_env", project.token_env, fetch.token_env),
        (
            "api_url",
            project.api_url.rstrip("/"),
            fetch.api_url.rstrip("/"),
        ),
    )
    issues = [
        f"{name} mismatch between project and fetch configs"
        for name, project_value, fetch_value in pairs
        if project_value != fetch_value
    ]
    if project.external_repository not in fetch.allowed_repositories:
        issues.append("repository missing from fetch allow-list")
    if project.external_repository not in project.allowed_repositories:
        issues.append("repository missing from project allow-list")
    return issues


def _generated_mapping(
    *,
    project: GithubArtifactScanConfig,
    fetch: GitHubArtifactServerFetchConfig,
    working_directory: Path,
    python_executable: str,
) -> dict[str, dict[str, object]]:
    normalized_python = python_executable.strip()
    if not normalized_python:
        raise GitHubActionsArtifactScanConfigBuildError(
            "python-executable must not be empty"
        )
    return {
        "github": {
            "token_env": fetch.token_env,
            "api_url": fetch.api_url,
        },
        "project": {
            "url": fetch.project_url,
            "owner": project.project_owner,
            "number": project.project_number,
        },
        "artifact_source": {
            "repositories": fetch.external_repository,
            "workflow_name": fetch.workflow_name,
            "artifact_name_prefix": fetch.artifact_name_prefix,
            "trigger_source": "github_action_on_ticket_event",
        },
        "scan": {
            "mode": "fcron",
            "interval_minutes": 10,
            "working_directory": str(working_directory),
            "python_executable": normalized_python,
            "scan_command": _CANONICAL_SCAN_COMMAND,
            "state_path": (
                ".var/github/actions_artifacts/state/index.json"
            ),
            "inbox_dir": ".var/github/actions_artifacts/inbox",
            "fcron_table_path": (
                ".var/fcron/autodoc-github-actions-artifact-scan.fcrontab"
            ),
        },
        "safety": {
            "development_repository": fetch.development_repository,
            "allowed_repositories": fetch.external_repository,
            "read_only_scan": "true",
            "query_only": "true",
            "graphql_mutation_allowed": "false",
            "allow_workflow_dispatch": "false",
            "allow_remote_mutation": "false",
            "allow_sql_write": "false",
            "allow_qdrant_write": "false",
        },
        "pipeline": {
            "context_option_names": ", ".join(
                project.context_option_names
            ),
            "copilot_preliminary_opinion": (
                "true"
                if project.copilot_preliminary_opinion
                else "false"
            ),
            "history_mode": "append_only",
        },
    }


def _snapshot(
    project: GithubArtifactScanConfig,
    fetch: GitHubArtifactServerFetchConfig,
) -> GitHubActionsArtifactScanSnapshot:
    return GitHubActionsArtifactScanSnapshot(
        project_config_path=str(project.config_path),
        fetch_config_path=str(fetch.config_path),
        repository=project.external_repository,
        fetch_repository=fetch.external_repository,
        development_repository=project.development_repository,
        fetch_development_repository=fetch.development_repository,
        project_url=project.project_url,
        fetch_project_url=fetch.project_url,
        workflow_name=project.workflow_name,
        fetch_workflow_name=fetch.workflow_name,
        artifact_name_prefix=project.artifact_name_prefix,
        fetch_artifact_name_prefix=fetch.artifact_name_prefix,
        token_env=project.token_env,
        fetch_token_env=fetch.token_env,
        api_url=project.api_url,
        fetch_api_url=fetch.api_url,
        allowed_repositories=project.allowed_repositories,
        fetch_allowed_repositories=fetch.allowed_repositories,
        scan_command=project.scan_command,
        history_mode=project.history_mode,
        dataset_root=str(fetch.dataset.root),
        dataset_state_path=str(fetch.dataset.state_path),
        read_only_scan=True,
        read_only_fetch=True,
        allow_workflow_dispatch=False,
        allow_remote_mutation=False,
        allow_sql_write=False,
        allow_qdrant_write=False,
    )


def _render_ini(
    payload: Mapping[str, Mapping[str, object]],
) -> str:
    lines: list[str] = [
        "# Dedicated GitHub Actions artifact scan configuration.",
        "# Generated locally; no token value is stored.",
        "",
    ]
    for section, values in payload.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            lines.append(f"{key} = {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _absolute_input(path: Path) -> Path:
    return path if path.is_absolute() else (_REPO_ROOT / path).resolve()


def _absolute_output(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _absolute_working_directory(path: Path) -> Path:
    return path if path.is_absolute() else (_REPO_ROOT / path).resolve()


def _boundaries(*, written: bool) -> dict[str, object]:
    return {
        "local_config_write_performed": written,
        "source_configs_modified": False,
        "token_value_read": False,
        "token_value_serialized": False,
        "github_api_called": False,
        "remote_mutation_performed": False,
        "sql_write_performed": False,
        "qdrant_write_performed": False,
        "scheduler_dispatch_started": False,
        "laboratory_execution_started": False,
        "canonical_scan_surface": _CANONICAL_SCAN_COMMAND,
    }


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    if output_format == "ini":
        print(str(payload.get("content", "")), end="")
        return
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"mode={payload.get('mode', '')}",
                f"status={payload.get('status', '')}",
                f"output={payload.get('output', '')}",
                f"scan_command={payload.get('scan_command', '')}",
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
