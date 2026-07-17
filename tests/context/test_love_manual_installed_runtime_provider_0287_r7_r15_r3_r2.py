from __future__ import annotations

import pytest

import context.love_manual_installed_runtime_provider_0287 as provider


def test_provider_fails_closed_without_live_registered_ports(monkeypatch) -> None:
    monkeypatch.setattr(provider, "_REGISTERED_PORTS", None)
    with pytest.raises(
        provider.ManualInstalledRuntimeProviderError,
        match="no installed",
    ):
        provider.get_registered_installed_runtime_ports()
