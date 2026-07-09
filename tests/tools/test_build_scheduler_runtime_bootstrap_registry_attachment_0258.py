import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_bootstrap_attachment_tool_uses_registry_file(tmp_path: Path) -> None:
    registry = tmp_path / "registry.json"
    output = tmp_path / "attachment.json"
    registry.write_text(
        json.dumps(
            {
                "scheduler_owned_runtime_registry": True,
                "valid": True,
                "issues": [],
                "owner": "scheduler",
                "source_map_complete": True,
                "launcher_bootstrap_only": True,
                "eventbus_observation_only": True,
                "no_cli_per_component": True,
                "creates_runtime_manager": False,
                "instantiates_components": False,
                "registrations": [
                    {"component_id": "eventbus", "capabilities": ["eventbus.publish_fact"], "depends_on": []},
                    {"component_id": "passive_supervisor_sink", "capabilities": ["supervisor.observe"], "depends_on": ["eventbus"]},
                    {"component_id": "sql_context_store", "capabilities": ["sql.context.write", "sql.context.rehydrate"], "depends_on": []},
                    {"component_id": "openvino_embedding_service", "capabilities": ["embedding.openvino.passage", "embedding.openvino.query"], "depends_on": []},
                    {"component_id": "qdrant_projection_store", "capabilities": ["qdrant.projection.upsert", "qdrant.recall"], "depends_on": ["sql_context_store", "openvino_embedding_service"]},
                    {"component_id": "github_artifact_exchange", "capabilities": ["github.artifact.scan_once"], "depends_on": []},
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_scheduler_runtime_bootstrap_registry_attachment_0258.py",
            "--registry",
            str(registry),
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "scheduler_runtime_bootstrap_registry_attachment_valid=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["dry_run"] is True
    assert payload["attachment"]["owner"] == "scheduler"
