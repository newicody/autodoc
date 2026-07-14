from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_laboratory_message_contract_0284.py"
REPORT = ROOT / "PHASE0284_R3_SPECIALIST_LABORATORY_MESSAGE_CONTRACT_REPORT.md"
ARCH = ROOT / "doc/architecture/SPECIALIST_LABORATORY_MESSAGE_CONTRACT_0284.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R3_SPECIALIST_LABORATORY_MESSAGE_CONTRACT.md"


def test_0284_r3_adds_the_missing_message_contract_and_reuses_existing_frames() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "class SpecialistLaboratoryMessage" in text
    assert "class SpecialistLaboratoryConversation" in text
    assert "build_specialist_demand_message" in text
    assert "build_specialist_opinion_message" in text
    assert "SpecialistDemandFrameLike" in text
    assert "SpecialistOpinionFrameLike" in text
    assert "validate_portable_specialist_visit_contract" in text


def test_0284_r3_does_not_create_parallel_runtime_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "class LaboratoryManager",
        "class SpecialistManager",
        "class SpecialistWorker",
        "class SpecialistScheduler",
        "Scheduler.run =",
        "EventBus(",
        "QdrantClient(",
        "sqlite3.connect(",
        "psycopg.connect(",
        "openvino.Core(",
        "requests.post(",
    )
    assert all(token not in text for token in forbidden)
    assert '"transport_created": False' in text
    assert '"eventbus_command": False' in text
    assert '"scheduler_remains_orchestrator": True' in text


def test_0284_r3_reports_code_rule_and_next_patch_boundaries() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    for text in (report, architecture, manifest):
        assert "message_contract_added: true" in text
        assert "existing_route_frames_reused: true" in text
        assert "transport_created: false" in text
        assert "scheduler_modified: false" in text
        assert "eventbus_observation_only: true" in text
        assert "sql_remains_authority: true" in text
        assert "qdrant_projection_recall_only: true" in text
    assert "live_path_status: n/a" in report
    assert "0284-r4-specialist-laboratory-transfer-contract" in report
