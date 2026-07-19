#!/usr/bin/env python3
"""Persist one typed GitHub research command in relational PostgreSQL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_research_scheduler_command_0287 import (  # noqa: E402
    ResearchExecutionBudget,
    build_typed_github_research_scheduler_command,
)
from context.love_manual_runtime_configuration_0287 import (  # noqa: E402
    load_manual_installed_runtime_settings,
)
from context.love_postgresql_authority_binding_0287 import (  # noqa: E402
    open_love_postgresql_authority,
)

REPORT_SCHEMA = "missipy.github.research_scheduler_command_sql_persist.v1"


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input report must contain a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one typed GitHub research command and, only with "
            "--execute, persist it in normalized PostgreSQL tables."
        )
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--runtime-config", required=True)
    parser.add_argument("--max-scheduler-steps", required=True, type=int)
    parser.add_argument("--max-specialist-visits", required=True, type=int)
    parser.add_argument("--max-wall-time-s", required=True, type=float)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)

    build = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_load_mapping(Path(args.input)),
        execution_budget=ResearchExecutionBudget(
            max_scheduler_steps=args.max_scheduler_steps,
            max_specialist_visits=args.max_specialist_visits,
            max_wall_time_s=args.max_wall_time_s,
        ),
    )
    command = build.command
    if not build.valid or command is None:
        report: dict[str, object] = {
            "schema": REPORT_SCHEMA,
            "valid": False,
            "mode": "execute" if args.execute else "dry-run",
            "status": "typed-command-invalid",
            "issues": list(build.issues),
            "command_ref": "",
            "command_digest": "",
            "inserted": False,
            "idempotent_replay": False,
            "state": "",
            "boundaries": _boundaries(
                sql_authority_accessed=False,
                sql_write_performed=False,
            ),
        }
        _emit(report, args.format)
        return 2

    if not args.execute:
        report = {
            "schema": REPORT_SCHEMA,
            "valid": True,
            "mode": "dry-run",
            "status": "typed-command-ready-for-sql",
            "issues": [],
            "command_ref": command.command_ref,
            "command_digest": command.command_digest,
            "inserted": False,
            "idempotent_replay": False,
            "state": "",
            "boundaries": _boundaries(
                sql_authority_accessed=False,
                sql_write_performed=False,
            ),
        }
        _emit(report, args.format)
        return 0

    settings = load_manual_installed_runtime_settings(args.runtime_config)
    binding = open_love_postgresql_authority(settings)
    try:
        command_store = binding.scheduler_command_store
        if command_store is None:
            raise RuntimeError(
                "installed PostgreSQL binding has no Scheduler command store"
            )
        write = command_store.put_command(command)
        state = command_store.get_state(command.command_ref)
        report = {
            "schema": REPORT_SCHEMA,
            "valid": True,
            "mode": "execute",
            "status": (
                "scheduler-command-persisted"
                if write.inserted
                else "scheduler-command-already-persisted"
            ),
            "issues": [],
            "command_ref": write.command_ref,
            "command_digest": write.command_digest,
            "authority_ref": write.authority_ref,
            "inserted": write.inserted,
            "idempotent_replay": write.idempotent_replay,
            "state": state.state if state is not None else "",
            "state_version": state.state_version if state is not None else 0,
            "boundaries": _boundaries(
                sql_authority_accessed=True,
                sql_write_performed=write.inserted,
            ),
        }
    finally:
        binding.close()

    _emit(report, args.format)
    return 0


def _boundaries(
    *,
    sql_authority_accessed: bool,
    sql_write_performed: bool,
) -> dict[str, bool]:
    return {
        "typed_command_used": True,
        "postgresql_authority_used": sql_authority_accessed,
        "relational_tables_used": sql_authority_accessed,
        "json_storage_used": False,
        "filesystem_queue_used": False,
        "scheduler_started": False,
        "dispatcher_called": False,
        "eventbus_used": False,
        "laboratory_execution_started": False,
        "qdrant_write_performed": False,
        "github_mutation_performed": False,
        "sql_write_performed": sql_write_performed,
    }


def _emit(report: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(
        " ".join(
            (
                f"valid={str(bool(report['valid'])).lower()}",
                f"mode={report['mode']}",
                f"status={report['status']}",
                f"command_ref={report['command_ref']}",
                f"command_digest={report['command_digest']}",
                f"inserted={str(bool(report['inserted'])).lower()}",
                "idempotent_replay="
                f"{str(bool(report['idempotent_replay'])).lower()}",
                f"state={report['state']}",
            )
        )
    )
    for issue in report.get("issues", ()):  # type: ignore[union-attr]
        print(f"issue: {issue}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
