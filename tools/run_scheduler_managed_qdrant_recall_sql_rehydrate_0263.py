#!/usr/bin/env python3
"""Run Scheduler-managed Qdrant recall -> SQL rehydrate usage."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (  # noqa: E402
    DemoQdrantRecallExecutor,
    SchedulerManagedQdrantRecallSqlRehydrateRequest,
    default_query_ref_from_embedding_report,
    load_json,
    run_scheduler_managed_qdrant_recall_sql_rehydrate_usage,
    write_report,
)
from context.sql_context_store import SQLiteSqlContextStore  # noqa: E402
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    build_qdrant_client_projection_executor,
)

DEFAULT_DB_PATH = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
DEFAULT_EMBEDDING_REPORT = ROOT / ".var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json"
DEFAULT_PROJECTION_REPORT = ROOT / ".var/reports/scheduler_managed_embedding_qdrant_projection_0262.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--embedding-report", default=str(DEFAULT_EMBEDDING_REPORT))
    parser.add_argument("--projection-report", default=str(DEFAULT_PROJECTION_REPORT))
    parser.add_argument("--output", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    qdrant_mode = parser.add_mutually_exclusive_group()
    qdrant_mode.add_argument("--demo-qdrant", action="store_true")
    qdrant_mode.add_argument("--live-qdrant", action="store_true")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--qdrant-timeout-seconds", type=float, default=10.0)
    parser.add_argument("--qdrant-prefer-grpc", action="store_true")
    parser.add_argument("--qdrant-grpc-port", type=int, default=6334)
    parser.add_argument("--qdrant-api-key-env", default="QDRANT_API_KEY")
    parser.add_argument("--query-ref", default="")
    parser.add_argument("--collection", default="autodoc_context_embeddings")
    parser.add_argument("--dimension", type=int, default=384)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def _sql_refs_from_projection_report(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    payload = load_json(path)
    refs: list[str] = []
    batch = payload.get("batch", {})
    if isinstance(batch, dict):
        for value in batch.get("sql_context_refs", []):
            if isinstance(value, str) and value.startswith("sql:") and value not in refs:
                refs.append(value)
        for point in batch.get("points", []):
            if isinstance(point, dict):
                ref = point.get("sql_context_ref") or point.get("payload", {}).get("sql_ref", "")
                if isinstance(ref, str) and ref.startswith("sql:") and ref not in refs:
                    refs.append(ref)
    return tuple(refs)


def _mode(args: argparse.Namespace) -> str:
    if args.live_qdrant:
        return "live"
    if args.demo_qdrant:
        return "demo"
    return "none"


def _build_live_executor(args: argparse.Namespace):
    config = QdrantClientConnectionConfig(
        url=args.qdrant_url,
        timeout_seconds=args.qdrant_timeout_seconds,
        prefer_grpc=args.qdrant_prefer_grpc,
        grpc_port=args.qdrant_grpc_port,
    )
    gate = QdrantClientEffectGate(
        policy_decision_id=args.policy_decision_id,
        allow_write=False,
        allow_search=True,
    )
    api_key = os.environ.get(args.qdrant_api_key_env) if args.qdrant_api_key_env else None
    return build_qdrant_client_projection_executor(config, gate, api_key=api_key), config


def _failure_payload(args: argparse.Namespace, exc: Exception) -> dict[str, Any]:
    return {
        "scheduler_managed_qdrant_recall_sql_rehydrate_usage": True,
        "valid": False,
        "issues": [f"qdrant_client_executor:{type(exc).__name__}:{str(exc)[:500]}"],
        "execute": args.execute,
        "dry_run": not args.execute,
        "qdrant_mode": _mode(args),
        "uses_qdrant_client_executor": args.live_qdrant,
        "qdrant_recall_live": False,
        "starts_qdrant": False,
        "touches_shm": False,
        "sql_remains_authority": True,
        "qdrant_recall_refs_only": True,
    }


def main() -> int:
    args = parse_args()
    store = None
    executor = None
    config = None
    try:
        if args.live_qdrant and not args.execute:
            raise ValueError("live_qdrant requires --execute")
        embedding_report = load_json(Path(args.embedding_report))
        query_ref = args.query_ref or default_query_ref_from_embedding_report(embedding_report)
        request = SchedulerManagedQdrantRecallSqlRehydrateRequest(
            query_ref=query_ref,
            policy_decision_id=args.policy_decision_id,
            collection_name=args.collection,
            vector_dimension=args.dimension,
            limit=args.limit,
        )
        store = SQLiteSqlContextStore(args.db_path)
        store.initialize_schema()
        if args.demo_qdrant:
            executor = DemoQdrantRecallExecutor(
                sql_refs=_sql_refs_from_projection_report(Path(args.projection_report))
            )
        elif args.live_qdrant:
            executor, config = _build_live_executor(args)
        result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
            embedding_report,
            store,
            request,
            execute=args.execute,
            executor=executor,
        )
        payload = result.to_mapping()
        payload["qdrant_mode"] = _mode(args)
        payload["uses_qdrant_client_executor"] = args.live_qdrant
        payload["qdrant_recall_live"] = bool(args.live_qdrant and args.execute and payload["valid"])
        payload["touches_shm"] = False
        if config is not None:
            payload["qdrant_connection"] = config.to_mapping()
    except Exception as exc:
        payload = _failure_payload(args, exc)
    finally:
        close = getattr(executor, "close", None)
        if callable(close):
            close()
        if store is not None:
            store.close()
    if args.output:
        write_report(Path(args.output), payload)
    if args.format == "summary":
        print(
            "scheduler_managed_qdrant_recall_sql_rehydrate_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"execute={payload['execute']} dry_run={payload['dry_run']} "
            f"qdrant_mode={payload.get('qdrant_mode', '-')} "
            f"hits={payload.get('recall', {}).get('hit_count', '-') if isinstance(payload.get('recall'), dict) else '-'} "
            f"hydrated={payload.get('hydrated_count', '-')} "
            f"missing={payload.get('missing_count', '-')} "
            f"sql_refs={','.join(payload.get('sql_refs', [])) or '-'}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
