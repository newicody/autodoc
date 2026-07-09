import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


BOOTSTRAP_PAYLOAD = {
    "scheduler_runtime_bootstrap_registry_attachment": True,
    "valid": True,
    "registry_payload_digest": "sha256:demo",
    "attachment": {
        "owner": "scheduler",
        "launcher_bootstrap_only": True,
        "eventbus_observation_only": True,
        "no_cli_per_component": True,
        "modifies_scheduler_run": False,
        "instantiates_components": False,
        "starts_components": False,
        "creates_runtime_manager": False,
        "capability_index": {
            "sql.context.write": "sql_context_store",
            "sql.context.rehydrate": "sql_context_store",
        },
        "dependency_index": {
            "sql_context_store": [],
        },
    },
}


def test_sql_usage_tool_dry_run(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.json"
    output = tmp_path / "usage.json"
    bootstrap.write_text(json.dumps(BOOTSTRAP_PAYLOAD), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_scheduler_managed_sql_context_store_usage_0259.py",
            "--bootstrap",
            str(bootstrap),
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

    assert "scheduler_managed_sql_context_store_usage_valid=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert payload["starts_postgresql"] is False


def test_sql_usage_tool_execute_with_demo_existing_store(tmp_path: Path) -> None:
    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text(json.dumps(BOOTSTRAP_PAYLOAD), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "tools/build_scheduler_managed_sql_context_store_usage_0259.py",
            "--bootstrap",
            str(bootstrap),
            "--execute",
            "--policy-decision-id",
            "policy:0259:test",
            "--demo-existing-store",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "execute=True" in result.stdout
    assert "dry_run=False" in result.stdout
    assert "sql_ref=sql:demo/" in result.stdout
