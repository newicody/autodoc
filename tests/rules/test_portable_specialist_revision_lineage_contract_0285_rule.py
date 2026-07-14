from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/portable_specialist_revision_lineage_contract_0285.py"
DOC = ROOT / "doc/architecture/PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT_0285.md"
DOT = ROOT / "doc/architecture/PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT_0285.dot"
REPORT = ROOT / "PHASE0285_R3_PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R3_PORTABLE_SPECIALIST_REVISION_LINEAGE_CONTRACT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_required_contract_and_delivery_surfaces_exist() -> None:
    for path in (SOURCE, DOC, DOT, REPORT, MANIFEST):
        assert path.is_file(), path


def test_contract_reuses_portable_descriptor_and_stays_declarative() -> None:
    source = SOURCE.read_text(encoding="utf-8")

    assert "class PortableSpecialistRevision" in source
    assert "class SpecialistRevisionLineage" in source
    assert "PortableSpecialistDescriptor" in source
    assert "SpecialistCapabilityGrowthProposal" in source
    assert "validate_revision_against_growth_proposal" in source
    assert source.count("@dataclass(frozen=True, slots=True)") >= 2
    assert "def append(" in source
    assert "operator_decision_required" in source
    assert "scheduler_remains_only_orchestrator" in source

    forbidden = (
        "from contracts.scheduler import",
        "import qdrant",
        "import openvino",
        "import psycopg",
        "import sqlite3",
        "import requests",
        "import httpx",
        "subprocess",
        "Scheduler.run",
        "LaboratoryManager",
    )
    for token in forbidden:
        assert token not in source


def test_revision_lineage_does_not_embed_approval_or_runtime_authority() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        '"approval_embedded": False',
        '"operator_decision_required": self.revision_number > 1',
        '"scheduler_selection_embedded": False',
        '"durable_state_written": False',
        '"runtime_attached": False',
        '"sql_history_not_written": True',
        '"qdrant_projection_not_written": True',
        '"eventbus_observation_not_published": True',
        '"github_mutation_performed": False',
    )
    for token in required:
        assert token in source


def test_documentation_locks_reuse_and_next_operator_gate() -> None:
    doc = DOC.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    dot = DOT.read_text(encoding="utf-8")

    for token in (
        "PortableSpecialistDescriptor",
        "stable specialist_ref",
        "append-only",
        "operator decision remains external",
        "0285-r4-specialist-capability-growth-operator-gate",
    ):
        assert token in doc
    assert "19 passed" in report
    assert "Scheduler" in dot
    assert "SQL durable history (r5)" in dot


def test_projects_installation_was_reviewed_and_does_not_need_r3_changes() -> None:
    source = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r9`." in source
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in source
    assert "Ne pas utiliser `--delete`" in source

    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "INSTALLATION.md reviewed: yes" in manifest
    assert "INSTALLATION.md modified: no" in manifest
