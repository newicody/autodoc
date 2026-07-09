from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0245_postgresql_schema_readiness_does_not_connect_or_execute_sql() -> None:
    source = (ROOT / "src/context/prod_server_postgresql_schema_readiness_0245.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "connects_postgresql" in source
    assert "executes_sql" in source
    assert "writes_postgresql" in source
    assert "calls_github_api" in source
    assert "writes_qdrant" in source
    assert "psycopg" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".execute(" not in lowered
    assert "qdrant.upsert" not in lowered


def test_0245_docs_lock_postgresql_readiness_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_POSTGRESQL_SCHEMA_READINESS_0245.md").read_text(
        encoding="utf-8"
    )

    assert "PostgreSQL schema readiness" in doc
    assert "No PostgreSQL connection is opened" in doc
    assert "SQL text is preview-only" in doc
    assert "0246" in doc
