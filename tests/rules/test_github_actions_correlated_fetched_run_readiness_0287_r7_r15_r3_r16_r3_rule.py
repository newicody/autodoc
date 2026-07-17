from pathlib import Path


SOURCE = (
    Path(__file__).parents[2]
    / "src/context/github_actions_artifact_scan_once_live_0272.py"
)


def test_existing_fetch_path_is_extended_without_new_poller() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "matches_actions_artifact_name",
        "_EXPECTED_CORRELATED_ARTIFACTS",
        "_correlate_fetched_runs",
        '"ready_runs"',
        '"deferred_runs"',
        '"ready_run_count"',
        '"deferred_run_count"',
        '"correlated_three_artifact_runs": True',
        '"laboratory_execution_started": False',
    ):
        assert marker in text

    for forbidden in (
        "while True:",
        "time.sleep(",
        "asyncio.create_task(",
        "Scheduler(",
        "LaboratoryManager",
        "requests.",
        "urlopen(",
        "subprocess.",
    ):
        assert forbidden not in text


def test_ready_run_contract_requires_exact_three_roles() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        '"authoritative_request", "autodoc-authoritative-request"',
        '"copilot_advisory", "autodoc-copilot-advisory"',
        '"run_manifest", "autodoc-dual-artifact-manifest"',
        "if not missing_roles and not duplicate_roles:",
        '"local_execution_started": False',
        '"remote_mutation_performed": False',
    ):
        assert marker in text
