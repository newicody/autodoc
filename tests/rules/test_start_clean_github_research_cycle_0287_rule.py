from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from tools import start_clean_github_research_cycle_0287 as tool


def _plan() -> tool.CyclePlan:
    return tool.CyclePlan(
        repository="newicody/projects",
        project_owner="newicody",
        project_number=3,
        workflow="autodoc-controlled-research.yml",
        ref="master",
        title="[Recherche] Test amour cycle propre",
        body=(
            "### Question ou objectif\n"
            "Analyser la question.\n\n"
            "### Résultat attendu\n"
            "Produire un résultat vérifiable.\n"
        ),
        cycle_ref="love-cycle-clean-1",
        token_env="GITHUB_TOKEN",
        wait_seconds=30,
        poll_seconds=1,
    )


class Clock:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class FakeGh:
    def __init__(self) -> None:
        self.run_lists = [
            [
                {
                    "databaseId": 100,
                    "displayTitle": "old",
                    "event": "issues",
                    "status": "completed",
                    "workflowName": "Autodoc controlled research request",
                }
            ],
            [
                {
                    "databaseId": 101,
                    "displayTitle": (
                        "[Recherche] Test amour cycle propre"
                    ),
                    "event": "issues",
                    "status": "queued",
                    "workflowName": "Autodoc controlled research request",
                },
                {
                    "databaseId": 100,
                    "displayTitle": "old",
                    "event": "issues",
                    "status": "completed",
                    "workflowName": "Autodoc controlled research request",
                },
            ],
        ]
        self.commands: list[tuple[str, ...]] = []

    def __call__(
        self,
        command,
        *,
        environment,
        label,
        stdin_payload=None,
    ):
        command = tuple(command)
        self.commands.append(command)
        if label == "list Issue workflow runs":
            return {"items": self.run_lists.pop(0)}
        if label == "create issue":
            assert stdin_payload["title"].startswith("[Recherche] ")
            assert "autodoc-cycle-ref:love-cycle-clean-1" in (
                stdin_payload["body"]
            )
            return {
                "number": 16,
                "title": "[Recherche] Test amour cycle propre",
                "html_url": (
                    "https://github.com/newicody/projects/issues/16"
                ),
                "node_id": "I_issue_16",
                "state": "open",
            }
        if label == "add Issue to ProjectV2":
            return {"id": "PVTI_issue_16"}
        if label == "view workflow run":
            return {
                "databaseId": 101,
                "displayTitle": (
                    "[Recherche] Test amour cycle propre"
                ),
                "event": "issues",
                "status": "completed",
                "conclusion": "success",
                "workflowName": "Autodoc controlled research request",
                "url": "https://github.com/run/101",
            }
        if label == "list workflow artifacts":
            return {
                "artifacts": [
                    {
                        "id": 201,
                        "name": (
                            "autodoc-i16-love--authoritative-request-v1"
                        ),
                        "expired": False,
                    },
                    {
                        "id": 202,
                        "name": (
                            "autodoc-i16-love--copilot-advisory-v2"
                        ),
                        "expired": False,
                    },
                    {
                        "id": 203,
                        "name": (
                            "autodoc-i16-love--run-manifest-v1"
                        ),
                        "expired": False,
                    },
                ]
            }
        raise AssertionError(label)


def test_plan_requires_issue_trigger_shape() -> None:
    plan = _plan()

    assert plan.plan_digest.startswith("sha256:")
    assert plan.to_plan_mapping()["trigger"] == "issues:opened"
    assert (
        plan.to_plan_mapping()["workflow_dispatch_emitted"]
        is False
    )
    assert "autodoc-cycle-ref:love-cycle-clean-1" in plan.marked_body


@pytest.mark.parametrize(
    "title",
    (
        "Test sans préfixe",
        "[Développement] mauvais statut",
    ),
)
def test_plan_rejects_non_research_title(title: str) -> None:
    with pytest.raises(
        tool.CleanResearchCycleError,
        match="title must start",
    ):
        tool.CyclePlan(
            repository="newicody/projects",
            project_owner="newicody",
            project_number=3,
            workflow="autodoc-controlled-research.yml",
            ref="master",
            title=title,
            body=_plan().body,
            cycle_ref="cycle",
            token_env="GITHUB_TOKEN",
            wait_seconds=30,
            poll_seconds=1,
        )


def test_execute_creates_one_issue_one_item_one_run_one_triplet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan()
    fake = FakeGh()
    clock = Clock()
    for gate in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_CREATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
    ):
        monkeypatch.setenv(gate, "true")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")

    result = tool.execute_clean_cycle(
        plan,
        gh_command="gh",
        confirm_plan_digest=plan.plan_digest,
        command_runner=fake,
        sleeper=clock.sleep,
        monotonic=clock.monotonic,
    )

    assert result["valid"] is True
    assert result["status"] == "clean-cycle-ready-for-local-fetch"
    assert result["issue"]["number"] == 16
    assert result["project_item"]["id"] == "PVTI_issue_16"
    assert result["run_id"] == 101
    assert set(result["artifact_triplet"]) == {
        "authoritative_request",
        "copilot_advisory",
        "run_manifest",
    }
    assert result["counts"]["artifact_count"] == 3
    assert (
        result["boundaries"]["workflow_dispatch_emitted"]
        is False
    )


def test_execute_requires_exact_digest_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan()
    fake = FakeGh()

    with pytest.raises(
        tool.CleanResearchCycleError,
        match="confirm-plan-digest mismatch",
    ):
        tool.execute_clean_cycle(
            plan,
            gh_command="gh",
            confirm_plan_digest="sha256:wrong",
            command_runner=fake,
        )

    assert fake.commands == []


def test_execute_requires_all_mutation_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan()
    monkeypatch.setenv(
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "true",
    )
    monkeypatch.setenv(
        "AUTODOC_ISSUE_CREATION_ALLOWED",
        "true",
    )
    monkeypatch.delenv(
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
        raising=False,
    )

    with pytest.raises(
        tool.CleanResearchCycleError,
        match="AUTODOC_PROJECT_PROJECTION_ALLOWED",
    ):
        tool.execute_clean_cycle(
            plan,
            gh_command="gh",
            confirm_plan_digest=plan.plan_digest,
            command_runner=FakeGh(),
        )


def test_duplicate_new_runs_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _plan()
    fake = FakeGh()
    duplicate = dict(fake.run_lists[1][0])
    duplicate["databaseId"] = 102
    fake.run_lists[1].insert(0, duplicate)
    clock = Clock()
    for gate in (
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_CREATION_ALLOWED",
        "AUTODOC_PROJECT_PROJECTION_ALLOWED",
    ):
        monkeypatch.setenv(gate, "true")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")

    with pytest.raises(
        tool.CleanResearchCycleError,
        match="more than one new",
    ):
        tool.execute_clean_cycle(
            plan,
            gh_command="gh",
            confirm_plan_digest=plan.plan_digest,
            command_runner=fake,
            sleeper=clock.sleep,
            monotonic=clock.monotonic,
        )


def test_artifact_duplicate_role_fails_closed() -> None:
    plan = _plan()

    def runner(command, *, environment, label, stdin_payload=None):
        return {
            "artifacts": [
                {
                    "id": 1,
                    "name": "autodoc-i16-x--authoritative-request-v1",
                    "expired": False,
                },
                {
                    "id": 2,
                    "name": "autodoc-i16-y--authoritative-request-v1",
                    "expired": False,
                },
                {
                    "id": 3,
                    "name": "autodoc-i16-z--copilot-advisory-v2",
                    "expired": False,
                },
                {
                    "id": 4,
                    "name": "autodoc-i16-z--run-manifest-v1",
                    "expired": False,
                },
            ]
        }

    with pytest.raises(
        tool.CleanResearchCycleError,
        match="authoritative_request.*found 2",
    ):
        tool._verify_artifact_triplet(  # noqa: SLF001
            runner,
            gh_command="gh",
            plan=plan,
            run_id=101,
            environment={},
        )


def test_operator_tool_does_not_dispatch_workflow_or_run_local_pipeline() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert '"issues:opened"' in source
    assert '"workflow_dispatch_emitted": False' in source
    assert '"api",' in source
    assert '"-X",' in source
    assert '"POST",' in source
    assert '"project",' in source
    assert '"item-add",' in source
    assert '"run",' in source
    assert '"list",' in source
    assert '"view",' in source

    for forbidden in (
        '"workflow", "run"',
        "run_github_research_love_prepare_once_0287",
        "run_github_actions_artifact_fetch_once_0287",
        "Scheduler(",
        "QdrantClient(",
        "psycopg.connect(",
        "openvino.Core(",
    ):
        assert forbidden not in source
