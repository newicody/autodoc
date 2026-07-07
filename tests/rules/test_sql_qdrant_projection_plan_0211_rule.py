from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_sql_qdrant_projection.py"
DOC = ROOT / "doc" / "architecture" / "SQL_QDRANT_PROJECTION_PLAN_0211.md"
RULE = ROOT / "doc" / "code-rules" / "0211_sql_qdrant_projection_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0211_CHANGED_FILES.md"


def test_0211_tool_is_projection_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0211 is the Bloc F SQL/Qdrant projection plan only",
        "sql_qdrant_projection_readiness_audit.json",
        "sql_qdrant_projection_plan.json",
        "Reuse/adapt existing surfaces first",
        "0211 must reuse the 0210 readiness audit",
        "0211 does not write SQL",
        "0211 does not write Qdrant",
        "0211 does not add a new SQL backend",
        "0211 does not add a new Qdrant backend",
        "0211 does not rewrite runtime history",
        "0211 does not execute Scheduler.run",
        "0211 does not import runtime handler modules",
        "0211 does not write ControlProxy or RouteProxy frames",
        "SQL remains durable authority",
        "Qdrant remains projection/search/recall only",
        "Qdrant payloads must carry sql_ref",
        "Qdrant recall must rehydrate from SQL",
        "0212-controlled_sql_qdrant_projection_acceptance",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0211_doc_locks_projection_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0211 creates the SQL/Qdrant projection plan",
        "The input is sql_qdrant_projection_readiness_audit.json",
        "The output is sql_qdrant_projection_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0211 does not write SQL or Qdrant",
        "SQL remains durable authority",
        "Qdrant remains projection/search/recall only",
        "P0212 may execute controlled SQL/Qdrant projection acceptance",
    ]:
        assert token in doc


def test_0211_rule_requires_projection_plan_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read sql_qdrant_projection_readiness_audit.json from 0210",
        "Plan SQL/Qdrant projection only",
        "Select SQL authority surface",
        "Select Qdrant projection surface",
        "Select SQL rehydrate surface",
        "Do not write SQL in 0211",
        "Do not write Qdrant in 0211",
        "Do not add a new SQL backend",
        "Do not add a new Qdrant backend",
        "Qdrant payloads must carry sql_ref",
        "Allow P0212 to execute controlled SQL/Qdrant projection acceptance",
    ]:
        assert token in rule


def test_0211_manifest_lists_projection_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_sql_qdrant_projection.py",
        "tests/tools/test_plan_sql_qdrant_projection_0211.py",
        "tests/rules/test_sql_qdrant_projection_plan_0211_rule.py",
        "doc/architecture/SQL_QDRANT_PROJECTION_PLAN_0211.md",
        "doc/code-rules/0211_sql_qdrant_projection_plan_rule.md",
    ]:
        assert token in manifest
