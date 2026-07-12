from context.github_project_v2_en_cours_dispatch_0275_r8 import (
    GitHubProjectV2EnCoursDispatchCommand,
    GitHubProjectV2EnCoursDispatchConfig,
    apply_successful_dispatch,
    build_en_cours_dispatch_plan,
    empty_dispatch_state,
)


def _change(
    *,
    item_id: str,
    number: int,
    title: str,
    before: str,
    after: str = "En cours",
    repository: str = "newicody/projects",
) -> dict:
    return {
        "item_id": item_id,
        "item_type": {"before": "ISSUE", "after": "ISSUE"},
        "status": {"before": before, "after": after},
        "after": {
            "id": item_id,
            "type": "ISSUE",
            "content": {
                "number": number,
                "title": title,
                "url": f"https://github.com/{repository}/issues/{number}",
                "repository": {"nameWithOwner": repository},
            },
        },
    }


def _change_set(*changes: dict) -> dict:
    return {
        "schema": "missipy.github.project_v2_snapshot_change_set.v1",
        "change_set_ref": "github-project-v2-change-set:test",
        "items": {"changed": list(changes)},
    }


def _config() -> GitHubProjectV2EnCoursDispatchConfig:
    return GitHubProjectV2EnCoursDispatchConfig(
        repository="newicody/projects",
        workflow_name="autodoc-controlled-research.yml",
        ref="master",
        allow_workflow_dispatch=True,
        allow_remote_mutation=True,
    )


def test_0275_r8_maps_intention_columns_to_en_cours_dispatch() -> None:
    plan = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=_change_set(
            _change(item_id="PVTI_1", number=1, title="R", before="Recherche"),
            _change(
                item_id="PVTI_2",
                number=2,
                title="D",
                before="Développement",
            ),
            _change(
                item_id="PVTI_3",
                number=3,
                title="P",
                before="Production",
            ),
            _change(item_id="PVTI_4", number=4, title="Blank", before=""),
        ),
        state=empty_dispatch_state(),
    )

    assert plan.valid is True
    assert [candidate.requested_status for candidate in plan.candidates] == [
        "Recherche",
        "Développement",
        "Production",
        "Recherche",
    ]
    assert all(candidate.current_status == "En cours" for candidate in plan.candidates)


def test_0275_r8_ignores_non_triggering_and_invalid_relaunch_transitions() -> None:
    plan = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=_change_set(
            _change(item_id="PVTI_1", number=1, title="Done", before="Terminé"),
            _change(item_id="PVTI_2", number=2, title="Drop", before="Drop"),
            _change(
                item_id="PVTI_3",
                number=3,
                title="Elsewhere",
                before="Recherche",
                after="Terminé",
            ),
        ),
        state=empty_dispatch_state(),
    )

    assert plan.valid is True
    assert plan.candidates == ()
    assert plan.skipped_non_triggering == 3


def test_0275_r8_is_idempotent_and_tracks_continuations() -> None:
    change_set = _change_set(
        _change(item_id="PVTI_1", number=12, title="Recherche", before="Recherche")
    )
    state = empty_dispatch_state()
    first = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=change_set,
        state=state,
    )
    assert first.candidates[0].request_mode == "initial"

    state = apply_successful_dispatch(state, first.candidates[0])
    duplicate = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=change_set,
        state=state,
    )
    assert duplicate.candidates == ()
    assert duplicate.skipped_already_processed == 1

    next_change_set = {
        **change_set,
        "change_set_ref": "github-project-v2-change-set:next",
    }
    continuation = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=next_change_set,
        state=state,
    )
    assert continuation.candidates[0].request_mode == "continuation"


def test_0275_r8_preserves_transversal_event_mode() -> None:
    plan = build_en_cours_dispatch_plan(
        _config(),
        GitHubProjectV2EnCoursDispatchCommand(),
        change_set=_change_set(
            _change(
                item_id="PVTI_EVENT",
                number=24,
                title="[Événement lié] Réseau et modèles",
                before="Recherche",
            )
        ),
        state=empty_dispatch_state(),
    )

    assert plan.valid is True
    assert plan.candidates[0].request_mode == "transversal"


def test_0275_r8_execute_requires_explicit_policy_and_scoped_permissions() -> None:
    config = GitHubProjectV2EnCoursDispatchConfig(
        repository="newicody/projects",
        workflow_name="autodoc-controlled-research.yml",
        ref="master",
    )
    plan = build_en_cours_dispatch_plan(
        config,
        GitHubProjectV2EnCoursDispatchCommand(execute=True),
        change_set=_change_set(),
        state=empty_dispatch_state(),
    )

    assert plan.valid is False
    assert "policy_decision_id is required for execute mode" in plan.issues
    assert "workflow dispatch is not allowed" in plan.issues
    assert "scoped remote mutation is not allowed" in plan.issues
