# Qdrant real binding configuration contract — 0283-r2

## Purpose

Define one immutable configuration contract that composes the existing real
Qdrant surfaces selected by the 0283-r1 reuse audit.

```text
reuse_audit_completed: true
existing_suitable_configuration_contract_found: false
existing_executor_reused: true
existing_sql_scope_reused: true
new_runtime_module_added: true
```

The module is a data and validation surface only. It does not inspect the
installed dependency, build a Qdrant client, read an API key, open a socket,
write a point or issue a recall query.

## Reused objects

```text
QdrantClientConnectionConfig
QdrantClientEffectGate
QdrantSqlAuthorityScope
QdrantStrictGrpcTransportPolicy
QdrantProjectionTarget
QdrantProjectionPolicy
```

## Requested operations and effect gate

The requested operations are limited to:

```text
projection
recall
```

By default, the effect gate must exactly match the requested operations:

```text
preview                    -> allow_write=false, allow_search=false
projection                 -> allow_write=true,  allow_search=false
recall                     -> allow_write=false, allow_search=true
projection + recall        -> allow_write=true,  allow_search=true
```

This prevents a binding configured for recall from silently carrying unused
write permission.

## Connection and transport coherence

The contract verifies:

- connection URL and REST administration URL have the same origin;
- credentials are never embedded in the URL;
- connection and transport agree on gRPC preference and port;
- strict data gRPC remains enabled by default;
- compatibility checking remains enabled;
- timeout stays bounded;
- loopback is required by default.

Remote endpoints may be allowed only by explicit policy. They require HTTPS and
an environment-variable name for the API key. The secret value is never read or
serialized by this phase.

## Shared projection policy

The default policy accepts only:

```text
collection: autodoc_context_embeddings
dimension: 384
```

The projection policy must continue to require SQL references and normalized
vectors. This keeps one shared Qdrant projection/recall surface rather than one
Qdrant authority per specialist.

## Boundaries

```text
new_executor_added: false
new_client_factory_added: false
dependency_inspection_performed: false
client_constructed: false
secret_value_serialized: false
network_used: false
qdrant_write_performed: false
qdrant_search_performed: false
sql_write_performed: false
scheduler_modified: false
projects_repository_change_required: false
external_dependencies_added: false
```
