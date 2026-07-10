#!/usr/bin/env python3
"""Run Scheduler-managed sql_ref -> OpenVINO/E5 embedding usage."""

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

from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (  # noqa: E402
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    build_demo_embedding,
    load_json,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
    write_report,
)
from context.sql_context_store import SQLiteSqlContextStore  # noqa: E402


DEFAULT_DB_PATH = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
DEFAULT_BINDING_REPORT = ROOT / ".var/reports/scheduler_managed_db_api_sql_context_store_binding_0260.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--binding-report", default=str(DEFAULT_BINDING_REPORT))
    parser.add_argument("--sql-ref", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--demo-embedding", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def _sql_ref_from_report(path: Path) -> str:
    if not path.exists():
        return ""
    payload = load_json(path)
    usage = payload.get("usage", {})
    if isinstance(usage, dict):
        value = usage.get("sql_ref", "")
        if value:
            return str(value)
    return ""


def main() -> int:
    args = parse_args()
    sql_ref = args.sql_ref or _sql_ref_from_report(Path(args.binding_report))
    request = SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
        sql_ref=sql_ref,
        role="passage",
        policy_decision_id=args.policy_decision_id,
        model_dir=args.model_dir,
        device=args.device,
    )
    store = SQLiteSqlContextStore(args.db_path)
    store.initialize_schema()
    embedder = build_demo_embedding if args.demo_embedding else None
    result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        store,
        request,
        execute=args.execute,
        embedder=embedder,
    )
    payload = result.to_mapping()

    if args.output:
        write_report(Path(args.output), payload)

    if args.format == "summary":
        embedding = payload.get("embedding", {})
        print(
            "scheduler_managed_sql_ref_openvino_embedding_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"execute={payload['execute']} dry_run={payload['dry_run']} "
            f"sql_ref={request.sql_ref or '-'} "
            f"embedding_ref={embedding.get('embedding_ref', '-') if isinstance(embedding, dict) else '-'} "
            f"dimension={embedding.get('dimension', '-') if isinstance(embedding, dict) else '-'}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))

    store.close()
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
