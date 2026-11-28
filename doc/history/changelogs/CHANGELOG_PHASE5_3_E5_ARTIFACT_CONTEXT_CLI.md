# Changelog — Phase 5.3 — E5 artifact context CLI

## Résumé

La Phase 5.3 ajoute une bordure CLI locale et testable pour inspecter l'`InferenceContext` construit depuis un `artifact-dir` Phase 4.

Elle ne crée pas de nouveau daemon et ne lance aucun Scheduler vivant. Elle réutilise les contrats déjà posés en 5.1 et 5.2 :

```text
artifact-dir Phase 4
-> E5RuntimeArtifactDirectoryLoader
-> E5RuntimeBridge
-> InferenceContext
-> rendu stdout text/json
```

## Ajouts

- `src/context/e5_artifact_cli.py`
  - `E5ArtifactContextRenderPolicy` ;
  - `E5ArtifactContextCommand` ;
  - `build_e5_artifact_context_parser()` ;
  - `command_from_args()` ;
  - `run_e5_artifact_context()`.
- `tests/context/test_e5_artifact_cli.py`.
- `doc/docs/architecture/context/27_e5_artifact_context_cli.dot`.

## Mise à jour architecture

- `doc/docs/architecture/context/26_e5_artifact_directory_loader.dot` pointe maintenant vers la Phase 5.3.
- `doc/docs/architecture/00_global.dot` affiche la bordure CLI locale dans le Context Fabric.

## Frontières

```text
pas de daemon
pas de Scheduler vivant
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
pas d'API GitHub
pas de token
pas de polling réseau
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.3 ajoute une bordure CLI locale typée autour des contrats 5.1/5.2 ; aucune règle de programmation nouvelle n'est nécessaire.
```
