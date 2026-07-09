"""PostgreSQL schema readiness for phase 0245.

This module reads the validated production server INI and derives the PostgreSQL
table/index shapes expected on the production server. It can emit idempotent SQL
text for review, but it does not connect to PostgreSQL or execute SQL.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_ini_validation_0241 import load_ini, validate_ini_file


POSTGRESQL_SCHEMA_READINESS_VERSION = "0245.r1"


POSTGRESQL_SCHEMA_READINESS_BOUNDARY: dict[str, bool] = {
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


@dataclass(frozen=True)
class PostgreSQLSchemaIssue:
    """One issue in the PostgreSQL schema readiness input."""

    table: str
    field: str
    message: str


@dataclass(frozen=True)
class PostgreSQLColumnSpec:
    """One PostgreSQL column shape derived from the INI."""

    name: str
    sql_type: str
    nullable: bool


@dataclass(frozen=True)
class PostgreSQLTableSpec:
    """One PostgreSQL table shape derived from the INI."""

    table: str
    primary_key: str
    columns: tuple[PostgreSQLColumnSpec, ...]
    jsonb_columns: tuple[str, ...]
    required_indexes: tuple[str, ...]
    create_table_sql: str
    create_index_sql: tuple[str, ...]


@dataclass(frozen=True)
class PostgreSQLSchemaReadinessReport:
    """JSON-compatible PostgreSQL schema readiness report."""

    version: str
    config_path: str
    ready: bool
    connection_section_present: bool
    tables: tuple[PostgreSQLTableSpec, ...]
    issues: tuple[PostgreSQLSchemaIssue, ...]


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _sql_type(column: str, jsonb_columns: tuple[str, ...]) -> str:
    if column in jsonb_columns or column.endswith("_json"):
        return "JSONB"
    if column == "created_at" or column.endswith("_at"):
        return "TIMESTAMPTZ"
    if column.startswith("is_") or column.endswith("_required"):
        return "BOOLEAN"
    return "TEXT"


def _quote_identifier(identifier: str) -> str:
    if not identifier.replace("_", "").isalnum() or not identifier:
        raise ValueError(f"unsafe identifier: {identifier}")
    return '"' + identifier + '"'


def _create_table_sql(table: str, columns: tuple[PostgreSQLColumnSpec, ...], primary_key: str) -> str:
    column_sql = []
    for column in columns:
        nullable = "" if column.nullable else " NOT NULL"
        column_sql.append(f"  {_quote_identifier(column.name)} {column.sql_type}{nullable}")
    column_sql.append(f"  PRIMARY KEY ({_quote_identifier(primary_key)})")
    joined = ",\n".join(column_sql)
    return f"CREATE TABLE IF NOT EXISTS {_quote_identifier(table)} (\n{joined}\n);"


def _create_index_sql(table: str, indexes: tuple[str, ...]) -> tuple[str, ...]:
    statements = []
    for column in indexes:
        index_name = f"idx_{table}_{column}"
        statements.append(
            "CREATE INDEX IF NOT EXISTS "
            f"{_quote_identifier(index_name)} ON {_quote_identifier(table)} ({_quote_identifier(column)});"
        )
    return tuple(statements)


def _table_spec_from_section(parser: Any, section: str) -> tuple[PostgreSQLTableSpec | None, tuple[PostgreSQLSchemaIssue, ...]]:
    table = section.removeprefix("postgresql.table.")
    issues: list[PostgreSQLSchemaIssue] = []
    primary_key = parser.get(section, "primary_key", fallback="")
    column_names = _split_csv(parser.get(section, "columns", fallback=""))
    jsonb_columns = _split_csv(parser.get(section, "jsonb_columns", fallback=""))
    required_indexes = _split_csv(parser.get(section, "required_indexes", fallback=""))

    if not primary_key:
        issues.append(PostgreSQLSchemaIssue(table, "primary_key", "missing primary key"))
    if not column_names:
        issues.append(PostgreSQLSchemaIssue(table, "columns", "missing columns"))
    if primary_key and column_names and primary_key not in column_names:
        issues.append(PostgreSQLSchemaIssue(table, "primary_key", "primary key must be in columns"))
    for column in jsonb_columns:
        if column not in column_names:
            issues.append(PostgreSQLSchemaIssue(table, "jsonb_columns", f"unknown column {column}"))
    for column in required_indexes:
        if column not in column_names:
            issues.append(PostgreSQLSchemaIssue(table, "required_indexes", f"unknown column {column}"))

    if issues:
        return None, tuple(issues)

    columns = tuple(
        PostgreSQLColumnSpec(
            name=column,
            sql_type=_sql_type(column, jsonb_columns),
            nullable=column != primary_key and column != "created_at" and column not in jsonb_columns,
        )
        for column in column_names
    )
    return (
        PostgreSQLTableSpec(
            table=table,
            primary_key=primary_key,
            columns=columns,
            jsonb_columns=jsonb_columns,
            required_indexes=required_indexes,
            create_table_sql=_create_table_sql(table, columns, primary_key),
            create_index_sql=_create_index_sql(table, required_indexes),
        ),
        tuple(),
    )


def build_postgresql_schema_readiness(config_path: Path) -> PostgreSQLSchemaReadinessReport:
    """Build PostgreSQL schema readiness from the production server INI."""

    ini_validation = validate_ini_file(config_path)
    parser = load_ini(config_path)
    issues: list[PostgreSQLSchemaIssue] = []
    tables: list[PostgreSQLTableSpec] = []

    if not ini_validation.valid:
        for issue in ini_validation.issues:
            if issue.section.startswith("postgresql"):
                issues.append(PostgreSQLSchemaIssue(issue.section, issue.key, issue.message))

    if not parser.has_section("postgresql.connection"):
        issues.append(PostgreSQLSchemaIssue("postgresql.connection", "*", "missing connection section"))

    table_sections = tuple(section for section in parser.sections() if section.startswith("postgresql.table."))
    if not table_sections:
        issues.append(PostgreSQLSchemaIssue("postgresql.table", "*", "missing table sections"))

    for section in table_sections:
        table, table_issues = _table_spec_from_section(parser, section)
        issues.extend(table_issues)
        if table is not None:
            tables.append(table)

    return PostgreSQLSchemaReadinessReport(
        version=POSTGRESQL_SCHEMA_READINESS_VERSION,
        config_path=str(config_path),
        ready=not issues,
        connection_section_present=parser.has_section("postgresql.connection"),
        tables=tuple(tables),
        issues=tuple(issues),
    )


def postgresql_schema_readiness_to_dict(report: PostgreSQLSchemaReadinessReport) -> dict[str, Any]:
    """Convert a PostgreSQL schema readiness report to JSON-compatible data."""

    return asdict(report)


def write_postgresql_schema_readiness_report(*, config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the PostgreSQL schema readiness report."""

    report = build_postgresql_schema_readiness(config_path)
    payload = {
        "production_server_postgresql_schema_readiness_written": True,
        "postgresql_schema_readiness": postgresql_schema_readiness_to_dict(report),
        "boundary": dict(POSTGRESQL_SCHEMA_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
