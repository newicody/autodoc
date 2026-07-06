#!/usr/bin/env python3
"""Perform a controlled real write through DbApiSqlContextStore.upsert_record.

0151 consumes the 0149 SQLContextStore persistence record and writes it through
DbApiSqlContextStore using a DB-API SQLite smoke database.  The write path is the
existing SQL context store authority boundary; this tool does not create a SQL
worker, does not import OpenVINO/Qdrant backends, and does not modify Scheduler
or RouteProxy runtime behavior.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Mapping, Sequence


def _ensure_context_import_path(root: Path) -> None:
    src = str(root / "src")
    if src not in sys.path:
        sys.path.insert(0, src)


def _resolve_repo_path(root: Path, path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return root / path


def _display_path(path: Path, *, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_json_mapping(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object in {path}")
    return loaded


@dataclass(frozen=True, slots=True)
class ExistingSurface:
    key: str
    path: Path
    required: bool
    reason: str

    def to_mapping(self, *, root: Path) -> dict[str, Any]:
        return {
            "key": self.key,
            "status": "present" if self.path.exists() else "missing",
            "required": self.required,
            "path": _display_path(self.path, root=root),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class SqlContextStoreControlledWritePlan:
    repository_root: Path
    persistence_json: Path
    output_dir: Path
    db_path: Path
    write_json: Path
    write_report: Path
    execute: bool
    surfaces: tuple[ExistingSurface, ...]

    @property
    def ready(self) -> bool:
        return all(not surface.required or surface.path.exists() for surface in self.surfaces)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "repository_root": str(self.repository_root),
            "persistence_json": str(self.persistence_json),
            "output_dir": str(self.output_dir),
            "db_path": str(self.db_path),
            "write_json": str(self.write_json),
            "write_report": str(self.write_report),
            "selected_store_class": "DbApiSqlContextStore",
            "selected_write_method": "upsert_record",
            "write_mode": "dbapi_sql_context_store_upsert_record",
            "ready_for_sql_context_store_controlled_write": self.ready,
            "execute": self.execute,
            "surfaces": [surface.to_mapping(root=self.repository_root) for surface in self.surfaces],
            "boundary": [
                "consumes sql_context_store_persistence_record.json from 0149",
                "uses DbApiSqlContextStore.upsert_record from src/context/sql_context_store.py",
                "builds an existing SqlContextRecord before writing",
                "uses a DB-API SQLite smoke database injected into DbApiSqlContextStore",
                "writes sql_context_store_controlled_write_result.json and report markdown",
                "does not create a SQL worker or SQL orchestrator",
                "does not import OpenVINO or Qdrant backends",
                "does not modify the Scheduler run loop",
                "Qdrant identifiers remain projection metadata; SQL remains durable authority",
            ],
        }

    def to_markdown(self) -> str:
        mapping = self.to_mapping()
        lines = [
            "# SQLContextStore controlled write smoke plan",
            "",
            f"repository_root: `{mapping['repository_root']}`",
            f"persistence_json: `{mapping['persistence_json']}`",
            f"output_dir: `{mapping['output_dir']}`",
            f"db_path: `{mapping['db_path']}`",
            f"write_json: `{mapping['write_json']}`",
            f"write_report: `{mapping['write_report']}`",
            f"selected_store_class: `{mapping['selected_store_class']}`",
            f"selected_write_method: `{mapping['selected_write_method']}`",
            f"write_mode: `{mapping['write_mode']}`",
            f"ready_for_sql_context_store_controlled_write: `{str(mapping['ready_for_sql_context_store_controlled_write']).lower()}`",
            f"execute: `{str(self.execute).lower()}`",
            "",
            "## Existing surfaces",
            "",
            "| key | status | required | path | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
        for surface in mapping["surfaces"]:
            lines.append(
                f"| {surface['key']} | {surface['status']} | `{str(surface['required']).lower()}` | "
                f"`{surface['path']}` | {surface['reason']} |"
            )
        lines.extend(["", "## Boundary", ""])
        lines.extend(f"- {item}" for item in mapping["boundary"])
        return "\n".join(lines) + "\n"


def build_sql_context_store_controlled_write_plan(
    repository_root: str | Path,
    *,
    persistence_json: str | Path = ".var/smoke/artifacts/0149/sql_context_store_persistence_record.json",
    output_dir: str | Path = ".var/smoke/artifacts/0151",
    db_path: str | Path | None = None,
    execute: bool = False,
) -> SqlContextStoreControlledWritePlan:
    root = Path(repository_root).resolve()
    persistence_path = _resolve_repo_path(root, Path(persistence_json)).resolve()
    out = _resolve_repo_path(root, Path(output_dir)).resolve()
    database = _resolve_repo_path(root, Path(db_path)).resolve() if db_path is not None else out / "sql_context_store.sqlite3"
    return SqlContextStoreControlledWritePlan(
        repository_root=root,
        persistence_json=persistence_path,
        output_dir=out,
        db_path=database,
        write_json=out / "sql_context_store_controlled_write_result.json",
        write_report=out / "sql_context_store_controlled_write_report.md",
        execute=execute,
        surfaces=(
            ExistingSurface(
                "sql_context_store",
                root / "src" / "context" / "sql_context_store.py",
                True,
                "existing durable SQL authority with DbApiSqlContextStore.upsert_record",
            ),
            ExistingSurface(
                "sql_context_store_controlled_write_contract",
                root / "src" / "context" / "sql_context_store_controlled_write_contract.py",
                True,
                "pure 0151 mapping from persistence record to SqlContextRecord",
            ),
            ExistingSurface(
                "sql_context_store_persistence_record",
                persistence_path,
                True,
                "record produced by 0149",
            ),
        ),
    )


def execute_sql_context_store_controlled_write_plan(plan: SqlContextStoreControlledWritePlan) -> int:
    if not plan.ready:
        return 2
    _ensure_context_import_path(plan.repository_root)

    from context.sql_context_store import DbApiSqlContextStore  # noqa: WPS433 - existing boundary import
    from context.sql_context_store_controlled_write_contract import (  # noqa: WPS433
        SqlContextStoreControlledWriteSummary,
        build_sql_context_record_from_persistence_mapping,
    )

    persistence = _read_json_mapping(plan.persistence_json)
    record = build_sql_context_record_from_persistence_mapping(persistence)
    plan.output_dir.mkdir(parents=True, exist_ok=True)
    plan.db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(plan.db_path))
    try:
        store = DbApiSqlContextStore(connection)
        store.initialize_schema()
        write_result = store.upsert_record(record)
        readback = store.get_record(record.context_ref)
    finally:
        connection.close()

    summary = SqlContextStoreControlledWriteSummary.from_write_result(
        persistence_mapping=persistence,
        write_result=write_result,
        db_path=str(plan.db_path),
        readback_ok=readback is not None and readback.context_ref == record.context_ref,
    )
    mapping = summary.to_mapping()
    plan.write_json.write_text(json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    plan.write_report.write_text(_write_report_markdown(plan=plan, result=mapping), encoding="utf-8")

    print("==> sql_context_store_controlled_write")
    print(_result_markdown(plan=plan, result=mapping), end="")
    return 0 if mapping["readback_ok"] else 1


def _write_report_markdown(*, plan: SqlContextStoreControlledWritePlan, result: Mapping[str, Any]) -> str:
    lines = [
        "# SQLContextStore controlled write report",
        "",
        f"write_status: `{result.get('write_status')}`",
        f"readback_ok: `{str(result.get('readback_ok')).lower()}`",
        f"sql_ref: `{result.get('sql_ref')}`",
        f"artifact_ref: `{result.get('artifact_ref')}`",
        f"db_path: `{plan.db_path}`",
        f"selected_store_class: `{result.get('selected_store_class')}`",
        f"selected_write_method: `{result.get('selected_write_method')}`",
        f"inserted: `{str(result.get('inserted')).lower()}`",
        f"replaced: `{str(result.get('replaced')).lower()}`",
        f"point_id: `{result.get('point_id')}`",
        f"qdrant_rest_id: `{result.get('qdrant_rest_id')}`",
        "",
        "Boundary: SQL is the durable authority; Qdrant identifiers are metadata for projection/recall.",
    ]
    return "\n".join(lines) + "\n"


def _result_markdown(*, plan: SqlContextStoreControlledWritePlan, result: Mapping[str, Any]) -> str:
    lines = [
        "# SQLContextStore controlled write smoke result",
        "",
        f"write_json: `{plan.write_json}`",
        f"write_report: `{plan.write_report}`",
        f"db_path: `{plan.db_path}`",
        f"write_status: `{result.get('write_status')}`",
        f"readback_ok: `{str(result.get('readback_ok')).lower()}`",
        f"selected_store_class: `{result.get('selected_store_class')}`",
        f"selected_write_method: `{result.get('selected_write_method')}`",
        f"write_mode: `{result.get('write_mode')}`",
        f"sql_ref: `{result.get('sql_ref')}`",
        f"artifact_ref: `{result.get('artifact_ref')}`",
        f"inserted: `{str(result.get('inserted')).lower()}`",
        f"replaced: `{str(result.get('replaced')).lower()}`",
        f"point_id: `{result.get('point_id')}`",
        f"qdrant_rest_id: `{result.get('qdrant_rest_id')}`",
        f"durable_authority: `{result.get('durable_authority')}`",
        f"qdrant_role: `{result.get('qdrant_role')}`",
        "boundary: `DbApiSqlContextStore.upsert_record real DB-API write with readback`",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository_root")
    parser.add_argument(
        "--persistence-json",
        default=".var/smoke/artifacts/0149/sql_context_store_persistence_record.json",
        help="0149 SQLContextStore persistence record JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default=".var/smoke/artifacts/0151",
        help="Directory for 0151 output artifacts.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="SQLite smoke database path injected into DbApiSqlContextStore.",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    plan = build_sql_context_store_controlled_write_plan(
        args.repository_root,
        persistence_json=args.persistence_json,
        output_dir=args.output_dir,
        db_path=args.db_path,
        execute=args.execute,
    )
    if args.format == "json":
        print(json.dumps(plan.to_mapping(), indent=2, sort_keys=True))
    else:
        print(plan.to_markdown(), end="")
    if not args.execute:
        return 0 if plan.ready else 2
    return execute_sql_context_store_controlled_write_plan(plan)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
