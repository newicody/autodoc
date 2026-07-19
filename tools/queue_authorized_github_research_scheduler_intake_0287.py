#!/usr/bin/env python3

"""Queue one authorized GitHub research intake for the canonical Scheduler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue import (  # noqa: E402
    append_authorized_github_research_scheduler_intake,
)


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input report must contain a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Queue one authorized GitHub research Scheduler request without "
            "starting Scheduler, Dispatcher, EventBus, handler, or laboratory."
        )
    )
    parser.add_argument("--input", required=True, help="Authorized Scheduler intake JSON report.")
    parser.add_argument("--runtime-root", required=True, help="Local runtime handoff directory.")
    parser.add_argument("--policy-decision-id", required=True, help="Expected policy decision id.")
    parser.add_argument("--repository", required=True, help="Expected repository in owner/name form.")
    parser.add_argument("--run-id", required=True, help="Expected GitHub Actions run id.")
    parser.add_argument(
        "--queue-name",
        default="scheduler.route_requests.jsonl",
        help="Local JSONL queue filename.",
    )
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)

    report = append_authorized_github_research_scheduler_intake(
        scheduler_intake_report=_load_mapping(Path(args.input)),
        runtime_root=Path(args.runtime_root),
        policy_decision_id=args.policy_decision_id,
        repository=args.repository,
        run_id=args.run_id,
        queue_name=args.queue_name,
    )
    mapping = report.to_mapping()
    if args.format == "json":
        print(json.dumps(mapping, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"valid={str(report.valid).lower()}",
                    f"status={report.status}",
                    f"action={report.action}",
                    f"queued_count={report.queued_count}",
                    f"replayed_count={report.replayed_count}",
                    f"request_id={report.request_id}",
                    f"queue_path={report.queue_path}",
                )
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
