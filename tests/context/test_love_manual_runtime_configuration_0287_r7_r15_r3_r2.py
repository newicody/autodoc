from __future__ import annotations

from pathlib import Path

import pytest

from context.love_manual_runtime_configuration_0287 import (
    ManualRuntimeConfigurationError,
    load_manual_installed_runtime_settings,
)


def _write(path: Path, *, dimension: int = 384) -> None:
    path.write_text(
        f"""
[manual-runtime]
schema = missipy.love.manual_installed_runtime_configuration.v1
[runtime]
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
[qdrant]
backend_ref = qdrant:local
url = http://127.0.0.1:6333
grpc_port = 6334
collection = autodoc_context_current
vector_name =
dimension = {dimension}
distance = Cosine
[postgresql]
host = 127.0.0.1
port = 5432
database = autodoc
user = autodoc
password_env = AUTODOC_POSTGRES_PASSWORD
sslmode = disable
schema = autodoc
[openvino]
model_dir = /models/e5
model_xml = /models/e5/openvino_model.xml
device = CPU
dimension = 384
query_prefix = query:
passage_prefix = passage:
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_manual_configuration_loads_local_backends(tmp_path: Path) -> None:
    path = tmp_path / "runtime.ini"
    _write(path)
    settings = load_manual_installed_runtime_settings(path)
    assert settings.postgresql.database == "autodoc"
    assert settings.qdrant.collection == "autodoc_context_current"
    assert settings.qdrant.dimension == 384
    assert settings.openvino.dimension == 384
    assert settings.scheduler_lifecycle == "externally-managed"
    assert "password" not in settings.to_public_mapping()["postgresql"]


def test_manual_configuration_rejects_non_e5_collection(tmp_path: Path) -> None:
    path = tmp_path / "runtime.ini"
    _write(path, dimension=4)
    with pytest.raises(ManualRuntimeConfigurationError, match="dimension 384"):
        load_manual_installed_runtime_settings(path)
