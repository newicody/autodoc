from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from roadmap_b_aider_orchestrator import (  # noqa: E402
    build_aider_command,
    build_aider_prompt,
    estimate_run_minutes,
    inspect_patch_bundle,
    next_patch_number,
    parse_git_status_paths,
    select_roadmap_steps,
)


def test_select_roadmap_steps_limits_steps() -> None:
    steps = select_roadmap_steps(max_steps=2)

    assert len(steps) == 2
    assert steps[0]["id"] == "part8_1_local_data_contract"


def test_estimate_run_minutes_has_minimum() -> None:
    assert estimate_run_minutes(0) == 20
    assert estimate_run_minutes(2) == 60


def test_next_patch_number_uses_existing_patch_dirs(tmp_path: Path) -> None:
    (tmp_path / "0038-a").mkdir()
    (tmp_path / "0039-b").mkdir()
    (tmp_path / "not-a-patch").mkdir()

    assert next_patch_number(tmp_path) == 40


def test_build_aider_command_uses_message_file_and_disables_auto_commits(tmp_path: Path) -> None:
    command = build_aider_command(
        message_file=tmp_path / "prompt.md",
        edit_files=["patch/0040-x/patch.diff"],
        read_files=["README.md"],
        yes_always=True,
        extra_args=["--model", "test/model"],
    )

    assert command[0] == "aider"
    assert "--message-file" in command
    assert "--no-auto-commits" in command
    assert "--yes-always" in command
    assert "--read" in command
    assert "--file" in command
    assert "--model" in command


def test_build_aider_prompt_requires_patch_bundle() -> None:
    prompt = build_aider_prompt(
        patch_number=40,
        step={
            "id": "demo",
            "title": "Demo",
            "goal": "Create demo",
            "risk": "low",
        },
        repo_snapshot="repo",
        conversation_context="context",
    )

    assert "patch/0040-part8_roadmap_b_demo/" in prompt
    assert "patch.diff must be applicable by apply_patch_queue.py" in prompt
    assert "Roadmap B" in prompt


def test_inspect_patch_bundle_detects_sensitive_changes(tmp_path: Path) -> None:
    patch_dir = tmp_path / "0040-demo"
    patch_dir.mkdir()
    (patch_dir / "patch.diff").write_text(
        "\n".join(
            [
                "diff --git a/tests/rules/test_x.py b/tests/rules/test_x.py",
                "+++ b/tests/rules/test_x.py",
                "+assert True",
                "diff --git a/requirements.txt b/requirements.txt",
                "+++ b/requirements.txt",
                "+newlib",
                "diff --git a/src/kernel/scheduler.py b/src/kernel/scheduler.py",
                "+++ b/src/kernel/scheduler.py",
                "+change",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    inspection = inspect_patch_bundle(patch_dir)

    assert inspection.requires_operator_validation is True
    assert any("rules" in warning for warning in inspection.warnings)
    assert any("dependency" in warning for warning in inspection.warnings)
    assert any("runtime" in warning for warning in inspection.warnings)


def test_parse_git_status_paths() -> None:
    assert parse_git_status_paths("?? patch/0038-x\n M README.md\n") == (
        "patch/0038-x",
        "README.md",
    )
