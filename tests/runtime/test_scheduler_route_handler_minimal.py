from __future__ import annotations

from pathlib import Path

import pytest

from runtime.route_proxy_runtime_minimal import (
    RouteProxyRuntimeError,
    RouteProxyRuntimePolicy,
    prepare_route_proxy_runtime,
    read_route_frame,
)
from runtime.scheduler_route_handler_minimal import (
    SchedulerRouteFrameRequest,
    SchedulerRouteHandlerCommand,
    build_single_frame_route_command,
    describe_existing_scheduler_route_handler_integration,
    handle_scheduler_route_command,
    handle_scheduler_route_command_with_readback,
    read_scheduler_route_handler_result_frames,
)


def make_policy(root: Path) -> RouteProxyRuntimePolicy:
    return RouteProxyRuntimePolicy(
        route_root=root,
        proxy_ref="proxy:route-proxy-test",
        require_dev_shm=False,
        allow_test_root=True,
        namespace="autodoc-test",
    )


def test_single_frame_command_writes_specialist_demand_via_route_proxy_runtime(tmp_path: Path) -> None:
    policy = make_policy(tmp_path / "routes")
    command = build_single_frame_route_command(
        command_ref="scheduler-command:dispatch-demand-1",
        route_ref="route:deliberation/cycle-1/round-1/demand-thermal",
        owner_ref="scheduler-command:dispatch-demand-1",
        context_ref="cycle-state:cycle-1",
        context_generation=1,
        priority=800,
        frame_kind="specialist_demand",
        payload={"specialist_ref": "specialist:thermal", "request": "analyse thermique"},
        runtime_policy=policy,
    )

    result = handle_scheduler_route_command(command)

    assert result.wrote_anything is True
    assert result.written_route_refs == ("route:deliberation/cycle-1/round-1/demand-thermal",)
    assert result.denied_route_refs == ()
    assert len(result.frame_paths) == 1
    frame = read_route_frame(prepare_route_proxy_runtime(policy), result.written_route_refs[0])
    assert frame.payload["frame_kind"] == "specialist_demand"
    assert frame.payload["specialist_ref"] == "specialist:thermal"


def test_handler_result_mapping_locks_scheduler_and_eventbus_boundaries(tmp_path: Path) -> None:
    command = build_single_frame_route_command(
        command_ref="scheduler-command:vector-request-1",
        route_ref="route:vector-indexing/default/embedding-request",
        owner_ref="scheduler-command:vector-request-1",
        context_ref="cycle-state:vector-1",
        context_generation=2,
        priority=600,
        frame_kind="vector_embedding_request",
        payload={"text_for_embedding": "query: cuillere bebe"},
        runtime_policy=make_policy(tmp_path / "routes"),
    )

    mapping = handle_scheduler_route_command(command).to_mapping()

    assert mapping["scheduler_is_orchestrator"] is True
    assert mapping["handler_is_executor"] is True
    assert mapping["event_bus_observation_only"] is True
    assert mapping["dev_shm_data_plane"] is True
    assert mapping["wrote_anything"] is True


def test_handler_can_deny_a_frame_without_writing_payload(tmp_path: Path) -> None:
    policy = make_policy(tmp_path / "routes")
    request = SchedulerRouteFrameRequest(
        route_ref="route:deliberation/cycle-2/round-1/demand-material",
        owner_ref="scheduler-command:dispatch-demand-2",
        context_ref="cycle-state:cycle-2",
        context_generation=5,
        priority=100,
        frame_kind="specialist_demand",
        payload={"specialist_ref": "specialist:material"},
        write_allowed=False,
        denial_reason="context_generation_changed",
    )
    command = SchedulerRouteHandlerCommand(
        command_ref="scheduler-command:dispatch-demand-2",
        handler_ref="handler:scheduler-route-minimal",
        route_root_ref="route:runtime/root",
        frame_requests=(request,),
        runtime_policy=policy,
    )

    result = handle_scheduler_route_command(command)

    assert result.written_route_refs == ()
    assert result.denied_route_refs == ("route:deliberation/cycle-2/round-1/demand-material",)
    with pytest.raises(RouteProxyRuntimeError, match="route frame not found"):
        read_route_frame(prepare_route_proxy_runtime(policy), request.route_ref)


def test_command_accepts_multiple_frame_requests_in_order(tmp_path: Path) -> None:
    policy = make_policy(tmp_path / "routes")
    requests = (
        SchedulerRouteFrameRequest(
            route_ref="route:deliberation/cycle-3/round-1/demand-thermal",
            owner_ref="scheduler-command:round-3",
            context_ref="cycle-state:cycle-3",
            context_generation=1,
            priority=900,
            frame_kind="specialist_demand",
            payload={"specialist_ref": "specialist:thermal"},
        ),
        SchedulerRouteFrameRequest(
            route_ref="route:deliberation/cycle-3/round-1/demand-safety",
            owner_ref="scheduler-command:round-3",
            context_ref="cycle-state:cycle-3",
            context_generation=1,
            priority=850,
            frame_kind="specialist_demand",
            payload={"specialist_ref": "specialist:safety"},
        ),
    )
    command = SchedulerRouteHandlerCommand(
        command_ref="scheduler-command:round-3",
        handler_ref="handler:scheduler-route-minimal",
        route_root_ref="route:runtime/root",
        frame_requests=requests,
        runtime_policy=policy,
    )

    result = handle_scheduler_route_command(command)

    assert result.written_route_refs == tuple(request.route_ref for request in requests)
    assert len(result.frame_paths) == 2


def test_request_rejects_unknown_frame_kind() -> None:
    with pytest.raises(RouteProxyRuntimeError, match="frame_kind"):
        SchedulerRouteFrameRequest(
            route_ref="route:bad",
            owner_ref="scheduler-command:bad",
            context_ref="cycle-state:bad",
            context_generation=1,
            priority=1,
            frame_kind="unknown",
            payload={},
        )



def test_0133_handler_readback_extends_existing_handler_surface(tmp_path: Path) -> None:
    policy = make_policy(tmp_path / "routes")
    command = build_single_frame_route_command(
        command_ref="scheduler-command:dispatch-demand-readback",
        route_ref="route:deliberation/cycle-4/round-1/demand-thermal",
        owner_ref="scheduler-command:dispatch-demand-readback",
        context_ref="cycle-state:cycle-4",
        context_generation=1,
        priority=700,
        frame_kind="specialist_demand",
        payload={"specialist_ref": "specialist:thermal", "request": "analyse"},
        runtime_policy=policy,
    )

    readback = handle_scheduler_route_command_with_readback(command)
    mapping = readback.to_mapping()

    assert mapping["extends_existing_scheduler_route_handler"] is True
    assert mapping["creates_parallel_runtime"] is False
    assert mapping["scheduler_is_orchestrator"] is True
    assert mapping["readback_count"] == 1
    assert readback.readback_frames[0].payload["specialist_ref"] == "specialist:thermal"


def test_0133_can_read_result_frames_from_existing_runtime_state(tmp_path: Path) -> None:
    policy = make_policy(tmp_path / "routes")
    state = prepare_route_proxy_runtime(policy)
    command = build_single_frame_route_command(
        command_ref="scheduler-command:dispatch-demand-readback-2",
        route_ref="route:deliberation/cycle-5/round-1/demand-safety",
        owner_ref="scheduler-command:dispatch-demand-readback-2",
        context_ref="cycle-state:cycle-5",
        context_generation=2,
        priority=650,
        frame_kind="specialist_demand",
        payload={"specialist_ref": "specialist:safety"},
        runtime_policy=policy,
    )

    result = handle_scheduler_route_command(command, runtime_state=state)
    frames = read_scheduler_route_handler_result_frames(state, result)

    assert len(frames) == 1
    assert frames[0].route_ref == result.written_route_refs[0]
    assert frames[0].payload["frame_kind"] == "specialist_demand"


def test_0133_integration_decision_reuses_existing_surfaces() -> None:
    decision = describe_existing_scheduler_route_handler_integration()
    mapping = decision.to_mapping()

    assert mapping["decision"] == "extend_existing"
    assert mapping["creates_parallel_runtime"] is False
    assert mapping["scheduler_run_modified"] is False
    assert mapping["extended_surface_path"] == "src/runtime/scheduler_route_handler_minimal.py"
    assert "src/runtime/route_proxy_runtime_minimal.py" in mapping["reused_runtime_paths"]
    assert "src/runtime/controlproxy_scheduler_handler.py" in mapping["reused_runtime_paths"]
    assert "tools/audit_existing_runtime_integration.py" in mapping["audit_source_refs"]
