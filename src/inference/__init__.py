from __future__ import annotations

from .adapter import InferenceAdapter
from .backend import DummyInferenceBackend
from .e5_profile import (
    MULTILINGUAL_E5_SMALL_DEFAULT_DIR,
    MULTILINGUAL_E5_SMALL_ENV,
    MULTILINGUAL_E5_SMALL_PROFILE_NAME,
    MULTILINGUAL_E5_SMALL_TOKENIZER_NAME,
    MultilingualE5SmallLocalConfig,
)
from .transformers_tokenizer import (
    TransformersAutoTokenizer,
    TransformersTokenizerAdapterConfig,
)
from .e5_pipeline import (
    MultilingualE5SmallPipelineBundle,
    MultilingualE5SmallPipelineBuildSummary,
    MultilingualE5SmallPipelineConfig,
    MultilingualE5SmallPipelineFactory,
    build_multilingual_e5_small_pipeline,
)

from .e5_cli import (
    E5CliOutput,
    build_parser as build_e5_cli_parser,
    main as e5_cli_main,
    run as run_e5_cli,
    run_async as run_e5_cli_async,
)

from .e5_rank_cli import (
    E5RankCliOutput,
    E5RankCliPassageOutput,
    build_parser as build_e5_rank_cli_parser,
    main as e5_rank_cli_main,
    run as run_e5_rank_cli,
    run_async as run_e5_rank_cli_async,
)

from .e5_corpus_cli import (
    E5CorpusBuildCliOutput,
    E5CorpusSearchCliOutput,
    build_build_parser as build_e5_corpus_cli_parser,
    build_search_parser as search_e5_corpus_cli_parser,
    build_main as e5_corpus_build_main,
    search_main as e5_corpus_search_main,
    run_build as run_e5_corpus_build_cli,
    run_search as run_e5_corpus_search_cli,
)


from .e5_rebuild_cli import (
    E5CorpusRebuildCliOutput,
    E5CorpusRebuildValidation,
    build_rebuild_parser as rebuild_e5_corpus_cli_parser,
    rebuild_main as e5_corpus_rebuild_main,
    rebuild_staging_path,
    run_rebuild as run_e5_corpus_rebuild_cli,
)

from .e5_text import (
    E5_PASSAGE_PREFIX,
    E5_PASSAGE_ROLE,
    E5_QUERY_PREFIX,
    E5_QUERY_ROLE,
    SUPPORTED_E5_TEXT_ROLES,
    E5Text,
    detect_e5_role,
    ensure_e5_text,
)
from .e5_ranker import (
    E5LocalRanker,
    E5RankedPassage,
    E5RankedResults,
    E5Similarity,
    dot_product,
)


from .e5_search_report import (
    E5SearchReport,
    E5SearchReportConfig,
    E5SearchReportHit,
    E5SearchSourceContext,
    make_excerpt,
)

from .e5_sources import (
    SUPPORTED_E5_SOURCE_EXTENSIONS,
    E5SourceDocument,
    E5TextChunk,
    chunk_e5_source_document,
    chunk_e5_sources,
    discover_e5_source_files,
    load_e5_corpus_documents_from_sources,
    load_e5_source_documents,
)


from .e5_incremental import (
    E5IncrementalBuildResult,
    E5IncrementalBuildStats,
    E5IncrementalCorpusBuilder,
    embedding_matches_document,
    make_e5_document_hash,
    reuse_embedding,
)

from .e5_corpus_lock import (
    E5CorpusBuildLock,
    E5CorpusBuildLockError,
    E5CorpusBuildLockInfo,
    build_e5_corpus_lock_path,
)

from .e5_corpus import (
    E5CorpusBuilder,
    E5CorpusDocument,
    E5CorpusEmbedding,
    E5CorpusIndex,
    E5CorpusJsonStore,
    E5CorpusSearcher,
    E5CorpusSearchHit,
    E5CorpusSearchResults,
    make_corpus_document_id,
)
from .embedding_pipeline import (
    OpenVINOEmbeddingPipeline,
    OpenVINOEmbeddingPipelineConfig,
    OpenVINOEmbeddingPipelineResult,
)
from .simple_tokenizer import (
    DeterministicTokenizer,
    register_deterministic_test_tokenizer,
)
from .embedding_raw import (
    OpenVINOEmbeddingOutputAdapter,
    OpenVINOEmbeddingOutputConfig,
    OpenVINOEmbeddingRawInputs,
    OpenVINOEmbeddingVector,
)
from .embedding_profile import (
    DEFAULT_EMBEDDING_INPUT_NAMES,
    DEFAULT_EMBEDDING_OUTPUT_NAMES,
    SUPPORTED_EMBEDDING_POOLING,
    OpenVINOEmbeddingProfileConfig,
    register_openvino_embedding_profile,
)
from .handlers import InferenceRequestHandler
from .model_profile import (
    OpenVINOModelProfile,
    OpenVINOModelProfileRegistry,
    OpenVINOModelProfileRegistrySnapshot,
    SUPPORTED_OPENVINO_TASKS,
)
from .openvino_factory import (
    OpenVINOBackendBuildResult,
    OpenVINOBackendFactory,
    OpenVINORuntimeFactory,
)
from .openvino_backend import (
    OpenVINOBackend,
    OpenVINOBackendConfig,
    OpenVINOBackendError,
    OpenVINOBackendState,
    OpenVINORuntime,
)
from .openvino_runtime import (
    RealOpenVINORuntime,
    RealOpenVINORuntimeError,
    RealOpenVINORuntimeState,
    RealOpenVINORuntimeUnavailable,
)

from .tokenizer_contract import (
    SUPPORTED_TOKENIZER_PADDING,
    SUPPORTED_TOKENIZER_TRUNCATION,
    TextTokenizer,
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
    TokenizerRegistry,
    TokenizerRegistrySnapshot,
)
from .registry import BackendRegistry, BackendRegistrySnapshot

__all__ = [
    "MULTILINGUAL_E5_SMALL_DEFAULT_DIR",
    "MULTILINGUAL_E5_SMALL_ENV",
    "MULTILINGUAL_E5_SMALL_PROFILE_NAME",
    "MULTILINGUAL_E5_SMALL_TOKENIZER_NAME",
    "MultilingualE5SmallLocalConfig",
    "TransformersAutoTokenizer",
    "TransformersTokenizerAdapterConfig",
    "MultilingualE5SmallPipelineBundle",
    "MultilingualE5SmallPipelineBuildSummary",
    "MultilingualE5SmallPipelineConfig",
    "MultilingualE5SmallPipelineFactory",
    "build_multilingual_e5_small_pipeline",
    "E5CliOutput",
    "build_e5_cli_parser",
    "e5_cli_main",
    "run_e5_cli",
    "run_e5_cli_async",
    "E5RankCliOutput",
    "E5RankCliPassageOutput",
    "build_e5_rank_cli_parser",
    "e5_rank_cli_main",
    "run_e5_rank_cli",
    "run_e5_rank_cli_async",
    "E5CorpusBuildCliOutput",
    "E5CorpusSearchCliOutput",
    "build_e5_corpus_cli_parser",
    "search_e5_corpus_cli_parser",
    "e5_corpus_build_main",
    "e5_corpus_search_main",
    "run_e5_corpus_build_cli",
    "run_e5_corpus_search_cli",
    "E5CorpusRebuildCliOutput",
    "E5CorpusRebuildValidation",
    "rebuild_e5_corpus_cli_parser",
    "e5_corpus_rebuild_main",
    "rebuild_staging_path",
    "run_e5_corpus_rebuild_cli",
    "E5_PASSAGE_PREFIX",
    "E5_PASSAGE_ROLE",
    "E5_QUERY_PREFIX",
    "E5_QUERY_ROLE",
    "SUPPORTED_E5_TEXT_ROLES",
    "E5Text",
    "detect_e5_role",
    "ensure_e5_text",
    "E5LocalRanker",
    "E5RankedPassage",
    "E5RankedResults",
    "E5Similarity",
    "dot_product",
    "E5SearchReport",
    "E5SearchReportConfig",
    "E5SearchReportHit",
    "E5SearchSourceContext",
    "make_excerpt",
    "SUPPORTED_E5_SOURCE_EXTENSIONS",
    "E5SourceDocument",
    "E5TextChunk",
    "chunk_e5_source_document",
    "chunk_e5_sources",
    "discover_e5_source_files",
    "load_e5_corpus_documents_from_sources",
    "load_e5_source_documents",
    "E5CorpusBuildLock",
    "E5CorpusBuildLockError",
    "E5CorpusBuildLockInfo",
    "build_e5_corpus_lock_path",
    "E5CorpusBuilder",
    "E5CorpusDocument",
    "E5CorpusEmbedding",
    "E5CorpusIndex",
    "E5CorpusJsonStore",
    "E5CorpusSearcher",
    "E5CorpusSearchHit",
    "E5CorpusSearchResults",
    "make_corpus_document_id",
    "E5IncrementalBuildResult",
    "E5IncrementalBuildStats",
    "E5IncrementalCorpusBuilder",
    "embedding_matches_document",
    "make_e5_document_hash",
    "reuse_embedding",
    "DEFAULT_EMBEDDING_INPUT_NAMES",
    "DEFAULT_EMBEDDING_OUTPUT_NAMES",
    "DeterministicTokenizer",
    "SUPPORTED_EMBEDDING_POOLING",
    "OpenVINOEmbeddingPipeline",
    "OpenVINOEmbeddingPipelineConfig",
    "OpenVINOEmbeddingPipelineResult",
    "OpenVINOEmbeddingOutputAdapter",
    "OpenVINOEmbeddingOutputConfig",
    "OpenVINOEmbeddingRawInputs",
    "OpenVINOEmbeddingVector",
    "OpenVINOEmbeddingProfileConfig",
    "register_openvino_embedding_profile",
    "register_deterministic_test_tokenizer",
    "BackendRegistry",
    "BackendRegistrySnapshot",
    "DummyInferenceBackend",
    "InferenceAdapter",
    "InferenceRequestHandler",
    "OpenVINOBackendBuildResult",
    "OpenVINOBackendFactory",
    "OpenVINORuntimeFactory",
    "OpenVINOBackend",
    "OpenVINOBackendConfig",
    "OpenVINOBackendError",
    "OpenVINOBackendState",
    "OpenVINORuntime",
    "SUPPORTED_OPENVINO_TASKS",
    "SUPPORTED_TOKENIZER_PADDING",
    "SUPPORTED_TOKENIZER_TRUNCATION",
    "TextTokenizer",
    "TokenizationRequest",
    "TokenizationResult",
    "TokenizerConfig",
    "TokenizerRegistry",
    "TokenizerRegistrySnapshot",
    "OpenVINOModelProfileRegistrySnapshot",
    "OpenVINOModelProfileRegistry",
    "OpenVINOModelProfile",
    "RealOpenVINORuntime",
    "RealOpenVINORuntimeError",
    "RealOpenVINORuntimeState",
    "RealOpenVINORuntimeUnavailable",
]
