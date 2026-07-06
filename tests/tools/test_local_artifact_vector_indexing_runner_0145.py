from __future__ import annotations

import json
from pathlib import Path

from tools.run_local_artifact_vector_indexing_runner import (
    build_local_artifact_vector_indexing_plan,
    build_local_artifact_vector_indexing_result,
    main,
)


def _make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for path in [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/context/sql_context_store.py",
    ]:
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("# stub\n", encoding="utf-8")
    return root


def test_0145_plan_reuses_existing_scheduler_vector_smoke_surfaces(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_local_artifact_vector_indexing_plan(
        root,
        artifact_dir=Path(".var/smoke/artifacts/0145"),
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0145",
        route_root=Path(".var/smoke/routeproxy-0145/routes"),
        text="artifact smoke text",
        execute=False,
    )

    assert plan.ready is True
    assert plan.text.startswith("passage: ")
    mapping = plan.to_mapping()
    assert mapping["ready_for_local_artifact_vector_indexing"] is True
    assert "tools/run_scheduler_vector_indexing_smoke.py" in plan.commands[0].shell_preview()
    assert "--sql-ref sql:artifact/vector-indexing/0145" in plan.commands[0].shell_preview()
    assert "LocalVectorIndexingOrchestrator" in Path("tools/run_local_artifact_vector_indexing_runner.py").read_text(encoding="utf-8")


def test_0145_plan_markdown_documents_artifact_outputs(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_local_artifact_vector_indexing_plan(
        root,
        artifact_dir=Path("artifacts"),
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0145",
        route_root=Path("routes"),
        text="passage: already prefixed",
        execute=False,
    )
    text = plan.to_markdown()
    assert "artifact_input" in text
    assert "artifact_report" in text
    assert "artifact_json" in text
    assert "does not modify Scheduler.run()" in text
    assert "SQLContextStore remains durable authority" in text


def test_0145_result_parser_builds_local_artifact_envelope(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_local_artifact_vector_indexing_plan(
        root,
        artifact_dir=Path("artifacts"),
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0145",
        route_root=Path("routes"),
        text="smoke",
        execute=True,
    )
    output = """
scheduler_route_frame: `ok`
local_vector_indexing_smoke: `ok`
vector_indexing_result_frame: `ok`
strict_vector_handoff: `true`
machine_vector_handoff: `true`
result_frame_path: `/tmp/result.json`
point_id: `qdrant-point:abc`
qdrant_rest_id: `uuid-abc`
vector_json: `/tmp/vector.json`
"""
    result = build_local_artifact_vector_indexing_result(plan, output)
    assert result.scheduler_route_frame == "ok"
    assert result.local_vector_indexing_smoke == "ok"
    assert result.vector_indexing_result_frame == "ok"
    assert result.strict_vector_handoff is True
    assert result.machine_vector_handoff is True
    assert result.point_id == "qdrant-point:abc"
    assert result.qdrant_rest_id == "uuid-abc"
    assert result.result_frame_path == "/tmp/result.json"
    mapping = result.to_mapping()
    assert mapping["boundary"] == "local artifact envelope around existing Scheduler vector indexing smoke"


def test_0145_json_plan_output_is_machine_readable(tmp_path: Path, capsys) -> None:
    root = _make_repo(tmp_path)
    rc = main([str(root), "--format", "json"])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ready_for_local_artifact_vector_indexing"] is True
    assert data["commands"]["scheduler_vector_indexing_smoke"]
