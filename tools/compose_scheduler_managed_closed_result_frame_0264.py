#!/usr/bin/env python3
"""Compose the 0260-0263 Scheduler-managed closed ResultFrame."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.scheduler_managed_closed_result_frame_0264 import (  # noqa: E402
    compose_scheduler_managed_closed_result_frame_from_paths,
    write_result_frame,
)


DEFAULT_SQL_WRITE_REPORT = ROOT / ".var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json"
DEFAULT_EMBEDDING_REPORT = ROOT / ".var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json"
DEFAULT_PROJECTION_REPORT = ROOT / ".var/reports/scheduler_managed_embedding_qdrant_projection_0262.json"
DEFAULT_RECALL_REHYDRATE_REPORT = ROOT / ".var/reports/scheduler_managed_qdrant_recall_sql_rehydrate_0263.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-write-report", default=str(DEFAULT_SQL_WRITE_REPORT))
    parser.add_argument("--embedding-report", default=str(DEFAULT_EMBEDDING_REPORT))
    parser.add_argument("--projection-report", default=str(DEFAULT_PROJECTION_REPORT))
    parser.add_argument("--recall-rehydrate-report", default=str(DEFAULT_RECALL_REHYDRATE_REPORT))
    parser.add_argument("--output", default="")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame = compose_scheduler_managed_closed_result_frame_from_paths(
        sql_write_report_path=Path(args.sql_write_report),
        embedding_report_path=Path(args.embedding_report),
        projection_report_path=Path(args.projection_report),
        recall_rehydrate_report_path=Path(args.recall_rehydrate_report),
    )
    payload = frame.to_mapping()

    if args.output:
        write_result_frame(Path(args.output), frame)

    if args.format == "summary":
        print(
            "scheduler_managed_closed_result_frame_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"sql_ref={payload.get('sql_ref') or '-'} "
            f"embedding_ref={payload.get('embedding_ref') or '-'} "
            f"projection_points={payload.get('projection_point_count', '-')} "
            f"recall_hits={payload.get('recall_hit_count', '-')} "
            f"hydrated={payload.get('hydrated_count', '-')} "
            f"missing={payload.get('missing_count', '-')}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
