from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_controlproxy_routeproxy_coherence_acceptance.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_ROUTEPROXY_COHERENCE_ACCEPTANCE_0206.md"
RULE = ROOT / "doc" / "code-rules" / "0206_controlproxy_routeproxy_coherence_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0206_CHANGED_FILES.md"


def test_0206_tool_executes_controlled_coherence_without_controlproxy_frames() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0206 is the Bloc D ControlProxy RouteProxy coherence acceptance patch",
        "controlproxy_stale_priority_zone_smoke_plan.json",
        "controlproxy_routeproxy_coherence_acceptance.json",
        "tools/run_isolated_route_pipeline_smoke.py",
        "Reuse/adapt existing surfaces first",
        "0206 explicitly unlocks controlled stale priority zone coherence smoke execution",
        "0206 must not add a new ControlProxy runtime",
        "0206 must not add a new RouteProxy runtime",
        "0206 must not add a new Scheduler hook implementation",
        "0206 does not execute Scheduler.run",
        "0206 does not modify Scheduler.run",
        "0206 does not import runtime handler modules directly",
        "0206 does not write ControlProxy frames",
        "0206 does not call mark_route_frame_stale directly",
        "0206 does not call GitHub API or use network",
        "0206 requires RouteProxy writes to stay inside target_isolated_runtime_root",
        "ControlProxy remains coordination, not business authority",
        "Scheduler/policy/zone remain authority",
        "RouteProxy remains the fast data-plane frame surface",
        "controlproxy-routeproxy-stale-priority-zone-coherence-v1",
        "0207-provenance_repair_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0206_doc_locks_coherence_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0206 closes Bloc D with ControlProxy/RouteProxy coherence acceptance",
        "The input is controlproxy_stale_priority_zone_smoke_plan.json",
        "The output is controlproxy_routeproxy_coherence_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0206 unlocks controlled stale priority zone coherence smoke execution",
        "0206 still does not execute Scheduler.run",
        "0206 still does not write ControlProxy frames",
        "The execution surface reused is tools/run_isolated_route_pipeline_smoke.py",
        "The next recommended patch is P0207 provenance repair audit",
    ]:
        assert token in doc


def test_0206_rule_requires_coherence_acceptance_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlproxy_stale_priority_zone_smoke_plan.json from 0205",
        "Reuse tools/run_isolated_route_pipeline_smoke.py",
        "Allow controlled stale priority zone coherence smoke execution in 0206",
        "Do not execute Scheduler.run in 0206",
        "Do not modify Scheduler.run in 0206",
        "Do not write ControlProxy frames in 0206",
        "Do not call mark_route_frame_stale directly in 0206",
        "Require explicit policy_decision_id",
        "Require RouteProxy writes to stay inside target_isolated_runtime_root",
        "Require ControlProxy frames false",
        "Open Bloc E only after acceptance",
    ]:
        assert token in rule


def test_0206_manifest_lists_coherence_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/run_controlproxy_routeproxy_coherence_acceptance.py",
        "tests/tools/test_run_controlproxy_routeproxy_coherence_acceptance_0206.py",
        "tests/rules/test_controlproxy_routeproxy_coherence_acceptance_0206_rule.py",
        "doc/architecture/CONTROLPROXY_ROUTEPROXY_COHERENCE_ACCEPTANCE_0206.md",
        "doc/code-rules/0206_controlproxy_routeproxy_coherence_acceptance_rule.md",
    ]:
        assert token in manifest
