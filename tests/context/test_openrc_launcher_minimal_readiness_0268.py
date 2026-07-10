from context.openrc_launcher_minimal_readiness_0268 import (
    EVENTBUS_OBSERVATION_SCHEMA,
    PASSIVE_SUPERVISOR_SCHEMA,
    OpenRcLauncherMinimalReadinessRequest,
    OpenRcLauncherServiceSpec,
    build_openrc_launcher_minimal_readiness,
    render_openrc_script,
)


CLOSED_FRAME = {
    "valid": True,
    "sql_ref": "sql:inference_context:test",
    "embedding_ref": "embedding:passage:test",
    "hydrated_count": 1,
    "missing_count": 0,
    "executes_runtime": False,
}

EVENTBUS_OBSERVATION = {
    "schema": EVENTBUS_OBSERVATION_SCHEMA,
    "valid": True,
    "frame_ref": "closed-result-frame:test",
    "fact_count": 3,
    "published_count": 3,
    "observed_count": 3,
    "eventbus_observation_only": True,
    "events_are_facts_not_commands": True,
    "executes_runtime": False,
}

PASSIVE_SUPERVISOR_OBSERVATION = {
    "schema": PASSIVE_SUPERVISOR_SCHEMA,
    "valid": True,
    "source_observation_ref": "eventbus-observation:test",
    "fact_count": 3,
    "accepted_fact_count": 3,
    "rejected_fact_count": 0,
    "runtime_violation_count": 0,
    "passive_supervisor_observation_only": True,
    "executes_runtime": False,
}

GITHUB_HANDOFF = {
    "valid": True,
    "handoff_ref": "github-scan-once-handoff:test",
    "scan_once": True,
    "remote_mutation_allowed": False,
    "request": {"repository": "newicody/autodoc"},
}

SQLITE_DATABASE = {
    "path": "/repo/.var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3",
    "exists": True,
    "is_file": True,
    "size_bytes": 4096,
    "opened": False,
    "queried": False,
    "written": False,
}


def _build(**overrides):
    values = {
        "closed_frame": CLOSED_FRAME,
        "eventbus_observation": EVENTBUS_OBSERVATION,
        "passive_supervisor_observation": PASSIVE_SUPERVISOR_OBSERVATION,
        "github_handoff": GITHUB_HANDOFF,
        "sqlite_database": SQLITE_DATABASE,
        "request": OpenRcLauncherMinimalReadinessRequest(
            service_name="autodoc-local-runtime"
        ),
        "source_reports": {
            "closed": "0264.json",
            "eventbus": "0265.json",
            "passive": "0266.json",
            "handoff": "0267.json",
            "sqlite": "0260.sqlite3",
        },
    }
    values.update(overrides)
    return build_openrc_launcher_minimal_readiness(**values)


def test_openrc_script_is_rendered_but_not_installed_or_started() -> None:
    payload = _build().to_mapping()

    assert payload["valid"] is True
    assert payload["ready_report_count"] == 4
    assert payload["checks"]["sqlite_database_present"] is True
    assert payload["sqlite_database_summary"]["opened"] is False
    assert payload["readiness_only"] is True
    assert payload["openrc_admin_action_required"] is True
    assert payload["scheduler_starts_external_services"] is False
    assert payload["starts_postgresql"] is False
    assert payload["starts_openvino"] is False
    assert payload["starts_qdrant"] is False
    assert payload["executes_openvino"] is False
    assert payload["writes_sql"] is False
    assert payload["calls_qdrant"] is False
    assert payload["calls_github"] is False
    assert payload["calls_rc_service"] is False
    assert "#!/sbin/openrc-run" in payload["rendered_openrc_script"]


def test_openrc_readiness_rejects_service_start_request() -> None:
    report = _build(
        request=OpenRcLauncherMinimalReadinessRequest(start_service=True)
    )

    assert report.valid is False
    assert "start_service is forbidden in 0268" in report.issues


def test_openrc_readiness_rejects_missing_sqlite_and_passive_drift() -> None:
    sqlite_database = dict(SQLITE_DATABASE)
    sqlite_database.update(exists=False, is_file=False, size_bytes=0)
    passive = dict(PASSIVE_SUPERVISOR_OBSERVATION)
    passive["rejected_fact_count"] = 1

    report = _build(
        sqlite_database=sqlite_database,
        passive_supervisor_observation=passive,
    )

    assert report.valid is False
    assert "phase-0260 SQLite database must exist" in report.issues
    assert "0266 PassiveSupervisor must reject zero facts" in report.issues


def test_rendered_openrc_script_contains_dependencies_only() -> None:
    script = render_openrc_script(
        OpenRcLauncherServiceSpec(
            service_name="autodoc-local-runtime",
            depends_need=("localmount",),
            depends_after=("postgresql", "qdrant"),
        )
    )

    assert "need localmount" in script
    assert "after postgresql qdrant" in script
    assert "rc-service" not in script
    assert "rc-update" not in script
