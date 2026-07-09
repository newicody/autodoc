from pathlib import Path

from context.prod_server_component_registry_0242 import (
    COMPONENT_REGISTRY_BOUNDARY,
    build_component_registry,
    dependency_order,
    write_component_registry_report,
)
from context.prod_server_ini_validation_0241 import load_ini, validate_ini_parser


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_component_registry_boundary_is_declarative_only() -> None:
    assert COMPONENT_REGISTRY_BOUNDARY == {
        "registry_only": True,
        "validates_ini_first": True,
        "imports_factory_modules": False,
        "calls_factories": False,
        "creates_scheduler": False,
        "creates_eventbus": False,
        "starts_openrc": False,
        "starts_threads": False,
        "publishes_events": False,
        "calls_github_api": False,
        "writes_postgresql": False,
        "writes_qdrant": False,
        "requires_non_stdlib": False,
    }


def test_example_registry_orders_components() -> None:
    report = build_component_registry(EXAMPLE)

    assert report.valid is True
    assert report.issues == ()
    assert report.ordered_components == (
        "eventbus",
        "scheduler",
        "passive_supervisor_sink",
        "sql_context_store",
        "github_artifact_exchange",
        "qdrant_projection",
    )


def test_registry_marks_command_and_observation_paths() -> None:
    report = build_component_registry(EXAMPLE)
    entries = {entry.component_id: entry for entry in report.entries}

    assert entries["scheduler"].command_path is True
    assert entries["scheduler"].observation_path is False
    assert entries["eventbus"].command_path is False
    assert entries["eventbus"].observation_path is True
    assert entries["passive_supervisor_sink"].observation_path is True


def test_invalid_factory_syntax_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "bad_factory.ini"
    config.write_text(EXAMPLE.read_text(encoding="utf-8").replace(
        "factory = autodoc.scheduler:create_scheduler",
        "factory = new create_scheduler",
    ), encoding="utf-8")

    report = build_component_registry(config)

    assert report.valid is False
    assert any(issue.component_id == "scheduler" and issue.field == "factory" for issue in report.issues)


def test_dependency_cycle_is_reported() -> None:
    parser = load_ini(EXAMPLE)
    parser.set("component.scheduler", "depends_on", "qdrant_projection")
    parser.set("component.qdrant_projection", "depends_on", "scheduler")
    validation = validate_ini_parser(parser, config_path=EXAMPLE)
    assert validation.valid is True

    from context.prod_server_component_registry_0242 import _entry_from_section, _component_sections

    entries = []
    for section in _component_sections(parser):
        entry, issues = _entry_from_section(parser, section)
        assert issues == ()
        assert entry is not None
        entries.append(entry)

    _ordered, issues = dependency_order(tuple(entries))
    assert any(issue.field == "depends_on" and "dependency cycle" in issue.message for issue in issues)


def test_write_component_registry_report(tmp_path: Path) -> None:
    output = tmp_path / "registry.json"
    payload = write_component_registry_report(config_path=EXAMPLE, output_path=output)

    assert payload["production_server_component_registry_written"] is True
    assert payload["registry"]["valid"] is True
    assert output.exists()
