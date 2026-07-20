from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_EXTERNALLY_MANAGED_BACKEND_FOUNDATION_0287_R16_R59.md"
RULE = ROOT / "doc/code-rules/0287_r16_r59_externally_managed_backend_foundation_rule.md"
SOURCE = ROOT / "src/context/love_externally_managed_installed_backend_foundation_0287.py"


def test_r16_r59_documents_architecture_boundaries() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(encoding="utf-8")
    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "Qdrant" in combined
    assert "OpenVINO E5" in combined
    assert "dimension 384" in combined
    assert "file JSONL" in combined
    assert "stockage interne JSON" in combined
    assert "OpenRC" in combined


def test_r16_r59_has_no_jsonl_or_parallel_orchestrator() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "jsonlines" not in source
    assert "JSONLWriter" not in source
    assert "subprocess" not in source
    assert "threading.Thread" not in source
    assert "LaboratoryManager" not in source
