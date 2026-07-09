from pathlib import Path

from context.prod_server_eventbus_attributes_readiness_0249 import (
    EVENTBUS_ATTRIBUTES_READINESS_BOUNDARY,
    build_eventbus_attributes_readiness,
    write_eventbus_attributes_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_eventbus_attributes_boundary_is_readiness_only() -> None:
    assert EVENTBUS_ATTRIBUTES_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_validated_ini": True,
        "uses_projection_path_readiness": True,
        "creates_eventbus": False,
        "publishes_events": False,
        "triggers_scheduler": False,
        "starts_threads": False,
        "writes_postgresql": False,
        "runs_openvino_inference": False,
        "writes_qdrant": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_eventbus_attributes_are_ready() -> None:
    report = build_eventbus_attributes_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.surface is not None
    assert report.surface.schema_version_required is True
    assert "sql_ref" in report.surface.optional
    assert "payload_hash" in report.surface.optional
    assert "secret" in report.surface.optional_redacted
    assert report.surface.large_payload_policy == "refs_only_no_large_payloads"


def test_large_payload_attributes_are_rejected(tmp_path: Path) -> None:
    config = tmp_path / "bad_eventbus.ini"
    config.write_text(
        SERVER_CONFIG.read_text(encoding="utf-8").replace(
            "optional = intent_id, result_id, sql_ref, qdrant_ref, github_ref, project_push_frame_ref, payload_hash, priority",
            "optional = intent_id, result_id, sql_ref, qdrant_ref, github_ref, project_push_frame_ref, payload_hash, priority, payload_json",
        ),
        encoding="utf-8",
    )

    report = build_eventbus_attributes_readiness(
        server_config_path=config,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is False
    assert any(issue.field == "large_payload_policy" for issue in report.issues)


def test_schema_version_is_required(tmp_path: Path) -> None:
    config = tmp_path / "bad_schema.ini"
    config.write_text(
        SERVER_CONFIG.read_text(encoding="utf-8").replace(
            "required = schema_version, event_type, trace_id, component, phase",
            "required = event_type, trace_id, component, phase",
        ),
        encoding="utf-8",
    )

    report = build_eventbus_attributes_readiness(
        server_config_path=config,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is False
    assert any("schema_version" in issue.message for issue in report.issues)


def test_write_eventbus_attributes_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "eventbus_attributes_readiness.json"
    payload = write_eventbus_attributes_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_eventbus_attributes_readiness_written"] is True
    assert payload["eventbus_attributes_readiness"]["ready"] is True
    assert output.exists()
