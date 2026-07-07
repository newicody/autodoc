from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "plan_prototype_live_execution.py"
DOC = ROOT / "doc" / "architecture" / "PROTOTYPE_LIVE_EXECUTION_PLAN_0217.md"
RULE = ROOT / "doc" / "code-rules" / "0217_prototype_live_execution_plan_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0217_CHANGED_FILES.md"


def test_0217_tool_plans_real_execution_not_smoke_loop() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0217 is the Bloc H prototype live execution plan",
        "prototype_live_readiness_audit.json",
        "prototype_live_execution_plan.json",
        "Reuse/adapt existing surfaces first",
        "0217 must plan a real controlled execution for P0218, not another contract-only",
        "0217 does not execute the prototype",
        "0217 does not write SQL",
        "0217 does not create Qdrant collections",
        "0217 does not upsert Qdrant points",
        "0217 does not query Qdrant semantic results",
        "P0218 must execute the live controlled path and produce true flags",
        "sql_written_by_0218",
        "qdrant_written_by_0218",
        "qdrant_queried_by_0218",
        "sql_record_read_by_0218",
        "rehydration_executed_by_0218",
        "response_artifact_written_by_0218",
        "prototype_success",
        "0218-prototype_live_execution_acceptance",
    ]:
        assert token in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "github.com" not in source


def test_0217_doc_locks_live_execution_plan_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0217 creates the prototype live execution plan",
        "The input is prototype_live_readiness_audit.json",
        "The output is prototype_live_execution_plan.json",
        "This is the plan for a real controlled P0218 execution",
        "P0218 must produce true flags",
        "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "0217 does not execute the prototype",
        "0217 does not write SQL or Qdrant",
    ]:
        assert token in doc


def test_0217_rule_requires_live_plan_without_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read prototype_live_readiness_audit.json from 0216",
        "Plan live prototype execution for P0218",
        "Do not create another contract-only smoke loop",
        "Do not execute the prototype in 0217",
        "Do not write SQL in 0217",
        "Do not upsert Qdrant points in 0217",
        "Do not query Qdrant semantic results in 0217",
        "Require P0218 true flags",
        "Allow P0218 to execute the live controlled prototype",
    ]:
        assert token in rule


def test_0217_manifest_lists_live_execution_plan_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/plan_prototype_live_execution.py",
        "tests/tools/test_plan_prototype_live_execution_0217.py",
        "tests/rules/test_prototype_live_execution_plan_0217_rule.py",
        "doc/architecture/PROTOTYPE_LIVE_EXECUTION_PLAN_0217.md",
        "doc/code-rules/0217_prototype_live_execution_plan_rule.md",
    ]:
        assert token in manifest
