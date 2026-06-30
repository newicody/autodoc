# Phase 5 — Entrée runtime local contrôlé

## Statut

La Phase 5 commence après la clôture Phase 4.

La Phase 4 a produit une chaîne locale déterministe :

```text
report.json
context.json
consumed_context.json
prompt.json
```

La Phase 5 ne doit pas encore transformer cette chaîne en daemon, en API GitHub, en Qdrant ou en génération LLM.

## Intention Phase 5.1

La Phase 5.1 ajoute un pont local pur :

```text
artefacts E5 déjà chargés
-> E5RuntimeArtifactBundle
-> E5RuntimeBridge
-> InferenceContext
```

Ce pont permet au Context Fabric de voir le résultat E5 comme une projection stable :

```text
features["e5_local_context"]
priorities["e5_local_context"]
```

## Ce que le pont contient

Le pont extrait des métadonnées déterministes :

```text
schema
query
prefixed_query
index
model
backend
tokenizer
dimension
hit_count
context_item_count
selected_item_count
skipped_item_count
max_context_chars
used_context_chars
prompt_chars
```

Selon la politique, il peut inclure :

```text
prompt_text
context_text
```

Cette inclusion est explicite dans `E5RuntimeBridgePolicy`.

## Frontières

La Phase 5.1 ne fait pas :

```text
lecture de fichiers
polling
GitHub API
Qdrant
Scheduler vivant
génération LLM
appel OpenVINO
```

Elle ne consomme que des payloads déjà chargés. L'IO reste donc une responsabilité de bordure future.

## Place dans l'architecture

Le pont se place entre :

```text
E5 local context stack — Phase 4 closed
```

et :

```text
Context Fabric / InferenceContext
```

Il prépare les phases suivantes :

```text
5.2 — local artifact intake contrôlé
5.3 — état local serveur / registre d'artefacts
5.4 — exposition ContextEngine sans Scheduler lourd
```

## SourceCandidate

La couche SourceCandidate / GitHub Project Orchestrator reste future.

Elle pourra plus tard alimenter le même type d'artefacts, mais la Phase 5.1 ne connaît pas GitHub.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.1 ajoute un pont pur et typé vers InferenceContext ; aucune règle de programmation nouvelle n'est nécessaire.
```
