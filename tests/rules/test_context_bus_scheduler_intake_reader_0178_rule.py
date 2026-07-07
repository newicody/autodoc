from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_artifact_context_bus_scheduler_intake.py"
TOOL = ROOT / "tools" / "build_github_artifact_scheduler_intake_from_context_bus.py"
DOC = ROOT / "doc" / "architecture" / "CONTEXT_BUS_SCHEDULER_INTAKE_READER_0178.md"
RULE = ROOT / "doc" / "code-rules" / "0178_context_bus_scheduler_intake_reader_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0178_CHANGED_FILES.md"


def test_0178_module_closes_direct_json_shortcut() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "0178 closes the direct JSON shortcut",
        "context.bus.jsonl",
        "ContextBusMessage.from_mapping",
        "topic github.artifact_dataset.context",
        "payload_schema missipy.github_artifact.dataset_context.v1",
        "This module does not instantiate EventBus",
        "This module does not modify Scheduler.run()",
        "This module does not call handle_scheduler_route_request",
    ]:
        assert token in source
    assert "from kernel.event_bus import EventBus" not in source
    assert "handle_scheduler_route_request(" not in source


def test_0178_doc_locks_context_bus_path() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0178 closes the shortcut left by 0177",
        "The scheduler intake source is context.bus.jsonl",
        "It reads ContextBusMessage through runtime.shm_runtime_schema",
        "It accepts only topic github.artifact_dataset.context",
        "It accepts only payload_schema missipy.github_artifact.dataset_context.v1",
        "No arbitrary JSON file is a scheduler intake source",
        "Scheduler/policy/zone remain the authority",
    ]:
        assert token in doc


def test_0178_rule_blocks_direct_intake_and_parallel_bus() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read scheduler intake source from context.bus.jsonl",
        "Use ContextBusMessage.from_mapping",
        "Accept only topic github.artifact_dataset.context",
        "Accept only payload_schema missipy.github_artifact.dataset_context.v1",
        "Do not introduce arbitrary direct JSON scheduler intake",
        "Do not instantiate EventBus",
        "Do not modify Scheduler.run()",
        "Do not call handle_scheduler_route_request",
    ]:
        assert token in rule


def test_0178_tool_is_context_bus_reader_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--context-bus" in source
    assert "read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl" in source
    assert "requests" not in source
    assert "urllib" not in source


def test_0178_manifest_lists_reader_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "src/context/github_artifact_context_bus_scheduler_intake.py",
        "tools/build_github_artifact_scheduler_intake_from_context_bus.py",
        "tests/context/test_github_artifact_context_bus_scheduler_intake_0178.py",
        "tests/tools/test_build_github_artifact_scheduler_intake_from_context_bus_0178.py",
        "tests/rules/test_context_bus_scheduler_intake_reader_0178_rule.py",
    ]:
        assert token in manifest
