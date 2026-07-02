from __future__ import annotations

import json
from pathlib import Path

from context.source_candidate_external_probe_operator_summary import (
    build_source_candidate_external_probe_operator_summary_from_index_file,
    build_source_candidate_external_probe_operator_summary_from_index_payload,
    read_source_candidate_external_probe_operator_summary,
    render_source_candidate_external_probe_operator_summary,
    write_source_candidate_external_probe_operator_summary,
)


def _index_payload() -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.external_probe_artifact_index.v1",
        "root": "/tmp/repo",
        "scan_root": "/tmp/repo/bundles",
        "bundle_count": 3,
        "total_artifact_count": 9,
        "total_byte_count": 600,
        "entries": [
            {
                "schema": "missipy.source_candidate.external_probe_artifact_index_entry.v1",
                "bundle_path": "bundles/ready",
                "manifest_path": "bundles/ready/manifest.json",
                "repository": "newicody/autodoc",
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": True,
                "artifact_count": 3,
                "byte_count": 100,
            },
            {
                "schema": "missipy.source_candidate.external_probe_artifact_index_entry.v1",
                "bundle_path": "bundles/check",
                "manifest_path": "bundles/check/manifest.json",
                "repository": "newicody/autodoc",
                "read_only": True,
                "external_call_performed": False,
                "probe_allowed": False,
                "artifact_count": 3,
                "byte_count": 200,
            },
            {
                "schema": "missipy.source_candidate.external_probe_artifact_index_entry.v1",
                "bundle_path": "bundles/blocked",
                "manifest_path": "bundles/blocked/manifest.json",
                "repository": "newicody/autodoc",
                "read_only": True,
                "external_call_performed": True,
                "probe_allowed": True,
                "artifact_count": 3,
                "byte_count": 300,
            },
        ],
    }


def test_external_probe_operator_summary_counts_statuses() -> None:
    summary = build_source_candidate_external_probe_operator_summary_from_index_payload(_index_payload())

    assert summary.bundle_count == 3
    assert summary.ready_count == 1
    assert summary.check_count == 1
    assert summary.blocked_count == 1
    assert summary.total_artifact_count == 9
    assert summary.total_byte_count == 600


def test_external_probe_operator_summary_builds_from_file(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps(_index_payload()) + "\n", encoding="utf-8")

    summary = build_source_candidate_external_probe_operator_summary_from_index_file(index_path)

    assert summary.index_path == index_path
    assert summary.items[0].status == "ready"
    assert summary.items[1].status == "check"
    assert summary.items[2].status == "blocked"


def test_external_probe_operator_summary_writes_and_reads_json(tmp_path: Path) -> None:
    output = tmp_path / "summary.json"
    summary = build_source_candidate_external_probe_operator_summary_from_index_payload(_index_payload())

    returned = write_source_candidate_external_probe_operator_summary(output, summary)
    payload = read_source_candidate_external_probe_operator_summary(output)

    assert returned == output
    assert payload["schema"] == "missipy.source_candidate.external_probe_operator_summary.v1"
    assert payload["ready_count"] == 1


def test_external_probe_operator_summary_render_is_stable() -> None:
    text = render_source_candidate_external_probe_operator_summary(
        build_source_candidate_external_probe_operator_summary_from_index_payload(_index_payload())
    )

    assert "external probe operator summary" in text
    assert "ready_count: 1" in text
    assert "check_count: 1" in text
    assert "blocked_count: 1" in text
    assert "newicody/autodoc" in text
