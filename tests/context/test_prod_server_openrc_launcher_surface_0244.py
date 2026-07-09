from pathlib import Path

from context.prod_server_openrc_launcher_surface_0244 import (
    OPENRC_LAUNCHER_SURFACE_BOUNDARY,
    validate_openrc_surface,
    write_openrc_surface_report,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
INITD = ROOT / "doc/examples/openrc_autodoc_0244.initd"


def test_openrc_surface_boundary_is_validation_only() -> None:
    assert OPENRC_LAUNCHER_SURFACE_BOUNDARY == {
        "validation_only": True,
        "uses_bootstrap_readiness": True,
        "installs_openrc_service": False,
        "calls_openrc": False,
        "starts_launcher": False,
        "creates_scheduler": False,
        "creates_eventbus": False,
        "starts_threads": False,
        "publishes_events": False,
        "calls_github_api": False,
        "writes_postgresql": False,
        "writes_qdrant": False,
        "requires_non_stdlib": False,
    }


def test_example_openrc_surface_validates() -> None:
    report = validate_openrc_surface(config_path=CONFIG, initd_path=INITD)

    assert report.valid is True
    assert report.bootstrap_ready is True
    assert report.expected_commands == ("configtest", "start", "stop", "status")
    assert report.issues == ()


def test_openrc_surface_rejects_embedded_github_token(tmp_path: Path) -> None:
    initd = tmp_path / "autodoc.initd"
    initd.write_text(INITD.read_text(encoding="utf-8") + "\nGITHUB_TOKEN=secret\n", encoding="utf-8")

    report = validate_openrc_surface(config_path=CONFIG, initd_path=initd)

    assert report.valid is False
    assert any(issue.message == "must not embed GITHUB_TOKEN value" for issue in report.issues)


def test_openrc_surface_requires_configtest(tmp_path: Path) -> None:
    initd = tmp_path / "autodoc.initd"
    initd.write_text(INITD.read_text(encoding="utf-8").replace("configtest()", "config_check()"), encoding="utf-8")

    report = validate_openrc_surface(config_path=CONFIG, initd_path=initd)

    assert report.valid is False
    assert any("configtest()" in issue.message for issue in report.issues)


def test_write_openrc_surface_report(tmp_path: Path) -> None:
    output = tmp_path / "openrc_surface.json"
    payload = write_openrc_surface_report(config_path=CONFIG, initd_path=INITD, output_path=output)

    assert payload["production_server_openrc_launcher_surface_written"] is True
    assert payload["openrc_surface"]["valid"] is True
    assert output.exists()
