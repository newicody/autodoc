#!/usr/bin/env python3
"""Consume one approved ProjectV2 gate record into the existing SQL authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_v2_source_candidate_durable_consumer_0272 import (  # noqa: E402
    GitHubProjectV2DurableConsumerCommand,
    build_durable_consumer_plan,
    close_durable_consumer_result,
    consume_approved_gate_record,
)
from context.scheduler_managed_db_api_sql_context_store_binding_0260 import (  # noqa: E402
    build_db_api_sql_context_store_binding_report,
)

_DEFAULT_DB_PATH = Path(".var/local/sql_context_store.sqlite3")
_DEFAULT_OUTPUT = Path(
    ".var/reports/github_project_v2_source_candidate_durable_consumer_0272.json"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-record", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, default=_DEFAULT_DB_PATH)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    gate_path = _repo_path(args.gate_record)
    command = GitHubProjectV2DurableConsumerCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
    )
    plan = build_durable_consumer_plan(command, gate_record_path=str(gate_path))
    errors: list[str] = []
    result = None
    binding_payload: Mapping[str, Any] = {}

    if plan.valid:
        try:
            gate_record = _read_json(gate_path)
            store = None
            if args.execute:
                binding, store = build_db_api_sql_context_store_binding_report(
                    _REPO_ROOT,
                    db_path=_repo_path(args.db_path),
                    construct=True,
                )
                binding_payload = binding.to_dict()
                if binding.issues:
                    errors.extend(binding.issues)
            else:
                binding, _ = build_db_api_sql_context_store_binding_report(
                    _REPO_ROOT,
                    construct=False,
                )
                binding_payload = binding.to_dict()
            if not errors:
                result = consume_approved_gate_record(
                    gate_record,
                    command,
                    store=store,
                )
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")

    closed = close_durable_consumer_result(plan, result=result, errors=errors)
    payload = closed.to_json_dict()
    payload["binding"] = dict(binding_payload)
    _write_json_atomic(_repo_path(args.output), payload)
    print(
        json.dumps(payload, indent=2, sort_keys=True)
        if args.format == "json"
        else closed.to_summary()
    )
    return 0 if closed.valid else 2


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"gate record must be a JSON object: {path}")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _repo_path(value: Path) -> Path:
    path = value.expanduser()
    return path if path.is_absolute() else _REPO_ROOT / path


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
