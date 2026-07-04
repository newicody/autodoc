#!/usr/bin/env python3
"""Validate a ControlFS route manifest.

Usage:

    PYTHONPATH=src:. python tools/validate_controlfs_manifest.py \
      /run/autodoc/controlfs/desired/routes/baby_fork.retrieval/manifest.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from runtime.controlfs_manifest import ManifestValidationError, RouteManifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a ControlFS route manifest.")
    parser.add_argument("manifest", type=Path, help="Path to manifest.json")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print normalized manifest JSON instead of a short OK line.",
    )
    args = parser.parse_args(argv)

    try:
        manifest = RouteManifest.from_path(args.manifest)
    except ManifestValidationError as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(manifest.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"OK route_id={manifest.route_id} zone={manifest.zone} scope={manifest.scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
