from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MESSAGE_V1 = ROOT / "src/context/specialist_laboratory_message_contract_0284.py"
MESSAGE_V2 = ROOT / "src/context/specialist_laboratory_message_v2_0287.py"
ANALYSIS = ROOT / "src/context/specialist_deep_analysis_contract_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R8_SPECIALIST_MESSAGE_V2_DEEP_ANALYSIS_REPORT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_message_v1_remains_unchanged_and_v2_is_explicit() -> None:
    v1 = MESSAGE_V1.read_text(encoding="utf-8")
    v2 = MESSAGE_V2.read_text(encoding="utf-8")

    assert (
        'SPECIALIST_LABORATORY_MESSAGE_SCHEMA = '
        '"missipy.specialist.laboratory_message.v1"'
    ) in v1
    assert "SpecialistLaboratoryMessageV2" not in v1
    assert "missipy.specialist.laboratory_message.v2" in v2
    assert "missipy.specialist.laboratory_conversation.v2" in v2
    assert "missipy.specialist.artifact_reference.v1" in v2
    assert "missipy.specialist.exchange_error.v1" in v2


def test_v2_contract_locks_digest_idempotency_and_continuation() -> None:
    source = MESSAGE_V2.read_text(encoding="utf-8")

    for marker in (
        "payload_sha256",
        "content_sha256",
        "correlation_ref",
        "idempotency_key",
        "parent_visit_ref",
        "continuation_of_message_ref",
        '"completion"',
        '"error"',
        "scheduler_remains_orchestrator",
        "transport_created",
    ):
        assert marker in source


def test_deep_analysis_preserves_detail_before_liaison_synthesis() -> None:
    source = ANALYSIS.read_text(encoding="utf-8")

    for marker in (
        "missipy.specialist.deep_analysis_request.v1",
        "missipy.specialist.deep_analysis_finding.v1",
        "missipy.specialist.deep_analysis_contribution.v1",
        '"domain_analysis"',
        '"global_synthesis"',
        "uncertainties",
        "contradictions",
        "limitations",
        "recommendations",
        "ready_for_liaison_synthesis",
        "liaison_synthesis_created",
    ):
        assert marker in source


def test_contract_modules_do_not_create_parallel_runtime() -> None:
    combined = MESSAGE_V2.read_text(encoding="utf-8") + ANALYSIS.read_text(
        encoding="utf-8"
    )

    forbidden = (
        "class LaboratoryManager",
        "class SpecialistManager",
        "Scheduler(",
        "import openvino",
        "import qdrant",
        "import psycopg",
        "requests.",
        "urllib.request",
        "subprocess.",
    )
    for marker in forbidden:
        assert marker not in combined


def test_current_roadmap_and_report_close_r8_without_installation_change() -> None:
    current = CURRENT.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    assert "0287-r7-r8 — specialist/laboratory message v2" in current
    assert "Closure status: implemented" in current
    assert "historical v1 message" in current
    assert "code_rule_review: done" in report
    assert "code_rule_update_required: false" in report
    assert "live_path_status: n/a" in report
    assert INSTALLATION.exists()
