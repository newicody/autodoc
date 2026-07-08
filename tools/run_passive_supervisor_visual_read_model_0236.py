#!/usr/bin/env python3
"""Build a read-only visual read-model from a passive supervisor snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _path in (str(SRC_ROOT), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.context.passive_supervisor_visual_read_model import build_visual_read_model


def parse_args(argv: tuple[str, ...]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--layout-kind", default="cellular")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args(argv)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: tuple[str, ...] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    snapshot = json.loads(args.snapshot_json.read_text(encoding="utf-8"))
    model = build_visual_read_model(
        snapshot,
        generated_at=args.generated_at,
        layout_kind=args.layout_kind,
    ).to_dict()
    _write_json(args.output, model)
    if args.format == "summary":
        print(
            "passive_supervisor_visual_read_model_written=True "
            f"nodes={model['node_count']} edges={model['edge_count']} "
            f"zones={model['zone_count']}"
        )
    else:
        print(json.dumps(model, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
