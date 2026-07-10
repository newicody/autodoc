from context.openrc_launcher_minimal_readiness_0268 import (
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

GITHUB_HANDOFF = {
    "valid": True,
    "handoff_ref": "github-scan-once-handoff:test",
    "scan_once": True,
    "remote_mutation_allowed": False,
    "request": {"repository": "newicody/autodoc"},
}


def test_openrc_script_is_rendered_but_not_installed_or_started() -> None:
    report = build_openrc_launcher_minimal_readiness(
        closed_frame=CLOSED_FRAME,
        github_handoff=GITHUB_HANDOFF,
        request=OpenRcLauncherMinimalReadinessRequest(service_name="autodoc-local-runtime"),
        source_reports={"closed": "0264.json", "handoff": "0267.json"},
    )
    payload = report.to_mapping()

    assert payload["valid"] is True
    assert payload["readiness_only"] is True
    assert payload["openrc_admin_action_required"] is True
    assert payload["starts_postgresql"] is False
    assert payload["starts_openvino"] is False
    assert payload["starts_qdrant"] is False
    assert payload["calls_rc_service"] is False
    assert "#!/sbin/openrc-run" in payload["rendered_openrc_script"]


def test_openrc_readiness_rejects_service_start_request() -> None:
    report = build_openrc_launcher_minimal_readiness(
        closed_frame=CLOSED_FRAME,
        github_handoff=GITHUB_HANDOFF,
        request=OpenRcLauncherMinimalReadinessRequest(start_service=True),
        source_reports={},
    )

    assert report.valid is False
    assert "start_service is forbidden in 0268" in report.issues


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
