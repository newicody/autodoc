from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_controlled_sql_projection_seed_0287.py"
TOOL = ROOT / "tools/seed_love_live_projection_sql_0287.py"
REPORT = ROOT / "PHASE0287_R7_R15_R3_R11_R2_CONTROLLED_SQL_PROJECTION_SEED_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R3_R11_R2_CONTROLLED_SQL_PROJECTION_SEED.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R15_R3_R11_R2_CONTROLLED_SQL_PROJECTION_SEED.md"
DOT = ROOT / "doc/architecture/CONTROLLED_SQL_PROJECTION_SEED_0287_R7_R15_R3_R11_R2.dot"


def test_phase_artifacts_exist() -> None:
    for path in (SOURCE, TOOL, REPORT, MANIFEST, CHANGELOG, DOT):
        assert path.is_file(), path


def test_seed_reuses_sql_authority_and_has_no_other_backend() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for required in (
        "ContextAuthorityObject",
        "ContextRevisionMembership",
        "ContextRevision",
        "put_object",
        "put_revision",
        "parent_revision_refs=(parent_revision_ref,)",
        'validation_status="accepted"',
        'state="active"',
        "confirm_plan_digest",
    ):
        assert required in source
    for forbidden in (
        "from qdrant_client",
        "import qdrant_client",
        "from openvino",
        "import openvino",
        "from scheduler",
        "import scheduler",
        "import psycopg",
        "import sqlite3",
        "import asyncio",
        "import requests",
    ):
        assert forbidden not in source


def test_cli_is_thin_and_uses_dedicated_write_gate() -> None:
    tool = TOOL.read_text(encoding="utf-8")
    assert "AUTODOC_SQL_PROJECTION_SEED_WRITE_ALLOWED" in tool
    assert "open_love_postgresql_authority" in tool
    assert "execute_love_controlled_sql_projection_seed" in tool
    assert "argparse.Namespace" not in tool
    for forbidden in (
        "QdrantClient",
        "build_multilingual_e5_small_pipeline",
        "CREATE TABLE",
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
    ):
        assert forbidden not in tool


def test_report_contains_required_code_rule_review() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
    ):
        assert required in report
