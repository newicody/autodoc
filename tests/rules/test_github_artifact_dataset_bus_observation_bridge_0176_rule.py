from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "context" / "github_artifact_dataset_bus_observation.py"
TOOL = ROOT / "tools" / "project_github_artifact_dataset_bus_observation.py"
DOC = ROOT / "doc" / "architecture" / "GITHUB_ARTIFACT_DATASET_BUS_OBSERVATION_BRIDGE_0176.md"
RULE = ROOT / "doc" / "code-rules" / "0176_github_artifact_dataset_bus_observation_bridge_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0176_CHANGED_FILES.md"


def test_0176_module_reuses_existing_runtime_schema() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for token in [
        "from runtime.shm_runtime_schema import",
        "EventBusMessage",
        "ContextBusMessage",
        "EventBusMessage.from_mapping",
        "ContextBusMessage.from_mapping",
        "does not define a new bus message schema",
        "does not create EventBus",
        "does not write to VisPy",
        "does not call GitHub",
    ]:
        assert token in source
    assert "class EventBusMessage" not in source
    assert "class ContextBusMessage" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0176_doc_locks_bridge_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0176 is a bridge to existing event.bus/context.bus messages",
        "It reuses runtime.shm_runtime_schema EventBusMessage and ContextBusMessage",
        "It does not create a new bus",
        "It does not write directly to VisPy",
        "It does not modify Scheduler.run()",
        "GitHub remains workflow/exchange/validation surface",
        "dataset outcome -> existing bus facts -> bus_visualization_adapter",
    ]:
        assert token in doc


def test_0176_rule_blocks_parallel_bus_and_scheduler_bypass() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Reuse runtime.shm_runtime_schema EventBusMessage and ContextBusMessage",
        "Do not define replacement EventBusMessage or ContextBusMessage classes",
        "Do not instantiate EventBus",
        "Do not modify Scheduler.run()",
        "Do not write directly to VisPy",
        "Do not call the GitHub API",
        "Bus facts are observation-only",
    ]:
        assert token in rule


def test_0176_tool_requires_explicit_runtime_root_for_writes() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--runtime-root" in source
    assert "append_github_artifact_dataset_bus_observation" in source
    assert "build_github_artifact_dataset_bus_observation" in source
    assert "requests" not in source
    assert "urllib" not in source


def test_0176_manifest_lists_bridge_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "src/context/github_artifact_dataset_bus_observation.py",
        "tools/project_github_artifact_dataset_bus_observation.py",
        "tests/context/test_github_artifact_dataset_bus_observation_0176.py",
        "tests/tools/test_project_github_artifact_dataset_bus_observation_0176.py",
        "tests/rules/test_github_artifact_dataset_bus_observation_bridge_0176_rule.py",
    ]:
        assert token in manifest
