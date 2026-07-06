from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "audit_existing_runtime_integration.py"
DOC = ROOT / "doc" / "architecture" / "EXISTING_RUNTIME_INTEGRATION_AUDIT_0132.md"
RULE = ROOT / "doc" / "code-rules" / "0132_no_reinvent_runtime_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0132_CHANGED_FILES.md"


def test_0132_docs_lock_no_reinvent_runtime_integration_rule() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0132 is an integration audit, not a new runtime feature",
        "reuse, extend, or modify existing modules before creating a new module",
        "Scheduler.run() must not be modified by integration patches unless a dedicated migration patch explicitly says so",
        "OpenVINO work must first audit existing embedding adapter surfaces",
        "Qdrant work must first audit existing projection adapter surfaces",
        "RouteProxy work must first audit existing /dev/shm runtime surfaces",
        "Fake specialist work must first audit existing handler/worker surfaces",
        "code_rule update required: yes",
        "New module default: forbidden until audit says no existing wheel fits",
    ]
    for phrase in required:
        assert phrase in text


def test_0132_rule_supplement_mentions_main_code_rule_and_decision_gate() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Supplement to doc/code-rules/code_rule.md",
        "No runtime wheel may be added before an existing-runtime audit",
        "Decision must be one of: reuse existing, extend existing, modify existing, or create new with documented gap",
        "Creating a parallel Scheduler, handler, RouteProxy, OpenVINO adapter, Qdrant adapter, SQL store, or EventBus path is forbidden",
    ]
    for phrase in required:
        assert phrase in text


def test_0132_manifest_lists_only_audit_docs_tests_and_tool() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/audit_existing_runtime_integration.py",
        "tests/runtime/test_existing_runtime_integration_audit.py",
        "tests/rules/test_existing_runtime_integration_audit_0132_rule.py",
        "doc/architecture/EXISTING_RUNTIME_INTEGRATION_AUDIT_0132.md",
        "doc/code-rules/0132_no_reinvent_runtime_rule.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/fake_specialist_worker",
        "src/inference/openvino",
        "src/inference/qdrant",
        "requests",
        "socket",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0132_audit_tool_has_no_runtime_backend_imports() -> None:
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
    forbidden = {
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "openvino",
        "qdrant",
        "qdrant_client",
        "psycopg",
        "sqlite3",
        "vispy",
        "src",
    }
    assert sorted(imports & forbidden) == []
