"""Locked materializer for ControlProxy route generation allocation.

This module implements phase 0095. It composes the phase 0094
inter-process route generation lock with the phase 0091-r2 generation table
materializer. The operational critical section is intentionally small:
load -> verify -> materialize -> persist.

The lock protects route_id -> current_generation allocation for g2/g3 route
updates. The generation table is incremented only when a new route generation
is materialized by materialize_route_generation_candidate(). Normal Scheduler
handshakes, route writes, route reads and notifier wakeups do not allocate a
generation.

Boundaries deliberately kept out of this module:
- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No policy/zone/scope decision in ControlProxy.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- No live mmap resize.
- Not /dev/shm-only; callers may still pass a file-backed runtime root.
- standard library only.
"""
from __future__ import annotations

from pathlib import Path

from runtime.controlproxy_prepare import RoutePrepareDecision
from runtime.route_generation_lock import acquire_route_generation_lock
from runtime.route_generation_table import (
    RouteGenerationCandidateResult,
    materialize_route_generation_candidate,
)


def materialize_route_generation_candidate_with_lock(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    decision: RoutePrepareDecision,
    blocking: bool = True,
) -> RouteGenerationCandidateResult:
    """Materialize one route generation while holding the route table lock.

    The function does not decide whether the request is authorized. It expects
    the caller to provide the Scheduler/policy/zone-authorized prepare decision
    already used by the unlocked materializer. Its only added responsibility is
    serializing the ControlFS generation table mutation for one logical route.
    """

    with acquire_route_generation_lock(
        controlfs_root=controlfs_root,
        route_id=decision.route_id,
        blocking=blocking,
    ):
        return materialize_route_generation_candidate(
            controlfs_root=controlfs_root,
            runtime_root=runtime_root,
            decision=decision,
        )
