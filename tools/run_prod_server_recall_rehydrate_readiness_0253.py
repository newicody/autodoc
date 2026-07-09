#!/usr/bin/env python3
"""Check production server recall to SQL rehydrate readiness."""

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

from context.prod_server_recall_rehydrate_readiness_0253 import (  # noqa: E402
    build_recall_rehydrate_readiness,
    recall_rehydrate_readiness_to_dict,
    write_recall_rehydrate_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="doc/examples/autodoc_prod_server_initial_0241.ini")
    parser.add_argument("--openvino-config", default="doc/examples/autodoc_openvino_embedding_e5_small_0246.ini")
    parser.add_argument("--output", default=".var/reports/prod_server_recall_rehydrate_readiness_0253.json")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server_config_path = Path(args.config)
    openvino_config_path = Path(args.openvino_config)

    if args.check_only:
        report = build_recall_rehydrate_readiness(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )
        if args.format == "summary":
            read = report.sql_rehydrate_read
            table = read.table if read is not None else ""
            lookup = read.lookup_field if read is not None else ""
            print(
                "production_server_recall_rehydrate_ready="
                f"{report.ready} issues={len(report.issues)} table={table} lookup={lookup}"
            )
        else:
            print(json.dumps(recall_rehydrate_readiness_to_dict(report), indent=2, sort_keys=True))
        return 0 if report.ready else 1

    output_path = Path(args.output)
    payload = write_recall_rehydrate_readiness_report(
        server_config_path=server_config_path,
        openvino_config_path=openvino_config_path,
        output_path=output_path,
    )
    report = payload["recall_rehydrate_readiness"]
    if args.format == "summary":
        print(
            "production_server_recall_rehydrate_readiness_written=True "
            f"ready={report['ready']} issues={len(report['issues'])} output={output_path}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
