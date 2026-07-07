from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_provenance_repair.py"
DOC = ROOT / "doc" / "architecture" / "PROVENANCE_REPAIR_PLAN_0208.md"
RULE = ROOT / "doc" / "code-rules" / "0208_provenance_repair_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0208_CHANGED_FILES.md"


def test_0208_tool_is_forward_only_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0208 is the Bloc E provenance repair plan only",
        "provenance_repair_audit.json",
        "provenance_repair_plan.json",
        "Reuse/adapt existing surfaces first",
        "0208 must plan a forward-only provenance repair",
        "0208 does not repair source_baseline_ref",
        "0208 does not repair source_entry_digest",
        "0208 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "0208 does not rewrite runtime history",
        "0208 does not write SQL",
        "0208 does not write Qdrant",
        "0208 does not execute Scheduler.run",
        "0208 does not call mark_route_frame_stale",
        "0208 does not write ControlProxy or RouteProxy frames",
        "0208 selects source_baseline_ref and source_entry_digest candidates",
        "0209-forward_only_provenance_repair_acceptance",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0208_doc_locks_forward_only_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0208 creates a forward-only provenance repair plan",
        "The input is provenance_repair_audit.json",
        "The output is provenance_repair_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0208 does not repair provenance",
        "0208 does not rewrite runtime history",
        "0208 does not write SQL or Qdrant",
        "P0209 may write the forward-only provenance repair acceptance",
    ]:
        assert token in doc


def test_0208_rule_requires_plan_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read provenance_repair_audit.json from 0207",
        "Plan forward-only provenance repair only",
        "Select source_baseline_ref candidate",
        "Select source_entry_digest candidate",
        "Do not repair source_baseline_ref in 0208",
        "Do not repair source_entry_digest in 0208",
        "Do not rewrite runtime history in 0208",
        "Do not write SQL in 0208",
        "Do not write Qdrant in 0208",
        "Allow P0209 to write provenance_repair_acceptance.json only",
    ]:
        assert token in rule


def test_0208_manifest_lists_provenance_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_provenance_repair.py",
        "tests/tools/test_plan_provenance_repair_0208.py",
        "tests/rules/test_provenance_repair_plan_0208_rule.py",
        "doc/architecture/PROVENANCE_REPAIR_PLAN_0208.md",
        "doc/code-rules/0208_provenance_repair_plan_rule.md",
    ]:
        assert token in manifest
