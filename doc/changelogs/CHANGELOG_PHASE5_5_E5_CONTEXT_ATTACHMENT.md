# Phase 5.5 — E5 context attachment contract

## Objectif

Préparer l'intégration future du runtime E5 local dans le `ContextEngine` sans lancer de Scheduler vivant.

La phase ajoute un contrat d'attachement explicite :

```text
InferenceContext existant
+ E5LocalContextRuntimeResult
-> E5ContextAttachment
-> InferenceContext fusionné
```

## Changements

- Ajout de `src/context/e5_context_attachment.py` :
  - `E5ContextAttachmentPolicy` ;
  - `E5ContextAttachmentResult` ;
  - `E5ContextAttachment` ;
  - `attach_e5_runtime_context()` ;
  - `attach_e5_artifact_dir_to_context()`.
- Export contrôlé depuis `src/context/__init__.py`.
- Ajout des tests `tests/context/test_e5_context_attachment.py`.
- Ajout du graphe `doc/docs/architecture/context/29_e5_context_attachment.dot`.
- Liaison depuis `28_e5_local_context_runtime.dot`.
- Mise à jour de `00_global.dot` pour rendre l'attachement visible dans le Context Fabric.

## Frontières

Cette phase ne fait pas de mutation du contexte d'origine. Elle construit un nouveau `InferenceContext` gelé.

Elle n'ajoute pas :

- Scheduler vivant ;
- daemon ;
- réseau ;
- API GitHub ;
- Qdrant ;
- LLM ;
- appel OpenVINO.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.5 ajoute un contrat d'attachement local pur vers InferenceContext ; aucune règle de programmation nouvelle n'est nécessaire.
```
