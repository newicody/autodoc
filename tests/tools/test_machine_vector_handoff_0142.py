from __future__ import annotations

import json
from pathlib import Path
import subprocess

from tools.run_local_vector_indexing_live_smoke import (
    build_local_vector_indexing_smoke_plan,
    generate_machine_vector_json,
    load_vector_json,
)
from tools.run_qdrant_projection_live_smoke import (
    build_qdrant_projection_smoke_plan,
    load_machine_vector_json,
)


def _create_surface(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# existing surface\n", encoding="utf-8")


def _create_all_local_surfaces(root: Path) -> None:
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


def _unit_vector() -> list[float]:
    return [1.0] + [0.0] * 383


def test_0142_qdrant_plan_accepts_machine_vector_json(tmp_path: Path) -> None:
    vector_path = tmp_path / "e5-vector.json"
    vector_path.write_text(json.dumps({"vector": _unit_vector()}), encoding="utf-8")
    _create_surface(tmp_path, "src/inference/qdrant_projection_adapter.py")
    _create_surface(tmp_path, "src/context/vector_collection_registry.py")
    _create_surface(tmp_path, "src/context/vector_indexing_job_plan.py")

    plan = build_qdrant_projection_smoke_plan(
        tmp_path,
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/vector-indexing/0142",
        execute=False,
        vector_json=vector_path,
    )

    assert plan.ready is True
    assert plan.vector_json == vector_path
    assert load_machine_vector_json(vector_path, expected_dimension=384) == tuple(_unit_vector())
    markdown = plan.to_markdown()
    assert "machine_vector_handoff: `true`" in markdown
    assert "--vector-json enables strict machine-vector handoff without creating a new adapter" in markdown


def test_0142_local_plan_auto_vector_json_passes_file_to_qdrant_tool(tmp_path: Path) -> None:
    _create_all_local_surfaces(tmp_path)

    plan = build_local_vector_indexing_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/vector-indexing/0142",
        text="passage: strict vector handoff",
        execute=False,
        strict_vector_handoff=True,
        vector_json=None,
        auto_vector_json=True,
    )

    assert plan.vector_json == tmp_path / ".var" / "smoke" / "e5_vector_0142.json"
    assert plan.auto_vector_json is True
    assert "--vector-json" in plan.commands[1].argv
    assert str(plan.vector_json) in plan.commands[1].argv
    assert "strict full-vector handoff reuses tools/embed_e5.py --format json --full-vector" in plan.to_markdown()


def test_0142_generate_machine_vector_json_reuses_existing_embed_cli(monkeypatch, tmp_path: Path) -> None:
    _create_all_local_surfaces(tmp_path)
    output_vector = {"model": "openvino.embedding.e5-small", "vector": _unit_vector()}

    def fake_run(argv, cwd, text, stdout, stderr, check):
        assert "embed_e5.py" in str(argv[1])
        assert "--format" in argv
        assert "json" in argv
        assert "--full-vector" in argv
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(output_vector), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    plan = build_local_vector_indexing_smoke_plan(
        tmp_path,
        model_dir=tmp_path / "model",
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:smoke/vector-indexing/0142",
        text="passage: strict vector handoff",
        execute=True,
        strict_vector_handoff=True,
        vector_json=None,
        auto_vector_json=True,
    )

    rc = generate_machine_vector_json(plan)

    assert rc == 0
    assert plan.vector_json is not None
    assert load_vector_json(plan.vector_json) == tuple(_unit_vector())


def test_0142_machine_vector_json_rejects_wrong_dimension(tmp_path: Path) -> None:
    vector_path = tmp_path / "bad-vector.json"
    vector_path.write_text(json.dumps({"vector": [1.0, 0.0]}), encoding="utf-8")

    try:
        load_machine_vector_json(vector_path, expected_dimension=384)
    except ValueError as exc:
        assert "machine vector dimension must be 384" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("wrong vector dimension must be rejected")
