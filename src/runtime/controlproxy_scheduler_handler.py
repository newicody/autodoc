from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib import import_module
from inspect import isawaitable

from contracts.event import Event


SchedulerRouteRequestHandler = Callable[[object], object | Awaitable[object]]

SCHEDULER_ROUTE_REQUEST_HANDLER_MODULES: tuple[str, ...] = (
    "runtime.controlproxy_scheduler_adapter",
    "runtime.controlproxy_scheduler",
    "runtime.controlproxy_route_adapter",
    "runtime.controlproxy_route_scheduler",
    "runtime.control_proxy_scheduler_adapter",
    "runtime.control_proxy_scheduler",
    "runtime.control_proxy_route_adapter",
    "runtime.control_proxy_route_scheduler",
)


def resolve_scheduler_route_request_handler() -> SchedulerRouteRequestHandler:
    """Resolve the 0086 Scheduler-facing ControlProxy adapter.

    0088 intentionally stays on the Scheduler/Dispatcher handler boundary. The
    actual route preparation remains in ``handle_scheduler_route_request()`` from
    the 0086 adapter; this resolver only keeps the handler importable while the
    surrounding ControlProxy files still settle on their final module name.
    """
    for module_name in SCHEDULER_ROUTE_REQUEST_HANDLER_MODULES:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as exc:
            missing = exc.name or ""
            if missing == module_name or module_name.startswith(f"{missing}."):
                continue
            raise
        handler = getattr(module, "handle_scheduler_route_request", None)
        if callable(handler):
            return handler
    candidates = ", ".join(SCHEDULER_ROUTE_REQUEST_HANDLER_MODULES)
    raise RuntimeError(
        "handle_scheduler_route_request() not found in ControlProxy Scheduler adapter modules: "
        + candidates
    )


def handle_scheduler_route_request(request: object) -> object | Awaitable[object]:
    """Call the concrete 0086 route-request adapter.

    The adapter, not this handler, owns the Scheduler-facing authorization
    contract such as ``authorized=True`` and ``policy_decision_id``.
    """
    return resolve_scheduler_route_request_handler()(request)


def scheduler_route_request_payload(event: Event) -> object:
    """Extract the ControlProxy route request payload from a Scheduler Event."""
    if event.payload is None:
        raise ValueError("ControlProxy Scheduler route request payload is required")
    return event.payload


@dataclass(frozen=True, slots=True)
class ControlProxySchedulerRouteRequestHandler:
    """Dispatcher handler for Scheduler-authorized ControlProxy route requests.

    This class is deliberately tiny: it does not decide policy, it does not
    create a daemon, and it does not mutate the Scheduler loop. It only bridges
    an already-authorized Scheduler event to the 0086 adapter and returns the
    adapter reply so ``Dispatcher`` can resolve ``Request.reply``.
    """

    route_request_handler: SchedulerRouteRequestHandler | None = None

    async def handle(self, event: Event) -> object:
        request = scheduler_route_request_payload(event)
        handler = self.route_request_handler or handle_scheduler_route_request
        reply = handler(request)
        if isawaitable(reply):
            reply = await reply
        return reply


ControlProxySchedulerRouteHandler = ControlProxySchedulerRouteRequestHandler

__all__ = (
    "ControlProxySchedulerRouteHandler",
    "ControlProxySchedulerRouteRequestHandler",
    "SCHEDULER_ROUTE_REQUEST_HANDLER_MODULES",
    "SchedulerRouteRequestHandler",
    "handle_scheduler_route_request",
    "resolve_scheduler_route_request_handler",
    "scheduler_route_request_payload",
)
