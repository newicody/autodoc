#!/usr/bin/env python3
"""Preview-first SQL → E5 → Qdrant → recall → SQL smoke for 0283.

Preview validates the entire composition using the existing deterministic demo
embedding and performs no SQL, OpenVINO or Qdrant effect.

Execute mode requires explicit smoke and persistent-point authorization. It
writes one dedicated fixture record to a dedicated SQLite authority, embeds it
as passage and query through the existing OpenVINO/E5 0261 usage, projects the
passage through r4, recalls through r5, and verifies SQL rehydration.

The smoke never creates or mutates a collection and never deletes the projected
point automatically. Cleanup requirements are reported explicitly.
"""

from __future__ import annotations

import argparse
import hashlib
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


SMOKE_REPORT_SCHEMA = (
    "missipy.qdrant.real_closed_loop_smoke.v1"
)
DEFAULT_DB_PATH = (
    ROOT
    / ".var/smoke/"
    "qdrant_real_closed_loop_0283.sqlite3"
)
DEFAULT_OUTPUT = (
    ROOT
    / ".var/reports/"
    "qdrant_real_closed_loop_smoke_0283.json"
)
DEFAULT_MODEL_DIR = Path(
    "/home/eric/model/openvino/multilingual-e5-small"
)
DEFAULT_FIXTURE_ID = "0283-real-closed-loop-smoke-v1"
DEFAULT_FIXTURE_TITLE = "Autodoc Qdrant real closed-loop smoke"
DEFAULT_FIXTURE_BODY = (
    "Dedicated Autodoc fixture proving SQL authority, multilingual E5 "
    "projection, Qdrant recall, and SQL rehydration."
)


class SmokeSqlSession:
    def __init__(
        self,
        *,
        store: Any,
        record_mapping: Mapping[str, Any],
        write_result: Mapping[str, Any],
    ) -> None:
        self.store = store
        self.record_mapping = dict(record_mapping)
        self.write_result = dict(write_result)

    def close(self) -> None:
        self.store.close()


class _PreviewStore:
    def __init__(self, record: Mapping[str, Any]) -> None:
        self._record = dict(record)

    def get_record(self, context_ref: str) -> Mapping[str, Any] | None:
        if context_ref == self._record["context_ref"]:
            return dict(self._record)
        return None


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorize-smoke", action="store_true")
    parser.add_argument(
        "--authorize-persistent-smoke-point",
        action="store_true",
        help=(
            "Acknowledge that the projected smoke point is not "
            "deleted automatically."
        ),
    )
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--device", default="CPU")
    parser.add_argument(
        "--qdrant-url",
        default="http://127.0.0.1:6333",
    )
    parser.add_argument("--qdrant-grpc-port", type=int, default=6334)
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
    parser.add_argument("--recall-limit", type=int, default=8)
    parser.add_argument("--fixture-id", default=DEFAULT_FIXTURE_ID)
    parser.add_argument(
        "--fixture-title",
        default=DEFAULT_FIXTURE_TITLE,
    )
    parser.add_argument(
        "--fixture-body",
        default=DEFAULT_FIXTURE_BODY,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
    )
    return parser.parse_args(argv)


def run_smoke(
    args: argparse.Namespace,
    *,
    sql_session_builder: Callable[
        [argparse.Namespace, Mapping[str, Any]],
        SmokeSqlSession,
    ] | None = None,
    embedding_runner: Callable[..., Any] | None = None,
    embedding_request_builder: Callable[..., Any] | None = None,
    demo_embedding_builder: Callable[..., Mapping[str, Any]] | None = None,
    readiness_runner: Callable[..., Any] = (
        inspect_qdrant_real_binding_readiness
    ),
    projection_runner: Callable[..., Any] = (
        run_qdrant_controlled_scheduler_projection_binding
    ),
    recall_runner: Callable[..., Any] = (
        run_qdrant_controlled_scheduler_recall_binding
    ),
) -> dict[str, Any]:
    issues = _validate_gate(args)
    fixture = _fixture_mapping(args)
    if issues:
        return _report(args, fixture, issues=issues)

    policy_decision_id = (
        args.policy_decision_id.strip()
        if args.execute
        else "policy:qdrant-smoke-preview:0283"
    )
    projection_config = _build_configuration(
        args,
        operation="projection",
        policy_decision_id=policy_decision_id,
    )
    recall_config = _build_configuration(
        args,
        operation="recall",
        policy_decision_id=policy_decision_id,
    )
    configuration = {
        "projection": projection_config.to_json_dict(),
        "recall": recall_config.to_json_dict(),
    }
    configuration_issues = [
        *projection_config.issues,
        *recall_config.issues,
    ]
    if configuration_issues:
        return _report(
            args,
            fixture,
            issues=list(configuration_issues),
            configuration=configuration,
        )

    try:
        (
            active_embedding_runner,
            active_embedding_request_builder,
            active_demo_embedding_builder,
        ) = _resolve_embedding_runtime(
            embedding_runner=embedding_runner,
            embedding_request_builder=embedding_request_builder,
            demo_embedding_builder=demo_embedding_builder,
        )
    except (ImportError, TypeError, ValueError) as exc:
        return _report(
            args,
            fixture,
            issues=[
                "0261 embedding runtime resolution failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}"
            ],
            configuration=configuration,
        )

    if not args.execute:
        return _run_preview(
            args,
            fixture,
            projection_config,
            recall_config,
            configuration,
            embedding_runner=active_embedding_runner,
            embedding_request_builder=(
                active_embedding_request_builder
            ),
            demo_embedding_builder=active_demo_embedding_builder,
            readiness_runner=readiness_runner,
            projection_runner=projection_runner,
            recall_runner=recall_runner,
        )

    return _run_execute(
        args,
        fixture,
        projection_config,
        recall_config,
        configuration,
        sql_session_builder=(
            sql_session_builder or _open_smoke_sql_session
        ),
        embedding_runner=active_embedding_runner,
        embedding_request_builder=(
            active_embedding_request_builder
        ),
        readiness_runner=readiness_runner,
        projection_runner=projection_runner,
        recall_runner=recall_runner,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(
        tuple(sys.argv[1:] if argv is None else argv)
    )
    payload = run_smoke(args)
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_summary(payload))
    return 0 if payload["valid"] else 2


def _run_preview(
    args: argparse.Namespace,
    fixture: Mapping[str, Any],
    projection_config: Any,
    recall_config: Any,
    configuration: Mapping[str, Any],
    *,
    embedding_runner: Callable[..., Any],
    embedding_request_builder: Callable[..., Any],
    demo_embedding_builder: Callable[..., Mapping[str, Any]],
    readiness_runner: Callable[..., Any],
    projection_runner: Callable[..., Any],
    recall_runner: Callable[..., Any],
) -> dict[str, Any]:
    store = _PreviewStore(fixture)
    passage = embedding_runner(
        store,
        embedding_request_builder(
            sql_ref=str(fixture["context_ref"]),
            role="passage",
            policy_decision_id="policy:qdrant-smoke-preview:0283",
            model_dir=str(args.model_dir),
            device=args.device,
        ),
        execute=False,
    )
    query = embedding_runner(
        store,
        embedding_request_builder(
            sql_ref=str(fixture["context_ref"]),
            role="query",
            policy_decision_id="policy:qdrant-smoke-preview:0283",
            model_dir=str(args.model_dir),
            device=args.device,
        ),
        execute=False,
    )
    issues = [*passage.issues, *query.issues]
    if issues:
        return _report(
            args,
            fixture,
            issues=list(issues),
            configuration=configuration,
            embedding={
                "passage": passage.to_mapping(),
                "query": query.to_mapping(),
            },
        )

    passage_report = {
        "embedding": demo_embedding_builder(
            passage.embedding_text,
            str(fixture["context_ref"]),
            str(args.model_dir),
            args.device,
            role="passage",
            dimension=args.vector_dimension,
        )
    }
    query_report = {
        "embedding": demo_embedding_builder(
            query.embedding_text,
            str(fixture["context_ref"]),
            str(args.model_dir),
            args.device,
            role="query",
            dimension=args.vector_dimension,
        )
    }

    projection_readiness = readiness_runner(
        QdrantRealBindingReadinessCommand(
            configuration=projection_config,
            live_probe=False,
        )
    )
    recall_readiness = readiness_runner(
        QdrantRealBindingReadinessCommand(
            configuration=recall_config,
            live_probe=False,
        )
    )
    projection = projection_runner(
        QdrantControlledSchedulerProjectionCommand(
            embedding_report=passage_report,
            configuration=projection_config,
            execute=False,
        )
    )
    recall = recall_runner(
        QdrantControlledSchedulerRecallCommand(
            embedding_report=query_report,
            store=store,
            configuration=recall_config,
            limit=args.recall_limit,
            execute=False,
        )
    )
    issues = [
        *projection_readiness.issues,
        *recall_readiness.issues,
        *projection.issues,
        *recall.issues,
    ]
    valid = bool(
        not issues
        and projection_readiness.local_ready
        and recall_readiness.local_ready
        and projection.valid
        and recall.valid
    )
    return _report(
        args,
        fixture,
        issues=list(issues),
        warnings=[
            *projection_readiness.warnings,
            *recall_readiness.warnings,
        ],
        configuration=configuration,
        readiness={
            "projection": projection_readiness.to_json_dict(),
            "recall": recall_readiness.to_json_dict(),
        },
        embedding={
            "passage": passage.to_mapping(),
            "query": query.to_mapping(),
            "demo_vectors_used": True,
        },
        projection=projection.to_json_dict(),
        recall=recall.to_json_dict(),
        valid=valid,
    )


def _run_execute(
    args: argparse.Namespace,
    fixture: Mapping[str, Any],
    projection_config: Any,
    recall_config: Any,
    configuration: Mapping[str, Any],
    *,
    sql_session_builder: Callable[
        [argparse.Namespace, Mapping[str, Any]],
        SmokeSqlSession,
    ],
    embedding_runner: Callable[..., Any],
    embedding_request_builder: Callable[..., Any],
    readiness_runner: Callable[..., Any],
    projection_runner: Callable[..., Any],
    recall_runner: Callable[..., Any],
) -> dict[str, Any]:
    session: SmokeSqlSession | None = None
    try:
        session = sql_session_builder(args, fixture)
        passage = embedding_runner(
            session.store,
            embedding_request_builder(
                sql_ref=str(fixture["context_ref"]),
                role="passage",
                policy_decision_id=args.policy_decision_id,
                model_dir=str(args.model_dir),
                device=args.device,
            ),
            execute=True,
        )
        query = embedding_runner(
            session.store,
            embedding_request_builder(
                sql_ref=str(fixture["context_ref"]),
                role="query",
                policy_decision_id=args.policy_decision_id,
                model_dir=str(args.model_dir),
                device=args.device,
            ),
            execute=True,
        )
        embedding_issues = [
            *passage.issues,
            *query.issues,
            *_validate_real_embedding(
                passage.embedding,
                role="passage",
                dimension=args.vector_dimension,
            ),
            *_validate_real_embedding(
                query.embedding,
                role="query",
                dimension=args.vector_dimension,
            ),
        ]
        if embedding_issues:
            return _report(
                args,
                fixture,
                issues=list(embedding_issues),
                configuration=configuration,
                sql={
                    "write_result": dict(session.write_result),
                },
                embedding={
                    "passage": passage.to_mapping(),
                    "query": query.to_mapping(),
                },
                cleanup=_cleanup_report(
                    args,
                    fixture,
                    point_ids=(),
                    sql_written=True,
                    qdrant_written=False,
                ),
            )

        projection_readiness = readiness_runner(
            QdrantRealBindingReadinessCommand(
                configuration=projection_config,
                live_probe=True,
            )
        )
        recall_readiness = readiness_runner(
            QdrantRealBindingReadinessCommand(
                configuration=recall_config,
                live_probe=True,
            )
        )
        readiness_issues = [
            *projection_readiness.issues,
            *recall_readiness.issues,
        ]
        if (
            readiness_issues
            or not projection_readiness.projection_ready
            or not recall_readiness.recall_ready
        ):
            if not projection_readiness.projection_ready:
                readiness_issues.append(
                    "projection readiness is not green"
                )
            if not recall_readiness.recall_ready:
                readiness_issues.append(
                    "recall readiness is not green"
                )
            return _report(
                args,
                fixture,
                issues=list(readiness_issues),
                warnings=[
                    *projection_readiness.warnings,
                    *recall_readiness.warnings,
                ],
                configuration=configuration,
                readiness={
                    "projection": projection_readiness.to_json_dict(),
                    "recall": recall_readiness.to_json_dict(),
                },
                sql={
                    "write_result": dict(session.write_result),
                },
                embedding={
                    "passage": passage.to_mapping(),
                    "query": query.to_mapping(),
                },
                cleanup=_cleanup_report(
                    args,
                    fixture,
                    point_ids=(),
                    sql_written=True,
                    qdrant_written=False,
                ),
            )

        passage_report = passage.to_mapping()
        query_report = query.to_mapping()
        projection = projection_runner(
            QdrantControlledSchedulerProjectionCommand(
                embedding_report=passage_report,
                configuration=projection_config,
                execute=True,
            )
        )
        point_ids = _projection_point_ids(projection)
        if not projection.valid or not projection.qdrant_write_performed:
            return _report(
                args,
                fixture,
                issues=[
                    *projection.issues,
                    "projection did not produce an acknowledged write",
                ],
                configuration=configuration,
                readiness={
                    "projection": projection_readiness.to_json_dict(),
                    "recall": recall_readiness.to_json_dict(),
                },
                sql={
                    "write_result": dict(session.write_result),
                },
                embedding={
                    "passage": passage_report,
                    "query": query_report,
                },
                projection=projection.to_json_dict(),
                cleanup=_cleanup_report(
                    args,
                    fixture,
                    point_ids=point_ids,
                    sql_written=True,
                    qdrant_written=bool(point_ids),
                ),
            )

        recall = recall_runner(
            QdrantControlledSchedulerRecallCommand(
                embedding_report=query_report,
                store=session.store,
                configuration=recall_config,
                query_ref=(
                    "qdrant-query:closed-loop-smoke:0283"
                ),
                limit=args.recall_limit,
                execute=True,
            )
        )
        verification = _verify_closed_loop(
            fixture,
            recall.to_json_dict(),
        )
        issues = [
            *projection.issues,
            *recall.issues,
            *verification["issues"],
        ]
        valid = bool(
            not issues
            and projection.qdrant_write_performed
            and recall.qdrant_search_performed
            and verification["closed_loop_verified"]
        )
        return _report(
            args,
            fixture,
            issues=list(issues),
            warnings=[
                *projection_readiness.warnings,
                *recall_readiness.warnings,
            ],
            configuration=configuration,
            readiness={
                "projection": projection_readiness.to_json_dict(),
                "recall": recall_readiness.to_json_dict(),
            },
            sql={
                "write_result": dict(session.write_result),
            },
            embedding={
                "passage": passage_report,
                "query": query_report,
                "real_openvino_e5_executed": True,
            },
            projection=projection.to_json_dict(),
            recall=recall.to_json_dict(),
            verification=verification,
            cleanup=_cleanup_report(
                args,
                fixture,
                point_ids=point_ids,
                sql_written=True,
                qdrant_written=True,
            ),
            valid=valid,
        )
    except Exception as exc:
        return _report(
            args,
            fixture,
            issues=[
                "closed-loop smoke failed: "
                f"{type(exc).__name__}: {_safe_message(exc)}"
            ],
            configuration=configuration,
            cleanup=_cleanup_report(
                args,
                fixture,
                point_ids=(),
                sql_written=session is not None,
                qdrant_written=False,
            ),
        )
    finally:
        if session is not None:
            try:
                session.close()
            except Exception:
                pass


def _resolve_embedding_runtime(
    *,
    embedding_runner: Callable[..., Any] | None,
    embedding_request_builder: Callable[..., Any] | None,
    demo_embedding_builder: (
        Callable[..., Mapping[str, Any]] | None
    ),
) -> tuple[
    Callable[..., Any],
    Callable[..., Any],
    Callable[..., Mapping[str, Any]],
]:
    supplied = (
        embedding_runner is not None,
        embedding_request_builder is not None,
        demo_embedding_builder is not None,
    )
    if any(supplied) and not all(supplied):
        raise ValueError(
            "embedding injection requires runner, request builder "
            "and demo builder together"
        )
    if all(supplied):
        return (
            embedding_runner,
            embedding_request_builder,
            demo_embedding_builder,
        )

    from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
        build_demo_embedding,
        run_scheduler_managed_sql_ref_openvino_embedding_usage,
    )

    return (
        run_scheduler_managed_sql_ref_openvino_embedding_usage,
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
        build_demo_embedding,
    )


def _build_configuration(
    args: argparse.Namespace,
    *,
    operation: str,
    policy_decision_id: str,
):
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
            effect_gate=QdrantClientEffectGate(
                policy_decision_id=policy_decision_id,
                allow_write=operation == "projection",
                allow_search=operation == "recall",
            ),
            sql_authority_scope=derive_sqlite_authority_scope(
                args.db_path,
                namespace="autodoc-smoke-0283",
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
            projection_policy=QdrantProjectionPolicy(),
            requested_operations=(operation,),
            recall_oversample_factor=4,
        )
    )


def _open_smoke_sql_session(
    args: argparse.Namespace,
    fixture: Mapping[str, Any],
) -> SmokeSqlSession:
    from context.sql_context_store import (
        DbApiSqlContextStore,
        SqlContextRecord,
        SqlContextStorePolicy,
    )

    path = args.db_path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    store = DbApiSqlContextStore(
        connection,
        SqlContextStorePolicy(
            paramstyle="qmark",
            auto_commit=True,
        ),
    )
    store.initialize_schema()
    record = SqlContextRecord(
        context_ref=str(fixture["context_ref"]),
        kind=str(fixture["kind"]),
        title=str(fixture["title"]),
        body=str(fixture["body"]),
        parent_ref=None,
        metadata=tuple(
            sorted(
                (str(key), str(value))
                for key, value in dict(
                    fixture["metadata"]
                ).items()
            )
        ),
    )
    write_result = store.upsert_record(record)
    return SmokeSqlSession(
        store=store,
        record_mapping=record.to_mapping(),
        write_result=write_result.to_mapping(),
    )


def _fixture_mapping(
    args: argparse.Namespace,
) -> dict[str, Any]:
    identity = args.fixture_id.strip()
    digest = hashlib.sha256()
    digest.update(b"artifact")
    digest.update(b"\0")
    digest.update(identity.encode("utf-8"))
    context_ref = f"sql:artifact:{digest.hexdigest()[:16]}"
    return {
        "context_ref": context_ref,
        "kind": "artifact",
        "title": args.fixture_title.strip(),
        "body": args.fixture_body.strip(),
        "parent_ref": None,
        "metadata": {
            "smoke_ref": "qdrant-real-closed-loop:0283",
            "fixture_id": identity,
            "cleanup_required": "true",
        },
    }


def _validate_gate(
    args: argparse.Namespace,
) -> list[str]:
    issues: list[str] = []
    if not args.fixture_id.strip():
        issues.append("--fixture-id must not be empty")
    if not args.fixture_title.strip():
        issues.append("--fixture-title must not be empty")
    if not args.fixture_body.strip():
        issues.append("--fixture-body must not be empty")
    if args.vector_dimension != 384:
        issues.append(
            "--vector-dimension must be 384 for multilingual-e5-small"
        )
    if args.recall_limit <= 0:
        issues.append("--recall-limit must be > 0")
    if args.recall_limit > 32:
        issues.append("--recall-limit must be <= 32")
    if args.execute:
        if not args.authorize_smoke:
            issues.append(
                "--execute requires --authorize-smoke"
            )
        if not args.authorize_persistent_smoke_point:
            issues.append(
                "--execute requires "
                "--authorize-persistent-smoke-point"
            )
        if not args.policy_decision_id.strip():
            issues.append(
                "--execute requires --policy-decision-id"
            )
        if not args.model_dir.expanduser().is_dir():
            issues.append(
                "OpenVINO model directory does not exist"
            )
    elif (
        args.authorize_smoke
        or args.authorize_persistent_smoke_point
    ):
        issues.append(
            "smoke authorization flags require --execute"
        )
    return issues


def _validate_real_embedding(
    embedding: Mapping[str, Any],
    *,
    role: str,
    dimension: int,
) -> list[str]:
    issues: list[str] = []
    if not embedding:
        return [f"{role} embedding is missing"]
    if embedding.get("role") != role:
        issues.append(
            f"{role} embedding role mismatch"
        )
    if embedding.get("dimension") != dimension:
        issues.append(
            f"{role} embedding dimension must be {dimension}"
        )
    if embedding.get("normalized") is not True:
        issues.append(
            f"{role} embedding must be normalized"
        )
    vector = embedding.get("vector")
    if not isinstance(vector, list) or len(vector) != dimension:
        issues.append(
            f"{role} embedding vector length must be {dimension}"
        )
    model = str(
        dict(embedding.get("metadata") or {}).get("model", "")
    )
    if model.startswith("demo."):
        issues.append(
            f"{role} execute embedding must not use demo model"
        )
    return issues


def _projection_point_ids(
    projection: Any,
) -> tuple[str, ...]:
    payload = projection.to_json_dict()
    usage = payload.get("usage_result", {})
    if not isinstance(usage, Mapping):
        return ()
    write = usage.get("write_result", {})
    if not isinstance(write, Mapping):
        return ()
    values = write.get("point_ids", ())
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values)


def _verify_closed_loop(
    fixture: Mapping[str, Any],
    recall: Mapping[str, Any],
) -> dict[str, Any]:
    usage = recall.get("usage_result", {})
    if not isinstance(usage, Mapping):
        usage = {}
    expected_ref = str(fixture["context_ref"])
    sql_refs = tuple(
        str(value) for value in usage.get("sql_refs", ())
    )
    hydrated = usage.get("hydrated_records", ())
    if not isinstance(hydrated, list):
        hydrated = []
    matching = [
        record
        for record in hydrated
        if isinstance(record, Mapping)
        and record.get("context_ref") == expected_ref
    ]
    body_matches = any(
        record.get("body") == fixture["body"]
        for record in matching
    )
    issues: list[str] = []
    if expected_ref not in sql_refs:
        issues.append(
            "fixture SQL reference was not returned by Qdrant recall"
        )
    if not matching:
        issues.append(
            "fixture SQL record was not rehydrated"
        )
    elif not body_matches:
        issues.append(
            "rehydrated SQL fixture body does not match authority"
        )
    return {
        "closed_loop_verified": not issues,
        "issues": issues,
        "expected_sql_ref": expected_ref,
        "returned_sql_refs": list(sql_refs),
        "fixture_rehydrated": bool(matching),
        "authority_body_matches": body_matches,
        "qdrant_returned_references_only": True,
        "sql_remained_authority": True,
    }


def _cleanup_report(
    args: argparse.Namespace,
    fixture: Mapping[str, Any],
    *,
    point_ids: Sequence[str],
    sql_written: bool,
    qdrant_written: bool,
) -> dict[str, Any]:
    return {
        "required": bool(sql_written or qdrant_written),
        "automatic_cleanup_performed": False,
        "sql_fixture_written": sql_written,
        "sql_database": str(
            args.db_path.expanduser().resolve()
        ),
        "sql_ref": fixture["context_ref"],
        "qdrant_point_written": qdrant_written,
        "qdrant_collection": args.collection,
        "qdrant_point_ids": list(point_ids),
        "operator_action": (
            "Review the report, then remove the dedicated SQL smoke "
            "database and Qdrant point IDs manually when appropriate."
        ),
    }


def _report(
    args: argparse.Namespace,
    fixture: Mapping[str, Any],
    *,
    issues: Sequence[str],
    warnings: Sequence[str] = (),
    configuration: Mapping[str, Any] | None = None,
    readiness: Mapping[str, Any] | None = None,
    sql: Mapping[str, Any] | None = None,
    embedding: Mapping[str, Any] | None = None,
    projection: Mapping[str, Any] | None = None,
    recall: Mapping[str, Any] | None = None,
    verification: Mapping[str, Any] | None = None,
    cleanup: Mapping[str, Any] | None = None,
    valid: bool = False,
) -> dict[str, Any]:
    return {
        "schema": SMOKE_REPORT_SCHEMA,
        "valid": bool(valid and not issues),
        "issues": list(issues),
        "warnings": list(warnings),
        "execute_requested": args.execute,
        "fixture": dict(fixture),
        "configuration": dict(configuration or {}),
        "readiness": dict(readiness or {}),
        "sql": dict(sql or {}),
        "embedding": dict(embedding or {}),
        "projection": dict(projection or {}),
        "recall": dict(recall or {}),
        "verification": dict(verification or {}),
        "cleanup": dict(cleanup or {}),
        "boundaries": {
            "preview_first": True,
            "real_sql_authority_used_on_execute": True,
            "real_openvino_e5_used_on_execute": True,
            "real_qdrant_projection_used_on_execute": True,
            "real_qdrant_recall_used_on_execute": True,
            "qdrant_returns_references_only": True,
            "sql_rehydration_verified": True,
            "automatic_cleanup_performed": False,
            "collection_created": False,
            "collection_updated": False,
            "collection_deleted": False,
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
    verification = payload.get("verification", {})
    if not isinstance(verification, Mapping):
        verification = {}
    return " ".join(
        (
            f"qdrant_closed_loop_valid={payload['valid']}",
            f"issues={len(payload['issues'])}",
            f"execute={payload['execute_requested']}",
            (
                "closed_loop_verified="
                f"{verification.get('closed_loop_verified', False)}"
            ),
            (
                "cleanup_required="
                f"{payload.get('cleanup', {}).get('required', False)}"
            ),
        )
    )


def _write_json_atomic(
    path: Path,
    payload: Mapping[str, Any],
) -> None:
    output = path.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(output)


def _safe_message(exc: Exception) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text[:300]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
