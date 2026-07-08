"""Local read-only pipeline for passive supervisor visual reports.

The pipeline composes existing command surfaces:

1. all-surfaces passive supervisor smoke
2. passive supervisor visual read-model
3. passive supervisor visual layout model

It exists only to generate local `.var/reports` files in the right order. It
does not create a runtime service, renderer, bus, scheduler action, proxy
control path, or persistence mutation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


VISUAL_PIPELINE_AUTHORITY_BOUNDARY: dict[str, bool] = {
    "read_only_visual_pipeline": True,
    "uses_scheduler_run": False,
    "creates_eventbus": False,
    "controls_proxy": False,
    "mutates_shm": False,
    "decides_policy": False,
    "writes_sql": False,
    "writes_qdrant": False,
    "mutates_github": False,
    "requires_non_stdlib": False,
}


def visual_pipeline_paths(report_dir: Path) -> dict[str, Path]:
    """Return the local report paths produced by the visual pipeline."""

    return {
        "all_surfaces_smoke": report_dir / "all_surfaces_passive_supervisor_smoke_0234.json",
        "all_surfaces_audit": report_dir / "all_surfaces_passive_supervisor_smoke_0234.events.jsonl",
        "visual_read_model": report_dir / "passive_supervisor_visual_read_model_0236.json",
        "visual_layout_model": report_dir / "passive_supervisor_visual_layout_model_0237.json",
        "visual_pipeline": report_dir / "passive_supervisor_visual_pipeline_0238.json",
    }


def visual_pipeline_commands(
    *,
    repo_root: Path,
    report_dir: Path,
    python_executable: str = sys.executable,
) -> list[dict[str, Any]]:
    """Build the deterministic command chain without executing it."""

    paths = visual_pipeline_paths(report_dir)
    return [
        {
            "name": "all_surfaces_passive_supervisor_smoke_0234",
            "output": str(paths["all_surfaces_smoke"]),
            "command": [
                python_executable,
                str(repo_root / "tools/run_all_surfaces_passive_supervisor_smoke_0234.py"),
                "--output",
                str(paths["all_surfaces_smoke"]),
                "--audit-jsonl",
                str(paths["all_surfaces_audit"]),
                "--format",
                "summary",
            ],
        },
        {
            "name": "passive_supervisor_visual_read_model_0236",
            "output": str(paths["visual_read_model"]),
            "command": [
                python_executable,
                str(repo_root / "tools/run_passive_supervisor_visual_read_model_0236.py"),
                "--snapshot-json",
                str(paths["all_surfaces_smoke"]),
                "--output",
                str(paths["visual_read_model"]),
                "--format",
                "summary",
            ],
        },
        {
            "name": "passive_supervisor_visual_layout_model_0237",
            "output": str(paths["visual_layout_model"]),
            "command": [
                python_executable,
                str(repo_root / "tools/run_passive_supervisor_visual_layout_model_0237.py"),
                "--input-json",
                str(paths["visual_read_model"]),
                "--output",
                str(paths["visual_layout_model"]),
                "--format",
                "summary",
            ],
        },
    ]


def command_environment(repo_root: Path) -> dict[str, str]:
    """Return an environment with repo and src import paths for subprocess tools."""

    env = dict(os.environ)
    src_root = repo_root / "src"
    existing = env.get("PYTHONPATH", "")
    paths = [str(src_root), str(repo_root)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_command(command: Sequence[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    """Run one pipeline command and return a JSON-compatible result."""

    result = subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


Runner = Callable[[Sequence[str]], dict[str, Any]]


def run_visual_pipeline(
    *,
    repo_root: Path,
    report_dir: Path,
    python_executable: str = sys.executable,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Run the local visual report pipeline and write a summary report."""

    report_dir.mkdir(parents=True, exist_ok=True)
    paths = visual_pipeline_paths(report_dir)
    env = command_environment(repo_root)
    commands = visual_pipeline_commands(
        repo_root=repo_root,
        report_dir=report_dir,
        python_executable=python_executable,
    )

    step_results: list[dict[str, Any]] = []
    effective_runner = runner

    for step in commands:
        if effective_runner is None:
            result = run_command(step["command"], cwd=repo_root, env=env)
        else:
            result = effective_runner(step["command"])
        step_results.append(
            {
                "name": step["name"],
                "output": step["output"],
                "result": result,
            }
        )

    summary = {
        "passive_supervisor_visual_pipeline_written": True,
        "authority_boundary": dict(VISUAL_PIPELINE_AUTHORITY_BOUNDARY),
        "report_dir": str(report_dir),
        "outputs": {key: str(value) for key, value in paths.items()},
        "steps": step_results,
    }
    paths["visual_pipeline"].write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def visual_pipeline_plan(
    *,
    repo_root: Path,
    report_dir: Path,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    """Return the planned command chain without executing it."""

    paths = visual_pipeline_paths(report_dir)
    return {
        "passive_supervisor_visual_pipeline_plan": True,
        "authority_boundary": dict(VISUAL_PIPELINE_AUTHORITY_BOUNDARY),
        "report_dir": str(report_dir),
        "outputs": {key: str(value) for key, value in paths.items()},
        "steps": visual_pipeline_commands(
            repo_root=repo_root,
            report_dir=report_dir,
            python_executable=python_executable,
        ),
    }
