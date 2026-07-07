from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_provenance_repair.py"
DOC = ROOT / "doc" / "architecture" / "PROVENANCE_REPAIR_AUDIT_0207.md"
RULE = ROOT / "doc" / "code-rules" / "0207_provenance_repair_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0207_CHANGED_FILES.md"


def test_0207_tool_is_provenance_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0207 is the Bloc E provenance repair audit only",
        "controlproxy_routeproxy_coherence_acceptance.json",
        "provenance_repair_audit.json",
        "Reuse/adapt existing surfaces first",
        "0207 must audit the provenance gap before any provenance repair write is allowed",
        "0207 does not repair source_baseline_ref",
        "0207 does not repair source_entry_digest",
        "0207 does not rewrite controlled_dev_routeproxy_smoke_post_execution_acceptance.json",
        "0207 does not rewrite runtime history",
        "0207 does not write SQL",
        "0207 does not write Qdrant",
        "0207 does not execute Scheduler.run",
        "0207 does not call mark_route_frame_stale",
        "0207 does not write ControlProxy or RouteProxy frames",
        "0207 preserves source_baseline_ref or source_entry_digest missing",
        "0208-provenance_repair_plan",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0207_doc_locks_provenance_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0207 opens Bloc E with a provenance repair audit",
        "The input is controlproxy_routeproxy_coherence_acceptance.json",
        "The output is provenance_repair_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0207 does not repair provenance",
        "0207 does not rewrite runtime history",
        "0207 does not write SQL or Qdrant",
        "P0208 may plan a forward-only provenance repair",
    ]:
        assert token in doc


def test_0207_rule_requires_audit_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlproxy_routeproxy_coherence_acceptance.json from 0206",
        "Audit source_baseline_ref and source_entry_digest",
        "Do not repair source_baseline_ref in 0207",
        "Do not repair source_entry_digest in 0207",
        "Do not rewrite runtime history in 0207",
        "Do not write SQL in 0207",
        "Do not write Qdrant in 0207",
        "Allow P0208 to plan forward-only provenance repair",
    ]:
        assert token in rule


def test_0207_manifest_lists_provenance_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_provenance_repair.py",
        "tests/tools/test_audit_provenance_repair_0207.py",
        "tests/rules/test_provenance_repair_audit_0207_rule.py",
        "doc/architecture/PROVENANCE_REPAIR_AUDIT_0207.md",
        "doc/code-rules/0207_provenance_repair_audit_rule.md",
    ]:
        assert token in manifest
