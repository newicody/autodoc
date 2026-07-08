from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_all_surfaces_passive_supervisor_smoke_0234.py"
DOC = ROOT / "doc" / "architecture" / "ALL_SURFACES_PASSIVE_SUPERVISOR_SMOKE_0234.md"


def test_0234_smoke_is_downstream_only_and_does_not_create_bus() -> None:
    text = TOOL.read_text(encoding="utf-8")
    forbidden = (
        "Scheduler.run(",
        "create_eventbus(",
        "write_sql(",
        "upsert(",
        "mutate_github(",
        "write_shm(",
        "decide_policy(",
        "claim_lease(",
    )
    for token in forbidden:
        assert token not in text


def test_0234_contract_mentions_all_planned_surfaces_and_optional_outputs() -> None:
    text = DOC.read_text(encoding="utf-8")
    for token in (
        "Scheduler",
        "RouteProxy",
        "ControlProxy",
        "SHM",
        "Policy",
        "GitHub artifact",
        "SourceCandidate",
        "SQL",
        "Qdrant",
        "Rehydration",
        "Pushback",
        "snapshot optionnel",
        "audit/replay optionnel",
    ):
        assert token in text
