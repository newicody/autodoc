#!/usr/bin/env python3
"""Write or print the phase 0240 production server initial configuration requirements."""

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

from context.prod_server_initial_config_requirements_0240 import (  # noqa: E402
    configuration_to_dict,
    validate_production_server_initial_configuration,
    write_production_server_initial_configuration,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_initial_config_requirements_0240.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)

    if args.check_only:
        errors = validate_production_server_initial_configuration()
        payload = {
            "production_server_initial_configuration_valid": not errors,
            "validation_errors": errors,
            "configuration": configuration_to_dict(),
        }
    else:
        payload = write_production_server_initial_configuration(output_path)

    if args.format == "summary":
        errors = payload["validation_errors"]
        if args.check_only:
            print(
                "production_server_initial_configuration_valid="
                f"{str(not errors)} errors={len(errors)}"
            )
        else:
            print(
                "production_server_initial_configuration_written="
                f"{str(not errors)} errors={len(errors)} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if not payload["validation_errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
