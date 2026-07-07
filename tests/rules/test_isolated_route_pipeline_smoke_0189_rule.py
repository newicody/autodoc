from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_isolated_route_pipeline_smoke.py"
DOC = ROOT / "doc" / "architecture" / "ISOLATED_ROUTE_PIPELINE_SMOKE_0189.md"
RULE = ROOT / "doc" / "code-rules" / "0189_isolated_route_pipeline_smoke_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0189_CHANGED_FILES.md"


def test_0189_tool_reuses_stages_and_locks_boundary() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0189 is an isolated pipeline smoke",
        "0179 authorized route request queue handoff",
        "0184 route request to command dry-run plan",
        "0185 SchedulerRouteHandlerCommand builder smoke",
        "0186 isolated handler execution plan",
        "0187 isolated Scheduler route handler smoke",
        "0188 isolated Scheduler route handler readback smoke",
        "It executes the existing handler only through the 0187 isolated smoke stage",
        "POLICY_SCOPED_QUEUE_NAME",
        "scheduler.route_requests.policy_scoped.jsonl",
        "policy scoped queue is empty",
        "It must not modify Scheduler.run",
        "It must not instantiate Scheduler",
        "It must not instantiate EventBus",
        "It must not write ControlProxy frames",
    ]:
        assert token in source
    assert "from kernel.scheduler import Scheduler" not in source
    assert "from kernel.event_bus import EventBus" not in source
    assert "subprocess" not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0189_doc_locks_pipeline_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0189 runs the isolated route pipeline end to end",
        "It reuses 0179, 0184, 0185, 0186, 0187, and 0188",
        "It writes RouteProxy frames only inside isolated_runtime_root",
        "It must not modify Scheduler.run",
        "It must not instantiate EventBus",
        "It must not write ControlProxy frames",
        "This is the first isolated write/read pipeline prototype",
    ]:
        assert token in doc


def test_0189_rule_blocks_production_runtime_paths() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Run only against an explicit isolated_runtime_root",
        "Reuse existing 0179 and 0184 through 0188 stages",
        "Do not add a new runtime handler",
        "Do not modify Scheduler.run",
        "Do not instantiate Scheduler",
        "Do not instantiate EventBus",
        "Do not write ControlProxy frames",
        "Do not call GitHub API",
        "Do not write SQL",
        "Do not write Qdrant",
    ]:
        assert token in rule


def test_0189_tool_has_no_network_imports() -> None:
    source = TOOL.read_text(encoding="utf-8")
    assert "--context-bus" in source
    assert "--isolated-runtime-root" in source
    assert "--output" in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "urllib" not in source


def test_0190_tool_locks_policy_scoped_queue() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "_write_policy_scoped_queue",
        "policy_decision_id",
        "scheduler.route_requests.policy_scoped.jsonl",
        "policy_scoped_queued_count",
        "policy scoped queue is empty",
    ]:
        assert token in source


def test_0189_manifest_lists_pipeline_smoke_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/run_isolated_route_pipeline_smoke.py",
        "tests/tools/test_run_isolated_route_pipeline_smoke_0189.py",
        "tests/rules/test_isolated_route_pipeline_smoke_0189_rule.py",
        "doc/architecture/ISOLATED_ROUTE_PIPELINE_SMOKE_0189.md",
        "doc/code-rules/0189_isolated_route_pipeline_smoke_rule.md",
    ]:
        assert token in manifest
