from __future__ import annotations

import pytest

from runtime.specialist_kernel_boundary import (
    SPECIALIST_KERNEL_COMMAND_SCHEMA,
    SpecialistKernelBoundaryError,
    SpecialistKernelCommand,
    build_specialist_kernel_boundary_plan,
    specialist_route_runtime_prepare_command,
)


def test_specialist_route_runtime_command_requires_kernel_path() -> None:
    command = specialist_route_runtime_prepare_command(
        specialist_id="planner.alpha",
        route_id="route-a",
        zone="zone-a",
        intent="prepare route for specialist output",
        payload={"slots": 8, "slot_size": 64},
    )

    plan = build_specialist_kernel_boundary_plan(command)
    mapping = plan.to_mapping()

    assert mapping["next_boundary"] == "Scheduler.emit()"
    assert mapping["runtime_boundary"] == "Handler -> RouteRuntimeManager"
    assert mapping["status"] == "kernel_path_required"
    assert mapping["kernel_path"] == [
        "SpecialistKernelCommand -> Scheduler.emit()",
        "PolicyEngine.decide()",
        "PriorityQueue",
        "Scheduler.run()",
        "Dispatcher",
        "Handler",
    ]
    assert "Specialist -> RouteRuntimeManager" in mapping["forbidden_direct_boundaries"]
    assert "ControlProxyBus" in mapping["forbidden_direct_boundaries"]


def test_route_runtime_prepare_requires_route_and_zone() -> None:
    with pytest.raises(SpecialistKernelBoundaryError, match="route_id is required"):
        SpecialistKernelCommand(
            schema=SPECIALIST_KERNEL_COMMAND_SCHEMA,
            specialist_id="planner.alpha",
            command_kind="route_runtime_prepare",
            intent="prepare route",
            zone="zone-a",
        )

    with pytest.raises(SpecialistKernelBoundaryError, match="zone is required"):
        SpecialistKernelCommand(
            schema=SPECIALIST_KERNEL_COMMAND_SCHEMA,
            specialist_id="planner.alpha",
            command_kind="route_runtime_prepare",
            intent="prepare route",
            route_id="route-a",
        )


def test_non_route_specialist_command_has_no_runtime_boundary() -> None:
    command = SpecialistKernelCommand(
        schema=SPECIALIST_KERNEL_COMMAND_SCHEMA,
        specialist_id="reasoner.alpha",
        command_kind="specialist_result",
        intent="publish specialist result intent",
        payload={"result_id": "r1"},
    )

    plan = build_specialist_kernel_boundary_plan(command)

    assert plan.runtime_boundary is None
    assert plan.next_boundary == "Scheduler.emit()"
    assert plan.to_mapping()["command"]["payload"] == {"result_id": "r1"}


def test_command_payload_is_immutable_projection() -> None:
    payload = {"slots": 4}
    command = specialist_route_runtime_prepare_command(
        specialist_id="planner.alpha",
        route_id="route-a",
        zone="zone-a",
        intent="prepare route",
        payload=payload,
    )
    payload["slots"] = 99

    assert dict(command.payload) == {"slots": 4}
    with pytest.raises(TypeError):
        command.payload["slots"] = 100  # type: ignore[index]
