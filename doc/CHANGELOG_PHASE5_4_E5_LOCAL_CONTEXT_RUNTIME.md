# Phase 5.4 — E5 local context runtime facade

## But

La Phase 5.4 ajoute une façade runtime locale stable au-dessus des contrats 5.1 et 5.2.

La chaîne reste volontairement locale et déterministe :

```text
artifact-dir Phase 4
-> E5RuntimeArtifactDirectoryLoader
-> E5RuntimeBridge
-> E5LocalContextRuntimeResult
-> InferenceContext
```

## Changements

- Ajout de `src/context/e5_local_context_runtime.py` :
  - `E5LocalContextRuntimePolicy` ;
  - `E5LocalContextRuntimeRequest` ;
  - `E5LocalContextRuntimeResult` ;
  - `E5LocalContextRuntime` ;
  - `build_e5_local_context_from_artifact_dir()` ;
  - `build_e5_local_inference_context_from_artifact_dir()`.
- Export des contrats runtime depuis `src/context/__init__.py`.
- Ajout de tests unitaires dédiés.
- Ajout du graphe `doc/docs/architecture/context/28_e5_local_context_runtime.dot`.
- Mise à jour de `00_global.dot` et du graphe 5.3 pour rendre la façade visible.

## Frontières

La Phase 5.4 ne lance pas de daemon, ne démarre pas le Scheduler, ne fait aucun appel réseau, ne contacte pas GitHub, n'appelle pas Qdrant, ne fait pas de génération LLM et n'appelle pas OpenVINO.

La lecture de fichiers reste dans le loader 5.2. La façade 5.4 orchestre seulement loader + bridge et retourne un résultat typé.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.4 ajoute une façade runtime locale typée autour des contrats 5.1/5.2 ; aucune règle de programmation nouvelle n'est nécessaire.
```
