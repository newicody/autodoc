# Runbook d'acceptation réelle — 0287 r16-r50

Cette procédure doit être exécutée sur le serveur local après création d'une
nouvelle Issue `Recherche` dans `newicody/projects`.

## 1. Produire les rapports existants

Conserver les quatre preuves suivantes :

```text
/tmp/autodoc-r50-fetch.json
/tmp/autodoc-r50-prepared.json
/tmp/autodoc-r50-completed.json
/tmp/autodoc-r50-observations.csv
```

Le fetch doit provenir du mode `--execute`. La préparation doit s'arrêter au
digest. La complétion doit réutiliser exactement ce digest.

## 2. Exporter les observations PostgreSQL

Exemple, en remplaçant la référence de commande :

```bash
psql -X --csv -d autodoc -c "
SELECT
  observation_ref,
  scheduler_ref,
  command_ref,
  task_ref,
  handler_ref,
  capability_ref,
  phase,
  occurred_at,
  result_ref,
  attempt
FROM scheduler_handler_temporal_observations
WHERE command_ref = 'scheduler-command:...'
ORDER BY occurred_at, observation_ref
" > /tmp/autodoc-r50-observations.csv
```

## 3. Exécuter la porte finale

```bash
PYTHONPATH=src:. python   tools/validate_github_research_love_end_to_end_0287.py   --repository newicody/projects   --issue-number "$ISSUE_NUMBER"   --run-id "$RUN_ID"   --fetch-cycle-report /tmp/autodoc-r50-fetch.json   --prepared-report /tmp/autodoc-r50-prepared.json   --completed-report /tmp/autodoc-r50-completed.json   --temporal-observations-csv /tmp/autodoc-r50-observations.csv   --output /tmp/autodoc-r50-acceptance.json   --format summary
```

Le résultat final attendu est :

```text
valid=true status=accepted
```

Cette commande ne réalise aucune mutation GitHub et ne relance aucun handler.
