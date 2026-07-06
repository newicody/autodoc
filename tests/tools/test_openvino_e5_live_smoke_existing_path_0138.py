from __future__ import annotations

from pathlib import Path

from tools.run_openvino_e5_live_smoke import build_openvino_e5_smoke_plan, main


def _create_surface(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# existing surface\n", encoding="utf-8")


def test_openvino_e5_smoke_plan_reports_ready_when_existing_surfaces_are_present(tmp_path: Path) -> None:
    _create_surface(tmp_path, "tools/embed_e5.py")
    _create_surface(tmp_path, "src/inference/openvino_embedding_adapter.py")
    _create_surface(tmp_path, "src/inference/openvino_runtime.py")

    plan = build_openvino_e5_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        query_text="find scheduler route frames",
        passage_text="scheduler route frames are indexed later",
        execute=False,
    )

    assert plan.ready is True
    assert plan.commands[0].argv[-1].startswith("query: ")
    assert plan.commands[1].argv[-1].startswith("passage: ")
    assert "ready_for_openvino_e5_smoke: `true`" in plan.to_markdown()
    assert "tools/embed_e5.py" in plan.to_markdown()


def test_openvino_e5_smoke_plan_reports_missing_surfaces_without_running_backend(tmp_path: Path) -> None:
    plan = build_openvino_e5_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        query_text="query: already prefixed",
        passage_text="passage: already prefixed",
        execute=False,
    )

    assert plan.ready is False
    assert {surface.key for surface in plan.missing_surfaces()} == {
        "embed_e5_cli",
        "openvino_embedding_membrane",
        "openvino_runtime_boundary",
    }


def test_openvino_e5_smoke_cli_dry_run_returns_zero_when_surfaces_exist(tmp_path: Path, capsys) -> None:
    _create_surface(tmp_path, "tools/embed_e5.py")
    _create_surface(tmp_path, "src/inference/openvino_embedding_adapter.py")
    _create_surface(tmp_path, "src/inference/openvino_runtime.py")

    rc = main((str(tmp_path), "--model-dir", str(tmp_path / "model"), "--format", "markdown"))

    assert rc == 0
    out = capsys.readouterr().out
    assert "# OpenVINO/E5 live smoke plan" in out
    assert "--model-dir" in out


def test_openvino_e5_smoke_cli_dry_run_returns_two_when_surface_missing(tmp_path: Path) -> None:
    assert main((str(tmp_path), "--model-dir", str(tmp_path / "model"))) == 2
