#!/usr/bin/env python3
"""Dispatch controlled Actions runs for ProjectV2 transitions into En cours."""

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

from context.github_project_v2_en_cours_dispatch_0275_r8 import (  # noqa: E402
    GitHubProjectV2EnCoursDispatchCommand,
    GitHubProjectV2EnCoursDispatchConfig,
    apply_successful_dispatch,
    build_en_cours_dispatch_plan,
    empty_dispatch_state,
)


_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")


class GitHubWorkflowDispatchError(RuntimeError):
    """Typed IO-boundary failure for the GitHub workflow dispatch endpoint."""


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select idempotent ProjectV2 transitions into En cours and "
            "dispatch the controlled projects workflow."
        )
    )
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--change-set", type=Path, default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    loaded = _load_config(args.config)
    change_set_path = args.change_set or _latest_change_set(loaded["change_set_dir"])
    change_set = _read_json(change_set_path)
    state_path = loaded["state_path"]
    state = _read_json(state_path) if state_path.exists() else empty_dispatch_state()

    command = GitHubProjectV2EnCoursDispatchCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
    )
    plan = build_en_cours_dispatch_plan(
        loaded["config"],
        command,
        change_set=change_set,
        state=state,
    )

    errors: list[str] = []
    dispatched: list[str] = []
    external_call_performed = False
    current_state = dict(state)

    if args.execute and plan.valid:
        token = os.environ.get(loaded["token_env"], "")
        if not token:
            errors.append(
                f"missing token environment variable: {loaded['token_env']}"
            )
        else:
            for candidate in plan.candidates:
                try:
                    external_call_performed = True
                    _post_workflow_dispatch(
                        api_url=loaded["api_url"],
                        token=token,
                        repository=plan.repository,
                        workflow_name=plan.workflow_name,
                        ref=plan.ref,
                        inputs={
                            "issue_number": str(candidate.issue_number),
                            "requested_status": candidate.requested_status,
                            "request_mode": candidate.request_mode,
                            "parent_event_ref": candidate.parent_event_ref,
                        },
                    )
                    current_state = apply_successful_dispatch(
                        current_state,
                        candidate,
                    )
                    _write_json_atomic(state_path, current_state)
                    dispatched.append(candidate.decision_id)
                except (GitHubWorkflowDispatchError, OSError, ValueError) as exc:
                    errors.append(f"{type(exc).__name__}:{exc}")
                    break

    valid = plan.valid and not errors
    payload = {
        "schema": "missipy.github.project_v2_en_cours_dispatch_execution.v1",
        "valid": valid,
        "issues": [*plan.issues, *errors],
        "execute": args.execute,
        "policy_decision_id": args.policy_decision_id,
        "change_set_path": str(change_set_path),
        "plan": plan.to_json_dict(),
        "dispatched_decision_ids": dispatched,
        "external_call_performed": external_call_performed,
        "boundaries": {
            "project_mutation_allowed": False,
            "issue_mutation_allowed": False,
            "workflow_dispatch_performed": bool(dispatched),
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
            "token_value_serialized": False,
        },
    }
    _write_json_atomic(loaded["report_path"], payload)

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"github_project_v2_en_cours_dispatch_valid={valid}",
                    f"execute={args.execute}",
                    f"candidates={len(plan.candidates)}",
                    f"dispatched={len(dispatched)}",
                    f"skipped_processed={plan.skipped_already_processed}",
                    f"skipped_non_triggering={plan.skipped_non_triggering}",
                    f"external_call_performed={external_call_performed}",
                )
            )
        )
    return 0 if valid else 2


def _load_config(path: Path) -> dict[str, Any]:
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path, encoding="utf-8"):
        raise ValueError(f"config not found: {path}")
    section = parser["workflow_dispatch"]
    config = GitHubProjectV2EnCoursDispatchConfig(
        repository=section.get("repository", "").strip(),
        workflow_name=section.get("workflow_name", "").strip(),
        ref=section.get("ref", "").strip(),
        target_status=section.get("target_status", "En cours").strip(),
        max_dispatches=section.getint("max_dispatches", fallback=10),
        allow_workflow_dispatch=section.getboolean(
            "allow_workflow_dispatch",
            fallback=False,
        ),
        allow_remote_mutation=section.getboolean(
            "allow_remote_mutation",
            fallback=False,
        ),
    )
    return {
        "config": config,
        "token_env": section.get("token_env", "GITHUB_TOKEN").strip(),
        "api_url": section.get("api_url", "https://api.github.com").strip(),
        "change_set_dir": Path(
            section.get(
                "change_set_dir",
                ".var/github/project_v2/changes",
            ).strip()
        ),
        "state_path": Path(
            section.get(
                "state_path",
                ".var/github/project_v2/state/en_cours_dispatch_0275_r8.json",
            ).strip()
        ),
        "report_path": Path(
            section.get(
                "report_path",
                ".var/reports/github_project_v2_en_cours_dispatch_0275_r8.json",
            ).strip()
        ),
    }


def _latest_change_set(directory: Path) -> Path:
    if not directory.exists():
        raise ValueError(f"change-set directory not found: {directory}")
    candidates = [
        path
        for path in directory.glob("project-v2-change-set-*.json")
        if path.is_file()
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime_ns, path.name))
    if not candidates:
        raise ValueError(f"no ProjectV2 change set found in {directory}")
    return candidates[-1]


def _post_workflow_dispatch(
    *,
    api_url: str,
    token: str,
    repository: str,
    workflow_name: str,
    ref: str,
    inputs: Mapping[str, str],
) -> None:
    url = (
        f"{api_url.rstrip('/')}/repos/{repository}/actions/workflows/"
        f"{workflow_name}/dispatches"
    )
    body = json.dumps(
        {"ref": ref, "inputs": dict(inputs)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    request = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "autodoc-project-v2-en-cours-dispatch-0275-r8",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            status = int(getattr(response, "status", 0) or 0)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise GitHubWorkflowDispatchError(
            f"GitHub workflow dispatch HTTP {exc.code}: {detail}"
        ) from exc
    except URLError as exc:
        raise GitHubWorkflowDispatchError(
            f"GitHub workflow dispatch transport: {exc.reason}"
        ) from exc
    if status not in {200, 204}:
        raise GitHubWorkflowDispatchError(
            f"unexpected GitHub workflow dispatch status: {status}"
        )


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


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
