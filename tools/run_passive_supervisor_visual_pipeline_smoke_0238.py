#!/usr/bin/env python3
"""Run the local passive supervisor visual report pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for _path in (str(SRC_ROOT), str(REPO_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.passive_supervisor_visual_pipeline_0238 import (  # noqa: E402
    run_visual_pipeline,
    visual_pipeline_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-dir", default=".var/reports")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report_dir = Path(args.report_dir)

    if args.plan_only:
        payload = visual_pipeline_plan(repo_root=REPO_ROOT, report_dir=report_dir)
    else:
        payload = run_visual_pipeline(repo_root=REPO_ROOT, report_dir=report_dir)

    if args.format == "summary":
        if args.plan_only:
            print(
                "passive_supervisor_visual_pipeline_plan=True "
                f"steps={len(payload['steps'])} report_dir={payload['report_dir']}"
            )
        else:
            print(
                "passive_supervisor_visual_pipeline_written=True "
                f"steps={len(payload['steps'])} report_dir={payload['report_dir']} "
                f"summary={payload['outputs']['visual_pipeline']}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
