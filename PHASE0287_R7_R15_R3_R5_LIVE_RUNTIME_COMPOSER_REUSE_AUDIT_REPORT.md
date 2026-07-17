# Phase 0287-r7-r15-r3-r5 — live runtime composer reuse audit

## Decision

The installed PostgreSQL, Qdrant and OpenVINO readiness is green, but readiness
is not an executable imported-run runtime.  The source audit confirms that the
existing kernel, authority, embedding, Qdrant and laboratory contracts must be
reused.  It also confirms that a truthful tool-bounded composer cannot yet be
introduced because four leaf adapters and one durable SQL seed are absent.

## Reusable surfaces

- `DbApiContextRevisionAuthorityStore` is the SQL-authoritative store required
  by the love memory/evidence/synthesis path.
- `PostgresSqlContextStoreTarget` already describes the PostgreSQL target, but
  no production `psycopg.connect()` factory exists.
- `build_multilingual_e5_small_pipeline()` and
  `MultilingualE5SmallPipelineBundle` are the canonical real E5 construction
  path; `OpenVINOEmbeddingPipeline.embed_text()` is intentionally asynchronous.
- `QdrantClientProjectionExecutor` is the real qdrant-client boundary and owns a
  close surface.
- `QdrantNamedVectorProfile` and `QdrantCollectionProfile` remain the canonical
  named-vector schema; SQL remains authoritative and Qdrant stores references.
- `DenseQueryEmbedder`, `QdrantHybridQueryExecutor` and
  `LoveAnalysisProjectionPort` are the contracts that the live adapters must
  implement.
- Native and collaborative love handler registration functions already exist
  and must be reused with the existing Dispatcher and Scheduler.

## Confirmed gaps

1. No PostgreSQL connection factory opens a DB-API connection for
   `DbApiContextRevisionAuthorityStore`.
2. No production adapter bridges async E5 `embed_text()` to the dense-query
   contract without nesting an event loop.
3. No production Qdrant adapter implements both `search_dense()` and
   `search_sparse()` for the canonical hybrid contract.
4. No production adapter implements `LoveAnalysisProjectionPort.project()` on
   the SQL-authoritative/Qdrant projection path.
5. `context-revision:love-base` is configured but no durable bootstrap seed is
   present in the live composition path.

Test-only fake/demo implementations are not counted as live adapters.

## Locked implementation sequence

```text
0287-r7-r15-r3-r6 PostgreSQL authority live binding and idempotent base seed
0287-r7-r15-r3-r7 asynchronous OpenVINO dense-query adapter alignment
0287-r7-r15-r3-r8 Qdrant hybrid projection/recall adapters and profile readiness
0287-r7-r15-r3-r9 canonical tool-bounded live runtime composer
0287-r7-r15-r3-r10 first live imported Actions preview
```

The sequence may combine adjacent leaf adapters only when tests prove the same
ownership boundary; it must not introduce another Scheduler, Dispatcher,
RuntimeManager, SQL authority or Qdrant executor.

## Non-effects

This audit imports no external runtime, opens no socket or database connection,
loads no model, performs no inference, performs no SQL/Qdrant/GitHub write and
modifies no existing runtime module.

## Code-rule review

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: existing reuse-audit, leaf-adapter and walking-skeleton rules are sufficient
live_path_status: n/a
live_path_uses_real_backend: n/a
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```
