from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from tools.run_qdrant_projection_live_smoke import (
    build_qdrant_projection_smoke_plan,
    deterministic_normalized_vector,
    qdrant_put_collection_payload,
    qdrant_rest_point_from_projection,
    qdrant_search_payload,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@dataclass(frozen=True)
class FakeProjectionPoint:
    point_id: str = "qdrant-point:abc"
    vector: tuple[float, ...] = (1.0, 0.0, 0.0)
    payload: tuple[tuple[str, str], ...] = (("role", "passage"),)
    sql_context_ref: str = "sql:smoke/test"


def test_0140_smoke_plan_documents_operator_rest_executor_boundary(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "inference" / "qdrant_projection_adapter.py", "class QdrantProjectionAdapter:\n    pass\n")
    _write(tmp_path / "src" / "context" / "vector_collection_registry.py", "class VectorCollectionRegistry:\n    pass\n")
    _write(tmp_path / "src" / "context" / "vector_indexing_job_plan.py", "class VectorProjectionJob:\n    pass\n")

    plan = build_qdrant_projection_smoke_plan(
        tmp_path,
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/test",
        execute=True,
    )

    markdown = plan.to_markdown()
    assert plan.ready is True
    assert "0140 uses the existing QdrantProjectionExecutor injection seam instead of a new adapter" in markdown
    assert "operator REST execution lives in tools/run_qdrant_projection_live_smoke.py only" in markdown
    assert "does not create VectorQdrantProjectionAdapter" in markdown


def test_0140_deterministic_vector_is_unit_normalized() -> None:
    vector = deterministic_normalized_vector(384)

    assert len(vector) == 384
    assert math.isclose(math.sqrt(sum(value * value for value in vector)), 1.0, rel_tol=1e-12)


def test_0140_builds_qdrant_rest_payloads_without_qdrant_client() -> None:
    point = FakeProjectionPoint()
    rest_point = qdrant_rest_point_from_projection(point)
    collection_payload = qdrant_put_collection_payload(384)
    search_payload = qdrant_search_payload(point.vector, limit=1)

    assert rest_point["id"] != point.point_id
    assert rest_point["payload"]["typed_point_id"] == point.point_id  # type: ignore[index]
    assert rest_point["payload"]["sql_context_ref"] == "sql:smoke/test"  # type: ignore[index]
    assert collection_payload == {"vectors": {"size": 384, "distance": "Cosine"}}
    assert search_payload["limit"] == 1
    assert search_payload["with_payload"] is True
    assert search_payload["with_vector"] is False
