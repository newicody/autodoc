from pathlib import Path

from context.production_prototype_smoke_composition_0269 import (
    ProductionPrototypeSmokeCommand,
    ProductionPrototypeSmokePolicy,
    ProductionPrototypeStepOutcome,
    build_production_prototype_smoke_plan,
    run_production_prototype_smoke,
)


def _command(tmp_path: Path, **overrides) -> ProductionPrototypeSmokeCommand:
    values = {
        "repo_root": tmp_path,
        "python_executable": "python",
        "bootstrap_report": tmp_path / "bootstrap.json",
        "database_path": tmp_path / "store.sqlite3",
        "reports_dir": tmp_path / "reports",
        "openrc_script_output": tmp_path / "autodoc-local-runtime.openrc",
        "execute": True,
        "policy_decision_id": "policy:0271:scope-live-test",
        "live_qdrant": True,
        "qdrant_url": "http://127.0.0.1:6333",
        "qdrant_collection": "autodoc_live_test",
        "qdrant_timeout_seconds": 7.0,
        "qdrant_prefer_grpc": True,
        "qdrant_grpc_port": 6334,
        "qdrant_api_key_env": "AUTODOC_TEST_QDRANT_API_KEY",
        "sql_authority_namespace": "autodoc-test",
        "strict_data_grpc": True,
    }
    values.update(overrides)
    return ProductionPrototypeSmokeCommand(**values)


def _successful_outcome(step) -> ProductionPrototypeStepOutcome:
    refs = ()
    checks = ()
    if step.phase == "0260":
        refs = (("sql_ref", "sql:test"),)
    elif step.phase == "0261":
        refs = (("embedding_ref", "embedding:test"),)
    elif step.phase == "0262":
        refs = (("sql_authority_ref", "sql-authority:sqlite:test"),)
        checks = (
            ("qdrant_projection_live", True),
            ("qdrant_projection_scoped", True),
            ("strict_data_grpc", True),
            ("rest_admin_only", True),
        )
    elif step.phase == "0263":
        refs = (("sql_authority_ref", "sql-authority:sqlite:test"),)
        checks = (
            ("qdrant_recall_live", True),
            ("qdrant_recall_scoped", True),
            ("strict_data_grpc", True),
            ("rest_admin_only", True),
        )
    elif step.phase == "0265":
        checks = (
            ("eventbus_observation_only", True),
            ("events_are_facts_not_commands", True),
            ("starts_postgresql", False),
            ("starts_openvino", False),
            ("starts_qdrant", False),
        )
    elif step.phase == "0266":
        checks = (("passive_supervisor_observation_only", True),)
    elif step.phase == "0267":
        refs = (("handoff_ref", "github-scan-once-handoff:test"),)
        checks = (("remote_mutation_allowed", False),)
    elif step.phase == "0268":
        refs = (("readiness_ref", "openrc-launcher-readiness:test"),)
        checks = (
            ("sqlite_database_present", True),
            ("readiness_only", True),
            ("scheduler_starts_external_services", False),
            ("calls_rc_service", False),
            ("starts_postgresql", False),
            ("starts_openvino", False),
            ("starts_qdrant", False),
        )
    return ProductionPrototypeStepOutcome(
        phase=step.phase,
        returncode=0,
        report_exists=True,
        report_valid=True,
        references=refs,
        checks=checks,
    )


def test_live_plan_passes_one_sql_scope_to_0262_and_0263(tmp_path: Path) -> None:
    command = _command(tmp_path)
    plan = build_production_prototype_smoke_plan(command)
    projection = plan[2].argv
    recall = plan[3].argv

    assert projection[projection.index("--db-path") + 1] == str(command.database_path)
    for argv in (projection, recall):
        assert "--sql-authority-namespace" in argv
        assert argv[argv.index("--sql-authority-namespace") + 1] == "autodoc-test"
        assert "--strict-data-grpc" in argv
        assert "--qdrant-prefer-grpc" in argv
        assert "http://127.0.0.1:6333" in argv
        assert "6334" in argv


def test_live_command_rejects_non_strict_or_ambiguous_transport(tmp_path: Path) -> None:
    policy = ProductionPrototypeSmokePolicy()
    assert "live_qdrant requires qdrant_prefer_grpc" in _command(
        tmp_path, qdrant_prefer_grpc=False
    ).issues(policy)
    assert "live_qdrant requires strict_data_grpc" in _command(
        tmp_path, strict_data_grpc=False
    ).issues(policy)
    assert "qdrant REST administration port must differ from gRPC port" in _command(
        tmp_path, qdrant_url="http://127.0.0.1:6334"
    ).issues(policy)
    assert "qdrant_url contains an invalid port" in _command(
        tmp_path, qdrant_url="http://127.0.0.1:not-a-port"
    ).issues(policy)


def test_live_run_accepts_matching_scoped_authority_proofs(tmp_path: Path) -> None:
    command = _command(tmp_path)
    result = run_production_prototype_smoke(command, _successful_outcome)

    assert result.valid is True
    mapping = result.to_mapping()
    assert mapping["references"]["sql_authority_ref"] == "sql-authority:sqlite:test"
    assert mapping["checks"]["qdrant_projection_scoped"] is True
    assert mapping["checks"]["qdrant_recall_scoped"] is True
    assert mapping["checks"]["strict_data_grpc"] is True


def test_live_run_rejects_mismatched_sql_authorities(tmp_path: Path) -> None:
    command = _command(tmp_path)

    def executor(step):
        outcome = _successful_outcome(step)
        if step.phase == "0263":
            return ProductionPrototypeStepOutcome(
                phase=outcome.phase,
                returncode=outcome.returncode,
                report_exists=outcome.report_exists,
                report_valid=outcome.report_valid,
                references=(("sql_authority_ref", "sql-authority:sqlite:other"),),
                checks=outcome.checks,
            )
        return outcome

    result = run_production_prototype_smoke(command, executor)

    assert result.valid is False
    assert "0262 and 0263 must report one shared sql_authority_ref" in result.issues
