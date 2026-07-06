from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_projection_live_smoke.py"
DOC = ROOT / "doc" / "architecture" / "QDRANT_PROJECTION_OPERATOR_REST_SMOKE_0140.md"
RULE = ROOT / "doc" / "code-rules" / "0140_qdrant_projection_operator_rest_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0140_CHANGED_FILES.md"


def test_0140_tool_extends_existing_qdrant_smoke_without_new_adapter() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "0140 keeps the same operator surface",
        "QdrantProjectionExecutor injection seam",
        "run_operator_rest_smoke",
        "build_smoke_projection_point",
        "qdrant_rest_point_from_projection",
        "urllib.request",
        "does not create VectorQdrantProjectionAdapter",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorQdrantProjectionAdapter(",
        "SchedulerOpenVINORunner",
        "LocalVectorIndexingOrchestrator",
        "from qdrant_client",
        "import qdrant_client",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0140_tool_does_not_import_scheduler_routeproxy_or_policy() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    forbidden = {
        "kernel.scheduler",
        "runtime.route_proxy_runtime_minimal",
        "policy.engine",
        "qdrant_client",
    }
    assert sorted(imports & forbidden) == []


def test_0140_docs_and_rules_lock_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8") + "\n" + RULE.read_text(encoding="utf-8")
    required = [
        "0140 extends the existing Qdrant smoke operator, not the Scheduler",
        "the existing src/inference/qdrant_projection_adapter.py contract remains the Qdrant projection membrane",
        "operator REST execution is allowed only in tools/run_qdrant_projection_live_smoke.py",
        "do not create VectorQdrantProjectionAdapter",
        "Qdrant stores projection and recall indexes, not durable truth",
        "SQLContextStore remains durable context authority",
    ]
    for phrase in required:
        assert phrase in text


def test_0140_manifest_lists_only_existing_tool_and_docs_tests() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_qdrant_projection_live_smoke.py",
        "tests/tools/test_qdrant_projection_operator_rest_smoke_0140.py",
        "tests/rules/test_qdrant_projection_operator_rest_smoke_0140_rule.py",
        "doc/architecture/QDRANT_PROJECTION_OPERATOR_REST_SMOKE_0140.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/route_proxy_qdrant_worker.py",
        "src/inference/vector_qdrant_projection_adapter.py",
        "src/inference/qdrant_client_adapter.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
