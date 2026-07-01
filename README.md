# autodoc — Phase 6.1-r1 — SourceCandidate live path

Cette archive reprend Phase 6.1 après mise à jour de `doc/code_rule.md`.

La CLI `source_candidate_intake_cli` n'est plus seulement un chemin direct vers le use-case local. Elle devient un adaptateur opérateur au-dessus d'un chemin Scheduler vivant.

## Chaîne

```text
CLI args
-> SourceCandidateIntakeCommand
-> EventType.SOURCE_CANDIDATE_INTAKE
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> SourceCandidateIntakeHandler
-> SourceCandidateStore JSON réel
-> EventType.SOURCE_CANDIDATE_INTAKE_RESULT
-> Request.reply
-> stdout text/json
```

## Usage inchangé

```bash
PYTHONPATH=src python3 -m context.source_candidate_intake_cli \
  --store-file /tmp/source_candidates.json \
  --title "Inspect artifact-dir local" \
  --body "artifact-dir à analyser" \
  --origin-kind artifact_dir \
  --origin-reference /tmp/autodoc_e5_dry_run
```

Avec sortie JSON et rapport :

```bash
PYTHONPATH=src python3 -m context.source_candidate_intake_cli \
  --store-file /tmp/source_candidates.json \
  --title "Inspect artifact-dir local" \
  --body "artifact-dir à analyser" \
  --origin-kind artifact_dir \
  --origin-reference /tmp/autodoc_e5_dry_run \
  --decision inspect \
  --format json \
  --report-file /tmp/source_candidate_intake_report.json
```

## Frontières

- pas de modification du Scheduler ;
- pas de serveur ;
- pas de daemon/watcher/polling ;
- pas de réseau ;
- pas d'API GitHub ;
- pas de token ;
- pas de Qdrant ;
- pas de LLM ;
- pas d'appel OpenVINO.

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.1-r1 applique le nouvel addendum Phase 6-r1 en ajoutant un chemin Scheduler vivant pour SourceCandidate intake ; aucune règle supplémentaire n'est nécessaire.
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```
