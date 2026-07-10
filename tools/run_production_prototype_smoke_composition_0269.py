#!/usr/bin/env python3
"""Compose the existing 0260-0268 production prototype tools in one shot."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (str(SRC_ROOT), str(ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from context.production_prototype_smoke_composition_0269 import (  # noqa: E402
    ProductionPrototypeSmokeCommand,
    ProductionPrototypeStepOutcome,
    ProductionPrototypeStepSpec,
    plan_production_prototype_smoke,
    run_production_prototype_smoke,
)

DEFAULT_BOOTSTRAP = ROOT / ".var/reports/scheduler_runtime_bootstrap_registry_attachment_0258.json"
DEFAULT_DATABASE = ROOT / ".var/local/scheduler_managed_db_api_sql_context_store_0260.sqlite3"
DEFAULT_REPORTS_DIR = ROOT / ".var/reports"
DEFAULT_OPENRC_SCRIPT = ROOT / ".var/reports/autodoc-local-runtime.openrc"
DEFAULT_OUTPUT = ROOT / ".var/reports/production_prototype_smoke_composition_0269.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--python-executable", default=sys.executable)
    parser.add_argument("--bootstrap-report", default=str(DEFAULT_BOOTSTRAP))
    parser.add_argument("--db-path", default=str(DEFAULT_DATABASE))
    parser.add_argument("--reports-dir", default=str(DEFAULT_REPORTS_DIR))
    parser.add_argument("--openrc-script-output", default=str(DEFAULT_OPENRC_SCRIPT))
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--model-dir", default="")
    parser.add_argument("--device", default="CPU")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--demo-embedding", action="store_true")
    parser.add_argument("--demo-eventbus", action="store_true")
    parser.add_argument("--demo-qdrant", action="store_true")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args()


def _atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _extract_pairs(payload: object, names: set[str], *, prefix: str = "") -> dict[str, object]:
    found: dict[str, object] = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            qualified = f"{prefix}.{key}" if prefix else str(key)
            if key in names and isinstance(value, (str, bool, int, float)):
                found[str(key)] = value
            found.update(_extract_pairs(value, names, prefix=qualified))
    elif isinstance(payload, list):
        for item in payload:
            found.update(_extract_pairs(item, names, prefix=prefix))
    return found


def _load_report(path: Path) -> tuple[bool | None, tuple[tuple[str, str], ...], tuple[tuple[str, bool], ...]]:
    if not path.is_file():
        return None, (), ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, (), ()
    if not isinstance(payload, dict):
        return False, (), ()

    values = _extract_pairs(
        payload,
        {
            "sql_ref",
            "embedding_ref",
            "handoff_ref",
            "readiness_ref",
            "remote_mutation_allowed",
            "scheduler_starts_external_services",
            "calls_rc_service",
            "starts_postgresql",
            "starts_openvino",
            "starts_qdrant",
            "eventbus_observation_only",
            "events_are_facts_not_commands",
            "passive_supervisor_observation_only",
            "sqlite_database_present",
            "readiness_only",
        },
    )
    references = tuple(
        sorted(
            (key, value)
            for key, value in values.items()
            if key.endswith("_ref") and isinstance(value, str) and value
        )
    )
    checks = tuple(
        sorted(
            (key, value)
            for key, value in values.items()
            if not key.endswith("_ref") and isinstance(value, bool)
        )
    )
    return payload.get("valid") is True, references, checks


def _subprocess_executor(repo_root: Path):
    def execute(step: ProductionPrototypeStepSpec) -> ProductionPrototypeStepOutcome:
        environment = os.environ.copy()
        existing = environment.get("PYTHONPATH", "")
        required = os.pathsep.join((str(repo_root / "src"), str(repo_root)))
        environment["PYTHONPATH"] = os.pathsep.join((required, existing)) if existing else required
        try:
            completed = subprocess.run(
                step.argv,
                cwd=repo_root,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            return ProductionPrototypeStepOutcome(
                phase=step.phase,
                returncode=127,
                stderr=f"{type(exc).__name__}: {exc}",
                report_exists=False,
                report_valid=False,
            )
        report_valid, references, checks = _load_report(step.report_path)
        return ProductionPrototypeStepOutcome(
            phase=step.phase,
            returncode=completed.returncode,
            stdout=completed.stdout.strip(),
            stderr=completed.stderr.strip(),
            report_exists=step.report_path.is_file(),
            report_valid=report_valid,
            references=references,
            checks=checks,
        )

    return execute


def _command_from_args(args: argparse.Namespace) -> ProductionPrototypeSmokeCommand:
    repo_root = Path(args.repo_root).resolve()
    model_dir = Path(args.model_dir).resolve() if args.model_dir else None
    return ProductionPrototypeSmokeCommand(
        repo_root=repo_root,
        python_executable=args.python_executable,
        bootstrap_report=Path(args.bootstrap_report).resolve(),
        database_path=Path(args.db_path).resolve(),
        reports_dir=Path(args.reports_dir).resolve(),
        openrc_script_output=Path(args.openrc_script_output).resolve(),
        repository=args.repository,
        model_dir=model_dir,
        device=args.device,
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
        demo_embedding=args.demo_embedding,
        demo_eventbus=args.demo_eventbus,
        demo_qdrant=args.demo_qdrant,
    )


def _summary(payload: Mapping[str, object]) -> str:
    references = payload.get("references", {})
    checks = payload.get("checks", {})
    boundaries = payload.get("boundaries", {})
    if not isinstance(references, dict):
        references = {}
    if not isinstance(checks, dict):
        checks = {}
    if not isinstance(boundaries, dict):
        boundaries = {}
    return (
        "production_prototype_smoke_composition_valid="
        f"{payload.get('valid')} issues={len(payload.get('issues', []))} "
        f"execute={payload.get('execute')} "
        f"steps={payload.get('valid_step_count', 0)}/{payload.get('planned_step_count', 0)} "
        f"sql_ref={references.get('sql_ref', '-')} "
        f"embedding_ref={references.get('embedding_ref', '-')} "
        f"handoff_ref={references.get('handoff_ref', '-')} "
        f"readiness_ref={references.get('readiness_ref', '-')} "
        f"remote_mutation_allowed={checks.get('remote_mutation_allowed', False)} "
        f"services_started={boundaries.get('scheduler_starts_external_services', False)}"
    )


def main() -> int:
    args = parse_args()
    command = _command_from_args(args)
    if command.execute:
        result = run_production_prototype_smoke(command, _subprocess_executor(command.repo_root))
    else:
        result = plan_production_prototype_smoke(command)
    payload = result.to_mapping()
    if args.output:
        _atomic_write_json(Path(args.output), payload)
    if args.format == "summary":
        print(_summary(payload))
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
