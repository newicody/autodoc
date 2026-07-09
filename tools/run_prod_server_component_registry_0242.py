#!/usr/bin/env python3
"""Build the phase 0242 declarative production server component registry."""

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

from context.prod_server_component_registry_0242 import (  # noqa: E402
    COMPONENT_REGISTRY_BOUNDARY,
    build_component_registry,
    registry_to_dict,
    write_component_registry_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="doc/examples/autodoc_prod_server_initial_0241.ini",
    )
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_component_registry_0242.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)

    if args.check_only:
        report = build_component_registry(config_path)
        payload = {
            "production_server_component_registry_valid": report.valid,
            "registry": registry_to_dict(report),
            "boundary": dict(COMPONENT_REGISTRY_BOUNDARY),
        }
    else:
        payload = write_component_registry_report(config_path=config_path, output_path=output_path)
        report = build_component_registry(config_path)

    if args.format == "summary":
        issue_count = len(report.issues)
        ordered = ",".join(report.ordered_components)
        if args.check_only:
            print(
                "production_server_component_registry_valid="
                f"{str(report.valid)} issues={issue_count} order={ordered}"
            )
        else:
            print(
                "production_server_component_registry_written=True "
                f"valid={str(report.valid)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
