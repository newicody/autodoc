from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_postgresql_shared_adapter_port_0287.py"
BOUNDARY = ROOT / "src/context/github_research_love_externally_managed_postgresql_adapter_boundary_0287.py"
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_SHARED_POSTGRESQL_ADAPTER_PORT_0287_R16_R62.md"
RULE = ROOT / "doc/code-rules/0287_r16_r62_shared_postgresql_adapter_port_rule.md"


def test_r16_r62_documents_architecture_boundaries() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + RULE.read_text(encoding="utf-8")
    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "OpenRC" in combined
    assert "Qdrant" in combined
    assert "384" in combined
    assert "stockage interne JSON" in combined
    assert "file JSONL" in combined


def test_r16_r62_boundary_does_not_open_or_close_a_backend() -> None:
    source = BOUNDARY.read_text(encoding="utf-8")
    assert "psycopg" not in source
    assert ".close(" not in source
    assert "Scheduler(" not in source
    assert "PriorityQueue(" not in source
    assert "foundation._connection" not in source
    assert "port._connection" not in source
    port_source = SOURCE.read_text(encoding="utf-8")
    assert "build_adapter" in port_source
    assert "raw_connection_exposed" in port_source
