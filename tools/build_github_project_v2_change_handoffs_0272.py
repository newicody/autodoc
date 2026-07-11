#!/usr/bin/env python3
"""Build local SourceCandidate handoffs from a ProjectV2 change set."""
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_v2_change_handoff_0272 import (  # noqa: E402
    GitHubProjectV2ChangeHandoffCommand,
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
    build_change_handoff_plan,
    close_change_handoff_result,
)

_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")
_DEFAULT_OUTPUT = Path(".var/reports/github_project_v2_change_handoff_0272.json")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--change-set", type=Path, default=None)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--max-handoffs", type=int, default=None)
    parser.add_argument("--include-baseline", action="store_true")
    parser.add_argument("--exclude-removed", action="store_true")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = _load_config(args.config)
    change_set_path, selection_errors = _select_change_set(
        explicit=args.change_set,
        change_set_dir=config["change_set_dir"],
    )
    policy = GitHubProjectV2ChangeHandoffPolicy(
        include_added=True,
        include_changed=True,
        include_removed=(
            False if args.exclude_removed else bool(config["include_removed"])
        ),
        include_baseline=(
            True if args.include_baseline else bool(config["include_baseline"])
        ),
        max_handoffs=(
            args.max_handoffs
            if args.max_handoffs is not None
            else int(config["max_handoffs"])
        ),
    )
    command = GitHubProjectV2ChangeHandoffCommand(
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
    )
    plan = build_change_handoff_plan(
        command,
        change_set_path=str(change_set_path or ""),
        policy=policy,
    )
    handoff_batch: Mapping[str, Any] | None = None
    handoff_batch_path = ""
    errors = list(selection_errors)
    if args.execute and plan.valid and not errors:
        try:
            change_set = _read_json(change_set_path)
            handoff_batch = build_change_handoff_batch(
                change_set=change_set,
                policy=policy,
            )
            handoff_batch_path = str(
                _write_immutable_handoff_batch(
                    Path(config["handoff_dir"]),
                    handoff_batch,
                )
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
    result = close_change_handoff_result(
        plan,
        handoff_batch=handoff_batch,
        handoff_batch_path=handoff_batch_path,
        errors=errors,
    )
    payload = result.to_json_dict()
    _write_json_atomic(args.output, payload)
    print(
        json.dumps(payload, indent=2, sort_keys=True)
        if args.format == "json"
        else result.to_summary()
    )
    return 0 if result.valid else 2


def _load_config(path: Path) -> dict[str, object]:
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path, encoding="utf-8"):
        raise ValueError(f"config not found: {path}")
    section = parser["change_handoff"]
    return {
        "change_set_dir": _repo_path(
            section.get("change_set_dir", ".var/github/project_v2/changes")
        ),
        "handoff_dir": _repo_path(
            section.get("handoff_dir", ".var/github/project_v2/handoffs")
        ),
        "max_handoffs": section.getint("max_handoffs", fallback=100),
        "include_removed": section.getboolean("include_removed", fallback=True),
        "include_baseline": section.getboolean("include_baseline", fallback=False),
    }


def _select_change_set(
    *,
    explicit: Path | None,
    change_set_dir: object,
) -> tuple[Path | None, tuple[str, ...]]:
    if explicit is not None:
        return explicit, ()
    directory = Path(change_set_dir)
    if not directory.exists():
        return None, (f"change-set directory not found: {directory}",)
    candidates = [
        path
        for path in directory.glob("project-v2-change-set-*.json")
        if path.is_file()
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime_ns, path.name))
    if not candidates:
        return None, (f"no ProjectV2 change sets found in {directory}",)
    return candidates[-1], ()


def _read_json(path: Path | None) -> Mapping[str, Any]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"change set must be a JSON object: {path}")
    return payload


def _write_immutable_handoff_batch(
    output_dir: Path,
    payload: Mapping[str, Any],
) -> Path:
    handoff_batch_ref = str(payload.get("handoff_batch_ref", ""))
    digest = handoff_batch_ref.rsplit(":", 1)[-1]
    if not digest:
        raise ValueError("handoff_batch_ref missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"project-v2-handoff-batch-{digest}.json"
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"immutable handoff-batch collision: {path}")
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


def _repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else _REPO_ROOT / path


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
