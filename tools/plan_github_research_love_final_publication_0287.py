#!/usr/bin/env python3
"""Build the r16-r17 final Issue + ProjectV2 publication plan.

This tool is pure and performs no network access.  Its JSON output carries the
canonical existing publication plan under ``publication_plan`` and can be
passed directly to ``tools/publish_love_final_deliverable_0287.py``.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from context.github_research_love_final_remote_publication_0287 import (  # noqa: E402
    GitHubResearchLoveFinalPublicationCommand,
    build_github_research_love_final_publication_plan,
)


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-deliverable", required=True)
    parser.add_argument("--liaison", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", required=True, type=int)
    parser.add_argument("--policy-decision-id", required=True)
    parser.add_argument("--operator-decision", choices=("approve",), required=True)
    parser.add_argument("--project-item-id", required=True)
    parser.add_argument("--project-field-ref", required=True)
    parser.add_argument("--project-field-name", default="Résumé")
    parser.add_argument(
        "--project-status-value",
        default="Livrable final prêt",
    )
    parser.add_argument("--max-body-chars", type=int, default=30_000)
    parser.add_argument("--max-project-value-chars", type=int, default=500)
    parser.add_argument("--output")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    return parser.parse_args(argv)


def _load_mapping(path: str, name: str) -> Mapping[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise ValueError(f"{name} file not found: {source}")
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} file is not valid JSON: {source}") from exc
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} file must contain a JSON object")
    return value


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        final_deliverable = _load_mapping(
            args.final_deliverable,
            "final deliverable",
        )
        liaison = _load_mapping(args.liaison, "liaison")
        source_issue_ref = (
            f"github-frame:{args.repository}/issues/{args.issue_number}"
        )
        plan = build_github_research_love_final_publication_plan(
            GitHubResearchLoveFinalPublicationCommand(
                final_deliverable=final_deliverable,
                liaison=liaison,
                repository=args.repository,
                issue_number=args.issue_number,
                source_issue_ref=source_issue_ref,
                policy_decision_id=args.policy_decision_id,
                operator_decision=args.operator_decision,
                project_item_id=args.project_item_id,
                project_field_ref=args.project_field_ref,
                project_field_name=args.project_field_name,
                project_status_value=args.project_status_value,
                max_body_chars=args.max_body_chars,
                max_project_value_chars=args.max_project_value_chars,
            )
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = plan.to_mapping()
    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")

    if args.format == "json":
        print(rendered)
    else:
        print(
            f"valid=true action={plan.publication_plan.action} "
            f"plan_digest={plan.plan_digest} "
            f"lineage_digest={plan.lineage_digest}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
