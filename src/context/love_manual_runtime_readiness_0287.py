"""Read-only readiness checks for the installed PostgreSQL/Qdrant/OpenVINO path."""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import os
from pathlib import Path
import subprocess
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from context.love_manual_runtime_configuration_0287 import (
    ManualInstalledRuntimeSettings,
)

MANUAL_RUNTIME_READINESS_SCHEMA = (
    "missipy.love.manual_installed_runtime_readiness.v1"
)


@dataclass(frozen=True, slots=True)
class BackendReadiness:
    backend: str
    valid: bool
    issues: tuple[str, ...]
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(
            self,
            "evidence",
            MappingProxyType(dict(self.evidence)),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "valid": self.valid,
            "issues": list(self.issues),
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True, slots=True)
class ManualRuntimeReadinessReport:
    schema: str
    valid: bool
    issues: tuple[str, ...]
    postgresql: BackendReadiness
    qdrant: BackendReadiness
    openvino: BackendReadiness
    boundaries: Mapping[str, bool]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "postgresql": self.postgresql.to_mapping(),
            "qdrant": self.qdrant.to_mapping(),
            "openvino": self.openvino.to_mapping(),
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"manual_runtime_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"postgresql={self.postgresql.valid}",
                f"qdrant={self.qdrant.valid}",
                f"openvino={self.openvino.valid}",
                "write_performed=False",
            )
        )


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
UrlLoader = Callable[..., tuple[int, bytes, Mapping[str, str]]]
OpenVINOInspector = Callable[[ManualInstalledRuntimeSettings, bool], Mapping[str, Any]]


def _default_url_loader(
    request: Request,
    *,
    timeout: float,
) -> tuple[int, bytes, Mapping[str, str]]:
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - loopback is validated
        return (
            int(response.status),
            response.read(),
            MappingProxyType(dict(response.headers.items())),
        )


def _safe_error(exc: BaseException) -> str:
    text = str(exc).strip() or type(exc).__name__
    return text.replace("\n", " ")[:300]


def inspect_postgresql_readiness(
    settings: ManualInstalledRuntimeSettings,
    *,
    runner: CommandRunner = subprocess.run,
    environment: Mapping[str, str] | None = None,
) -> BackendReadiness:
    cfg = settings.postgresql
    source = environment if environment is not None else os.environ
    password = str(source.get(cfg.password_env, ""))
    issues: list[str] = []
    if not password:
        issues.append(
            f"PostgreSQL password environment variable {cfg.password_env} is missing"
        )
        return BackendReadiness(
            backend="postgresql",
            valid=False,
            issues=tuple(issues),
            evidence={
                "host": cfg.host,
                "port": cfg.port,
                "database": cfg.database,
                "user": cfg.user,
                "schema": cfg.schema_name,
                "password_env": cfg.password_env,
                "password_loaded": False,
                "secret_value_serialized": False,
                "query_kind": "read-only",
            },
        )

    query = (
        "SELECT current_database(), current_user, current_schema(), "
        "current_setting('server_version_num')"
    )
    env = dict(source)
    env["PGPASSWORD"] = password
    command = (
        "psql",
        "-X",
        "-A",
        "-t",
        "-v",
        "ON_ERROR_STOP=1",
        "--host",
        cfg.host,
        "--port",
        str(cfg.port),
        "--username",
        cfg.user,
        "--dbname",
        cfg.database,
        "--command",
        query,
    )
    try:
        completed = runner(
            command,
            env=env,
            text=True,
            capture_output=True,
            timeout=cfg.connect_timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        issues.append(f"PostgreSQL readiness command failed: {_safe_error(exc)}")
        output = ""
        return_code = -1
    else:
        output = completed.stdout.strip()
        return_code = int(completed.returncode)
        if return_code != 0:
            issues.append(
                "PostgreSQL read-only query failed: "
                + _safe_error(RuntimeError(completed.stderr))
            )

    values = tuple(output.split("|")) if output else ()
    if not issues and len(values) != 4:
        issues.append("PostgreSQL readiness query returned an unexpected shape")
    if not issues:
        database, user, schema_name, version_num = values
        if database != cfg.database:
            issues.append("PostgreSQL current_database differs from configuration")
        if user != cfg.user:
            issues.append("PostgreSQL current_user differs from configuration")
        if schema_name != cfg.schema_name:
            issues.append("PostgreSQL current_schema differs from configuration")
    else:
        database = user = schema_name = version_num = ""

    return BackendReadiness(
        backend="postgresql",
        valid=not issues,
        issues=tuple(issues),
        evidence={
            "host": cfg.host,
            "port": cfg.port,
            "database": database or cfg.database,
            "user": user or cfg.user,
            "schema": schema_name or cfg.schema_name,
            "server_version_num": version_num,
            "password_env": cfg.password_env,
            "password_loaded": True,
            "secret_value_serialized": False,
            "return_code": return_code,
            "query_kind": "read-only",
            "write_performed": False,
        },
    )


def _qdrant_request(
    settings: ManualInstalledRuntimeSettings,
    path: str,
) -> Request:
    cfg = settings.qdrant
    headers = {"Accept": "application/json"}
    if cfg.api_key_env:
        api_key = os.environ.get(cfg.api_key_env, "").strip()
        if api_key:
            headers["api-key"] = api_key
    return Request(cfg.url.rstrip("/") + path, headers=headers, method="GET")


def inspect_qdrant_readiness(
    settings: ManualInstalledRuntimeSettings,
    *,
    loader: UrlLoader = _default_url_loader,
) -> BackendReadiness:
    cfg = settings.qdrant
    issues: list[str] = []
    health_status = 0
    collection_status = 0
    payload: Mapping[str, Any] = {}
    collection_name = (
        cfg.physical_collection
        if cfg.named_vectors_enabled
        else cfg.collection
    )
    try:
        health_status, health_body, _ = loader(
            _qdrant_request(settings, "/readyz"),
            timeout=cfg.timeout_seconds,
        )
        if health_status != 200 or b"ready" not in health_body.lower():
            issues.append("Qdrant /readyz did not report ready")
        collection_status, collection_body, _ = loader(
            _qdrant_request(
                settings,
                "/collections/" + quote(collection_name, safe=""),
            ),
            timeout=cfg.timeout_seconds,
        )
        decoded = json.loads(collection_body.decode("utf-8"))
        result = decoded.get("result") if isinstance(decoded, Mapping) else None
        payload = result if isinstance(result, Mapping) else {}
    except (HTTPError, URLError, OSError, TimeoutError, ValueError) as exc:
        issues.append(f"Qdrant read-only readiness failed: {_safe_error(exc)}")

    config = payload.get("config", {}) if isinstance(payload, Mapping) else {}
    params = config.get("params", {}) if isinstance(config, Mapping) else {}
    vectors = params.get("vectors", {}) if isinstance(params, Mapping) else {}
    sparse_vectors = (
        params.get("sparse_vectors", {})
        if isinstance(params, Mapping)
        else {}
    )
    if not isinstance(vectors, Mapping):
        vectors = {}
    if not isinstance(sparse_vectors, Mapping):
        sparse_vectors = {}

    dense_config: Mapping[str, Any]
    sparse_config: Mapping[str, Any]
    dense_present = True
    sparse_present = False
    if cfg.named_vectors_enabled:
        dense_present = cfg.dense_vector_name in vectors
        sparse_present = cfg.sparse_vector_name in sparse_vectors
        selected_dense = vectors.get(cfg.dense_vector_name)
        selected_sparse = sparse_vectors.get(cfg.sparse_vector_name)
        dense_config = (
            selected_dense if isinstance(selected_dense, Mapping) else {}
        )
        sparse_config = (
            selected_sparse if isinstance(selected_sparse, Mapping) else {}
        )
    elif cfg.vector_name:
        dense_present = cfg.vector_name in vectors
        selected = vectors.get(cfg.vector_name)
        dense_config = selected if isinstance(selected, Mapping) else {}
        sparse_config = {}
    else:
        dense_config = vectors
        sparse_config = {}

    size = dense_config.get("size") if isinstance(dense_config, Mapping) else None
    distance = (
        dense_config.get("distance")
        if isinstance(dense_config, Mapping)
        else None
    )
    status = payload.get("status") if isinstance(payload, Mapping) else None
    if not issues:
        if collection_status != 200:
            issues.append("Qdrant collection readback did not return HTTP 200")
        if status != "green":
            issues.append("Qdrant collection status is not green")
        if int(size or 0) != cfg.dimension:
            issues.append("Qdrant vector dimension differs from 384")
        if str(distance or "").casefold() != cfg.distance.casefold():
            issues.append("Qdrant distance differs from Cosine")
        if cfg.named_vectors_enabled and not dense_present:
            issues.append("Qdrant named dense vector is missing")
        if cfg.named_vectors_enabled and not sparse_present:
            issues.append("Qdrant named sparse vector is missing")

    return BackendReadiness(
        backend="qdrant",
        valid=not issues,
        issues=tuple(issues),
        evidence={
            "url": cfg.url,
            "grpc_port": cfg.grpc_port,
            "collection": cfg.collection,
            "physical_collection": collection_name,
            "collection_alias": cfg.collection_alias,
            "vector_name": cfg.vector_name,
            "dense_vector_name": cfg.dense_vector_name,
            "sparse_vector_name": cfg.sparse_vector_name,
            "named_vectors_enabled": cfg.named_vectors_enabled,
            "dimension": size,
            "distance": distance,
            "sparse_configured": sparse_present,
            "status": status,
            "points_count": payload.get("points_count"),
            "readyz_http_status": health_status,
            "collection_http_status": collection_status,
            "api_key_env": cfg.api_key_env,
            "api_key_loaded": bool(
                cfg.api_key_env and os.environ.get(cfg.api_key_env, "")
            ),
            "secret_value_serialized": False,
            "request_kind": "GET-only",
            "write_performed": False,
        },
    )

def _default_openvino_inspector(
    settings: ManualInstalledRuntimeSettings,
    compile_model: bool,
) -> Mapping[str, Any]:
    cfg = settings.openvino
    module = importlib.import_module("openvino")
    core = module.Core()
    devices = tuple(str(value) for value in core.available_devices)
    evidence: dict[str, Any] = {
        "version": str(getattr(module, "__version__", "")),
        "available_devices": devices,
        "configured_device": cfg.device,
        "model_dir": cfg.model_dir,
        "model_xml": cfg.model_xml,
        "dimension": cfg.dimension,
        "model_read": False,
        "model_compiled": False,
        "inference_performed": False,
    }
    model = core.read_model(cfg.model_xml)
    evidence["model_read"] = True
    evidence["input_count"] = len(model.inputs)
    evidence["output_count"] = len(model.outputs)
    if compile_model:
        compiled = core.compile_model(model, cfg.device)
        evidence["model_compiled"] = True
        evidence["compiled_input_count"] = len(compiled.inputs)
        evidence["compiled_output_count"] = len(compiled.outputs)
    return MappingProxyType(evidence)


def inspect_openvino_readiness(
    settings: ManualInstalledRuntimeSettings,
    *,
    compile_model: bool = True,
    inspector: OpenVINOInspector = _default_openvino_inspector,
) -> BackendReadiness:
    cfg = settings.openvino
    issues: list[str] = []
    model_dir = Path(cfg.model_dir)
    model_xml = Path(cfg.model_xml)
    model_bin = model_xml.with_suffix(".bin")
    tokenizer_xml = model_dir / "openvino_tokenizer.xml"
    tokenizer_bin = model_dir / "openvino_tokenizer.bin"
    for path, label in (
        (model_dir, "model directory"),
        (model_xml, "model XML"),
        (model_bin, "model BIN"),
        (tokenizer_xml, "tokenizer XML"),
        (tokenizer_bin, "tokenizer BIN"),
    ):
        if not path.exists():
            issues.append(f"OpenVINO {label} is missing: {path}")
    evidence: Mapping[str, Any] = {
        "model_dir": cfg.model_dir,
        "model_xml": cfg.model_xml,
        "device": cfg.device,
        "dimension": cfg.dimension,
        "model_read": False,
        "model_compiled": False,
        "inference_performed": False,
    }
    if not issues:
        try:
            evidence = inspector(settings, compile_model)
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            issues.append(f"OpenVINO readiness failed: {_safe_error(exc)}")
    devices = tuple(str(value) for value in evidence.get("available_devices", ()))
    if not issues and cfg.device not in devices:
        issues.append("configured OpenVINO device is not available")
    if not issues and not evidence.get("model_read"):
        issues.append("OpenVINO model was not read")
    if not issues and compile_model and not evidence.get("model_compiled"):
        issues.append("OpenVINO model was not compiled")

    return BackendReadiness(
        backend="openvino",
        valid=not issues,
        issues=tuple(issues),
        evidence={
            **dict(evidence),
            "query_prefix": cfg.query_prefix,
            "passage_prefix": cfg.passage_prefix,
            "write_performed": False,
        },
    )


def inspect_manual_runtime_readiness(
    settings: ManualInstalledRuntimeSettings,
    *,
    compile_openvino_model: bool = True,
    postgresql_runner: CommandRunner = subprocess.run,
    qdrant_loader: UrlLoader = _default_url_loader,
    openvino_inspector: OpenVINOInspector = _default_openvino_inspector,
    environment: Mapping[str, str] | None = None,
) -> ManualRuntimeReadinessReport:
    postgresql = inspect_postgresql_readiness(
        settings,
        runner=postgresql_runner,
        environment=environment,
    )
    qdrant = inspect_qdrant_readiness(settings, loader=qdrant_loader)
    openvino = inspect_openvino_readiness(
        settings,
        compile_model=compile_openvino_model,
        inspector=openvino_inspector,
    )
    issues = tuple(
        f"{backend.backend}: {issue}"
        for backend in (postgresql, qdrant, openvino)
        for issue in backend.issues
    )
    return ManualRuntimeReadinessReport(
        schema=MANUAL_RUNTIME_READINESS_SCHEMA,
        valid=not issues,
        issues=issues,
        postgresql=postgresql,
        qdrant=qdrant,
        openvino=openvino,
        boundaries=MappingProxyType(
            {
                "configuration_read_only": True,
                "postgresql_query_read_only": True,
                "qdrant_get_only": True,
                "openvino_inference_performed": False,
                "sql_write_performed": False,
                "qdrant_write_performed": False,
                "scheduler_constructed": False,
                "secret_value_serialized": False,
            }
        ),
    )


__all__ = (
    "BackendReadiness",
    "MANUAL_RUNTIME_READINESS_SCHEMA",
    "ManualRuntimeReadinessReport",
    "inspect_manual_runtime_readiness",
    "inspect_openvino_readiness",
    "inspect_postgresql_readiness",
    "inspect_qdrant_readiness",
)
# r10-r1 keeps legacy unnamed settings compatible before this readiness boundary.
# r10-r2 keeps manual readiness read-only; SDK normalization stays in inference I/O.
