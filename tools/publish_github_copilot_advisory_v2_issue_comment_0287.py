#!/usr/bin/env python3
"""Preview or execute controlled publication of one Copilot v2 Issue comment."""

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

from context.github_copilot_advisory_v2_issue_publication_0287 import (  # noqa: E402
    CopilotAdvisoryV2IssuePublicationCommand,
    parse_issue_comment_snapshots,
    plan_copilot_advisory_v2_issue_publication,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument("--gh-command", default="gh")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    preview = _read_mapping(args.preview)
    comments = _fetch_comments(args.gh_command, args.repository, args.issue_number)
    plan = plan_copilot_advisory_v2_issue_publication(
        CopilotAdvisoryV2IssuePublicationCommand(
            repository=args.repository,
            issue_number=args.issue_number,
            policy_decision_id=args.policy_decision_id,
            operator_decision=args.operator_decision,
            publication_preview=preview,
            existing_comments=comments,
        )
    )
    report: dict[str, Any] = {
        "schema": "missipy.github.copilot_advisory_v2_issue_publication_adapter.v1",
        "mode": "execute" if args.execute else "preview",
        "plan": plan.to_mapping(),
        "mutation_action": "none",
        "github_mutation_performed": False,
        "readback_verified": plan.action == "replay" and plan.valid,
        "published_comment": {},
    }

    if not plan.valid:
        _emit(report, args.format)
        return 2
    if not args.execute:
        _emit(report, args.format)
        return 0
    if not _enabled("AUTODOC_REMOTE_MUTATION_ALLOWED"):
        report["execution_error"] = "AUTODOC_REMOTE_MUTATION_ALLOWED is not enabled"
        _emit(report, args.format)
        return 3
    if not _enabled("AUTODOC_ISSUE_PUBLICATION_ALLOWED"):
        report["execution_error"] = "AUTODOC_ISSUE_PUBLICATION_ALLOWED is not enabled"
        _emit(report, args.format)
        return 3
    if args.confirm_plan_digest != plan.plan_digest:
        report["execution_error"] = "confirm-plan-digest mismatch"
        _emit(report, args.format)
        return 3
    if plan.action == "replay":
        report["mutation_action"] = "replay-noop"
        _emit(report, args.format)
        return 0
    if plan.action != "create":
        report["execution_error"] = f"unsupported plan action: {plan.action}"
        _emit(report, args.format)
        return 4

    published = _gh_json(
        args.gh_command,
        (
            "api",
            "--method",
            "POST",
            f"repos/{args.repository}/issues/{args.issue_number}/comments",
            "-f",
            f"body={plan.body}",
        ),
    )
    if not isinstance(published, Mapping):
        raise RuntimeError("GitHub create-comment response must be an object")

    readback = _fetch_comments(args.gh_command, args.repository, args.issue_number)
    matches = [item for item in readback if plan.marker in item.body]
    verified = len(matches) == 1 and matches[0].body == plan.body
    if not verified:
        raise RuntimeError("published Copilot v2 comment readback mismatch")

    report["mutation_action"] = "created"
    report["github_mutation_performed"] = True
    report["readback_verified"] = True
    report["published_comment"] = {
        "comment_id": published.get("id"),
        "html_url": published.get("html_url"),
    }
    _emit(report, args.format)
    return 0


def _fetch_comments(
    command: str,
    repository: str,
    issue_number: int,
) -> tuple[Any, ...]:
    payload = _gh_json(
        command,
        (
            "api",
            "--paginate",
            f"repos/{repository}/issues/{issue_number}/comments",
        ),
    )
    return parse_issue_comment_snapshots(payload)


def _gh_json(command: str, arguments: Sequence[str]) -> object:
    completed = subprocess.run(
        [command, *arguments],
        cwd=_REPO_ROOT,
        text=True,
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
        raise RuntimeError("GitHub CLI did not return valid JSON") from exc


def _read_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise SystemExit("preview JSON must be an object")
    return dict(payload)


def _enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    plan = report["plan"]
    print(f"mode: {report['mode']}")
    print(f"valid: {plan['valid']}")
    print(f"action: {plan['action']}")
    print(f"plan_digest: {plan['plan_digest']}")
    print(f"mutation_action: {report['mutation_action']}")
    print(f"readback_verified: {report['readback_verified']}")
    for issue in plan["issues"]:
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
