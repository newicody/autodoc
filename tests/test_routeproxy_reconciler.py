import json
from pathlib import Path

from runtime.controlfs_manifest import ROUTE_MANIFEST_SCHEMA
from runtime.routeproxy_reconciler import build_routeproxy_plan, summarize_plan


def _manifest(route_id: str, ttl_seconds: int = 30, mode: str = "rw") -> dict:
    return {
        "schema": ROUTE_MANIFEST_SCHEMA,
        "route_id": route_id,
        "task_id": "baby_fork_smoke",
        "zone": "workers",
        "scope": "context.read",
        "producer": "scheduler",
        "consumer": "retrieval_worker",
        "ttl_seconds": ttl_seconds,
        "mode": mode,
        "message_schema": "missipy.runtime.route_message.v1",
        "created_by": "scheduler",
        "created_at": "2026-07-04T20:00:00Z",
    }


def _write_manifest(root: Path, side: str, route_id: str, manifest: dict | None = None) -> None:
    route_dir = root / side / "routes" / route_id
    route_dir.mkdir(parents=True)
    payload = _manifest(route_id) if manifest is None else manifest
    (route_dir / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_plan_create_when_desired_missing_from_active(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "desired", "baby_fork.retrieval")

    plan = build_routeproxy_plan(tmp_path)

    assert summarize_plan(plan) == {"create": 1, "delete": 0, "update": 0, "noop": 0, "error": 0}
    assert plan.items[0].action == "create"
    assert plan.items[0].route_id == "baby_fork.retrieval"


def test_plan_delete_when_active_no_longer_desired(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "active", "baby_fork.retrieval")

    plan = build_routeproxy_plan(tmp_path)

    assert summarize_plan(plan) == {"create": 0, "delete": 1, "update": 0, "noop": 0, "error": 0}
    assert plan.items[0].action == "delete"


def test_plan_update_when_manifests_differ(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "desired", "baby_fork.retrieval", _manifest("baby_fork.retrieval", ttl_seconds=60))
    _write_manifest(tmp_path, "active", "baby_fork.retrieval", _manifest("baby_fork.retrieval", ttl_seconds=30))

    plan = build_routeproxy_plan(tmp_path)

    assert summarize_plan(plan) == {"create": 0, "delete": 0, "update": 1, "noop": 0, "error": 0}
    assert plan.items[0].action == "update"


def test_plan_noop_only_when_requested(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "desired", "baby_fork.retrieval")
    _write_manifest(tmp_path, "active", "baby_fork.retrieval")

    plan_without_noop = build_routeproxy_plan(tmp_path)
    plan_with_noop = build_routeproxy_plan(tmp_path, include_noop=True)

    assert plan_without_noop.items == ()
    assert summarize_plan(plan_with_noop) == {"create": 0, "delete": 0, "update": 0, "noop": 1, "error": 0}


def test_plan_error_for_invalid_manifest(tmp_path: Path) -> None:
    route_dir = tmp_path / "desired" / "routes" / "baby_fork.retrieval"
    route_dir.mkdir(parents=True)
    (route_dir / "manifest.json").write_text("{}", encoding="utf-8")

    plan = build_routeproxy_plan(tmp_path)

    assert plan.has_errors()
    assert summarize_plan(plan) == {"create": 0, "delete": 0, "update": 0, "noop": 0, "error": 1}
    assert plan.items[0].action == "error"
    assert "invalid desired route manifest" in plan.items[0].reason


def test_plan_error_when_manifest_route_id_mismatch(tmp_path: Path) -> None:
    _write_manifest(tmp_path, "desired", "baby_fork.retrieval", _manifest("baby_fork.variant_stub"))

    plan = build_routeproxy_plan(tmp_path)

    assert plan.has_errors()
    assert plan.items[0].action == "error"
    assert "route_id does not match directory name" in plan.items[0].reason
