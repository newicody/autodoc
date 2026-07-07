from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "accept_controlled_context_recall_integration.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLLED_CONTEXT_RECALL_INTEGRATION_ACCEPTANCE_0215.md"
RULE = ROOT / "doc" / "code-rules" / "0215_controlled_context_recall_integration_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0215_CHANGED_FILES.md"


def test_0215_tool_accepts_context_recall_contract_without_live_recall() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0215 is the Bloc G controlled context recall integration acceptance patch",
        "context_recall_integration_plan.json",
        "controlled_context_recall_integration_acceptance.json only",
        "Reuse/adapt existing surfaces first",
        "0215 explicitly unlocks controlled context recall integration acceptance",
        "0215 does not perform live Qdrant recall",
        "0215 does not query Qdrant",
        "0215 does not read SQL records",
        "0215 does not write SQL",
        "0215 does not write Qdrant",
        "0215 does not add a new inference path",
        "0215 does not execute Scheduler.run",
        "0215 does not write ControlProxy or RouteProxy frames",
        "Bloc G target path is context/query -> Qdrant recall -> sql_ref -> SQL rehydrate",
        "0215 closes Bloc G by writing controlled_context_recall_integration_acceptance.json only",
        "0216-prototype_readiness_audit",
    ]:
        assert token in source
    assert "from runtime." not in source
    assert "import runtime." not in source
    assert "import requests" not in source
    assert "from requests" not in source


def test_0215_doc_locks_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0215 closes Bloc G with controlled context recall integration acceptance",
        "The input is context_recall_integration_plan.json",
        "The output is controlled_context_recall_integration_acceptance.json",
        "Reuse/adapt existing surfaces first",
        "doc/code-rules/code_rule.md remains the primary rule",
        "0215 does not perform live Qdrant recall",
        "0215 does not query Qdrant",
        "0215 does not read SQL records",
        "The next recommended patch is P0216 prototype readiness audit",
    ]:
        assert token in doc


def test_0215_rule_requires_acceptance_only() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read context_recall_integration_plan.json from 0214",
        "Write controlled_context_recall_integration_acceptance.json only",
        "Do not perform live Qdrant recall in 0215",
        "Do not query Qdrant in 0215",
        "Do not read SQL records in 0215",
        "Do not write SQL in 0215",
        "Do not write Qdrant in 0215",
        "Require controlled recall result sql_ref",
        "Require controlled response artifact",
        "Open Bloc H only after acceptance",
    ]:
        assert token in rule


def test_0215_manifest_lists_context_recall_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/accept_controlled_context_recall_integration.py",
        "tests/tools/test_accept_controlled_context_recall_integration_0215.py",
        "tests/rules/test_controlled_context_recall_integration_acceptance_0215_rule.py",
        "doc/architecture/CONTROLLED_CONTEXT_RECALL_INTEGRATION_ACCEPTANCE_0215.md",
        "doc/code-rules/0215_controlled_context_recall_integration_acceptance_rule.md",
    ]:
        assert token in manifest
