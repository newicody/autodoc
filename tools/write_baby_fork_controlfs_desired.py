#!/usr/bin/env python3
"""Write ControlFS desired route manifests for baby-fork routes.

Usage:

    PYTHONPATH=src:. python tools/write_baby_fork_controlfs_desired.py \
      .var/baby_fork_controlfs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.baby_fork_controlfs import write_baby_fork_desired_manifests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write baby-fork ControlFS desired route manifests.")
    parser.add_argument("controlfs_root", type=Path)
    parser.add_argument("--context-id", default="baby_fork_smoke")
    args = parser.parse_args(argv)

    paths = write_baby_fork_desired_manifests(
        args.controlfs_root,
        context_id=args.context_id,
    )
    print(json.dumps({"written": [str(path) for path in paths]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
