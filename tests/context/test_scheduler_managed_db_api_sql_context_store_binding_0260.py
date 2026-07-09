import json
from pathlib import Path

from context.scheduler_managed_db_api_sql_context_store_binding_0260 import (
    build_db_api_sql_context_store_binding_report,
    discover_db_api_sql_context_store_candidates,
    run_scheduler_managed_db_api_sql_context_store_binding,
)


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


def make_fake_store(root: Path) -> None:
    write(
        root / "src/context/fake_db_api_sql_context_store.py",
        """
class DbApiSqlContextStore:
    def __init__(self, connection=None, **kwargs):
        self.connection = connection
    def controlled_write(self, payload):
        return {"sql_ref": "sql:real-existing/" + payload["intent_id"], "payload": dict(payload)}
""",
    )


def test_discovers_existing_db_api_sql_context_store_class(tmp_path: Path) -> None:
    make_fake_store(tmp_path)

    candidates = discover_db_api_sql_context_store_candidates(tmp_path)

    assert candidates
    assert candidates[0].symbol == "DbApiSqlContextStore"
    assert candidates[0].path == "src/context/fake_db_api_sql_context_store.py"




def test_candidate_discovery_does_not_match_binding_candidate_names(tmp_path: Path) -> None:
    write(
        tmp_path / "src/context/noise.py",
        """
class DbApiSqlContextStoreBindingCandidate:
    pass
class DbApiSqlContextStoreBindingReport:
    pass
""",
    )
    make_fake_store(tmp_path)

    candidates = discover_db_api_sql_context_store_candidates(tmp_path)

    assert [candidate.path for candidate in candidates] == [
        "src/context/fake_db_api_sql_context_store.py"
    ]

def test_binding_report_can_import_existing_store(tmp_path: Path) -> None:
    make_fake_store(tmp_path)

    report, store = build_db_api_sql_context_store_binding_report(tmp_path, construct=False)

    assert report.to_dict()["valid"] is True
    assert report.bindable is True
    assert store is None
    assert report.starts_postgresql is False
    assert report.creates_sql_store is False


def test_execute_uses_existing_store_object_under_scheduler_usage(tmp_path: Path) -> None:
    make_fake_store(tmp_path)

    result = run_scheduler_managed_db_api_sql_context_store_binding(
        tmp_path,
        BOOTSTRAP_PAYLOAD,
        text="passage: execute real existing store",
        execute=True,
        policy_decision_id="policy:0260:test",
        db_path=tmp_path / "db.sqlite3",
    )
    payload = result.to_dict()

    assert payload["valid"] is True
    assert payload["binding"]["constructed"] is True
    assert payload["usage"]["execute"] is True
    assert payload["usage"]["dry_run"] is False
    assert payload["usage"]["sql_ref"].startswith("sql:real-existing/")
    assert payload["usage"]["starts_postgresql"] is False
