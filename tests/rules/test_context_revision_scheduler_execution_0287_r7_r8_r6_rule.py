from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/context_revision_scheduler_execution_0287.py"
EVENTS = ROOT / "src/contracts/event.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R8_R6_CONTEXT_REVISION_SCHEDULER_EXECUTION_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/CONTEXT_REVISION_SCHEDULER_EXECUTION_0287_R7_R8_R6.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R8_R6_CONTEXT_REVISION_SCHEDULER_EXECUTION.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R8_R6_CONTEXT_REVISION_SCHEDULER_EXECUTION.md"


def test_r8_r6_reuses_scheduler_eventbus_and_controlproxy_boundaries() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "SchedulerContextImpactExecutionHandler",
        "EventType.CONTEXT_IMPACT_EXECUTION",
        "EventType.CONTEXT_IMPACT_EXECUTION_RESULT",
        "EventType.LABORATORY_CONTEXT_UPDATE",
        "missipy.scheduler.route_adapter_request.v1",
        "controlproxy_is_transport_only",
        "sql_revision_is_authority",
    ):
        assert marker in text

    assert "class Scheduler(" not in text
    assert "class EventBus(" not in text
    assert "class ControlProxy(" not in text
    assert "LaboratoryManager" not in text


def test_r8_r6_adds_event_types_without_replacing_existing_ones() -> None:
    text = EVENTS.read_text(encoding="utf-8")
    for marker in (
        "CONTEXT_REQUEST = auto()",
        "CONTEXT_REPLY = auto()",
        "CONTEXT_IMPACT_EXECUTION = auto()",
        "CONTEXT_IMPACT_EXECUTION_RESULT = auto()",
        "LABORATORY_CONTEXT_UPDATE = auto()",
        "LABORATORY_VISIT_REQUEST = auto()",
        "LABORATORY_VISIT_RESULT = auto()",
    ):
        assert marker in text


def test_current_roadmap_records_r8_r6_closure_and_r9_next() -> None:
    text = CURRENT.read_text(encoding="utf-8")
    assert "0287-r7-r8-r6 — authorized context-impact execution" in text
    assert "ControlProxy is called only for an explicit transport transition" in text
    assert "0287-r7-r9 — love-study contracts and specialist descriptors" in text


def test_r8_r6_deliverables_record_boundaries_and_installation_review() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")

    for marker in (
        "Scheduler authorization + exact plan digest",
        "ControlProxy remains transport-only",
        "INSTALLATION.md` was reviewed and remains",
        "85 reconstructed",
    ):
        assert marker in report

    assert "Context change and route change are independent" in architecture
    assert "## Explicitly unchanged" in manifest
    assert "INSTALLATION.md" in manifest
