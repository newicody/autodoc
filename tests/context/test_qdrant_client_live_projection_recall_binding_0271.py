from pathlib import Path

from context.production_prototype_smoke_composition_0269 import (
    ProductionPrototypeSmokeCommand,
    ProductionPrototypeStepOutcome,
    build_production_prototype_smoke_plan,
    run_production_prototype_smoke,
)


def _command(tmp_path: Path) -> ProductionPrototypeSmokeCommand:
    return ProductionPrototypeSmokeCommand(
        repo_root=tmp_path,
        python_executable="python",
        bootstrap_report=tmp_path / "bootstrap.json",
        database_path=tmp_path / "store.sqlite3",
        reports_dir=tmp_path / "reports",
        openrc_script_output=tmp_path / "autodoc-local-runtime.openrc",
        execute=True,
        policy_decision_id="policy:0271:live-test",
        live_qdrant=True,
        qdrant_url="http://127.0.0.1:6333",
        qdrant_collection="autodoc_live_test",
        qdrant_timeout_seconds=7.0,
        qdrant_prefer_grpc=True,
        qdrant_grpc_port=6334,
        qdrant_api_key_env="AUTODOC_TEST_QDRANT_API_KEY",
        strict_data_grpc=True,
    )


def test_live_plan_injects_existing_executor_mode_into_0262_and_0263(tmp_path: Path) -> None:
    plan = build_production_prototype_smoke_plan(_command(tmp_path))
    for index in (2, 3):
        argv = plan[index].argv
        assert "--live-qdrant" in argv
        assert "--demo-qdrant" not in argv
        assert "--qdrant-url" in argv
        assert "--collection" in argv
        assert "autodoc_live_test" in argv
        assert "--qdrant-prefer-grpc" in argv
        assert "--strict-data-grpc" in argv
        assert "AUTODOC_TEST_QDRANT_API_KEY" in argv
        assert "secret" not in " ".join(argv).lower()


def test_live_run_requires_projection_and_recall_proofs(tmp_path: Path) -> None:
    command = _command(tmp_path)

    def executor(step):
        refs = ()
        checks = ()
        if step.phase == "0260":
            refs = (("sql_ref", "sql:test"),)
        elif step.phase == "0261":
            refs = (("embedding_ref", "embedding:test"),)
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

    result = run_production_prototype_smoke(command, executor)
    assert result.valid is False
    assert "required live Qdrant check failed or missing: qdrant_projection_live" in result.issues
    assert "required live Qdrant check failed or missing: qdrant_recall_live" in result.issues
