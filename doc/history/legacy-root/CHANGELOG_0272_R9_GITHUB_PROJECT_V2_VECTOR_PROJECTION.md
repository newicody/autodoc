# Changelog — 0272-r9 ProjectV2 vector projection

## Added

- immutable `EmbeddingSpaceProfile` and deterministic `profile_ref`;
- strict compatibility gate for model, tokenizer, role, dimension and normalization;
- composition of existing 0261 and 0262 surfaces;
- `embedding_profile_ref` propagation into Qdrant point payloads;
- real qdrant-client CLI binding through the existing 0271 membrane;
- focused context, CLI and rule tests;
- architecture, graph, release, manifest and test report.

## Boundaries

- SQL remains authority;
- no SQL write in r9;
- no external embedding accepted into the local E5 collection;
- no GitHub mutation;
- no laboratory selection;
- no Scheduler.run or SHM modification;
- no new non-stdlib dependency.

## Fixed in r9-r2

- discard empty optional embedding metadata before the existing 0262 builder;
- preserve the strict non-empty metadata contract of `OpenVINOEmbeddingVector`;
- add a regression test for an omitted local `model_path`.
