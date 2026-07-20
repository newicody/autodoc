from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from runtime.controlfs_manifest import (
    RouteManifest,
    route_manifest_path,
)
from runtime.controlproxy_scheduler_adapter import (
    CONTROLFS_ROOT_ENV,
    ControlProxySchedulerAdapterError,
    ensure_desired_scheduler_route_manifest,
    handle_scheduler_route_request,
)
from runtime.scheduler_route_adapter import scheduler_route_request_mapping
import runtime.controlproxy_scheduler_adapter as adapter


def _request(*, task_id: str = "task:github-research:abc") -> dict[str, object]:
    return scheduler_route_request_mapping(
        request_id="request:scheduler-candidate-github-research-abc",
        route_id="github-research-laboratory-abc",
        task_id=task_id,
        holder="scheduler",
        scope="route.write",
        policy_decision_id="policy-decision:github-research-auto:abc",
        ttl_seconds=300,
        activate=True,
        requested_at="2026-07-20T04:00:00Z",
    )


def test_handler_requires_explicit_controlfs_root(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CONTROLFS_ROOT_ENV, raising=False)
    with pytest.raises(
        ControlProxySchedulerAdapterError,
        match=CONTROLFS_ROOT_ENV,
    ):
        handle_scheduler_route_request(_request())


def test_handler_binds_controlfs_and_dev_shm_then_delegates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlfs_root = tmp_path / "controlfs"
    runtime_root = tmp_path / "routes-runtime"
    monkeypatch.setenv(CONTROLFS_ROOT_ENV, str(controlfs_root))
    monkeypatch.setattr(
        adapter,
        "prepare_dev_shm_route_runtime_root",
        lambda: SimpleNamespace(runtime_root=str(runtime_root)),
    )
    expected_reply = object()
    observed: dict[str, object] = {}

    def fake_handle(**kwargs: object) -> object:
        observed.update(kwargs)
        return expected_reply

    monkeypatch.setattr(adapter, "_handle_scheduler_route_request", fake_handle)

    result = handle_scheduler_route_request(_request())

    assert result is expected_reply
    assert observed["controlfs_root"] == controlfs_root
    assert observed["runtime_root"] == str(runtime_root)
    assert observed["publish_bus"] is False
    manifest = RouteManifest.from_path(
        route_manifest_path(controlfs_root, "github-research-laboratory-abc")
    )
    assert manifest.task_id == "task:github-research:abc"
    assert manifest.zone == "scheduler"
    assert manifest.transport == "mmap.fixed_slot"
    assert manifest.sizing_source == "scheduler.route_request.refs_only"


def test_desired_manifest_replay_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controlfs_root = tmp_path / "controlfs"
    first = ensure_desired_scheduler_route_manifest(
        controlfs_root=controlfs_root,
        request=_request(),
    )

    def refuse_rewrite(path: Path, manifest: RouteManifest) -> None:
        raise AssertionError("replay must not rewrite the manifest")

    monkeypatch.setattr(adapter, "_write_manifest_create_only", refuse_rewrite)
    second = ensure_desired_scheduler_route_manifest(
        controlfs_root=controlfs_root,
        request=_request(),
    )

    assert second == first


def test_conflicting_existing_manifest_fails_closed(tmp_path: Path) -> None:
    controlfs_root = tmp_path / "controlfs"
    original = ensure_desired_scheduler_route_manifest(
        controlfs_root=controlfs_root,
        request=_request(),
    )
    path = route_manifest_path(controlfs_root, original.route_id)
    raw = original.to_mapping()
    raw["task_id"] = "task:github-research:other"
    path.write_text(
        __import__("json").dumps(raw, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ControlProxySchedulerAdapterError,
        match="conflicts with authorized request",
    ):
        ensure_desired_scheduler_route_manifest(
            controlfs_root=controlfs_root,
            request=_request(),
        )


def test_relative_controlfs_root_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        ControlProxySchedulerAdapterError,
        match="absolute path",
    ):
        ensure_desired_scheduler_route_manifest(
            controlfs_root=Path("relative-controlfs"),
            request=_request(),
        )
