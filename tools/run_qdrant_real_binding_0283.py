#!/usr/bin/env python3
"""Preview-first CLI for the existing real Qdrant binding chain.

Default execution performs local configuration and factory readiness only.
A live collection metadata read requires ``--live-readiness``. A projection or
recall data effect additionally requires ``--execute`` and its operation-
specific authorization flag.

The tool does not create collections, start Qdrant, modify Scheduler.run or add
another transport, proxy, bus, shared-memory or hardware path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for _path in (str(SRC), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.scheduler_managed_qdrant_projection_binding_0283 import (  # noqa: E402
    QdrantControlledSchedulerProjectionCommand,
    run_qdrant_controlled_scheduler_projection_binding,
)
from context.scheduler_managed_qdrant_recall_binding_0283 import (  # noqa: E402
    QdrantControlledSchedulerRecallCommand,
    run_qdrant_controlled_scheduler_recall_binding,
)
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
)
from inference.qdrant_projection_adapter import (  # noqa: E402
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
)
from inference.qdrant_real_binding_configuration_0283 import (  # noqa: E402
    QdrantRealBindingConfigurationCommand,
    build_qdrant_real_binding_configuration,
)
from inference.qdrant_real_binding_readiness_0283 import (  # noqa: E402
    QdrantRealBindingReadinessCommand,
    inspect_qdrant_real_binding_readiness,
)
from inference.qdrant_sql_authority_scope import (  # noqa: E402
    QdrantStrictGrpcTransportPolicy,
    derive_sqlite_authority_scope,
)


DEFAULT_DB_PATH = (
    ROOT
    / ".var/local/"
    "scheduler_managed_db_api_sql_context_store_0260.sqlite3"
)
DEFAULT_OUTPUT = (
    ROOT
    / ".var/reports/"
    "qdrant_real_binding_preview_first_0283.json"
)
CLI_REPORT_SCHEMA = (
    "missipy.qdrant.real_binding_preview_first_cli.v1"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operation",
        choices=("readiness", "projection", "recall"),
        default="readiness",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Request the selected projection or recall effect.",
    )
    parser.add_argument(
        "--live-readiness",
        action="store_true",
        help="Read target collection metadata before any effect.",
    )
    parser.add_argument(
        "--authorize-projection",
        action="store_true",
        help="Explicitly authorize projection when --execute is used.",
    )
    parser.add_argument(
        "--authorize-recall",
        action="store_true",
        help="Explicitly authorize recall when --execute is used.",
    )
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--embedding-report", type=Path, default=None)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--sql-authority-namespace",
        default="autodoc-local",
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://127.0.0.1:6333",
    )
    parser.add_argument(
        "--qdrant-grpc-port",
        type=int,
        default=6334,
    )
    parser.add_argument(
        "--qdrant-timeout-seconds",
        type=float,
        default=10.0,
    )
    parser.add_argument(
        "--collection",
        default="autodoc_context_embeddings",
    )
    parser.add_argument("--vector-dimension", type=int, default=384)
    parser.add_argument("--distance", default="Cosine")
    parser.add_argument("--max-points", type=int, default=128)
    parser.add_argument("--max-recall-hits", type=int, default=32)
    parser.add_argument("--recall-limit", type=int, default=8)
    parser.add_argument(
        "--recall-oversample-factor",
        type=int,
        default=4,
    )
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
    )
    return parser.parse_args(argv)


def build_configuration(
    args: argparse.Namespace,
):
    operations = (
        ()
        if args.operation == "readiness"
        else (args.operation,)
    )
    policy_decision_id = (
        args.policy_decision_id.strip()
        or "policy:qdrant-cli-preview:0283"
    )
    effect_gate = QdrantClientEffectGate(
        policy_decision_id=policy_decision_id,
        allow_write=args.operation == "projection",
        allow_search=args.operation == "recall",
    )
    return build_qdrant_real_binding_configuration(
        QdrantRealBindingConfigurationCommand(
            connection=QdrantClientConnectionConfig(
                url=args.qdrant_url,
                timeout_seconds=args.qdrant_timeout_seconds,
                prefer_grpc=True,
                grpc_port=args.qdrant_grpc_port,
                wait_for_write=True,
                check_compatibility=True,
            ),
            effect_gate=effect_gate,
            sql_authority_scope=derive_sqlite_authority_scope(
                args.db_path,
                namespace=args.sql_authority_namespace,
            ),
            transport_policy=QdrantStrictGrpcTransportPolicy(
                rest_admin_url=args.qdrant_url,
                grpc_port=args.qdrant_grpc_port,
                prefer_grpc=True,
                strict_data_grpc=True,
            ),
            target=QdrantProjectionTarget(
                collection_name=args.collection,
                vector_dimension=args.vector_dimension,
                distance=args.distance,
            ),
            projection_policy=QdrantProjectionPolicy(
                max_points=args.max_points,
                max_recall_hits=args.max_recall_hits,
                require_sql_context_ref=True,
                require_normalized_vectors=True,
            ),
            requested_operations=operations,
            api_key_env_var=args.api_key_env.strip(),
            recall_oversample_factor=(
                args.recall_oversample_factor
            ),
        )
    )


def run_cli(
    args: argparse.Namespace,
    *,
    readiness_runner: Callable[
        ...,
        Any,
    ] = inspect_qdrant_real_binding_readiness,
    projection_runner: Callable[
        ...,
        Any,
    ] = run_qdrant_controlled_scheduler_projection_binding,
    recall_runner: Callable[
        ...,
        Any,
    ] = run_qdrant_controlled_scheduler_recall_binding,
    store_builder: Callable[
        [Path],
        Any,
    ] | None = None,
) -> dict[str, Any]:
    gate_issues = _validate_cli_gate(args)
    if gate_issues:
        return _report(
            args,
            issues=gate_issues,
        )

    try:
        configuration = build_configuration(args)
    except (OSError, TypeError, ValueError) as exc:
        return _report(
            args,
            issues=[
                "configuration build failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}"
            ],
        )

    configuration_payload = configuration.to_json_dict()
    if not configuration.valid:
        return _report(
            args,
            issues=list(configuration.issues),
            configuration=configuration_payload,
        )

    readiness = readiness_runner(
        QdrantRealBindingReadinessCommand(
            configuration=configuration,
            live_probe=args.live_readiness,
        )
    )
    readiness_payload = readiness.to_json_dict()

    if args.operation == "readiness":
        return _report(
            args,
            issues=list(readiness.issues),
            warnings=list(readiness.warnings),
            configuration=configuration_payload,
            readiness=readiness_payload,
            valid=readiness.valid,
        )

    if not readiness.local_ready:
        return _report(
            args,
            issues=list(readiness.issues),
            warnings=list(readiness.warnings),
            configuration=configuration_payload,
            readiness=readiness_payload,
        )

    if args.execute:
        effect_ready = (
            readiness.projection_ready
            if args.operation == "projection"
            else readiness.recall_ready
        )
        if not readiness.operational_ready or not effect_ready:
            issues = list(readiness.issues)
            issues.append(
                f"{args.operation} is not operationally ready"
            )
            return _report(
                args,
                issues=issues,
                warnings=list(readiness.warnings),
                configuration=configuration_payload,
                readiness=readiness_payload,
            )

    try:
        embedding_report = _read_json_object(
            args.embedding_report
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return _report(
            args,
            issues=[
                "embedding report read failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}"
            ],
            warnings=list(readiness.warnings),
            configuration=configuration_payload,
            readiness=readiness_payload,
        )

    action: Any
    store = None
    sql_store_opened = False
    sql_store_closed = False
    try:
        if args.operation == "projection":
            action = projection_runner(
                QdrantControlledSchedulerProjectionCommand(
                    embedding_report=embedding_report,
                    configuration=configuration,
                    execute=args.execute,
                )
            )
        else:
            if args.execute:
                builder = store_builder or _open_read_only_sql_store
                store = builder(args.db_path)
                sql_store_opened = True
            else:
                store = object()
            action = recall_runner(
                QdrantControlledSchedulerRecallCommand(
                    embedding_report=embedding_report,
                    store=store,
                    configuration=configuration,
                    limit=args.recall_limit,
                    execute=args.execute,
                )
            )
    except Exception as exc:
        return _report(
            args,
            issues=[
                f"{args.operation} runner failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}"
            ],
            warnings=list(readiness.warnings),
            configuration=configuration_payload,
            readiness=readiness_payload,
            sql_store_opened=sql_store_opened,
            sql_store_closed=sql_store_closed,
        )
    finally:
        if sql_store_opened and store is not None:
            try:
                store.close()
                sql_store_closed = True
            except Exception:
                sql_store_closed = False

    action_payload = action.to_json_dict()
    return _report(
        args,
        issues=list(action.issues),
        warnings=list(readiness.warnings),
        configuration=configuration_payload,
        readiness=readiness_payload,
        action=action_payload,
        valid=action.valid,
        data_effect_performed=bool(
            args.execute
            and (
                getattr(action, "qdrant_write_performed", False)
                or getattr(
                    action,
                    "qdrant_search_performed",
                    False,
                )
            )
        ),
        sql_store_opened=sql_store_opened,
        sql_store_closed=sql_store_closed,
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    payload = run_cli(args)
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_summary(payload))
    return 0 if payload["valid"] else 2


def _validate_cli_gate(
    args: argparse.Namespace,
) -> list[str]:
    issues: list[str] = []

    if args.operation == "readiness" and args.execute:
        issues.append(
            "--execute is not valid for readiness operation"
        )

    if (
        args.operation in {"projection", "recall"}
        and args.embedding_report is None
    ):
        issues.append(
            "--embedding-report is required for projection or recall"
        )

    if args.execute and not args.live_readiness:
        issues.append(
            "--execute requires --live-readiness"
        )

    if args.operation == "projection" and args.execute:
        if not args.authorize_projection:
            issues.append(
                "projection execute requires --authorize-projection"
            )
        if args.authorize_recall:
            issues.append(
                "--authorize-recall is invalid for projection"
            )

    if args.operation == "recall" and args.execute:
        if not args.authorize_recall:
            issues.append(
                "recall execute requires --authorize-recall"
            )
        if args.authorize_projection:
            issues.append(
                "--authorize-projection is invalid for recall"
            )

    if not args.execute and (
        args.authorize_projection or args.authorize_recall
    ):
        issues.append(
            "authorization flags require --execute"
        )

    if args.execute and not args.policy_decision_id.strip():
        issues.append(
            "--execute requires --policy-decision-id"
        )

    if args.vector_dimension <= 0:
        issues.append("--vector-dimension must be > 0")
    if args.max_points <= 0:
        issues.append("--max-points must be > 0")
    if args.max_recall_hits <= 0:
        issues.append("--max-recall-hits must be > 0")
    if args.recall_limit <= 0:
        issues.append("--recall-limit must be > 0")
    if args.recall_limit > args.max_recall_hits:
        issues.append(
            "--recall-limit must not exceed --max-recall-hits"
        )
    return issues


def _open_read_only_sql_store(
    path: Path,
) -> Any:
    from context.sql_context_store import (
        DbApiSqlContextStore,
        SqlContextStorePolicy,
    )

    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise ValueError(
            f"SQL authority database not found: {resolved}"
        )
    connection = sqlite3.connect(
        resolved.as_uri() + "?mode=ro",
        uri=True,
    )
    return DbApiSqlContextStore(
        connection,
        SqlContextStorePolicy(
            paramstyle="qmark",
            auto_commit=False,
        ),
    )


def _read_json_object(
    path: Path | None,
) -> Mapping[str, Any]:
    if path is None:
        raise ValueError("embedding report path is required")
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    if not isinstance(payload, Mapping):
        raise ValueError(
            "embedding report must decode to an object"
        )
    return payload


def _report(
    args: argparse.Namespace,
    *,
    issues: list[str],
    warnings: list[str] | None = None,
    configuration: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
    action: Mapping[str, Any] | None = None,
    valid: bool = False,
    data_effect_performed: bool = False,
    sql_store_opened: bool = False,
    sql_store_closed: bool = False,
) -> dict[str, Any]:
    return {
        "schema": CLI_REPORT_SCHEMA,
        "valid": bool(valid and not issues),
        "issues": list(issues),
        "warnings": list(warnings or ()),
        "operation": args.operation,
        "execute_requested": args.execute,
        "live_readiness_requested": args.live_readiness,
        "authorization": {
            "projection": args.authorize_projection,
            "recall": args.authorize_recall,
            "policy_decision_id_present": bool(
                args.policy_decision_id.strip()
            ),
        },
        "configuration": dict(configuration or {}),
        "readiness": dict(readiness or {}),
        "action": dict(action or {}),
        "data_effect_performed": data_effect_performed,
        "sql_store": {
            "opened": sql_store_opened,
            "closed": sql_store_closed,
            "read_only_when_opened": True,
        },
        "boundaries": {
            "preview_first": True,
            "live_readiness_is_explicit": True,
            "operation_authorization_is_explicit": True,
            "projection_authorization_separate": True,
            "recall_authorization_separate": True,
            "collection_created": False,
            "collection_updated": False,
            "collection_deleted": False,
            "qdrant_started": False,
            "scheduler_modified": False,
            "new_scheduler_added": False,
            "new_qdrant_executor_added": False,
            "new_transport_added": False,
            "control_proxy_integrated": False,
            "event_bus_integrated": False,
            "shm_or_mmio_integrated": False,
            "projects_repository_change_required": False,
        },
    }


def _summary(payload: Mapping[str, Any]) -> str:
    readiness = payload.get("readiness")
    if not isinstance(readiness, Mapping):
        readiness = {}
    return " ".join(
        (
            f"qdrant_cli_valid={payload['valid']}",
            f"issues={len(payload['issues'])}",
            f"operation={payload['operation']}",
            f"execute={payload['execute_requested']}",
            (
                "live_readiness="
                f"{payload['live_readiness_requested']}"
            ),
            (
                "operational_ready="
                f"{readiness.get('operational_ready', False)}"
            ),
            (
                "data_effect_performed="
                f"{payload['data_effect_performed']}"
            ),
        )
    )


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    output = path.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(
        output.suffix + ".tmp"
    )
    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
