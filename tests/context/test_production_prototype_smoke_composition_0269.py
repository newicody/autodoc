from pathlib import Path

from context.production_prototype_smoke_composition_0269 import (
    PHASES,
    ProductionPrototypeSmokeCommand,
    ProductionPrototypeStepOutcome,
    build_production_prototype_smoke_plan,
    plan_production_prototype_smoke,
    run_production_prototype_smoke,
)


def _command(
    tmp_path: Path,
    *,
    execute: bool = False,
    demo_eventbus: bool = False,
    demo_qdrant: bool = False,
):
    return ProductionPrototypeSmokeCommand(
        repo_root=tmp_path,
        python_executable="python",
        bootstrap_report=tmp_path / ".var/reports/bootstrap_0258.json",
        database_path=tmp_path / ".var/local/store_0260.sqlite3",
        reports_dir=tmp_path / ".var/reports",
        openrc_script_output=tmp_path / ".var/reports/autodoc-local-runtime.openrc",
        execute=execute,
        policy_decision_id="policy:0269:test" if execute else "",
        demo_eventbus=demo_eventbus,
        demo_qdrant=demo_qdrant,
    )


def test_plan_reuses_all_existing_phase_tools_in_order(tmp_path: Path) -> None:
    command = _command(tmp_path)
    plan = build_production_prototype_smoke_plan(command)

    assert tuple(step.phase for step in plan) == PHASES
    assert plan[0].tool == "bind_scheduler_managed_db_api_sql_context_store_0260.py"
    assert plan[-1].tool == "build_openrc_launcher_minimal_readiness_0268.py"
    assert "--execute" not in plan[0].argv
    assert "--publish-demo" not in plan[5].argv
    assert "rc-service" not in " ".join(token for step in plan for token in step.argv)



def test_eventbus_demo_publish_is_explicit(tmp_path: Path) -> None:
    command = _command(tmp_path, demo_eventbus=True)
    plan = build_production_prototype_smoke_plan(command)

    assert "--publish-demo" in plan[5].argv

def test_plan_result_is_valid_without_running_effects(tmp_path: Path) -> None:
    result = plan_production_prototype_smoke(_command(tmp_path))

    assert result.valid is True
    assert result.execute is False
    assert result.executed_step_count == 0
    assert result.planned_step_count == 9
    assert result.to_mapping()["boundaries"]["scheduler_starts_external_services"] is False


def test_execute_requires_explicit_qdrant_demo_until_real_executor_exists(tmp_path: Path) -> None:
    result = run_production_prototype_smoke(
        _command(tmp_path, execute=True, demo_qdrant=False),
        lambda step: ProductionPrototypeStepOutcome(
            phase=step.phase,
            returncode=0,
            report_exists=True,
            report_valid=True,
        ),
    )

    assert result.valid is False
    assert any("explicit demo_qdrant" in issue for issue in result.issues)


def test_execute_folds_injected_step_outcomes_without_runtime_manager(tmp_path: Path) -> None:
    command = _command(tmp_path, execute=True, demo_qdrant=True)

    def executor(step):
        references = ()
        if step.phase == "0260":
            references = (("sql_ref", "sql:inference_context:test"),)
        elif step.phase == "0261":
            references = (("embedding_ref", "embedding:passage:test"),)
        elif step.phase == "0267":
            references = (("handoff_ref", "github-scan-once-handoff:test"),)
        checks = ()
        if step.phase == "0265":
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
            checks = (("remote_mutation_allowed", False),)
        elif step.phase == "0268":
            references = (("readiness_ref", "openrc-launcher-readiness:test"),)
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
            references=references,
            checks=checks,
        )

    result = run_production_prototype_smoke(command, executor)
    payload = result.to_mapping()

    assert result.valid is True
    assert result.executed_step_count == 9
    assert result.valid_step_count == 9
    assert payload["references"]["sql_ref"] == "sql:inference_context:test"
    assert payload["references"]["readiness_ref"] == "openrc-launcher-readiness:test"
