from __future__ import annotations

from collections.abc import Iterable, Mapping

from contracts.replay import ReplayReport, ReplayScenario, ReplayScenarioResult
from observability.replay_sandbox import (
    ReplaySandbox,
    ReplaySandboxConfig,
    ReplaySandboxHandler,
)


class ReplayScenarioRunner:
    """Exécuteur déterministe de scénarios de replay isolés.

    Le runner ne connaît pas le Scheduler et ne publie aucun événement. Il
    transforme chaque ReplayScenario en ReplaySandboxConfig puis agrège les
    résultats dans un ReplayReport immuable.
    """

    def __init__(
        self,
        handlers: Mapping[str, ReplaySandboxHandler] | None = None,
    ) -> None:
        self._handlers: dict[str, ReplaySandboxHandler] = dict(handlers or {})

    def register(self, event_type: str, handler: ReplaySandboxHandler) -> None:
        """Enregistre un handler de simulation partagé par les scénarios."""

        if not event_type:
            raise ValueError("event_type must not be empty")
        self._handlers[event_type] = handler

    def run(self, scenario: ReplayScenario) -> ReplayScenarioResult:
        """Exécute un scénario dans un ReplaySandbox isolé."""

        config = ReplaySandboxConfig(
            max_events=scenario.max_events,
            allowed_types=scenario.allowed_types,
            denied_types=scenario.denied_types,
        )
        sandbox = ReplaySandbox(config=config, handlers=self._handlers)
        return ReplayScenarioResult(
            scenario_name=scenario.name,
            tags=scenario.tags,
            sandbox_result=sandbox.replay(scenario.plan),
        )

    def report(self, scenarios: Iterable[ReplayScenario]) -> ReplayReport:
        """Exécute plusieurs scénarios et produit un rapport immuable."""

        results = tuple(self.run(scenario) for scenario in scenarios)
        return ReplayReport(scenario_results=results)
