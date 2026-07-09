from pathlib import Path

from context.prod_server_scheduler_intention_event_emission_0250 import TypedSchedulerIntention
from context.prod_server_sql_controlled_write_handler_readiness_0251 import (
    SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY,
    build_sql_controlled_write_handler_readiness,
    write_sql_controlled_write_handler_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_sql_controlled_write_boundary_is_readiness_only() -> None:
    assert SQL_CONTROLLED_WRITE_HANDLER_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_scheduler_intention_event_emission": True,
        "uses_postgresql_schema_readiness": True,
        "connects_postgresql": False,
        "executes_sql": False,
        "writes_postgresql": False,
        "creates_eventbus": False,
        "publishes_events": False,
        "calls_scheduler_run": False,
        "dispatches_handler": False,
        "runs_openvino_inference": False,
        "writes_qdrant": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_sql_controlled_write_handler_frame_is_ready() -> None:
    report = build_sql_controlled_write_handler_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.handler_frame is not None
    request = report.handler_frame.write_request
    assert request.handler_id == "handler.sql_context_store.controlled_write"
    assert request.table == "context_records"
    assert request.operation == "insert_if_absent"
    assert request.primary_key_field == "id"
    assert "ON CONFLICT (id) DO NOTHING" in request.preview_sql


def test_missing_payload_hash_is_reported() -> None:
    intention = TypedSchedulerIntention(
        intent_id="intent:no-hash",
        intent_type="scheduler.intent.sql-write",
        component="scheduler",
        phase="D07_functional_handler_chain",
        trace_id="trace:no-hash",
        priority=10,
        sql_ref="context_records.id",
    )

    report = build_sql_controlled_write_handler_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        intention=intention,
    )

    assert report.ready is False
    assert any(issue.field == "payload_hash" for issue in report.issues)


def test_write_sql_controlled_write_handler_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "sql_controlled_write_handler_readiness.json"
    payload = write_sql_controlled_write_handler_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_sql_controlled_write_handler_readiness_written"] is True
    assert payload["sql_controlled_write_handler_readiness"]["ready"] is True
    assert output.exists()
