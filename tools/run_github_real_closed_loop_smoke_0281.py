#!/usr/bin/env python3
"""Run the real local 0281 closed-loop smoke and write publication preview.

Input is the same INI consumed by the 0167/0168 fetch path. The tool requires
a ready 0281-r3 run-group report and resolves all bytes from
``server_dataset.raw``. It never consumes a Git checkout or a manual download
directory.

The tool owns only the standalone process lifecycle of the existing platform
Scheduler implementation. It does not introduce a laboratory Scheduler or
mutate GitHub.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_artifact_server_fetch_config import (  # noqa: E402
    load_github_artifact_server_fetch_config,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (  # noqa: E402
    EmbeddingSpaceProfile,
)
from context.github_real_closed_loop_smoke_0281 import (  # noqa: E402
    GitHubRealClosedLoopSmokeCommand,
    load_imported_github_run_bundle,
    run_github_real_closed_loop_smoke,
)
from context.scheduler_laboratory_visit_binding_0274 import (  # noqa: E402
    register_laboratory_visit_handler,
)
from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (  # noqa: E402
    DemoQdrantProjectionExecutor,
)
from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (  # noqa: E402
    DemoQdrantRecallExecutor,
)
from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (  # noqa: E402
    build_embedding_mapping,
)
from context.sql_context_store import SQLiteSqlContextStore  # noqa: E402
from kernel.dispatcher import Dispatcher  # noqa: E402
from kernel.event_bus import EventBus  # noqa: E402
from kernel.queue import PriorityQueue  # noqa: E402
from kernel.registry import Registry  # noqa: E402
from kernel.scheduler import Scheduler  # noqa: E402


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the imported GitHub run-group -> existing Scheduler -> "
            "fake laboratory -> publication preview smoke."
        )
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument(
        "--policy-decision-id",
        default="",
        help=(
            "Defaults to policy:0281:r7:<repository-slug>:<run-id>:"
            "<issue-number>."
        ),
    )
    parser.add_argument(
        "--operator-reason",
        default=(
            "Operator-approved real local closed-loop smoke for an imported "
            "GitHub request and Copilot advisory."
        ),
    )
    parser.add_argument("--allow-missing-advisory", action="store_true")
    parser.add_argument("--no-observations", action="store_true")
    parser.add_argument("--no-sql-replay", action="store_true")
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = load_github_artifact_server_fetch_config(args.config)
    repository = config.external_repository
    run_id = str(args.run_id)

    imported = load_imported_github_run_bundle(
        dataset_raw_path=config.dataset.raw_path,
        dataset_index_path=config.dataset.index_path,
        repository=repository,
        run_id=run_id,
    )
    policy_decision_id = args.policy_decision_id or (
        "policy:0281:r7:"
        + _repository_slug(repository)
        + f":{run_id}:{args.issue_number}"
    )
    command = GitHubRealClosedLoopSmokeCommand(
        repository=repository,
        run_id=run_id,
        issue_number=args.issue_number,
        members=imported.members,
        run_group_report_ref=imported.report_ref,
        policy_decision_id=policy_decision_id,
        operator_reason=args.operator_reason,
        require_advisory=not args.allow_missing_advisory,
        publish_observations=not args.no_observations,
        verify_sql_replay=not args.no_sql_replay,
    )
    result = asyncio.run(_execute(command))
    result_mapping = result.to_mapping()
    output_dir = (
        config.dataset.index_path
        / "github_closed_loop_0281"
        / _repository_slug(repository)
        / run_id
    )
    write_actions = _write_outputs(output_dir, result_mapping)
    report = {
        "schema": "missipy.github.real_closed_loop_smoke_tool.v1",
        "valid": result.valid,
        "issues": list(result.issues),
        "repository": repository,
        "run_id": run_id,
        "issue_number": args.issue_number,
        "config_path": str(args.config.resolve()),
        "dataset_root": str(config.dataset.root.resolve()),
        "run_group_report_path": str(imported.report_path),
        "run_group_report_ref": imported.report_ref,
        "raw_run_root": str(imported.raw_run_root),
        "input_source": "configured_server_dataset",
        "output_dir": str(output_dir.resolve()),
        "write_actions": write_actions,
        "publication_preview_path": str(
            (output_dir / "publication_preview.json").resolve()
        ),
        "publication_plan_path": str(
            (output_dir / "publication_plan.json").resolve()
        ),
        "github_mutation_performed": False,
        "projects_repository_change_required": False,
    }
    _emit(report, args.format)
    return 0 if result.valid else 2


async def _execute(command: GitHubRealClosedLoopSmokeCommand):
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    register_laboratory_visit_handler(dispatcher)
    scheduler = Scheduler(
        queue=PriorityQueue(),
        dispatcher=dispatcher,
        event_bus=event_bus,
        registry=Registry(),
        context_interval=60.0,
    )
    run_task = asyncio.create_task(scheduler.run())
    try:
        return await run_github_real_closed_loop_smoke(
            scheduler,
            command,
            store=SQLiteSqlContextStore(),
            passage_profile=_passage_profile(),
            embedder=_deterministic_embedder,
            projection_executor=DemoQdrantProjectionExecutor(),
            recall_executor_factory=lambda sql_ref: DemoQdrantRecallExecutor(
                sql_refs=(sql_ref,)
            ),
            event_bus=event_bus,
        )
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def _passage_profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        backend_ref="openvino:model:multilingual-e5-small",
        model_ref="openvino.embedding.e5-small",
        model_revision="local-smoke",
        tokenizer_ref="transformers.multilingual-e5-small",
        role="passage",
        collection_name="laboratory_outputs_e5_384",
    )


def _deterministic_embedder(
    text: str,
    sql_ref: str,
    model_dir: str | None,
    device: str,
) -> Mapping[str, Any]:
    vector = [0.0] * 384
    vector[0] = 1.0
    role = "query" if text.startswith("query:") else "passage"
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role=role,
        text=text,
        vector=vector,
        backend_ref="openvino:model:multilingual-e5-small",
        model="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        model_path=model_dir or "",
        device=device,
    )


def _write_outputs(
    output_dir: Path,
    result: Mapping[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "closed_loop_result.json": result,
        "run_assembly.json": result.get("assembly", {}),
        "laboratory_projection.json": result.get(
            "laboratory_projection",
            {},
        ),
        "publication_preview.json": result.get("publication_preview", {}),
        "publication_plan.json": result.get("publication_plan", {}),
    }
    actions: dict[str, str] = {}
    for filename, payload in files.items():
        actions[filename] = _write_json_idempotent(
            output_dir / filename,
            payload,
        )
    return actions


def _write_json_idempotent(path: Path, payload: object) -> str:
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    if path.exists():
        if path.read_bytes() == encoded:
            return "replayed"
        raise RuntimeError(
            f"refusing to overwrite different closed-loop proof: {path}"
        )
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(encoded)
    temporary.replace(path)
    return "created"


def _repository_slug(repository: str) -> str:
    return repository.replace("/", "__")


def _emit(report: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(f"valid: {report['valid']}")
    print(f"run_id: {report['run_id']}")
    print(f"dataset_root: {report['dataset_root']}")
    print(f"run_group_report_path: {report['run_group_report_path']}")
    print(f"output_dir: {report['output_dir']}")
    print(f"publication_preview_path: {report['publication_preview_path']}")
    print(f"publication_plan_path: {report['publication_plan_path']}")
    print("github_mutation_performed: false")
    for issue in report["issues"]:
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
