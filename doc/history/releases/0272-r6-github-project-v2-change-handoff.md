# 0272-r6 — GitHub ProjectV2 change handoff

0272-r6 ferme la prochaine section du flux entrant : les changements détectés
localement deviennent des `SourceCandidate` sérialisables, mais restent bloqués
avant ingestion durable.

## Operator command

```bash
PYTHONPATH=src:. python \
  tools/build_github_project_v2_change_handoffs_0272.py \
  --config config/github_project_v2_query_only.example.ini \
  --execute \
  --policy-decision-id policy:0272:project-v2-change-handoff \
  --format summary
```

## Result

```text
github_project_v2_change_handoff_valid=True
external_call_performed=False
sql_write_allowed=False
qdrant_write_allowed=False
remote_mutation_allowed=False
```

## Next gate

0272-r7 devra accepter, rejeter, archiver, promouvoir ou fusionner les candidates
par une décision opérateur explicite avant toute ingestion SQL.
