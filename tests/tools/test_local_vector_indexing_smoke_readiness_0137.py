from __future__ import annotations

from pathlib import Path

from tools.plan_local_vector_indexing_smoke import (
    EXPECTED_SURFACES,
    build_local_vector_indexing_smoke_readiness,
    main,
)


def _make_surface_files(root: Path) -> None:
    for _, path, _ in EXPECTED_SURFACES:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# existing surface\n", encoding="utf-8")


def test_readiness_report_detects_all_existing_surfaces(tmp_path: Path) -> None:
    _make_surface_files(tmp_path)

    report = build_local_vector_indexing_smoke_readiness(tmp_path)

    assert report.ready_for_local_smoke is True
    assert report.missing_paths == ()
    mapping = report.to_mapping()
    assert mapping["decision"] == "reuse_existing_surfaces_before_runtime_extension"
    assert mapping["scheduler_remains_orchestrator"] is True
    assert mapping["openvino_import_boundary"] == "src/inference/openvino_runtime.py"
    assert mapping["qdrant_projection_boundary"] == "src/inference/qdrant_projection_adapter.py"


def test_readiness_report_lists_missing_paths_without_creating_files(tmp_path: Path) -> None:
    report = build_local_vector_indexing_smoke_readiness(tmp_path)

    assert report.ready_for_local_smoke is False
    assert set(report.missing_paths) == {path for _, path, _ in EXPECTED_SURFACES}
    assert not (tmp_path / "src").exists()


def test_readiness_markdown_presents_steps_before_first_real_test(tmp_path: Path) -> None:
    _make_surface_files(tmp_path)
    report = build_local_vector_indexing_smoke_readiness(tmp_path)

    markdown = report.to_markdown()

    assert "Local vector indexing smoke readiness" in markdown
    assert "Next steps before the first real test" in markdown
    assert "run OpenVINO/E5 smoke through the existing inference membrane only" in markdown
    assert "run Qdrant projection smoke through the existing Qdrant adapter only" in markdown
    assert "VectorOpenVINOEmbeddingAdapter" in markdown


def test_cli_returns_zero_when_surfaces_are_present(tmp_path: Path, capsys) -> None:
    _make_surface_files(tmp_path)

    exit_code = main([str(tmp_path), "--format", "json"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert '"ready_for_local_smoke": true' in output


def test_cli_returns_two_when_surfaces_are_missing(tmp_path: Path, capsys) -> None:
    exit_code = main([str(tmp_path), "--format", "markdown"])

    assert exit_code == 2
    output = capsys.readouterr().out
    assert "ready_for_local_smoke: `false`" in output
