from context.scheduler_managed_sql_context_store_usage_0259 import (
    run_scheduler_managed_sql_context_store_usage,
    validate_scheduler_sql_capability_attachment,
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
        "dependency_index": {
            "sql_context_store": [],
        },
    },
}


class ExistingStore:
    def controlled_write(self, payload):
        return {
            "sql_ref": "sql:test/" + payload["intent_id"],
            "payload": dict(payload),
        }


def test_validates_scheduler_sql_capability_attachment() -> None:
    assert validate_scheduler_sql_capability_attachment(BOOTSTRAP_PAYLOAD) == ()


def test_sql_usage_dry_run_is_valid_without_store() -> None:
    result = run_scheduler_managed_sql_context_store_usage(
        BOOTSTRAP_PAYLOAD,
        text="passage: dry run",
    )

    payload = result.to_dict()
    assert payload["valid"] is True
    assert payload["execute"] is False
    assert payload["dry_run"] is True
    assert payload["starts_postgresql"] is False
    assert payload["creates_sql_store"] is False
    assert payload["creates_runtime_manager"] is False
    assert payload["modifies_scheduler_run"] is False


def test_sql_usage_execute_requires_policy_decision_id() -> None:
    result = run_scheduler_managed_sql_context_store_usage(
        BOOTSTRAP_PAYLOAD,
        text="passage: execute",
        execute=True,
        store=ExistingStore(),
    )

    assert result.valid is False
    assert "execute requires policy_decision_id" in result.issues


def test_sql_usage_execute_calls_existing_store_object() -> None:
    result = run_scheduler_managed_sql_context_store_usage(
        BOOTSTRAP_PAYLOAD,
        text="passage: execute",
        execute=True,
        policy_decision_id="policy:0259:test",
        store=ExistingStore(),
        intent_id="intent:0259:test",
    )

    assert result.valid is True
    assert result.dry_run is False
    assert result.sql_ref == "sql:test/intent:0259:test"
    assert result.store_result["payload"]["capability"] == "sql.context.write"
