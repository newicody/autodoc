from pathlib import Path


def test_manual_runtime_binding_preserves_architecture_boundaries() -> None:
    config = Path("config/love_installed_runtime.example.ini").read_text(
        encoding="utf-8"
    )
    provider = Path(
        "src/context/love_manual_installed_runtime_provider_0287.py"
    ).read_text(encoding="utf-8")
    readiness = Path(
        "src/context/love_manual_runtime_readiness_0287.py"
    ).read_text(encoding="utf-8")

    assert (
        "context.love_manual_installed_runtime_provider_0287:"
        "build_installed_runtime_ports"
    ) in config
    for marker in (
        "database = autodoc",
        "collection = autodoc_context_current",
        "dimension = 384",
        "distance = Cosine",
        "model_dir = /home/eric/model/openvino/multilingual-e5-small",
        "password_env = AUTODOC_POSTGRES_PASSWORD",
    ):
        assert marker in config
    assert "from kernel.scheduler import Scheduler" not in provider
    assert "Scheduler(" not in provider
    assert "INSERT " not in readiness
    assert "UPDATE " not in readiness
    assert "DELETE " not in readiness
    assert 'method="GET"' in readiness
    assert "secret_value_serialized" in readiness
