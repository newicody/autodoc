from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = (
    ROOT
    / "doc"
    / "architecture"
    / "GITHUB_RESEARCH_FINAL_PUBLICATION_COMPACT_SYNTHESIS_0287_R16_R51.md"
)
RULE = ROOT / "doc/code-rules/0287_r16_r51_final_publication_compact_synthesis_rule.md"
SOURCE = ROOT / "src/context/github_research_love_final_remote_publication_0287.py"


def test_r16_r51_documents_compact_boundary_and_authorities() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + RULE.read_text(
        encoding="utf-8"
    )

    assert "PostgreSQL" in combined
    assert "Scheduler canonique unique" in combined
    assert "file JSONL" in combined
    assert "synthesis_ref" in combined
    assert "final_publication_ready=false" in combined


def test_r16_r51_does_not_expand_the_durable_packet_contract() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "_publication_ready_packet_synthesis" in source
    assert 'source = _required_mapping(liaison, "synthesis")' in source
    assert 'ready["final_publication_ready"] = True' in source
    assert 'packet["synthesis"] =' not in source
