#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]

ROADMAP_B_DEFAULT = [
    {
        "id": "part8_1_local_data_contract",
        "title": "Local data contract",
        "goal": "Define stable local data directories, manifests, generated artifacts policy, and source-of-truth rules.",
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
        "goal": "Scan local repo/data files, hash them, detect changes, and write local scan manifests.",
        "risk": "medium",
    },
    {
        "id": "part8_4_context_bundle_builder",
        "title": "Context bundle builder",
        "goal": "Build small auditable context bundles from documents without embeddings yet.",
        "risk": "medium",
    },
    {
        "id": "part8_5_eval_set",
        "title": "Retrieval evaluation set",
        "goal": "Create local evaluation fixtures for known questions, expected files, and expected context.",
        "risk": "medium",
    },
    {
        "id": "part8_6_feedback_loop",
        "title": "Operator feedback loop",
        "goal": "Record accept/reject/needs-more-context decisions and replay them locally.",
        "risk": "medium",
    },
]


SIGNIFICANT_RULE_PATHS = (
    "tests/rules/",
    "doc/code-rules/",
)

SIGNIFICANT_DEPENDENCY_FILES = (
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
)

SIGNIFICANT_RUNTIME_PATHS = (
    "src/kernel/scheduler.py",
    "src/scheduler",
)

DEFAULT_TESTS = [
    "PYTHONPATH=src:. python -m compileall -q src tests tools",
    "PYTHONPATH=src:. pytest -q tests/rules",
    "PYTHONPATH=src:. pytest -q",
]


@dataclass
class StepResult:
    step_id: str
    title: str
    status: str
    patch_id: str | None = None
    notes: list[str] = field(default_factory=list)
    test_output: str = ""


@dataclass
class RunState:
    started_at: float
    max_minutes: int
    max_steps: int
    results: list[StepResult] = field(default_factory=list)

    @property
    def elapsed_minutes(self) -> float:
        return (time.time() - self.started_at) / 60.0

    @property
    def remaining_minutes(self) -> float:
        return max(0.0, self.max_minutes - self.elapsed_minutes)

    def should_stop(self) -> bool:
        return self.elapsed_minutes >= self.max_minutes or len(self.results) >= self.max_steps


def run_cmd(
    cmd: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(shlex.quote(part) for part in cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    if proc.stdout:
        print(proc.stdout)
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}")
    return proc


def git_status_short() -> str:
    return run_cmd(["git", "status", "--short"]).stdout.strip()


def require_clean_tree(*, allow_patch_dirs: bool = True) -> None:
    status = git_status_short()
    if not status:
        return

    bad_lines = []
    for line in status.splitlines():
        path = line[3:] if len(line) > 3 else line
        if allow_patch_dirs and path.startswith("patch/"):
            continue
        bad_lines.append(line)

    if bad_lines:
        raise RuntimeError(
            "working tree is not clean outside allowed patch dirs:\n"
            + "\n".join(bad_lines)
        )


def load_conversation_context(paths: Iterable[Path]) -> str:
    chunks: list[str] = []
    for path in paths:
        if path.exists():
            chunks.append(f"\n# Context from {path}\n")
            chunks.append(path.read_text(encoding="utf-8", errors="replace")[:20_000])
    return "\n".join(chunks)


def repo_snapshot() -> str:
    commands = [
        ["git", "log", "--oneline", "-12"],
        ["git", "status", "--short"],
        ["find", "src", "tests", "tools", "doc", "-maxdepth", "3", "-type", "f"],
    ]
    chunks = []
    for cmd in commands:
        proc = run_cmd(cmd)
        chunks.append(f"\n## {' '.join(cmd)}\n{proc.stdout[:20_000]}")
    return "\n".join(chunks)


def estimate_run(steps: list[dict], max_minutes: int) -> None:
    estimated = len(steps) * 18
    print(f"Étapes prévues: {len(steps)}")
    print(f"Budget demandé: {max_minutes} min")
    print(f"Estimation grossière: {estimated} min")

    if estimated > max_minutes:
        print()
        print("La tâche risque de dépasser le budget.")
        print("Réduction conseillée:")
        print("- limiter --max-steps")
        print("- commencer par les étapes low/medium")
        print("- éviter les refactors rétroactifs dans ce run")
        answer = input("Continuer quand même ? [yes/no] ").strip().lower()
        if answer not in {"yes", "y", "oui", "o"}:
            raise SystemExit("run annulé avant démarrage")


def next_patch_number() -> int:
    existing = []
    patch_root = ROOT / "patch"
    if patch_root.exists():
        for child in patch_root.iterdir():
            match = re.match(r"^(\d{4})-", child.name)
            if match:
                existing.append(int(match.group(1)))
    return max(existing, default=37) + 1


def build_codex_prompt(
    *,
    patch_number: int,
    step: dict,
    snapshot: str,
    conversation_context: str,
    last_failure: str | None,
) -> str:
    patch_id_hint = f"{patch_number:04d}-roadmap_b_{step['id']}"
    failure_block = ""
    if last_failure:
        failure_block = f"""
# Previous failure to address

{last_failure[:16_000]}
"""

    return f"""
Tu es Codex dans le repo Autodoc/MissiPy.

Objectif global verrouillé: Roadmap B.
Priorité: socle local robuste avant vraie intégration externe.

Tu dois produire un patch bundle, pas modifier directement le repo final.

Créer exactement:

patch/{patch_id_hint}/
  README.md
  metadata.json
  patch.diff

Règles impératives:
- utiliser le style actuel du repo
- petits incréments
- local-first
- pas de réseau
- pas de mutation distante
- pas de Scheduler sauf demande explicite
- pas de nouvelle dépendance sans justification dans README.md
- pas de modification significative des tests/rules sans justification claire
- garder les Markdown dans les répertoires existants
- pas de SVG contextuel versionné
- si tu ajoutes un DOT, ne mets pas de référence code_rule dans le DOT
- ajouter tests context/tools/rules si pertinent
- metadata.json doit inclure patch_id, phase, title, commit_message, tests
- patch.diff doit être applicable par apply_patch_queue.py

Étape demandée:
id: {step['id']}
title: {step['title']}
goal: {step['goal']}
risk: {step['risk']}

{failure_block}

# Contexte conversation/projet

{conversation_context[:24_000]}

# Snapshot repo

{snapshot[:30_000]}

Produit le patch bundle maintenant.
"""


def call_codex(prompt: str, *, timeout: int) -> None:
    codex_cmd = os.environ.get("CODEX_CMD", "codex exec")
    cmd = shlex.split(codex_cmd) + [prompt]
    proc = run_cmd(cmd, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError("Codex failed")


def find_new_patch_dirs(before: set[str]) -> list[Path]:
    patch_root = ROOT / "patch"
    if not patch_root.exists():
        return []
    after = {child.name for child in patch_root.iterdir() if child.is_dir()}
    created = sorted(after - before)
    return [patch_root / name for name in created]


def inspect_patch_for_significant_changes(patch_dir: Path) -> list[str]:
    diff_path = patch_dir / "patch.diff"
    if not diff_path.exists():
        return ["missing patch.diff"]

    text = diff_path.read_text(encoding="utf-8", errors="replace")
    warnings = []

    for marker in SIGNIFICANT_RULE_PATHS:
        if f" b/{marker}" in text or f"+++ b/{marker}" in text:
            warnings.append(f"modification de règles détectée: {marker}")

    for dep in SIGNIFICANT_DEPENDENCY_FILES:
        if f" b/{dep}" in text or f"+++ b/{dep}" in text:
            warnings.append(f"modification de dépendances détectée: {dep}")

    for path in SIGNIFICANT_RUNTIME_PATHS:
        if path in text:
            warnings.append(f"modification runtime sensible détectée: {path}")

    added_lines = [line for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    removed_lines = [line for line in text.splitlines() if line.startswith("-") and not line.startswith("---")]
    if len(added_lines) + len(removed_lines) > 1200:
        warnings.append("patch volumineux détecté > 1200 lignes modifiées")

    return warnings


def approve_or_abort(warnings: list[str], patch_dir: Path) -> None:
    if not warnings:
        return

    print()
    print(f"Validation humaine requise pour {patch_dir.name}:")
    for warning in warnings:
        print(f"- {warning}")

    answer = input("Appliquer quand même ? [yes/no] ").strip().lower()
    if answer not in {"yes", "y", "oui", "o"}:
        raise RuntimeError("patch refusé par validation humaine")


def archive_patch_bundle(patch_dir: Path) -> None:
    run_cmd(["git", "add", str(patch_dir)])
    proc = run_cmd(["git", "diff", "--cached", "--quiet"])
    if proc.returncode == 0:
        print("Aucun bundle patch à archiver.")
        return
    run_cmd(["git", "commit", "-m", f"archive patch bundle {patch_dir.name}"], check=True)
    run_cmd(["git", "push"], check=True)


def apply_patch_queue(patch_id: str) -> None:
    run_cmd(["python", "apply_patch_queue.py", "--patch", patch_id, "--dry-run"], check=True)
    run_cmd(["python", "apply_patch_queue.py", "--patch", patch_id, "--commit", "--push"], check=True)


def run_tests() -> tuple[bool, str]:
    output = []
    for cmd_text in DEFAULT_TESTS:
        cmd = shlex.split(cmd_text)
        proc = run_cmd(cmd)
        output.append(f"$ {cmd_text}\n{proc.stdout}")
        if proc.returncode != 0:
            return False, "\n".join(output)
    return True, "\n".join(output)


def run_docs_svg_policy_if_available() -> None:
    tool = ROOT / "tools" / "docs_svg_build_policy.py"
    if not tool.exists():
        return

    run_cmd(
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


def write_run_report(state: RunState) -> Path:
    path = ROOT / "doc" / "maintenance" / "roadmap_b_orchestrator_run_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "missipy.roadmap_b_orchestrator_run_report.v1",
        "elapsed_minutes": state.elapsed_minutes,
        "max_minutes": state.max_minutes,
        "max_steps": state.max_steps,
        "results": [
            {
                "step_id": result.step_id,
                "title": result.title,
                "status": result.status,
                "patch_id": result.patch_id,
                "notes": result.notes,
            }
            for result in state.results
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Roadmap B local orchestrator using Codex + apply_patch_queue.py")
    parser.add_argument("--max-minutes", type=int, default=180)
    parser.add_argument("--max-steps", type=int, default=2)
    parser.add_argument("--codex-timeout", type=int, default=3600)
    parser.add_argument("--no-codex", action="store_true", help="plan only, do not call Codex")
    parser.add_argument("--archive-patch-bundles", action="store_true", help="commit/push patch/<id> before applying")
    parser.add_argument(
        "--context-file",
        action="append",
        default=[
            "README.md",
            "doc/maintenance/PHASE7_FREEZE_HANDOFF_CONTRACT.md",
            "doc/maintenance/PHASE7_CLOSURE_REPORT.md",
        ],
    )
    args = parser.parse_args()

    require_clean_tree(allow_patch_dirs=True)

    steps = ROADMAP_B_DEFAULT[: args.max_steps]
    estimate_run(steps, args.max_minutes)

    state = RunState(
        started_at=time.time(),
        max_minutes=args.max_minutes,
        max_steps=args.max_steps,
    )

    context_paths = [ROOT / path for path in args.context_file]
    conversation_context = load_conversation_context(context_paths)

    last_failure: str | None = None

    for step in steps:
        if state.should_stop():
            break

        print()
        print("=" * 80)
        print(f"Étape: {step['id']} — {step['title']}")
        print("=" * 80)

        before_patch_dirs = {
            child.name
            for child in (ROOT / "patch").iterdir()
            if (ROOT / "patch").exists() and child.is_dir()
        }

        snapshot = repo_snapshot()
        patch_number = next_patch_number()
        prompt = build_codex_prompt(
            patch_number=patch_number,
            step=step,
            snapshot=snapshot,
            conversation_context=conversation_context,
            last_failure=last_failure,
        )

        if args.no_codex:
            print(prompt)
            state.results.append(
                StepResult(
                    step_id=step["id"],
                    title=step["title"],
                    status="planned",
                    notes=["no-codex mode"],
                )
            )
            continue

        try:
            call_codex(prompt, timeout=args.codex_timeout)
            new_patch_dirs = find_new_patch_dirs(before_patch_dirs)
            if not new_patch_dirs:
                raise RuntimeError("Codex did not create a new patch directory")

            patch_dir = new_patch_dirs[-1]
            patch_id = patch_dir.name

            warnings = inspect_patch_for_significant_changes(patch_dir)
            approve_or_abort(warnings, patch_dir)

            if args.archive_patch_bundles:
                archive_patch_bundle(patch_dir)

            apply_patch_queue(patch_id)
            run_docs_svg_policy_if_available()

            ok, test_output = run_tests()
            if ok:
                state.results.append(
                    StepResult(
                        step_id=step["id"],
                        title=step["title"],
                        status="passed",
                        patch_id=patch_id,
                        test_output=test_output,
                    )
                )
                last_failure = None
            else:
                state.results.append(
                    StepResult(
                        step_id=step["id"],
                        title=step["title"],
                        status="failed_tests",
                        patch_id=patch_id,
                        test_output=test_output,
                    )
                )
                last_failure = test_output
                print("Tests en échec. La prochaine étape sera une étape de debug.")
                break

        except Exception as exc:
            state.results.append(
                StepResult(
                    step_id=step["id"],
                    title=step["title"],
                    status="error",
                    notes=[str(exc)],
                )
            )
            last_failure = str(exc)
            print(f"Erreur: {exc}")
            break
        finally:
            report = write_run_report(state)
            print(f"Rapport local: {report}")

    print()
    print("Résumé:")
    for result in state.results:
        print(f"- {result.status}: {result.step_id} {result.patch_id or ''}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
