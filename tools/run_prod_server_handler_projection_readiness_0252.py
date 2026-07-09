#!/usr/bin/env python3
"""Check phase 0252 handler projection readiness."""

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

from context.prod_server_handler_projection_readiness_0252 import (  # noqa: E402
    HANDLER_PROJECTION_READINESS_BOUNDARY,
    build_handler_projection_readiness,
    handler_projection_readiness_to_dict,
    write_handler_projection_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-config", default="doc/examples/autodoc_prod_server_initial_0241.ini")
    parser.add_argument("--openvino-config", default="doc/examples/autodoc_openvino_embedding_e5_small_0246.ini")
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_handler_projection_readiness_0252.json",
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
        report = build_handler_projection_readiness(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )
        payload = {
            "production_server_handler_projection_ready": report.ready,
            "handler_projection_readiness": handler_projection_readiness_to_dict(report),
            "boundary": dict(HANDLER_PROJECTION_READINESS_BOUNDARY),
        }
    else:
        payload = write_handler_projection_readiness_report(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
            output_path=output_path,
        )
        report = build_handler_projection_readiness(
            server_config_path=server_config_path,
            openvino_config_path=openvino_config_path,
        )

    if args.format == "summary":
        issue_count = len(report.issues)
        if report.projection_request is None:
            details = "collection=missing dimension=0 sql_ref=missing"
        else:
            details = (
                f"collection={report.projection_request.qdrant_collection} "
                f"dimension={report.projection_request.vector_dimension} "
                f"sql_ref={report.projection_request.sql_ref}"
            )
        if args.check_only:
            print(
                "production_server_handler_projection_ready="
                f"{str(report.ready)} issues={issue_count} {details}"
            )
        else:
            print(
                "production_server_handler_projection_readiness_written=True "
                f"ready={str(report.ready)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
