from __future__ import annotations

from pathlib import Path

from context.github_controlled_advisory_issue_publication_0281 import (
    GitHubIssueCommentSnapshot,
)
from context.github_research_love_final_deliverable_sql_0287 import (
    RECEIPT_SCHEMA as FINAL_SQL_RECEIPT_SCHEMA,
    RESULT_SCHEMA as FINAL_SQL_RESULT_SCHEMA,
)
from context.github_research_love_final_remote_publication_0287 import (
    GitHubResearchLoveFinalPublicationCommand,
    GitHubResearchLoveFinalPublicationExecution,
    build_github_research_love_final_publication_plan,
    execute_github_research_love_final_publication,
)
from context.github_research_love_liaison_synthesis_0287 import (
    RESULT_SCHEMA as LIAISON_RESULT_SCHEMA,
)
from context.love_final_deliverable_publication_plan_0287 import (
    ProjectV2FieldSnapshot,
)
from context.love_final_deliverable_remote_publication_0287 import (
    parse_love_final_deliverable_publication_plan,
)


def _liaison() -> dict[str, object]:
    return {
        "schema": LIAISON_RESULT_SCHEMA,
        "valid": True,
        "status": "synthesized",
        "plan": {
            "plan_digest": "sha256:" + "1" * 64,
            "work_package_ref": "research-work-package:test",
            "first_sql_ref": "context-object:first",
            "second_sql_ref": "context-object:second",
        },
        "mutualization": {
            "schema": "missipy.love.evidence_mutualization.v1",
            "convergences": ["réciprocité"],
            "contradictions": ["confiance et asymétrie"],
            "uncertainties": ["intentions indisponibles"],
            "recommendations": ["clarifier les limites"],
            "evidence_refs": [
                "sql:context-object:first",
                "sql:context-object:second",
            ],
        },
        "synthesis": {
            "final_publication_ready": False,
            "provenance_hidden": True,
        },
    }


def _final_deliverable() -> dict[str, object]:
    target = "github:newicody/projects#15"
    return {
        "schema": FINAL_SQL_RESULT_SCHEMA,
        "valid": True,
        "status": "persisted",
        "remote_publication_performed": False,
        "plan": {
            "plan_digest": "sha256:" + "2" * 64,
            "work_package_ref": "research-work-package:test",
            "liaison_plan_digest": "sha256:" + "1" * 64,
            "analysis_sql_plan_digest": "sha256:" + "3" * 64,
            "parent_revision_ref": "context-revision:github-love-pair",
            "first_analysis_object_ref": "context-object:first",
            "second_analysis_object_ref": "context-object:second",
            "packet": {
                "schema": "missipy.specialist_liaison.final_packet.v1",
                "packet_ref": "publication:final-synthesis:test",
                "target_ref": target,
                "title": "Synthèse finale de l’étude",
                "body": (
                    "La confiance, la réciprocité et les limites doivent "
                    "être examinées ensemble."
                ),
                "evidence_refs": [
                    "sql:context-object:first",
                    "sql:context-object:second",
                ],
                "context_influence_refs": ["ctx:github-research-test"],
                "validation_refs": ["artifact:validation-test"],
                "synthesis": {
                    "synthesis_ref": "specialist-synthesis:test",
                    "request_ref": "research-work-package:test",
                    "title": "Synthèse finale de l’étude",
                    "final_publication_ready": True,
                    "provenance_hidden": True,
                },
            },
            "authority_object": {
                "object_ref": "context-object:github-love-final-test",
            },
            "artifact": {
                "artifact_ref": "artifact:github-love-final-test",
            },
            "revision": {
                "revision_ref": "context-revision:github-love-final-test",
            },
        },
        "receipt": {
            "schema": FINAL_SQL_RECEIPT_SCHEMA,
            "plan_digest": "sha256:" + "2" * 64,
            "packet_ref": "publication:final-synthesis:test",
            "target_ref": target,
            "authority_object_ref": "context-object:github-love-final-test",
            "artifact_ref": "artifact:github-love-final-test",
            "revision_ref": "context-revision:github-love-final-test",
            "readback_verified": True,
            "action": "created",
        },
    }


def _command() -> GitHubResearchLoveFinalPublicationCommand:
    return GitHubResearchLoveFinalPublicationCommand(
        final_deliverable=_final_deliverable(),
        liaison=_liaison(),
        repository="newicody/projects",
        issue_number=15,
        source_issue_ref="github-frame:newicody/projects/issues/15",
        policy_decision_id="policy:github-love-final-test",
        operator_decision="approve",
        project_item_id="PVTI_test",
        project_field_ref="PVTF_test",
        project_field_name="Résumé",
    )


class FakeRemotePorts:
    def __init__(self) -> None:
        self.comments: list[GitHubIssueCommentSnapshot] = []
        self.project_snapshot = ProjectV2FieldSnapshot(
            project_item_id="PVTI_test",
            field_ref="PVTF_test",
            field_name="Résumé",
            value="",
        )
        self.create_count = 0
        self.update_count = 0

    def list_comments(
        self,
        repository: str,
        issue_number: int,
    ) -> tuple[GitHubIssueCommentSnapshot, ...]:
        assert repository == "newicody/projects"
        assert issue_number == 15
        return tuple(self.comments)

    def create_comment(
        self,
        repository: str,
        issue_number: int,
        body: str,
    ) -> GitHubIssueCommentSnapshot:
        self.create_count += 1
        comment = GitHubIssueCommentSnapshot(
            comment_id=123,
            body=body,
            html_url=(
                "https://github.com/newicody/projects/issues/15"
                "#issuecomment-123"
            ),
        )
        self.comments.append(comment)
        return comment

    def read_field(
        self,
        *,
        project_item_id: str,
        field_ref: str,
        field_name: str,
    ) -> ProjectV2FieldSnapshot:
        assert project_item_id == "PVTI_test"
        assert field_ref == "PVTF_test"
        assert field_name == "Résumé"
        return self.project_snapshot

    def update_field(self, projection) -> None:
        self.update_count += 1
        self.project_snapshot = ProjectV2FieldSnapshot(
            project_item_id=projection.project_item_id,
            field_ref=projection.field_ref,
            field_name=projection.field_name,
            value=projection.value,
        )


def test_plan_reuses_existing_planner_and_is_cli_parseable() -> None:
    plan = build_github_research_love_final_publication_plan(_command())
    mapping = plan.to_mapping()
    reparsed = parse_love_final_deliverable_publication_plan(mapping)

    assert plan.publication_plan.valid is True
    assert plan.publication_plan.action == "create_and_project"
    assert plan.publication_plan.issue_action == "create"
    assert plan.publication_plan.project_action == "update"
    assert "autodoc:final-deliverable:" in plan.publication_plan.body
    assert "Synthèse finale de l’étude" in plan.publication_plan.body
    assert reparsed.plan_digest == plan.plan_digest
    assert mapping["publication_plan"]["plan_digest"] == plan.plan_digest
    assert mapping["boundaries"]["preview_is_default"] is True


def test_preview_reads_remote_state_without_mutation() -> None:
    plan = build_github_research_love_final_publication_plan(_command())
    ports = FakeRemotePorts()

    result = execute_github_research_love_final_publication(
        GitHubResearchLoveFinalPublicationExecution(
            plan=plan,
            operator_decision="approve",
        ),
        issue_port=ports,
        project_port=ports,
    )

    assert result.valid is True
    assert result.status == "preview"
    assert ports.create_count == 0
    assert ports.update_count == 0
    assert result.to_mapping()["boundaries"][
        "exact_remote_readback_confirmed"
    ] is False


def test_execute_publishes_issue_and_project_then_reads_back_exactly() -> None:
    plan = build_github_research_love_final_publication_plan(_command())
    ports = FakeRemotePorts()

    first = execute_github_research_love_final_publication(
        GitHubResearchLoveFinalPublicationExecution(
            plan=plan,
            operator_decision="approve",
            execute=True,
            confirm_plan_digest=plan.plan_digest,
            remote_mutation_allowed=True,
            issue_publication_allowed=True,
            project_projection_allowed=True,
        ),
        issue_port=ports,
        project_port=ports,
    )
    second = execute_github_research_love_final_publication(
        GitHubResearchLoveFinalPublicationExecution(
            plan=plan,
            operator_decision="approve",
            execute=True,
            confirm_plan_digest=plan.plan_digest,
            remote_mutation_allowed=True,
            issue_publication_allowed=True,
            project_projection_allowed=True,
        ),
        issue_port=ports,
        project_port=ports,
    )

    assert first.valid is True
    assert first.status == "published"
    assert first.remote_result.action == "created_and_projected"
    assert first.remote_result.readback is not None
    assert first.remote_result.readback.valid is True
    assert ports.create_count == 1
    assert ports.update_count == 1

    assert second.valid is True
    assert second.status == "published-replay"
    assert second.remote_result.action == "replay"
    assert ports.create_count == 1
    assert ports.update_count == 1


def test_wrong_digest_blocks_before_mutation() -> None:
    plan = build_github_research_love_final_publication_plan(_command())
    ports = FakeRemotePorts()

    result = execute_github_research_love_final_publication(
        GitHubResearchLoveFinalPublicationExecution(
            plan=plan,
            operator_decision="approve",
            execute=True,
            confirm_plan_digest="wrong",
            remote_mutation_allowed=True,
            issue_publication_allowed=True,
            project_projection_allowed=True,
        ),
        issue_port=ports,
        project_port=ports,
    )

    assert result.valid is False
    assert result.remote_result.action == "blocked"
    assert "confirm-plan-digest mismatch" in result.remote_result.issues
    assert ports.create_count == 0
    assert ports.update_count == 0


def test_module_reuses_existing_publication_boundaries() -> None:
    import context.github_research_love_final_remote_publication_0287 as module

    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "plan_love_final_deliverable_publication(" in source
    assert "execute_love_final_deliverable_remote_publication(" in source
    assert "LoveFinalDeliverableRemotePublicationCommand(" in source
    assert "GitHubCliFinalDeliverablePublicationAdapter(" not in source
    assert "import subprocess" not in source
    assert "from subprocess" not in source
    assert "subprocess." not in source
    assert "requests." not in source
    assert "put_object(" not in source
    assert ".upsert(" not in source
    assert "Scheduler(" not in source
