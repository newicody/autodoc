from pathlib import Path

from context.passive_supervisor_visual_pipeline_0238 import (
    VISUAL_PIPELINE_AUTHORITY_BOUNDARY,
    run_visual_pipeline,
    visual_pipeline_commands,
    visual_pipeline_paths,
)


def test_visual_pipeline_paths_are_ordered_reports(tmp_path: Path) -> None:
    paths = visual_pipeline_paths(tmp_path)

    assert paths["all_surfaces_smoke"].name == "all_surfaces_passive_supervisor_smoke_0234.json"
    assert paths["visual_read_model"].name == "passive_supervisor_visual_read_model_0236.json"
    assert paths["visual_layout_model"].name == "passive_supervisor_visual_layout_model_0237.json"
    assert paths["visual_pipeline"].name == "passive_supervisor_visual_pipeline_0238.json"


def test_visual_pipeline_commands_compose_existing_tools(tmp_path: Path) -> None:
    commands = visual_pipeline_commands(
        repo_root=Path("/repo"),
        report_dir=tmp_path,
        python_executable="python",
    )

    assert [step["name"] for step in commands] == [
        "all_surfaces_passive_supervisor_smoke_0234",
        "passive_supervisor_visual_read_model_0236",
        "passive_supervisor_visual_layout_model_0237",
    ]
    assert "run_all_surfaces_passive_supervisor_smoke_0234.py" in commands[0]["command"][1]
    assert "run_passive_supervisor_visual_read_model_0236.py" in commands[1]["command"][1]
    assert "run_passive_supervisor_visual_layout_model_0237.py" in commands[2]["command"][1]


def test_run_visual_pipeline_with_fake_runner_writes_summary(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_runner(command):
        calls.append(list(command))
        return {"returncode": 0, "stdout": "ok\n", "stderr": ""}

    summary = run_visual_pipeline(
        repo_root=Path("/repo"),
        report_dir=tmp_path,
        python_executable="python",
        runner=fake_runner,
    )

    assert summary["passive_supervisor_visual_pipeline_written"] is True
    assert len(calls) == 3
    assert Path(summary["outputs"]["visual_pipeline"]).exists()


def test_visual_pipeline_boundary_is_read_only() -> None:
    assert VISUAL_PIPELINE_AUTHORITY_BOUNDARY == {
        "read_only_visual_pipeline": True,
        "uses_scheduler_run": False,
        "creates_eventbus": False,
        "controls_proxy": False,
        "mutates_shm": False,
        "decides_policy": False,
        "writes_sql": False,
        "writes_qdrant": False,
        "mutates_github": False,
        "requires_non_stdlib": False,
    }
