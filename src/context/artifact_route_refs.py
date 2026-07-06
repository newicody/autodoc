"""Pure dynamic route refs for local artifact vector indexing.

0147 derives Scheduler/RouteProxy refs from the 0146 artifact intake contract
instead of keeping static smoke refs from phases 0143/0144.  This module is a
pure contract helper: it does not import Scheduler, RouteProxy, OpenVINO,
Qdrant, or SQL clients and it performs no IO.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ArtifactRouteRefs:
    """Dynamic refs derived from artifact and vector indexing job refs."""

    artifact_ref: str
    vector_indexing_job_ref: str
    artifact_slug: str
    job_slug: str
    command_ref: str
    request_route_ref: str
    result_command_ref: str
    result_route_ref: str
    result_owner_ref: str
    route_namespace: str
    result_route_namespace: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "artifact_ref": self.artifact_ref,
            "vector_indexing_job_ref": self.vector_indexing_job_ref,
            "artifact_slug": self.artifact_slug,
            "job_slug": self.job_slug,
            "command_ref": self.command_ref,
            "request_route_ref": self.request_route_ref,
            "result_command_ref": self.result_command_ref,
            "result_route_ref": self.result_route_ref,
            "result_owner_ref": self.result_owner_ref,
            "route_namespace": self.route_namespace,
            "result_route_namespace": self.result_route_namespace,
            "boundary": "pure artifact route refs; Scheduler/RouteProxy/OpenVINO/Qdrant stay outside",
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "ArtifactRouteRefs":
        return build_artifact_route_refs(
            artifact_ref=str(data["artifact_ref"]),
            vector_indexing_job_ref=str(data["vector_indexing_job_ref"]),
        )


def build_artifact_route_refs(*, artifact_ref: str, vector_indexing_job_ref: str) -> ArtifactRouteRefs:
    """Derive dynamic request/result refs from typed artifact fields."""

    artifact_ref = _require_prefix("artifact_ref", artifact_ref.strip(), "artifact:")
    vector_indexing_job_ref = _require_prefix(
        "vector_indexing_job_ref",
        vector_indexing_job_ref.strip(),
        "vector-indexing-job:",
    )
    artifact_slug = _slug_from_ref(artifact_ref, prefix="artifact:")
    job_slug = _slug_from_ref(vector_indexing_job_ref, prefix="vector-indexing-job:")
    route_stem = f"artifact/{artifact_slug}/job/{job_slug}"
    namespace_stem = f"artifact-{artifact_slug}-job-{job_slug}"
    return ArtifactRouteRefs(
        artifact_ref=artifact_ref,
        vector_indexing_job_ref=vector_indexing_job_ref,
        artifact_slug=artifact_slug,
        job_slug=job_slug,
        command_ref=f"scheduler-command:{route_stem}/embedding-request",
        request_route_ref=f"vector-route:{route_stem}/embedding-request",
        result_command_ref=f"scheduler-command:{route_stem}/indexing-result",
        result_route_ref=f"vector-route:{route_stem}/indexing-result",
        result_owner_ref=f"worker:local-vector-indexing-smoke/{route_stem}",
        route_namespace=f"autodoc-{namespace_stem}-request",
        result_route_namespace=f"autodoc-{namespace_stem}-result",
    )


def _slug_from_ref(value: str, *, prefix: str) -> str:
    value = value[len(prefix):]
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower()
    if not slug:
        raise ValueError("ref slug must be non-empty")
    return slug[:96]


def _require_prefix(field: str, value: str, prefix: str) -> str:
    if not value:
        raise ValueError(f"{field} must be non-empty")
    if not value.startswith(prefix):
        raise ValueError(f"{field} must start with {prefix!r}")
    return value
