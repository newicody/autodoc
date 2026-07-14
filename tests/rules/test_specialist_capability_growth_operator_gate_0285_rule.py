from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_operator_gate_0285.py"
TEST = ROOT / "tests/context/test_specialist_capability_growth_operator_gate_0285.py"
DOC = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_0285.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_0285.dot"
REPORT = ROOT / "PHASE0285_R4_SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R4_SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R4_SPECIALIST_CAPABILITY_GROWTH_OPERATOR_GATE.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r4_delivers_complete_systematic_bundle() -> None:
    for path in (SOURCE, TEST, DOC, DOT, REPORT, MANIFEST, CHANGELOG):
        assert path.is_file(), path


def test_operator_gate_reuses_r2_and_r3_without_runtime_imports() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert "context.specialist_capability_growth_proposal_contract_0285" in imported
    assert "context.portable_specialist_revision_lineage_contract_0285" in imported
    forbidden = (
        "scheduler",
        "sql",
        "qdrant",
        "openvino",
        "eventbus",
        "github",
        "requests",
        "subprocess",
    )
    assert not any(
        token in module.lower() for module in imported for token in forbidden
    )


def test_operator_gate_locks_explicit_authority_and_no_side_effects() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for token in (
        "class SpecialistCapabilityGrowthDecision",
        "class SpecialistCapabilityGrowthOperatorGate",
        '"approve"',
        '"reject"',
        '"defer"',
        '"explicit_operator_authority": True',
        '"durable_state_written": False',
        '"scheduler_selection_allowed": False',
        '"github_mutation_performed": False',
    ):
        assert token in source


def test_documentation_preserves_architecture_boundaries_and_next_phase() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "Scheduler remains the only orchestration authority",
        "SQL remains the durable authority",
        "Qdrant remains projection and recall only",
        "EventBus remains observation only",
        "0285-r5-specialist-capability-growth-durable-history",
        "INSTALLATION.md",
    ):
        assert token in text


def test_projects_installation_is_still_safe_and_was_reviewed() -> None:
    source = INSTALLATION.read_text(encoding="utf-8")
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in source
    assert "--delete" in source
    report = REPORT.read_text(encoding="utf-8")
    assert "INSTALLATION reviewed: yes" in report
    assert "INSTALLATION modified: no" in report
