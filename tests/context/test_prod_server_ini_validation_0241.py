from pathlib import Path

from context.prod_server_ini_validation_0241 import (
    INI_VALIDATION_BOUNDARY,
    load_ini,
    validate_ini_file,
    validate_ini_parser,
    write_ini_validation_report,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_ini_validation_boundary_is_read_only() -> None:
    assert INI_VALIDATION_BOUNDARY == {
        "validation_only": True,
        "configobj_compatible_layout": True,
        "imports_configobj": False,
        "starts_openrc": False,
        "creates_scheduler": False,
        "creates_eventbus": False,
        "writes_postgresql": False,
        "writes_qdrant": False,
        "calls_github_api": False,
        "publishes_github": False,
        "publishes_events": False,
        "requires_non_stdlib": False,
    }


def test_example_ini_validates() -> None:
    result = validate_ini_file(EXAMPLE)

    assert result.valid is True
    assert result.issues == ()
    assert "github.publication" in result.checked_sections


def test_missing_required_section_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "bad.ini"
    config.write_text("[server]\nname = autodoc-prod\n", encoding="utf-8")

    result = validate_ini_file(config)

    assert result.valid is False
    assert any(issue.message == "missing required section" for issue in result.issues)


def test_github_publication_must_be_reviewed_and_disabled() -> None:
    parser = load_ini(EXAMPLE)
    parser.set("github.publication", "publish_enabled_by_default", "true")
    parser.set("github.publication", "publication_review_required", "false")

    result = validate_ini_parser(parser, config_path=EXAMPLE)

    messages = {(issue.section, issue.key, issue.message) for issue in result.issues}
    assert ("github.publication", "publish_enabled_by_default", "must be false initially") in messages
    assert ("github.publication", "publication_review_required", "must be true") in messages


def test_qdrant_payload_must_include_sql_ref() -> None:
    parser = load_ini(EXAMPLE)
    parser.set(
        "qdrant.collection.autodoc_context_e5_small",
        "required_payload",
        "model_id, embedding_version, content_hash",
    )

    result = validate_ini_parser(parser, config_path=EXAMPLE)

    assert any(
        issue.section == "qdrant.collection.autodoc_context_e5_small"
        and issue.key == "required_payload"
        and issue.message == "must include sql_ref"
        for issue in result.issues
    )


def test_write_ini_validation_report(tmp_path: Path) -> None:
    output = tmp_path / "report.json"
    payload = write_ini_validation_report(config_path=EXAMPLE, output_path=output)

    assert payload["production_server_ini_validation_written"] is True
    assert payload["validation"]["valid"] is True
    assert output.exists()
