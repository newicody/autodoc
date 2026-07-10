#!/usr/bin/env python3
"""Run Scheduler-managed embedding -> Qdrant projection usage."""

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

from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (  # noqa: E402
    DemoQdrantProjectionExecutor,
    SchedulerManagedEmbeddingQdrantProjectionRequest,
    load_json,
    run_scheduler_managed_embedding_qdrant_projection_usage,
    write_report,
)


DEFAULT_EMBEDDING_REPORT = ROOT / ".var/reports/scheduler_managed_sql_ref_openvino_embedding_0261.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-report", default=str(DEFAULT_EMBEDDING_REPORT))
    parser.add_argument("--output", default="")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--demo-qdrant", action="store_true")
    parser.add_argument("--collection", default="autodoc_context_embeddings")
    parser.add_argument("--dimension", type=int, default=384)
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_json(Path(args.embedding_report))
    request = SchedulerManagedEmbeddingQdrantProjectionRequest(
        policy_decision_id=args.policy_decision_id,
        collection_name=args.collection,
        vector_dimension=args.dimension,
    )
    executor = DemoQdrantProjectionExecutor() if args.demo_qdrant else None
    result = run_scheduler_managed_embedding_qdrant_projection_usage(
        report,
        request,
        execute=args.execute,
        executor=executor,
    )
    payload = result.to_mapping()

    if args.output:
        write_report(Path(args.output), payload)

    if args.format == "summary":
        batch = payload.get("batch", {})
        write = payload.get("write_result", {})
        print(
            "scheduler_managed_embedding_qdrant_projection_valid="
            f"{payload['valid']} issues={len(payload['issues'])} "
            f"execute={payload['execute']} dry_run={payload['dry_run']} "
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
