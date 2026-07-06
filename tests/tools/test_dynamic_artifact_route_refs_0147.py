from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.artifact_route_refs import ArtifactRouteRefs, build_artifact_route_refs
from tools.run_local_artifact_vector_indexing_runner import build_local_artifact_vector_indexing_plan, main as artifact_main
from tools.run_scheduler_vector_indexing_smoke import build_scheduler_vector_indexing_smoke_plan, main as scheduler_main


def _make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for path in [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/context/sql_context_store.py",
        "src/context/vector_indexing_job_plan.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
    ]:
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("# stub\n", encoding="utf-8")
    return root


def test_0147_artifact_route_refs_are_dynamic_and_pure() -> None:
    refs = build_artifact_route_refs(
        artifact_ref="artifact:local/0147/demo",
        vector_indexing_job_ref="vector-indexing-job:artifact/0147-demo",
    )

    assert isinstance(refs, ArtifactRouteRefs)
    assert refs.artifact_slug == "local-0147-demo"
    assert refs.job_slug == "artifact-0147-demo"
    assert refs.command_ref == "scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request"
    assert refs.request_route_ref == "vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request"
    assert refs.result_command_ref.endswith("/indexing-result")
    assert refs.result_route_ref == "vector-route:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result"
    assert refs.route_namespace.startswith("autodoc-artifact-local-0147-demo-job-artifact-0147-demo")
    assert ArtifactRouteRefs.from_mapping(refs.to_mapping()).request_route_ref == refs.request_route_ref


def test_0147_artifact_route_refs_reject_bad_inputs() -> None:
    with pytest.raises(ValueError, match="artifact_ref"):
        build_artifact_route_refs(
            artifact_ref="local/0147/demo",
            vector_indexing_job_ref="vector-indexing-job:artifact/0147-demo",
        )
    with pytest.raises(ValueError, match="vector_indexing_job_ref"):
        build_artifact_route_refs(
            artifact_ref="artifact:local/0147/demo",
            vector_indexing_job_ref="artifact/0147-demo",
        )


def test_0147_scheduler_smoke_accepts_dynamic_refs(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_scheduler_vector_indexing_smoke_plan(
        root,
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0147",
        route_root=Path(".var/smoke/routeproxy-0147/routes"),
        command_ref="scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request",
        request_route_ref="vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request",
        result_command_ref="scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result",
        result_route_ref="vector-route:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result",
        result_owner_ref="worker:local-vector-indexing-smoke/artifact/local-0147-demo/job/artifact-0147-demo",
        vector_indexing_job_ref="vector-indexing-job:artifact/0147-demo",
        route_namespace="autodoc-artifact-local-0147-demo-request",
        result_route_namespace="autodoc-artifact-local-0147-demo-result",
        text="passage: dynamic refs",
        execute=False,
        strict_vector_handoff=True,
    )

    assert plan.ready is True
    assert plan.route_frame_preview.route_ref == "vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request"
    assert plan.route_frame_preview.owner_ref == "scheduler-command:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request"
    assert plan.route_frame_preview.payload["vector_indexing_job_ref"] == "vector-indexing-job:artifact/0147-demo"
    mapping = plan.route_frame_preview.to_mapping()
    assert "0143-smoke" not in json.dumps(mapping)
    markdown = plan.to_markdown()
    assert "request_route_ref: `vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request`" in markdown
    assert "dynamic refs replace static 0143/0144 smoke refs" in markdown


def test_0147_artifact_runner_passes_dynamic_refs_to_existing_scheduler_tool(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_local_artifact_vector_indexing_plan(
        root,
        artifact_dir=Path(".var/smoke/artifacts/0147"),
        artifact_ref="artifact:local/0147/demo",
        artifact_kind="local_markdown",
        text_kind="passage",
        vector_indexing_job_ref="vector-indexing-job:artifact/0147-demo",
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0147",
        route_root=Path(".var/smoke/routeproxy-0147/routes"),
        text="passage: dynamic artifact runner",
        execute=False,
    )

    command = plan.commands[0].shell_preview()
    assert plan.ready is True
    assert plan.artifact_route_refs.request_route_ref == "vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request"
    assert "--request-route-ref vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request" in command
    assert "--result-route-ref vector-route:artifact/local-0147-demo/job/artifact-0147-demo/indexing-result" in command
    assert "--vector-indexing-job-ref vector-indexing-job:artifact/0147-demo" in command
    assert "vector-route:smoke/0143/embedding-request" not in command
    assert "vector-route:smoke/0144/indexing-result" not in command
    assert "## Dynamic route refs" in plan.to_markdown()


def test_0147_scheduler_json_cli_reports_dynamic_refs(tmp_path: Path, capsys) -> None:
    root = _make_repo(tmp_path)
    rc = scheduler_main([
        str(root),
        "--command-ref", "scheduler-command:artifact/local-0147-json/job/artifact-0147-json/embedding-request",
        "--request-route-ref", "vector-route:artifact/local-0147-json/job/artifact-0147-json/embedding-request",
        "--result-command-ref", "scheduler-command:artifact/local-0147-json/job/artifact-0147-json/indexing-result",
        "--result-route-ref", "vector-route:artifact/local-0147-json/job/artifact-0147-json/indexing-result",
        "--result-owner-ref", "worker:local-vector-indexing-smoke/artifact/local-0147-json/job/artifact-0147-json",
        "--vector-indexing-job-ref", "vector-indexing-job:artifact/0147-json",
        "--route-namespace", "autodoc-artifact-local-0147-json-request",
        "--result-route-namespace", "autodoc-artifact-local-0147-json-result",
        "--format", "json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["request_route_ref"] == "vector-route:artifact/local-0147-json/job/artifact-0147-json/embedding-request"
    assert data["route_frame_preview"]["payload"]["vector_indexing_job_ref"] == "vector-indexing-job:artifact/0147-json"


def test_0147_artifact_json_cli_reports_route_refs(tmp_path: Path, capsys) -> None:
    root = _make_repo(tmp_path)
    rc = artifact_main([
        str(root),
        "--artifact-ref", "artifact:local/0147/json",
        "--vector-indexing-job-ref", "vector-indexing-job:artifact/0147-json",
        "--format", "json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    refs = data["artifact_route_refs"]
    assert refs["request_route_ref"] == "vector-route:artifact/local-0147-json/job/artifact-0147-json/embedding-request"
    assert refs["result_route_ref"] == "vector-route:artifact/local-0147-json/job/artifact-0147-json/indexing-result"
