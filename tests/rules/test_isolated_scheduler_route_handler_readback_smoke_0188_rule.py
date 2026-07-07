from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "readback_isolated_scheduler_route_handler_smoke.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_SCHEDULER_ROUTE_HANDLER_READBACK_SMOKE_0188.md"
RULE = ROOT / "doc" / "code-rules" / "0188_isolated_scheduler_route_handler_readback_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0188_CHANGED_FILES.md"


def test_0188_tool_allows_only_isolated_readback() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0188 is a controlled isolated readback smoke",
        "isolated_scheduler_route_handler_smoke.jsonl",
        "isolated_scheduler_route_handler_readback_smoke.jsonl",
        "read_route_frame",
        "It must not call handle_scheduler_route_command",
        "It must not call handle_scheduler_route_request",
        "It must not request writer permits",
        "It must not call write_route_frame",
        "It must not modify Scheduler.run",
        "It must not instantiate Scheduler",
        "It must not instantiate EventBus",
        "It must not write ControlProxy frames",
        "network_used",
    ]:
        assert token in source
    assert "handle_scheduler_route_command(" not in source
    assert "handle_scheduler_route_request(" not in source
    assert "request_writer_permit(" not in source
    assert "write_route_frame(" not in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source


def test_0188_doc_locks_isolated_readback_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0188 reads back frames written by 0187, but does not call the handler",
        "The input is isolated_scheduler_route_handler_smoke.jsonl",
        "The output is isolated_scheduler_route_handler_readback_smoke.jsonl",
        "It may call read_route_frame",
        "It must not call write_route_frame",
        "It must verify no new frame files are created by readback",
        "This proves isolated RouteProxy write/read smoke",
    ]:
        assert token in doc


def test_0188_rule_blocks_handler_and_writer_paths() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_scheduler_route_handler_smoke.jsonl from 0187",
        "Call read_route_frame only for written_route_refs from 0187",
        "Do not call handle_scheduler_route_command",
        "Do not call handle_scheduler_route_request",
        "Do not request writer permits",
        "Do not call write_route_frame",
        "Verify readback does not create new frame files",
        "Do not write ControlProxy frames",
    ]:
        assert token in rule


def test_0188_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--smoke" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0188_manifest_lists_readback_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/readback_isolated_scheduler_route_handler_smoke.py",
        "tests/tools/test_readback_isolated_scheduler_route_handler_smoke_0188.py",
        "tests/rules/test_isolated_scheduler_route_handler_readback_smoke_0188_rule.py",
        "doc/architecture/ISOLATED_SCHEDULER_ROUTE_HANDLER_READBACK_SMOKE_0188.md",
        "doc/code-rules/0188_isolated_scheduler_route_handler_readback_smoke_rule.md",
    ]:
        assert token in manifest
