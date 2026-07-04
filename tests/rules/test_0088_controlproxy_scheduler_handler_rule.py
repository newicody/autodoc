from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "doc/manifests/MANIFEST_0088_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0088_TEST_REPORT.md"
ALIGNMENT = ROOT / "doc/0088_CODE_RULE_ALIGNMENT.md"
HANDLER = ROOT / "src/runtime/controlproxy_scheduler_handler.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0088_documents_code_rule_review_block() -> None:
    text = _read(REPORT) + "\n" + _read(ALIGNMENT)

    assert "code_rule_review: done" in text
    assert "code_rule_update_required: false" in text
    assert "live_path_status: transition" in text
    assert "scheduler_modified: false" in text
    assert "external_dependencies_added: false" in text
    assert "qdrant_added: false" in text
    assert "llm_or_openvino_added: false" in text
    assert "search_commands_bounded: n/a" in text


def test_0088_manifest_keeps_kernel_loop_unchanged() -> None:
    manifest = _read(MANIFEST)

    assert "src/runtime/controlproxy_scheduler_handler.py" in manifest
    assert "tests/runtime/test_controlproxy_scheduler_handler.py" in manifest
    assert "src/kernel/scheduler.py" not in manifest
    assert "src/kernel/queue.py" not in manifest
    assert "src/kernel/dispatcher.py" not in manifest
    assert "src/runtime/component.py" not in manifest


def test_0088_handler_is_importable_boundary_not_operator_or_policy_layer() -> None:
    source = _read(HANDLER)

    assert "handle_scheduler_route_request" in source
    assert "argparse" not in source
    assert "subprocess" not in source
    assert "OpenRC" not in source
    assert "Service" not in source
    assert "PolicyEngine" not in source
    assert "authorized = True" not in source
    assert "policy_decision_id =" not in source
