"""OpenVINO embedding readiness for phase 0246.

This module validates the production server embedding configuration for the
OpenVINO multilingual-e5-small path. It is stdlib-only and does not import
OpenVINO, load a model, tokenize text, run inference, or read model files.
"""

from __future__ import annotations

import configparser
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


OPENVINO_EMBEDDING_READINESS_VERSION = "0246.r1"


OPENVINO_EMBEDDING_READINESS_BOUNDARY: dict[str, bool] = {
    "readiness_only": True,
    "imports_openvino": False,
    "imports_transformers": False,
    "loads_model": False,
    "runs_inference": False,
    "reads_model_files": False,
    "writes_postgresql": False,
    "writes_qdrant": False,
    "publishes_events": False,
    "calls_github_api": False,
    "requires_non_stdlib_for_readiness": False,
}


REQUIRED_SECTION = "openvino.embedding.e5_small"
REQUIRED_MODEL_ID = "openvino.embedding.e5-small"
REQUIRED_TOKENIZER = "transformers.multilingual-e5-small"
REQUIRED_DIMENSION = 384
REQUIRED_POOLING = "mean"
REQUIRED_DISTANCE = "cosine"
REQUIRED_QUERY_PREFIX = "query:"
REQUIRED_PASSAGE_PREFIX = "passage:"


@dataclass(frozen=True)
class OpenVINOEmbeddingIssue:
    """One issue in the OpenVINO embedding readiness input."""

    section: str
    field: str
    message: str


@dataclass(frozen=True)
class OpenVINOEmbeddingSpec:
    """OpenVINO embedding shape expected by the production server."""

    model_id: str
    model_dir: str
    model_xml: str
    model_path: str
    tokenizer: str
    device: str
    candidate_devices: tuple[str, ...]
    dimension: int
    normalized: bool
    pooling: str
    qdrant_distance: str
    query_prefix: str
    passage_prefix: str


@dataclass(frozen=True)
class OpenVINOEmbeddingReadinessReport:
    """JSON-compatible OpenVINO embedding readiness report."""

    version: str
    config_path: str
    ready: bool
    embedding: OpenVINOEmbeddingSpec | None
    issues: tuple[OpenVINOEmbeddingIssue, ...]


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def load_embedding_ini(path: Path) -> configparser.ConfigParser:
    """Load the OpenVINO embedding INI with a stdlib parser."""

    parser = configparser.ConfigParser()
    parser.optionxform = str
    with path.open("r", encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def build_openvino_embedding_readiness(config_path: Path) -> OpenVINOEmbeddingReadinessReport:
    """Build OpenVINO embedding readiness from an INI file."""

    parser = load_embedding_ini(config_path)
    issues: list[OpenVINOEmbeddingIssue] = []

    if not parser.has_section(REQUIRED_SECTION):
        return OpenVINOEmbeddingReadinessReport(
            version=OPENVINO_EMBEDDING_READINESS_VERSION,
            config_path=str(config_path),
            ready=False,
            embedding=None,
            issues=(OpenVINOEmbeddingIssue(REQUIRED_SECTION, "*", "missing required section"),),
        )

    section = REQUIRED_SECTION
    required_keys = (
        "model_id",
        "model_dir",
        "model_xml",
        "tokenizer",
        "device",
        "candidate_devices",
        "dimension",
        "normalized",
        "pooling",
        "qdrant_distance",
        "query_prefix",
        "passage_prefix",
    )
    for key in required_keys:
        if not parser.has_option(section, key):
            issues.append(OpenVINOEmbeddingIssue(section, key, "missing required key"))

    model_id = parser.get(section, "model_id", fallback="")
    model_dir = parser.get(section, "model_dir", fallback="")
    model_xml = parser.get(section, "model_xml", fallback="")
    tokenizer = parser.get(section, "tokenizer", fallback="")
    device = parser.get(section, "device", fallback="")
    candidate_devices = _split_csv(parser.get(section, "candidate_devices", fallback=""))
    dimension = parser.getint(section, "dimension", fallback=0)
    normalized = parser.getboolean(section, "normalized", fallback=False)
    pooling = parser.get(section, "pooling", fallback="")
    qdrant_distance = parser.get(section, "qdrant_distance", fallback="")
    query_prefix = parser.get(section, "query_prefix", fallback="")
    passage_prefix = parser.get(section, "passage_prefix", fallback="")

    if model_id != REQUIRED_MODEL_ID:
        issues.append(OpenVINOEmbeddingIssue(section, "model_id", f"must be {REQUIRED_MODEL_ID}"))
    if tokenizer != REQUIRED_TOKENIZER:
        issues.append(OpenVINOEmbeddingIssue(section, "tokenizer", f"must be {REQUIRED_TOKENIZER}"))
    if dimension != REQUIRED_DIMENSION:
        issues.append(OpenVINOEmbeddingIssue(section, "dimension", f"must be {REQUIRED_DIMENSION}"))
    if not normalized:
        issues.append(OpenVINOEmbeddingIssue(section, "normalized", "must be true"))
    if pooling != REQUIRED_POOLING:
        issues.append(OpenVINOEmbeddingIssue(section, "pooling", f"must be {REQUIRED_POOLING}"))
    if qdrant_distance != REQUIRED_DISTANCE:
        issues.append(OpenVINOEmbeddingIssue(section, "qdrant_distance", f"must be {REQUIRED_DISTANCE}"))
    if query_prefix != REQUIRED_QUERY_PREFIX:
        issues.append(OpenVINOEmbeddingIssue(section, "query_prefix", f"must be {REQUIRED_QUERY_PREFIX}"))
    if passage_prefix != REQUIRED_PASSAGE_PREFIX:
        issues.append(OpenVINOEmbeddingIssue(section, "passage_prefix", f"must be {REQUIRED_PASSAGE_PREFIX}"))
    if device and candidate_devices and device not in candidate_devices:
        issues.append(OpenVINOEmbeddingIssue(section, "device", "must be listed in candidate_devices"))
    if model_xml and not model_xml.endswith(".xml"):
        issues.append(OpenVINOEmbeddingIssue(section, "model_xml", "must point to an OpenVINO XML file"))

    model_path = str(Path(model_dir) / model_xml) if model_dir and model_xml else ""
    embedding = OpenVINOEmbeddingSpec(
        model_id=model_id,
        model_dir=model_dir,
        model_xml=model_xml,
        model_path=model_path,
        tokenizer=tokenizer,
        device=device,
        candidate_devices=candidate_devices,
        dimension=dimension,
        normalized=normalized,
        pooling=pooling,
        qdrant_distance=qdrant_distance,
        query_prefix=query_prefix,
        passage_prefix=passage_prefix,
    )

    return OpenVINOEmbeddingReadinessReport(
        version=OPENVINO_EMBEDDING_READINESS_VERSION,
        config_path=str(config_path),
        ready=not issues,
        embedding=embedding,
        issues=tuple(issues),
    )


def openvino_embedding_readiness_to_dict(report: OpenVINOEmbeddingReadinessReport) -> dict[str, Any]:
    """Convert an OpenVINO embedding readiness report to JSON-compatible data."""

    return asdict(report)


def write_openvino_embedding_readiness_report(*, config_path: Path, output_path: Path) -> dict[str, Any]:
    """Build and write the OpenVINO embedding readiness report."""

    report = build_openvino_embedding_readiness(config_path)
    payload = {
        "production_server_openvino_embedding_readiness_written": True,
        "openvino_embedding_readiness": openvino_embedding_readiness_to_dict(report),
        "boundary": dict(OPENVINO_EMBEDDING_READINESS_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
