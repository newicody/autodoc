from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/passive_bus_supervisor_cellular_snapshot.py"


def test_0233_reuses_existing_passive_supervisor_module() -> None:
    text = MODULE.read_text(encoding="utf-8")
    assert "def data_surface_supervision_event" in text
    assert "def github_artifact_supervision_event" in text
    assert "class PassiveSupervisorSink" in text


def test_0233_keeps_data_surfaces_observation_only() -> None:
    text = MODULE.read_text(encoding="utf-8")
    section = text.split("def data_surface_supervision_event", 1)[1]
    section = section.split("RUNTIME_SURFACE_CELL_KINDS", 1)[0]
    forbidden = [
        "Scheduler.run(",
        "requests.",
        "github.Github",
        "create_issue",
        "update_issue",
        "upsert(",
        "execute(",
        "write_shm",
        "control_proxy",
        "claim_lease",
    ]
    for needle in forbidden:
        assert needle not in section


def test_0233_keeps_audit_and_snapshot_optional() -> None:
    text = MODULE.read_text(encoding="utf-8")
    section = text.split("def data_surface_supervision_event", 1)[1]
    section = section.split("RUNTIME_SURFACE_CELL_KINDS", 1)[0]
    assert "events.jsonl" not in section
    assert "snapshot.json" not in section


def test_0233_data_surface_refs_are_first_class() -> None:
    text = MODULE.read_text(encoding="utf-8")
    section = text.split("def data_surface_supervision_event", 1)[1]
    section = section.split("RUNTIME_SURFACE_CELL_KINDS", 1)[0]
    assert "artifact_ref" in section
    assert "source_candidate_ref" in section
    assert "sql_ref" in section
    assert "qdrant_ref" in section
