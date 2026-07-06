from __future__ import annotations

from pathlib import Path

import pytest

from runtime.route_proxy_runtime_minimal import (
    RouteProxyRuntimeError,
    RouteProxyRuntimePolicy,
    list_observation_facts,
    mark_route_frame_stale,
    prepare_route_proxy_runtime,
    read_route_frame,
    request_writer_permit,
    write_route_frame,
)


def make_policy(root: Path) -> RouteProxyRuntimePolicy:
    return RouteProxyRuntimePolicy(
        route_root=root,
        proxy_ref="proxy:route-proxy-test",
        require_dev_shm=False,
        allow_test_root=True,
        namespace="autodoc-test",
    )


def test_prepare_runtime_root_creates_minimal_directories_without_mount_scan(tmp_path: Path) -> None:
    state = prepare_route_proxy_runtime(make_policy(tmp_path / "routes"))

    assert state.route_root.exists()
    assert state.frames_dir.exists()
    assert state.meta_dir.exists()
    assert state.facts_dir.exists()
    mapping = state.to_mapping()
    assert mapping["mount_scan"] is False
    assert mapping["daemon"] is False
    assert mapping["scheduler_is_orchestrator"] is True
    assert mapping["route_proxy_is_fast_data_plane_control"] is True


def test_prepare_runtime_root_rejects_symlink_root(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "routes"
    link.symlink_to(target, target_is_directory=True)

    with pytest.raises(RouteProxyRuntimeError, match="route_root must not be a symlink"):
        RouteProxyRuntimePolicy(
            route_root=link,
            require_dev_shm=False,
            allow_test_root=True,
        )


def test_request_permit_write_and_read_frame_roundtrip(tmp_path: Path) -> None:
    state = prepare_route_proxy_runtime(make_policy(tmp_path / "routes"))
    permit = request_writer_permit(
        state,
        route_ref="route:deliberation/cycle-1/round-1/opinion-thermal",
        owner_ref="specialist:thermal",
        context_ref="cycle-state:cycle-1",
        context_generation=4,
        priority=900,
    )
    assert permit.write_allowed is True
    assert permit.frame_path.parent == state.frames_dir

    result = write_route_frame(state, permit, {"summary": "ok", "risk": "low"})
    assert result.frame_path.exists()
    assert result.to_mapping()["atomic_replace"] is True

    frame = read_route_frame(state, permit.route_ref)
    assert frame.payload == {"summary": "ok", "risk": "low"}
    assert frame.context_generation == 4
    assert frame.stale is False


def test_denied_permit_blocks_write(tmp_path: Path) -> None:
    state = prepare_route_proxy_runtime(make_policy(tmp_path / "routes"))
    permit = request_writer_permit(
        state,
        route_ref="route:deliberation/cycle-1/round-1/opinion-material",
        owner_ref="specialist:material",
        context_ref="cycle-state:cycle-1",
        context_generation=4,
        priority=100,
        write_allowed=False,
        denial_reason="context_generation_changed",
    )

    assert permit.denial_reason == "context_generation_changed"
    with pytest.raises(RouteProxyRuntimeError, match="writer permit denies"):
        write_route_frame(state, permit, {"summary": "blocked"})


def test_mark_route_frame_stale_advances_generation(tmp_path: Path) -> None:
    state = prepare_route_proxy_runtime(make_policy(tmp_path / "routes"))
    permit = request_writer_permit(
        state,
        route_ref="route:deliberation/cycle-2/round-1/opinion-safety",
        owner_ref="specialist:safety",
        context_ref="cycle-state:cycle-2",
        context_generation=7,
        priority=500,
    )
    write_route_frame(state, permit, {"summary": "needs refresh"})

    stale = mark_route_frame_stale(
        state,
        route_ref=permit.route_ref,
        new_context_generation=8,
    )
    assert stale.stale is True
    assert stale.context_generation == 8
    assert read_route_frame(state, permit.route_ref).stale is True

    with pytest.raises(RouteProxyRuntimeError, match="greater than current"):
        mark_route_frame_stale(state, route_ref=permit.route_ref, new_context_generation=8)


def test_observation_facts_are_persisted_as_lightweight_records(tmp_path: Path) -> None:
    state = prepare_route_proxy_runtime(make_policy(tmp_path / "routes"))
    permit = request_writer_permit(
        state,
        route_ref="route:deliberation/cycle-3/round-1/demand-vector",
        owner_ref="scheduler-command:vector-indexing",
        context_ref="cycle-state:cycle-3",
        context_generation=1,
        priority=600,
    )
    write_route_frame(state, permit, {"frame_type": "demand"})
    read_route_frame(state, permit.route_ref)

    kinds = {fact["kind"] for fact in list_observation_facts(state)}
    assert {
        "route.runtime_prepared",
        "route.writer_permit_granted",
        "route.frame_written",
        "route.frame_read",
    }.issubset(kinds)


def test_default_policy_requires_dev_shm() -> None:
    policy = RouteProxyRuntimePolicy()
    assert str(policy.route_root).startswith("/dev/shm")
    assert policy.require_dev_shm is True


def test_non_dev_shm_root_is_rejected_without_test_override(tmp_path: Path) -> None:
    with pytest.raises(RouteProxyRuntimeError, match="route_root must be under /dev/shm"):
        RouteProxyRuntimePolicy(route_root=tmp_path / "routes", require_dev_shm=True)
