from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_architecture_docs_and_surfaces.py"
RULE = ROOT / "doc" / "code-rules" / "0153_architecture_docs_surface_audit_rule.md"
DOC = ROOT / "doc" / "architecture" / "ARCHITECTURE_REFRESH_AND_DOC_AUDIT_0153.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "153_architecture_docs_surface_audit.dot"


def test_0153_rule_files_exist() -> None:
    for path in (TOOL, RULE, DOC, DOT):
        assert path.exists(), path


def test_0153_rule_locks_audit_only_boundary() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "read-only audit tool" in text
    assert "preserve the existing documentation hierarchy" in text
    assert "SQL as durable authority" in text
    assert "Qdrant as projection/recall only" in text


def test_0153_tool_does_not_create_parallel_runtime() -> None:
    combined = TOOL.read_text(encoding="utf-8") + "\n" + RULE.read_text(encoding="utf-8")
    forbidden = [
        "SQLPersistenceWorker(",
        "SQLOrchestrator(",
        "LocalArtifactOrchestrator(",
        "LocalVectorIndexingOrchestrator(",
        "SchedulerOpenVINORunner(",
        "VectorOpenVINOEmbeddingAdapter(",
        "VectorQdrantProjectionAdapter(",
        "qdrant_client",
        "openvino.runtime",
        "Scheduler.run(",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_0153_doc_distinguishes_e5_openvino_qdrant_sql() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "E5 is the embedding model family" in text
    assert "OpenVINO is the local inference runtime" in text
    assert "Qdrant is the vector projection/recall index" in text
    assert "SQL remains durable authority" in text
