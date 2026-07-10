#!/usr/bin/env python3
"""Check SQL-authority scope and strict gRPC transport without network IO."""

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

from inference.qdrant_sql_authority_scope import (  # noqa: E402
    QdrantStrictGrpcTransportPolicy,
    derive_sqlite_authority_scope,
)

DEFAULT_DB_PATH = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
DEFAULT_OUTPUT = ROOT / ".var/reports/qdrant_sql_authority_scope_strict_grpc_0271.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--sql-authority-namespace", default="autodoc-local")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--qdrant-grpc-port", type=int, default=6334)
    parser.add_argument(
        "--qdrant-prefer-grpc",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--strict-data-grpc",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def build_report(args: argparse.Namespace) -> dict[str, object]:
    issues: list[str] = []
    scope = None
    transport = None
    try:
        scope = derive_sqlite_authority_scope(
            args.db_path,
            namespace=args.sql_authority_namespace,
        )
        transport = QdrantStrictGrpcTransportPolicy(
            rest_admin_url=args.qdrant_url,
            grpc_port=args.qdrant_grpc_port,
            prefer_grpc=args.qdrant_prefer_grpc,
            strict_data_grpc=args.strict_data_grpc,
        )
    except (TypeError, ValueError) as exc:
        issues.append(f"{type(exc).__name__}:{exc}")

    return {
        "qdrant_sql_authority_scope_strict_grpc": True,
        "valid": not issues,
        "issues": issues,
        "scope": scope.to_mapping() if scope is not None else None,
        "transport": transport.to_mapping() if transport is not None else None,
        "network_used": False,
        "qdrant_called": False,
        "touches_shm": False,
        "starts_qdrant": False,
        "sql_remains_authority": True,
        "integration_required": True,
        "next": "0271-r5-bind-sql-authority-scope-to-live-qdrant",
    }


def main() -> int:
    args = parse_args()
    report = build_report(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if args.format == "summary":
        scope = report.get("scope") or {}
        transport = report.get("transport") or {}
        print(
            "qdrant_sql_authority_scope_ready="
            f"{report['valid']} issues={len(report['issues'])} "
            f"authority_ref={scope.get('authority_ref', '-')} "
            f"data_transport={transport.get('requested_data_transport', '-')} "
            f"strict_data_grpc={transport.get('strict_data_grpc', False)} "
            f"rest_admin_only={transport.get('rest_admin_only', False)} "
            "network_used=False touches_shm=False"
        )
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
