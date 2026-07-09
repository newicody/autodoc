from pathlib import Path

from context.scheduler_owned_runtime_reuse_source_map_0256 import (
    build_scheduler_owned_runtime_reuse_source_map,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_source_map_filters_noise_and_selects_source_surfaces(tmp_path: Path) -> None:
    write(tmp_path / ".aider.chat.history.md", "src/kernel/scheduler.py class Scheduler")
    write(tmp_path / "PHASE9999_TEST_REPORT.md", "OpenVINO Qdrant DbApiSqlContextStore")
    write(tmp_path / "doc/architecture/noise.md", "ProjectPushFrame EventBus")
    write(tmp_path / "src/kernel/scheduler.py", "class Scheduler:\n    pass\n")
    write(tmp_path / "src/contracts/scheduler.py", "Scheduler = object\n")
    write(tmp_path / "src/kernel/event_bus.py", "class EventBus:\n    def publish(self): pass\n")
    write(tmp_path / "src/context/passive_supervisor/sink.py", "PassiveSupervisorSink = object\n")
    write(tmp_path / "src/context/db_api_sql_context_store.py", "class DbApiSqlContextStore:\n    sql_ref = None\n")
    write(tmp_path / "tools/embed_e5.py", "OpenVINO multilingual-e5-small embed_query embed_passage\n")
    write(tmp_path / "tools/run_qdrant_projection.py", "Qdrant qdrant sql_ref qdrant_ref\n")
    write(tmp_path / "src/context/github/artifact.py", "ProjectPushFrame GitHubArtifact github_artifact\n")

    payload = build_scheduler_owned_runtime_reuse_source_map(tmp_path).to_dict()

    assert payload["complete"] is True
    assert payload["audit_first_adapt_second"] is True
    assert payload["scheduler_owns_runtime_components"] is True
    assert payload["no_cli_per_component"] is True
    paths = {
        hit["path"]
        for selection in payload["selections"]
        for hit in selection["hits"]
    }
    assert ".aider.chat.history.md" not in paths
    assert "PHASE9999_TEST_REPORT.md" not in paths
    assert "doc/architecture/noise.md" not in paths
    assert "src/kernel/scheduler.py" in paths
    assert "tools/embed_e5.py" in paths
