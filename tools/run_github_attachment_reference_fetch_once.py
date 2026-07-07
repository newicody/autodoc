#!/usr/bin/env python3
"""Fetch GitHub issue attachment references into the configured server dataset.

0171 runs after GitHub Actions artifacts have been fetched. It reads an
attachment manifest, resolves each reference, writes raw bytes to the server
 dataset, and emits conversion queue records only for successfully fetched files.
"""

from __future__ import annotations

import argparse
import configparser
from dataclasses import dataclass
from pathlib import Path
import json
import os
import sys
from typing import Any, Mapping, Sequence
import urllib.request

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_attachment_reference_fetch import (  # noqa: E402
    GitHubAttachmentConversionQueueRecord,
    GitHubAttachmentFetchRecord,
    GitHubAttachmentReference,
    GitHubAttachmentReferenceFetchReport,
    build_attachment_raw_dataset_ref,
    extract_attachment_references,
    sha256_bytes,
)


@dataclass(frozen=True)
class DatasetPaths:
    root: Path
    raw_dir: str
    index_dir: str
    history_dir: str
    conversion_queue_dir: str
    vispy_events_dir: str

    @property
    def raw_path(self) -> Path:
        return self.root / self.raw_dir

    @property
    def index_path(self) -> Path:
        return self.root / self.index_dir

    @property
    def history_path(self) -> Path:
        return self.root / self.history_dir

    @property
    def conversion_queue_path(self) -> Path:
        return self.root / self.conversion_queue_dir

    @property
    def vispy_events_path(self) -> Path:
        return self.root / self.vispy_events_dir


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch attachment references from a local GitHub Actions artifact manifest into the server dataset.")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--repository", default="")
    parser.add_argument("--attachment-fixture-root", type=Path, default=None)
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    dataset = _load_dataset_paths(args.config)
    manifest_path = args.manifest or args.artifact_dir / "attachment_manifest.json"
    manifest = _read_json(manifest_path)
    artifact_bundle = _read_optional_json(args.artifact_dir / "artifact_bundle.json")

    repository = args.repository or _repository_from_manifest(manifest, artifact_bundle)
    origin_frame_id = str(manifest.get("origin_frame_id") or artifact_bundle.get("origin_frame_id") or "")
    ticket_revision_id = str(manifest.get("ticket_revision_id") or artifact_bundle.get("ticket_revision_id") or "")
    references = extract_attachment_references(manifest)

    raw_attachment_root = dataset.raw_path / repository.replace("/", "__") / args.run_id / args.artifact_id / "attachments"
    dataset.index_path.mkdir(parents=True, exist_ok=True)
    dataset.history_path.mkdir(parents=True, exist_ok=True)
    dataset.conversion_queue_path.mkdir(parents=True, exist_ok=True)
    dataset.vispy_events_path.mkdir(parents=True, exist_ok=True)
    raw_attachment_root.mkdir(parents=True, exist_ok=True)

    records: list[GitHubAttachmentFetchRecord] = []
    queue_records: list[GitHubAttachmentConversionQueueRecord] = []
    used_names: set[str] = set()

    for reference in references:
        target_name = _unique_name(reference.filename, used_names)
        target_path = raw_attachment_root / target_name
        raw_ref = build_attachment_raw_dataset_ref(repository, args.run_id, args.artifact_id, target_name)
        status = "fetched"
        message = ""
        content = b""
        try:
            content = _resolve_reference_bytes(reference, args.attachment_fixture_root, args.allow_network)
            target_path.write_bytes(content)
            digest = sha256_bytes(content)
            if reference.expected_sha256 and reference.expected_sha256 != digest:
                status = "hash_mismatch"
                message = "expected sha256 does not match fetched bytes"
        except Exception as exc:  # noqa: BLE001 - report the fetch failure in dataset index.
            status = "failed"
            message = str(exc)
            digest = ""

        record = GitHubAttachmentFetchRecord(
            reference=reference,
            repository=repository,
            run_id=args.run_id,
            artifact_id=args.artifact_id,
            origin_frame_id=origin_frame_id,
            ticket_revision_id=ticket_revision_id,
            raw_dataset_ref=raw_ref,
            local_path=str(target_path),
            sha256=digest,
            byte_count=len(content),
            status=status,
            message=message,
        )
        records.append(record)
        if status == "fetched":
            queue_records.append(
                GitHubAttachmentConversionQueueRecord(
                    raw_dataset_ref=raw_ref,
                    sha256=digest,
                    kind=reference.kind,
                    origin_frame_id=origin_frame_id,
                    ticket_revision_id=ticket_revision_id,
                )
            )

    status = "ok" if len(queue_records) == len(records) else "partial"
    if not records:
        status = "empty"
    vispy_path = dataset.vispy_events_path / f"{args.run_id}-{args.artifact_id}-attachments.json"
    report = GitHubAttachmentReferenceFetchReport(
        repository=repository,
        run_id=args.run_id,
        artifact_id=args.artifact_id,
        origin_frame_id=origin_frame_id,
        ticket_revision_id=ticket_revision_id,
        records=tuple(records),
        queue_records=tuple(queue_records),
        vispy_event_path=str(vispy_path),
        status=status,
    )
    payload = report.to_json_dict()
    _write_json(dataset.index_path / f"{args.run_id}-{args.artifact_id}-attachment-fetch.json", payload)
    _write_json(vispy_path, _vispy_payload(payload))
    _append_jsonl(dataset.history_path / "attachment_fetch_history.jsonl", payload)
    _write_jsonl(dataset.conversion_queue_path / f"{args.run_id}-{args.artifact_id}-attachments.jsonl", [record.to_json_dict() for record in queue_records])

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"status: {status}")
        print(f"references: {len(records)}")
        print(f"queued: {len(queue_records)}")
        print(f"vispy_event_path: {vispy_path}")
    return 0 if status in {"ok", "empty"} else 2


def _load_dataset_paths(config_path: Path) -> DatasetPaths:
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    section = parser["server_dataset"] if parser.has_section("server_dataset") else parser["dataset"]
    return DatasetPaths(
        root=Path(section.get("root") or section.get("dataset_root") or ".var/server_datasets/github_artifacts").expanduser(),
        raw_dir=section.get("raw_dir", "raw"),
        index_dir=section.get("index_dir", "index"),
        history_dir=section.get("history_dir", "history"),
        conversion_queue_dir=section.get("conversion_queue_dir", "conversion_queue"),
        vispy_events_dir=section.get("vispy_events_dir", "vispy_events"),
    )


def _resolve_reference_bytes(reference: GitHubAttachmentReference, fixture_root: Path | None, allow_network: bool) -> bytes:
    if fixture_root is not None:
        candidates = [fixture_root / reference.filename]
        if reference.url:
            candidates.append(fixture_root / Path(reference.url.split("?", 1)[0].rstrip("/")).name)
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.read_bytes()
        raise FileNotFoundError(f"fixture attachment not found for {reference.filename}")

    if reference.url.startswith("file://"):
        return Path(reference.url.removeprefix("file://")).read_bytes()

    if not allow_network:
        raise RuntimeError("network fetch disabled; use --attachment-fixture-root or --allow-network")

    request = urllib.request.Request(reference.url, headers=_headers())
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - explicit opt-in read-only fetch.
        return response.read()


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "autodoc-attachment-fetch/0171"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _repository_from_manifest(manifest: Mapping[str, Any], artifact_bundle: Mapping[str, Any]) -> str:
    for payload in (manifest, artifact_bundle):
        value = payload.get("repository")
        if isinstance(value, str) and value:
            return value
    origin = str(manifest.get("origin_frame_id") or artifact_bundle.get("origin_frame_id") or "")
    marker = "github-frame:"
    if origin.startswith(marker):
        parts = origin.removeprefix(marker).split("/")
        if len(parts) >= 2:
            return f"{parts[0]}/{parts[1]}"
    return "unknown/unknown"


def _unique_name(filename: str, used: set[str]) -> str:
    path = Path(filename)
    stem = path.stem or "attachment"
    suffix = path.suffix
    candidate = path.name
    index = 2
    while candidate in used:
        candidate = f"{stem}-{index}{suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _read_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _write_jsonl(path: Path, payloads: list[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")


def _vispy_payload(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_kind": "github_attachment_reference_fetch",
        "status": report["status"],
        "repository": report["repository"],
        "run_id": report["run_id"],
        "artifact_id": report["artifact_id"],
        "counts": report["counts"],
        "origin_frame_id": report["origin_frame_id"],
        "ticket_revision_id": report["ticket_revision_id"],
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
