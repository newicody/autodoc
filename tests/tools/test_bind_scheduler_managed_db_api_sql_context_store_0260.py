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
        "dependency_index": {"sql_context_store": []},
    },
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_bind_tool_executes_with_existing_fake_store(tmp_path: Path) -> None:
    write(
        tmp_path / "src/context/fake_db_api_sql_context_store.py",
        """
class DbApiSqlContextStore:
    def __init__(self, connection=None, **kwargs):
        self.connection = connection
    def controlled_write(self, payload):
        return {"sql_ref": "sql:tool/" + payload["intent_id"]}
""",
    )
    bootstrap = tmp_path / "bootstrap.json"
    bootstrap.write_text(json.dumps(BOOTSTRAP_PAYLOAD), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/bind_scheduler_managed_db_api_sql_context_store_0260.py"),
            "--root",
            str(tmp_path),
            "--bootstrap",
            str(bootstrap),
            "--execute",
            "--policy-decision-id",
            "policy:0260:test",
            "--db-path",
            str(tmp_path / "db.sqlite3"),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "scheduler_managed_db_api_sql_context_store_binding_valid=True" in result.stdout
    assert "constructed=True" in result.stdout
    assert "sql_ref=sql:tool/" in result.stdout
