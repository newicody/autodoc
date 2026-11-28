# GitHub Actions ready-run → Copilot v2 ProjectV2 projection — 0287 r16-r4

## But

Rendre visible l’avis Copilot déjà produit et déjà récupéré dans le champ
ProjectV2 configuré comme `Avis Copilot`, sans télécharger une seconde fois les
artefacts et sans réimplémenter les adaptateurs v2 existants.

## Composition

```text
scan-once report ready_runs
  -> durable raw dataset (exactly three artifact IDs)
  -> existing build_copilot_advisory_v2_publication_preview.py
  -> existing project_copilot_advisory_v2_fields.py
  -> preview + plan digest
  -> explicit operator approval + two environment gates
  -> ProjectV2 mutation + readback
```

La projection v2 écrit le statut, le résumé humain `Avis Copilot`, la date,
l’artefact et le cycle. Elle ne fabrique ni route ni confiance absentes du
schéma v2.

## Limites verrouillées

- aucun `gh run download` dans cette unité ;
- lecture exclusive de `.var/server_datasets/github_artifacts/raw` ;
- aucune écriture SQL ou Qdrant ;
- aucun lancement de laboratoire ;
- aucun changement du Scheduler ;
- mutation distante seulement avec décision opérateur, digest confirmé,
  `AUTODOC_REMOTE_MUTATION_ALLOWED=true` et
  `AUTODOC_PROJECT_PROJECTION_ALLOWED=true` ;
- readback ProjectV2 obligatoire après exécution.
