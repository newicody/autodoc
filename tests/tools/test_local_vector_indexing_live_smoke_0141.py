from __future__ import annotations

import json
from pathlib import Path

from tools.run_local_vector_indexing_live_smoke import (
    build_local_vector_indexing_smoke_plan,
    inspect_machine_vector_source,
    load_vector_json,
    main,
    validate_vector,
)


def _create_surface(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# existing surface\n", encoding="utf-8")


def _create_all_surfaces(root: Path) -> None:
    for relative in (
        "tools/run_openvino_e5_live_smoke.py",
        "tools/run_qdrant_projection_live_smoke.py",
        "tools/embed_e5.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/openvino_runtime.py",
        "src/inference/qdrant_projection_adapter.py",
        "src/context/vector_indexing_job_plan.py",
        "src/context/sql_context_store.py",
    ):
        _create_surface(root, relative)


def test_0141_plan_reports_ready_when_existing_surfaces_are_present(tmp_path: Path) -> None:
    _create_all_surfaces(tmp_path)

    plan = build_local_vector_indexing_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/vector-indexing/0141",
        text="local vector indexing smoke",
        execute=False,
        strict_vector_handoff=False,
        vector_json=None,
    )

    assert plan.ready is True
    assert plan.ready_for_strict_vector_handoff is False
    markdown = plan.to_markdown()
    assert "ready_for_local_vector_indexing_smoke: `true`" in markdown
    assert "reuses tools/run_openvino_e5_live_smoke.py for OpenVINO/E5 execution" in markdown
    assert "reuses tools/run_qdrant_projection_live_smoke.py for Qdrant projection" in markdown
    assert "does not create LocalVectorIndexingOrchestrator" in markdown


def test_0141_plan_reports_missing_surfaces_without_running_backend(tmp_path: Path) -> None:
    plan = build_local_vector_indexing_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/vector-indexing/0141",
        text="passage: already prefixed",
        execute=False,
        strict_vector_handoff=False,
        vector_json=None,
    )

    assert plan.ready is False
    assert {surface.key for surface in plan.missing_surfaces()} == {
        "openvino_live_smoke_tool",
        "qdrant_projection_smoke_tool",
        "embed_e5_cli",
        "openvino_embedding_membrane",
        "openvino_runtime_boundary",
        "qdrant_projection_adapter",
        "vector_indexing_job_plan",
        "sql_context_store",
    }


def test_0141_accepts_machine_readable_vector_json(tmp_path: Path) -> None:
    vector_path = tmp_path / "vector.json"
    vector = [1.0] + [0.0] * 383
    vector_path.write_text(json.dumps({"vector": vector}), encoding="utf-8")

    probe = inspect_machine_vector_source(vector_path, expected_dimension=384)

    assert probe.available is True
    assert probe.dimension == 384
    assert probe.l2_norm == 1.0
    assert load_vector_json(vector_path) == tuple(vector)


def test_0141_rejects_wrong_dimension_vector_json(tmp_path: Path) -> None:
    vector_path = tmp_path / "vector.json"
    vector_path.write_text(json.dumps([1.0, 0.0]), encoding="utf-8")

    probe = inspect_machine_vector_source(vector_path, expected_dimension=384)

    assert probe.available is False
    assert "vector dimension must be 384" in probe.reason


def test_0141_cli_dry_run_returns_zero_when_surfaces_exist(tmp_path: Path, capsys) -> None:
    _create_all_surfaces(tmp_path)

    rc = main((str(tmp_path), "--model-dir", str(tmp_path / "model"), "--format", "markdown"))

    assert rc == 0
    out = capsys.readouterr().out
    assert "# Local vector indexing live smoke plan" in out
    assert "ready_for_local_vector_indexing_smoke: `true`" in out


def test_0141_vector_validation_requires_positive_norm() -> None:
    try:
        validate_vector((0.0,) * 384, expected_dimension=384)
    except ValueError as exc:
        assert "vector norm must be finite and > 0" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("validate_vector should reject zero vectors")
