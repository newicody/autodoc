from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_external_probe_artifact_index import (
    build_source_candidate_external_probe_artifact_index,
    read_source_candidate_external_probe_artifact_index,
    render_source_candidate_external_probe_artifact_index,
    write_source_candidate_external_probe_artifact_index,
)


def _write_bundle(path: Path, *, repository: str = "newicody/autodoc", allowed: bool = True) -> None:
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "missipy.source_candidate.external_probe_bundle.v1",
                "path": str(path),
                "manifest_path": str(path / "manifest.json"),
                "repository": repository,
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": allowed,
                "artifact_count": 3,
                "byte_count": 123,
                "artifacts": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_external_probe_artifact_index_discovers_bundle_manifests(tmp_path: Path) -> None:
    scan_root = tmp_path / "bundles"
    _write_bundle(scan_root / "one")
    _write_bundle(scan_root / "two", repository="newicody/other", allowed=False)

    index = build_source_candidate_external_probe_artifact_index(
        tmp_path,
        scan_root=scan_root,
    )

    assert index.bundle_count == 2
    assert index.total_artifact_count == 6
    assert index.total_byte_count == 246
    assert {entry.repository for entry in index.entries} == {"newicody/autodoc", "newicody/other"}


def test_external_probe_artifact_index_ignores_non_bundle_manifests(tmp_path: Path) -> None:
    scan_root = tmp_path / "bundles"
    _write_bundle(scan_root / "valid")
    invalid = scan_root / "invalid"
    invalid.mkdir(parents=True)
    (invalid / "manifest.json").write_text(
        json.dumps({"schema": "other.schema"}) + "\n",
        encoding="utf-8",
    )

    index = build_source_candidate_external_probe_artifact_index(
        tmp_path,
        scan_root=scan_root,
    )

    assert index.bundle_count == 1
    assert index.entries[0].repository == "newicody/autodoc"


def test_external_probe_artifact_index_writes_and_reads_json(tmp_path: Path) -> None:
    scan_root = tmp_path / "bundles"
    output = tmp_path / "index.json"
    _write_bundle(scan_root / "one")

    index = build_source_candidate_external_probe_artifact_index(
        tmp_path,
        scan_root=scan_root,
    )
    returned = write_source_candidate_external_probe_artifact_index(output, index)
    payload = read_source_candidate_external_probe_artifact_index(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.external_probe_artifact_index.v1"
    assert payload["bundle_count"] == 1


def test_external_probe_artifact_index_render_is_stable(tmp_path: Path) -> None:
    scan_root = tmp_path / "bundles"
    _write_bundle(scan_root / "one")

    text = render_source_candidate_external_probe_artifact_index(
        build_source_candidate_external_probe_artifact_index(tmp_path, scan_root=scan_root)
    )

    assert "external probe artifact index" in text
    assert "bundle_count: 1" in text
    assert "newicody/autodoc" in text
