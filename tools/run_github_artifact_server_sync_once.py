#!/usr/bin/env python3
"""Synchronize a downloaded GitHub Actions artifact into the server dataset.

This is a server-side sync step. It expects a local artifact directory that was
already fetched from GitHub Actions. It writes raw data to the configured server
dataset, emits an index/history record, emits a VisPy observation event, and
queues conversion only after raw sync is complete.

No GitHub API call is performed here.
"""

from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Mapping, Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


from context.github_artifact_server_dataset import (
    ServerDatasetLayout,  # noqa: E402
    AttachmentRecord,
    ConversionQueueRecord,
    GitHubFetchedArtifactRecord,
    ServerDatasetSyncReport,
    build_conversion_queue_ref,
    build_raw_dataset_ref,
    hash_file,
    infer_attachment_kind,
)
from context.github_artifact_server_fetch_config import load_github_artifact_server_fetch_config  # noqa: E402


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync one local GitHub Actions artifact directory into the configured server dataset.")
    parser.add_argument("--config", type=Path, default=Path("config/github_artifact_server_fetch.example.ini"))
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--repository", default="")
    parser.add_argument("--run-id", default="local-run")
    parser.add_argument("--artifact-id", default="local-artifact")
    parser.add_argument("--artifact-name", default="autodoc-ticket-artifact-local")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = load_github_artifact_server_fetch_config(args.config)
    repository = args.repository or config.external_repository
    if repository not in config.allowed_repositories:
        raise SystemExit(f"repository not allowed: {repository}")

    report = sync_artifact_directory(
        artifact_dir=args.artifact_dir,
        repository=repository,
        run_id=args.run_id,
        artifact_id=args.artifact_id,
        artifact_name=args.artifact_name,
        config_path=args.config,
    )

    if args.format == "json":
        print(json.dumps(report.to_json_dict(), indent=2, sort_keys=True))
    else:
        payload = report.to_json_dict()
        print(f"status: {payload['status']}")
        print(f"origin_frame_id: {payload['origin_frame_id']}")
        print(f"attachment_count: {payload['counts']['attachment_count']}")
        print(f"queued_count: {payload['counts']['queued_count']}")
    return 0 if report.status == "ok" else 1


def sync_artifact_directory(
    *,
    artifact_dir: Path,
    repository: str,
    run_id: str,
    artifact_id: str,
    artifact_name: str,
    config_path: Path,
) -> ServerDatasetSyncReport:
    config = load_github_artifact_server_fetch_config(config_path)
    bundle_path = artifact_dir / "artifact_bundle.json"
    bundle = _read_json(bundle_path) if bundle_path.exists() else {}
    origin_frame_id = str(bundle.get("origin_frame_id", f"github-frame:{repository}/unknown"))
    ticket_revision_id = str(bundle.get("ticket_revision_id", "github-ticket-revision:unknown"))

    dataset = config.dataset
    raw_root = dataset.raw_path / repository.replace("/", "__") / run_id / artifact_id
    raw_root.mkdir(parents=True, exist_ok=True)
    dataset.index_path.mkdir(parents=True, exist_ok=True)
    dataset.history_path.mkdir(parents=True, exist_ok=True)
    dataset.conversion_queue_path.mkdir(parents=True, exist_ok=True)
    dataset.vispy_events_path.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    attachment_records: list[AttachmentRecord] = []
    queue_records: list[ConversionQueueRecord] = []
    total_bytes = 0

    for source in sorted(path for path in artifact_dir.rglob("*") if path.is_file()):
        relative = source.relative_to(artifact_dir)
        target = raw_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_files.append(str(relative))
        size = target.stat().st_size
        total_bytes += size
        digest = hash_file(target)
        raw_ref = build_raw_dataset_ref(repository, run_id, artifact_id, str(relative))

        if _is_attachment_relative(relative):
            kind = infer_attachment_kind(target)
            attachment = AttachmentRecord(
                filename=target.name,
                kind=kind,
                source="github_actions_artifact",
                raw_dataset_ref=raw_ref,
                sha256=digest,
                byte_count=size,
                processed=False,
            )
            attachment_records.append(attachment)
            if config.queue_after_complete_sync and kind in config.allowed_attachment_kinds:
                queue_ref = build_conversion_queue_ref(raw_ref, digest)
                queue_record = ConversionQueueRecord(
                    queue_ref=queue_ref,
                    origin_frame_id=origin_frame_id,
                    ticket_revision_id=ticket_revision_id,
                    raw_dataset_ref=raw_ref,
                    kind=kind,
                    sha256=digest,
                )
                queue_records.append(queue_record)

    artifact_sha = _hash_directory(raw_root)
    artifact_record = GitHubFetchedArtifactRecord(
        repository=repository,
        artifact_name=artifact_name,
        artifact_id=artifact_id,
        run_id=run_id,
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        raw_dataset_ref=build_raw_dataset_ref(repository, run_id, artifact_id, "."),
        sha256=artifact_sha,
        byte_count=total_bytes,
        files=tuple(copied_files),
        status="synced",
    )

    index_path = dataset.index_path / f"{run_id}-{artifact_id}.json"
    queue_path = dataset.conversion_queue_path / f"{run_id}-{artifact_id}.jsonl"
    history_path = dataset.history_path / "fetch_history.jsonl"
    vispy_path = dataset.vispy_events_path / f"{run_id}-{artifact_id}.json"

    report = ServerDatasetSyncReport(
        repository=repository,
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        artifact_record=artifact_record,
        attachments=tuple(attachment_records),
        queue_records=tuple(queue_records),
        vispy_event_path=str(vispy_path),
        status="ok",
    )

    _write_json(index_path, report.to_json_dict())
    _append_jsonl(history_path, report.to_json_dict())
    _write_json(vispy_path, _build_vispy_event(report))
    _write_jsonl(queue_path, [record.to_json_dict() for record in queue_records])
    _write_json(dataset.state_path, {"last_sync": report.to_json_dict()})
    return report



def _layout_from_config(config: object) -> ServerDatasetLayout:
    dataset = getattr(config, "dataset", None)
    if dataset is None:
        dataset = getattr(config, "dataset_layout", None)

    def value(*names: str, default: str) -> str:
        for name in names:
            if dataset is not None and hasattr(dataset, name):
                candidate = getattr(dataset, name)
                if candidate:
                    return str(candidate)
            if hasattr(config, name):
                candidate = getattr(config, name)
                if candidate:
                    return str(candidate)
        return default

    root = value("root", "dataset_root", default=".var/server_datasets/github_artifacts")
    return ServerDatasetLayout(
        root=Path(root),
        raw_dir=value("raw_dir", default="raw"),
        index_dir=value("index_dir", default="index"),
        history_dir=value("history_dir", default="history"),
        conversion_queue_dir=value("conversion_queue_dir", default="conversion_queue"),
        converted_dir=value("converted_dir", default="converted"),
        vispy_events_dir=value("vispy_events_dir", default="vispy_events"),
    )


def _dataset_layout_from_config_path(config_path: Path) -> ServerDatasetLayout:
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    dataset = parser["dataset"] if parser.has_section("dataset") else {}

    root = dataset.get("root") or dataset.get("dataset_root") or ".var/server_datasets/github_artifacts"

    return ServerDatasetLayout(
        root=Path(root),
        raw_dir=dataset.get("raw_dir", "raw"),
        index_dir=dataset.get("index_dir", "index"),
        history_dir=dataset.get("history_dir", "history"),
        conversion_queue_dir=dataset.get("conversion_queue_dir", "conversion_queue"),
        converted_dir=dataset.get("converted_dir", "converted"),
        vispy_events_dir=dataset.get("vispy_events_dir", "vispy_events"),
    )


def _read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _write_jsonl(path: Path, payloads: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _is_attachment_relative(relative: Path) -> bool:
    return len(relative.parts) >= 2 and relative.parts[0] == "attachments"


def _hash_directory(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(str(item.relative_to(path)).encode("utf-8"))
        digest.update(b"\0")
        with item.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _build_vispy_event(report: ServerDatasetSyncReport) -> dict[str, Any]:
    payload = report.to_json_dict()
    return {
        "schema": "missipy.vispy.github_artifact_fetch_event.v1",
        "event_kind": "github_artifact_dataset_sync",
        "origin_frame_id": payload["origin_frame_id"],
        "ticket_revision_id": payload["ticket_revision_id"],
        "counts": payload["counts"],
        "status": payload["status"],
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
