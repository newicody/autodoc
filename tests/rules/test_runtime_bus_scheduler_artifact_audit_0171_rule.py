from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "RUNTIME_BUS_SCHEDULER_ARTIFACT_AUDIT_0171.md"
RULE = ROOT / "doc" / "code-rules" / "0171_runtime_bus_scheduler_artifact_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0171_CHANGED_FILES.md"
VIS_ADAPTER = ROOT / "src" / "runtime" / "bus_visualization_adapter.py"
SCHEDULER_ADAPTER = ROOT / "src" / "runtime" / "scheduler_route_adapter.py"
SCHEDULER_HANDLER = ROOT / "src" / "runtime" / "scheduler_route_handler_minimal.py"
SCHEDULER_HANDSHAKE = ROOT / "src" / "runtime" / "scheduler_route_handshake.py"
SHM_SCHEMA = ROOT / "src" / "runtime" / "shm_runtime_schema.py"


def test_0171_doc_locks_existing_bus_scheduler_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "VisPy/browser views read existing `event.bus/context.bus` facts",
        "must not write directly to VisPy",
        "must not create a parallel bus",
        "existing `event.bus/context.bus` path remains the canonical observation",
        "Scheduler/policy/zone remain the authority",
        "EventBus is observation-only",
        "Events and bus facts are facts, not commands",
        "0171-github_attachment_reference_fetch",
        "superseded",
    ]:
        assert token in doc


def test_0171_code_rule_prevents_parallel_artifact_observation_paths() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Reuse existing event.bus/context.bus observation surfaces",
        "Reuse the existing bus visualization adapter",
        "EventBus is observation-only",
        "facts, not commands",
        "must not create a parallel bus",
        "must not write directly to VisPy",
        "Dataset-local observation files are audit/staging only",
        "Do not modify Scheduler.run()",
    ]:
        assert token in rule


def test_0171_existing_bus_visualization_surface_is_present() -> None:
    source = VIS_ADAPTER.read_text(encoding="utf-8")
    for token in [
        "event_bus.subscribe()",
        "read_existing_bus_visualization_snapshot",
        "drain_existing_event_bus_reader",
        "The adapter reads existing event.bus/context.bus objects",
        "The adapter does not instantiate EventBus",
        "The adapter does not create a parallel bus",
        "EventBus is observation only",
        "Scheduler/policy/zone remain the authority",
    ]:
        assert token in source


def test_0171_existing_scheduler_route_surfaces_are_present() -> None:
    adapter = SCHEDULER_ADAPTER.read_text(encoding="utf-8")
    handler = SCHEDULER_HANDLER.read_text(encoding="utf-8")
    handshake = SCHEDULER_HANDSHAKE.read_text(encoding="utf-8")
    shm_schema = SHM_SCHEMA.read_text(encoding="utf-8")

    for token in [
        "SchedulerRouteRequest",
        "verify authorized=True and policy_decision_id exists",
        "prepare_route_for_scheduler(...)",
        "SchedulerRouteReply",
        "publish adapter facts to event.bus/context.bus",
        "not the Scheduler loop itself",
    ]:
        assert token in adapter

    for token in [
        "SchedulerRouteHandlerCommand",
        "event_bus_observation_only",
        "extends_existing_scheduler_route_handler",
    ]:
        assert token in handler

    for token in [
        "prepare_route_for_scheduler",
        "publish handshake facts to event.bus/context.bus",
        "EVENT_BUS_MESSAGE_SCHEMA",
        "CONTEXT_BUS_MESSAGE_SCHEMA",
    ]:
        assert token in handshake

    for token in [
        "EVENT_BUS_MESSAGE_SCHEMA",
        "CONTEXT_BUS_MESSAGE_SCHEMA",
        "Lightweight fact message for event.bus",
        "Compact active context message for context.bus",
    ]:
        assert token in shm_schema


def test_0171_manifest_lists_only_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "PHASE0171_TEST_REPORT.md",
        "RUNTIME_BUS_SCHEDULER_ARTIFACT_AUDIT_0171.md",
        "0171_runtime_bus_scheduler_artifact_audit_rule.md",
        "171_runtime_bus_scheduler_artifact_audit.dot",
        "test_runtime_bus_scheduler_artifact_audit_0171_rule.py",
    ]:
        assert token in manifest

    assert "src/context/github_attachment_reference_fetch.py" not in manifest
    assert "tools/run_github_attachment_reference_fetch_once.py" not in manifest
