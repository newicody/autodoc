#!/usr/bin/env python3
"""Encode/decode fake route messages through the RouteMessage frame codec.

Usage:

    PYTHONPATH=src:. python tools/roundtrip_route_frame.py \
      .var/baby_fork_fake_runtime \
      --route-id baby_fork.variant_stub
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.fake_route_transport import FakeLocalRouteTransport
from runtime.route_frame_codec import decode_route_message_frame, encode_route_message_frame


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roundtrip fake route messages through binary frames.")
    parser.add_argument("fake_runtime_root", type=Path)
    parser.add_argument("--route-id", help="Only roundtrip one route id.")
    args = parser.parse_args(argv)

    fake = FakeLocalRouteTransport(args.fake_runtime_root)
    route_ids = (args.route_id,) if args.route_id else fake.route_ids()

    frames = []
    for route_id in route_ids:
        for message in fake.receive(route_id):
            encoded = encode_route_message_frame(message)
            decoded = decode_route_message_frame(encoded)
            frames.append({
                "route_id": decoded.message.route_id,
                "message_id": decoded.message.message_id,
                "frame_size": len(encoded),
                "payload_size": decoded.header.payload_size,
                "payload_sha256": decoded.header.payload_sha256,
            })

    print(json.dumps({
        "frame_count": len(frames),
        "frames": frames,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
