from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "doc" / "architecture" / "PASSIVE_SUPERVISION_EVENTBUS_CONTRACT_0221.md"
RULE = ROOT / "doc" / "code-rules" / "0221_passive_supervision_eventbus_contract_rule.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "221_passive_supervision_eventbus_contract.dot"


def test_0221_contract_keeps_scheduler_upstream_authority() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Scheduler = upstream authority" in text
    assert "Le superviseur ne lance pas Scheduler.run()." in text
    assert "Le superviseur ne decide pas a la place du Scheduler." in text


def test_0221_contract_keeps_eventbus_as_main_path() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "L'EventBus est le transport principal" in text
    assert "EventBus -> superviseur" in text
    assert "EventBus -> events.jsonl -> superviseur" in text
    assert "ne doit pas etre le chemin normal" in text


def test_0221_rule_keeps_passive_supervisor_downstream_only() -> None:
    text = RULE.read_text(encoding="utf-8")

    assert "downstream-only" in text
    assert "call or modify `Scheduler.run()`" in text
    assert "control RouteProxy or ControlProxy" in text
    assert "mutate GitHub" in text
    assert "write SQL or Qdrant" in text


def test_0221_dot_marks_optional_outputs_and_forbidden_edges() -> None:
    text = DOT.read_text(encoding="utf-8")

    assert "EventBus\\ncanonical event transport" in text
    assert "PassiveSupervisorSink\\ndownstream-only" in text
    assert "snapshot.json\\noptional output" in text
    assert "events.jsonl\\noptional audit/replay" in text
    assert "forbidden" in text
