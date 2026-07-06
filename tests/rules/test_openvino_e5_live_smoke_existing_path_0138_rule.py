from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_openvino_e5_live_smoke.py"
DOC = ROOT / "doc" / "architecture" / "OPENVINO_E5_LIVE_SMOKE_EXISTING_PATH_0138.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0138_openvino_e5_live_smoke_existing_path_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0138_CHANGED_FILES.md"


def test_0138_docs_lock_existing_openvino_e5_cli_and_membrane() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0138 runs the first OpenVINO/E5 live smoke through existing surfaces only",
        "tools/embed_e5.py is the existing operator CLI",
        "src/inference/openvino_embedding_adapter.py is the existing embedding membrane",
        "src/inference/openvino_runtime.py is the only real OpenVINO import boundary",
        "dry-run is the default",
        "--execute is required for backend execution",
        "Do not create SchedulerOpenVINORunner",
        "Do not create VectorOpenVINOEmbeddingAdapter",
        "Scheduler remains outside OpenVINO",
        "Qdrant remains outside OpenVINO",
    ]
    for phrase in required:
        assert phrase in text


def test_0138_code_rule_requires_existing_surfaces_for_live_smoke() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before running an OpenVINO/E5 live smoke",
        "reuse tools/embed_e5.py",
        "reuse src/inference/openvino_embedding_adapter.py",
        "reuse src/inference/openvino_runtime.py",
        "do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, Qdrant, or context contracts",
        "dry-run must remain the default",
    ]
    for phrase in required:
        assert phrase in text


def test_0138_tool_does_not_import_openvino_or_qdrant_directly() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {"openvino", "qdrant", "qdrant_client", "psycopg", "sqlite3", "socket", "requests", "httpx"}
    assert sorted(imports & forbidden) == []


def test_0138_manifest_does_not_add_parallel_adapter_or_scheduler_runner() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_openvino_e5_live_smoke.py",
        "tests/tools/test_openvino_e5_live_smoke_existing_path_0138.py",
        "tests/rules/test_openvino_e5_live_smoke_existing_path_0138_rule.py",
        "doc/architecture/OPENVINO_E5_LIVE_SMOKE_EXISTING_PATH_0138.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "VectorOpenVINOEmbeddingAdapter",
        "SchedulerOpenVINORunner",
        "src/runtime/openvino",
        "src/scheduler/openvino",
        "src/context/openvino",
        "qdrant_client",
    ]
    for phrase in forbidden:
        assert phrase not in text
