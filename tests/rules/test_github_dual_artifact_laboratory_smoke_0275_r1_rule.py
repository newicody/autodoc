from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST = (
    ROOT
    / "tests/context/test_github_dual_artifact_laboratory_smoke_0275.py"
)


def test_0275_r5_test_uses_current_0274_boundary_signature() -> None:
    text = TEST.read_text(encoding="utf-8")

    assert "monkeypatch.setattr(" in text
    assert (
        '"run_fake_laboratory_existing_scheduler_closed_loop_smoke"'
        in text
    )
    assert "fake_closed_loop" in text
    assert 'FakeLaboratoryClosedLoopSmokeCommand("sc:x")' not in text
    assert "handoff=" not in text
    assert "recall=" not in text
