"""Local server boundary contracts.

Phase 5.17 deliberately does not start a server, bind a socket, call a
framework, or reach the network.  It only describes the loopback server
surface that later phases may implement explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


LocalServerHttpMethod = Literal["GET", "POST"]

_ALLOWED_METHODS: tuple[str, ...] = ("GET", "POST")


@dataclass(frozen=True, slots=True)
class LocalServerEndpoint:
    """Serializable description of one future local server endpoint."""

    name: str
    method: LocalServerHttpMethod
    path: str
    description: str
    request_schema: str
    response_schema: str
    mutates_local_state: bool = False
    implemented: bool = False
    loopback_only: bool = True
    requires_token: bool = False
    external_network: bool = False
    side_effects: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("endpoint name must not be empty")
        if self.method not in _ALLOWED_METHODS:
            raise ValueError("endpoint method is unsupported")
        if not self.path.startswith("/"):
            raise ValueError("endpoint path must be absolute")
        if not self.description.strip():
            raise ValueError("endpoint description must not be empty")
        if not self.request_schema.strip():
            raise ValueError("endpoint request_schema must not be empty")
        if not self.response_schema.strip():
            raise ValueError("endpoint response_schema must not be empty")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "method": self.method,
            "path": self.path,
            "description": self.description,
            "request_schema": self.request_schema,
            "response_schema": self.response_schema,
            "mutates_local_state": self.mutates_local_state,
            "implemented": self.implemented,
            "loopback_only": self.loopback_only,
            "requires_token": self.requires_token,
            "external_network": self.external_network,
            "side_effects": list(self.side_effects),
        }


@dataclass(frozen=True, slots=True)
class LocalServerBoundaryPolicy:
    """Global policy for the future local server boundary."""

    repository: str = "newicody/autodoc"
    implementation_state: str = "contract_only"
    bind_host: str = "127.0.0.1"
    default_port: int = 8765
    loopback_only: bool = True
    external_network_allowed: bool = False
    github_api_allowed: bool = False
    token_allowed: bool = False
    daemon_allowed: bool = False
    scheduler_autoload_allowed: bool = False
    model_execution_allowed: bool = False
    qdrant_allowed: bool = False
    llm_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.repository.strip():
            raise ValueError("repository must not be empty")
        if "/" not in self.repository:
            raise ValueError("repository must use owner/name form")
        if self.bind_host != "127.0.0.1":
            raise ValueError("local server boundary must stay loopback-only")
        if self.default_port <= 0:
            raise ValueError("default_port must be positive")
        if not self.loopback_only:
            raise ValueError("loopback_only must remain true")
        if self.external_network_allowed:
            raise ValueError("external network is not allowed in this boundary")
        if self.github_api_allowed:
            raise ValueError("GitHub API is not allowed in this boundary")
        if self.token_allowed:
            raise ValueError("tokens are not allowed in this boundary")
        if self.daemon_allowed:
            raise ValueError("daemon mode is not allowed in this boundary")
        if self.scheduler_autoload_allowed:
            raise ValueError("Scheduler autoload is not allowed in this boundary")
        if self.model_execution_allowed:
            raise ValueError("model execution is not allowed in this boundary")
        if self.qdrant_allowed:
            raise ValueError("Qdrant is not allowed in this boundary")
        if self.llm_allowed:
            raise ValueError("LLM execution is not allowed in this boundary")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "implementation_state": self.implementation_state,
            "bind_host": self.bind_host,
            "default_port": self.default_port,
            "loopback_only": self.loopback_only,
            "external_network_allowed": self.external_network_allowed,
            "github_api_allowed": self.github_api_allowed,
            "token_allowed": self.token_allowed,
            "daemon_allowed": self.daemon_allowed,
            "scheduler_autoload_allowed": self.scheduler_autoload_allowed,
            "model_execution_allowed": self.model_execution_allowed,
            "qdrant_allowed": self.qdrant_allowed,
            "llm_allowed": self.llm_allowed,
        }


@dataclass(frozen=True, slots=True)
class LocalServerBoundary:
    """Complete serializable contract for the future local HTTP boundary."""

    policy: LocalServerBoundaryPolicy = field(default_factory=LocalServerBoundaryPolicy)
    endpoints: tuple[LocalServerEndpoint, ...] = field(default_factory=tuple)
    schema: str = "missipy.local_server.boundary.v1"

    def __post_init__(self) -> None:
        names = [endpoint.name for endpoint in self.endpoints]
        if len(names) != len(set(names)):
            raise ValueError("endpoint names must be unique")
        paths = [(endpoint.method, endpoint.path) for endpoint in self.endpoints]
        if len(paths) != len(set(paths)):
            raise ValueError("endpoint method/path pairs must be unique")
        for endpoint in self.endpoints:
            if not endpoint.loopback_only:
                raise ValueError("all endpoints must stay loopback-only")
            if endpoint.external_network:
                raise ValueError("endpoints must not use external network")
            if endpoint.requires_token:
                raise ValueError("endpoints must not require tokens in this contract")

    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)

    @property
    def endpoint_names(self) -> tuple[str, ...]:
        return tuple(endpoint.name for endpoint in self.endpoints)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "policy": self.policy.to_json_dict(),
            "endpoint_count": self.endpoint_count,
            "endpoint_names": list(self.endpoint_names),
            "endpoints": [endpoint.to_json_dict() for endpoint in self.endpoints],
        }

    def to_text(self) -> str:
        lines = [
            "Local server boundary",
            f"repository: {self.policy.repository}",
            f"state: {self.policy.implementation_state}",
            f"bind: {self.policy.bind_host}:{self.policy.default_port}",
            f"endpoints: {self.endpoint_count}",
            "network: disabled except future loopback implementation",
            "github_api: disabled",
            "tokens: disabled",
            "scheduler_autoload: disabled",
            "model_execution: disabled",
        ]
        for endpoint in self.endpoints:
            state = "implemented" if endpoint.implemented else "contract-only"
            lines.append(f"- {endpoint.method} {endpoint.path} [{endpoint.name}] {state}")
        return "\n".join(lines)


def default_local_server_endpoints() -> tuple[LocalServerEndpoint, ...]:
    """Return the planned local server endpoints without implementing HTTP."""

    return (
        LocalServerEndpoint(
            name="status_get",
            method="GET",
            path="/status",
            description="Read passive local runtime status.",
            request_schema="missipy.local_server.empty_request.v1",
            response_schema="missipy.local_server.status_response.v1",
        ),
        LocalServerEndpoint(
            name="source_candidate_create",
            method="POST",
            path="/source-candidates",
            description="Create or preview a local SourceCandidate through an explicit future boundary.",
            request_schema="missipy.source_candidate.input.v1",
            response_schema="missipy.source_candidate.creation_result.v1",
            mutates_local_state=True,
            side_effects=("future_explicit_store_write",),
        ),
        LocalServerEndpoint(
            name="source_candidate_decide",
            method="POST",
            path="/source-candidates/{candidate_id}/decision",
            description="Apply a human decision to one local SourceCandidate through an explicit future boundary.",
            request_schema="missipy.source_candidate.decision.v1",
            response_schema="missipy.source_candidate.decision_result.v1",
            mutates_local_state=True,
            side_effects=("future_explicit_store_write",),
        ),
        LocalServerEndpoint(
            name="e5_context_intake",
            method="POST",
            path="/context/e5/intake",
            description="Attach an existing Phase 4 artifact-dir to ContextEngine through explicit intake.",
            request_schema="missipy.e5.local_context_runtime.request.v1",
            response_schema="missipy.e5.context_engine_status.v1",
            mutates_local_state=True,
            side_effects=("future_context_engine_last_context_update",),
        ),
        LocalServerEndpoint(
            name="report_get",
            method="GET",
            path="/reports/{report_id}",
            description="Read a local report by explicit identifier in a future implementation.",
            request_schema="missipy.local_server.report_lookup.v1",
            response_schema="missipy.local_server.report_response.v1",
        ),
    )


def build_local_server_boundary(
    policy: LocalServerBoundaryPolicy | None = None,
    endpoints: tuple[LocalServerEndpoint, ...] | None = None,
) -> LocalServerBoundary:
    """Build the default contract-only local server boundary."""

    return LocalServerBoundary(
        policy=policy or LocalServerBoundaryPolicy(),
        endpoints=endpoints if endpoints is not None else default_local_server_endpoints(),
    )
