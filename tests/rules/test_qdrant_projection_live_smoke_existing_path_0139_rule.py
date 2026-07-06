from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_projection_live_smoke.py"
DOC = ROOT / "doc" / "architecture" / "QDRANT_PROJECTION_LIVE_SMOKE_EXISTING_PATH_0139.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0139_qdrant_projection_live_smoke_existing_path_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0139_CHANGED_FILES.md"


def test_0139_docs_lock_existing_qdrant_projection_membrane() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0139 prepares the first Qdrant projection live smoke through existing surfaces only",
        "src/inference/qdrant_projection_adapter.py is the existing Qdrant projection membrane",
        "src/context/vector_collection_registry.py is the existing collection registry",
        "src/context/vector_indexing_job_plan.py is the existing projection job contract",
        "Do not create a parallel VectorQdrantProjectionAdapter",
        "Qdrant stores projection/recall indexes, not durable truth",
        "SQLContextStore remains durable context authority",
        "dry-run is the default",
        "--execute is required for backend execution",
        "code_rule_review: done",
    ]
    for phrase in required:
        assert phrase in text


def test_0139_code_rule_requires_existing_qdrant_surfaces_for_live_smoke() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before running a Qdrant projection live smoke",
        "reuse src/inference/qdrant_projection_adapter.py",
        "reuse src/context/vector_collection_registry.py",
        "reuse src/context/vector_indexing_job_plan.py",
        "Do not create a parallel VectorQdrantProjectionAdapter",
        "do not import Qdrant from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts",
        "dry-run must remain the default",
    ]
    for phrase in required:
        assert phrase in text


def test_0139_tool_does_not_import_qdrant_client_directly() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {"qdrant", "qdrant_client", "openvino", "psycopg", "sqlite3", "socket", "requests", "httpx"}
    assert sorted(imports & forbidden) == []


def test_0139_manifest_does_not_add_parallel_adapter_or_worker() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_qdrant_projection_live_smoke.py",
        "tests/tools/test_qdrant_projection_live_smoke_existing_path_0139.py",
        "tests/rules/test_qdrant_projection_live_smoke_existing_path_0139_rule.py",
        "doc/architecture/QDRANT_PROJECTION_LIVE_SMOKE_EXISTING_PATH_0139.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorQdrantProjectionAdapter",
        "LocalVectorIndexingOrchestrator",
        "src/runtime/qdrant",
        "src/scheduler/qdrant",
        "src/context/qdrant_adapter",
        "src/inference/vector_qdrant_projection_adapter.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
