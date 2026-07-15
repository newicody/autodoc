from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_projects_operator_authorized_adapter_0286.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r6_reuses_a_structural_port_and_creates_no_http_client() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "class SpecialistCapabilityGrowthGitHubExecutionPort(Protocol)" in text
    assert "new_http_client_created" in text
    assert "requests" not in text
    assert "urllib" not in text
    assert "httpx" not in text


def test_r6_requires_operator_execute_and_exact_plan_digest() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert 'operator_decision != "approve"' in text
    assert "if not command.execute" in text
    assert "confirmed plan digest does not match" in text


def test_r6_preserves_authority_boundaries() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for token in (
        "github_projects_authoritative",
        "sql_remains_durable_authority",
        "scheduler_remains_only_orchestrator",
        "qdrant_authoritative",
    ):
        assert token in text


def test_projects_installation_guide_remains_cumulative() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "0286-r4" in text
    assert "--delete" in text
