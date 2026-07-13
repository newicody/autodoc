#!/usr/bin/env python3
"""Local controlled adapter for publishing one advisory comment to an Issue.

Default mode is preview-only. ``--execute`` additionally requires an exact
``--confirm-plan-digest`` produced by the preview. The adapter creates a
comment only for a valid ``create`` plan. Replays perform no mutation and
collisions are blocked.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_controlled_advisory_issue_publication_0281 import (  # noqa: E402
    GitHubControlledAdvisoryIssuePublicationCommand,
    parse_issue_comment_snapshots,
    plan_github_controlled_advisory_issue_publication,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute an operator-authorized, idempotent "
            "Copilot advisory Issue comment publication."
        )
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument(
        "--operator-decision",
        choices=("approve",),
        required=True,
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-plan-digest", default="")
    parser.add_argument(
        "--gh-command",
        default="gh",
        help="GitHub CLI executable, default: gh",
    )
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    preview = _read_mapping(args.preview)
    comments_payload = _gh_json(
        args.gh_command,
        [
            "api",
            "--paginate",
            f"repos/{args.repository}/issues/{args.issue_number}/comments",
        ],
    )
    comments = parse_issue_comment_snapshots(comments_payload)
    plan = plan_github_controlled_advisory_issue_publication(
        GitHubControlledAdvisoryIssuePublicationCommand(
            repository=args.repository,
            issue_number=args.issue_number,
            policy_decision_id=args.policy_decision_id,
            operator_decision=args.operator_decision,
            publication_preview=preview,
            existing_comments=comments,
        )
    )
    report = {
        "schema": "missipy.github.controlled_advisory_issue_publication_adapter.v1",
        "mode": "execute" if args.execute else "preview",
        "plan": plan.to_mapping(),
        "mutation_action": "none",
        "github_mutation_performed": False,
        "published_comment": {},
        "boundary": [
            "local adapter only",
            "explicit operator approve decision",
            "exact plan digest confirmation required for execute",
            "create only; replay does not mutate",
            "collision blocks mutation",
            "workflow producer cannot self-authorize publication",
        ],
    }

    if not plan.valid:
        _emit(report, args.format)
        return 2
    if not args.execute:
        _emit(report, args.format)
        return 0
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
        [
            "api",
            "--method",
            "POST",
            f"repos/{args.repository}/issues/{args.issue_number}/comments",
            "-f",
            f"body={plan.body}",
        ],
    )
    if not isinstance(published, Mapping):
        raise RuntimeError("GitHub create-comment response must be an object")
    report["mutation_action"] = "created"
    report["github_mutation_performed"] = True
    report["published_comment"] = {
        "comment_id": published.get("id"),
        "html_url": published.get("html_url"),
    }
    _emit(report, args.format)
    return 0


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
    print(
        "github_mutation_performed: "
        f"{report['github_mutation_performed']}"
    )
    for issue in plan["issues"]:
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
