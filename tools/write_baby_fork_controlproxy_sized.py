#!/usr/bin/env python3
"""Write baby-fork ControlProxy/ControlFS desired manifests with measured sizing.

Usage:

    PYTHONPATH=src:. python tools/write_baby_fork_controlproxy_sized.py \
      .var/baby_fork_smoke/baby_fork_report.json \
      .var/baby_fork_controlfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from context.baby_fork_controlfs import (
    build_route_sizing_hints_from_messages,
    write_baby_fork_desired_manifests,
)
from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write sized baby-fork ControlProxy desired route manifests.")
    parser.add_argument("report_path", type=Path)
    parser.add_argument("controlfs_root", type=Path)
    parser.add_argument("--context-id")
    parser.add_argument("--slot-count", type=int, default=16)
    parser.add_argument("--headroom-bytes", type=int, default=256)
    args = parser.parse_args(argv)

    try:
        report = json.loads(args.report_path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"INVALID JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(report, dict):
        print("INVALID JSON: report must be an object", file=sys.stderr)
        return 2

    projection = build_baby_fork_runtime_projection(report, report_uri=str(args.report_path))
    sizing_hints = build_route_sizing_hints_from_messages(
        projection.routes,
        slot_count=args.slot_count,
        headroom_bytes=args.headroom_bytes,
    )

    context_id = args.context_id
    if context_id is None:
        final_context = report.get("final_context")
        if isinstance(final_context, dict) and final_context.get("context_id"):
            context_id = str(final_context["context_id"])

    paths = write_baby_fork_desired_manifests(
        args.controlfs_root,
        context_id=context_id or "baby_fork_smoke",
        sizing_hints=sizing_hints,
    )

    print(json.dumps({
        "written": [str(path) for path in paths],
        "sizing_hints": {
            route_id: {
                "observed_frame_bytes": hint.observed_frame_bytes,
                "slot_size": hint.slot_size,
                "slot_count": hint.slot_count,
                "max_frame_bytes": hint.normalized_max_frame_bytes(),
                "transport": hint.transport,
                "notify": hint.notify,
                "overflow_policy": hint.overflow_policy,
            }
            for route_id, hint in sorted(sizing_hints.items())
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
