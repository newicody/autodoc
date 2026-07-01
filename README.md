# autodoc — Phase 6.1 — SourceCandidate intake CLI

Cette archive démarre la Phase 6 avec une bordure CLI locale pour créer ou
remplacer une `SourceCandidate` dans le store JSON atomique introduit en Phase
5.15.

## Usage

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
code_rule_reason: 6.1 ajoute une bordure CLI manuelle autour des contrats SourceCandidate existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
