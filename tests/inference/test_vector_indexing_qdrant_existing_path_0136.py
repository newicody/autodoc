from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
QDRANT_ADAPTER = ROOT / "src" / "inference" / "qdrant_projection_adapter.py"
VECTOR_JOB_PLAN = ROOT / "src" / "context" / "vector_indexing_job_plan.py"
VECTOR_COLLECTION_REGISTRY = ROOT / "src" / "context" / "vector_collection_registry.py"


def _read_existing(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"complete repository surface not present in reduced test fixture: {path}")
    return path.read_text(encoding="utf-8")


def test_vector_projection_path_reuses_existing_qdrant_adapter_file() -> None:
    qdrant_text = _read_existing(QDRANT_ADAPTER)
    plan_text = _read_existing(VECTOR_JOB_PLAN)

    assert "qdrant" in qdrant_text.lower()
    assert "Projection" in qdrant_text or "projection" in qdrant_text
    assert "VectorProjectionJob" in plan_text
    assert "sql_ref" in plan_text or "source_ref" in plan_text


def test_vector_projection_path_reuses_existing_collection_registry() -> None:
    registry_text = _read_existing(VECTOR_COLLECTION_REGISTRY)
    qdrant_text = _read_existing(QDRANT_ADAPTER)

    assert "VectorCollectionRegistry" in registry_text
    registry_lower = registry_text.lower()
    assert "collection" in registry_lower
    assert "registry" in registry_lower
    assert "collection" in qdrant_text.lower()


def test_qdrant_existing_adapter_stays_outside_scheduler_and_route_proxy() -> None:
    qdrant_text = _read_existing(QDRANT_ADAPTER)
    forbidden = [
        "from kernel.scheduler",
        "import kernel.scheduler",
        "Scheduler(",
        "Scheduler.run(",
        "PolicyEngine(",
        "RouteProxyRuntime(",
        "route_proxy_runtime_minimal",
    ]
    for phrase in forbidden:
        assert phrase not in qdrant_text
