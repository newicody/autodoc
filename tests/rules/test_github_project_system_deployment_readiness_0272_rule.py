from pathlib import Path


def test_readiness_is_not_an_installer_or_deployer() -> None:
    text = Path("tools/run_github_project_system_deployment_readiness_0272.py").read_text()
    assert "subprocess" not in text
    assert "git push" not in text
    assert "workflow_dispatch_performed=False" not in text  # field is serialized, not executed
    assert 'method="GET"' in text
    assert "PROJECT_QUERY" in text


def test_architecture_keeps_scheduler_and_stores_outside() -> None:
    rule = Path("doc/code-rules/0272_github_project_system_deployment_readiness_rule.md").read_text()
    assert "must not install" in rule
    assert "must not dispatch" in rule
    assert "SQL, Qdrant, Scheduler" in rule
