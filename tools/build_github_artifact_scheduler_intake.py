#!/usr/bin/env python3
"""Build a GitHub artifact scheduler intake candidate or authorized route request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_artifact_scheduler_intake import build_github_artifact_scheduler_intake_plan  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scheduler intake candidate from GitHub artifact dataset observation."
    )
    parser.add_argument("--input", required=True, help="JSON mapping with scheduler intake fields.")
    parser.add_argument("--policy-decision-id", help="Policy decision id required to emit an authorized route request.")
    parser.add_argument("--authorized", action="store_true", help="Emit authorized SchedulerRouteRequest mapping.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("--input JSON must contain an object")

    plan = build_github_artifact_scheduler_intake_plan(
        raw,
        policy_decision_id=args.policy_decision_id,
        authorized=args.authorized,
    )

    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"authorized: {plan.authorized}")
        print(f"candidate_ref: {plan.candidate.candidate_ref}")
        print(f"route_id: {plan.candidate.route_id}")
        print(f"task_id: {plan.candidate.task_id}")
        print("scheduler_modified: False")
        print("creates_parallel_scheduler: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
