from __future__ import annotations

import json
from pathlib import Path

from tools.run_scheduler_vector_indexing_smoke import (
    DEFAULT_COLLECTION,
    DEFAULT_DIMENSION,
    DEFAULT_RESULT_ROUTE_REF,
    build_scheduler_vector_indexing_smoke_plan,
    extract_vector_indexing_smoke_result,
    write_scheduler_vector_indexing_request_frame,
    write_scheduler_vector_indexing_result_frame,
)


def _plan(tmp_path: Path):
    repo_root = Path(__file__).resolve().parents[2]
    return build_scheduler_vector_indexing_smoke_plan(
        repo_root,
        model_dir=Path("/models/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection=DEFAULT_COLLECTION,
        dimension=DEFAULT_DIMENSION,
        sql_ref="sql:smoke/vector-indexing/result-frame-test",
        route_root=tmp_path / "routes",
        text="passage: scheduler result frame smoke",
        execute=False,
        strict_vector_handoff=True,
    )


def test_extract_vector_indexing_smoke_result_reads_machine_lines_only() -> None:
    output = """
values_preview: [0.1, 0.2]
point_id: `qdrant-point:abc123`
qdrant_rest_id: `uuid-123`
machine_vector_handoff: `true`
strict_vector_handoff: `true`
vector_json: `/tmp/e5_vector.json`
qdrant_projection_smoke: `ok`
"""

    parsed = extract_vector_indexing_smoke_result(output)

    assert parsed["point_id"] == "qdrant-point:abc123"
    assert parsed["qdrant_rest_id"] == "uuid-123"
    assert parsed["machine_vector_handoff"] is True
    assert parsed["strict_vector_handoff"] is True
    assert parsed["vector_json"] == "/tmp/e5_vector.json"
    assert "values_preview" not in parsed


def test_write_scheduler_vector_indexing_result_frame_through_existing_handler(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    request_summary = write_scheduler_vector_indexing_request_frame(plan)
    smoke_output = """
# Qdrant projection live smoke result
point_id: `qdrant-point:result-frame`
qdrant_rest_id: `rest-id-result-frame`
machine_vector_handoff: `true`
strict_vector_handoff: `true`
vector_json: `/tmp/e5_vector_0144.json`
qdrant_projection_smoke: `ok`
"""

    result_summary = write_scheduler_vector_indexing_result_frame(
        plan,
        request_summary=request_summary,
        smoke_output=smoke_output,
    )

    assert result_summary.result_route_ref == DEFAULT_RESULT_ROUTE_REF
    assert result_summary.status == "ok"
    assert result_summary.sql_ref == "sql:smoke/vector-indexing/result-frame-test"
    assert result_summary.point_id == "qdrant-point:result-frame"
    assert result_summary.qdrant_rest_id == "rest-id-result-frame"
    assert result_summary.machine_vector_handoff is True
    assert result_summary.strict_vector_handoff is True
    assert result_summary.result_frame_path.exists()

    data = json.loads(result_summary.result_frame_path.read_text(encoding="utf-8"))
    assert data["payload"]["frame_kind"] == "vector_indexing_result"
    assert data["payload"]["request_route_ref"] == "vector-route:smoke/0143/embedding-request"
    assert data["payload"]["scheduler_run_modified"] is False


def test_plan_markdown_mentions_result_frame_boundary(tmp_path: Path) -> None:
    plan = _plan(tmp_path)
    markdown = plan.to_markdown()

    assert "0144 writes a vector_indexing_result frame back through the existing RouteProxyRuntime" in markdown
    assert "OpenVINO and Qdrant stay behind operator tools and existing adapters" in markdown
