from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_isolated_scheduler_route_handler_smoke.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_SCHEDULER_ROUTE_HANDLER_SMOKE_0187.md"
RULE = ROOT / "doc" / "code-rules" / "0187_isolated_scheduler_route_handler_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0187_CHANGED_FILES.md"


def test_0187_tool_allows_only_isolated_handler_smoke() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0187 is the first controlled handler smoke",
        "isolated_handler_execution_plan.jsonl",
        "isolated_scheduler_route_handler_smoke.jsonl",
        "handle_scheduler_route_command",
        "RouteProxyRuntimePolicy",
        "It must write only inside the isolated runtime root from the plan",
        "It must not modify Scheduler.run",
        "It must not instantiate Scheduler",
        "It must not instantiate EventBus",
        "It must not write ControlProxy frames",
        "network_used",
    ]:
        assert token in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source
    assert "subprocess" not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0187_doc_locks_isolated_smoke_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0187 executes the existing handler only inside an isolated runtime root",
        "The input is isolated_handler_execution_plan.jsonl",
        "The output is isolated_scheduler_route_handler_smoke.jsonl",
        "It may call handle_scheduler_route_command",
        "It must verify frame paths remain inside isolated_runtime_root",
        "It must not modify Scheduler.run",
        "This is the first RouteProxy frame write smoke",
    ]:
        assert token in doc


def test_0187_rule_blocks_non_isolated_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read isolated_handler_execution_plan.jsonl from 0186",
        "Execute only ready plan items",
        "Call handle_scheduler_route_command only with RouteProxyRuntimePolicy rooted in isolated_runtime_root",
        "Verify written frame paths stay under isolated_runtime_root",
        "Do not modify Scheduler.run",
        "Do not instantiate Scheduler",
        "Do not instantiate EventBus",
        "Do not write ControlProxy frames",
        "Do not call GitHub API",
    ]:
        assert token in rule


def test_0187_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--plan" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0187_manifest_lists_isolated_smoke_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/run_isolated_scheduler_route_handler_smoke.py",
        "tests/tools/test_run_isolated_scheduler_route_handler_smoke_0187.py",
        "tests/rules/test_isolated_scheduler_route_handler_smoke_0187_rule.py",
        "doc/architecture/ISOLATED_SCHEDULER_ROUTE_HANDLER_SMOKE_0187.md",
        "doc/code-rules/0187_isolated_scheduler_route_handler_smoke_rule.md",
    ]:
        assert token in manifest
