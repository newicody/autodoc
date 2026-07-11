from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = (
    ROOT
    / "src/context/github_project_v2_source_candidate_durable_consumer_0272.py"
)
CLI = ROOT / "tools/consume_github_project_v2_source_candidate_gate_0272.py"
ARCH = (
    ROOT
    / "doc/architecture/GITHUB_PROJECT_V2_SOURCE_CANDIDATE_DURABLE_CONSUMER_0272.md"
)
RUNTIME = (
    ROOT
    / "doc/docs/architecture/runtime/272_r8_github_project_v2_durable_consumer.dot"
)


def test_r8_reuses_sql_and_keeps_vector_and_remote_boundaries_closed() -> None:
    core = CORE.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    assert "build_sql_context_record" in core
    assert "build_db_api_sql_context_store_binding_report" in cli
    assert "laboratory_assignment_state" in core
    assert "embedding_projection_state" in core
    forbidden = (
        "import qdrant_client",
        "from qdrant_client",
        "import openvino",
        "from openvino",
        "import urllib",
        "from urllib",
        "import requests",
        "from requests",
        "import scheduler",
        "from scheduler",
        "RuntimeManager",
        "LaboratoryManager",
        "LaboratoryOrchestrator",
    )
    for token in forbidden:
        assert token not in core
        assert token not in cli


def test_r8_documentation_keeps_r9_and_laboratory_sequence_explicit() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = RUNTIME.read_text(encoding="utf-8")
    assert "0272-r9" in architecture
    assert "EmbeddingSpaceProfile" in architecture
    assert "0273-r1" in architecture
    assert "laboratoire fictif" in architecture
    assert "GateR7 -> DurableR8" in graph
    assert "DurableR8 -> VectorR9" in graph
    assert "DurableR8 -> LaboratoryAudit0273" in graph
