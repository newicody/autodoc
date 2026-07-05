from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "ROUTE_MESSAGE_JOURNAL_0090.md"
MODULE = ROOT / "src" / "runtime" / "route_message_journal.py"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0090_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0090_TEST_REPORT.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_0090_doc_locks_recorder_journal_scope() -> None:
    text = _read(DOC)
    required_phrases = [
        "Status: 0090 implementation.",
        "Recorder/journal ingestion for RouteMessage objects drained from an active route",
        "RouteSelectorDrainResult",
        "RouteMessage",
        "deterministic JSONL journal",
        "write_drained_route_messages_journal",
        "load_route_message_journal",
        "No daemon, no service, no OpenRC",
        "No resident watcher",
        "No CLI",
        "No direct mmap read",
        "No notifier ownership",
        "No Scheduler loop modification",
        "Scheduler/policy/zone remain upstream authorities",
        "ControlProxy does not decide security",
        "no live mmap resize",
        "no route generation g2/g3",
        "no drain/closed cleanup",
        "no Qdrant, no LLM, no OpenVINO",
        "journal records are facts, not commands",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_0090_module_is_importable_recorder_boundary_not_service() -> None:
    text = _read(MODULE)
    required_phrases = [
        "Recorder/journal ingestion for drained RouteMessage objects",
        "RouteSelectorDrainResult",
        "RouteMessage",
        "deterministic JSONL",
        "create a daemon",
        "start a service",
        "use OpenRC",
        "run forever",
        "watch ControlFS",
        "sleep or poll",
        "add a CLI",
        "call Scheduler",
        "decide security policy",
        "grant leases",
        "resize live mmap routes",
        "own notifier lifecycle",
        "read mmap routes directly",
        "implement route generation g2/g3",
        "perform drain/closed cleanup",
        "implement inter-process locks",
        "require /dev/shm",
        "use Qdrant",
        "use an LLM",
        "use OpenVINO",
        "not commands",
    ]
    for phrase in required_phrases:
        assert phrase in text

    forbidden_snippets = [
        "argparse",
        "subprocess",
        "while True",
        "time.sleep",
        "MmapFixedSlotRoute",
        "RouteNotifier",
        "authorized = True",
        "policy_decision_id =",
    ]
    for snippet in forbidden_snippets:
        assert snippet not in text


def test_0090_manifest_and_report_preserve_kernel_loop_boundary() -> None:
    manifest = _read(MANIFEST)
    report = _read(REPORT)

    assert "src/runtime/route_message_journal.py" in manifest
    assert "tests/runtime/test_route_message_journal.py" in manifest
    assert "tests/rules/test_route_message_journal_rule.py" in manifest

    forbidden_paths = [
        "src/kernel/scheduler.py",
        "src/kernel/queue.py",
        "src/kernel/dispatcher.py",
        "src/runtime/component.py",
    ]
    for path in forbidden_paths:
        assert path not in manifest

    required_report_phrases = [
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: green",
        "live_path_uses_real_backend: true",
        "context_contract_version: n/a",
        "context_contract_changed: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ]
    for phrase in required_report_phrases:
        assert phrase in report
