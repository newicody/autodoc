#!/usr/bin/env python3
"""Check phase 0246 OpenVINO embedding readiness."""

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

from context.prod_server_openvino_embedding_readiness_0246 import (  # noqa: E402
    OPENVINO_EMBEDDING_READINESS_BOUNDARY,
    build_openvino_embedding_readiness,
    openvino_embedding_readiness_to_dict,
    write_openvino_embedding_readiness_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="doc/examples/autodoc_openvino_embedding_e5_small_0246.ini")
    parser.add_argument(
        "--output",
        default=".var/reports/prod_server_openvino_embedding_readiness_0246.json",
    )
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    output_path = Path(args.output)

    if args.check_only:
        report = build_openvino_embedding_readiness(config_path)
        payload = {
            "production_server_openvino_embedding_ready": report.ready,
            "openvino_embedding_readiness": openvino_embedding_readiness_to_dict(report),
            "boundary": dict(OPENVINO_EMBEDDING_READINESS_BOUNDARY),
        }
    else:
        payload = write_openvino_embedding_readiness_report(config_path=config_path, output_path=output_path)
        report = build_openvino_embedding_readiness(config_path)

    if args.format == "summary":
        issue_count = len(report.issues)
        if report.embedding is None:
            details = "model=missing dimension=0 device=missing"
        else:
            details = (
                f"model={report.embedding.model_id} "
                f"dimension={report.embedding.dimension} "
                f"device={report.embedding.device}"
            )
        if args.check_only:
            print(
                "production_server_openvino_embedding_ready="
                f"{str(report.ready)} issues={issue_count} {details}"
            )
        else:
            print(
                "production_server_openvino_embedding_readiness_written=True "
                f"ready={str(report.ready)} issues={issue_count} output={output_path}"
            )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
