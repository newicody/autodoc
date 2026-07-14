from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialists_laboratories_live_path_evidence_0284.py"
CLI = ROOT / "tools/verify_specialists_laboratories_live_path_evidence_0284.py"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r9_reuses_r8_closure_and_adds_no_parallel_runtime() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "audit_specialists_laboratories_chain_closure" in text
    assert "Phase0284OperationalEvidence" in text
    assert "dataclass(frozen=True, slots=True)" in text
    assert "EXPECTED_E5_DIMENSION = 384" in text
    assert "Scheduler(" not in text
    assert "LaboratoryManager" not in text
    assert "requests" not in text
    assert "qdrant_client" not in text
    assert "from openvino" not in text.lower()
    assert "import openvino" not in text.lower()
    assert "from qdrant_client" not in text.lower()


def test_r9_cli_is_thin_and_has_no_remote_execution_switch() -> None:
    text = CLI.read_text(encoding="utf-8")

    assert "build_specialists_laboratories_live_path_evidence" in text
    assert "--integrated-result" in text
    assert "--execute" not in text
    assert "urllib" not in text
    assert "requests" not in text
    assert "subprocess" not in text
    assert "argparse.Namespace" not in text


def test_projects_installation_remains_cumulative_and_safe() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")

    assert "Version du guide : `0284-r9`." in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "verify_specialists_laboratories_live_path_evidence_0284.py" in text
    assert "ne déclenche aucun dispatch" in text
    assert "Ne pas utiliser `--delete`" in text
