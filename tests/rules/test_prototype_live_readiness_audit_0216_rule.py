from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_prototype_live_readiness.py"
DOC = ROOT / "doc" / "architecture" / "PROTOTYPE_LIVE_READINESS_AUDIT_0216.md"
RULE = ROOT / "doc" / "code-rules" / "0216_prototype_live_readiness_audit_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0216_CHANGED_FILES.md"


def test_0216_tool_is_live_readiness_not_contract_only_smoke() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0216 is the Bloc H prototype live readiness audit",
        "controlled_context_recall_integration_acceptance.json",
        "prototype_live_readiness_audit.json",
        "Reuse/adapt existing surfaces first",
        "0216 must prepare a real controlled prototype execution path, not another",
        "0216 allows local readiness probing only when explicitly requested",
        "0216 does not upsert Qdrant points",
        "0216 does not query Qdrant collections for semantic results",
        "0216 does not read SQL records",
        "0216 does not write SQL",
        "0216 does not write Qdrant",
        "Bloc H target is a live controlled prototype",
        "P0218 must produce true flags for SQL write/read, Qdrant upsert/query",
        "0217-prototype_live_execution_plan",
    ]:
        assert token in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "github.com" not in source


def test_0216_doc_locks_live_readiness_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0216 opens Bloc H with prototype live readiness audit",
        "The input is controlled_context_recall_integration_acceptance.json",
        "The output is prototype_live_readiness_audit.json",
        "This is not another contract-only smoke loop",
        "P0218 must produce true flags",
        "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "0216 does not write SQL or Qdrant",
        "0216 may optionally probe localhost Qdrant",
    ]:
        assert token in doc


def test_0216_rule_requires_live_readiness_without_writes() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read controlled_context_recall_integration_acceptance.json from 0215",
        "Audit prototype live readiness",
        "Do not create another contract-only smoke loop",
        "Require P0218 true flags",
        "Only localhost Qdrant probe may be allowed in 0216",
        "Do not write SQL in 0216",
        "Do not write Qdrant in 0216",
        "Do not query Qdrant semantic results in 0216",
        "Do not read SQL records in 0216",
        "Allow P0217 to plan live prototype execution",
    ]:
        assert token in rule


def test_0216_manifest_lists_live_readiness_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/audit_prototype_live_readiness.py",
        "tests/tools/test_audit_prototype_live_readiness_0216.py",
        "tests/rules/test_prototype_live_readiness_audit_0216_rule.py",
        "doc/architecture/PROTOTYPE_LIVE_READINESS_AUDIT_0216.md",
        "doc/code-rules/0216_prototype_live_readiness_audit_rule.md",
    ]:
        assert token in manifest
