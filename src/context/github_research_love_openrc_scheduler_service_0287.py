"""Propriétaire OpenRC du processus Scheduler de recherche GitHub.

Cette unité possède uniquement le cycle de vie du processus Python et du
Scheduler canonique qui lui est injecté. Elle ne construit ni Scheduler,
Dispatcher, EventBus, connexion PostgreSQL, client Qdrant, moteur OpenVINO ou
laboratoire. Le runtime métier ``externally-managed`` reste injecté par une
fabrique d'installation explicite.

PostgreSQL demeure l'autorité durable des commandes et graphes. Aucun fichier
JSON, aucune file JSONL et aucun journal de commandes ne remplacent cette
autorité. Les mappings produits sont seulement des projections de contrôle.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
import inspect
import re
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from kernel.scheduler_canonical_continuation import SchedulerCanonicalCycleBound

OPENRC_SCHEDULER_SERVICE_SCHEMA = (
    "missipy.github.research_love_openrc_scheduler_service.v1"
)
OPENRC_SCHEDULER_SERVICE_RECEIPT_SCHEMA = (
    "missipy.github.research_love_openrc_scheduler_service_receipt.v1"
)
OPENRC_SCHEDULER_SERVICE_BUNDLE_SCHEMA = (
    "missipy.github.research_love_openrc_scheduler_service_bundle.v1"
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")


class GitHubResearchLoveOpenRcSchedulerServiceError(RuntimeError):
    """Erreur de propriété du processus ou du Scheduler canonique."""


@runtime_checkable
class CanonicalSchedulerProcess(Protocol):
    """Vue process-local du Scheduler déjà construit par l'installation."""

    @property
    def running(self) -> bool: ...

    async def run(self) -> None: ...

    async def shutdown(self) -> None: ...


@runtime_checkable
class ExternallyManagedResearchRuntime(Protocol):
    """Port du tick métier borné déjà composé par l'installation."""

    async def run_tick(
        self,
        *,
        actor_ref: str,
        cause_ref: str,
        bound: SchedulerCanonicalCycleBound,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class OpenRcSchedulerServiceSettings:
    """Réglages immuables de la boucle coopérative possédée par OpenRC."""

    schema: str = OPENRC_SCHEDULER_SERVICE_SCHEMA
    service_ref: str = "service:autodoc-github-research-scheduler"
    scheduler_ref: str = "scheduler:main"
    actor_ref: str = "actor:openrc-autodoc-scheduler"
    cause_ref: str = "cause:openrc-service-tick"
    poll_interval_seconds: float = 1.0
    max_task_steps: int = 16
    startup_yield_limit: int = 128

    def __post_init__(self) -> None:
        if self.schema != OPENRC_SCHEDULER_SERVICE_SCHEMA:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "schéma de service OpenRC non pris en charge"
            )
        for name, value, prefix in (
            ("service_ref", self.service_ref, "service:"),
            ("scheduler_ref", self.scheduler_ref, "scheduler:"),
            ("actor_ref", self.actor_ref, "actor:"),
            ("cause_ref", self.cause_ref, "cause:"),
        ):
            _require_typed_ref(name, value, prefix)
        if not 0.05 <= self.poll_interval_seconds <= 60.0:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "poll_interval_seconds doit être compris entre 0.05 et 60"
            )
        if isinstance(self.max_task_steps, bool) or not 1 <= self.max_task_steps <= 64:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "max_task_steps doit être compris entre 1 et 64"
            )
        if (
            isinstance(self.startup_yield_limit, bool)
            or not 1 <= self.startup_yield_limit <= 4096
        ):
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "startup_yield_limit doit être compris entre 1 et 4096"
            )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "service_ref": self.service_ref,
                "scheduler_ref": self.scheduler_ref,
                "actor_ref": self.actor_ref,
                "cause_ref": self.cause_ref,
                "poll_interval_seconds": self.poll_interval_seconds,
                "max_task_steps": self.max_task_steps,
                "startup_yield_limit": self.startup_yield_limit,
            }
        )


@dataclass(frozen=True, slots=True)
class OpenRcSchedulerServiceReceipt:
    """Preuve sérialisable de la possession puis de l'arrêt coopératif."""

    schema: str
    service_ref: str
    scheduler_ref: str
    status: str
    started_at: str
    finished_at: str
    tick_count: int
    idle_tick_count: int
    executed_tick_count: int
    scheduler_started_by_service: bool
    scheduler_shutdown_by_service: bool
    scheduler_task_joined: bool
    running_after: bool
    boundaries: Mapping[str, bool]

    def __post_init__(self) -> None:
        if self.schema != OPENRC_SCHEDULER_SERVICE_RECEIPT_SCHEMA:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "schéma de reçu OpenRC non pris en charge"
            )
        _require_typed_ref("service_ref", self.service_ref, "service:")
        _require_typed_ref("scheduler_ref", self.scheduler_ref, "scheduler:")
        if self.status != "stopped":
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le reçu final doit être stopped"
            )
        _require_utc("started_at", self.started_at)
        _require_utc("finished_at", self.finished_at)
        for name, value in (
            ("tick_count", self.tick_count),
            ("idle_tick_count", self.idle_tick_count),
            ("executed_tick_count", self.executed_tick_count),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise GitHubResearchLoveOpenRcSchedulerServiceError(
                    f"{name} doit être un entier positif ou nul"
                )
        if self.idle_tick_count + self.executed_tick_count != self.tick_count:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "les compteurs de ticks divergent"
            )
        if not self.scheduler_started_by_service:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le reçu doit prouver le démarrage du Scheduler"
            )
        if not self.scheduler_shutdown_by_service:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le reçu doit prouver l'arrêt du Scheduler"
            )
        if not self.scheduler_task_joined:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le reçu doit prouver la jointure de Scheduler.run()"
            )
        if self.running_after:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le Scheduler doit être arrêté dans le reçu final"
            )
        object.__setattr__(
            self,
            "boundaries",
            MappingProxyType(dict(self.boundaries)),
        )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "service_ref": self.service_ref,
                "scheduler_ref": self.scheduler_ref,
                "status": self.status,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "tick_count": self.tick_count,
                "idle_tick_count": self.idle_tick_count,
                "executed_tick_count": self.executed_tick_count,
                "scheduler_started_by_service": self.scheduler_started_by_service,
                "scheduler_shutdown_by_service": self.scheduler_shutdown_by_service,
                "scheduler_task_joined": self.scheduler_task_joined,
                "running_after": self.running_after,
                "boundaries": dict(self.boundaries),
            }
        )


@dataclass(slots=True)
class GitHubResearchLoveOpenRcSchedulerService:
    """Boucle coopérative du Scheduler unique possédé par le processus OpenRC."""

    scheduler: CanonicalSchedulerProcess
    runtime: ExternallyManagedResearchRuntime
    settings: OpenRcSchedulerServiceSettings
    clock: Callable[[], str] = field(default=lambda: _utc_now())

    def __post_init__(self) -> None:
        if not isinstance(self.scheduler, CanonicalSchedulerProcess):
            raise TypeError("scheduler ne respecte pas CanonicalSchedulerProcess")
        if not isinstance(self.runtime, ExternallyManagedResearchRuntime):
            raise TypeError("runtime ne respecte pas ExternallyManagedResearchRuntime")
        if not isinstance(self.settings, OpenRcSchedulerServiceSettings):
            raise TypeError("settings doit être OpenRcSchedulerServiceSettings")
        if not callable(self.clock):
            raise TypeError("clock doit être callable")

    async def run(self, stop_event: asyncio.Event) -> OpenRcSchedulerServiceReceipt:
        """Démarre le Scheduler injecté, exécute des ticks et l'arrête en finally."""

        if not isinstance(stop_event, asyncio.Event):
            raise TypeError("stop_event doit être asyncio.Event")
        if self.scheduler.running:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le Scheduler est déjà actif avant la prise de propriété OpenRC"
            )

        started_at = self.clock()
        scheduler_task = asyncio.create_task(
            self.scheduler.run(),
            name="autodoc-canonical-scheduler",
        )
        scheduler_started = False
        scheduler_shutdown = False
        scheduler_joined = False
        tick_count = 0
        idle_count = 0
        executed_count = 0

        try:
            for _ in range(self.settings.startup_yield_limit):
                if self.scheduler.running:
                    scheduler_started = True
                    break
                if scheduler_task.done():
                    await scheduler_task
                await asyncio.sleep(0)
            if not scheduler_started:
                raise GitHubResearchLoveOpenRcSchedulerServiceError(
                    "le Scheduler injecté ne devient pas actif"
                )

            bound = SchedulerCanonicalCycleBound(
                max_task_steps=self.settings.max_task_steps
            )
            while not stop_event.is_set():
                if scheduler_task.done():
                    await scheduler_task
                    raise GitHubResearchLoveOpenRcSchedulerServiceError(
                        "Scheduler.run() s'est terminé avant la demande d'arrêt"
                    )
                report = await self.runtime.run_tick(
                    actor_ref=self.settings.actor_ref,
                    cause_ref=self.settings.cause_ref,
                    bound=bound,
                )
                status = str(getattr(report, "status", ""))
                if status not in {"idle", "cycle-executed"}:
                    raise GitHubResearchLoveOpenRcSchedulerServiceError(
                        "le runtime externe a retourné un statut de tick inconnu"
                    )
                tick_count += 1
                if status == "idle":
                    idle_count += 1
                    await _wait_for_stop(
                        stop_event,
                        timeout=self.settings.poll_interval_seconds,
                    )
                else:
                    executed_count += 1
                    await asyncio.sleep(0)
        finally:
            if self.scheduler.running:
                await self.scheduler.shutdown()
                scheduler_shutdown = True
            await scheduler_task
            scheduler_joined = True

        finished_at = self.clock()
        return OpenRcSchedulerServiceReceipt(
            schema=OPENRC_SCHEDULER_SERVICE_RECEIPT_SCHEMA,
            service_ref=self.settings.service_ref,
            scheduler_ref=self.settings.scheduler_ref,
            status="stopped",
            started_at=started_at,
            finished_at=finished_at,
            tick_count=tick_count,
            idle_tick_count=idle_count,
            executed_tick_count=executed_count,
            scheduler_started_by_service=scheduler_started,
            scheduler_shutdown_by_service=scheduler_shutdown,
            scheduler_task_joined=scheduler_joined,
            running_after=self.scheduler.running,
            boundaries=MappingProxyType(
                {
                    "openrc_owns_process": True,
                    "existing_scheduler_reused": True,
                    "new_scheduler_created": False,
                    "new_dispatcher_created": False,
                    "new_eventbus_created": False,
                    "postgresql_remains_durable_authority": True,
                    "qdrant_remains_projection_and_recall": True,
                    "controlfs_remains_fast_data_plane": True,
                    "internal_json_storage_created": False,
                    "jsonl_queue_created": False,
                }
            ),
        )


CloseCallback = Callable[[], object | Awaitable[object]]


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveOpenRcServiceBundle:
    """Bundle process-local produit par la fabrique d'installation explicite."""

    schema: str
    service: GitHubResearchLoveOpenRcSchedulerService = field(
        repr=False,
        compare=False,
    )
    close_callbacks: tuple[CloseCallback, ...] = field(
        default=(),
        repr=False,
        compare=False,
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != OPENRC_SCHEDULER_SERVICE_BUNDLE_SCHEMA:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "schéma de bundle OpenRC non pris en charge"
            )
        if not isinstance(self.service, GitHubResearchLoveOpenRcSchedulerService):
            raise TypeError("service doit être GitHubResearchLoveOpenRcSchedulerService")
        for callback in self.close_callbacks:
            if not callable(callback):
                raise TypeError("chaque close_callback doit être callable")
        if not self.evidence_refs:
            raise GitHubResearchLoveOpenRcSchedulerServiceError(
                "le bundle doit exposer au moins une preuve d'installation"
            )
        for value in self.evidence_refs:
            _require_typed_ref("evidence_ref", value)

    async def close(self) -> tuple[str, ...]:
        """Ferme les backends injectés en ordre inverse, sans masquer les erreurs."""

        errors: list[str] = []
        for callback in reversed(self.close_callbacks):
            try:
                result = callback()
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # frontière de fermeture opérateur
                errors.append(type(exc).__name__)
        return tuple(errors)

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "service_settings": dict(self.service.settings.to_mapping()),
                "close_callback_count": len(self.close_callbacks),
                "evidence_refs": self.evidence_refs,
                "secret_value_serialized": False,
            }
        )


async def _wait_for_stop(stop_event: asyncio.Event, *, timeout: float) -> None:
    if stop_event.is_set():
        return
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=timeout)
    except TimeoutError:
        return


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _require_typed_ref(name: str, value: object, prefix: str = "") -> None:
    if not isinstance(value, str) or _TYPED_REF_RE.fullmatch(value) is None:
        raise GitHubResearchLoveOpenRcSchedulerServiceError(
            f"{name} doit être une référence typée"
        )
    if prefix and not value.startswith(prefix):
        raise GitHubResearchLoveOpenRcSchedulerServiceError(
            f"{name} doit commencer par {prefix}"
        )


def _require_utc(name: str, value: object) -> None:
    if not isinstance(value, str) or "T" not in value or not value.endswith("Z"):
        raise GitHubResearchLoveOpenRcSchedulerServiceError(
            f"{name} doit être UTC et finir par Z"
        )


__all__ = (
    "OPENRC_SCHEDULER_SERVICE_BUNDLE_SCHEMA",
    "OPENRC_SCHEDULER_SERVICE_RECEIPT_SCHEMA",
    "OPENRC_SCHEDULER_SERVICE_SCHEMA",
    "CanonicalSchedulerProcess",
    "ExternallyManagedResearchRuntime",
    "GitHubResearchLoveOpenRcSchedulerService",
    "GitHubResearchLoveOpenRcSchedulerServiceError",
    "GitHubResearchLoveOpenRcServiceBundle",
    "OpenRcSchedulerServiceReceipt",
    "OpenRcSchedulerServiceSettings",
)
