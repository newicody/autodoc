from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_laboratory_transfer_contract_0284.py"
REPORT = ROOT / "PHASE0284_R4_SPECIALIST_LABORATORY_TRANSFER_CONTRACT_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_LABORATORY_TRANSFER_CONTRACT_0284.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R4_SPECIALIST_LABORATORY_TRANSFER_CONTRACT.md"


def test_r4_declares_audit_expected_transfer_classes() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "class SpecialistTransferRequest" in text
    assert "class SpecialistTransferResult" in text
    assert "class SpecialistTransferVisitPlan" in text
    assert "build_specialist_transfer_visit_plan" in text


def test_r4_preserves_existing_orchestration_and_authorities() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (SOURCE, REPORT, ARCHITECTURE, MANIFEST)
    )
    for marker in (
        "scheduler_modified: false",
        "new_scheduler_added: false",
        "new_laboratory_manager_added: false",
        "transport_created: false",
        "eventbus_observation_only: true",
        "sql_remains_authority: true",
        "qdrant_projection_recall_only: true",
    ):
        assert marker in text


def test_r4_has_no_effectful_imports_or_project_mode() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "subprocess",
        "qdrant_client",
        "openvino",
        "sqlite3",
        "psycopg",
        "from observability",
        "from scheduler",
        "import scheduler",
        "LaboratoryManager(",
        "from context.github",
    ):
        assert forbidden not in text
