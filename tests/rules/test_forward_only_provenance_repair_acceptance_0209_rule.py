from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "write_forward_only_provenance_repair_acceptance.py"
DOC = ROOT / "doc" / "architecture" / "FORWARD_ONLY_PROVENANCE_REPAIR_ACCEPTANCE_0209.md"
RULE = ROOT / "doc" / "code-rules" / "0209_forward_only_provenance_repair_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0209_CHANGED_FILES.md"


def test_0209_tool_writes_forward_only_repair_acceptance_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0209 is the Bloc E forward-only provenance repair acceptance patch",
        "provenance_repair_plan.json",
        "provenance_repair_acceptance.json only",
        "Reuse/adapt existing surfaces first",
        "0209 must write a forward-only provenance repair artifact",
        "0209 repairs source_baseline_ref by forward-only acceptance artifact",
        "0209 repairs source_entry_digest by forward-only acceptance artifact",
        "0209 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "0209 does not rewrite runtime history",
        "0209 does not write SQL",
        "0209 does not write Qdrant",
        "0209 does not execute Scheduler.run",
        "0209 does not call mark_route_frame_stale",
        "0209 does not write ControlProxy or RouteProxy frames",
        "0209 closes Bloc E only by writing provenance_repair_acceptance.json",
        "0210-sql_qdrant_projection_readiness_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0209_doc_locks_forward_only_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0209 closes Bloc E with forward-only provenance repair acceptance",
        "The input is provenance_repair_plan.json",
        "The output is provenance_repair_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0209 writes only the forward-only repair acceptance artifact",
        "0209 does not rewrite runtime history",
        "0209 does not write SQL or Qdrant",
        "The next recommended patch is P0210 SQL/Qdrant projection readiness audit",
    ]:
        assert token in doc


def test_0209_rule_requires_forward_only_acceptance() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read provenance_repair_plan.json from 0208",
        "Write provenance_repair_acceptance.json only",
        "Repair source_baseline_ref by forward-only artifact",
        "Repair source_entry_digest by forward-only artifact",
        "Do not rewrite runtime history in 0209",
        "Do not write SQL in 0209",
        "Do not write Qdrant in 0209",
        "Do not write ControlProxy or RouteProxy frames in 0209",
        "Open Bloc F only after acceptance",
    ]:
        assert token in rule


def test_0209_manifest_lists_forward_only_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/write_forward_only_provenance_repair_acceptance.py",
        "tests/tools/test_write_forward_only_provenance_repair_acceptance_0209.py",
        "tests/rules/test_forward_only_provenance_repair_acceptance_0209_rule.py",
        "doc/architecture/FORWARD_ONLY_PROVENANCE_REPAIR_ACCEPTANCE_0209.md",
        "doc/code-rules/0209_forward_only_provenance_repair_acceptance_rule.md",
    ]:
        assert token in manifest
