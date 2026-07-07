from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_context_recall_integration.py"
DOC = ROOT / "doc" / "architecture" / "CONTEXT_RECALL_INTEGRATION_AUDIT_0213.md"
RULE = ROOT / "doc" / "code-rules" / "0213_context_recall_integration_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0213_CHANGED_FILES.md"


def test_0213_tool_is_context_recall_audit_only() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0213 is the Bloc G context recall integration audit only",
        "controlled_sql_qdrant_projection_acceptance.json",
        "context_recall_integration_audit.json",
        "Reuse/adapt existing surfaces first",
        "0213 must audit existing context, recall, sql_ref, rehydrate, and response",
        "0213 does not execute recall",
        "0213 does not query Qdrant",
        "0213 does not read SQL records",
        "0213 does not write SQL",
        "0213 does not write Qdrant",
        "0213 does not add a new inference path",
        "0213 does not execute Scheduler.run",
        "0213 does not write ControlProxy or RouteProxy frames",
        "Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate",
        "0214-context_recall_integration_plan",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0213_doc_locks_context_recall_audit_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0213 opens Bloc G with context recall integration audit",
        "The input is controlled_sql_qdrant_projection_acceptance.json",
        "The output is context_recall_integration_audit.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0213 does not execute recall",
        "0213 does not query Qdrant",
        "0213 does not read SQL records",
        "context/query -> Qdrant recall -> sql_ref -> SQL rehydrate -> response artifact",
    ]:
        assert token in doc


def test_0213_rule_requires_audit_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_sql_qdrant_projection_acceptance.json from 0212",
        "Audit context/query surfaces",
        "Audit recall/Qdrant surfaces",
        "Audit sql_ref rehydrate surfaces",
        "Audit response/result artifact surfaces",
        "Do not execute recall in 0213",
        "Do not query Qdrant in 0213",
        "Do not read SQL records in 0213",
        "Do not write SQL in 0213",
        "Do not write Qdrant in 0213",
        "Allow P0214 to plan context recall integration only after audit",
    ]:
        assert token in rule


def test_0213_manifest_lists_context_recall_audit_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_context_recall_integration.py",
        "tests/tools/test_audit_context_recall_integration_0213.py",
        "tests/rules/test_context_recall_integration_audit_0213_rule.py",
        "doc/architecture/CONTEXT_RECALL_INTEGRATION_AUDIT_0213.md",
        "doc/code-rules/0213_context_recall_integration_audit_rule.md",
    ]:
        assert token in manifest
