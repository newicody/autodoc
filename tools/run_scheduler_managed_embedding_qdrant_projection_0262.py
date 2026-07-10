#!/usr/bin/env python3
"""Run Scheduler-managed embedding -> Qdrant projection usage."""

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

from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (  # noqa: E402
    DemoQdrantProjectionExecutor,
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    load_json,
    run_scheduler_managed_embedding_qdrant_projection_usage,
    write_report,
)
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    build_qdrant_client_projection_executor,
)
from inference.qdrant_sql_authority_scope import (  # noqa: E402
    QdrantStrictGrpcTransportPolicy,
    SqlAuthorityScopedQdrantExecutor,
    derive_sqlite_authority_scope,
)

DEFAULT_DB_PATH = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
DEFAULT_EMBEDDING_REPORT = ROOT / ".var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--sql-authority-namespace", default="autodoc-local")
    parser.add_argument("--embedding-report", default=str(DEFAULT_EMBEDDING_REPORT))
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
    parser.add_argument("--strict-data-grpc", action="store_true")
    parser.add_argument("--qdrant-api-key-env", default="QDRANT_API_KEY")
    parser.add_argument("--collection", default="autodoc_context_embeddings")
    parser.add_argument("--dimension", type=int, default=384)
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def _mode(args: argparse.Namespace) -> str:
    if args.live_qdrant:
        return "live"
    if args.demo_qdrant:
        return "demo"
    return "none"


def _build_live_executor(args: argparse.Namespace):
    transport = QdrantStrictGrpcTransportPolicy(
        rest_admin_url=args.qdrant_url,
        grpc_port=args.qdrant_grpc_port,
        prefer_grpc=args.qdrant_prefer_grpc,
        strict_data_grpc=args.strict_data_grpc,
    )
    scope = derive_sqlite_authority_scope(
        args.db_path,
        namespace=args.sql_authority_namespace,
    )
    config = QdrantClientConnectionConfig(
        url=args.qdrant_url,
        timeout_seconds=args.qdrant_timeout_seconds,
        prefer_grpc=args.qdrant_prefer_grpc,
        grpc_port=args.qdrant_grpc_port,
    )
    gate = QdrantClientEffectGate(
        policy_decision_id=args.policy_decision_id,
        allow_write=True,
        allow_search=False,
    )
    api_key = os.environ.get(args.qdrant_api_key_env) if args.qdrant_api_key_env else None
    delegate = build_qdrant_client_projection_executor(config, gate, api_key=api_key)
    return SqlAuthorityScopedQdrantExecutor(delegate, scope), config, scope, transport


def _failure_payload(args: argparse.Namespace, exc: Exception) -> dict[str, Any]:
    return {
        "scheduler_managed_embedding_qdrant_projection_usage": True,
        "valid": False,
        "issues": [f"qdrant_client_executor:{type(exc).__name__}:{str(exc)[:500]}"],
        "execute": args.execute,
        "dry_run": not args.execute,
        "qdrant_mode": _mode(args),
        "uses_qdrant_client_executor": args.live_qdrant,
        "qdrant_projection_live": False,
        "qdrant_projection_scoped": False,
        "strict_data_grpc": False,
        "rest_admin_only": False,
        "starts_qdrant": False,
        "touches_shm": False,
        "sql_remains_authority": True,
    }


def main() -> int:
    args = parse_args()
    report = load_json(Path(args.embedding_report))
    request = SchedulerManagedEmbeddingQdrantProjectionRequest(
        policy_decision_id=args.policy_decision_id,
        collection_name=args.collection,
        vector_dimension=args.dimension,
    )
    executor = None
    config = None
    scope = None
    transport = None
    try:
        if args.live_qdrant and not args.execute:
            raise ValueError("live_qdrant requires --execute")
        if args.live_qdrant and not args.qdrant_prefer_grpc:
            raise ValueError("live_qdrant requires --qdrant-prefer-grpc")
        if args.live_qdrant and not args.strict_data_grpc:
            raise ValueError("live_qdrant requires --strict-data-grpc")
        if args.demo_qdrant:
            executor = DemoQdrantProjectionExecutor()
        elif args.live_qdrant:
            executor, config, scope, transport = _build_live_executor(args)
        result = run_scheduler_managed_embedding_qdrant_projection_usage(
            report,
            request,
            execute=args.execute,
            executor=executor,
        )
        payload = result.to_mapping()
        payload["qdrant_mode"] = _mode(args)
        payload["uses_qdrant_client_executor"] = args.live_qdrant
        payload["qdrant_projection_live"] = bool(args.live_qdrant and args.execute and payload["valid"])
        payload["qdrant_projection_scoped"] = bool(
            scope is not None and payload["qdrant_projection_live"]
        )
        payload["strict_data_grpc"] = bool(
            transport is not None and transport.strict_data_grpc
        )
        payload["rest_admin_only"] = bool(transport is not None)
        payload["touches_shm"] = False
        if config is not None:
            payload["qdrant_connection"] = config.to_mapping()
        if scope is not None:
            payload["sql_authority_ref"] = scope.authority_ref
            payload["sql_authority_scope"] = scope.to_mapping()
        if transport is not None:
            payload["qdrant_transport_policy"] = transport.to_mapping()
    except Exception as exc:
        payload = _failure_payload(args, exc)
    finally:
        close = getattr(executor, "close", None)
        if callable(close):
            close()
    if args.output:
        write_report(Path(args.output), payload)
    if args.format == "summary":
        batch = payload.get("batch", {})
        write = payload.get("write_result", {})
        print(
            "scheduler_managed_embedding_qdrant_projection_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"execute={payload['execute']} dry_run={payload['dry_run']} "
            f"qdrant_mode={payload.get('qdrant_mode', '-')} "
            f"sql_ref={payload.get('sql_ref') or '-'} "
            f"embedding_ref={payload.get('embedding_ref') or '-'} "
            f"points={batch.get('point_count', '-') if isinstance(batch, dict) else '-'} "
            f"acknowledged={write.get('acknowledged', '-') if isinstance(write, dict) else '-'}"
        )
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
