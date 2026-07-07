#!/usr/bin/env python3
"""Project a GitHub artifact dataset report to existing bus JSONL files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_artifact_dataset_bus_observation import (  # noqa: E402
    append_github_artifact_dataset_bus_observation,
    build_github_artifact_dataset_bus_observation,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Project GitHub artifact dataset outcome to existing event.bus/context.bus JSONL."
    )
    parser.add_argument("--input", required=True, help="JSON mapping with dataset observation fields.")
    parser.add_argument("--runtime-root", help="Explicit runtime root containing event.bus.jsonl/context.bus.jsonl.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit("--input JSON must contain an object")

    if args.runtime_root:
        projection = append_github_artifact_dataset_bus_observation(
            runtime_root=Path(args.runtime_root),
            raw=raw,
        )
    else:
        projection = build_github_artifact_dataset_bus_observation(raw)

    if args.format == "json":
        print(json.dumps(projection.to_mapping(), indent=2, sort_keys=True))
    else:
        print(f"event_count: {projection.event_count}")
        print(f"context_count: {projection.context_count}")
        print("creates_parallel_bus: False")
        print("writes_vispy_directly: False")
        print("scheduler_modified: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
