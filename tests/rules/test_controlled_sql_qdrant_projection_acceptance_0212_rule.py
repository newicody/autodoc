from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_sql_qdrant_projection.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_SQL_QDRANT_PROJECTION_ACCEPTANCE_0212.md"
RULE = ROOT / "doc" / "code-rules" / "0212_controlled_sql_qdrant_projection_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0212_CHANGED_FILES.md"


def test_0212_tool_accepts_projection_contract_without_backend_writes() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0212 is the Bloc F controlled SQL/Qdrant projection acceptance patch",
        "sql_qdrant_projection_plan.json",
        "controlled_sql_qdrant_projection_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "0212 explicitly unlocks controlled SQL/Qdrant projection acceptance",
        "0212 does not write SQL rows",
        "0212 does not write Qdrant points",
        "0212 does not add a new SQL backend",
        "0212 does not add a new Qdrant backend",
        "0212 does not rewrite runtime history",
        "0212 does not execute Scheduler.run",
        "0212 does not import runtime handler modules",
        "0212 does not write ControlProxy or RouteProxy frames",
        "SQL remains durable authority",
        "Qdrant remains projection/search/recall only",
        "Qdrant payloads must carry sql_ref",
        "Qdrant recall must rehydrate from SQL",
        "0212 closes Bloc F by writing controlled_sql_qdrant_projection_acceptance.json only",
        "0213-context_recall_integration_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0212_doc_locks_controlled_projection_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0212 closes Bloc F with controlled SQL/Qdrant projection acceptance",
        "The input is sql_qdrant_projection_plan.json",
        "The output is controlled_sql_qdrant_projection_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0212 writes no SQL rows and no Qdrant points",
        "Qdrant payloads carry sql_ref",
        "SQL remains durable authority",
        "The next recommended patch is P0213 context recall integration audit",
    ]:
        assert token in doc


def test_0212_rule_requires_acceptance_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read sql_qdrant_projection_plan.json from 0211",
        "Write controlled_sql_qdrant_projection_acceptance.json only",
        "Do not write SQL rows in 0212",
        "Do not write Qdrant points in 0212",
        "Do not add a new SQL backend",
        "Do not add a new Qdrant backend",
        "Require qdrant_payload.sql_ref",
        "Require rehydration from SQL authority",
        "Open Bloc G only after acceptance",
    ]:
        assert token in rule


def test_0212_manifest_lists_projection_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/accept_controlled_sql_qdrant_projection.py",
        "tests/tools/test_accept_controlled_sql_qdrant_projection_0212.py",
        "tests/rules/test_controlled_sql_qdrant_projection_acceptance_0212_rule.py",
        "doc/architecture/CONTROLLED_SQL_QDRANT_PROJECTION_ACCEPTANCE_0212.md",
        "doc/code-rules/0212_controlled_sql_qdrant_projection_acceptance_rule.md",
    ]:
        assert token in manifest
