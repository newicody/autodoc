from __future__ import annotations

from pathlib import Path
from types import MappingProxyType, ModuleType, SimpleNamespace
import sys

import pytest

import context.love_installed_runtime_factory_0287 as factory


def _write_config(path: Path, *, provider: str = "installed_provider:build") -> None:
    path.write_text(
        f"""
[provider]
factory = {provider}
[runtime]
schema = {factory.INSTALLED_RUNTIME_FACTORY_SCHEMA}
runtime_ref = runtime:love-installed
[scheduler]
scheduler_ref = scheduler:main
lifecycle = externally-managed
[sql]
authority_ref = sql-authority:context-revisions
base_revision_ref = context-revision:love-base
[projection]
backend_ref = projection:sql-authority
[embedding]
backend_ref = openvino:multilingual-e5-small
model_ref = model:multilingual-e5-small
model_revision = 2026-07
dimension = 384
[qdrant]
backend_ref = qdrant:local
collection = autodoc_context_e5_384
[evidence]
refs = evidence:openvino-model, evidence:qdrant-collection
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_settings_are_loaded_from_one_local_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "love.ini"
    _write_config(config)
    monkeypatch.setenv(factory.INSTALLED_RUNTIME_CONFIG_ENV, str(config))

    settings = factory.load_installed_runtime_factory_settings()

    assert settings.provider_ref == "installed_provider:build"
    assert settings.scheduler_lifecycle == "externally-managed"
    assert settings.embedding_dimension == 384
    assert settings.qdrant_collection == "autodoc_context_e5_384"
    assert settings.evidence_refs == (
        "evidence:openvino-model",
        "evidence:qdrant-collection",
    )


def test_missing_config_has_operator_facing_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing.ini"
    monkeypatch.setenv(factory.INSTALLED_RUNTIME_CONFIG_ENV, str(missing))

    with pytest.raises(factory.InstalledRuntimeFactoryError, match="Copy config"):
        factory.load_installed_runtime_factory_settings()


def test_non_real_provider_markers_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "love.ini"
    _write_config(config, provider="tests.fake_runtime:build")
    monkeypatch.setenv(factory.INSTALLED_RUNTIME_CONFIG_ENV, str(config))

    with pytest.raises(factory.InstalledRuntimeFactoryError, match="non-real"):
        factory.load_installed_runtime_factory_settings()


def test_provider_mapping_is_composed_into_existing_runtime_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "love.ini"
    _write_config(config)
    monkeypatch.setenv(factory.INSTALLED_RUNTIME_CONFIG_ENV, str(config))
    provider_module = ModuleType("installed_provider")
    ports = {
        "scheduler": object(),
        "dispatcher": object(),
        "authority_store": object(),
        "projection_port": object(),
        "collection": SimpleNamespace(collection_name="autodoc_context_e5_384"),
        "embedder": object(),
        "executor": object(),
    }
    provider_module.build = lambda **_: MappingProxyType(ports)
    monkeypatch.setitem(sys.modules, "installed_provider", provider_module)

    seen = {}

    class Attestation:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            seen["attestation"] = kwargs

    class RuntimePorts:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            seen["ports"] = kwargs

    monkeypatch.setattr(factory, "ImportedActionsRealBackendAttestation", Attestation)
    monkeypatch.setattr(factory, "ImportedActionsRuntimePorts", RuntimePorts)
    monkeypatch.setattr(
        factory, "validate_imported_actions_runtime_ports", lambda value: value
    )

    result = factory.build_runtime(
        repository="newicody/projects",
        run_id=123,
        request_payload=MappingProxyType({"issue_number": 42}),
        runtime_context=MappingProxyType({"cycle_ref": "cycle:42"}),
        created_at="2026-07-17T00:00:00Z",
    )

    assert result.schema == factory.IMPORTED_ACTIONS_RUNTIME_PORTS_SCHEMA
    assert result.runtime_ref == "runtime:love-installed"
    assert result.scheduler is ports["scheduler"]
    assert result.base_revision_ref == "context-revision:love-base"
    assert result.scheduler_lifecycle == "externally-managed"
    assert seen["attestation"]["schema"] == factory.IMPORTED_ACTIONS_REAL_BACKEND_ATTESTATION_SCHEMA
    assert seen["attestation"]["embedding_dimension"] == 384
    assert seen["attestation"]["scheduler_contract_reused"] is True
    assert seen["attestation"]["sql_authority_reused"] is True
    assert seen["attestation"]["openvino_e5_real"] is True
    assert seen["attestation"]["qdrant_write_real"] is True
    assert seen["attestation"]["qdrant_returns_references_only"] is True


def test_provider_must_return_every_existing_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "love.ini"
    _write_config(config)
    monkeypatch.setenv(factory.INSTALLED_RUNTIME_CONFIG_ENV, str(config))
    provider_module = ModuleType("installed_provider")
    provider_module.build = lambda **_: {"scheduler": object()}
    monkeypatch.setitem(sys.modules, "installed_provider", provider_module)
    monkeypatch.setattr(
        factory,
        "ImportedActionsRealBackendAttestation",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )

    with pytest.raises(factory.InstalledRuntimeFactoryError, match="dispatcher"):
        factory.build_runtime(
            repository="newicody/projects",
            run_id=123,
            request_payload={},
            runtime_context={},
            created_at="2026-07-17T00:00:00Z",
        )
