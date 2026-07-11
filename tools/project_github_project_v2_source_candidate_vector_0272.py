#!/usr/bin/env python3
"""Project one r8 durable ProjectV2 candidate through locked E5/Qdrant space."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_v2_source_candidate_vector_projection_0272 import (  # noqa: E402
    EmbeddingSpaceProfile,
    GitHubProjectV2VectorProjectionCommand,
    run_project_v2_source_candidate_vector_projection,
)
from context.scheduler_managed_db_api_sql_context_store_binding_0260 import (  # noqa: E402
    build_db_api_sql_context_store_binding_report,
)
from inference.qdrant_client_projection_executor import (  # noqa: E402
    QdrantClientConnectionConfig,
    QdrantClientEffectGate,
    build_qdrant_client_projection_executor,
)

_DEFAULT_DB_PATH = Path(".var/local/sql_context_store.sqlite3")
_DEFAULT_OUTPUT = Path(
    ".var/reports/github_project_v2_source_candidate_vector_projection_0272.json"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--durable-report", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, default=_DEFAULT_DB_PATH)
    parser.add_argument("--model-dir", default=None)
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--collection", default="autodoc_context_embeddings")
    parser.add_argument("--qdrant-url", default="http://127.0.0.1:6333")
    parser.add_argument("--prefer-grpc", action="store_true")
    parser.add_argument("--grpc-port", type=int, default=6334)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    report = _read_json(_repo_path(args.durable_report))
    binding, store = build_db_api_sql_context_store_binding_report(
        _REPO_ROOT,
        db_path=_repo_path(args.db_path),
        construct=True,
    )
    issues = list(binding.issues)
    executor = None
    try:
        if args.execute and not issues:
            config = QdrantClientConnectionConfig(
                url=args.qdrant_url,
                prefer_grpc=args.prefer_grpc,
                grpc_port=args.grpc_port,
            )
            gate = QdrantClientEffectGate(
                policy_decision_id=args.policy_decision_id,
                allow_write=True,
                allow_search=False,
            )
            executor = build_qdrant_client_projection_executor(config, gate)
        command = GitHubProjectV2VectorProjectionCommand(
            execute=args.execute,
            policy_decision_id=args.policy_decision_id,
            model_dir=args.model_dir,
            device=args.device,
        )
        profile = EmbeddingSpaceProfile(collection_name=args.collection)
        result = run_project_v2_source_candidate_vector_projection(
            report,
            store,
            command,
            profile=profile,
            qdrant_executor=executor,
        )
        payload = result.to_json_dict()
        payload["binding"] = binding.to_dict()
        if issues:
            payload["valid"] = False
            payload["issues"] = list(dict.fromkeys([*payload["issues"], *issues]))
        _write_json_atomic(_repo_path(args.output), payload)
        print(
            json.dumps(payload, indent=2, sort_keys=True)
            if args.format == "json"
            else result.to_summary()
        )
        return 0 if payload["valid"] else 2
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        payload = {
            "valid": False,
            "issues": [f"{type(exc).__name__}:{exc}"],
            "binding": binding.to_dict(),
        }
        _write_json_atomic(_repo_path(args.output), payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 2
    finally:
        close = getattr(executor, "close", None)
        if callable(close):
            close()


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"durable report must be a JSON object: {path}")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _repo_path(value: Path) -> Path:
    path = value.expanduser()
    return path if path.is_absolute() else _REPO_ROOT / path


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
