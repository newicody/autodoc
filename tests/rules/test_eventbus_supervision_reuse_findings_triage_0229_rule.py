from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "triage_eventbus_supervision_reuse_findings_0229.py"
DOC = ROOT / "doc" / "architecture" / "EVENTBUS_SUPERVISION_REUSE_FINDINGS_TRIAGE_0229.md"
RULE = ROOT / "doc" / "code-rules" / "0229_eventbus_supervision_reuse_findings_triage_rule.md"


def test_0229_tool_is_read_only_and_does_not_use_scheduler_run() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert "Scheduler.run()" in text
    assert "subprocess.run" not in text
    assert "git " not in text
    assert ".write_text" in text
    assert "writes_sql" in text
    assert "writes_qdrant" in text
    assert "mutates_github" in text


def test_0229_contract_requires_audit_before_functional_resumption() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "0228" in text
    assert "forbidden_runtime_evidence_count" in text
    assert "runtime_review_required" in text
    assert "may_resume_functional_supervision_patch" in text
    assert "EventBus -> PassiveSupervisorSink" in text


def test_0229_code_rule_keeps_supervisor_downstream_only() -> None:
    text = RULE.read_text(encoding="utf-8")
    assert "read-only" in text
    assert "must not call Scheduler.run" in text
    assert "must not create a new EventBus" in text
    assert "must not turn events.jsonl into the live path" in text
