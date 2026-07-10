#!/usr/bin/env python3
"""Build EventBus observation facts from the 0264 closed ResultFrame."""

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

from context.closed_result_frame_eventbus_observation_0265 import (  # noqa: E402
    build_and_optionally_publish_closed_result_frame_eventbus_observation,
    load_json,
    write_report,
)


DEFAULT_FRAME_REPORT = ROOT / ".var/reports/scheduler_managed_closed_result_frame_0264.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame-report", default=str(DEFAULT_FRAME_REPORT))
    parser.add_argument("--frame-ref", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--publish-demo", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame_path = Path(args.frame_report)
    frame = load_json(frame_path)
    report = build_and_optionally_publish_closed_result_frame_eventbus_observation(
        frame,
        frame_ref=args.frame_ref or str(frame_path),
        publish_demo=args.publish_demo,
    )
    payload = report.to_mapping()

    if args.output:
        write_report(Path(args.output), payload)

    if args.format == "summary":
        print(
            "closed_result_frame_eventbus_observation_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"facts={payload['fact_count']} "
            f"published={payload['published_count']} "
            f"observed={payload['observed_count']} "
            f"event_types={','.join(payload['event_types']) or '-'}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
