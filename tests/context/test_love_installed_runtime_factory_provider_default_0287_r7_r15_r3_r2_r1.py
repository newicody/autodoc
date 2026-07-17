from pathlib import Path

from context import love_installed_runtime_factory_0287 as factory


def test_blank_provider_selects_canonical_manual_provider(tmp_path: Path) -> None:
    config = tmp_path / "runtime.ini"
    config.write_text(
        """
[provider]
factory =
[runtime]
schema = missipy.love.installed_runtime_factory_configuration.v1
runtime_ref = runtime:love-installed
[scheduler]
scheduler_ref = scheduler:main
lifecycle = externally-managed
[sql]
authority_ref = sql-authority:context-revisions
base_revision_ref = context-revision:love-base
[projection]
backend_ref = projection:context-revision-sql-authority
[embedding]
backend_ref = openvino:multilingual-e5-small
model_ref = model:multilingual-e5-small
model_revision = installed
dimension = 384
[qdrant]
backend_ref = qdrant:local
collection = autodoc_context_current
[evidence]
refs = config:love-installed-runtime
""".strip()
        + "\n",
        encoding="utf-8",
    )

    settings = factory.load_installed_runtime_factory_settings(config)

    assert settings.provider_ref == factory.DEFAULT_INSTALLED_RUNTIME_PROVIDER
    assert settings.provider_ref == (
        "context.love_manual_installed_runtime_provider_0287:"
        "build_installed_runtime_ports"
    )
