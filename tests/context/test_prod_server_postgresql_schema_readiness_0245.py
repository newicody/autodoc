from pathlib import Path

from context.prod_server_postgresql_schema_readiness_0245 import (
    POSTGRESQL_SCHEMA_READINESS_BOUNDARY,
    build_postgresql_schema_readiness,
    write_postgresql_schema_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_postgresql_schema_readiness_boundary_is_check_only() -> None:
    assert POSTGRESQL_SCHEMA_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_validated_ini": True,
        "connects_postgresql": False,
        "executes_sql": False,
        "writes_postgresql": False,
        "starts_openrc": False,
        "creates_scheduler": False,
        "creates_eventbus": False,
        "publishes_events": False,
        "calls_github_api": False,
        "writes_qdrant": False,
        "requires_non_stdlib": False,
    }


def test_example_postgresql_schema_is_ready() -> None:
    report = build_postgresql_schema_readiness(CONFIG)

    assert report.ready is True
    assert report.connection_section_present is True
    assert report.issues == ()
    assert {table.table for table in report.tables} == {
        "context_records",
        "event_journal",
        "result_frames",
        "github_project_push_frames",
    }


def test_jsonb_and_boolean_columns_are_typed() -> None:
    report = build_postgresql_schema_readiness(CONFIG)
    tables = {table.table: table for table in report.tables}
    context_columns = {column.name: column for column in tables["context_records"].columns}
    github_columns = {column.name: column for column in tables["github_project_push_frames"].columns}

    assert context_columns["payload_json"].sql_type == "JSONB"
    assert github_columns["publication_review_required"].sql_type == "BOOLEAN"
    assert "CREATE TABLE IF NOT EXISTS" in tables["context_records"].create_table_sql
    assert any("CREATE INDEX IF NOT EXISTS" in sql for sql in tables["context_records"].create_index_sql)


def test_unknown_index_column_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "bad_postgresql.ini"
    config.write_text(
        CONFIG.read_text(encoding="utf-8").replace(
            "required_indexes = content_hash, kind",
            "required_indexes = content_hash, missing_column",
            1,
        ),
        encoding="utf-8",
    )

    report = build_postgresql_schema_readiness(config)

    assert report.ready is False
    assert any(issue.field == "required_indexes" for issue in report.issues)


def test_write_postgresql_schema_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "postgresql_schema_readiness.json"
    payload = write_postgresql_schema_readiness_report(config_path=CONFIG, output_path=output)

    assert payload["production_server_postgresql_schema_readiness_written"] is True
    assert payload["postgresql_schema_readiness"]["ready"] is True
    assert output.exists()
