from pathlib import Path

import pytest

from runtime.controlfs_manifest import (
    ManifestValidationError,
    ROUTE_MANIFEST_SCHEMA,
    RouteManifest,
    load_desired_route_manifest,
    normalize_route_id,
    route_manifest_path,
)


def _valid_manifest() -> dict:
    return {
        "schema": ROUTE_MANIFEST_SCHEMA,
        "route_id": "baby_fork.retrieval",
        "task_id": "baby_fork_smoke",
        "zone": "workers",
        "scope": "context.read",
        "producer": "scheduler",
        "consumer": "retrieval_worker",
        "ttl_seconds": 30,
        "mode": "rw",
        "message_schema": "missipy.runtime.route_message.v1",
        "created_by": "scheduler",
        "created_at": "2026-07-04T20:00:00Z",
    }


def test_valid_route_manifest_from_mapping() -> None:
    manifest = RouteManifest.from_mapping(_valid_manifest())

    assert manifest.schema == ROUTE_MANIFEST_SCHEMA
    assert manifest.route_id == "baby_fork.retrieval"
    assert manifest.scope == "context.read"
    assert manifest.ttl_seconds == 30
    assert manifest.to_mapping()["route_id"] == "baby_fork.retrieval"


@pytest.mark.parametrize(
    "route_id",
    [
        "../escape",
        "baby_fork/retrieval",
        "baby_fork\\retrieval",
        " baby_fork.retrieval",
        "baby_fork.retrieval ",
        "BabyFork",
        "",
    ],
)
def test_route_id_rejects_path_or_non_normalized_values(route_id: str) -> None:
    with pytest.raises(ManifestValidationError):
        normalize_route_id(route_id)


def test_route_manifest_rejects_missing_required_field() -> None:
    raw = _valid_manifest()
    raw.pop("consumer")

    with pytest.raises(ManifestValidationError, match="missing required fields"):
        RouteManifest.from_mapping(raw)


def test_route_manifest_rejects_unsupported_schema() -> None:
    raw = _valid_manifest()
    raw["schema"] = "missipy.controlfs.route_manifest.v0"

    with pytest.raises(ManifestValidationError, match="unsupported route manifest schema"):
        RouteManifest.from_mapping(raw)


def test_route_manifest_rejects_invalid_ttl() -> None:
    raw = _valid_manifest()
    raw["ttl_seconds"] = 0

    with pytest.raises(ManifestValidationError, match="ttl_seconds"):
        RouteManifest.from_mapping(raw)


def test_route_manifest_rejects_invalid_mode() -> None:
    raw = _valid_manifest()
    raw["mode"] = "execute"

    with pytest.raises(ManifestValidationError, match="mode"):
        RouteManifest.from_mapping(raw)


def test_route_manifest_path_uses_safe_controlfs_layout(tmp_path: Path) -> None:
    path = route_manifest_path(tmp_path, "baby_fork.retrieval")

    assert path == tmp_path / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json"


def test_load_desired_route_manifest(tmp_path: Path) -> None:
    path = route_manifest_path(tmp_path, "baby_fork.retrieval")
    path.parent.mkdir(parents=True)
    path.write_text(
        """{
          "schema": "missipy.controlfs.route_manifest.v1",
          "route_id": "baby_fork.retrieval",
          "task_id": "baby_fork_smoke",
          "zone": "workers",
          "scope": "context.read",
          "producer": "scheduler",
          "consumer": "retrieval_worker",
          "ttl_seconds": 30,
          "mode": "rw",
          "message_schema": "missipy.runtime.route_message.v1",
          "created_by": "scheduler",
          "created_at": "2026-07-04T20:00:00Z"
        }""",
        encoding="utf-8",
    )

    manifest = load_desired_route_manifest(tmp_path, "baby_fork.retrieval")

    assert manifest.route_id == "baby_fork.retrieval"
