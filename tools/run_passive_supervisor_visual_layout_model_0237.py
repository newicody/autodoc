#!/usr/bin/env python3
"""Build a read-only passive supervisor visual layout model."""

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

from context.passive_supervisor_visual_layout_model import (  # noqa: E402
    build_passive_supervisor_visual_layout_model,
    write_passive_supervisor_visual_layout_model,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="Snapshot or visual read-model JSON")
    parser.add_argument("--output", required=True, help="Output layout JSON")
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input_json)
    output_path = Path(args.output)
    model: dict[str, Any] = json.loads(input_path.read_text(encoding="utf-8"))
    layout = write_passive_supervisor_visual_layout_model(
        output_path,
        model,
        generated_at=args.generated_at,
    )

    if args.format == "summary":
        print(
            "passive_supervisor_visual_layout_model_written="
            f"{layout['passive_supervisor_visual_layout_model_written']} "
            f"zones={layout['zone_count']} nodes={layout['node_count']} "
            f"edges={layout['edge_count']} output={output_path}"
        )
    else:
        print(json.dumps(layout, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
