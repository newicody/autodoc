from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.artifact_intake_contract import ArtifactIntakeContract, build_artifact_intake_contract
from tools.run_local_artifact_vector_indexing_runner import build_local_artifact_vector_indexing_plan, main


def _make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for path in [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/context/sql_context_store.py",
        "src/context/artifact_intake_contract.py",
    ]:
        full = root / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text("# stub\n", encoding="utf-8")
    return root


def test_0146_artifact_intake_contract_validates_and_normalizes_text(tmp_path: Path) -> None:
    contract = build_artifact_intake_contract(
        artifact_ref="artifact:local/0146/demo",
        artifact_kind="local_markdown",
        artifact_path=tmp_path / "artifact.md",
        text_kind="passage",
        sql_ref="sql:artifact/vector-indexing/0146",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        route_root=tmp_path / "routes",
        vector_indexing_job_ref="vector-indexing-job:artifact/0146-demo",
        text="hello artifact",
    )

    assert isinstance(contract, ArtifactIntakeContract)
    assert contract.normalized_text() == "passage: hello artifact"
    mapping = contract.to_mapping()
    assert mapping["artifact_ref"] == "artifact:local/0146/demo"
    assert mapping["text_kind"] == "passage"
    assert mapping["dimension"] == 384
    assert "Scheduler/RouteProxy/OpenVINO/Qdrant stay outside" in mapping["boundary"]
    assert ArtifactIntakeContract.from_mapping(mapping).normalized_text() == contract.normalized_text()


def test_0146_artifact_intake_contract_rejects_bad_refs(tmp_path: Path) -> None:
    kwargs = dict(
        artifact_ref="local/0146/demo",
        artifact_kind="local_markdown",
        artifact_path=tmp_path / "artifact.md",
        text_kind="passage",
        sql_ref="sql:artifact/vector-indexing/0146",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        route_root=tmp_path / "routes",
        vector_indexing_job_ref="vector-indexing-job:artifact/0146-demo",
        text="hello",
    )
    with pytest.raises(ValueError, match="artifact_ref"):
        build_artifact_intake_contract(**kwargs)
    kwargs["artifact_ref"] = "artifact:local/0146/demo"
    kwargs["sql_ref"] = "artifact/vector-indexing/0146"
    with pytest.raises(ValueError, match="sql_ref"):
        build_artifact_intake_contract(**kwargs)


def test_0146_runner_plan_exposes_typed_artifact_contract(tmp_path: Path) -> None:
    root = _make_repo(tmp_path)
    plan = build_local_artifact_vector_indexing_plan(
        root,
        artifact_dir=Path(".var/smoke/artifacts/0146"),
        artifact_ref="artifact:local/0146/demo",
        artifact_kind="local_text",
        text_kind="query",
        vector_indexing_job_ref="vector-indexing-job:artifact/0146-demo",
        model_dir=Path("/model/e5"),
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        dimension=384,
        sql_ref="sql:artifact/vector-indexing/0146",
        route_root=Path(".var/smoke/routeproxy-0146/routes"),
        text="find artifact",
        execute=False,
    )

    assert plan.ready is True
    assert plan.artifact_contract.artifact_ref == "artifact:local/0146/demo"
    assert plan.artifact_contract.normalized_text() == "query: find artifact"
    mapping = plan.to_mapping()
    assert mapping["artifact_contract"]["vector_indexing_job_ref"] == "vector-indexing-job:artifact/0146-demo"
    assert mapping["artifact_contract_path"].endswith("artifact_intake_contract.json")
    assert "--text 'query: find artifact'" in plan.commands[0].shell_preview()
    markdown = plan.to_markdown()
    assert "## Artifact intake contract" in markdown
    assert "artifact_ref: `artifact:local/0146/demo`" in markdown


def test_0146_json_plan_output_contains_contract(tmp_path: Path, capsys) -> None:
    root = _make_repo(tmp_path)
    rc = main([
        str(root),
        "--artifact-ref", "artifact:local/0146/json",
        "--vector-indexing-job-ref", "vector-indexing-job:artifact/0146-json",
        "--format", "json",
    ])
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ready_for_local_artifact_vector_indexing"] is True
    assert data["artifact_contract"]["artifact_ref"] == "artifact:local/0146/json"
    assert data["artifact_contract"]["vector_indexing_job_ref"] == "vector-indexing-job:artifact/0146-json"
