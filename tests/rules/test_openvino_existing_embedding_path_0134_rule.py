from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "src" / "inference" / "openvino_embedding_adapter.py"
RUNTIME = ROOT / "src" / "inference" / "openvino_runtime.py"
DOC = ROOT / "doc" / "architecture" / "OPENVINO_EXISTING_EMBEDDING_PATH_0134.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0134_CHANGED_FILES.md"
CODE_RULE = ROOT / "doc" / "code-rules" / "0134_extend_existing_openvino_path_rule.md"


def test_0134_documents_extend_existing_openvino_path_not_new_adapter() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0134 extends the existing OpenVINO/E5 embedding path by tests and integration documentation",
        "Do not create a parallel E5OpenVINOEmbeddingAdapter",
        "src/inference/openvino_embedding_adapter.py is the existing embedding membrane",
        "src/inference/openvino_runtime.py is the only real OpenVINO import boundary",
        "Scheduler remains outside OpenVINO",
        "Qdrant remains outside OpenVINO",
        "query: text is for retrieval",
        "passage: text is for corpus, contracts, outputs, and synthesis candidates",
        "code_rule_review: done",
        "code_rule_update_required: true",
    ]
    for phrase in required:
        assert phrase in text


def test_0134_code_rule_addendum_exists_for_openvino_reuse() -> None:
    text = CODE_RULE.read_text(encoding="utf-8")
    required = [
        "Before adding any new OpenVINO or E5 adapter",
        "reuse or extend src/inference/openvino_embedding_adapter.py",
        "reuse or extend src/inference/e5_pipeline.py",
        "openvino imports remain confined to src/inference/openvino_runtime.py",
        "Do not import OpenVINO from Scheduler, Dispatcher, PolicyEngine, RouteProxy, or context contracts",
    ]
    for phrase in required:
        assert phrase in text


def test_0134_existing_adapter_contains_required_query_passage_contracts() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    required = [
        "class OpenVINOEmbeddingAdapter",
        "class OpenVINOEmbeddingText",
        "class OpenVINOEmbeddingPolicy",
        "build_embedding_texts_from_hydrated_bundle",
        "build_embedding_vector",
        "local_multilingual_e5_openvino_target",
        "query",
        "passage",
    ]
    for phrase in required:
        assert phrase in text


def test_0134_real_openvino_import_stays_in_openvino_runtime_only() -> None:
    adapter_tree = ast.parse(ADAPTER.read_text(encoding="utf-8"))
    adapter_imports: set[str] = set()
    for node in ast.walk(adapter_tree):
        if isinstance(node, ast.Import):
            adapter_imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            adapter_imports.add(node.module.split(".", 1)[0])
    assert "openvino" not in adapter_imports

    runtime_text = RUNTIME.read_text(encoding="utf-8")
    assert "import openvino" in runtime_text


def test_0134_manifest_does_not_add_parallel_openvino_adapter_source() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tests/inference/test_openvino_embedding_existing_path_0134.py",
        "tests/rules/test_openvino_existing_embedding_path_0134_rule.py",
        "doc/architecture/OPENVINO_EXISTING_EMBEDDING_PATH_0134.md",
        "doc/code-rules/0134_extend_existing_openvino_path_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/inference/e5_openvino_runtime_adapter.py",
        "src/inference/new_openvino_embedding_adapter.py",
        "src/runtime/openvino",
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/policy/engine.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
