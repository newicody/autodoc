from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / (
    "doc/architecture/"
    "GITHUB_RESEARCH_LOVE_PUBLICATION_EVIDENCE_DIGEST_BOUNDARY_0287_R16_R56.md"
)
RULE = ROOT / (
    "doc/code-rules/"
    "0287_r16_r56_publication_evidence_digest_boundary_rule.md"
)
SOURCE = ROOT / (
    "src/context/github_research_love_publication_evidence_sql_0287.py"
)


def test_r16_r56_documents_digest_and_architecture_boundaries() -> None:
    combined = ARCHITECTURE.read_text(encoding="utf-8") + "\n" + RULE.read_text(
        encoding="utf-8"
    )

    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "sha256:*" in combined
    assert "replay" in combined
    assert "file JSONL" in combined
    assert "stockage interne JSON" in combined


def test_r16_r56_normalizes_only_for_sql_evidence() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "typed_plan_digest = _typed_sha256_digest(" in source
    assert '"plan_digest": typed_plan_digest' in source
    assert 'remote.get("plan_digest") != plan_digest' in source
    assert 'publication_plan.get("plan_digest") != plan_digest' in source
    assert 'return "sha256:" + hexadecimal' in source
    assert "hashlib.sha256(hexadecimal" not in source
