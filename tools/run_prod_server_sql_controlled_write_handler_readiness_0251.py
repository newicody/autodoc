#!/usr/bin/env python3
"""Check phase 0251 SQL controlled write handler readiness."""

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

from context.prod_server_sql_controlled_write_handler_readiness_0251 import (  # noqa: E402
    SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY,
    build_sql_controlled_write_handler_readiness,
    sql_controlled_write_handler_readiness_to_dict,
    write_sql_controlled_write_handler_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-config", default="doc/examples/autodoc_prod_server_initial_0241.ini")
    parser.add_argument("--openvino-config", default="doc/examples/autodoc_openvino_embedding_e5_small_0246.ini")
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_sql_controlled_write_handler_readiness_0251.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server_config_path = Path(args.server_config)
    openvino_config_path = Path(args.openvino_config)
    output_path = Path(args.output)

    if args.check_only:
        report = build_sql_controlled_write_handler_readiness(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )
        payload = {
            "production_server_sql_controlled_write_handler_ready": report.ready,
            "sql_controlled_write_handler_readiness": sql_controlled_write_handler_readiness_to_dict(report),
            "boundary": dict(SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY),
        }
    else:
        payload = write_sql_controlled_write_handler_readiness_report(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
            output_path=output_path,
        )
        report = build_sql_controlled_write_handler_readiness(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )

    if args.format == "summary":
        issue_count = len(report.issues)
        if report.handler_frame is None:
            details = "handler=missing table=missing operation=missing"
        else:
            details = (
                f"handler={report.handler_frame.write_request.handler_id} "
                f"table={report.handler_frame.write_request.table} "
                f"operation={report.handler_frame.write_request.operation}"
            )
        if args.check_only:
            print(
                "production_server_sql_controlled_write_handler_ready="
                f"{str(report.ready)} issues={issue_count} {details}"
            )
        else:
            print(
                "production_server_sql_controlled_write_handler_readiness_written=True "
                f"ready={str(report.ready)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
