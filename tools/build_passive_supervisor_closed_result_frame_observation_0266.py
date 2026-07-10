#!/usr/bin/env python3
"""Build PassiveSupervisor read model from 0265 EventBus observation report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.passive_supervisor_closed_result_frame_observation_0266 import (  # noqa: E402
    build_passive_supervisor_closed_frame_observation_report,
    load_json,
    write_report,
)


DEFAULT_OBSERVATION_REPORT = ROOT / ".var/reports/closed_result_frame_eventbus_observation_0265.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observation-report", default=str(DEFAULT_OBSERVATION_REPORT))
    parser.add_argument("--source-observation-ref", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    observation_path = Path(args.observation_report)
    observation_report = load_json(observation_path)
    report = build_passive_supervisor_closed_frame_observation_report(
        observation_report,
        source_observation_ref=args.source_observation_ref or str(observation_path),
    )
    payload = report.to_mapping()

    if args.output:
        write_report(Path(args.output), payload)

    if args.format == "summary":
        print(
            "passive_supervisor_closed_result_frame_observation_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"facts={payload['fact_count']} "
            f"accepted={payload['accepted_fact_count']} "
            f"rejected={payload['rejected_fact_count']} "
            f"command_like={payload['command_like_fact_count']} "
            f"runtime_violations={payload['runtime_violation_count']}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
