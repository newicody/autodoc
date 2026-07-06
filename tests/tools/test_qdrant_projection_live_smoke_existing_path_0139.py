from __future__ import annotations

from pathlib import Path

from tools.run_qdrant_projection_live_smoke import (
    build_qdrant_projection_smoke_plan,
    inspect_qdrant_adapter,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_qdrant_smoke_plan_detects_existing_surfaces(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "inference" / "qdrant_projection_adapter.py", "def run_qdrant_smoke(**kwargs):\n    return kwargs\n")
    _write(tmp_path / "src" / "context" / "vector_collection_registry.py", "class VectorCollectionRegistry:\n    pass\n")
    _write(tmp_path / "src" / "context" / "vector_indexing_job_plan.py", "class VectorProjectionJob:\n    pass\n")

    plan = build_qdrant_projection_smoke_plan(
        tmp_path,
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/test",
        execute=False,
    )

    assert plan.ready is True
    assert plan.adapter_inventory is not None
    assert plan.adapter_inventory.executable_entrypoints == ("run_qdrant_smoke",)
    markdown = plan.to_markdown()
    assert "src/inference/qdrant_projection_adapter.py" in markdown
    assert "dry-run is the default" in markdown
    assert "Qdrant stores projection/recall indexes, not durable truth" in markdown


def test_qdrant_smoke_plan_reports_missing_surfaces(tmp_path: Path) -> None:
    plan = build_qdrant_projection_smoke_plan(
        tmp_path,
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/test",
        execute=False,
    )

    assert plan.ready is False
    assert {surface.key for surface in plan.missing_surfaces()} == {
        "qdrant_projection_adapter",
        "vector_collection_registry",
        "vector_indexing_job_plan",
    }


def test_inspect_qdrant_adapter_reads_existing_symbols_without_importing_backend(tmp_path: Path) -> None:
    adapter = tmp_path / "qdrant_projection_adapter.py"
    adapter.write_text(
        "import qdrant_client\n"
        "class QdrantProjectionAdapter:\n    pass\n"
        "def run_qdrant_projection_live_smoke(**kwargs):\n    return kwargs\n",
        encoding="utf-8",
    )

    inventory = inspect_qdrant_adapter(adapter)

    assert "QdrantProjectionAdapter" in inventory.classes
    assert "run_qdrant_projection_live_smoke" in inventory.functions
    assert inventory.executable_entrypoints == ("run_qdrant_projection_live_smoke",)
    assert inventory.imports_qdrant_client is True
