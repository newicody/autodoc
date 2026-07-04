#!/usr/bin/env python3
"""Prepare fake runtime routes through ControlProxy handshake.

This is 0079-r2: it does not create mmap. It reads existing fake route
messages, measures their encoded frame sizes, decides route readiness by zone
policy, and writes ControlProxy state to event.bus/context.bus for Recorder,
VisPy or any later UI lens.
"""

from __future__ import annotations

import argparse
import json

from runtime.controlproxy_prepare import (
    decide_route_prepare,
    route_prepare_request_from_message,
    write_controlproxy_decisions_to_fake_bus,
)
from runtime.fake_route_transport import FakeLocalRouteTransport


def _zone_scope(route_id: str) -> tuple[str, str]:
    if route_id.endswith(".context_gate"):
        return "context", "context.patch"
    return "workers", "context.read"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare fake routes with ControlProxy handshake.")
    parser.add_argument("fake_runtime_root")
    parser.add_argument("--task-id", default="ctx-baby-fork-001")
    parser.add_argument("--replace-bus", action="store_true", help="Rewrite ControlProxy bus files instead of appending.")
    args = parser.parse_args(argv)

    transport = FakeLocalRouteTransport(args.fake_runtime_root)
    requests = []
    decisions = []

    for route_id in transport.route_ids():
        zone, scope = _zone_scope(route_id)
        for message in transport.receive(route_id):
            request = route_prepare_request_from_message(
                message,
                task_id=args.task_id,
                zone=zone,
                scope=scope,
            )
            requests.append(request)
            decisions.append(decide_route_prepare(request))

    bus_counts = write_controlproxy_decisions_to_fake_bus(
        args.fake_runtime_root,
        decisions,
        append=not args.replace_bus,
    )

    print(json.dumps({
        "request_count": len(requests),
        "decision_count": len(decisions),
        "bus_counts": bus_counts,
        "decisions": [decision.to_mapping() for decision in decisions],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
