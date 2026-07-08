from pathlib import Path

import apply_patch_queue


def test_commit_candidate_excludes_var_runtime_artifacts() -> None:
    assert not apply_patch_queue.commit_candidate(
        ".var/reports/eventbus_supervision_reuse_findings_triage_0229.json",
        include_patch_artifact=False,
    )
    assert not apply_patch_queue.commit_candidate(
        ".var/reports/eventbus_supervision_reuse_findings_triage_0229.json",
        include_patch_artifact=True,
    )


def test_commit_candidate_keeps_patch_artifact_policy() -> None:
    assert not apply_patch_queue.commit_candidate(
        "patch/0235-r3-patch_queue_ignored_runtime_artifacts_guard/patch.diff",
        include_patch_artifact=False,
    )
    assert apply_patch_queue.commit_candidate(
        "patch/0235-r3-patch_queue_ignored_runtime_artifacts_guard/patch.diff",
        include_patch_artifact=True,
    )


def test_changed_files_for_commit_filters_var_and_patch_by_default(monkeypatch) -> None:
    responses = {
        ("diff", "--name-only"): "src/example.py\n.var/reports/local.json\n",
        ("diff", "--cached", "--name-only"): "doc/example.md\n",
        ("ls-files", "--others", "--exclude-standard"): (
            "patch/example/patch.diff\ntests/example_test.py\n"
        ),
    }

    def fake_git_capture(args: tuple[str, ...], *, root: Path) -> str:
        return responses[args]

    monkeypatch.setattr(apply_patch_queue, "git_capture", fake_git_capture)

    assert apply_patch_queue.changed_files_for_commit(
        Path("."), include_patch_artifact=False
    ) == (
        "doc/example.md",
        "src/example.py",
        "tests/example_test.py",
    )
