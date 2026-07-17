from __future__ import annotations

import json
from pathlib import Path
import subprocess

from context.love_manual_runtime_configuration_0287 import (
    load_manual_installed_runtime_settings,
)
from context.love_manual_runtime_readiness_0287 import (
    inspect_manual_runtime_readiness,
)


def _settings(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    for name in (
        "openvino_model.xml",
        "openvino_model.bin",
        "openvino_tokenizer.xml",
        "openvino_tokenizer.bin",
    ):
        (model / name).write_bytes(b"x")
    config = tmp_path / "runtime.ini"
    config.write_text(
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
dimension = 384
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
model_dir = {model}
model_xml = {model / 'openvino_model.xml'}
device = CPU
dimension = 384
query_prefix = query:
passage_prefix = passage:
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return load_manual_installed_runtime_settings(config)


def test_combined_readiness_is_read_only_and_secret_free(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    def runner(*args, **kwargs):
        del args, kwargs
        return subprocess.CompletedProcess((), 0, "autodoc|autodoc|autodoc|180000\n", "")

    def loader(request, *, timeout):
        del timeout
        if request.full_url.endswith("/readyz"):
            return 200, b"all shards are ready", {}
        body = {
            "result": {
                "status": "green",
                "points_count": 0,
                "config": {
                    "params": {
                        "vectors": {"size": 384, "distance": "Cosine"}
                    }
                },
            }
        }
        return 200, json.dumps(body).encode(), {}

    def openvino(settings, compile_model):
        del settings
        return {
            "version": "test",
            "available_devices": ("CPU",),
            "configured_device": "CPU",
            "model_read": True,
            "model_compiled": compile_model,
            "inference_performed": False,
        }

    report = inspect_manual_runtime_readiness(
        settings,
        postgresql_runner=runner,
        qdrant_loader=loader,
        openvino_inspector=openvino,
        environment={"AUTODOC_POSTGRES_PASSWORD": "not-serialized"},
    )
    assert report.valid is True
    payload = report.to_mapping()
    assert payload["boundaries"]["sql_write_performed"] is False
    assert payload["boundaries"]["qdrant_write_performed"] is False
    assert "not-serialized" not in json.dumps(payload)
