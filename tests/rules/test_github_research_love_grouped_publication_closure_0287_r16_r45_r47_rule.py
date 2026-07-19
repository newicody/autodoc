from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_grouped_publication_closure_0287.py"
DOC = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_GROUPED_PUBLICATION_CLOSURE_0287_R16_R45_R47.md"
RULE = ROOT / "doc/code-rules/0287_r16_r45_r47_grouped_publication_closure_rule.md"


def test_grouped_publication_closure_locks_authority_boundaries() -> None:
    module = MODULE.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    assert "close_github_research_love_cycle" in module
    assert "execute_github_research_love_final_publication" in module
    assert "confirm_plan_digest" in module
    assert "les trois verrous distants" in module
    assert "VisPy reste observation-only" in doc
    assert "PostgreSQL demeure l'autorité durable" in doc
    assert "aucun Scheduler parallèle" in rule
    assert "JSONL" not in module
    assert "__pycache__" not in module
