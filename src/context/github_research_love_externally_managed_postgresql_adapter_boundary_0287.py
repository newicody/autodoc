"""Build durable SQL adapters from the shared externally-managed foundation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from context.github_research_love_externally_managed_runtime_0287 import (
    DbApiSchedulerTemporalObservationStore,
)
from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundation,
)
from context.love_postgresql_shared_adapter_port_0287 import (
    LovePostgreSqlSharedAdapterPort,
)

EXTERNALLY_MANAGED_POSTGRESQL_ADAPTER_BOUNDARY_SCHEMA = (
    "missipy.github.research_love_externally_managed_postgresql_adapter_boundary.v1"
)


class GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundaryError(
    RuntimeError
):
    """Raised when the durable SQL adapter boundary cannot fail closed."""


@dataclass(frozen=True, slots=True)
class GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary:
    """Concrete observation adapter plus the shared typed adapter port."""

    schema: str
    adapter_port: LovePostgreSqlSharedAdapterPort = field(
        repr=False,
        compare=False,
    )
    observation_store: DbApiSchedulerTemporalObservationStore = field(
        repr=False,
        compare=False,
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != EXTERNALLY_MANAGED_POSTGRESQL_ADAPTER_BOUNDARY_SCHEMA:
            raise GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundaryError(
                "schéma de frontière PostgreSQL non pris en charge"
            )
        if not isinstance(self.adapter_port, LovePostgreSqlSharedAdapterPort):
            raise TypeError("adapter_port doit être le port PostgreSQL partagé")
        for method_name in ("initialize_schema", "append_many"):
            if not callable(getattr(self.observation_store, method_name, None)):
                raise TypeError(
                    f"observation_store doit exposer {method_name}()"
                )
        if not self.evidence_refs:
            raise GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundaryError(
                "une preuve d'installation PostgreSQL est requise"
            )

    def to_mapping(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "schema": self.schema,
                "evidence_refs": self.evidence_refs,
                "shared_connection_reused": True,
                "observation_store_bound": True,
                "new_postgresql_connection_opened": False,
                "scheduler_created": False,
                "internal_json_storage_created": False,
                "jsonl_queue_created": False,
            }
        )


def build_github_research_love_externally_managed_postgresql_adapter_boundary(
    *,
    foundation: LoveExternallyManagedInstalledBackendFoundation,
) -> GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary:
    """Build the first concrete durable adapter on the owned SQL connection."""

    if not isinstance(foundation, LoveExternallyManagedInstalledBackendFoundation):
        raise TypeError(
            "foundation doit être LoveExternallyManagedInstalledBackendFoundation"
        )
    port = foundation.postgresql_adapter_port
    observation_store = port.build_adapter(
        DbApiSchedulerTemporalObservationStore,
        required_methods=("initialize_schema", "append_many"),
        required_connection_methods=("cursor", "commit"),
        initialize_schema=True,
    )
    if not isinstance(observation_store, DbApiSchedulerTemporalObservationStore):
        raise GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundaryError(
            "le port partagé doit construire le store d'observation attendu"
        )
    return GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary(
        schema=EXTERNALLY_MANAGED_POSTGRESQL_ADAPTER_BOUNDARY_SCHEMA,
        adapter_port=port,
        observation_store=observation_store,
        evidence_refs=(
            "evidence:externally-managed-shared-postgresql-adapter-port-r16-r62",
            "evidence:scheduler-temporal-observation-postgresql-r16-r62",
        ),
    )


__all__ = (
    "EXTERNALLY_MANAGED_POSTGRESQL_ADAPTER_BOUNDARY_SCHEMA",
    "GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundary",
    "GitHubResearchLoveExternallyManagedPostgreSqlAdapterBoundaryError",
    "build_github_research_love_externally_managed_postgresql_adapter_boundary",
)

# Marqueur de fin volontaire : le fichier généré doit rester complet.
