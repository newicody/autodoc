from __future__ import annotations

from pathlib import Path

from tools.run_scheduler_vector_indexing_smoke import (
    DEFAULT_COLLECTION,
    DEFAULT_DIMENSION,
    build_scheduler_vector_indexing_smoke_plan,
    write_scheduler_vector_indexing_request_frame,
)


def _touch(path: Path, text: str = "# surface\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_build_scheduler_vector_indexing_smoke_plan_reuses_existing_surfaces(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    for path in (
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "src/context/vector_indexing_job_plan.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
    ):
        _touch(root / path)

    plan = build_scheduler_vector_indexing_smoke_plan(
        root,
        model_dir=Path("/models/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection=DEFAULT_COLLECTION,
        dimension=DEFAULT_DIMENSION,
        sql_ref="sql:smoke/vector-indexing/test",
        route_root=Path(".var/smoke/routes"),
        text="passage: smoke",
        execute=False,
        strict_vector_handoff=True,
    )

    assert plan.ready is True
    assert plan.route_frame_preview.frame_kind == "vector_embedding_request"
    assert plan.route_frame_preview.payload["operator_tool"] == "tools/run_local_vector_indexing_live_smoke.py"
    assert plan.route_frame_preview.payload["strict_vector_handoff"] is True
    markdown = plan.to_markdown()
    assert "reuses src/runtime/scheduler_route_handler_minimal.py as existing handler surface" in markdown
    assert "does not create SchedulerOpenVINORunner" in markdown
    assert "does not modify the Scheduler run loop" in markdown


def test_build_scheduler_vector_indexing_smoke_plan_reports_missing_surfaces(tmp_path: Path) -> None:
    plan = build_scheduler_vector_indexing_smoke_plan(
        tmp_path,
        model_dir=Path("/models/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection=DEFAULT_COLLECTION,
        dimension=DEFAULT_DIMENSION,
        sql_ref="sql:smoke/vector-indexing/test",
        route_root=Path(".var/smoke/routes"),
        text="smoke",
        execute=False,
        strict_vector_handoff=True,
    )

    assert plan.ready is False
    assert {surface.key for surface in plan.missing_surfaces()} >= {
        "scheduler_route_handler",
        "route_proxy_runtime",
        "local_vector_indexing_smoke_tool",
    }


def test_write_scheduler_vector_indexing_request_frame_through_existing_handler(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    plan = build_scheduler_vector_indexing_smoke_plan(
        repo_root,
        model_dir=Path("/models/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection=DEFAULT_COLLECTION,
        dimension=DEFAULT_DIMENSION,
        sql_ref="sql:smoke/vector-indexing/test",
        route_root=tmp_path / "routes",
        text="passage: scheduler handler frame smoke",
        execute=False,
        strict_vector_handoff=True,
    )

    summary = write_scheduler_vector_indexing_request_frame(plan)

    assert summary.written_route_refs == ("vector-route:smoke/0143/embedding-request",)
    assert summary.readback_count == 1
    assert summary.payload_frame_kind == "vector_embedding_request"
    assert summary.payload_sql_ref == "sql:smoke/vector-indexing/test"
    assert summary.payload_operator_tool == "tools/run_local_vector_indexing_live_smoke.py"
    assert summary.frame_paths[0].exists()
