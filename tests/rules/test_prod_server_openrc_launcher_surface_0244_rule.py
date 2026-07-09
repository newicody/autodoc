from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0244_openrc_surface_does_not_install_or_start_runtime() -> None:
    source = (ROOT / "src/context/prod_server_openrc_launcher_surface_0244.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "validation_only" in source
    assert "installs_openrc_service" in source
    assert "calls_openrc" in source
    assert "starts_launcher" in source
    assert "creates_scheduler" in source
    assert "creates_eventbus" in source
    assert "starts_threads" in source
    assert "calls_github_api" in source
    assert "writes_postgresql" in source
    assert "writes_qdrant" in source
    assert "subprocess.run" not in source
    assert "openrc" in lowered
    assert "requests." not in lowered
    assert "qdrant.upsert" not in lowered


def test_0244_openrc_example_locks_configtest_and_dependencies() -> None:
    initd = (ROOT / "doc/examples/openrc_autodoc_0244.initd").read_text(encoding="utf-8")

    assert "#!/sbin/openrc-run" in initd
    assert "configtest()" in initd
    assert "start_pre()" in initd
    assert "need postgresql qdrant" in initd
    assert "supervisor=supervise-daemon" in initd
    assert "GITHUB_TOKEN=" not in initd


def test_0244_docs_lock_openrc_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_OPENRC_LAUNCHER_SURFACE_0244.md").read_text(
        encoding="utf-8"
    )

    assert "OpenRC launcher surface" in doc
    assert "No service is installed or started" in doc
    assert "configtest/start/stop/status" in doc
    assert "Scheduler remains runtime authority" in doc
