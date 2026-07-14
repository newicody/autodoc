from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_durable_history_0285.py"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY_0285.md"
GRAPH = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY_0285.dot"
REPORT = ROOT / "PHASE0285_R5_SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R5_SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R5_SPECIALIST_CAPABILITY_GROWTH_DURABLE_HISTORY.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_r5_systematic_deliverables_exist() -> None:
    for path in (SOURCE, ARCHITECTURE, GRAPH, REPORT, MANIFEST, CHANGELOG):
        assert path.is_file(), path


def test_history_is_sql_authoritative_and_qdrant_projection_only() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "SpecialistCapabilityGrowthHistoryPort",
        "DeterministicSpecialistCapabilityGrowthHistoryAdapter",
        '"sql_authoritative": True',
        '"qdrant_authoritative": False',
        '"scheduler_selection_performed": False',
        '"durable_write_performed": self.durable_write_performed',
    )
    for token in required:
        assert token in source


def test_test_adapter_is_not_a_fake_sql_backend() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'return "sql"' in source
    assert "return False" in source
    assert 'adapter_kind="deterministic_test_memory"' in source
    forbidden = (
        "import sqlite3",
        "import psycopg",
        "import qdrant",
        "import openvino",
        "Scheduler(",
        "LaboratoryManager",
        "requests.",
        "urllib.request",
    )
    for token in forbidden:
        assert token not in source


def test_operator_gate_and_append_only_lineage_are_reused() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "SpecialistCapabilityGrowthDecision" in source
    assert "PortableSpecialistRevision" in source
    assert "SpecialistRevisionLineage" in source
    assert "revision_authorized" in source
    assert ".append(self.candidate_revision)" in source


def test_projects_installation_remains_cumulative_and_unchanged_in_scope() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r9`." in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "Ne pas utiliser `--delete`" in text
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    assert "INSTALLATION.md" in architecture
    assert "aucune modification" in architecture
