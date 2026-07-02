# Changelog — Phase 5.2 — E5 artifact directory loader

## Résumé

La Phase 5.2 ajoute la première bordure IO locale de la Phase 5 pour les artefacts E5.

Elle lit un dossier produit par `search --artifact-dir` en Phase 4 et le transforme en `E5RuntimeArtifactBundle`, sans lancer de Scheduler vivant, sans daemon, sans Qdrant, sans LLM et sans réseau.

## Ajouts

- `src/context/e5_artifact_loader.py`
  - `E5RuntimeArtifactDirectoryPolicy` ;
  - `E5RuntimeArtifactDirectoryReadResult` ;
  - `E5RuntimeArtifactDirectoryLoader` ;
  - `E5RuntimeArtifactDirectoryBridge` ;
  - `load_e5_runtime_artifacts_from_directory()` ;
  - `build_e5_runtime_bridge_from_directory()`.
- `tests/context/test_e5_artifact_loader.py`.
- `doc/docs/architecture/context/26_e5_artifact_directory_loader.dot`.

## Frontières

```text
artifact-dir local
-> lecture JSON contrôlée
-> E5RuntimeArtifactBundle
-> E5RuntimeBridge
-> InferenceContext
```

La lecture de fichiers est autorisée seulement dans `e5_artifact_loader.py`, qui est une bordure IO explicite. `E5RuntimeBridge` reste pur.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.2 ajoute une bordure IO locale explicite autour du pont pur 5.1 ; aucune règle de programmation nouvelle n'est nécessaire.
```
