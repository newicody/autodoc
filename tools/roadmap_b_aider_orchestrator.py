#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]

ROADMAP_B_STEPS: tuple[dict[str, str], ...] = (
    {
        "id": "part8_1_local_data_contract",
        "title": "Local data contract",
        "goal": "Define stable local data directories, manifests, generated artifacts policy and source-of-truth rules.",
        "risk": "low",
    },
    {
        "id": "part8_2_document_model",
        "title": "Document model",
        "goal": "Add Document, DocumentChunk, Artifact and OperatorDecision local models.",
        "risk": "medium",
    },
    {
        "id": "part8_3_incremental_file_scan",
        "title": "Incremental file scanner",
        "goal": "Scan local files, hash them, detect changes and write local scan manifests.",
        "risk": "medium",
    },
    {
        "id": "part8_4_context_bundle_builder",
        "title": "Context bundle builder",
        "goal": "Build small auditable context bundles from documents without embeddings yet.",
        "risk": "medium",
    },
    {
        "id": "part8_5_retrieval_evaluation_set",
        "title": "Retrieval evaluation set",
        "goal": "Create local evaluation fixtures for known questions, expected files and expected context.",
        "risk": "medium",
    },
    {
        "id": "part8_6_operator_feedback_loop",
        "title": "Operator feedback loop",
        "goal": "Record accept, reject and needs-more-context decisions and replay them locally.",
        "risk": "medium",
    },
)

DEFAULT_CONTEXT_FILES: tuple[str, ...] = (
    "README.md",
    "doc/maintenance/ROADMAP_B_LOCK.md",
    "doc/maintenance/PHASE7_FREEZE_HANDOFF_CONTRACT.md",
    "doc/maintenance/PHASE7_CLOSURE_REPORT.md",
)

DEFAULT_TEST_COMMANDS: tuple[str, ...] = (
    "PYTHONPATH=src:. python -m compileall -q src tests tools",
    "PYTHONPATH=src:. pytest -q tests/rules",
    "PYTHONPATH=src:. pytest -q",
)

SENSITIVE_RULE_PATHS: tuple[str, ...] = ("tests/rules/", "doc/code-rules/")
SENSITIVE_DEPENDENCY_FILES: tuple[str, ...] = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
)
SENSITIVE_RUNTIME_PATHS: tuple[str, ...] = ("src/kernel/scheduler.py", "src/scheduler/")


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    output: str


@dataclass(frozen=True)
class PatchInspection:
    patch_id: str
    warnings: tuple[str, ...]
    added_line_count: int
    removed_line_count: int

    @property
    def requires_operator_validation(self) -> bool:
        return bool(self.warnings)


@dataclass
class OrchestratorStepResult:
    step_id: str
    title: str
    status: str
    patch_id: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class OrchestratorRunReport:
    started_at_epoch: float
    max_minutes: int
    max_steps: int
    results: list[OrchestratorStepResult] = field(default_factory=list)

    @property
    def elapsed_minutes(self) -> float:
        return (time.time() - self.started_at_epoch) / 60.0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.roadmap_b_aider_orchestrator_run_report.v1",
            "elapsed_minutes": self.elapsed_minutes,
            "max_minutes": self.max_minutes,
            "max_steps": self.max_steps,
            "results": [
                {
                    "step_id": result.step_id,
                    "title": result.title,
                    "status": result.status,
                    "patch_id": result.patch_id,
                    "notes": result.notes,
                }
                for result in self.results
            ],
        }


def build_aider_command(
    *,
    message_file: Path,
    edit_files: Sequence[str],
    read_files: Sequence[str],
    yes_always: bool = False,
    extra_args: Sequence[str] = (),
) -> list[str]:
    command = [
        os.environ.get("AIDER_BIN", "aider"),
        "--message-file",
        str(message_file),
        "--no-auto-commits",
        "--no-stream",
        "--no-auto-test",
        "--no-auto-lint",
    ]
    if yes_always:
        command.append("--yes-always")
    command.extend(extra_args)
    for read_file in read_files:
        command.extend(["--read", read_file])
    for edit_file in edit_files:
        command.extend(["--file", edit_file])
    return command


def build_aider_prompt(
    *,
    patch_number: int,
    step: dict[str, str],
    repo_snapshot: str,
    conversation_context: str,
    last_failure: str | None = None,
) -> str:
    patch_id_hint = f"{patch_number:04d}-part8_roadmap_b_{step['id']}"
    failure_block = ""
    if last_failure:
        failure_block = f"""
# Previous failure to fix first

{last_failure[:16000]}
"""

    return f"""
You are Aider operating inside the Autodoc/MissiPy git repository.

You must create a patch bundle only. Do not apply the patch to source files
outside the patch bundle.

Create exactly this directory:

patch/{patch_id_hint}/
  README.md
  metadata.json
  patch.diff

Roadmap is locked to Roadmap B:
- build a robust local-first foundation before real external integration
- local server/repo remains source of truth
- GitHub/external surfaces are synchronization/review surfaces only
- no remote mutation by default
- no Scheduler path unless explicitly approved

Patch rules:
- use the existing patch queue contract
- patch.diff must be applicable by apply_patch_queue.py
- keep increments small
- add tests and docs for the new behavior
- keep Markdown under existing doc/ subdirectories
- do not version generated context SVG files
- if adding DOT, do not reference code_rule inside DOT labels or nodes
- no network code
- no token/authorization handling
- no dependency additions unless explicitly justified
- no significant rules changes unless explicitly justified
- no broad retroactive refactor unless explicitly justified

Current step:
id: {step['id']}
title: {step['title']}
goal: {step['goal']}
risk: {step['risk']}

{failure_block}

Conversation/project context:

{conversation_context[:24000]}

Repository snapshot:

{repo_snapshot[:30000]}
"""


def estimate_run_minutes(step_count: int) -> int:
    return max(20, step_count * 30)


def select_roadmap_steps(*, max_steps: int) -> tuple[dict[str, str], ...]:
    return ROADMAP_B_STEPS[:max_steps]


def next_patch_number(patch_root: Path) -> int:
    numbers: list[int] = []
    if patch_root.exists():
        for child in patch_root.iterdir():
            match = re.match(r"^(\d{4})-", child.name)
            if match:
                numbers.append(int(match.group(1)))
    return max(numbers, default=37) + 1


def inspect_patch_bundle(patch_dir: Path, *, max_changed_lines: int = 1200) -> PatchInspection:
    diff_path = patch_dir / "patch.diff"
    warnings: list[str] = []
    if not diff_path.exists():
        return PatchInspection(
            patch_id=patch_dir.name,
            warnings=("missing patch.diff",),
            added_line_count=0,
            removed_line_count=0,
        )

    text = diff_path.read_text(encoding="utf-8", errors="replace")
    added = [line for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed = [line for line in text.splitlines() if line.startswith("-") and not line.startswith("---")]

    for marker in SENSITIVE_RULE_PATHS:
        if marker in text:
            warnings.append(f"sensitive rules path touched: {marker}")
    for file_name in SENSITIVE_DEPENDENCY_FILES:
        if f" b/{file_name}" in text or f"+++ b/{file_name}" in text:
            warnings.append(f"dependency file touched: {file_name}")
    for marker in SENSITIVE_RUNTIME_PATHS:
        if marker in text:
            warnings.append(f"sensitive runtime path touched: {marker}")
    if len(added) + len(removed) > max_changed_lines:
        warnings.append(f"large patch: {len(added) + len(removed)} changed lines")

    return PatchInspection(
        patch_id=patch_dir.name,
        warnings=tuple(warnings),
        added_line_count=len(added),
        removed_line_count=len(removed),
    )


def parse_git_status_paths(status: str) -> tuple[str, ...]:
    paths: list[str] = []
    for line in status.splitlines():
        if not line:
            continue
        paths.append(line[3:] if len(line) > 3 else line)
    return tuple(paths)


def require_clean_worktree(*, allow_patch_dirs: bool = True) -> None:
    status = run_command(["git", "status", "--short"]).output.strip()
    if not status:
        return
    blocked = []
    for path in parse_git_status_paths(status):
        if allow_patch_dirs and path.startswith("patch/"):
            continue
        blocked.append(path)
    if blocked:
        raise RuntimeError("working tree is not clean outside allowed patch dirs: " + ", ".join(blocked))


def run_command(command: Sequence[str], *, timeout: int | None = None) -> CommandResult:
    completed = subprocess.run(
        list(command),
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return CommandResult(tuple(command), completed.returncode, completed.stdout)


def run_command_checked(command: Sequence[str], *, timeout: int | None = None) -> CommandResult:
    result = run_command(command, timeout=timeout)
    print("$ " + " ".join(shlex.quote(part) for part in command))
    if result.output:
        print(result.output)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}")
    return result


def repo_snapshot() -> str:
    commands = (
        ("git", "log", "--oneline", "-12"),
        ("git", "status", "--short"),
        ("find", "src", "tests", "tools", "doc", "-maxdepth", "3", "-type", "f"),
    )
    chunks: list[str] = []
    for command in commands:
        result = run_command(command)
        chunks.append(f"## {' '.join(command)}\n{result.output[:20000]}")
    return "\n\n".join(chunks)


def load_context_files(paths: Sequence[str]) -> str:
    chunks: list[str] = []
    for raw_path in paths:
        path = ROOT / raw_path
        if path.exists():
            chunks.append(f"# {raw_path}\n{path.read_text(encoding='utf-8', errors='replace')[:20000]}")
    return "\n\n".join(chunks)


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_run_report(path: Path, report: OrchestratorRunReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def maybe_request_operator_approval(inspection: PatchInspection, *, assume_yes: bool = False) -> None:
    if not inspection.requires_operator_validation:
        return
    print("Validation opérateur requise pour " + inspection.patch_id)
    for warning in inspection.warnings:
        print("- " + warning)
    if assume_yes:
        return
    answer = input("Appliquer malgré ces alertes ? [yes/no] ").strip().lower()
    if answer not in {"yes", "y", "oui", "o"}:
        raise RuntimeError("operator refused sensitive patch")


def apply_patch_queue(patch_id: str) -> None:
    run_command_checked(["python", "apply_patch_queue.py", "--patch", patch_id, "--dry-run"])
    run_command_checked(["python", "apply_patch_queue.py", "--patch", patch_id, "--commit", "--push"])


def archive_patch_bundle(patch_dir: Path) -> None:
    run_command_checked(["git", "add", str(patch_dir)])
    diff = run_command(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return
    run_command_checked(["git", "commit", "-m", f"archive patch bundle {patch_dir.name}"])
    run_command_checked(["git", "push"])


def run_default_tests() -> tuple[bool, str]:
    chunks: list[str] = []
    for command_text in DEFAULT_TEST_COMMANDS:
        command = shlex.split(command_text)
        result = run_command(command)
        chunks.append("$ " + command_text + "\n" + result.output)
        print("$ " + command_text)
        if result.output:
            print(result.output)
        if result.returncode != 0:
            return False, "\n".join(chunks)
    return True, "\n".join(chunks)


def run_docs_svg_policy_if_present() -> None:
    tool = ROOT / "tools" / "docs_svg_build_policy.py"
    if tool.exists():
        run_command_checked(
            [
                "python",
                "tools/docs_svg_build_policy.py",
                "--root",
                ".",
                "--clean",
                "--check",
                "--report-file",
                "doc/maintenance/docs_svg_build_policy_report.json",
            ]
        )


def discover_created_patch_dirs(before: set[str]) -> tuple[Path, ...]:
    patch_root = ROOT / "patch"
    if not patch_root.exists():
        return ()
    after = {child.name for child in patch_root.iterdir() if child.is_dir()}
    return tuple(patch_root / name for name in sorted(after - before))


def run_aider_for_step(
    *,
    step: dict[str, str],
    patch_number: int,
    context_files: Sequence[str],
    last_failure: str | None,
    timeout: int,
    yes_always: bool,
    extra_args: Sequence[str],
) -> tuple[Path, str]:
    patch_root = ROOT / "patch"
    patch_root.mkdir(exist_ok=True)
    prompt = build_aider_prompt(
        patch_number=patch_number,
        step=step,
        repo_snapshot=repo_snapshot(),
        conversation_context=load_context_files(context_files),
        last_failure=last_failure,
    )
    prompt_file = write_text(ROOT / "doc" / "maintenance" / "roadmap_b_aider_prompt.md", prompt)
    before = {child.name for child in patch_root.iterdir() if child.is_dir()}
    patch_id_hint = f"{patch_number:04d}-part8_roadmap_b_{step['id']}"
    edit_files = [
        f"patch/{patch_id_hint}/README.md",
        f"patch/{patch_id_hint}/metadata.json",
        f"patch/{patch_id_hint}/patch.diff",
    ]
    command = build_aider_command(
        message_file=prompt_file,
        edit_files=edit_files,
        read_files=context_files,
        yes_always=yes_always,
        extra_args=extra_args,
    )
    result = run_command_checked(command, timeout=timeout)
    created = discover_created_patch_dirs(before)
    if created:
        return created[-1], result.output
    fallback = patch_root / patch_id_hint
    if fallback.exists():
        return fallback, result.output
    raise RuntimeError("aider did not create a patch bundle")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roadmap B orchestrator using Python + Aider + apply_patch_queue.py")
    parser.add_argument("--max-minutes", type=int, default=180)
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--aider-timeout", type=int, default=3600)
    parser.add_argument("--no-aider", action="store_true", help="plan only; print prompts but do not call aider")
    parser.add_argument("--aider-yes-always", action="store_true", help="pass --yes-always to aider")
    parser.add_argument("--assume-yes", action="store_true", help="auto-approve orchestrator warnings")
    parser.add_argument("--archive-patch-bundles", action="store_true", help="commit/push patch bundle before applying it")
    parser.add_argument("--context-file", action="append", default=list(DEFAULT_CONTEXT_FILES))
    parser.add_argument("--aider-extra-arg", action="append", default=[])
    args = parser.parse_args(argv)

    steps = select_roadmap_steps(max_steps=args.max_steps)
    estimate = estimate_run_minutes(len(steps))
    print(f"Roadmap B steps selected: {len(steps)}")
    print(f"Estimated minutes: {estimate}")
    print(f"Budget minutes: {args.max_minutes}")
    if estimate > args.max_minutes and not args.assume_yes:
        answer = input("Estimation supérieure au budget. Continuer ? [yes/no] ").strip().lower()
        if answer not in {"yes", "y", "oui", "o"}:
            return 1

    require_clean_worktree(allow_patch_dirs=True)
    report = OrchestratorRunReport(started_at_epoch=time.time(), max_minutes=args.max_minutes, max_steps=args.max_steps)
    last_failure: str | None = None

    for step in steps:
        if report.elapsed_minutes >= args.max_minutes:
            break
        patch_number = next_patch_number(ROOT / "patch")
        if args.no_aider:
            prompt = build_aider_prompt(
                patch_number=patch_number,
                step=step,
                repo_snapshot=repo_snapshot(),
                conversation_context=load_context_files(args.context_file),
                last_failure=last_failure,
            )
            print(prompt)
            report.results.append(OrchestratorStepResult(step_id=step["id"], title=step["title"], status="planned"))
            continue

        try:
            patch_dir, aider_output = run_aider_for_step(
                step=step,
                patch_number=patch_number,
                context_files=args.context_file,
                last_failure=last_failure,
                timeout=args.aider_timeout,
                yes_always=args.aider_yes_always,
                extra_args=args.aider_extra_arg,
            )
            inspection = inspect_patch_bundle(patch_dir)
            maybe_request_operator_approval(inspection, assume_yes=args.assume_yes)
            if args.archive_patch_bundles:
                archive_patch_bundle(patch_dir)
            apply_patch_queue(patch_dir.name)
            run_docs_svg_policy_if_present()
            ok, test_output = run_default_tests()
            if not ok:
                last_failure = test_output
                report.results.append(
                    OrchestratorStepResult(
                        step_id=step["id"],
                        title=step["title"],
                        status="failed_tests",
                        patch_id=patch_dir.name,
                        notes=[test_output[-4000:]],
                    )
                )
                break
            last_failure = None
            report.results.append(
                OrchestratorStepResult(
                    step_id=step["id"],
                    title=step["title"],
                    status="passed",
                    patch_id=patch_dir.name,
                    notes=[aider_output[-1000:]],
                )
            )
        except Exception as exc:
            last_failure = str(exc)
            report.results.append(OrchestratorStepResult(step_id=step["id"], title=step["title"], status="error", notes=[str(exc)]))
            break
        finally:
            write_run_report(ROOT / "doc" / "maintenance" / "roadmap_b_aider_orchestrator_run_report.json", report)

    for result in report.results:
        print(f"{result.status}: {result.step_id} {result.patch_id or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
