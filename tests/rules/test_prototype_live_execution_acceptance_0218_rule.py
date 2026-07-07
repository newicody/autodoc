from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "execute_prototype_live_execution.py"
DOC = ROOT / "doc" / "architecture" / "PROTOTYPE_LIVE_EXECUTION_ACCEPTANCE_0218.md"
RULE = ROOT / "doc" / "code-rules" / "0218_prototype_live_execution_acceptance_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0218_CHANGED_FILES.md"


def test_0218_tool_executes_real_controlled_prototype() -> None:
    source = TOOL.read_text(encoding="utf-8")
    for token in [
        "0218 is the Bloc H prototype live execution acceptance patch",
        "prototype_live_execution_plan.json",
        "prototype_live_execution_acceptance.json",
        "0218 executes a real controlled prototype, not another contract-only smoke loop",
        "0218 performs controlled local SQL write/read using a stdlib sqlite dev store",
        "0218 performs controlled local Qdrant collection create/recreate",
        "0218 performs controlled local Qdrant point upsert",
        "0218 performs controlled local Qdrant query",
        "0218 extracts payload.sql_ref from Qdrant result",
        "0218 reads the SQL record by sql_ref",
        "0218 writes prototype_live_response.json",
        "0218 must set prototype_success true only when the complete local path succeeds",
        "0218 only allows localhost Qdrant",
        "0218 does not call external network",
        "0218 does not execute Scheduler.run",
        "Bloc H live controlled path",
    ]:
        assert token in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "github.com" not in source


def test_0218_doc_locks_live_execution_acceptance_boundary() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0218 executes and accepts the live controlled prototype",
        "The input is prototype_live_execution_plan.json",
        "The output is prototype_live_execution_acceptance.json",
        "This is not another contract-only smoke loop",
        "P0218 must produce true flags",
        "context/query -> vector -> Qdrant upsert -> Qdrant query -> sql_ref -> SQL read -> rehydrate -> response artifact",
        "0218 performs real local SQL write/read",
        "0218 performs real local Qdrant create/upsert/query",
        "prototype_success must be true only after the complete path succeeds",
    ]:
        assert token in doc


def test_0218_rule_requires_live_execution() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Read prototype_live_execution_plan.json from 0217",
        "Execute the live controlled prototype",
        "Do not create another contract-only smoke loop",
        "Write SQL dev record in 0218",
        "Create or recreate the dedicated local Qdrant collection in 0218",
        "Upsert Qdrant point in 0218",
        "Query Qdrant in 0218",
        "Read SQL record in 0218",
        "Write response artifact in 0218",
        "Require prototype_success true only when all true flags are true",
        "Only localhost Qdrant is allowed",
        "External network remains forbidden",
    ]:
        assert token in rule


def test_0218_manifest_lists_live_execution_acceptance_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "tools/execute_prototype_live_execution.py",
        "tests/tools/test_execute_prototype_live_execution_0218.py",
        "tests/rules/test_prototype_live_execution_acceptance_0218_rule.py",
        "doc/architecture/PROTOTYPE_LIVE_EXECUTION_ACCEPTANCE_0218.md",
        "doc/code-rules/0218_prototype_live_execution_acceptance_rule.md",
    ]:
        assert token in manifest
