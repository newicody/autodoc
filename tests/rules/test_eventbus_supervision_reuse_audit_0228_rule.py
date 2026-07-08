from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_0228_rule_requires_audit_before_runtime_sink() -> None:
    text = read("doc/code-rules/0228_eventbus_supervision_reuse_audit_rule.md")
    assert "audit existing EventBus" in text
    assert "reuse or extend" in text
    assert "no new bus" in text
    assert "Scheduler.run" in text
    assert "downstream-only" in text


def test_0228_architecture_keeps_events_jsonl_optional() -> None:
    text = read("doc/architecture/EVENTBUS_SUPERVISION_REUSE_AUDIT_0228.md")
    assert "events.jsonl is optional" in text
    assert "snapshot is optional" in text
    assert "EventBus -> PassiveSupervisorSink -> CellularState" in text
    assert "Scheduler remains the upstream orchestration authority" in text


def test_0228_changelog_mentions_reuse_gate() -> None:
    text = read("doc/CHANGELOG_0228_EVENTBUS_SUPERVISION_REUSE_AUDIT.md")
    assert "reuse audit" in text
    assert "functional resumption gate" in text
    assert "read-only" in text
