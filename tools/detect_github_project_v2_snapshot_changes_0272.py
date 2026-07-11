#!/usr/bin/env python3
"""Compare immutable local ProjectV2 snapshots without contacting GitHub."""

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

from context.github_project_v2_snapshot_change_detection_0272 import (  # noqa: E402
    GitHubProjectV2SnapshotChangeCommand,
    build_snapshot_change_plan,
    build_snapshot_change_set,
    close_snapshot_change_result,
)

_DEFAULT_SNAPSHOT_DIR = Path(".var/github/project_v2/snapshots")
_DEFAULT_CHANGE_DIR = Path(".var/github/project_v2/changes")
_DEFAULT_REPORT = Path(
    ".var/reports/github_project_v2_snapshot_change_detection_0272.json"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare the newest immutable ProjectV2 snapshots locally."
    )
    parser.add_argument("--snapshot-dir", type=Path, default=_DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--previous-snapshot", type=Path, default=None)
    parser.add_argument("--current-snapshot", type=Path, default=None)
    parser.add_argument("--change-dir", type=Path, default=_DEFAULT_CHANGE_DIR)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--output", type=Path, default=_DEFAULT_REPORT)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    previous_path, current_path, selection_errors = _select_snapshot_paths(
        snapshot_dir=args.snapshot_dir,
        previous_snapshot=args.previous_snapshot,
        current_snapshot=args.current_snapshot,
    )
    command = GitHubProjectV2SnapshotChangeCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
    )
    plan = build_snapshot_change_plan(
        command,
        previous_snapshot_path=str(previous_path or ""),
        current_snapshot_path=str(current_path or ""),
    )
    change_set: Mapping[str, Any] | None = None
    change_set_path = ""
    errors = list(selection_errors)

    if args.execute and plan.valid and not errors:
        try:
            current = _read_json(current_path)
            previous = _read_json(previous_path) if previous_path is not None else None
            change_set = build_snapshot_change_set(
                previous_snapshot=previous,
                current_snapshot=current,
            )
            change_set_path = str(_write_immutable_change_set(args.change_dir, change_set))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")

    result = close_snapshot_change_result(
        plan,
        change_set=change_set,
        change_set_path=change_set_path,
        errors=errors,
    )
    payload = result.to_json_dict()
    _write_json_atomic(args.output, payload)
    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(result.to_summary())
    return 0 if result.valid else 2


def _select_snapshot_paths(
    *,
    snapshot_dir: Path,
    previous_snapshot: Path | None,
    current_snapshot: Path | None,
) -> tuple[Path | None, Path | None, list[str]]:
    issues: list[str] = []
    if previous_snapshot is not None and current_snapshot is None:
        issues.append("--previous-snapshot requires --current-snapshot")
        return previous_snapshot, current_snapshot, issues
    if current_snapshot is not None:
        return previous_snapshot, current_snapshot, issues
    if not snapshot_dir.exists():
        issues.append(f"snapshot directory not found: {snapshot_dir}")
        return None, None, issues
    candidates = [
        path
        for path in snapshot_dir.glob("project-v2-*.json")
        if path.is_file()
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime_ns, path.name))
    if not candidates:
        issues.append(f"no ProjectV2 snapshots found in {snapshot_dir}")
        return None, None, issues
    current = candidates[-1]
    previous = candidates[-2] if len(candidates) >= 2 else None
    return previous, current, issues


def _read_json(path: Path | None) -> Mapping[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"snapshot must be a JSON object: {path}")
    return payload


def _write_immutable_change_set(
    output_dir: Path,
    payload: Mapping[str, Any],
) -> Path:
    change_set_ref = str(payload.get("change_set_ref", ""))
    digest = change_set_ref.rsplit(":", 1)[-1]
    if not digest:
        raise ValueError("change_set_ref missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"project-v2-change-set-{digest}.json"
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"immutable change-set collision: {path}")
        return path
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    return path


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
