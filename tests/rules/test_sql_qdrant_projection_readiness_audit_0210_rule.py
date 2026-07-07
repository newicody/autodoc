from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_sql_qdrant_projection_readiness.py"
DOC = ROOT / "doc" / "architecture" / "SQL_QDRANT_PROJECTION_READINESS_AUDIT_0210.md"
RULE = ROOT / "doc" / "code-rules" / "0210_sql_qdrant_projection_readiness_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0210_CHANGED_FILES.md"


def test_0210_tool_is_projection_readiness_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0210 is the Bloc F SQL/Qdrant projection readiness audit only",
        "provenance_repair_acceptance.json",
        "sql_qdrant_projection_readiness_audit.json",
        "Reuse/adapt existing surfaces first",
        "0210 must audit existing SQL and Qdrant projection surfaces",
        "0210 does not write SQL",
        "0210 does not write Qdrant",
        "0210 does not add a new SQL backend",
        "0210 does not add a new Qdrant backend",
        "0210 does not rewrite runtime history",
        "0210 does not execute Scheduler.run",
        "0210 does not import runtime handler modules",
        "0210 does not write ControlProxy or RouteProxy frames",
        "SQL remains durable authority",
        "Qdrant remains projection/search/recall only",
        "Qdrant payloads must carry sql_ref",
        "0211-sql_qdrant_projection_plan",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0210_doc_locks_projection_readiness_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0210 opens Bloc F with SQL/Qdrant projection readiness audit",
        "The input is provenance_repair_acceptance.json",
        "The output is sql_qdrant_projection_readiness_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0210 does not write SQL or Qdrant",
        "SQL remains durable authority",
        "Qdrant remains projection/search/recall only",
        "P0211 may plan SQL/Qdrant projection",
    ]:
        assert token in doc


def test_0210_rule_requires_readiness_audit_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read provenance_repair_acceptance.json from 0209",
        "Audit existing SQL and Qdrant projection surfaces",
        "Do not write SQL in 0210",
        "Do not write Qdrant in 0210",
        "Do not add a new SQL backend",
        "Do not add a new Qdrant backend",
        "Qdrant payloads must carry sql_ref",
        "Rehydrate Qdrant results from SQL authority",
        "Allow P0211 to plan SQL/Qdrant projection only after audit",
    ]:
        assert token in rule


def test_0210_manifest_lists_projection_readiness_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_sql_qdrant_projection_readiness.py",
        "tests/tools/test_audit_sql_qdrant_projection_readiness_0210.py",
        "tests/rules/test_sql_qdrant_projection_readiness_audit_0210_rule.py",
        "doc/architecture/SQL_QDRANT_PROJECTION_READINESS_AUDIT_0210.md",
        "doc/code-rules/0210_sql_qdrant_projection_readiness_audit_rule.md",
    ]:
        assert token in manifest
