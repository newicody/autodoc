# 0272-r7 — ProjectV2 SourceCandidate operator gate

R7 ferme la gate locale entre les handoffs r6 et la future ingestion durable.
Il corrige également le readiness : le mode ProjectV2 direct fonctionne sans
installer ni déployer GitHub Actions.

## Command

```bash
PYTHONPATH=src:. python \
  tools/gate_github_project_v2_source_candidate_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --candidate-id ghpv2-... \
  --action promote \
  --reason "accepted by operator" \
  --execute \
  --policy-decision-id policy:0272:source-candidate-gate \
  --format summary
```

## Result

```text
github_project_v2_source_candidate_gate_valid=True
durable_ingestion_allowed=True
durable_ingestion_performed=False
external_call_performed=False
sql_write_performed=False
qdrant_write_performed=False
remote_mutation_allowed=False
```

## Next

0272-r8 consommera uniquement les gate records `promote` ou `merge`, écrira
d'abord dans SQL autoritaire puis projettera dans Qdrant avec `payload.sql_ref`.
