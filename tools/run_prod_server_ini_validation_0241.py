#!/usr/bin/env python3
"""Validate the production server INI file for phase 0241."""

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

from context.prod_server_ini_validation_0241 import (  # noqa: E402
    INI_VALIDATION_BOUNDARY,
    validate_ini_file,
    validation_to_dict,
    write_ini_validation_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        default="doc/examples/autodoc_prod_server_initial_0241.ini",
    )
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_ini_validation_0241.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)

    if args.check_only:
        result = validate_ini_file(config_path)
        payload = {
            "production_server_ini_valid": result.valid,
            "validation": validation_to_dict(result),
            "boundary": dict(INI_VALIDATION_BOUNDARY),
        }
    else:
        payload = write_ini_validation_report(config_path=config_path, output_path=output_path)
        result = validate_ini_file(config_path)

    if args.format == "summary":
        issue_count = len(result.issues)
        if args.check_only:
            print(
                "production_server_ini_valid="
                f"{str(result.valid)} issues={issue_count} config={config_path}"
            )
        else:
            print(
                "production_server_ini_validation_written=True "
                f"valid={str(result.valid)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
