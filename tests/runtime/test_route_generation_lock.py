from __future__ import annotations

from pathlib import Path

import pytest

from runtime.route_generation_lock import (
    ROUTE_GENERATION_LOCK_SCHEMA,
    RouteGenerationFileLock,
    RouteGenerationLockError,
    RouteGenerationLockUnavailable,
    acquire_route_generation_lock,
    route_generation_lock_path,
)


def test_route_generation_lock_path_is_controlfs_sidecar(tmp_path: Path) -> None:
    path = route_generation_lock_path(tmp_path, "route-a")

    assert path == tmp_path / "active" / "routes" / "route-a" / "generation.lock"


def test_route_generation_lock_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(Exception, match="route_id"):
        route_generation_lock_path(tmp_path, "../route-a")


def test_route_generation_lock_serializes_nonblocking_acquire(tmp_path: Path) -> None:
    first = RouteGenerationFileLock(controlfs_root=tmp_path, route_id="route-a")

    with first as first_info:
        assert first_info.schema == ROUTE_GENERATION_LOCK_SCHEMA
        assert first_info.state == "locked"
        assert first_info.route_id == "route-a"
        assert Path(first_info.lock_path).exists()

        second = RouteGenerationFileLock(
            controlfs_root=tmp_path,
            route_id="route-a",
            blocking=False,
        )
        with pytest.raises(RouteGenerationLockUnavailable):
            second.acquire()

    third = RouteGenerationFileLock(
        controlfs_root=tmp_path,
        route_id="route-a",
        blocking=False,
    )
    with third as third_info:
        assert third_info.state == "locked"


def test_route_generation_lock_allows_different_routes(tmp_path: Path) -> None:
    with acquire_route_generation_lock(controlfs_root=tmp_path, route_id="route-a") as first_info:
        with acquire_route_generation_lock(controlfs_root=tmp_path, route_id="route-b", blocking=False) as second_info:
            assert first_info.route_id == "route-a"
            assert second_info.route_id == "route-b"


def test_route_generation_lock_to_mapping_is_stable(tmp_path: Path) -> None:
    lock = RouteGenerationFileLock(controlfs_root=tmp_path, route_id="route-a", blocking=False)

    with lock as info:
        assert info.to_mapping() == {
            "blocking": False,
            "lock_path": str(tmp_path / "active" / "routes" / "route-a" / "generation.lock"),
            "route_id": "route-a",
            "schema": ROUTE_GENERATION_LOCK_SCHEMA,
            "state": "locked",
        }


def test_route_generation_lock_release_requires_acquire(tmp_path: Path) -> None:
    lock = RouteGenerationFileLock(controlfs_root=tmp_path, route_id="route-a")

    with pytest.raises(RouteGenerationLockError, match="not acquired"):
        lock.release()
