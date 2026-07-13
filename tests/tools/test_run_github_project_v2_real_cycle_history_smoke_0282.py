from __future__ import annotations

import argparse
import json
from pathlib import Path

from context.github_project_push_frame import (
    build_origin_frame_id,
    build_ticket_revision_id,
)
from context.github_project_v2_append_only_cycle_history_0282 import (
    GitHubProjectV2AppendOnlyCycleHistoryCommand,
    project_github_project_v2_append_only_cycle_history,
)
from context.github_project_v2_cycle_lineage_0282 import (
    GitHubProjectV2CycleLineageCommand,
    build_github_project_v2_cycle_lineage,
    build_github_project_v2_item_ref,
    build_github_project_v2_theme_ref,
)
from context.github_project_v2_parent_theme_query_normalization_0282 import (
    GitHubProjectV2NormalizedParentThemeItem,
)
from tools.run_github_project_v2_real_cycle_history_smoke_0282 import (
    run,
)


REPOSITORY = "newicody/projects"
PROJECT_ID = "PVT_kwHOA3ouXM4Ba3Ar"
ROOT_REF = build_origin_frame_id(REPOSITORY, 15)
ITEM_REF = build_github_project_v2_item_ref("PVTI_15")
THEME_REF = build_github_project_v2_theme_ref(
    PROJECT_ID,
    "PVTF_theme",
    "general",
)
STATUS_REF = build_ticket_revision_id(
    ROOT_REF,
    "project_v2_snapshot_status",
    "snapshot-1",
)


def _write_inputs(tmp_path: Path):
    lineage = build_github_project_v2_cycle_lineage(
        GitHubProjectV2CycleLineageCommand(
            repository=REPOSITORY,
            project_id=PROJECT_ID,
            project_item_ref=ITEM_REF,
            root_issue_ref=ROOT_REF,
            cycle_ordinal=1,
            status_revision_ref=STATUS_REF,
            theme_refs=(THEME_REF,),
        )
    )
    normalized = GitHubProjectV2NormalizedParentThemeItem(
        project_item_ref=ITEM_REF,
        issue_ref=ROOT_REF,
        parent_issue_ref="",
        sub_issue_refs=(),
        theme_refs=(THEME_REF,),
        theme_values=("Général",),
        status_name="En cours",
        status_revision_ref=STATUS_REF,
        hierarchy_payload_present=True,
    )
    history = project_github_project_v2_append_only_cycle_history(
        GitHubProjectV2AppendOnlyCycleHistoryCommand(
            lineage=lineage,
            normalized_item=normalized,
        )
    )

    history_path = tmp_path / "history.json"
    issues_path = tmp_path / "issues.json"
    theme_path = tmp_path / "theme.json"
    history_path.write_text(
        json.dumps(history.to_json_dict()),
        encoding="utf-8",
    )
    issues_path.write_text(
        json.dumps(
            {
                "issues": [
                    {
                        "issue_ref": ROOT_REF,
                        "issue_number": 15,
                        "title": "Recherche racine",
                        "body": "Besoin initial",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    theme_path.write_text(
        json.dumps(
            {
                "owner_kind": "user",
                "owner_login": "newicody",
                "project_number": 3,
                "project_id": PROJECT_ID,
                "field_name": "Thème",
                "desired_options": [
                    {
                        "name": "Général",
                        "color": "BLUE",
                    }
                ],
                "target_view_number": 2,
            }
        ),
        encoding="utf-8",
    )
    return history_path, issues_path, theme_path


def _args(tmp_path: Path):
    history_path, issues_path, theme_path = _write_inputs(
        tmp_path
    )
    return argparse.Namespace(
        history=history_path,
        issues=issues_path,
        theme_command=theme_path,
        next_cycle_title="Cycle 2",
        next_cycle_summary="Continuer la recherche.",
        policy_decision_id="policy:0282:r8",
        operator_decision="approve",
        source_artifact_ref=[],
        decision_ref=[],
        output_root=tmp_path / "out",
        execute=False,
        confirm_smoke_digest="",
        gh_command="gh",
        format="json",
    )


def _fake_adapter(calls, report=None):
    payload = report or {
        "schema": (
            "missipy.github."
            "project_v2_operator_authorized_mutation_adapter.v1"
        ),
        "mode": "preview",
        "operation_results": [],
        "github_mutation_performed": False,
        "partial_execution": False,
    }

    def invoke(argv):
        calls.append(tuple(argv or ()))
        print(json.dumps(payload))
        return 0

    return invoke


def test_preview_reuses_r7_and_writes_deterministic_artifacts(
    tmp_path,
    capsys,
):
    args = _args(tmp_path)
    calls = []

    code = run(args, adapter_main=_fake_adapter(calls))

    assert code == 0
    assert len(calls) == 1
    assert "--execute" not in calls[0]
    output = json.loads(capsys.readouterr().out)
    output_dir = Path(output["output_dir"])
    assert (output_dir / "parent_sub_ticket_plan.json").is_file()
    assert (output_dir / "theme_grouping_plan.json").is_file()
    assert (output_dir / "smoke_result.json").is_file()
    assert (output_dir / "adapter_report.json").is_file()
    assert output["github_mutation_performed"] is False


def test_execute_rejects_wrong_smoke_digest_before_adapter(
    tmp_path,
    capsys,
):
    args = _args(tmp_path)
    args.execute = True
    args.confirm_smoke_digest = "0" * 64
    calls = []

    code = run(args, adapter_main=_fake_adapter(calls))

    assert code == 3
    assert calls == []
    output = json.loads(capsys.readouterr().out)
    assert output["execution_error"] == (
        "confirm-smoke-digest mismatch"
    )
    assert output["github_mutation_performed"] is False


def test_execute_passes_internal_exact_plan_digests(
    tmp_path,
    capsys,
):
    preview_args = _args(tmp_path)
    preview_calls = []
    assert (
        run(
            preview_args,
            adapter_main=_fake_adapter(preview_calls),
        )
        == 0
    )
    preview = json.loads(capsys.readouterr().out)

    execute_args = _args(tmp_path)
    execute_args.execute = True
    execute_args.confirm_smoke_digest = preview["smoke_digest"]
    execute_calls = []

    code = run(
        execute_args,
        adapter_main=_fake_adapter(
            execute_calls,
            {
                "schema": (
                    "missipy.github."
                    "project_v2_operator_authorized_mutation_adapter.v1"
                ),
                "mode": "execute",
                "operation_results": [
                    {"operation_kind": "create_issue"}
                ],
                "github_mutation_performed": True,
                "partial_execution": False,
            },
        ),
    )

    assert code == 0
    invocation = execute_calls[0]
    assert "--execute" in invocation
    assert "--confirm-parent-plan-digest" in invocation
    assert "--confirm-theme-plan-digest" in invocation
    output = json.loads(capsys.readouterr().out)
    assert output["github_mutation_performed"] is True


def test_partial_execution_is_propagated_honestly(
    tmp_path,
    capsys,
):
    args = _args(tmp_path)
    calls = []

    code = run(
        args,
        adapter_main=_fake_adapter(
            calls,
            {
                "schema": (
                    "missipy.github."
                    "project_v2_operator_authorized_mutation_adapter.v1"
                ),
                "mode": "preview",
                "operation_results": [
                    {"operation_kind": "create_issue"}
                ],
                "github_mutation_performed": True,
                "partial_execution": True,
                "execution_error": "later operation failed",
            },
        ),
    )

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["partial_execution"] is True
    assert output["github_mutation_performed"] is True
