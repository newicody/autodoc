from __future__ import annotations

from pathlib import Path

import pytest

from runtime.route_dev_shm_runtime import (
    RouteDevShmRuntimeError,
    RouteDevShmRuntimePolicy,
    build_dev_shm_route_runtime_manager,
    prepare_dev_shm_route_runtime_root,
    route_dev_shm_runtime_root_from_mapping,
)


def test_prepare_dev_shm_runtime_root_creates_namespaced_runtime_root(tmp_path: Path) -> None:
    root = tmp_path / "dev-shm"
    root.mkdir()

    result = prepare_dev_shm_route_runtime_root(
        RouteDevShmRuntimePolicy(
            dev_shm_root=root,
            namespace="autodoc-test",
            require_tmpfs=False,
        )
    )

    assert result.namespace == "autodoc-test"
    assert Path(result.runtime_root) == root / "autodoc-test" / "routes-runtime"
    assert Path(result.runtime_root).is_dir()
    assert result.tmpfs_required is False
    assert result.created is True


def test_prepare_dev_shm_runtime_root_rejects_namespace_traversal(tmp_path: Path) -> None:
    root = tmp_path / "dev-shm"
    root.mkdir()

    for namespace in ("", ".", "..", "a/b", "a\\b"):
        with pytest.raises(RouteDevShmRuntimeError):
            RouteDevShmRuntimePolicy(
                dev_shm_root=root,
                namespace=namespace,
                require_tmpfs=False,
            )


def test_prepare_dev_shm_runtime_root_rejects_symlink_root(tmp_path: Path) -> None:
    target = tmp_path / "real-shm"
    target.mkdir()
    symlink = tmp_path / "shm-link"
    symlink.symlink_to(target, target_is_directory=True)

    with pytest.raises(RouteDevShmRuntimeError, match="must not be a symlink"):
        prepare_dev_shm_route_runtime_root(
            RouteDevShmRuntimePolicy(
                dev_shm_root=symlink,
                namespace="autodoc-test",
                require_tmpfs=False,
            )
        )


def test_prepare_dev_shm_runtime_root_rejects_symlink_namespace(tmp_path: Path) -> None:
    root = tmp_path / "dev-shm"
    root.mkdir()
    target = tmp_path / "elsewhere"
    target.mkdir()
    (root / "autodoc-test").symlink_to(target, target_is_directory=True)

    with pytest.raises(RouteDevShmRuntimeError, match="namespace root"):
        prepare_dev_shm_route_runtime_root(
            RouteDevShmRuntimePolicy(
                dev_shm_root=root,
                namespace="autodoc-test",
                require_tmpfs=False,
            )
        )


def test_route_dev_shm_runtime_root_mapping_roundtrip(tmp_path: Path) -> None:
    root = tmp_path / "dev-shm"
    root.mkdir()
    result = prepare_dev_shm_route_runtime_root(
        RouteDevShmRuntimePolicy(
            dev_shm_root=root,
            namespace="autodoc-test",
            require_tmpfs=False,
        )
    )

    loaded = route_dev_shm_runtime_root_from_mapping(result.to_mapping())

    assert loaded == result
    assert loaded.to_mapping() == result.to_mapping()


def test_build_dev_shm_route_runtime_manager_uses_explicit_runtime_root(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    root = tmp_path / "dev-shm"
    root.mkdir()

    binding = build_dev_shm_route_runtime_manager(
        controlfs_root=controlfs_root,
        policy=RouteDevShmRuntimePolicy(
            dev_shm_root=root,
            namespace="autodoc-test",
            require_tmpfs=False,
        ),
        blocking_lock=False,
    )

    expected_runtime_root = root / "autodoc-test" / "routes-runtime"
    assert binding.manager.controlfs_root == controlfs_root
    assert binding.manager.runtime_root == expected_runtime_root
    assert binding.to_mapping()["root"]["runtime_root"] == str(expected_runtime_root)
