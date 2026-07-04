#!/usr/bin/env python3
"""Replay fake runtime route messages into an in-process ring runtime.

Usage:

    PYTHONPATH=src:. python tools/replay_fake_routes_to_ring.py \
      .var/baby_fork_fake_runtime \
      --capacity 4
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.fake_route_transport import FakeLocalRouteTransport
from runtime.inprocess_ring_buffer import InProcessRouteRuntime, RingBufferOverflowError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay fake route messages into in-process ring buffers.")
    parser.add_argument("fake_runtime_root", type=Path)
    parser.add_argument("--capacity", type=int, default=4)
    parser.add_argument("--overflow-policy", choices=("reject", "drop_oldest"), default="reject")
    args = parser.parse_args(argv)

    fake = FakeLocalRouteTransport(args.fake_runtime_root)
    runtime = InProcessRouteRuntime(
        route_capacity=args.capacity,
        overflow_policy=args.overflow_policy,
    )

    sent = 0
    errors: list[dict[str, str]] = []

    for route_id in fake.route_ids():
        for message in fake.receive(route_id):
            try:
                runtime.send(message)
                sent += 1
            except RingBufferOverflowError as exc:
                errors.append({"route_id": route_id, "error": str(exc)})

    print(json.dumps({
        "sent": sent,
        "errors": errors,
        "stats": runtime.stats(),
    }, indent=2, sort_keys=True))

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
