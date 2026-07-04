#!/usr/bin/env python3
"""Replay fake route messages into in-process frame rings.

Usage:

    PYTHONPATH=src:. python tools/replay_fake_routes_to_frame_ring.py \
      .var/baby_fork_fake_runtime \
      --capacity 4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.fake_route_transport import FakeLocalRouteTransport
from runtime.inprocess_frame_ring import (
    FrameRingOverflowError,
    FrameTooLargeError,
    InProcessFrameRouteRuntime,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay fake routes into in-process frame rings.")
    parser.add_argument("fake_runtime_root", type=Path)
    parser.add_argument("--capacity", type=int, default=4)
    parser.add_argument("--overflow-policy", choices=("reject", "drop_oldest"), default="reject")
    parser.add_argument("--max-frame-bytes", type=int)
    args = parser.parse_args(argv)

    fake = FakeLocalRouteTransport(args.fake_runtime_root)
    runtime = InProcessFrameRouteRuntime(
        route_capacity=args.capacity,
        overflow_policy=args.overflow_policy,
        max_frame_bytes=args.max_frame_bytes,
    )

    sent = 0
    frames = []
    errors: list[dict[str, str]] = []

    for route_id in fake.route_ids():
        for message in fake.receive(route_id):
            try:
                slot = runtime.send_message(message)
                decoded = slot.decode()
                sent += 1
                frames.append({
                    "sequence": slot.sequence,
                    "route_id": decoded.message.route_id,
                    "message_id": decoded.message.message_id,
                    "frame_size": slot.frame_size,
                    "payload_sha256": decoded.header.payload_sha256,
                })
            except (FrameRingOverflowError, FrameTooLargeError) as exc:
                errors.append({"route_id": route_id, "error": str(exc)})

    print(json.dumps({
        "sent": sent,
        "errors": errors,
        "frames": frames,
        "stats": runtime.stats(),
    }, indent=2, sort_keys=True))

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
