import json
from pathlib import Path

from context.baby_fork_controlfs import (
    BABY_FORK_CONTEXT_GATE_ROUTE,
    BABY_FORK_RETRIEVAL_ROUTE,
    BABY_FORK_VARIANT_ROUTE,
    baby_fork_route_specs,
    build_baby_fork_routeproxy_plan,
    write_baby_fork_desired_manifests,
)
from runtime.controlfs_manifest import RouteManifest


def test_baby_fork_route_specs_lock_three_routes() -> None:
    specs = baby_fork_route_specs(context_id="ctx-baby-fork-001")

    assert tuple(spec.route_id for spec in specs) == (
        BABY_FORK_RETRIEVAL_ROUTE,
        BABY_FORK_VARIANT_ROUTE,
        BABY_FORK_CONTEXT_GATE_ROUTE,
    )
    assert all(spec.task_id == "ctx-baby-fork-001" for spec in specs)


def test_write_baby_fork_desired_manifests(tmp_path: Path) -> None:
    paths = write_baby_fork_desired_manifests(tmp_path, context_id="ctx-baby-fork-001")

    assert len(paths) == 3
    for path in paths:
        assert path.exists()
        manifest = RouteManifest.from_mapping(json.loads(path.read_text(encoding="utf-8")))
        assert manifest.task_id == "ctx-baby-fork-001"

    assert (tmp_path / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json").exists()
    assert (tmp_path / "desired" / "routes" / "baby_fork.variant_stub" / "manifest.json").exists()
    assert (tmp_path / "desired" / "routes" / "baby_fork.context_gate" / "manifest.json").exists()


def test_baby_fork_routeproxy_plan_creates_three_routes_when_active_empty(tmp_path: Path) -> None:
    plan = build_baby_fork_routeproxy_plan(tmp_path, context_id="ctx-baby-fork-001")

    assert len(plan.by_action("create")) == 3
    assert len(plan.by_action("delete")) == 0
    assert len(plan.by_action("update")) == 0
    assert len(plan.by_action("error")) == 0

    assert tuple(item.route_id for item in plan.by_action("create")) == (
        "baby_fork.context_gate",
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
    )
