#!/usr/bin/env python3
"""Run one bounded ProjectV2 snapshot, diff and En cours dispatch pass."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")
_DEFAULT_REPORT = Path(
    ".var/reports/github_project_v2_en_cours_dispatch_once_0275_r8.json"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compose the existing 0272 query-only snapshot and local diff "
            "with the governed 0275-r8 workflow dispatcher."
        )
    )
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--output", type=Path, default=_DEFAULT_REPORT)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    issues: list[str] = []
    steps: list[dict[str, Any]] = []

    if args.execute and not args.policy_decision_id.strip():
        issues.append("policy_decision_id is required for execute mode")

    commands = _commands(args)
    if args.execute and not issues:
        for name, command in commands:
            completed = subprocess.run(
                command,
                cwd=_REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            steps.append(
                {
                    "name": name,
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-4000:],
                    "stderr": completed.stderr[-4000:],
                }
            )
            if completed.returncode != 0:
                issues.append(f"{name} failed with {completed.returncode}")
                break

    payload: Mapping[str, Any] = {
        "schema": "missipy.github.project_v2_en_cours_dispatch_once.v1",
        "valid": not issues,
        "execute": args.execute,
        "policy_decision_id": args.policy_decision_id,
        "issues": issues,
        "steps": steps,
        "planned_commands": [
            {"name": name, "command": command}
            for name, command in commands
        ],
        "boundaries": {
            "bounded_single_pass": True,
            "loop_added": False,
            "daemon_added": False,
            "openrc_service_added": False,
            "scheduler_modified": False,
            "scheduler_run_modified": False,
            "project_mutation_allowed": False,
            "issue_mutation_allowed": False,
            "workflow_dispatch_is_only_remote_mutation": True,
        },
    }
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"github_project_v2_en_cours_dispatch_once_valid={not issues}",
                    f"execute={args.execute}",
                    f"steps={len(steps)}",
                    f"issues={len(issues)}",
                    "bounded_single_pass=True",
                )
            )
        )
    return 0 if not issues else 2


def _commands(args: argparse.Namespace) -> list[tuple[str, list[str]]]:
    python = sys.executable
    policy = args.policy_decision_id
    return [
        (
            "project_v2_query_only_snapshot_0272",
            [
                python,
                "tools/run_github_project_v2_query_only_snapshot_0272.py",
                "--config",
                str(args.config),
                "--execute",
                "--policy-decision-id",
                f"{policy}:snapshot",
            ],
        ),
        (
            "project_v2_snapshot_change_detection_0272",
            [
                python,
                "tools/detect_github_project_v2_snapshot_changes_0272.py",
                "--execute",
                "--policy-decision-id",
                f"{policy}:diff",
            ],
        ),
        (
            "project_v2_en_cours_dispatch_0275_r8",
            [
                python,
                "tools/dispatch_github_project_v2_en_cours_transitions_0275_r8.py",
                "--config",
                str(args.config),
                "--execute",
                "--policy-decision-id",
                f"{policy}:dispatch",
            ],
        ),
    ]


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
