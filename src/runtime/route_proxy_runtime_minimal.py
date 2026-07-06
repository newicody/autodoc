"""Minimal RouteProxy runtime around route frames.

0130 is the first live data-plane step after the RouteProxy flow-control
contracts.  It prepares a local root, grants/blocks writer permits, writes route
frames atomically, reads frames, marks routes stale, and emits observation-ready
facts.  It is deliberately small: no daemon, no Scheduler mutation, no mount scan, no OpenVINO, no Qdrant, no PostgreSQL, and no network client.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any

_RUNTIME_SCHEMA = "missipy.route_proxy.runtime.v1"
_POLICY_SCHEMA = "missipy.route_proxy.runtime_policy.v1"
_PERMIT_SCHEMA = "missipy.route_proxy.runtime_writer_permit.v1"
_FACT_SCHEMA = "missipy.route_proxy.runtime_observation_fact.v1"
_FRAME_SCHEMA = "missipy.route_proxy.runtime_frame.v1"
_STALE_SCHEMA = "missipy.route_proxy.runtime_stale_marker.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SAFE_SEGMENT_RE = re.compile(r"[^a-zA-Z0-9_.=-]+")
_ALLOWED_OWNER_PREFIXES = ("specialist:", "worker:", "scheduler-command:", "proxy:")
_ALLOWED_CONTEXT_PREFIXES = ("sql:", "ctx:", "ctx-result:", "cycle-state:")
_ALLOWED_ROUTE_PREFIXES = ("route:", "route-frame:", "route-zone:", "vector-route:")
_ALLOWED_FACT_KINDS = (
    "route.runtime_prepared",
    "route.writer_permit_granted",
    "route.writer_permit_denied",
    "route.frame_written",
    "route.frame_read",
    "route.frame_marked_stale",
)


class RouteProxyRuntimeError(RuntimeError):
    """Raised when the minimal RouteProxy runtime refuses unsafe route IO."""


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimePolicy:
    """Policy for preparing a minimal RouteProxy runtime root."""

    route_root: Path = Path("/dev/shm/autodoc/routes")
    proxy_ref: str = "proxy:route-proxy"
    require_dev_shm: bool = True
    allow_test_root: bool = False
    namespace: str = "autodoc"

    def __post_init__(self) -> None:
        _require_typed_ref("proxy_ref", self.proxy_ref, required_prefixes=("proxy:",))
        _require_non_empty("namespace", self.namespace)
        if self.route_root.is_symlink():
            raise RouteProxyRuntimeError("route_root must not be a symlink")
        if self.require_dev_shm and not _is_under_dev_shm(self.route_root):
            raise RouteProxyRuntimeError("route_root must be under /dev/shm unless allow_test_root disables the check")
        if self.allow_test_root and self.require_dev_shm:
            raise RouteProxyRuntimeError("allow_test_root requires require_dev_shm=False")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _POLICY_SCHEMA,
            "route_root": str(self.route_root),
            "proxy_ref": self.proxy_ref,
            "require_dev_shm": self.require_dev_shm,
            "allow_test_root": self.allow_test_root,
            "namespace": self.namespace,
            "mount_scan": False,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimeObservationFact:
    """Observation fact ready for EventBus publication by a caller."""

    fact_ref: str
    kind: str
    route_ref: str
    owner_ref: str | None = None
    count: int = 1
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("fact_ref", self.fact_ref, required_prefixes=("route-proxy-fact:", "bus:"))
        if self.kind not in _ALLOWED_FACT_KINDS:
            raise RouteProxyRuntimeError("kind must be a locked RouteProxy runtime observation kind")
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if self.owner_ref is not None:
            _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        if self.count < 0:
            raise RouteProxyRuntimeError("count must be >= 0")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _FACT_SCHEMA,
            "fact_ref": self.fact_ref,
            "kind": self.kind,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "count": self.count,
            "metadata": dict(self.metadata),
            "event_bus_role": "observation_only",
            "payload_command": False,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimePermit:
    """Runtime writer permit for one route frame."""

    permit_ref: str
    route_ref: str
    owner_ref: str
    context_ref: str
    context_generation: int
    priority: int
    write_allowed: bool
    frame_path: Path
    denial_reason: str | None = None

    def __post_init__(self) -> None:
        _require_typed_ref("permit_ref", self.permit_ref, required_prefixes=("route-permit:",))
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_typed_ref("context_ref", self.context_ref, required_prefixes=_ALLOWED_CONTEXT_PREFIXES)
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        _require_priority(self.priority)
        if self.write_allowed and self.denial_reason is not None:
            raise RouteProxyRuntimeError("denial_reason must be None when write_allowed is true")
        if not self.write_allowed:
            _require_non_empty("denial_reason", self.denial_reason or "")

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _PERMIT_SCHEMA,
            "permit_ref": self.permit_ref,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "context_ref": self.context_ref,
            "context_generation": self.context_generation,
            "priority": self.priority,
            "write_allowed": self.write_allowed,
            "frame_path": str(self.frame_path),
            "denial_reason": self.denial_reason,
            "scheduler_is_orchestrator": True,
            "route_proxy_is_fast_data_plane_control": True,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimeState:
    """Prepared RouteProxy runtime root."""

    route_root: Path
    proxy_ref: str
    frames_dir: Path
    meta_dir: Path
    facts_dir: Path
    policy: RouteProxyRuntimePolicy

    def __post_init__(self) -> None:
        if self.route_root.is_symlink():
            raise RouteProxyRuntimeError("route_root must not be a symlink")
        for path in (self.route_root, self.frames_dir, self.meta_dir, self.facts_dir):
            if not path.exists() or not path.is_dir():
                raise RouteProxyRuntimeError(f"runtime path is not a directory: {path}")
            if path.is_symlink():
                raise RouteProxyRuntimeError(f"runtime path must not be a symlink: {path}")

    def frame_path_for(self, route_ref: str) -> Path:
        _require_typed_ref("route_ref", route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        digest = _stable_suffix(route_ref)
        return self.frames_dir / f"{_safe_route_slug(route_ref)}.{digest}.json"

    def meta_path_for(self, ref: str, suffix: str = "json") -> Path:
        _require_typed_ref("ref", ref)
        digest = _stable_suffix(ref)
        return self.meta_dir / f"{_safe_route_slug(ref)}.{digest}.{suffix}"

    def fact_path_for(self, fact_ref: str) -> Path:
        _require_typed_ref("fact_ref", fact_ref, required_prefixes=("route-proxy-fact:", "bus:"))
        return self.facts_dir / f"{_safe_route_slug(fact_ref)}.{_stable_suffix(fact_ref)}.json"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _RUNTIME_SCHEMA,
            "route_root": str(self.route_root),
            "proxy_ref": self.proxy_ref,
            "frames_dir": str(self.frames_dir),
            "meta_dir": str(self.meta_dir),
            "facts_dir": str(self.facts_dir),
            "policy": self.policy.to_mapping(),
            "scheduler_is_orchestrator": True,
            "route_proxy_is_fast_data_plane_control": True,
            "mount_scan": False,
            "daemon": False,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimeFrame:
    """Frame persisted under the RouteProxy runtime root."""

    route_ref: str
    owner_ref: str
    context_ref: str
    context_generation: int
    payload: dict[str, Any]
    stale: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_typed_ref("context_ref", self.context_ref, required_prefixes=_ALLOWED_CONTEXT_PREFIXES)
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        if not isinstance(self.payload, dict):
            raise RouteProxyRuntimeError("payload must be a dict")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _FRAME_SCHEMA,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "context_ref": self.context_ref,
            "context_generation": self.context_generation,
            "payload": self.payload,
            "stale": self.stale,
            "durable_authority": False,
        }


@dataclass(frozen=True, slots=True)
class RouteProxyRuntimeWriteResult:
    """Result of an atomic route frame write."""

    frame_path: Path
    frame: RouteProxyRuntimeFrame
    fact: RouteProxyRuntimeObservationFact

    def to_mapping(self) -> dict[str, object]:
        return {
            "frame_path": str(self.frame_path),
            "frame": self.frame.to_mapping(),
            "fact": self.fact.to_mapping(),
            "atomic_replace": True,
        }


def prepare_route_proxy_runtime(policy: RouteProxyRuntimePolicy | None = None) -> RouteProxyRuntimeState:
    """Prepare a minimal runtime root without scanning system mount tables."""

    active_policy = policy or RouteProxyRuntimePolicy()
    root = active_policy.route_root
    if root.exists() and root.is_symlink():
        raise RouteProxyRuntimeError("route_root must not be a symlink")
    root.mkdir(parents=True, exist_ok=True)
    frames_dir = root / "frames"
    meta_dir = root / "meta"
    facts_dir = root / "facts"
    for path in (frames_dir, meta_dir, facts_dir):
        if path.exists() and path.is_symlink():
            raise RouteProxyRuntimeError(f"runtime path must not be a symlink: {path}")
        path.mkdir(parents=True, exist_ok=True)
    state = RouteProxyRuntimeState(
        route_root=root,
        proxy_ref=active_policy.proxy_ref,
        frames_dir=frames_dir,
        meta_dir=meta_dir,
        facts_dir=facts_dir,
        policy=active_policy,
    )
    fact = RouteProxyRuntimeObservationFact(
        fact_ref=f"route-proxy-fact:runtime-prepared-{_stable_suffix(str(root))}",
        kind="route.runtime_prepared",
        route_ref="route:runtime/root",
        owner_ref=active_policy.proxy_ref,
        metadata=(("route_root", str(root)),),
    )
    _atomic_write_json(state.fact_path_for(fact.fact_ref), fact.to_mapping())
    return state


def request_writer_permit(
    state: RouteProxyRuntimeState,
    *,
    route_ref: str,
    owner_ref: str,
    context_ref: str,
    context_generation: int,
    priority: int,
    write_allowed: bool = True,
    denial_reason: str | None = None,
) -> RouteProxyRuntimePermit:
    """Grant or deny a writer permit and persist the permit metadata."""

    frame_path = state.frame_path_for(route_ref)
    seed = f"{route_ref}|{owner_ref}|{context_ref}|{context_generation}|{priority}|{write_allowed}|{denial_reason or ''}"
    permit = RouteProxyRuntimePermit(
        permit_ref=f"route-permit:{_stable_suffix(seed)}",
        route_ref=route_ref,
        owner_ref=owner_ref,
        context_ref=context_ref,
        context_generation=context_generation,
        priority=priority,
        write_allowed=write_allowed,
        frame_path=frame_path,
        denial_reason=denial_reason,
    )
    _assert_under_root(state, frame_path)
    _atomic_write_json(state.meta_path_for(permit.permit_ref), permit.to_mapping())
    fact = RouteProxyRuntimeObservationFact(
        fact_ref=f"route-proxy-fact:permit-{_stable_suffix(permit.permit_ref)}",
        kind="route.writer_permit_granted" if write_allowed else "route.writer_permit_denied",
        route_ref=route_ref,
        owner_ref=owner_ref,
        metadata=(("permit_ref", permit.permit_ref),),
    )
    _atomic_write_json(state.fact_path_for(fact.fact_ref), fact.to_mapping())
    return permit


def write_route_frame(
    state: RouteProxyRuntimeState,
    permit: RouteProxyRuntimePermit,
    payload: dict[str, Any],
) -> RouteProxyRuntimeWriteResult:
    """Atomically write one route frame if the writer permit is valid."""

    if not permit.write_allowed:
        raise RouteProxyRuntimeError("writer permit denies frame write")
    _assert_under_root(state, permit.frame_path)
    frame = RouteProxyRuntimeFrame(
        route_ref=permit.route_ref,
        owner_ref=permit.owner_ref,
        context_ref=permit.context_ref,
        context_generation=permit.context_generation,
        payload=payload,
    )
    _atomic_write_json(permit.frame_path, frame.to_mapping())
    fact = RouteProxyRuntimeObservationFact(
        fact_ref=f"route-proxy-fact:frame-written-{_stable_suffix(permit.permit_ref)}",
        kind="route.frame_written",
        route_ref=permit.route_ref,
        owner_ref=permit.owner_ref,
        metadata=(("frame_path", str(permit.frame_path)),),
    )
    _atomic_write_json(state.fact_path_for(fact.fact_ref), fact.to_mapping())
    return RouteProxyRuntimeWriteResult(frame_path=permit.frame_path, frame=frame, fact=fact)


def read_route_frame(state: RouteProxyRuntimeState, route_ref: str) -> RouteProxyRuntimeFrame:
    """Read one route frame by route ref."""

    frame_path = state.frame_path_for(route_ref)
    _assert_under_root(state, frame_path)
    try:
        data = json.loads(frame_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RouteProxyRuntimeError(f"route frame not found: {route_ref}") from exc
    frame = RouteProxyRuntimeFrame(
        route_ref=str(data["route_ref"]),
        owner_ref=str(data["owner_ref"]),
        context_ref=str(data["context_ref"]),
        context_generation=int(data["context_generation"]),
        payload=dict(data["payload"]),
        stale=bool(data.get("stale", False)),
    )
    fact = RouteProxyRuntimeObservationFact(
        fact_ref=f"route-proxy-fact:frame-read-{_stable_suffix(route_ref)}",
        kind="route.frame_read",
        route_ref=route_ref,
        owner_ref=frame.owner_ref,
    )
    _atomic_write_json(state.fact_path_for(fact.fact_ref), fact.to_mapping())
    return frame


def mark_route_frame_stale(
    state: RouteProxyRuntimeState,
    *,
    route_ref: str,
    new_context_generation: int,
) -> RouteProxyRuntimeFrame:
    """Mark an existing frame stale when the context generation advances."""

    current = read_route_frame(state, route_ref)
    _require_positive_int("new_context_generation", new_context_generation, allow_zero=False)
    if new_context_generation <= current.context_generation:
        raise RouteProxyRuntimeError("new_context_generation must be greater than current context_generation")
    stale_frame = RouteProxyRuntimeFrame(
        route_ref=current.route_ref,
        owner_ref=current.owner_ref,
        context_ref=current.context_ref,
        context_generation=new_context_generation,
        payload=current.payload,
        stale=True,
    )
    frame_path = state.frame_path_for(route_ref)
    _atomic_write_json(frame_path, stale_frame.to_mapping())
    marker = {
        "schema": _STALE_SCHEMA,
        "route_ref": route_ref,
        "old_context_generation": current.context_generation,
        "new_context_generation": new_context_generation,
        "frame_path": str(frame_path),
    }
    _atomic_write_json(state.meta_path_for(f"route-frame:{route_ref}:stale"), marker)
    fact = RouteProxyRuntimeObservationFact(
        fact_ref=f"route-proxy-fact:frame-stale-{_stable_suffix(route_ref + str(new_context_generation))}",
        kind="route.frame_marked_stale",
        route_ref=route_ref,
        owner_ref=current.owner_ref,
        metadata=(("new_context_generation", str(new_context_generation)),),
    )
    _atomic_write_json(state.fact_path_for(fact.fact_ref), fact.to_mapping())
    return stale_frame


def list_observation_facts(state: RouteProxyRuntimeState) -> tuple[dict[str, Any], ...]:
    """Return persisted observation facts for tests and later passive bridges."""

    facts: list[dict[str, Any]] = []
    for path in sorted(state.facts_dir.glob("*.json")):
        facts.append(json.loads(path.read_text(encoding="utf-8")))
    return tuple(facts)


def _is_under_dev_shm(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except OSError as exc:
        raise RouteProxyRuntimeError(f"cannot resolve route_root: {path}") from exc
    dev_shm = Path("/dev/shm").resolve(strict=False)
    return resolved == dev_shm or dev_shm in resolved.parents


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def _assert_under_root(state: RouteProxyRuntimeState, path: Path) -> None:
    try:
        root = state.route_root.resolve(strict=True)
        target_parent = path.parent.resolve(strict=True)
    except OSError as exc:
        raise RouteProxyRuntimeError("cannot resolve runtime path") from exc
    if target_parent != root and root not in target_parent.parents:
        raise RouteProxyRuntimeError("route frame path escapes runtime root")


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise RouteProxyRuntimeError(f"{name} must be a typed ref")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise RouteProxyRuntimeError(f"{name} must start with one of: {', '.join(required_prefixes)}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RouteProxyRuntimeError(f"{name} must not be empty")


def _require_positive_int(name: str, value: int, *, allow_zero: bool) -> None:
    if not isinstance(value, int):
        raise RouteProxyRuntimeError(f"{name} must be an integer")
    if allow_zero:
        if value < 0:
            raise RouteProxyRuntimeError(f"{name} must be >= 0")
    elif value <= 0:
        raise RouteProxyRuntimeError(f"{name} must be > 0")


def _require_priority(value: int) -> None:
    _require_positive_int("priority", value, allow_zero=True)
    if value > 10_000:
        raise RouteProxyRuntimeError("priority must be between 0 and 10000")


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(normalized)


def _safe_route_slug(route_ref: str) -> str:
    return _SAFE_SEGMENT_RE.sub("-", route_ref).strip("-.") or "route"


def _stable_suffix(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
