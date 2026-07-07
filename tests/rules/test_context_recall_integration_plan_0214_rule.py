from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_context_recall_integration.py"
DOC = ROOT / "doc" / "architecture" / "CONTEXT_RECALL_INTEGRATION_PLAN_0214.md"
RULE = ROOT / "doc" / "code-rules" / "0214_context_recall_integration_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0214_CHANGED_FILES.md"


def test_0214_tool_is_context_recall_plan_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0214 is the Bloc G context recall integration plan only",
        "context_recall_integration_audit.json",
        "context_recall_integration_plan.json",
        "Reuse/adapt existing surfaces first",
        "0214 must reuse the 0213 context recall integration audit",
        "0214 does not execute recall",
        "0214 does not query Qdrant",
        "0214 does not read SQL records",
        "0214 does not write SQL",
        "0214 does not write Qdrant",
        "0214 does not add a new inference path",
        "0214 does not execute Scheduler.run",
        "0214 does not write ControlProxy or RouteProxy frames",
        "Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate",
        "0215-controlled_context_recall_integration_acceptance",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0214_doc_locks_context_recall_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0214 creates the context recall integration plan",
        "The input is context_recall_integration_audit.json",
        "The output is context_recall_integration_plan.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0214 does not execute recall",
        "0214 does not query Qdrant",
        "0214 does not read SQL records",
        "P0215 may execute controlled context recall integration acceptance",
    ]:
        assert token in doc


def test_0214_rule_requires_plan_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read context_recall_integration_audit.json from 0213",
        "Plan context recall integration only",
        "Select context/query surface",
        "Select recall/Qdrant surface",
        "Select sql_ref rehydrate surface",
        "Select response/result artifact surface",
        "Do not execute recall in 0214",
        "Do not query Qdrant in 0214",
        "Do not read SQL records in 0214",
        "Do not write SQL in 0214",
        "Do not write Qdrant in 0214",
        "Allow P0215 to execute controlled context recall integration acceptance",
    ]:
        assert token in rule


def test_0214_manifest_lists_context_recall_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_context_recall_integration.py",
        "tests/tools/test_plan_context_recall_integration_0214.py",
        "tests/rules/test_context_recall_integration_plan_0214_rule.py",
        "doc/architecture/CONTEXT_RECALL_INTEGRATION_PLAN_0214.md",
        "doc/code-rules/0214_context_recall_integration_plan_rule.md",
    ]:
        assert token in manifest
