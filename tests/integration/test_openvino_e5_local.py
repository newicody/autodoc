from __future__ import annotations

import asyncio
import os

import pytest

from inference.e5_pipeline import (
    MultilingualE5SmallPipelineConfig,
    build_multilingual_e5_small_pipeline,
)
from inference.e5_profile import MultilingualE5SmallLocalConfig


@pytest.mark.integration
def test_multilingual_e5_small_local_openvino_pipeline() -> None:
    """Test réel optionnel du pipeline local multilingual-e5-small.

    Il est volontairement désactivé par défaut pour que la suite reste portable.
    Lancer avec :

    MISSIPY_RUN_OPENVINO_LOCAL=1 \
    MISSIPY_E5_SMALL_DIR=/home/eric/model/openvino/multilingual-e5-small \
    pytest -q tests/integration/test_openvino_e5_local.py
    """

    if os.environ.get("MISSIPY_RUN_OPENVINO_LOCAL") != "1":
        pytest.skip("set MISSIPY_RUN_OPENVINO_LOCAL=1 to run local OpenVINO test")

    pytest.importorskip("openvino")
    pytest.importorskip("transformers")

    local = MultilingualE5SmallLocalConfig()
    if not local.model_path.exists():
        pytest.skip(f"missing OpenVINO model: {local.model_path}")

    bundle = build_multilingual_e5_small_pipeline(
        MultilingualE5SmallPipelineConfig(local=local, require_model_exists=True)
    )
    result = asyncio.run(
        bundle.pipeline.embed_text("query: test de recherche vectorielle pour MissiPy")
    )

    assert bundle.summary.model_exists is True
    assert bundle.summary.backend_registered is True
    assert bundle.summary.tokenizer_registered is True
    assert result.vector.dimension == 384
    assert result.vector.normalized is True
    assert result.vector.pooling == "mean"
    assert result.raw_inputs.token_type_ids is not None
    assert result.inference.metadata["runtime"] == "RealOpenVINORuntime"
