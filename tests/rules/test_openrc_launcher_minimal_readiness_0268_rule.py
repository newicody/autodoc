from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0268_source_locks_openrc_readiness_boundary() -> None:
    source = (ROOT / "src/context/openrc_launcher_minimal_readiness_0268.py").read_text(
        encoding="utf-8"
    )

    assert "OpenRC/system/admin starts external services" in source
    assert "0268 is readiness/rendering only" in source
    assert "does not start PostgreSQL" in source
    assert "does not call rc-service/rc-update" in source
    assert "render_openrc_script" in source
    assert "eventbus_observation" in source
    assert "passive_supervisor_observation" in source
    assert "sqlite_database" in source
    assert "subprocess.run" not in source
    assert "rc-service" not in source.replace("does not call rc-service/rc-update", "")
    assert "rc-update" not in source.replace("does not call rc-service/rc-update", "")
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0268_tool_is_metadata_only_for_sqlite_and_services() -> None:
    tool = (ROOT / "tools/build_openrc_launcher_minimal_readiness_0268.py").read_text(
        encoding="utf-8"
    )

    assert "path.stat()" in tool
    assert "import sqlite3" not in tool
    assert "sqlite3.connect" not in tool
    assert "subprocess" not in tool
    assert "os.system" not in tool
    assert "Popen(" not in tool
    assert "rc-service" not in tool
    assert "rc-update" not in tool


def test_0268_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/OPENRC_LAUNCHER_MINIMAL_READINESS_0268.md").read_text(
        encoding="utf-8"
    )

    assert "OpenRC launcher minimal readiness" in doc
    assert "OpenRC/system/admin starts external services" in doc
    assert "Scheduler owns Autodoc runtime objects" in doc
    normalized = " ".join(doc.split())
    assert "0264, 0265, 0266 and 0267" in normalized
    assert "SQLite" in doc
    assert "does not install, enable, or start services" in doc
    assert "0269 can run the prototype production smoke" in doc
