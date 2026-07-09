from pathlib import Path

from context.prod_server_scheduler_eventbus_bootstrap_readiness_0243 import (
    BOOTSTRAP_READINESS_BOUNDARY,
    build_bootstrap_readiness,
    write_bootstrap_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"


def test_bootstrap_readiness_boundary_is_readiness_only() -> None:
    assert BOOTSTRAP_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_validated_registry": True,
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


def test_example_is_ready_for_scheduler_eventbus_bootstrap() -> None:
    report = build_bootstrap_readiness(EXAMPLE)

    assert report.ready is True
    assert report.issues == ()
    assert [component.component_id for component in report.core_components] == [
        "eventbus",
        "scheduler",
    ]


def test_core_components_keep_command_and_observation_roles() -> None:
    report = build_bootstrap_readiness(EXAMPLE)
    components = {component.component_id: component for component in report.core_components}

    assert components["scheduler"].command_path is True
    assert components["scheduler"].observation_path is False
    assert components["eventbus"].command_path is False
    assert components["eventbus"].observation_path is True


def test_missing_scheduler_is_reported(tmp_path: Path) -> None:
    text = EXAMPLE.read_text(encoding="utf-8")
    start = text.index("[component.scheduler]")
    end = text.index("[component.eventbus]")
    config = tmp_path / "missing_scheduler.ini"
    config.write_text(text[:start] + text[end:], encoding="utf-8")

    report = build_bootstrap_readiness(config)

    assert report.ready is False
    assert any(issue.component_id == "component.scheduler" for issue in report.issues)
    assert any(issue.component_id == "scheduler" for issue in report.issues)


def test_write_bootstrap_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "bootstrap_readiness.json"
    payload = write_bootstrap_readiness_report(config_path=EXAMPLE, output_path=output)

    assert payload["production_server_scheduler_eventbus_bootstrap_readiness_written"] is True
    assert payload["readiness"]["ready"] is True
    assert output.exists()
